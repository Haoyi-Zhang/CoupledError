"""Reproduce all finite evidence in an isolated worktree and compare it.

Run from the repository root: python3 reproduce.py
Replay-only verifiers and the self-contained finite enumerators use the Python
standard library.  The full orchestration also runs the SciPy-backed order
certificate producer and the differential contract driver that calls both the
producer and replay checker.  Every produced candidate is accepted only after
exact rational replay.  The supplied repository is never used as the
generation workspace: all stages run in a fresh isolated copy. With
--output-dir, raw logs and the resource record stay outside the supplied tree;
without it, the copy is temporary and the final volatile resource record is
written back to the supplied tree for compatibility with the original route.
"""
import argparse
from contextlib import nullcontext
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from compare_certificates import compare_order_certificates

ROOT = Path(__file__).resolve().parent
VOLATILE = {"cpu_seconds", "wall_seconds", "peak_rss_kib"}


def scientific(value):
    if isinstance(value, dict):
        return {key: scientific(item) for key, item in value.items()
                if key not in VOLATILE}
    if isinstance(value, list):
        return [scientific(item) for item in value]
    return value


def snapshot(base):
    out = {}
    for folder in ("inputs", "results"):
        for path in (base / folder).glob("*"):
            if (not path.is_file() or path.name.endswith("-resources.json") or
                    path.name == "reproduction.json"):
                continue
            if path.suffix == ".json":
                out[str(path.relative_to(base))] = scientific(
                    json.loads(path.read_text(encoding="utf-8")))
            elif path.suffix == ".csv":
                out[str(path.relative_to(base))] = path.read_text(encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        help="retain the isolated run tree and every stage stdout/stderr")
    args = parser.parse_args()
    output = args.output_dir.resolve() if args.output_dir else None
    if output:
        # Never overwrite a previous campaign or recursively copy this output.
        if output == ROOT or ROOT in output.parents:
            raise ValueError("output directory must be outside the artifact tree")
        output.mkdir(parents=True, exist_ok=False)
        (output / "logs").mkdir()
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))

    before = snapshot(ROOT)
    start = time.perf_counter()
    parent_start = time.process_time()
    child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    stages = []

    storage = (nullcontext(str(output)) if output else
               tempfile.TemporaryDirectory(prefix="compositional-reliability-reproduction-"))
    with storage as td:
        temp_root = Path(td)
        run_root = temp_root / "compositional-reliability"
        shutil.copytree(
            ROOT,
            run_root,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "reproduction.json"),
        )
        command_dir = temp_root / "command-line-checks"
        command_dir.mkdir()

        def execute(args, expected=0):
            stage_start = time.perf_counter()
            display = "python3 " + " ".join(str(arg) for arg in args)
            display = display.replace(str(temp_root), "<temporary-worktree>")
            index = len(stages) + 1
            log_base = output / "logs" / f"{index:02d}" if output else None
            if log_base:
                log_base.with_suffix(".command.txt").write_text(display + "\n", encoding="utf-8")
            try:
                if log_base:
                    # Stream directly to persistent files. Even an outer
                    # whole-run termination leaves the in-flight raw output.
                    with log_base.with_suffix(".stdout.txt").open("w", encoding="utf-8") as out, \
                            log_base.with_suffix(".stderr.txt").open("w", encoding="utf-8") as err:
                        completed = subprocess.run(
                            [sys.executable, "-B", *args], cwd=run_root,
                            stdout=out, stderr=err, text=True, timeout=40, check=False)
                    completed.stdout = log_base.with_suffix(".stdout.txt").read_text(encoding="utf-8")
                    completed.stderr = log_base.with_suffix(".stderr.txt").read_text(encoding="utf-8")
                else:
                    completed = subprocess.run(
                        [sys.executable, "-B", *args], cwd=run_root,
                        capture_output=True, text=True, timeout=40, check=False)
            except subprocess.TimeoutExpired as exc:
                if log_base:
                    log_base.with_suffix(".command.txt").write_text(display + "\nTIMEOUT\n", encoding="utf-8")
                    stages.append({"command": display,
                                   "wall_seconds": time.perf_counter() - stage_start,
                                   "expected_exit": expected, "exit_code": 124})
                    (output / "stages.json").write_text(json.dumps(stages, indent=2) + "\n", encoding="utf-8")
                raise
            stages.append({
                "command": display,
                "wall_seconds": time.perf_counter() - stage_start,
                "expected_exit": expected,
                "exit_code": completed.returncode,
            })
            if output:
                (output / "stages.json").write_text(json.dumps(stages, indent=2) + "\n", encoding="utf-8")
            if completed.returncode != expected:
                raise RuntimeError(
                    f"{display}: expected exit {expected}, got {completed.returncode}; "
                    f"stdout={completed.stdout!r}; stderr={completed.stderr!r}")
            if completed.stdout.strip() and expected == 0:
                print(completed.stdout.strip())

        execute(["tests/pilot.py"])
        for stage in ("grid", "stress", "pipeline", "controls"):
            execute(["tests/campaign.py", stage])
        execute(["tests/randomization.py"])
        execute(["tests/order_campaign.py"])
        execute(["tests/poset_sweep.py"])
        execute(["tests/all_posets_exhaustive.py"])
        execute(["tests/data_processing_exhaustive.py"])
        execute(["tests/context_exhaustive.py"])
        execute(["tests/independent_contract_oracle.py"])
        execute(["tests/certificate_mutation.py"])
        execute(["tests/metamorphic_invariance.py"])
        execute(["tests/scaling_profile.py"])
        execute(["tests/input_validation.py"])
        execute(["tests/semantic_boundaries.py"])
        execute(["-m","unittest","discover","-s","tests",
                 "-p","test_reproduction_comparison.py","-v"])
        execute(["tests/campaign.py", "replay"])

        replay_record = json.loads(
            (run_root / "results" / "replay-resources.json").read_text(encoding="utf-8"))
        if replay_record["result"]["certificates_replayed"] != 432:
            raise RuntimeError("unexpected legacy certificate count")
        order_record = json.loads(
            (run_root / "results" / "order-campaign.json").read_text(encoding="utf-8"))
        if (order_record["random_exact_certificates"] != 20 or
                len(order_record["retained_cases"]) != 4):
            raise RuntimeError("unexpected retained order-certificate count")
        dependency_record = order_record["dependency"]
        if (dependency_record["join_tree_global_cells"] != 8 or
                dependency_record["retained_certificate_cells"] != 8 or
                not dependency_record["generated_certificate_replayed"] or
                not dependency_record["retained_certificate_replayed"] or
                not dependency_record["retained_matches_generated"] or
                not dependency_record["single_cell_mutation_rejected"] or
                not dependency_record["mutation_used_isolated_copy"] or
                not dependency_record["retained_input_preserved"]):
            raise RuntimeError("unexpected join-tree replay gate result")
        poset_record = json.loads(
            (run_root / "results" / "poset-sweep.json").read_text(encoding="utf-8"))
        if (poset_record["posets"] != 6 or
                poset_record["ordered_pairs"] != 1116 or
                poset_record["triangle_triples"] != 19064 or
                poset_record["transport_upset_mismatches"] != 0 or
                poset_record["triangle_violations"] != 0 or
                poset_record["target_monitor_upward_violations"] != 0):
            raise RuntimeError("unexpected multi-poset sweep result")
        all_posets_record = json.loads(
            (run_root / "results" / "all-posets-exhaustive.json").read_text(
                encoding="utf-8"))
        if (all_posets_record["labeled_posets_by_size"] != {"2": 3, "3": 19, "4": 219} or
                all_posets_record["total_labeled_posets"] != 241 or
                all_posets_record["ordered_law_pairs"] != 22611 or
                all_posets_record["ordered_law_triples"] != 223185 or
                all_posets_record["flow_upward_set_mismatches"] != 0 or
                all_posets_record["triangle_violations"] != 0 or
                all_posets_record["target_monitor_upward_violations"] != 0):
            raise RuntimeError("unexpected exhaustive all-poset result")
        data_processing_record = json.loads(
            (run_root / "results" / "data-processing-exhaustive.json").read_text(
                encoding="utf-8"))
        if (data_processing_record["source_posets"] != 22 or
                data_processing_record["target_posets"] != 22 or
                data_processing_record["source_target_poset_pairs"] != 484 or
                data_processing_record["deterministic_monotone_maps"] != 4732 or
                data_processing_record["deterministic_law_pair_map_checks"] != 159957 or
                data_processing_record["deterministic_data_processing_violations"] != 0 or
                data_processing_record["stochastically_monotone_kernels"] != 24972 or
                data_processing_record["stochastic_law_pair_kernel_checks"] != 864081 or
                data_processing_record["stochastic_data_processing_violations"] != 0):
            raise RuntimeError("unexpected exhaustive data-processing result")
        context_record = json.loads(
            (run_root / "results" / "context-exhaustive.json").read_text(
                encoding="utf-8"))
        if (context_record["contract_pairs"] != 225 or
                context_record["boolean_contexts_enumerated"] != 36 or
                context_record["reward_contexts_enumerated"] != 144 or
                context_record["boolean_mismatches"] != 0 or
                context_record["reward_mismatches"] != 0 or
                context_record["mismatches"] != 0):
            raise RuntimeError("unexpected exhaustive-context result")
        independent_record = json.loads(
            (run_root / "results" / "independent-contract-oracle.json").read_text(
                encoding="utf-8"))
        if (independent_record["tasks"] != 50 or
                independent_record["target_generators"] != 99 or
                independent_record["listed_interior_candidate_targets"] != 31 or
                independent_record["interior_optimum_exists_targets"] != 58 or
                independent_record["interior_required_targets"] != 11 or
                independent_record[
                    "endpoint_also_optimal_among_listed_interior_targets"] != 20 or
                independent_record["both_endpoints_optimal_targets"] != 31 or
                independent_record["pure_test_strict_gap_targets"] != 9 or
                independent_record["mixed_test_duality_mismatches"] != 0 or
                independent_record["largest_pure_test_gap"] != "1/4" or
                independent_record["mismatches"] != 0):
            raise RuntimeError("unexpected independent contract-oracle result")
        regressions = independent_record["classification_regressions"]
        if (regressions["seed_813"]["minimizer_interval"] != ["0", "1/4"] or
                regressions["seed_813"]["endpoint_values"] != ["0", "2/3"] or
                not regressions["seed_813"]["interior_optimum_exists"] or
                regressions["seed_813"]["interior_required"] or
                regressions["constant_objective"]["minimizer_interval"] != ["0", "1"] or
                regressions["constant_objective"]["endpoint_values"] != ["0", "0"] or
                not regressions["constant_objective"]["interior_optimum_exists"] or
                regressions["constant_objective"]["interior_required"]):
            raise RuntimeError("interior-mixture classification regression")
        mutation_record = json.loads(
            (run_root / "results" / "certificate-mutation.json").read_text(
                encoding="utf-8"))
        if (mutation_record["certificates_mutated"] != 24 or
                mutation_record["mutations_attempted"] != 1636 or
                mutation_record["mutations_rejected"] != 1636 or
                mutation_record["unexpected_acceptances"] != 0):
            raise RuntimeError("unexpected certificate-mutation result")
        metamorphic_record = json.loads(
            (run_root / "results" / "metamorphic-invariance.json").read_text(
                encoding="utf-8"))
        if (metamorphic_record["named_tasks"] != 4 or
                metamorphic_record["transformed_tasks_checked"] != 18 or
                metamorphic_record["value_or_replay_failures"] != 0):
            raise RuntimeError("unexpected metamorphic-invariance result")
        scaling_record = json.loads(
            (run_root / "results" / "scaling-profile.json").read_text(
                encoding="utf-8"))
        if (scaling_record["cases_checked"] != 14 or
                scaling_record["supported_outcome_range"] != [2, 8] or
                scaling_record["maximum_nonempty_upward_sets"] != 255 or
                scaling_record["failures"] != 0):
            raise RuntimeError("unexpected scaling-profile result")
        validation_record = json.loads(
            (run_root / "results" / "input-validation.json").read_text(encoding="utf-8"))
        if (validation_record["cases_checked"] != 14 or
                validation_record["expected_rejections"] != 12 or
                validation_record["unexpected_acceptances"] != 0):
            raise RuntimeError("unexpected input-validation result")

        # Exercise every documented command-line route with outputs outside the
        # copied repository, then compare the scientific objects exactly.
        cert = command_dir / "certificate.json"
        execute(["src/run.py", "inputs/boundary-sensitive.json", str(cert)])
        execute(["src/verify.py", "inputs/boundary-sensitive.json", str(cert)])
        if json.loads(cert.read_text()) != json.loads(
                (run_root / "results" / "boundary-sensitive.certificate.json").read_text()):
            raise RuntimeError("command-line binary producer differs")

        execute(["src/run.py", "--source", "inputs/pipeline-model.json", str(cert)])
        execute(["src/verify.py", str(cert.with_suffix(".task.json")), str(cert)])
        if json.loads(cert.read_text()) != json.loads(
                (run_root / "results" / "pipeline.certificate.json").read_text()):
            raise RuntimeError("source command-line producer differs")

        execute(["src/order_run.py", "inputs/order-relational.json", str(cert)])
        execute(["src/order_verify.py", "inputs/order-relational.json", str(cert)])
        if json.loads(cert.read_text()) != json.loads(
                (run_root / "results" / "order-relational.certificate.json").read_text()):
            raise RuntimeError("order command-line producer differs")

        execute(["src/join_tree.py", "inputs/join-tree.json", str(cert)])
        execute(["src/join_tree.py", "inputs/join-tree.json", str(cert), "--verify"])
        generated_join = json.loads(cert.read_text())
        canonical_join = json.loads(
            (run_root / "results" / "dependency.certificate.json").read_text())
        retained_join_path = run_root / "results" / "join-tree.certificate.json"
        retained_join = json.loads(retained_join_path.read_text())
        if generated_join != canonical_join:
            raise RuntimeError("join-tree command-line producer differs")
        execute(["src/join_tree.py", "inputs/join-tree.json",
                 "results/join-tree.certificate.json", "--verify"])
        if retained_join != generated_join:
            raise RuntimeError("retained join-tree certificate differs from generation")
        mutated_join = json.loads(json.dumps(retained_join))
        first_cell = next(iter(mutated_join["law"]))
        mutated_join["law"][first_cell] = (
            "1/4" if mutated_join["law"][first_cell] != "1/4" else "1/3")
        mutated_path = command_dir / "join-tree-single-cell-mutated.json"
        mutated_path.write_text(json.dumps(mutated_join, indent=2) + "\n",
                                encoding="utf-8")
        execute(["src/join_tree.py", "inputs/join-tree.json", str(mutated_path),
                 "--verify"], expected=1)

        after = snapshot(run_root)

    certificate_key='results/order-certificates.json'
    certificates_compared=compare_order_certificates(before[certificate_key],after[certificate_key])
    differences = sorted(set(before) ^ set(after))
    differences += sorted(key for key in before.keys() & after.keys()
                          if key!=certificate_key and before[key] != after[key])
    if differences:
        raise RuntimeError("scientific reference mismatch: " + ", ".join(differences))

    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = (children.ru_utime + children.ru_stime -
                 child_start.ru_utime - child_start.ru_stime)
    record = {
        "scientific_files_compared": len(before),
        "scientific_mismatches": 0,
        "order_certificate_objects_exactly_replayed": certificates_compared,
        "order_witness_identity_required": False,
        "contextual_certificates_replayed": 456,
        "dependency_certificate_objects": 1,
        "dependency_generated_certificate_replays": 1,
        "dependency_retained_certificate_replays": 1,
        "dependency_retained_matches_generated": True,
        "dependency_single_cell_mutations_rejected": 1,
        "multi_poset_pairs": poset_record["ordered_pairs"],
        "multi_poset_triangle_triples": poset_record["triangle_triples"],
        "exhaustive_labeled_posets": all_posets_record["total_labeled_posets"],
        "exhaustive_all_poset_pairs": all_posets_record["ordered_law_pairs"],
        "exhaustive_all_poset_triples": all_posets_record["ordered_law_triples"],
        "exhaustive_deterministic_monotone_maps": data_processing_record["deterministic_monotone_maps"],
        "exhaustive_deterministic_data_processing_checks": data_processing_record["deterministic_law_pair_map_checks"],
        "exhaustive_stochastically_monotone_kernels": data_processing_record["stochastically_monotone_kernels"],
        "exhaustive_stochastic_data_processing_checks": data_processing_record["stochastic_law_pair_kernel_checks"],
        "exhaustive_context_contract_pairs": context_record["contract_pairs"],
        "exhaustive_boolean_contexts": context_record["boolean_contexts_enumerated"],
        "exhaustive_reward_contexts": context_record["reward_contexts_enumerated"],
        "independent_contract_oracle_tasks": independent_record["tasks"],
        "independent_contract_oracle_targets": independent_record["target_generators"],
        "independent_contract_oracle_listed_interior_candidates": independent_record["listed_interior_candidate_targets"],
        "independent_contract_oracle_interior_optimum_exists": independent_record["interior_optimum_exists_targets"],
        "independent_contract_oracle_interior_required": independent_record["interior_required_targets"],
        "independent_contract_oracle_endpoint_also_optimal_among_listed": independent_record["endpoint_also_optimal_among_listed_interior_targets"],
        "independent_contract_oracle_both_endpoints_optimal": independent_record["both_endpoints_optimal_targets"],
        "independent_contract_oracle_strict_pure_test_gaps": independent_record["pure_test_strict_gap_targets"],
        "certificate_mutations_rejected": mutation_record["mutations_rejected"],
        "metamorphic_transformed_tasks": metamorphic_record["transformed_tasks_checked"],
        "structural_scaling_cases": scaling_record["cases_checked"],
        "input_validation_cases": validation_record["cases_checked"],
        "input_validation_expected_rejections": validation_record["expected_rejections"],
        "one_worker": True,
        "isolated_temporary_worktree": True,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - parent_start + child_cpu,
        "peak_child_rss_kib": children.ru_maxrss,
        "parent_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "stages": stages,
        "scope": "finite exact reproduction, not a general mechanized proof or independent review",
    }
    record_path = (output / "reproduction.json" if output else
                   ROOT / "results" / "reproduction.json")
    record_path.write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key != "stages"},
                     sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print("REPRODUCTION FAILED: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
