"""Equivalent exact dual witnesses pass; wrong objectives or inputs do not."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from compare_certificates import compare_order_certificates


class CertificateComparisonTests(unittest.TestCase):
    def setUp(self):
        self.old=json.loads((ROOT/'results/order-certificates.json').read_text())

    def test_valid_alternative_dual(self):
        other=copy.deepcopy(self.old)
        proof=other['random'][2]['certificate']['proofs'][2]
        proof['dual_weights'][0][:2]=['1','0']
        proof['dual_alpha']='1/3'
        self.assertEqual(compare_order_certificates(self.old,other),24)

    def test_invalid_alternative_dual_rejected(self):
        other=copy.deepcopy(self.old)
        other['random'][2]['certificate']['proofs'][2]['dual_alpha']='9'
        with self.assertRaises(ValueError): compare_order_certificates(self.old,other)

    def test_seed_drift_rejected(self):
        other=copy.deepcopy(self.old)
        other['random'][2]['seed']+=1
        with self.assertRaises(ValueError): compare_order_certificates(self.old,other)

    def test_missing_record_rejected(self):
        other=copy.deepcopy(self.old)
        other['random'].pop()
        with self.assertRaises(ValueError): compare_order_certificates(self.old,other)
