"""Shared exact parsing and finite-poset utilities.

This module contains no optimizer.  The producer and the optimizer-free replay
checker use the same input syntax, but the checker re-establishes every
certificate equation with fractions.
"""
import json
from fractions import Fraction
from math import lcm
from pathlib import Path

F = Fraction

class InputError(ValueError):
    pass


def rat(value):
    if type(value) is int:
        out = F(value)
    else:
        if not isinstance(value, str) or not value or len(value) > 160:
            raise InputError("rational must be an integer or short string")
        if any(ch not in "-0123456789/" for ch in value):
            raise InputError("invalid rational syntax")
        try:
            out = F(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise InputError("invalid rational") from exc
    if out.numerator.bit_length() > 256 or out.denominator.bit_length() > 256:
        raise InputError("rational bit limit exceeded")
    return out


def parse_task(task):
    if not isinstance(task, dict) or set(task) != {"boundary", "poset", "old", "new"}:
        raise InputError("task keys must be boundary, poset, old, new")
    boundary = task["boundary"]
    if not isinstance(boundary, list) or not (1 <= len(boundary) <= 4):
        raise InputError("boundary must contain one to four labels")
    if any(not isinstance(x, str) or not x or len(x) > 40 for x in boundary):
        raise InputError("invalid boundary label")
    if len(set(boundary)) != len(boundary):
        raise InputError("duplicate boundary label")

    poset = task["poset"]
    if not isinstance(poset, dict) or set(poset) != {"outcomes", "leq"}:
        raise InputError("poset keys must be outcomes and leq")
    outcomes = poset["outcomes"]
    if not isinstance(outcomes, list) or not (2 <= len(outcomes) <= 8):
        raise InputError("poset must contain two to eight outcomes")
    if any(not isinstance(x, str) or not x or len(x) > 40 for x in outcomes):
        raise InputError("invalid outcome label")
    if len(set(outcomes)) != len(outcomes):
        raise InputError("duplicate outcome label")
    n = len(outcomes)
    leq_raw = poset["leq"]
    if not isinstance(leq_raw, list) or len(leq_raw) != n:
        raise InputError("leq matrix dimension mismatch")
    leq = []
    for row in leq_raw:
        if (not isinstance(row, list) or len(row) != n or
                any(not (type(x) is bool or (type(x) is int and x in (0, 1))) for x in row)):
            raise InputError("leq matrix must contain only Boolean values or integer 0/1")
        leq.append(tuple(bool(x) for x in row))
    leq = tuple(leq)
    for i in range(n):
        if not leq[i][i]:
            raise InputError("leq must be reflexive")
        for j in range(n):
            if i != j and leq[i][j] and leq[j][i]:
                raise InputError("leq must be antisymmetric")
            for k in range(n):
                if leq[i][j] and leq[j][k] and not leq[i][k]:
                    raise InputError("leq must be transitive")

    k = len(boundary)
    def parse_contract(obj, name):
        if not isinstance(obj, dict) or set(obj) != {"generators"}:
            raise InputError(f"{name} must contain generators")
        gs = obj["generators"]
        if not isinstance(gs, list) or not (1 <= len(gs) <= 6):
            raise InputError(f"{name} must have one to six generators")
        parsed = []
        for g in gs:
            if not isinstance(g, dict) or set(g) != {"mass"}:
                raise InputError("generator must contain mass")
            mass = g["mass"]
            if not isinstance(mass, list) or len(mass) != k:
                raise InputError("mass boundary dimension mismatch")
            rows = []
            for row in mass:
                if not isinstance(row, list) or len(row) != n:
                    raise InputError("mass outcome dimension mismatch")
                vals = tuple(rat(x) for x in row)
                if any(x < 0 for x in vals):
                    raise InputError("negative mass")
                rows.append(vals)
            if sum(sum(row) for row in rows) != 1:
                raise InputError("generator mass must sum to one")
            parsed.append(tuple(rows))
        priors = [tuple(sum(row) for row in g) for g in parsed]
        if any(p != priors[0] for p in priors[1:]):
            raise InputError(f"{name} generators must share one boundary prior")
        return tuple(parsed), priors[0]

    old, p_old = parse_contract(task["old"], "old")
    new, p_new = parse_contract(task["new"], "new")
    if p_old != p_new:
        raise InputError("old and new boundary priors differ")
    denominator = lcm(*(x.denominator for g in old + new for row in g for x in row))
    if denominator > 2**20:
        raise InputError("input common denominator exceeds 1048576")
    return tuple(boundary), tuple(outcomes), leq, old, new, p_old


def read_json(path):
    """Load one bounded UTF-8 JSON file and reject duplicate object keys."""
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 2**20:
        raise InputError("file missing or exceeds one MiB")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise InputError("duplicate JSON key")
            out[key] = value
        return out

    try:
        return json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError("invalid JSON") from exc


def upward_sets(leq):
    """Return nonempty up-sets as tuples of indices, deterministically."""
    n = len(leq)
    out = []
    for mask in range(1, 1 << n):
        ok = True
        for x in range(n):
            if mask & (1 << x):
                for y in range(n):
                    if leq[x][y] and not (mask & (1 << y)):
                        ok = False
                        break
            if not ok:
                break
        if ok:
            out.append(tuple(i for i in range(n) if mask & (1 << i)))
    return tuple(out)


def mix(generators, weights):
    k, n = len(generators[0]), len(generators[0][0])
    return tuple(tuple(sum(w * g[s][x] for w, g in zip(weights, generators))
                       for x in range(n)) for s in range(k))


def upset_mass(mass, s, upset):
    return sum((mass[s][x] for x in upset), F(0))


def cost_bad(leq, x, y):
    return F(0) if leq[x][y] else F(1)
