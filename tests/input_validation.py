"""Adversarial bounded-input checks for command-line parsers and replay paths."""
import copy
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, expected, case, cwd=ROOT):
    completed = subprocess.run([sys.executable, *args], cwd=cwd, text=True,
                               capture_output=True, timeout=20)
    if completed.returncode != expected:
        raise RuntimeError(
            f"{case}: expected exit {expected}, got {completed.returncode}; "
            f"stdout={completed.stdout!r}; stderr={completed.stderr!r}")
    return {
        "case": case,
        "expected_exit": expected,
        "actual_exit": completed.returncode,
        "diagnostic_present": bool((completed.stdout + completed.stderr).strip()),
    }


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    start_cpu = time.process_time()
    start_wall = time.perf_counter()
    records = []

    order_task = json.loads((ROOT / "inputs" / "order-relational.json").read_text())
    order_cert = json.loads((ROOT / "results" / "order-relational.certificate.json").read_text())
    join_task = json.loads((ROOT / "inputs" / "join-tree.json").read_text())
    join_cert = json.loads((ROOT / "results" / "dependency.certificate.json").read_text())

    with tempfile.TemporaryDirectory(prefix="contract-input-validation-") as td:
        temp = Path(td)

        duplicate_task = temp / "duplicate-task.json"
        duplicate_task.write_text(
            '{"boundary":["s"],"boundary":["t"],"poset":{"outcomes":["0","1"],'
            '"leq":[[1,1],[0,1]]},"old":{"generators":[{"mass":[["1","0"]]}]},'
            '"new":{"generators":[{"mass":[["1","0"]]}]}}', encoding="utf-8")
        records.append(run(["src/order_run.py", str(duplicate_task), str(temp / "x.json")],
                           1, "order-producer-duplicate-json-key"))

        duplicate_cert = temp / "duplicate-cert.json"
        duplicate_cert.write_text('{"kind":"order-coupling-loss","kind":"other"}', encoding="utf-8")
        valid_task = temp / "valid-order.json"
        valid_task.write_text(json.dumps(order_task), encoding="utf-8")
        records.append(run(["src/order_verify.py", str(valid_task), str(duplicate_cert)],
                           1, "order-replay-duplicate-json-key"))

        float_leq = copy.deepcopy(order_task)
        float_leq["poset"]["leq"][0][0] = 1.0
        path = temp / "float-leq.json"
        path.write_text(json.dumps(float_leq), encoding="utf-8")
        records.append(run(["src/order_run.py", str(path), str(temp / "x.json")],
                           1, "order-float-boolean-rejected"))

        bool_mass = copy.deepcopy(order_task)
        bool_mass["old"]["generators"][0]["mass"][0][0] = True
        path = temp / "bool-mass.json"
        path.write_text(json.dumps(bool_mass), encoding="utf-8")
        records.append(run(["src/order_run.py", str(path), str(temp / "x.json")],
                           1, "order-boolean-rational-rejected"))

        huge = copy.deepcopy(order_task)
        huge["old"]["generators"][0]["mass"][0][0] = "1" * 161
        path = temp / "huge-rational.json"
        path.write_text(json.dumps(huge), encoding="utf-8")
        records.append(run(["src/order_run.py", str(path), str(temp / "x.json")],
                           1, "order-long-rational-rejected"))

        huge_integer = copy.deepcopy(order_task)
        huge_integer["old"]["generators"][0]["mass"][0][0] = 1 << 256
        path = temp / "huge-json-integer.json"
        path.write_text(json.dumps(huge_integer), encoding="utf-8")
        records.append(run(["src/order_run.py", str(path), str(temp / "x.json")],
                           1, "order-257-bit-json-integer-rejected"))

        nontransitive = {
            "boundary": ["s"],
            "poset": {"outcomes": ["a", "b", "c"],
                      "leq": [[1, 1, 0], [0, 1, 1], [0, 0, 1]]},
            "old": {"generators": [{"mass": [["1", "0", "0"]]}]},
            "new": {"generators": [{"mass": [["1", "0", "0"]]}]},
        }
        path = temp / "nontransitive.json"
        path.write_text(json.dumps(nontransitive), encoding="utf-8")
        records.append(run(["src/order_run.py", str(path), str(temp / "x.json")],
                           1, "order-nontransitive-rejected"))

        boolean_index_cert = copy.deepcopy(order_cert)
        boolean_index_cert["worst_generator"] = False
        boolean_index_path = temp / "boolean-worst-generator.json"
        boolean_index_path.write_text(json.dumps(boolean_index_cert), encoding="utf-8")
        records.append(run(["src/order_verify.py", str(valid_task), str(boolean_index_path)],
                           1, "order-boolean-worst-generator-rejected"))

        valid_cert = temp / "valid-cert.json"
        valid_cert.write_text(json.dumps(order_cert), encoding="utf-8")
        records.append(run(["src/order_verify.py", str(valid_task), str(valid_cert)],
                           0, "order-valid-control"))

        duplicate_join = temp / "duplicate-join.json"
        raw_join = json.dumps(join_task, separators=(",", ":"))
        duplicate_join.write_text('{"variables":' + json.dumps(join_task["variables"]) +
                                  ',"variables":' + json.dumps(join_task["variables"]) +
                                  ',"bags":' + json.dumps(join_task["bags"]) +
                                  ',"tree_edges":' + json.dumps(join_task["tree_edges"]) +
                                  ',"marginals":' + json.dumps(join_task["marginals"]) + '}',
                                  encoding="utf-8")
        records.append(run(["src/join_tree.py", str(duplicate_join), str(temp / "j.json")],
                           1, "join-tree-duplicate-json-key"))

        invalid_label = copy.deepcopy(join_task)
        invalid_label["variables"][0] = ["not", "hashable"]
        path = temp / "invalid-variable.json"
        path.write_text(json.dumps(invalid_label), encoding="utf-8")
        records.append(run(["src/join_tree.py", str(path), str(temp / "j.json")],
                           1, "join-tree-invalid-variable-label"))

        valid_join_task = temp / "valid-join.json"
        valid_join_task.write_text(raw_join, encoding="utf-8")
        valid_join_cert = temp / "valid-join-cert.json"
        valid_join_cert.write_text(json.dumps(join_cert), encoding="utf-8")
        records.append(run(["src/join_tree.py", str(valid_join_task), str(valid_join_cert), "--verify"],
                           0, "join-tree-valid-control"))
        records.append(run(["src/join_tree.py", str(valid_join_task), str(valid_join_cert), "--wrong"],
                           2, "join-tree-invalid-mode-flag"))

        malformed_join_cert = copy.deepcopy(join_cert)
        malformed_join_cert["law"] = []
        path = temp / "malformed-join-cert.json"
        path.write_text(json.dumps(malformed_join_cert), encoding="utf-8")
        records.append(run(["src/join_tree.py", str(valid_join_task), str(path), "--verify"],
                           1, "join-tree-malformed-certificate-law"))

    result = {
        "cases": records,
        "cases_checked": len(records),
        "expected_rejections": sum(item["expected_exit"] != 0 for item in records),
        "unexpected_acceptances": 0,
        "scope": "bounded parser and CLI robustness checks",
    }
    (ROOT / "results" / "input-validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    resources = {
        "stage": "input-validation",
        "workers": 1,
        "result": {key: result[key] for key in (
            "cases_checked", "expected_rejections", "unexpected_acceptances")},
        "cpu_seconds": time.process_time() - start_cpu,
        "wall_seconds": time.perf_counter() - start_wall,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (ROOT / "results" / "input-validation-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resources, sort_keys=True))


if __name__ == "__main__":
    main()
