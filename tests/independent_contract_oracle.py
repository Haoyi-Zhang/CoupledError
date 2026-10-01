"""Exact differential oracle for two-generator finite order contracts.

The expected-value mathematics below independently reimplements upward-set
enumeration, one-dimensional convex minimization, and the two-action minimax
dual without importing production order helpers.  The executable differential
driver in ``main`` then imports and calls the production certificate generator
and replay checker.  Consequently that full driver requires SciPy through the
producer even though the oracle calculation itself uses only exact Fraction
arithmetic.  This is a finite cross-check, not a general proof.
"""
import itertools
import json
import os
import random
import resource
import sys
import time
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def upward_sets_independent(leq):
    n = len(leq)
    sets = [tuple()]  # supplies the zero affine function
    for mask in range(1, 1 << n):
        members = tuple(i for i in range(n) if mask & (1 << i))
        if all(not (mask & (1 << x)) or
               all(not leq[x][y] or (mask & (1 << y)) for y in range(n))
               for x in range(n)):
            sets.append(members)
    return tuple(sets)


def mass_on(row, subset):
    return sum((row[i] for i in subset), F(0))


def target_value_two_generators(old, target, leq):
    """Compute min_{lambda in [0,1]} deficiency exactly.

    Each row is the maximum of finitely many affine functions of lambda.
    The sum is convex and piecewise affine, so a minimum is attained at an
    endpoint or at an intersection of two row-affine functions.
    """
    if len(old) != 2:
        raise ValueError("independent oracle requires exactly two old generators")
    upsets = upward_sets_independent(leq)
    row_lines = []
    candidates = {F(0), F(1)}
    for s in range(len(target)):
        lines = []
        for subset in upsets:
            slope = mass_on(old[0][s], subset) - mass_on(old[1][s], subset)
            intercept = mass_on(old[1][s], subset) - mass_on(target[s], subset)
            lines.append((slope, intercept))
        row_lines.append(tuple(lines))
        for i, (a, b) in enumerate(lines):
            for c, d in lines[i + 1:]:
                if a == c:
                    continue
                point = (d - b) / (a - c)
                if F(0) <= point <= F(1):
                    candidates.add(point)

    def objective(lam):
        return sum(max(a * lam + b for a, b in lines) for lines in row_lines)

    values = {lam: objective(lam) for lam in candidates}
    optimum = min(values.values())
    minimizers = tuple(sorted(lam for lam, value in values.items() if value == optimum))
    # The minimizer set of a convex piecewise-affine function is an interval.
    # Candidate points contain every breakpoint and both endpoints, so the
    # first and last minimizing candidates are the exact interval endpoints.
    minimizer_interval = (minimizers[0], minimizers[-1])
    endpoint_values = (values[F(0)], values[F(1)])
    interior_optimum_exists = (minimizer_interval[0] < F(1) and
                               minimizer_interval[1] > F(0))
    # "Required" is deliberately stronger than "an interior optimum exists":
    # both supplied endpoints must be strictly worse than the optimum.
    interior_required = (endpoint_values[0] > optimum and
                         endpoint_values[1] > optimum)
    return {
        "value": optimum,
        "listed_minimizers": minimizers,
        "minimizer_interval": minimizer_interval,
        "endpoint_values": endpoint_values,
        "interior_optimum_exists": interior_optimum_exists,
        "interior_required": interior_required,
        "breakpoint_candidates": len(candidates),
    }



def pure_test_payoffs(old, target, leq):
    """Payoff vectors for deterministic row-indexed upward tests.

    One pure test chooses one upward set, including the empty set, in every
    boundary row.  Its two coordinates are the old-generator score minus the
    target score.  The empty choices ensure a nonnegative game value.
    """
    upsets = upward_sets_independent(leq)
    payoffs = set()
    for choices in itertools.product(upsets, repeat=len(target)):
        pair = tuple(
            sum(mass_on(old[i][s], choices[s]) - mass_on(target[s], choices[s])
                for s in range(len(target)))
            for i in range(2)
        )
        payoffs.add(pair)
    return tuple(sorted(payoffs))


