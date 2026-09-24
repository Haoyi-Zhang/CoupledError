"""Independent exact point-law sweep over several finite poset shapes.

The implementation below does not import the production order library.  It
compares an integer maximum-flow computation of order-preserving transport with
independent upward-set enumeration, checks the directed triangle inequality,
and verifies that every target-law witness predicate {x : x not<= y} is upward.
The sweep is finite evidence only, not a mechanized proof.
"""
from __future__ import annotations

import json
import os
import resource
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENOMINATOR = 3


def compositions(total: int, parts: int):
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in compositions(total - first, parts - 1):
            yield (first,) + rest


def transitive_closure(n: int, covers):
    leq = [[i == j for j in range(n)] for i in range(n)]
    for x, y in covers:
        leq[x][y] = True
    for k in range(n):
        for i in range(n):
            if leq[i][k]:
                for j in range(n):
                    leq[i][j] = leq[i][j] or leq[k][j]
    return tuple(tuple(row) for row in leq)


def posets():
    return {
        "chain2": transitive_closure(2, ((0, 1),)),
        "chain3": transitive_closure(3, ((0, 1), (1, 2))),
        "vee3": transitive_closure(3, ((0, 1), (0, 2))),
        "wedge3": transitive_closure(3, ((0, 2), (1, 2))),
        "diamond4": transitive_closure(4, ((0, 1), (0, 2), (1, 3), (2, 3))),
        "antichain4": transitive_closure(4, ()),
    }


def upward_sets(leq):
    n = len(leq)
    result = []
    for mask in range(1, 1 << n):
        members = tuple(i for i in range(n) if mask & (1 << i))
        if all(not (mask & (1 << x)) or
               all(not leq[x][y] or (mask & (1 << y)) for y in range(n))
               for x in range(n)):
            result.append(members)
    return tuple(result)


def max_good_flow(left, right, leq):
    """Integer Edmonds--Karp maximum flow on the allowed order edges."""
    n = len(left)
    source, left0, right0, sink = 0, 1, 1 + n, 1 + 2 * n
    size = sink + 1
    capacity = [[0] * size for _ in range(size)]
    adjacency = [set() for _ in range(size)]

    def add_edge(u, v, cap):
        capacity[u][v] = cap
        adjacency[u].add(v)
        adjacency[v].add(u)

    for x, value in enumerate(left):
        add_edge(source, left0 + x, value)
    for x in range(n):
        for y in range(n):
            if leq[x][y]:
                add_edge(left0 + x, right0 + y, DENOMINATOR)
    for y, value in enumerate(right):
        add_edge(right0 + y, sink, value)

    residual = [row[:] for row in capacity]
    flow = 0
    while True:
        parent = [-1] * size
        parent[source] = source
        queue = deque([source])
        while queue and parent[sink] < 0:
            u = queue.popleft()
            for v in sorted(adjacency[u]):
                if parent[v] < 0 and residual[u][v] > 0:
                    parent[v] = u
                    queue.append(v)
                    if v == sink:
                        break
        if parent[sink] < 0:
            break
        amount = DENOMINATOR
        v = sink
        while v != source:
            u = parent[v]
            amount = min(amount, residual[u][v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= amount
            residual[v][u] += amount
            v = u
        flow += amount
    return flow


def transport_deficiency(left, right, leq):
    return DENOMINATOR - max_good_flow(left, right, leq)


def upset_deficiency(left, right, upsets):
    return max([0] + [sum(left[i] for i in upset) - sum(right[i] for i in upset)
                      for upset in upsets])


def witness_upward_violations(leq):
    n = len(leq)
    violations = 0
    for y in range(n):
        for x in range(n):
            for xp in range(n):
                if leq[x][xp] and not leq[x][y] and leq[xp][y]:
                    violations += 1
    return violations


def main() -> None:
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    records = []
    total_pairs = 0
    total_triples = 0
    total_mismatches = 0
    total_triangle_violations = 0
    total_witness_violations = 0

    for name, leq in posets().items():
        laws = tuple(compositions(DENOMINATOR, len(leq)))
        upsets = upward_sets(leq)
        distances = {}
        mismatches = 0
        for i, left in enumerate(laws):
            for j, right in enumerate(laws):
                transport = transport_deficiency(left, right, leq)
                upset = upset_deficiency(left, right, upsets)
                if transport != upset:
                    mismatches += 1
                distances[(i, j)] = transport
        triangle_violations = sum(
            distances[(i, k)] > distances[(i, j)] + distances[(j, k)]
            for i in range(len(laws))
            for j in range(len(laws))
            for k in range(len(laws))
        )
        witness_violations = witness_upward_violations(leq)
        record = {
            "poset": name,
            "outcomes": len(leq),
            "nonempty_upward_sets": len(upsets),
            "laws": len(laws),
            "ordered_pairs": len(laws) ** 2,
            "transport_upset_mismatches": mismatches,
            "triangle_triples": len(laws) ** 3,
            "triangle_violations": triangle_violations,
            "target_monitor_upward_violations": witness_violations,
        }
        records.append(record)
        total_pairs += record["ordered_pairs"]
        total_triples += record["triangle_triples"]
        total_mismatches += mismatches
        total_triangle_violations += triangle_violations
        total_witness_violations += witness_violations

    if total_mismatches or total_triangle_violations or total_witness_violations:
        raise RuntimeError("finite poset sweep found a mismatch")

    result = {
        "denominator": DENOMINATOR,
        "posets": len(records),
        "records": records,
        "ordered_pairs": total_pairs,
        "transport_upset_mismatches": 0,
        "triangle_triples": total_triples,
        "triangle_violations": 0,
        "target_monitor_upward_violations": 0,
        "scope": "finite exact multi-poset cross-check; not a proof of the general theorem",
    }
    (ROOT / "results" / "poset-sweep.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    resources_record = {
        "stage": "poset-sweep",
        "workers": 1,
        "result": {key: result[key] for key in (
            "posets", "ordered_pairs", "transport_upset_mismatches",
            "triangle_triples", "triangle_violations",
            "target_monitor_upward_violations")},
        "cpu_seconds": time.process_time() - cpu_start,
        "wall_seconds": time.perf_counter() - wall_start,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (ROOT / "results" / "poset-sweep-resources.json").write_text(
        json.dumps(resources_record, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
