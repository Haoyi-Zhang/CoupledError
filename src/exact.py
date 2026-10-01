"""Exact, finite arrangement enumeration for boundary-success contracts.

No floating-point solver, network access, or third-party dependencies are used.
The algorithms are deliberately exponential and intended for small interfaces.
"""
from fractions import Fraction as F
from itertools import combinations
from math import lcm


def rat(value):
    """Parse one bounded exact rational string."""
    if type(value) is not str or not value or len(value) > 160:
        raise ValueError('masses must be short exact rational strings')
    if any(c not in '-0123456789/' for c in value):
        raise ValueError('masses must be short exact rational strings')
    try:
        out = F(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError('invalid exact rational mass') from exc
    if out.numerator.bit_length() > 256 or out.denominator.bit_length() > 256:
        raise ValueError('rational bit limit exceeded')
    return out


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), F(0))


def solve(rows, rhs, n):
    """Solve a full-rank square rational system; return None if singular."""
    if len(rows) != n or len(rhs) != n:
        return None
    a = [list(row) + [b] for row, b in zip(rows, rhs)]
    for col in range(n):
        pivot = next((i for i in range(col, n) if a[i][col]), None)
        if pivot is None:
            return None
        a[col], a[pivot] = a[pivot], a[col]
        v = a[col][col]
        a[col] = [x/v for x in a[col]]
        for i in range(n):
            if i != col and a[i][col]:
                v = a[i][col]
                a[i] = [x-v*y for x, y in zip(a[i], a[col])]
    return tuple(row[-1] for row in a)


def rank(rows):
    if not rows:
        return 0
    a = [list(row) for row in rows]
    r = 0
    for c in range(len(a[0])):
        j = next((i for i in range(r, len(a)) if a[i][c]), None)
        if j is None:
            continue
        a[r], a[j] = a[j], a[r]
        v = a[r][c]
        a[r] = [x/v for x in a[r]]
        for i in range(r+1, len(a)):
            if a[i][c]:
                v = a[i][c]
                a[i] = [x-v*y for x, y in zip(a[i], a[r])]
        r += 1
        if r == len(a):
            break
    return r


def independent_indices(rows):
    selected = []
    for i, row in enumerate(rows):
        if rank([rows[j] for j in selected] + [row]) > len(selected):
            selected.append(i)
    return selected


def load_contract(obj):
    if set(obj) != {'states', 'vertices'}:
        raise ValueError('contract keys must be states and vertices')
    k = obj['states']
    if type(k) is not int or not 1 <= k <= 4:
        raise ValueError('one to four boundary states supported by this runner')
    vertices = []
    if not isinstance(obj['vertices'], list) or not 1 <= len(obj['vertices']) <= 5:
        raise ValueError('one to five supplied generators supported')
    for v in obj['vertices']:
        if set(v) != {'p', 'a'} or len(v['p']) != k or len(v['a']) != k:
            raise ValueError('invalid vertex shape')
        p = tuple(rat(x) for x in v['p'])
        a = tuple(rat(x) for x in v['a'])
        if sum(p) != 1 or any(not 0 <= x <= y for x,y in zip(a,p)):
            raise ValueError('invalid boundary-success masses')
        vertices.append((p,a))
    return tuple(vertices)


def equalities(old, p):
    m, k = len(old), len(p)
    rows = [tuple(F(1) for _ in old)]
    rows += [tuple(v[0][s] for v in old) for s in range(k)]
    rhs = [F(1)] + list(p)
    indices = independent_indices(rows)
    return rows, rhs, indices


def prior_witness(old, p):
    """Find a convex combination whose boundary marginal is p, or None."""
    rows, rhs, ii = equalities(old, p)
    m = len(old)
    units = [tuple(F(i==j) for j in range(m)) for i in range(m)]
    for active in combinations(range(m), m-len(ii)):
        lam = solve([rows[i] for i in ii]+[units[i] for i in active],
                    [rhs[i] for i in ii]+[F(0)]*len(active), m)
        if lam is not None and min(lam)>=0 and all(dot(r,lam)==b for r,b in zip(rows,rhs)):
            return lam
    return None


