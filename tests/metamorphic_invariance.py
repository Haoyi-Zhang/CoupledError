"""Metamorphic invariance checks for the production certificate path.

The mathematical value must not depend on boundary/outcome labels, index
orders, or convex-generator enumeration.  This deterministic campaign applies
representation-preserving transformations to every named order task, produces
a fresh certificate, and replays it exactly.  It targets hard-coded ordering
and corpus-specific bugs; it is not a completeness proof for the producer.
"""
from __future__ import annotations

import copy
import json
import os
import resource
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from order_run import certificate  # noqa: E402
from order_verify import replay  # noqa: E402

TASKS = (
    "order-binary.json",
    "order-convex.json",
    "order-pipeline.json",
    "order-relational.json",
)


def transformed(task, outcome_perm=None, boundary_perm=None,
                reverse_old=False, reverse_new=False, rename=False):
    value = copy.deepcopy(task)
    outcomes = task["poset"]["outcomes"]
    boundary = task["boundary"]
    op = tuple(range(len(outcomes))) if outcome_perm is None else tuple(outcome_perm)
    bp = tuple(range(len(boundary))) if boundary_perm is None else tuple(boundary_perm)

    value["boundary"] = [boundary[i] for i in bp]
    value["poset"]["outcomes"] = [outcomes[i] for i in op]
    value["poset"]["leq"] = [
        [task["poset"]["leq"][i][j] for j in op] for i in op
    ]
    if rename:
        value["boundary"] = [f"boundary-{i}" for i in range(len(bp))]
        value["poset"]["outcomes"] = [f"outcome-{i}" for i in range(len(op))]

    for side, reverse in (("old", reverse_old), ("new", reverse_new)):
        generators = []
        for generator in task[side]["generators"]:
            mass = generator["mass"]
            generators.append({
                "mass": [[mass[s][x] for x in op] for s in bp]
            })
        if reverse:
            generators.reverse()
        value[side]["generators"] = generators
    return value


def unique_transforms(task):
    no = len(task["poset"]["outcomes"])
    nb = len(task["boundary"])
    identity_o = tuple(range(no))
    identity_b = tuple(range(nb))
    outcome_perms = {
        tuple(reversed(identity_o)),
        identity_o[1:] + identity_o[:1],
        ((1, 0) + identity_o[2:]) if no >= 2 else identity_o,
    }
    boundary_perms = {
        tuple(reversed(identity_b)),
        identity_b[1:] + identity_b[:1],
    }
    specs = []
    for op in sorted(outcome_perms):
        if op != identity_o:
            specs.append((op, identity_b, False, False, False, "outcome-permutation"))
    for bp in sorted(boundary_perms):
        if bp != identity_b:
            specs.append((identity_o, bp, False, False, False, "boundary-permutation"))
    if len(task["old"]["generators"]) > 1:
        specs.append((identity_o, identity_b, True, False, False, "old-generator-reversal"))
    if len(task["new"]["generators"]) > 1:
        specs.append((identity_o, identity_b, False, True, False, "new-generator-reversal"))
    specs.append((tuple(reversed(identity_o)), tuple(reversed(identity_b)),
                  True, True, True, "combined-permutation-and-renaming"))

    seen = set()
    for op, bp, ro, rn, rename, label in specs:
        key = (op, bp, ro, rn, rename)
        if key not in seen:
            seen.add(key)
            yield op, bp, ro, rn, rename, label


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    start = time.perf_counter()
    cpu = time.process_time()
    checks = 0
    classes = {}
    failures = []

    for filename in TASKS:
        task = json.loads((ROOT / "inputs" / filename).read_text(encoding="utf-8"))
        baseline_cert = certificate(task)
        baseline = replay(task, baseline_cert)
        for op, bp, ro, rn, rename, label in unique_transforms(task):
            variant = transformed(task, op, bp, ro, rn, rename)
            cert = certificate(variant)
            value = replay(variant, cert)
            checks += 1
            classes[label] = classes.get(label, 0) + 1
            if Fraction(value) != Fraction(baseline):
                failures.append({
                    "task": filename,
                    "transformation": label,
                    "baseline": str(baseline),
                    "observed": str(value),
                })

    scientific = {
        "named_tasks": len(TASKS),
        "transformed_tasks_checked": checks,
        "transformation_classes": classes,
        "value_or_replay_failures": len(failures),
        "failure_examples": failures[:5],
        "scope": (
            "deterministic representation-invariance checks for named production "
            "tasks; not a completeness proof for the numerical certificate producer"
        ),
    }
    if failures:
        raise RuntimeError(f"metamorphic invariance failure: {failures[:5]}")
    (ROOT / "results" / "metamorphic-invariance.json").write_text(
        json.dumps(scientific, indent=2) + "\n", encoding="utf-8")
    resources = {
        "result": scientific,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "one_worker": True,
    }
    (ROOT / "results" / "metamorphic-invariance-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scientific, sort_keys=True))


if __name__ == "__main__":
    main()
