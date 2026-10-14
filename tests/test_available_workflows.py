"""Available dependency workflow and mathematics from the existing 50 tasks.

No new campaign is generated. The contract driver is not run and no numerical
production is claimed; its independently implemented exact functions are used.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from fractions import Fraction as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import join_tree
import independent_contract_oracle as oracle


class AvailableWorkflows(unittest.TestCase):
    def test_full_join_tree_consumer_and_negatives(self):
        task = join_tree.read_json(ROOT / "inputs/join-tree.json")
        generated = join_tree.certificate(task)
        retained = join_tree.read_json(ROOT / "results/join-tree.certificate.json")
        self.assertEqual(generated, retained)
        self.assertEqual(join_tree.replay(task, generated), 8)
        self.assertEqual(join_tree.replay(task, retained), 8)
        bad = copy.deepcopy(retained)
        cell = next(iter(bad["law"]))
        bad["law"][cell] = "1/4" if bad["law"][cell] != "1/4" else "1/3"
        with self.assertRaises(ValueError): join_tree.replay(task, bad)
        for name in ("join-cycle-negative.json", "join-separator-negative.json"):
            with self.assertRaises(ValueError): join_tree.certificate(join_tree.read_json(ROOT / "inputs" / name))

    def test_all_existing_contract_math_without_numerical_production(self):
        retained = json.loads((ROOT / "results/independent-contract-oracle.json").read_text("utf-8"))
        cases = [("explicit-interior", oracle.explicit_interior_task()),
                 ("explicit-relational", oracle.explicit_relational_task())]
        cases += [(f"seed-{s}", oracle.random_task(s)) for s in range(811, 859)]
        expected = {r["case"]: r for r in retained["cases"]}
        self.assertEqual(set(expected), {name for name, _ in cases})
        oracle.assert_classification_regressions(cases)
        count, required, gaps = 0, 0, 0
        for name, task in cases:
            value, targets = oracle.oracle_contract_value(task)
            self.assertEqual(value, F(expected[name]["value"]))
            self.assertEqual([str(t["value"]) for t in targets], expected[name]["target_values"])
            leq = tuple(tuple(bool(v) for v in row) for row in task["poset"]["leq"])
            old = tuple(oracle.parse_mass(g) for g in task["old"]["generators"])
            for target, witness in zip(task["new"]["generators"], targets):
                pure, mixed, _, _, _ = oracle.test_game_values(old, oracle.parse_mass(target), leq)
                self.assertEqual(mixed, witness["value"])
                gaps += pure < mixed
                required += witness["interior_required"]
                count += 1
        self.assertEqual((len(cases), count, required, gaps), (50, 99, 11, 9))


if __name__ == "__main__":
    unittest.main()