def deficit(old, p, target):
    """Compute min_{old at p} sum_s (a_s-target_s)_+, with exact certificate.

    Arrangement vertices enumerate all possible minima, including interior
    mixtures of supplied old generators. The independent dual enumeration
    finds a supporting certificate rather than trusting enumeration in replay.
    """
    m, k = len(old), len(p)
    rows, rhs, ii = equalities(old,p)
    units = [tuple(F(i==j) for j in range(m)) for i in range(m)]
    successes = [tuple(v[1][s] for v in old) for s in range(k)]
    cuts = units + successes
    values = [F(0)]*m + list(target)
    best = None
    examined = 0
    for active in combinations(range(m+k), m-len(ii)):
        examined += 1
        lam = solve([rows[i] for i in ii]+[cuts[i] for i in active],
                    [rhs[i] for i in ii]+[values[i] for i in active], m)
        if lam is None or min(lam)<0 or any(dot(r,lam)!=b for r,b in zip(rows,rhs)):
            continue
        slack = tuple(max(F(0),dot(a,lam)-t) for a,t in zip(successes,target))
        value = sum(slack)
        if best is None or value < best[0]:
            best = (value,lam,slack)
    if best is None:
        raise ValueError('boundary marginal outside contract domain')
    val, lam, slack = best
    # Dual variables are y for independent equality rows, then w in [0,1]^k.
    r = len(ii)
    lhs, bounds = [], []
    for j in range(m):
        lhs.append(tuple(rows[i][j] for i in ii) + tuple(-successes[s][j] for s in range(k)))
        bounds.append(F(0))
    for s in range(k):
        row = [F(0)]*(r+k); row[r+s] = F(1)
        lhs.append(tuple(row)); bounds.append(F(1))
        lhs.append(tuple(-x for x in row)); bounds.append(F(0))
    dual_examined = 0
    for active in combinations(range(len(lhs)), r+k):
        dual_examined += 1
        z = solve([lhs[i] for i in active],[bounds[i] for i in active],r+k)
        if z is None or any(dot(row,z)>b for row,b in zip(lhs,bounds)):
            continue
        objective = dot([rhs[i] for i in ii],z[:r])-dot(target,z[r:])
        if objective == val:
            y = [F(0)]*(k+1)
            for i,v in zip(ii,z[:r]):
                y[i]=v
            return {'value':str(val),'lambda':[str(x) for x in lam],
                    'slack':[str(x) for x in slack], 'y':[str(x) for x in y],
                    'w':[str(x) for x in z[r:]],
                    'primal_systems':examined,'dual_systems':dual_examined}
    raise ArithmeticError('no exact primal-dual match: algorithm or input defect')


def certificate(task):
    if type(task) is not dict or set(task) != {'old','new'}:
        raise ValueError('task keys must be old and new')
    old,new = load_contract(task['old']),load_contract(task['new'])
    denominator = lcm(*(x.denominator for p,a in old+new for x in p+a))
    if denominator > 65536:
        raise ValueError('input common denominator exceeds 65536')
    if len(old[0][0]) != len(new[0][0]):
        raise ValueError('boundary dimension mismatch')
    o2n = [prior_witness(new,p) for p,a in old]
    n2o = [prior_witness(old,p) for p,a in new]
    if any(x is None for x in o2n+n2o):
        raise ValueError('different admissible-prior domains')
    proofs = [deficit(old,p,a) for p,a in new]
    values = [F(pr['value']) for pr in proofs]
    worst = max(range(len(values)), key=values.__getitem__)
    p,a = new[worst]
    return {'kind':'contextual-loss', 'value':str(values[worst]),
            'old_to_new_prior':[[str(x) for x in q] for q in o2n],
            'new_to_old_prior':[[str(x) for x in q] for q in n2o],
            'proofs':proofs,'worst_vertex':worst,
            'context_success':[str(x-y) for x,y in zip(p,a)]}
