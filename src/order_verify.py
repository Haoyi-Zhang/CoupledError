"""Optimizer-free exact replay for finite order-coupling certificates."""
import sys
from fractions import Fraction
from order_common import (F, InputError, mix, parse_task, rat, read_json,
                          upward_sets, upset_mass)

class Invalid(ValueError):
    pass

def require(test, message):
    if not test:
        raise Invalid(message)

def vec(values, length):
    require(isinstance(values, list) and len(values) == length, "vector length mismatch")
    return tuple(rat(x) for x in values)

def replay(task, cert):
    boundary, outcomes, leq, old, new, prior = parse_task(task)
    require(isinstance(cert, dict) and set(cert) == {"kind", "value", "proofs", "worst_generator", "witness"},
            "invalid certificate keys")
    require(cert["kind"] == "order-coupling-loss", "wrong certificate kind")
    require(isinstance(cert["proofs"], list) and len(cert["proofs"]) == len(new), "proof count mismatch")
    k, n = len(boundary), len(outcomes)
    upsets = upward_sets(leq)
    values = []
    for target, proof in zip(new, cert["proofs"]):
        require(isinstance(proof, dict) and set(proof) == {"value", "lambda", "row_deficit", "transport", "dual_alpha", "dual_weights"},
                "invalid target proof keys")
        lam = vec(proof["lambda"], len(old))
        require(all(x >= 0 for x in lam) and sum(lam) == 1, "invalid convex weights")
        old_mix = mix(old, lam)
        deficit = vec(proof["row_deficit"], k)
        require(all(x >= 0 for x in deficit), "negative row deficit")
        for s in range(k):
            for U in upsets:
                require(deficit[s] >= upset_mass(old_mix, s, U)-upset_mass(target, s, U),
                        "primal upset inequality violated")
        transports = proof["transport"]
        require(isinstance(transports, list) and len(transports) == k, "transport boundary dimension mismatch")
        bad = F(0)
        for s in range(k):
            require(isinstance(transports[s], list) and len(transports[s]) == n, "transport row dimension mismatch")
            plan = [vec(row, n) for row in transports[s]]
            require(all(x >= 0 for row in plan for x in row), "negative transport mass")
            for x in range(n):
                require(sum(plan[x]) == old_mix[s][x], "transport old marginal mismatch")
            for y in range(n):
                require(sum(plan[x][y] for x in range(n)) == target[s][y], "transport target marginal mismatch")
            row_bad = sum(plan[x][y] for x in range(n) for y in range(n)
                          if not leq[x][y])
            require(row_bad == deficit[s], "transport row bad mass/deficit mismatch")
            bad += row_bad
        alpha = rat(proof["dual_alpha"])
        zw = proof["dual_weights"]
        require(isinstance(zw, list) and len(zw) == k, "dual boundary dimension mismatch")
        z = [vec(row, len(upsets)) for row in zw]
        require(all(v >= 0 for row in z for v in row), "negative dual weight")
        for s in range(k):
            require(sum(z[s]) <= 1, "dual row budget exceeded")
        for g in old:
            require(alpha <= sum(upset_mass(g, s, U)*z[s][ui]
                                 for s in range(k) for ui, U in enumerate(upsets)),
                    "dual old-generator inequality violated")
        dual_value = alpha - sum(upset_mass(target, s, U)*z[s][ui]
                                 for s in range(k) for ui, U in enumerate(upsets))
        value = rat(proof["value"])
        require(value == sum(deficit) == bad == dual_value, "primal/transport/dual objective mismatch")
        require(F(0) <= value <= F(1), "loss outside [0,1]")
        values.append(value)
    claimed = rat(cert["value"])
    require(claimed == max(values), "global maximum mismatch")
    idx = cert["worst_generator"]
    require(type(idx) is int and 0 <= idx < len(new) and values[idx] == claimed,
            "invalid worst generator")
    witness = cert["witness"]
    require(isinstance(witness, dict) and set(witness) == {"frame", "monitor", "new_floor", "old_floor"},
            "invalid witness")
    require(witness["frame"] == "target-law" and witness["monitor"] == "1[x-not-leq-y]",
            "wrong witness description")
    require(rat(witness["new_floor"]) == 0 and rat(witness["old_floor"]) == claimed,
            "witness floors mismatch")
    return claimed

def main():
    if len(sys.argv) != 3:
        print("usage: python src/order_verify.py TASK.json CERTIFICATE.json", file=sys.stderr)
        return 2
    try:
        value = replay(read_json(sys.argv[1]), read_json(sys.argv[2]))
        print(f"ACCEPT: exact order-coupling contextual loss = {value}")
        return 0
    except (Invalid, InputError, OSError, TypeError, KeyError, IndexError) as exc:
        print("REJECT: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
