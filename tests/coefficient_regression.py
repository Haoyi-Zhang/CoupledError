"""Portable finite replay regression; no optimizer, saved data, or private paths.

The reference enumerates unit-token couplings independently of production
transport/upset helpers. Duplicate old generators are intentional; retained
mixed-generator witnesses are a separate reproduction gate, not this oracle.
"""
import copy
import itertools
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import order_verify as checker


def subsets(order):
    n = len(order)
    choices = []
    for flags in itertools.product((False, True), repeat=n):
        members = tuple(i for i, flag in enumerate(flags) if flag)
        if members and all(not order[x][y] or flags[y]
                           for x in members for y in range(n)):
            choices.append(members)
    return sorted(choices, key=lambda U: sum(2 ** x for x in U))


def coupling(left, right, order, denominator):
    """Literal finite token matching, including all unordered residual pairs."""
    xs = tuple(x for x, count in enumerate(left) for _ in range(count))
    ys = tuple(y for y, count in enumerate(right) for _ in range(count))
    best = None
    for perm in sorted(set(itertools.permutations(ys))):
        bad = sum(not order[x][y] for x, y in zip(xs, perm))
        if best is None or bad < best[0]:
            table = [[F(0) for _ in right] for _ in left]
            for x, y in zip(xs, perm):
                table[x][y] += F(1, denominator)
            best = bad, table
    return F(best[0], denominator), best[1]


def reference(order, old, targets, denominator, copies=1):
    """Construct exact primal/transport/dual witnesses for a singleton hull."""
    U = subsets(order)
    proofs = []
    for target in targets:
        deficits, transports, weights = [], [], []
        alpha = F(0)
        for left, right in zip(old, target):
            bad, table = coupling(left, right, order, denominator)
            gaps = [F(sum(left[x] - right[x] for x in up), denominator)
                    for up in U]
            if bad != max([F(0), *gaps]):
                raise AssertionError("independent coupling/upset mismatch")
            z = [0] * len(U)
            if bad:
                index = gaps.index(bad)
                z[index] = 1
                alpha += F(sum(left[x] for x in U[index]), denominator)
            deficits.append(str(bad))
            transports.append([[str(x) for x in row] for row in table])
            weights.append(z)
        proofs.append({"value": str(sum(map(F, deficits))),
                       "lambda": ["1"] + ["0"] * (copies - 1),
                       "row_deficit": deficits, "transport": transports,
                       "dual_alpha": str(alpha), "dual_weights": weights})
    maximum = max(F(p["value"]) for p in proofs)
    cert = {"kind": "order-coupling-loss", "value": str(maximum),
            "proofs": proofs,
            "worst_generator": next(i for i, p in enumerate(proofs)
                                    if F(p["value"]) == maximum),
            "witness": {"frame": "target-law", "monitor": "1[x-not-leq-y]",
                        "new_floor": "0", "old_floor": str(maximum)}}
    mass = lambda rows: [[str(F(x, denominator)) for x in row] for row in rows]
    task = {"boundary": [f"s{i}" for i in range(len(old))],
            "poset": {"outcomes": [f"x{i}" for i in range(len(order))],
                      "leq": copy.deepcopy(order)},
            "old": {"generators": [{"mass": mass(old)} for _ in range(copies)]},
            "new": {"generators": [{"mass": mass(t)} for t in targets]}}
    return task, cert, maximum


def cases():
    for n, denominator in ((2, 4), (3, 2)):
        laws = [counts for counts in itertools.product(range(denominator + 1), repeat=n)
                if sum(counts) == denominator]
        orders = [[[int(x <= y) for y in range(n)] for x in range(n)],
                  [[int(x == y) for y in range(n)] for x in range(n)]]
        if n == 3:
            orders.append([[1, 1, 1], [0, 1, 0], [0, 0, 1]])
        for order in orders:
            for old, new in itertools.product(laws, repeat=2):
                yield reference(order, [old], [[new], [old]], denominator, 3)
    for kind in ("chain", "antichain"):
        order = [[int(x <= y if kind == "chain" else x == y)
                  for y in range(8)] for x in range(8)]
        old = [[0] * 7 + [2], [0] * 8, [0] * 7 + [2], [0] * 8]
        target = [[2] + [0] * 7, [0] * 8, [2] + [0] * 7, [0] * 8]
        yield reference(order, old, [target, old, target, old, target, old], 4, 6)


