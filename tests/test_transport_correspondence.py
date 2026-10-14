"""Same-information transport baseline and small independent token oracle."""
import copy
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import transport_verify as ordinary
import order_run as producer
import order_common
from order_verify import replay as upset_replay


class TransportCorrespondence(unittest.TestCase):
    def records(self):
        data = json.loads((ROOT / "results/order-certificates.json").read_text("utf-8"))
        return list(data["retained"].values()) + data["random"]

    def test_complete_retained_contract_corpus(self):
        records = self.records()
        self.assertEqual(len(records), 24)
        for record in records:
            task, source = record["task"], record["certificate"]
            cert = ordinary.convert(task, source)
            with patch.object(order_common, "upward_sets", side_effect=AssertionError("forbidden enumeration")):
                self.assertEqual(ordinary.replay(task, cert), upset_replay(task, source))

    def test_small_literal_transport_oracle(self):
        # One owned three-outcome vee, two tokens. No production transport helper
        # supplies the expected minimum. This is one anchor, not a new grid.
        order = [[1, 1, 1], [0, 1, 0], [0, 0, 1]]
        left, right = (1, 2), (0, 1)
        expected = F(min(sum(not order[x][y] for x, y in zip(left, perm))
                         for perm in set(itertools.permutations(right))), 2)
        task = {"boundary": ["s"], "poset": {"outcomes": ["a", "b", "c"], "leq": order},
                "old": {"generators": [{"mass": [["0", "1/2", "1/2"]]}]},
                "new": {"generators": [{"mass": [["1/2", "1/2", "0"]]}]}}
        proof = {"value": "1/2", "lambda": ["1"], "alpha": "1",
                 "transport": [[["0", "0", "0"], ["0", "1/2", "0"], ["1/2", "0", "0"]]],
                 "left": [["0", "1", "1"]], "right": [["0", "-1", "-1"]]}
        cert = {"kind": "transport-potential-loss", "value": "1/2", "proofs": [proof],
                "worst_generator": 0, "witness": {"frame": "target-law", "monitor": "1[x-not-leq-y]",
                                                   "new_floor": "0", "old_floor": "1/2"}}
        self.assertEqual(ordinary.replay(task, cert), expected)

    def test_critical_negative_obligations(self):
        record = self.records()[0]
        task = record["task"]
        base = ordinary.convert(task, record["certificate"])
        edits = [("alpha", "9"), ("left", [["9"] * len(task["poset"]["outcomes"])])]
        for key, value in edits:
            bad = copy.deepcopy(base)
            bad["proofs"][0][key] = value
            with self.assertRaises(ValueError): ordinary.replay(task, bad)
        for field, value in (("value", "0"), ("worst_generator", False), ("proofs", [])):
            bad = copy.deepcopy(base)
            bad[field] = value
            with self.assertRaises(ValueError): ordinary.replay(task, bad)
        bad = copy.deepcopy(base)
        bad["proofs"][0]["transport"][0][0][0] = "1"
        with self.assertRaises(ValueError): ordinary.replay(task, bad)
        # A normalized law with a genuinely changed prior must be rejected.
        pipeline = next(r for r in self.records() if len(r["task"]["boundary"]) == 2)
        bad_task = copy.deepcopy(pipeline["task"])
        d = len(bad_task["poset"]["outcomes"])
        for target in bad_task["new"]["generators"]:
            target["mass"] = [["1"] + ["0"] * (d - 1), ["0"] * d]
        with self.assertRaisesRegex(ValueError, "boundary priors differ"):
            ordinary.replay(bad_task, ordinary.convert(pipeline["task"], pipeline["certificate"]))

    def test_nonmaximal_target_is_checked(self):
        record = next(r for r in self.records() if len(r["certificate"]["proofs"]) > 1)
        cert = ordinary.convert(record["task"], record["certificate"])
        other = (cert["worst_generator"] + 1) % len(cert["proofs"])
        cert["proofs"][other]["alpha"] = "9"
        with self.assertRaises(ValueError): ordinary.replay(record["task"], cert)

    def test_producer_replays_before_return(self):
        record = self.records()[0]
        task, cert = record["task"], record["certificate"]
        bad = copy.deepcopy(cert["proofs"][0])
        bad["dual_alpha"] = "9"
        with patch.object(producer, "solve_target", return_value=bad):
            with self.assertRaises(ValueError): producer.certificate(task)


if __name__ == "__main__":
    unittest.main()
