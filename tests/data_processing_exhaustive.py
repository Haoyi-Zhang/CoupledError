"""Independent exhaustive data-processing checks.

Enumerates every labeled poset with two or three outcomes.  It checks every
monotone deterministic map and every denominator-two stochastically monotone
Markov kernel between every source/target pair, against every denominator-two
source-law pair.  The implementation is self-contained and does not import
production order code.
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


def compositions(total, parts):
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in compositions(total - first, parts - 1):
            yield (first,) + rest


def labeled_posets(n):
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


def max_good_flow(left, right, leq):
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


def deficiency(left, right, leq):
    return sum(left) - max_good_flow(left, right, leq)


def monotone_maps(source, target):
    n, m = len(source), len(target)
    for mapping in itertools.product(range(m), repeat=n):
        if all(not source[x][xp] or target[mapping[x]][mapping[xp]]
               for x in range(n) for xp in range(n)):
            yield mapping


def push_map(law, mapping, target_size):
    out = [0] * target_size
    for x, value in enumerate(law):
        out[mapping[x]] += value
    return tuple(out)


def monotone_kernels(source, target, rows):
    """Yield all denominator-two kernels monotone in stochastic order."""
    row_def = {(i, j): deficiency(rows[i], rows[j], target)
               for i in range(len(rows)) for j in range(len(rows))}
    for indices in itertools.product(range(len(rows)), repeat=len(source)):
        if all(not source[x][xp] or row_def[indices[x], indices[xp]] == 0
               for x in range(len(source)) for xp in range(len(source))):
            yield tuple(rows[i] for i in indices)


def push_kernel(law, kernel, target_size):
    out = [0] * target_size
    for x, source_mass in enumerate(law):
        for z, row_mass in enumerate(kernel[x]):
            out[z] += source_mass * row_mass
    return tuple(out)


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    start = time.perf_counter()
    cpu = time.process_time()
    posets = {n: list(labeled_posets(n)) for n in (2, 3)}
    laws = {n: list(compositions(2, n)) for n in (2, 3)}

    map_count = 0
    map_checks = 0
    map_violations = 0
    kernel_count = 0
    kernel_checks = 0
    kernel_violations = 0
    source_target_pairs = 0

    for n in (2, 3):
        for source in posets[n]:
            source_dist = {(i, j): deficiency(a, b, source)
                           for i, a in enumerate(laws[n])
                           for j, b in enumerate(laws[n])}
            for m in (2, 3):
                target_rows = laws[m]
                target_laws4 = list(compositions(4, m))
                for target in posets[m]:
                    source_target_pairs += 1
                    target_dist2 = {(a, b): deficiency(a, b, target)
                                    for a in target_rows for b in target_rows}
                    target_dist4 = {(a, b): deficiency(a, b, target)
                                    for a in target_laws4 for b in target_laws4}

                    for mapping in monotone_maps(source, target):
                        map_count += 1
                        pushed = [push_map(law, mapping, m) for law in laws[n]]
                        for i in range(len(laws[n])):
                            for j in range(len(laws[n])):
                                map_checks += 1
                                if target_dist2[pushed[i], pushed[j]] > source_dist[i, j]:
                                    map_violations += 1

                    # Rows and source laws both have denominator two, so pushed
                    # laws have total mass four.  Compare with twice the source
                    # deficiency to keep the same probability scale.
                    for kernel in monotone_kernels(source, target, target_rows):
                        kernel_count += 1
                        pushed = [push_kernel(law, kernel, m) for law in laws[n]]
                        for i in range(len(laws[n])):
                            for j in range(len(laws[n])):
                                kernel_checks += 1
                                if target_dist4[pushed[i], pushed[j]] > 2 * source_dist[i, j]:
                                    kernel_violations += 1

    scientific = {
        "source_posets": sum(len(posets[n]) for n in posets),
        "target_posets": sum(len(posets[n]) for n in posets),
        "source_target_poset_pairs": source_target_pairs,
        "deterministic_monotone_maps": map_count,
        "deterministic_law_pair_map_checks": map_checks,
        "deterministic_data_processing_violations": map_violations,
        "stochastically_monotone_kernels": kernel_count,
        "stochastic_law_pair_kernel_checks": kernel_checks,
        "stochastic_data_processing_violations": kernel_violations,
        "source_law_denominator": 2,
        "kernel_row_denominator": 2,
        "scope": "exhaustive deterministic-map and denominator-two stochastic-kernel check over all labeled two- and three-outcome posets; not a proof for arbitrary kernels",
    }
    if map_violations or kernel_violations:
        raise RuntimeError("data-processing counterexample found")
    (ROOT / "results" / "data-processing-exhaustive.json").write_text(
        json.dumps(scientific, indent=2) + "\n", encoding="utf-8")
    resources = {
        "result": scientific,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "one_worker": True,
    }
    (ROOT / "results" / "data-processing-exhaustive-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scientific, sort_keys=True))


if __name__ == "__main__":
    main()