def invalid_cases():
    task, cert, _ = reference([[1, 1], [0, 1]], [[0, 4]], [[[4, 0]]], 4)
    edits = [
        (("proofs", 0, "lambda"), ["2"], "invalid convex weights"),
        (("proofs", 0, "row_deficit"), ["0"], "primal upset inequality violated"),
        (("proofs", 0, "transport"), [], "transport boundary dimension mismatch"),
        (("proofs", 0, "transport", 0, 0, 0), "1", "transport old marginal mismatch"),
        (("proofs", 0, "transport", 0, 1, 0), "-1", "negative transport mass"),
        (("proofs", 0, "dual_alpha"), "2", "dual old-generator inequality violated"),
        (("proofs", 0, "dual_weights", 0), ["-1", "0"], "negative dual weight"),
        (("proofs", 0, "dual_weights", 0), ["2", "0"], "dual row budget exceeded"),
        (("proofs", 0, "value"), "0", "primal/transport/dual objective mismatch"),
        (("value",), "0", "global maximum mismatch"),
        (("worst_generator",), False, "invalid worst generator"),
        (("witness", "monitor"), "other", "wrong witness description"),
        (("witness", "old_floor"), "0", "witness floors mismatch"),
    ]
    for path, value, error in edits:
        bad = copy.deepcopy(cert)
        obj = bad
        for key in path[:-1]:
            obj = obj[key]
        obj[path[-1]] = value
        yield copy.deepcopy(task), bad, error
    edits = [(("boundary",), [], "boundary must contain one to four labels"),
             (("poset", "leq", 0, 0), 1.0,
              "leq matrix must contain only Boolean values or integer 0/1"),
             (("old", "generators", 0, "mass", 0, 0), True,
              "rational must be an integer or short string"),
             (("old", "generators", 0, "mass", 0, 0), 1 << 256,
              "rational bit limit exceeded"),
             (("old", "generators", 0, "mass", 0), ["0"],
              "mass outcome dimension mismatch")]
    for path, value, error in edits:
        bad = copy.deepcopy(task)
        obj = bad
        for key in path[:-1]:
            obj = obj[key]
        obj[path[-1]] = value
        yield bad, copy.deepcopy(cert), error


class CoefficientRegression(unittest.TestCase):
    def test_finite_reference_and_all_inequalities(self):
        counts = []
        original = checker.require
        def traced(test, message):
            counts.append(message)
            return original(test, message)
        checker.require = traced
        try:
            for task, cert, expected in cases():
                counts.clear()
                self.assertEqual(checker.replay(task, cert), expected)
                self.assertEqual(counts.count("dual old-generator inequality violated"),
                                 len(cert["proofs"]) * len(task["old"]["generators"]))
                self.assertEqual(counts.count("primal upset inequality violated"),
                                 len(cert["proofs"]) * len(task["boundary"]) *
                                 len(subsets(task["poset"]["leq"])))
        finally:
            checker.require = original

    def test_malformed_first_diagnostics(self):
        for task, cert, expected in invalid_cases():
            with self.assertRaises(ValueError) as caught:
                checker.replay(task, cert)
            self.assertEqual(str(caught.exception), expected)

    def test_fresh_calls_mutable_input_and_rational_spellings(self):
        task, cert, expected = reference([[1, 1], [0, 1]], [[0, 4]], [[[4, 0]]], 4)
        self.assertEqual(checker.replay(task, cert), expected)
        task["old"]["generators"][0]["mass"][0][:] = ["4/4", "00/04"]
        _, fresh, zero = reference([[1, 1], [0, 1]], [[4, 0]], [[[4, 0]]], 4)
        self.assertEqual(checker.replay(task, fresh), zero)
        task["old"]["generators"][0]["mass"][0][:] = [0, 1]
        self.assertEqual(checker.replay(task, cert), expected)


if __name__ == "__main__":
    unittest.main()
