"""Bounded structural scaling profile for the reference certificate path.

The goal is not a performance claim.  It verifies exact production and replay
at every supported outcome size and records the explicit upward-set growth
that limits the reference implementation.
"""
from __future__ import annotations

import json
import os
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from order_common import upward_sets  # noqa: E402
from order_run import certificate  # noqa: E402
from order_verify import replay  # noqa: E402


def task_for(n, kind):
    outcomes = [f"x{i}" for i in range(n)]
    if kind == "chain":
        leq = [[int(i <= j) for j in range(n)] for i in range(n)]
    elif kind == "antichain":
        leq = [[int(i == j) for j in range(n)] for i in range(n)]
    else:
        raise ValueError(kind)
    # Point masses make the intended exact answer transparent while still
    # exercising every primal, transport, dual, and witness dimension.
    old = ["0"] * n
    old[-1] = "1"
    new = ["0"] * n
    new[0] = "1"
    return {
        "boundary": ["s"],
        "poset": {"outcomes": outcomes, "leq": leq},
        "old": {"generators": [{"mass": [old]}]},
        "new": {"generators": [{"mass": [new]}]},
    }


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    start = time.perf_counter()
    cpu = time.process_time()
    cases = []
    failures = 0
    for kind in ("chain", "antichain"):
        for n in range(2, 9):
            task = task_for(n, kind)
            cert = certificate(task)
            value = replay(task, cert)
            leq = tuple(tuple(bool(v) for v in row) for row in task["poset"]["leq"])
            upsets = len(upward_sets(leq))
            expected_upsets = n if kind == "chain" else (2 ** n - 1)
            if upsets != expected_upsets:
                failures += 1
            expected_value = "1" if kind == "antichain" else "1"
            if str(value) != expected_value:
                failures += 1
            cases.append({
                "order": kind,
                "outcomes": n,
                "nonempty_upward_sets": upsets,
                "transport_cells": n * n,
                "certificate_value": str(value),
                "exact_replay": True,
            })
    scientific = {
        "cases": cases,
        "cases_checked": len(cases),
        "supported_outcome_range": [2, 8],
        "maximum_nonempty_upward_sets": max(c["nonempty_upward_sets"] for c in cases),
        "maximum_transport_cells": max(c["transport_cells"] for c in cases),
        "failures": failures,
        "scope": "bounded structural profile of the explicit reference implementation; timings are excluded from scientific claims",
        "limitation": "antichain upward sets grow as 2^n-1, so the reference encoding is not a scalability result",
    }
    if failures:
        raise RuntimeError("scaling profile invariant failed")
    (ROOT / "results" / "scaling-profile.json").write_text(
        json.dumps(scientific, indent=2) + "\n", encoding="utf-8")
    resources = {
        "result": scientific,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "one_worker": True,
    }
    (ROOT / "results" / "scaling-profile-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scientific, sort_keys=True))


if __name__ == "__main__":
    main()
