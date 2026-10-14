"""Run every locally available scientific stage, recording unavailable stages.

This is not a successful full numerical reproduction. The default complete
Linux/SciPy orchestrator remains reproduce.py. Explicit Windows portable mode
does not emulate POSIX limits. Historical evidence is copied, never overwritten.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from runtime_support import configure, capabilities, peak_rss_kib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    if args.portable:
        os.environ["COUPLEDERROR_PORTABLE"] = "1"
    configure()
    out = args.output_dir.resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError("output must be outside the artifact tree")
    out.mkdir(parents=True, exist_ok=False)
    scratch = out / "tmp"
    scratch.mkdir()
    # Keep all standard-library fixture scratch inside the chosen run. This is
    # child-local environment, never a machine/global environment mutation.
    for key in ("TEMP", "TMP", "TMPDIR"):
        os.environ[key] = str(scratch)
    logs = out / "logs"
    logs.mkdir()
    run_root = out / "artifact"
    shutil.copytree(ROOT, run_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    source_inventory = [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in sorted(ROOT.rglob("*")) if p.is_file() and
                        not any(part in {".git", "__pycache__", "evidence"} for part in p.relative_to(ROOT).parts)]
    (out / "consumed-inventory.json").write_text(json.dumps(source_inventory, indent=2) + "\n", "utf-8")
    initial_times = {p.name: p.stat().st_mtime_ns for p in (run_root / "results").glob("*") if p.is_file()}
    stages = [(["tests/pilot.py"], False)]
    stages += [(["tests/campaign.py", stage], False) for stage in ("grid", "stress", "pipeline", "controls")]
    stages += [(["tests/" + name + ".py"], needs_scipy) for name, needs_scipy in (
        ("randomization", False), ("order_campaign", True), ("poset_sweep", False),
        ("all_posets_exhaustive", False), ("data_processing_exhaustive", False),
        ("context_exhaustive", False), ("independent_contract_oracle", True),
        ("certificate_mutation", False), ("metamorphic_invariance", True),
        ("scaling_profile", True), ("input_validation", False), ("semantic_boundaries", False),
        ("coefficient_regression", False))]
    stages += [(["-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"], False)
               for pattern in ("test_reproduction_comparison.py", "test_admission_regressions.py", "test_transport_correspondence.py", "test_available_workflows.py")]
    stages += [(["tests/campaign.py", "replay"], False),
               (["tests/transport_cost.py", "--output-dir", str(out / "transport-cost")], False)]
    cli = out / "command-line"
    cli.mkdir()
    stages += [(["src/run.py", "inputs/boundary-sensitive.json", str(cli / "binary.json")], False),
               (["src/verify.py", "inputs/boundary-sensitive.json", str(cli / "binary.json")], False),
               (["src/run.py", "--source", "inputs/pipeline-model.json", str(cli / "source.json")], False),
               (["src/verify.py", str(cli / "source.task.json"), str(cli / "source.json")], False),
               (["src/order_run.py", "inputs/order-relational.json", str(cli / "order.json")], True),
               (["src/order_verify.py", "inputs/order-relational.json", "results/order-relational.certificate.json"], False),
               (["src/transport_verify.py", "inputs/order-relational.json", "results/order-relational.certificate.json",
                 "--convert-to", str(cli / "transport.json")], False),
               (["src/transport_verify.py", "inputs/order-relational.json", str(cli / "transport.json")], False),
               (["src/join_tree.py", "inputs/join-tree.json", str(cli / "join.json")], False),
               (["src/join_tree.py", "inputs/join-tree.json", str(cli / "join.json"), "--verify"], False)]
    scipy_available = importlib.util.find_spec("scipy") is not None
    records = []
    for index, (arguments, needs_scipy) in enumerate(stages, 1):
        command = [sys.executable, "-B", *(["-O"] if sys.flags.optimize else []), *arguments]
        record = {"argv": command, "requires_scipy": needs_scipy}
        if needs_scipy and not scipy_available:
            record.update(status="UNAVAILABLE", reason="SciPy not installed; no numerical production claimed")
        else:
            started = time.perf_counter()
            with (logs / f"{index:02d}.stdout.txt").open("w", encoding="utf-8") as stdout, \
                 (logs / f"{index:02d}.stderr.txt").open("w", encoding="utf-8") as stderr:
                proc = subprocess.run(command, cwd=run_root, stdout=stdout, stderr=stderr,
                                      env=os.environ.copy(), timeout=60, check=False)
            record.update(status="PASS" if proc.returncode == 0 else "FAIL", exit_code=proc.returncode,
                          wall_seconds=time.perf_counter() - started)
        records.append(record)
        (out / "stages.json").write_text(json.dumps(records, indent=2) + "\n", "utf-8")
        print(str(index) + ": " + record["status"] + " " + " ".join(arguments), flush=True)
    # Compare all regenerated scientific files; untouched files are not counted
    # as fresh comparisons. Order certificates are only retained replay inputs.
    volatile = {"cpu_seconds", "wall_seconds", "peak_rss_kib"}
    def scientific(value):
        if type(value) is dict:
            return {k: scientific(v) for k, v in value.items() if k not in volatile}
        if type(value) is list:
            return [scientific(v) for v in value]
        return value
    comparisons = []
    for path in sorted((run_root / "results").glob("*")):
        reference = ROOT / "results" / path.name
        if not path.is_file() or not reference.is_file() or path.name.endswith("-resources.json") or path.name == "reproduction.json":
            continue
        if path.stat().st_mtime_ns == initial_times.get(path.name):
            # Unchanged copied historical results are not fresh generation.
            continue
        if path.suffix == ".json":
            equal = scientific(json.loads(path.read_text("utf-8"))) == scientific(json.loads(reference.read_text("utf-8")))
            comparisons.append({"file": path.name, "scientific_equal": equal})
        elif path.suffix == ".csv":
            comparisons.append({"file": path.name, "scientific_equal": path.read_text("utf-8") == reference.read_text("utf-8")})
    result = {"python": sys.version, "os": platform.platform(), "optimize": sys.flags.optimize,
              "resource_capabilities": capabilities(), "peak_controller_rss_kib": peak_rss_kib(),
              "stages": records, "available_stages_passed": sum(r["status"] == "PASS" for r in records),
              "unavailable_stages": sum(r["status"] == "UNAVAILABLE" for r in records),
              "failures": sum(r["status"] == "FAIL" for r in records), "regenerated_file_comparisons": comparisons,
              "full_numerical_reproduction_complete": False,
              "temporary_fixture_root": str(scratch),
              "scope": "available owned finite stages only; not current Linux/SciPy reproduction or production deployment"}
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    return 1 if result["failures"] or any(not c["scientific_equal"] for c in comparisons) else 0


if __name__ == "__main__":
    raise SystemExit(main())
