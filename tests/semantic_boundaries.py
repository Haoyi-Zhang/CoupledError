"""Exact regressions for freshness, prior fibers, and accepted rational syntax.

No optimizer or platform resource module is imported. These finite examples
test distinctions in the paper, not a universal theorem or deployed system.
"""
import copy
import json
import sys
from fractions import Fraction as F
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exact import certificate
from verify import replay
from order_common import parse_task, rat
from order_verify import replay as order_replay


def marginal(law, columns):
    out = {}
    for row in law:
        key = tuple(row[i] for i in columns)
        out[key] = out.get(key, F(0)) + row[-1]
    return {key: value for key, value in out.items() if value}


def main():
    # S,M,G,H. Fresh mode M is independent of frame H given S. The
    # ambient-correlated law has identical component and frame marginals.
    fresh = [(s, m, int(s == m), h, F(1, 8))
             for s, m, h in product((0, 1), repeat=3)]
    ambient = [(s, m, int(s == m), int(s != m), F(1, 4))
               for s, m in product((0, 1), repeat=2)]
    assert marginal(fresh, (0, 1, 2)) == marginal(ambient, (0, 1, 2))
    assert marginal(fresh, (0, 3)) == marginal(ambient, (0, 3))
    fresh_floor = sum(row[-1] for row in fresh if row[2] and row[3])
    ambient_floor = sum(row[-1] for row in ambient if row[2] and row[3])
    assert (fresh_floor, ambient_floor) == (F(1, 4), F(0))
    assert marginal(fresh, (0, 1, 3)) == {
        (s, m, h): F(1, 8) for s, m, h in product((0, 1), repeat=3)}
    assert marginal(ambient, (0, 1, 3)) != marginal(fresh, (0, 1, 3))
    # In each mode, G is fixed by S, so every compatible frame coupling
    # gives floor 1/4. Forgetting mode-frame freshness admits floor zero.
    point_floors = []
    for success in (["1/2", "0"], ["0", "1/2"]):
        task = {"old": {"states": 2, "vertices": [
                    {"p": ["1/2", "1/2"], "a": success}]},
                "new": {"states": 2, "vertices": [
                    {"p": ["1/2", "1/2"], "a": ["1/4", "1/4"]}]}}
        point_floors.append(replay(task, certificate(task)))
    assert point_floors == [F(1, 4), F(1, 4)]
    task["old"]["vertices"] = [
        {"p": ["1/2", "1/2"], "a": a}
        for a in (["1/2", "0"], ["0", "1/2"])]
    relaxed_floor = replay(task, certificate(task))
    assert relaxed_floor == 0

    # A variable-prior old mixture is constrained to the target fiber.
    # Dropping this equality admits the second old generator, giving zero
    # rather than the correct deficiency 1/2 at the fair target prior.
    variable = {
        "old": {"states": 2, "vertices": [
            {"p": ["1", "0"], "a": ["1", "0"]},
            {"p": ["0", "1"], "a": ["0", "0"]}]},
        "new": {"states": 2, "vertices": [
            {"p": ["1", "0"], "a": ["1", "0"]},
            {"p": ["0", "1"], "a": ["0", "0"]},
            {"p": ["1/2", "1/2"], "a": ["0", "0"]}]},
    }
    proof = certificate(variable)
    assert replay(variable, proof) == F(1, 2)
    assert proof["proofs"][2]["lambda"] == ["1/2", "1/2"]
    assert F(proof["proofs"][2]["value"]) == F(1, 2)
    unconstrained_endpoint = sum(max(F(0), F(c) - F(a)) for c, a in zip(
        variable["old"]["vertices"][1]["a"],
        variable["new"]["vertices"][2]["a"]))
    assert unconstrained_endpoint == 0

    order_task = json.loads((ROOT / "inputs/order-relational.json").read_text("utf-8"))
    order_cert = json.loads((ROOT / "results/order-relational.certificate.json").read_text("utf-8"))
    integer_task = copy.deepcopy(order_task)
    for side in ("old", "new"):
        for generator in integer_task[side]["generators"]:
            generator["mass"] = [[int(F(v)) if F(v).denominator == 1 else v
                                  for v in row] for row in generator["mass"]]
    assert parse_task(integer_task) == parse_task(order_task)
    nonreduced_cert = copy.deepcopy(order_cert)
    nonreduced_cert["value"] = "2/8"
    assert order_replay(integer_task, nonreduced_cert) == F(1, 4)
    assert rat("02/04") == F(1, 2)
    print(json.dumps({
        "fresh_mode_floor": str(fresh_floor),
        "averaged_all_coupling_floor": str(relaxed_floor),
        "ambient_correlated_witness_floor": str(ambient_floor),
        "same_component_and_frame_marginals": True,
        "variable_prior_fiber_value": str(F(proof["proofs"][2]["value"])),
        "incorrect_without_fiber_value": str(unconstrained_endpoint),
        "order_integer_and_nonreduced_rational_controls": "accepted exactly",
        "scope": "three finite semantic/syntax regression families, not a universal proof",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
