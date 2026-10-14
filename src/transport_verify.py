"""Exact ordinary transport-dual baseline for the same finite contract loss.

No optimizer, upward-set enumerator, or production replay helper is imported.
The strict task parser is shared. Signed potentials are dual variables, not
probabilities. This is classical finite LP duality, not a new distance.
"""
import copy
import json
from pathlib import Path
import sys
from order_common import F, InputError, parse_task, rat, read_json


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def vector(raw, n):
    require(type(raw) is list and len(raw) == n, "vector dimension")
    return tuple(rat(v) for v in raw)


def replay(task, cert):
    boundary, outcomes, leq, old, new, _ = parse_task(task)
    k, d, g = len(boundary), len(outcomes), len(old)
    require(type(cert) is dict and set(cert) == {
        "kind", "value", "proofs", "worst_generator", "witness"}, "certificate keys")
    require(cert["kind"] == "transport-potential-loss", "certificate kind")
    require(type(cert["proofs"]) is list and len(cert["proofs"]) == len(new), "proof count")
    values = []
    for target, proof in zip(new, cert["proofs"]):
        require(type(proof) is dict and set(proof) == {
            "value", "lambda", "transport", "alpha", "left", "right"}, "proof keys")
        lam = vector(proof["lambda"], g)
        require(all(v >= 0 for v in lam) and sum(lam) == 1, "mixture simplex")
        # Separate reconstruction and direct cell checks; no upset coefficients.
        mixture = [[sum(lam[i] * old[i][s][x] for i in range(g))
                    for x in range(d)] for s in range(k)]
        for field in ("transport", "left", "right"):
            require(type(proof[field]) is list and len(proof[field]) == k, field + " rows")
        a = [vector(row, d) for row in proof["left"]]
        b = [vector(row, d) for row in proof["right"]]
        primal = F(0)
        for s in range(k):
            require(type(proof["transport"][s]) is list and len(proof["transport"][s]) == d,
                    "transport rows")
            plan = [vector(row, d) for row in proof["transport"][s]]
            require(all(v >= 0 for row in plan for v in row), "negative transport")
            for x in range(d):
                require(sum(plan[x]) == mixture[s][x], "old marginal")
            for y in range(d):
                require(sum(plan[x][y] for x in range(d)) == target[s][y], "target marginal")
            for x in range(d):
                for y in range(d):
                    cost = F(not leq[x][y])
                    require(a[s][x] + b[s][y] <= cost, "cell dual inequality")
                    primal += cost * plan[x][y]
        alpha = rat(proof["alpha"])
        for generator in old:
            require(alpha <= sum(generator[s][x] * a[s][x]
                                 for s in range(k) for x in range(d)), "generator dual inequality")
        dual = alpha + sum(target[s][y] * b[s][y] for s in range(k) for y in range(d))
        value = rat(proof["value"])
        require(F(0) <= value <= 1 and value == primal == dual, "objective equality")
        values.append(value)
    value = rat(cert["value"])
    require(value == max(values), "outer maximum")
    worst = cert["worst_generator"]
    require(type(worst) is int and 0 <= worst < len(new) and values[worst] == value, "worst generator")
    witness = cert["witness"]
    require(type(witness) is dict and set(witness) == {"frame", "monitor", "new_floor", "old_floor"},
            "witness keys")
    require(witness["frame"] == "target-law" and witness["monitor"] == "1[x-not-leq-y]",
            "witness semantics")
    require(rat(witness["new_floor"]) == 0 and rat(witness["old_floor"]) == value, "witness floors")
    return value


def convert(task, source):
    """Untrusted proof conversion, followed by independent destination replay.

    Source feasibility is not presumed: invalid source data may fail conversion
    or yield a rejected destination. A valid destination proves the same parsed
    optimum irrespective of the converter. Conversion is included in costs.
    """
    # Only conversion imports the exponential enumerator, never replay.
    from order_common import upward_sets
    boundary, outcomes, leq, _, new, _ = parse_task(task)
    k, d = len(boundary), len(outcomes)
    upsets = upward_sets(leq)
    require(type(source) is dict and source.get("kind") == "order-coupling-loss", "source kind")
    require(type(source.get("proofs")) is list and len(source["proofs"]) == len(new), "source proof count")
    proofs = []
    for proof in source["proofs"]:
        require(type(proof) is dict, "source proof object")
        raw = proof["dual_weights"]
        require(type(raw) is list and len(raw) == k, "source dual rows")
        z = [vector(row, len(upsets)) for row in raw]
        a = [[sum(z[s][ui] for ui, U in enumerate(upsets) if x in U)
              for x in range(d)] for s in range(k)]
        proofs.append({"value": proof["value"], "lambda": copy.deepcopy(proof["lambda"]),
                       "transport": copy.deepcopy(proof["transport"]), "alpha": proof["dual_alpha"],
                       "left": [[str(v) for v in row] for row in a],
                       "right": [[str(-v) for v in row] for row in a]})
    cert = {"kind": "transport-potential-loss", "value": source["value"], "proofs": proofs,
            "worst_generator": source["worst_generator"], "witness": copy.deepcopy(source["witness"])}
    replay(task, cert)
    return cert


def main():
    if len(sys.argv) not in (3, 5) or (len(sys.argv) == 5 and sys.argv[3] != "--convert-to"):
        print("usage: transport_verify.py TASK CERT [--convert-to DEST]", file=sys.stderr)
        return 2
    try:
        task, cert = read_json(sys.argv[1]), read_json(sys.argv[2])
        if len(sys.argv) == 5:
            cert = convert(task, cert)
            destination = Path(sys.argv[4])
            # Never overwrite an existing proof or the input.
            with destination.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(cert, indent=2) + "\n")
        value = replay(task, cert)
        print("ACCEPT: exact transport-potential loss = " + str(value))
        return 0
    except (InputError, Invalid, ValueError, OSError, TypeError, KeyError, IndexError) as exc:
        print("REJECT: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
