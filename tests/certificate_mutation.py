"""Systematic adversarial mutation of retained order certificates.

Every mutation changes exactly one checked field or the certificate schema.
The campaign is deterministic and expects exact replay to reject every case.
It is a finite robustness test, not a proof that the checker is bug-free.
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
from order_common import InputError  # noqa: E402
from order_verify import Invalid, replay  # noqa: E402


def changed_rational(value):
    # Certificate probabilities, deficits, transports, and dual weights are
    # nonnegative.  Replacing one checked scalar by -1 is therefore a genuine
    # corruption rather than a different but still valid non-unique witness.
    Fraction(value)  # validate the original syntax
    return "-1"


def scalar_paths(value, path=()):
    if isinstance(value, dict):
        for key in sorted(value):
            yield from scalar_paths(value[key], path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from scalar_paths(item, path + (index,))
    elif isinstance(value, str):
        try:
            Fraction(value)
        except (ValueError, ZeroDivisionError):
            return
        yield path
    elif type(value) is int:
        yield path


def set_path(value, path, replacement):
    cursor = value
    for step in path[:-1]:
        cursor = cursor[step]
    cursor[path[-1]] = replacement


def get_path(value, path):
    cursor = value
    for step in path:
        cursor = cursor[step]
    return cursor


def try_replay(task, cert):
    try:
        replay(task, cert)
    except (Invalid, InputError, ValueError, TypeError, KeyError, IndexError):
        return False
    return True


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    start = time.perf_counter()
    cpu = time.process_time()

    corpus = json.loads((ROOT / "results" / "order-certificates.json").read_text(encoding="utf-8"))
    records = list(corpus["retained"].values()) + corpus["random"]
    attempted = 0
    rejected = 0
    unexpected = []
    classes = {"schema_delete": 0, "schema_extra": 0, "numeric_leaf": 0,
               "numeric_type": 0, "list_shape": 0}

    for record_index, record in enumerate(records):
        task = record["task"]
        cert = record["certificate"]
        if not try_replay(task, cert):
            raise RuntimeError(f"baseline certificate {record_index} failed replay")

        for key in sorted(cert):
            bad = copy.deepcopy(cert)
            del bad[key]
            attempted += 1
            classes["schema_delete"] += 1
            if try_replay(task, bad):
                unexpected.append([record_index, "delete", key])
            else:
                rejected += 1

        bad = copy.deepcopy(cert)
        bad["unexpected"] = 0
        attempted += 1
        classes["schema_extra"] += 1
        if try_replay(task, bad):
            unexpected.append([record_index, "extra"])
        else:
            rejected += 1

        paths = list(scalar_paths(cert))
        # Mutate every checked numeric scalar.  This traverses objectives,
        # mixture weights, row deficiencies, all transport cells, dual data,
        # global index, and witness floors.
        for path in paths:
            original = get_path(cert, path)
            bad = copy.deepcopy(cert)
            replacement = -1 if type(original) is int else changed_rational(original)
            set_path(bad, path, replacement)
            attempted += 1
            classes["numeric_leaf"] += 1
            if try_replay(task, bad):
                unexpected.append([record_index, "numeric", list(path)])
            else:
                rejected += 1

        # JSON floats are forbidden even when numerically integral.
        rational_paths = [p for p in paths if isinstance(get_path(cert, p), str)]
        if rational_paths:
            bad = copy.deepcopy(cert)
            set_path(bad, rational_paths[0], float(Fraction(get_path(cert, rational_paths[0]))))
            attempted += 1
            classes["numeric_type"] += 1
            if try_replay(task, bad):
                unexpected.append([record_index, "float", list(rational_paths[0])])
            else:
                rejected += 1

        # Shorten one required list dimension.
        bad = copy.deepcopy(cert)
        bad["proofs"] = bad["proofs"][:-1]
        attempted += 1
        classes["list_shape"] += 1
        if try_replay(task, bad):
            unexpected.append([record_index, "proof-count"])
        else:
            rejected += 1

    scientific = {
        "certificates_mutated": len(records),
        "mutations_attempted": attempted,
        "mutations_rejected": rejected,
        "unexpected_acceptances": len(unexpected),
        "mutation_classes": classes,
        "unexpected_examples": unexpected[:5],
        "scope": "deterministic single-field mutation testing of retained order certificates; not a proof of checker correctness",
    }
    if unexpected:
        raise RuntimeError(f"certificate mutations accepted: {unexpected[:5]}")
    (ROOT / "results" / "certificate-mutation.json").write_text(
        json.dumps(scientific, indent=2) + "\n", encoding="utf-8")
    resources = {
        "result": scientific,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "one_worker": True,
    }
    (ROOT / "results" / "certificate-mutation-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scientific, sort_keys=True))


if __name__ == "__main__":
    main()