def two_row_mixed_test_value(payoffs):
    """Exact max_mixed min_generator payoff for a two-row finite game.

    In two payoff dimensions, an optimum of max min(x_0,x_1) over the convex
    hull lies at a vertex or where an edge intersects the diagonal.  Enumerating
    every pair of pure payoff vectors therefore gives the exact mixed value.
    """
    if not payoffs:
        raise ValueError("at least one pure test is required")
    pure_value = max(min(pair) for pair in payoffs)
    mixed_value = pure_value
    mixed_witness = None
    candidates = len(payoffs)
    for i, left in enumerate(payoffs):
        for right in payoffs[i + 1:]:
            # theta*left + (1-theta)*right has equal coordinates.
            denominator = ((left[0] - left[1]) - (right[0] - right[1]))
            if denominator == 0:
                continue
            theta = (right[1] - right[0]) / denominator
            if not F(0) <= theta <= F(1):
                continue
            candidates += 1
            point = tuple(theta * left[j] + (F(1) - theta) * right[j]
                          for j in range(2))
            value = min(point)
            if value > mixed_value:
                mixed_value = value
                mixed_witness = (left, right, theta)
    return pure_value, mixed_value, mixed_witness, candidates


def test_game_values(old, target, leq):
    payoffs = pure_test_payoffs(old, target, leq)
    return (*two_row_mixed_test_value(payoffs), len(payoffs))


def parse_mass(generator):
    return tuple(tuple(F(value) for value in row) for row in generator["mass"])


def oracle_contract_value(task):
    leq = tuple(tuple(bool(value) for value in row) for row in task["poset"]["leq"])
    old = tuple(parse_mass(g) for g in task["old"]["generators"])
    targets = tuple(parse_mass(g) for g in task["new"]["generators"])
    target_records = tuple(target_value_two_generators(old, target, leq)
                           for target in targets)
    return max(record["value"] for record in target_records), target_records


def poset(name):
    if name == "chain2":
        outcomes = ["0", "1"]
        leq = [[1, 1], [0, 1]]
    elif name == "chain3":
        outcomes = ["0", "1", "2"]
        leq = [[1, 1, 1], [0, 1, 1], [0, 0, 1]]
    elif name == "square":
        outcomes = ["00", "01", "10", "11"]
        leq = [[int(all(int(a) <= int(b) for a, b in zip(x, y)))
                for y in outcomes] for x in outcomes]
    else:
        raise ValueError(name)
    return outcomes, leq


def composition(rng, total, parts):
    cuts = sorted(rng.randrange(total + 1) for _ in range(parts - 1))
    points = [0, *cuts, total]
    return [points[i + 1] - points[i] for i in range(parts)]


def random_task(seed):
    rng = random.Random(seed)
    kind = ("chain2", "chain3", "square")[seed % 3]
    outcomes, leq = poset(kind)
    k = 1 + (seed % 2)
    denominator = 6
    totals = [denominator] if k == 1 else [2 + (seed % 3), denominator - (2 + seed % 3)]

    def generator():
        return {"mass": [[str(F(value, denominator))
                           for value in composition(rng, total, len(outcomes))]
                          for total in totals]}

    return {
        "boundary": [f"s{i}" for i in range(k)],
        "poset": {"outcomes": outcomes, "leq": leq},
        "old": {"generators": [generator(), generator()]},
        "new": {"generators": [generator() for _ in range(1 + (seed % 3))]},
    }


def explicit_interior_task():
    return {
        "boundary": ["left", "right"],
        "poset": {"outcomes": ["fail", "success"], "leq": [[1, 1], [0, 1]]},
        "old": {"generators": [
            {"mass": [["0", "1/2"], ["1/2", "0"]]},
            {"mass": [["1/2", "0"], ["0", "1/2"]]},
        ]},
        "new": {"generators": [
            {"mass": [["1/4", "1/4"], ["1/4", "1/4"]]},
            {"mass": [["3/8", "1/8"], ["3/8", "1/8"]]},
        ]},
    }



def explicit_relational_task():
    """The paper's fixed-test/relational separation on the Boolean square."""
    outcomes, leq = poset("square")
    return {
        "boundary": ["s"],
        "poset": {"outcomes": outcomes, "leq": leq},
        "old": {"generators": [
            {"mass": [["0", "0", "1/2", "1/2"]]},
            {"mass": [["0", "1", "0", "0"]]},
        ]},
        "new": {"generators": [
            {"mass": [["0", "1/2", "1/2", "0"]]},
        ]},
    }


