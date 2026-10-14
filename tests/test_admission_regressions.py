"""Owned benign controls for optimized semantic gates and CLI proof identity."""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import semantic_boundaries as semantic
from compare_certificates import compare_order_record


class AdmissionRegressions(unittest.TestCase):
    def test_semantic_gate_survives_optimizer(self):
        # Erase both marginal maps: the supplied source no longer establishes
        # freshness. This must fail even if the interpreter removes assertions.
        with patch.object(semantic, "marginal", return_value={}):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises((AssertionError, RuntimeError)):
                    semantic.main()

    def test_prior_value_gate_survives_optimizer(self):
        original = semantic.replay
        def wrong_fiber(task, cert):
            value = original(task, cert)
            return 0 if len(cert["proofs"]) == 3 else value
        with patch.object(semantic, "replay", side_effect=wrong_fiber):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises((AssertionError, RuntimeError)):
                    semantic.main()

    def test_actual_cli_comparison_accepts_equivalent_proof(self):
        # Exercise the comparison expression in the actual orchestrator, not a
        # simulated LP. Only its read-only comparison gate is extracted.
        source = ast.parse((ROOT / "reproduce.py").read_text("utf-8"))
        main = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        gate = next(n for n in ast.walk(main) if isinstance(n, ast.If) and any(
            isinstance(c, ast.Constant) and c.value == "order command-line producer differs"
            for c in ast.walk(n)))
        task = json.loads((ROOT / "inputs/order-relational.json").read_text("utf-8"))
        base = json.loads((ROOT / "results/order-relational.certificate.json").read_text("utf-8"))
        other = copy.deepcopy(base)
        other["value"] = "2/8"  # same exact value; legal nonreduced syntax
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td)
            (run_root / "results").mkdir()
            (run_root / "inputs").mkdir()
            (run_root / "results/order-relational.certificate.json").write_text(json.dumps(base), "utf-8")
            (run_root / "inputs/order-relational.json").write_text(json.dumps(task), "utf-8")
            cert = run_root / "cli.json"
            cert.write_text(json.dumps(other), "utf-8")
            code = ast.fix_missing_locations(ast.Module(body=[gate], type_ignores=[]))
            namespace = {"json": json, "cert": cert, "run_root": run_root,
                         "compare_order_record": compare_order_record}
            exec(compile(code, "reproduce.py:actual-cli-comparison", "exec"), namespace)


if __name__ == "__main__":
    unittest.main()
