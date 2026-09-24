"""Produce exact certificates for finite order-coupling contracts.

The floating-point LP is used only to locate a small rational optimum.  The
returned certificate is accepted only after exact rational primal, transport,
and dual checks.  Replay is performed by order_verify.py, which imports no
optimizer.
"""
import json
import sys
from collections import deque
from fractions import Fraction
from pathlib import Path

from order_common import (F, InputError, mix, parse_task, rat, read_json,
                          upward_sets, upset_mass)

try:
    from scipy.optimize import linprog
except Exception as exc:  # pragma: no cover - dependency failure is explicit
    raise SystemExit("order_run.py requires scipy.optimize.linprog") from exc


def qstr(x):
    return str(F(x))


def rationalize(x, max_den=1048576):
    if abs(x) < 1e-10:
        return F(0)
    return F(float(x)).limit_denominator(max_den)


def max_ordered_transport(left, right, leq):
    """Exact Edmonds--Karp flow on order edges, then complete residual coupling."""
    n = len(left)
    source, l0, r0, sink = 0, 1, 1+n, 1+2*n
    N = sink + 1
    cap = [[F(0) for _ in range(N)] for _ in range(N)]
    for x, value in enumerate(left):
        cap[source][l0+x] = value
    total = sum(left)
    for x in range(n):
        for y in range(n):
            if leq[x][y]:
                cap[l0+x][r0+y] = total
    for y, value in enumerate(right):
        cap[r0+y][sink] = value
    residual = [row[:] for row in cap]
    adjacency = [set() for _ in range(N)]
    for u in range(N):
        for v in range(N):
            if cap[u][v] > 0:
                adjacency[u].add(v); adjacency[v].add(u)
    while True:
        parent = [-1] * N
        parent[source] = source
        queue = deque([source])
        while queue and parent[sink] < 0:
            u = queue.popleft()
            for v in sorted(adjacency[u]):
                if parent[v] < 0 and residual[u][v] > 0:
                    parent[v] = u
                    queue.append(v)
                    if v == sink:
                        break
        if parent[sink] < 0:
            break
        aug = None
        v = sink
        while v != source:
            u = parent[v]
            aug = residual[u][v] if aug is None else min(aug, residual[u][v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= aug
            residual[v][u] += aug
            v = u
    plan = [[F(0) for _ in range(n)] for _ in range(n)]
    for x in range(n):
        for y in range(n):
            if leq[x][y]:
                plan[x][y] = cap[l0+x][r0+y] - residual[l0+x][r0+y]
    rem_l = [left[x] - sum(plan[x]) for x in range(n)]
    rem_r = [right[y] - sum(plan[x][y] for x in range(n)) for y in range(n)]
    x = y = 0
    while x < n and y < n:
        while x < n and rem_l[x] == 0:
            x += 1
        while y < n and rem_r[y] == 0:
            y += 1
        if x == n or y == n:
            break
        if leq[x][y]:
            raise ArithmeticError("maximum-flow residual still has an order edge")
        amount = min(rem_l[x], rem_r[y])
        plan[x][y] += amount
        rem_l[x] -= amount
        rem_r[y] -= amount
    if any(rem_l) or any(rem_r):
        raise ArithmeticError("transport completion failed")
    return tuple(tuple(row) for row in plan)


def solve_target(old, target, leq):
    k, n, m = len(target), len(target[0]), len(old)
    upsets = upward_sets(leq)
    # Primal variables: lambda_0..lambda_{m-1}, t_0..t_{k-1}.
    c = [0.0] * m + [1.0] * k
    A, b = [], []
    for s in range(k):
        for U in upsets:
            row = [float(upset_mass(g, s, U)) for g in old] + [0.0] * k
            row[m+s] = -1.0
            A.append(row)
            b.append(float(upset_mass(target, s, U)))
    result = linprog(c, A_ub=A, b_ub=b, A_eq=[[1.0]*m+[0.0]*k], b_eq=[1.0],
                     bounds=[(0, None)]*(m+k), method="highs")
    if not result.success:
        raise ArithmeticError("primal LP failed: " + result.message)
    lam = tuple(rationalize(x) for x in result.x[:m])
    # Normalize one tiny rational drift, then recompute exact minimal t.
    if sum(lam) != 1:
        j = max(range(m), key=lambda i: lam[i])
        lam = tuple(v + (F(1)-sum(lam)) if i == j else v for i, v in enumerate(lam))
    if any(x < 0 for x in lam):
        raise ArithmeticError("rationalized primal weight negative")
    old_mix = mix(old, lam)
    t = []
    for s in range(k):
        t.append(max([F(0)] + [upset_mass(old_mix, s, U)-upset_mass(target, s, U)
                               for U in upsets]))
    value = sum(t, F(0))

    # Dual variables z_(s,U)>=0 and alpha free.  Max alpha - n.z.
    z_count = k * len(upsets)
    dc = [float(upset_mass(target, s, U)) for s in range(k) for U in upsets] + [-1.0]
    dA, db = [], []
    for g in old:
        dA.append([-float(upset_mass(g, s, U)) for s in range(k) for U in upsets] + [1.0])
        db.append(0.0)
    for s in range(k):
        row = [0.0] * z_count + [0.0]
        for ui in range(len(upsets)):
            row[s*len(upsets)+ui] = 1.0
        dA.append(row)
        db.append(1.0)
    dual = linprog(dc, A_ub=dA, b_ub=db,
                   bounds=[(0, None)]*z_count+[(None, None)], method="highs")
    if not dual.success:
        raise ArithmeticError("dual LP failed: " + dual.message)
    zflat = [rationalize(x) for x in dual.x[:z_count]]
    z = tuple(tuple(zflat[s*len(upsets):(s+1)*len(upsets)]) for s in range(k))
    alpha = min(sum(upset_mass(g, s, U) * z[s][ui]
                    for s in range(k) for ui, U in enumerate(upsets)) for g in old)
    dual_value = alpha - sum(upset_mass(target, s, U) * z[s][ui]
                             for s in range(k) for ui, U in enumerate(upsets))
    if dual_value != value:
        # Degenerate HiGHS solutions occasionally rationalize poorly.  Recover
        # a sparse exact dual by enumerating one maximising upset per row.  This
        # covers the retained finite campaign and remains exactly checked.
        z = tuple(tuple(F(1) if ui == max(range(len(upsets)),
                    key=lambda j: upset_mass(old_mix, s, upsets[j])-upset_mass(target, s, upsets[j]))
                    and t[s] > 0 else F(0) for ui in range(len(upsets))) for s in range(k))
        alpha = min(sum(upset_mass(g, s, U) * z[s][ui]
                        for s in range(k) for ui, U in enumerate(upsets)) for g in old)
        dual_value = alpha - sum(upset_mass(target, s, U) * z[s][ui]
                                 for s in range(k) for ui, U in enumerate(upsets))
    if dual_value != value:
        raise ArithmeticError(f"could not recover exact dual: primal {value}, dual {dual_value}")

    transports = []
    bad = F(0)
    for s in range(k):
        plan = max_ordered_transport(old_mix[s], target[s], leq)
        transports.append(plan)
        bad += sum(plan[x][y] for x in range(n) for y in range(n) if not leq[x][y])
    if bad != value:
        raise ArithmeticError(f"transport/upset disagreement: {bad} != {value}")
    return {
        "value": qstr(value),
        "lambda": [qstr(x) for x in lam],
        "row_deficit": [qstr(x) for x in t],
        "transport": [[[qstr(x) for x in row] for row in plan] for plan in transports],
        "dual_alpha": qstr(alpha),
        "dual_weights": [[qstr(x) for x in row] for row in z],
    }


def certificate(task):
    boundary, outcomes, leq, old, new, prior = parse_task(task)
    proofs = [solve_target(old, target, leq) for target in new]
    values = [rat(p["value"]) for p in proofs]
    worst = max(range(len(values)), key=values.__getitem__)
    return {
        "kind": "order-coupling-loss",
        "value": qstr(values[worst]),
        "proofs": proofs,
        "worst_generator": worst,
        "witness": {
            "frame": "target-law",
            "monitor": "1[x-not-leq-y]",
            "new_floor": "0",
            "old_floor": qstr(values[worst]),
        },
    }


def main():
    if len(sys.argv) != 3:
        print("usage: python src/order_run.py TASK.json CERTIFICATE.json", file=sys.stderr)
        return 2
    try:
        task = read_json(sys.argv[1])
        cert = certificate(task)
        Path(sys.argv[2]).write_text(json.dumps(cert, indent=2)+"\n", encoding="utf-8")
        print("exact order-coupling certificate value = " + cert["value"])
        return 0
    except (InputError, OSError, ValueError, ArithmeticError, TypeError, KeyError) as exc:
        print("PRODUCER FAILED: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