def constant_objective_regression():
    """A flat objective whose candidate list contains only the two endpoints."""
    leq = ((True, True), (False, True))
    law = ((F(1), F(0)),)
    record = target_value_two_generators((law, law), law, leq)
    return record


def assert_classification_regressions(cases):
    seed_task = dict(cases)["seed-813"]
    _, seed_targets = oracle_contract_value(seed_task)
    seed = seed_targets[0]
    if not (seed["minimizer_interval"] == (F(0), F(1, 4)) and
            seed["endpoint_values"] == (F(0), F(2, 3)) and
            seed["interior_optimum_exists"] and not seed["interior_required"]):
        raise RuntimeError("seed-813 interior classification regression")

    flat = constant_objective_regression()
    if not (flat["value"] == 0 and
            flat["minimizer_interval"] == (F(0), F(1)) and
            flat["endpoint_values"] == (F(0), F(0)) and
            flat["interior_optimum_exists"] and not flat["interior_required"]):
        raise RuntimeError("constant-objective interior classification regression")
    return {
        "seed_813": {
            "minimizer_interval": [str(x) for x in seed["minimizer_interval"]],
            "endpoint_values": [str(x) for x in seed["endpoint_values"]],
            "interior_optimum_exists": seed["interior_optimum_exists"],
            "interior_required": seed["interior_required"],
        },
        "constant_objective": {
            "minimizer_interval": [str(x) for x in flat["minimizer_interval"]],
            "endpoint_values": [str(x) for x in flat["endpoint_values"]],
            "interior_optimum_exists": flat["interior_optimum_exists"],
            "interior_required": flat["interior_required"],
        },
    }


