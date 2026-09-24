"""Independent exhaustive contextual oracle for a tiny binary fragment.

This script implements the semantic definition directly for one boundary,
a two-outcome chain, denominator-three laws, binary frame alphabets, and every
monotone reward with values in {0, 1/2, 1}.  The Boolean monitors are retained
as a distinguished subset.  It does not import the production order code.
Because the Boolean target-law witness is included among the enumerated
contexts, both the Boolean and bounded-reward contextual maxima can be
compared with the order-deficiency formula for every nonempty pair of finite
contracts on this grid.

The result is a bounded finite cross-check, not a proof of the general theorem.
"""
from __future__ import annotations

import itertools
import json
import os
import resource
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENOMINATOR = 3
REWARD_DENOMINATOR = 2


def couplings(left_success: int, right_success: int):
    """Enumerate all 2x2 integer couplings with the requested marginals."""
    d = DENOMINATOR
    # table[x][r], with index 1 denoting success
    lower = max(0, left_success + right_success - d)
    upper = min(left_success, right_success)
    for both_success in range(lower, upper + 1):
        yield (
            (d - left_success - right_success + both_success,
             right_success - both_success),
            (left_success - both_success, both_success),
        )


def monotone_rewards():
    """All h(x,r) in {0,1/2,1}, monotone in x for each frame value.

    Rewards are represented by numerators over REWARD_DENOMINATOR.
    """
    levels = tuple(range(REWARD_DENOMINATOR + 1))
    columns = tuple((low, high) for low in levels for high in levels if low <= high)
    for col0, col1 in itertools.product(columns, repeat=2):
        # h[x][r]
        yield ((col0[0], col1[0]), (col0[1], col1[1]))


def is_boolean_reward(reward) -> bool:
    return all(value in (0, REWARD_DENOMINATOR)
               for row in reward for value in row)


def point_floor(component_success: int, frame_success: int, reward) -> int:
    """Return the minimum expected reward numerator in units 1/(3*2)."""
    return min(
        sum(table[x][r] * reward[x][r] for x in (0, 1) for r in (0, 1))
        for table in couplings(component_success, frame_success)
    )


def contract_floor(contract, frame_success: int, reward) -> int:
    return min(point_floor(law, frame_success, reward) for law in contract)


def point_deficiency(old_success: int, new_success: int) -> int:
    # Units of 1 / DENOMINATOR on the chain 0 < 1.
    return max(0, old_success - new_success)


def contract_formula(old_contract, new_contract) -> int:
    return max(
        min(point_deficiency(old, new) for old in old_contract)
        for new in new_contract
    )


def contextual_value(floors, oi: int, ni: int, frame_count: int, reward_indices) -> int:
    return max(
        max(0, floors[(oi, qi, hi)] - floors[(ni, qi, hi)])
        for qi in range(frame_count)
        for hi in reward_indices
    )


def main() -> None:
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    laws = tuple(range(DENOMINATOR + 1))
    contracts = tuple(
        tuple(laws[i] for i in range(len(laws)) if mask & (1 << i))
        for mask in range(1, 1 << len(laws))
    )
    rewards = tuple(monotone_rewards())
    boolean_indices = tuple(i for i, reward in enumerate(rewards)
                            if is_boolean_reward(reward))
    reward_indices = tuple(range(len(rewards)))

    # Precompute all robust floors from the semantic definition.
    floors = {
        (ci, qi, hi): contract_floor(contract, frame_success, reward)
        for ci, contract in enumerate(contracts)
        for qi, frame_success in enumerate(laws)
        for hi, reward in enumerate(rewards)
    }

    boolean_mismatches = []
    reward_mismatches = []
    value_histogram = {}
    for oi, old_contract in enumerate(contracts):
        for ni, new_contract in enumerate(contracts):
            boolean_contextual = contextual_value(
                floors, oi, ni, len(laws), boolean_indices)
            reward_contextual = contextual_value(
                floors, oi, ni, len(laws), reward_indices)
            # Context values are reward numerators over 3*2.  The formula is
            # in probability numerators over 3.
            formula = contract_formula(old_contract, new_contract)
            expected_scaled = REWARD_DENOMINATOR * formula
            value_histogram[str(formula)] = value_histogram.get(str(formula), 0) + 1
            if boolean_contextual != expected_scaled:
                boolean_mismatches.append({
                    "old": list(old_contract),
                    "new": list(new_contract),
                    "contextual_scaled_units": boolean_contextual,
                    "formula_scaled_units": expected_scaled,
                })
            if reward_contextual != expected_scaled:
                reward_mismatches.append({
                    "old": list(old_contract),
                    "new": list(new_contract),
                    "contextual_scaled_units": reward_contextual,
                    "formula_scaled_units": expected_scaled,
                })

    if boolean_mismatches or reward_mismatches:
        raise RuntimeError(
            "exhaustive contextual mismatch: " +
            json.dumps((boolean_mismatches + reward_mismatches)[:3])
        )

    coupling_tables = sum(
        sum(1 for _ in couplings(left, right))
        for left in laws for right in laws
    )
    result = {
        "model": (
            "one boundary; chain 0<1; binary frame; every monotone "
            "{0,1/2,1}-valued reward, with Boolean monitors checked separately"
        ),
        "denominator": DENOMINATOR,
        "reward_denominator": REWARD_DENOMINATOR,
        "point_laws": len(laws),
        "nonempty_finite_contracts": len(contracts),
        "contract_pairs": len(contracts) ** 2,
        "frame_laws": len(laws),
        "monotone_boolean_monitors": len(boolean_indices),
        "monotone_three_level_rewards": len(rewards),
        "boolean_contexts_enumerated": len(laws) * len(boolean_indices),
        "reward_contexts_enumerated": len(laws) * len(rewards),
        "distinct_component_frame_couplings": coupling_tables,
        "boolean_mismatches": 0,
        "reward_mismatches": 0,
        "mismatches": 0,
        "formula_value_histogram_in_units_of_one_third": value_histogram,
        "scope": "bounded exhaustive semantic cross-check; not a proof of the general theorem",
    }
    (ROOT / "results" / "context-exhaustive.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    resources_record = {
        "stage": "context-exhaustive",
        "workers": 1,
        "result": {key: result[key] for key in (
            "point_laws", "nonempty_finite_contracts", "contract_pairs",
            "boolean_contexts_enumerated", "reward_contexts_enumerated", "mismatches")},
        "cpu_seconds": time.process_time() - cpu_start,
        "wall_seconds": time.perf_counter() - wall_start,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (ROOT / "results" / "context-exhaustive-resources.json").write_text(
        json.dumps(resources_record, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
