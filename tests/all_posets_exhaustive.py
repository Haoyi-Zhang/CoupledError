"""Independent exhaustive checks over every labeled poset through four points.

This test intentionally does not import the production order implementation.
It enumerates all reflexive, antisymmetric, transitive relations on labeled
sets of sizes 2--4, all denominator-two laws, and compares an independently
implemented integer max-flow deficiency with exhaustive upward-set deficits.
It also checks the directed triangle inequality and the target-law monitor's
upward monotonicity.
"""
from __future__ import annotations

import itertools
import json
import os
import resource
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compositions(total: int, parts: int):
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in compositions(total - first, parts - 1):
            yield (first,) + rest


def labeled_posets(n: int):
    """Enumerate all labeled posets by orienting each unordered pair."""
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    for choices in itertools.product((0, 1, 2), repeat=len(pairs)):
        leq = [[i == j for j in range(n)] for i in range(n)]
        for (i, j), choice in zip(pairs, choices):
            if choice == 1:
                leq[i][j] = True
            elif choice == 2:
                leq[j][i] = True
        if all(not (leq[i][j] and leq[j][k]) or leq[i][k]
               for i in range(n) for j in range(n) for k in range(n)):
            yield tuple(tuple(row) for row in leq)


def upward_sets(leq):
    n = len(leq)
    out = []
    for mask in range(1 << n):
        if all(not (mask & (1 << x)) or
               all(not leq[x][y] or (mask & (1 << y)) for y in range(n))
               for x in range(n)):
            out.append(tuple(i for i in range(n) if mask & (1 << i)))
    return tuple(out)


def max_good_flow(left, right, leq):
    """Exact integral Edmonds--Karp on x<=y edges."""
    n = len(left)
    source, l0, r0, sink = 0, 1, 1 + n, 1 + 2 * n
    size = sink + 1
    cap = [[0] * size for _ in range(size)]
    total = sum(left)
    for x, value in enumerate(left):
        cap[source][l0 + x] = value
    for x in range(n):
        for y in range(n):
            if leq[x][y]:
                cap[l0 + x][r0 + y] = total
    for y, value in enumerate(right):
        cap[r0 + y][sink] = value
    residual = [row[:] for row in cap]
    adjacency = [set() for _ in range(size)]
    for u in range(size):
        for v in range(size):
            if cap[u][v]:
                adjacency[u].add(v)
                adjacency[v].add(u)
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
            return flow
        aug = None
        v = sink
        while v != source:
            u = parent[v]
            aug = residual[u][v] if aug is None else min(aug, residual[u][v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= aug
            residual[v][u] += aug
            v = u
        flow += aug


def deficiency_flow(left, right, leq):
    return sum(left) - max_good_flow(left, right, leq)


def deficiency_upsets(left, right, leq):
    return max(sum(left[x] for x in up) - sum(right[x] for x in up)
               for up in upward_sets(leq))


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    start = time.perf_counter()
    cpu = time.process_time()

    expected = {2: 3, 3: 19, 4: 219}
    counts = {}
    pair_count = 0
    triple_count = 0
    flow_dual_mismatches = 0
    triangle_violations = 0
    target_monitor_violations = 0
    max_upward_sets = 0

    for n in (2, 3, 4):
        posets = list(labeled_posets(n))
        counts[str(n)] = len(posets)
        if len(posets) != expected[n]:
            raise RuntimeError(f"unexpected number of labeled {n}-posets: {len(posets)}")
        laws = list(compositions(2, n))
        for leq in posets:
            max_upward_sets = max(max_upward_sets, len(upward_sets(leq)))
            for y in range(n):
                for x in range(n):
                    for xp in range(n):
                        if leq[x][xp] and int(not leq[x][y]) > int(not leq[xp][y]):
                            target_monitor_violations += 1
            dist = {}
            for i, left in enumerate(laws):
                for j, right in enumerate(laws):
                    flow = deficiency_flow(left, right, leq)
                    dual = deficiency_upsets(left, right, leq)
                    pair_count += 1
                    if flow != dual:
                        flow_dual_mismatches += 1
                    dist[i, j] = flow
            for i in range(len(laws)):
                for j in range(len(laws)):
                    for k in range(len(laws)):
                        triple_count += 1
                        if dist[i, k] > dist[i, j] + dist[j, k]:
                            triangle_violations += 1

    scientific = {
        "labeled_posets_by_size": counts,
        "total_labeled_posets": sum(counts.values()),
        "law_denominator": 2,
        "ordered_law_pairs": pair_count,
        "ordered_law_triples": triple_count,
        "flow_upward_set_mismatches": flow_dual_mismatches,
        "triangle_violations": triangle_violations,
        "target_monitor_upward_violations": target_monitor_violations,
        "maximum_upward_sets_including_empty": max_upward_sets,
        "scope": "exhaustive finite check over every labeled poset with two to four outcomes; not a proof for arbitrary finite posets",
    }
    if any((flow_dual_mismatches, triangle_violations, target_monitor_violations)):
        raise RuntimeError("exhaustive all-poset check found a counterexample")
    (ROOT / "results" / "all-posets-exhaustive.json").write_text(
        json.dumps(scientific, indent=2) + "\n", encoding="utf-8")
    resources = {
        "result": scientific,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "one_worker": True,
    }
    (ROOT / "results" / "all-posets-exhaustive-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scientific, sort_keys=True))


if __name__ == "__main__":
    main()