def main():
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    start_cpu = time.process_time()
    start_wall = time.perf_counter()

    # The differential part imports production code only here. order_run imports
    # SciPy; the exact expectation/minimax routines above do not.
    from order_run import certificate  # candidate producer under test
    from order_verify import replay    # exact certificate replay under test

    cases = [
        ("explicit-interior", explicit_interior_task()),
        ("explicit-relational", explicit_relational_task()),
    ]
    cases.extend((f"seed-{seed}", random_task(seed)) for seed in range(811, 859))
    classification_regressions = assert_classification_regressions(cases)
    records = []
    target_count = 0
    listed_interior_candidate_targets = 0
    interior_optimum_exists_targets = 0
    interior_required_targets = 0
    endpoint_also_optimal_among_listed_interior_targets = 0
    both_endpoints_optimal_targets = 0
    pure_test_strict_gap_targets = 0
    mixed_test_duality_mismatches = []
    largest_pure_test_gap = F(0)
    mismatches = []
    for name, task in cases:
        expected, targets = oracle_contract_value(task)
        cert = certificate(task)
        accepted = replay(task, cert)
        produced_targets = tuple(F(proof["value"]) for proof in cert["proofs"])
        expected_targets = tuple(record["value"] for record in targets)
        leq = tuple(tuple(bool(value) for value in row) for row in task["poset"]["leq"])
        old = tuple(parse_mass(g) for g in task["old"]["generators"])
        target_masses = tuple(parse_mass(g) for g in task["new"]["generators"])
        game_records = []
        for target_mass, expected_target in zip(target_masses, expected_targets):
            pure_value, mixed_value, mixed_witness, game_candidates, pure_actions = \
                test_game_values(old, target_mass, leq)
            if mixed_value != expected_target:
                mixed_test_duality_mismatches.append({
                    "case": name,
                    "expected": str(expected_target),
                    "mixed_test": str(mixed_value),
                })
            gap = mixed_value - pure_value
            if gap > 0:
                pure_test_strict_gap_targets += 1
                largest_pure_test_gap = max(largest_pure_test_gap, gap)
            game_records.append({
                "pure_test_value": str(pure_value),
                "mixed_test_value": str(mixed_value),
                "strict_gap": str(gap),
                "pure_actions": pure_actions,
                "candidate_mixtures": game_candidates,
                "mixed_witness": None if mixed_witness is None else {
                    "left": [str(x) for x in mixed_witness[0]],
                    "right": [str(x) for x in mixed_witness[1]],
                    "left_weight": str(mixed_witness[2]),
                },
            })
        if accepted != expected or produced_targets != expected_targets:
            mismatches.append({
                "case": name,
                "oracle": str(expected),
                "certificate": str(accepted),
                "oracle_targets": [str(value) for value in expected_targets],
                "certificate_targets": [str(value) for value in produced_targets],
            })
        for target_record in targets:
            listed = any(F(0) < lam < F(1)
                         for lam in target_record["listed_minimizers"])
            endpoint_optimal = any(value == target_record["value"]
                                   for value in target_record["endpoint_values"])
            listed_interior_candidate_targets += int(listed)
            interior_optimum_exists_targets += int(
                target_record["interior_optimum_exists"])
            interior_required_targets += int(target_record["interior_required"])
            endpoint_also_optimal_among_listed_interior_targets += int(
                listed and endpoint_optimal)
            both_endpoints_optimal_targets += int(
                all(value == target_record["value"]
                    for value in target_record["endpoint_values"]))
        target_count += len(targets)
        records.append({
            "case": name,
            "poset": len(task["poset"]["outcomes"]),
            "boundary_rows": len(task["boundary"]),
            "targets": len(targets),
            "value": str(expected),
            "target_values": [str(record["value"]) for record in targets],
            "listed_minimizers": [[str(lam) for lam in record["listed_minimizers"]]
                                  for record in targets],
            "minimizer_intervals": [[str(x) for x in record["minimizer_interval"]]
                                    for record in targets],
            "endpoint_values": [[str(x) for x in record["endpoint_values"]]
                                for record in targets],
            "interior_optimum_exists": [record["interior_optimum_exists"]
                                        for record in targets],
            "interior_required": [record["interior_required"]
                                  for record in targets],
            "breakpoint_candidates": [record["breakpoint_candidates"]
                                      for record in targets],
            "test_game": game_records,
        })
    if mismatches:
        raise RuntimeError("independent contract oracle mismatch: " + json.dumps(mismatches[:3]))
    if mixed_test_duality_mismatches:
        raise RuntimeError("mixed-test minimax mismatch: " +
                           json.dumps(mixed_test_duality_mismatches[:3]))
    if interior_required_targets == 0:
        raise RuntimeError("campaign did not exercise a required interior old mixture")
    if pure_test_strict_gap_targets == 0:
        raise RuntimeError("campaign did not exercise a strict pure-test gap")

    result = {
        "method": ("mathematically independent exact piecewise-affine primal minimization "
                   "and two-payoff-dimensional mixed-test dual, differentially compared "
                   "with the SciPy-backed producer and exact replay checker"),
        "tasks": len(cases),
        "target_generators": target_count,
        "listed_interior_candidate_targets": listed_interior_candidate_targets,
        "interior_optimum_exists_targets": interior_optimum_exists_targets,
        "interior_required_targets": interior_required_targets,
        "endpoint_also_optimal_among_listed_interior_targets":
            endpoint_also_optimal_among_listed_interior_targets,
        "both_endpoints_optimal_targets": both_endpoints_optimal_targets,
        "pure_test_strict_gap_targets": pure_test_strict_gap_targets,
        "mixed_test_duality_mismatches": 0,
        "largest_pure_test_gap": str(largest_pure_test_gap),
        "mismatches": 0,
        "classification_regressions": classification_regressions,
        "cases": records,
        "scope": "finite cross-check; not a proof of the general contract theorem",
    }
    (ROOT / "results" / "independent-contract-oracle.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    resources = {
        "stage": "independent-contract-oracle",
        "workers": 1,
        "result": {key: result[key] for key in (
            "tasks", "target_generators", "listed_interior_candidate_targets",
            "interior_optimum_exists_targets", "interior_required_targets",
            "endpoint_also_optimal_among_listed_interior_targets",
            "both_endpoints_optimal_targets", "pure_test_strict_gap_targets",
            "mixed_test_duality_mismatches", "mismatches")},
        "cpu_seconds": time.process_time() - start_cpu,
        "wall_seconds": time.perf_counter() - start_wall,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (ROOT / "results" / "independent-contract-oracle-resources.json").write_text(
        json.dumps(resources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resources, sort_keys=True))


if __name__ == "__main__":
    main()
