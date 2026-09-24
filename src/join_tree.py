"""Exact join-tree extension and replay for small finite binary marginals."""
import json
import sys
from collections import defaultdict, deque
from fractions import Fraction
from itertools import product
from pathlib import Path

F = Fraction


class Invalid(ValueError):
    pass


def rat(value):
    if not isinstance(value, str) or not value or len(value) > 160:
        raise Invalid("rational must be a short string")
    if any(char not in "-0123456789/" for char in value):
        raise Invalid("invalid rational syntax")
    try:
        out = F(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise Invalid("invalid rational") from exc
    if out.numerator.bit_length() > 256 or out.denominator.bit_length() > 256:
        raise Invalid("rational bit limit exceeded")
    return out


def parse_assignment(text, width):
    if (not isinstance(text, str) or len(text) != width or
            any(char not in "01" for char in text)):
        raise Invalid("assignments must be binary strings")
    return tuple(int(char) for char in text)


def marginalize(law, positions):
    out = defaultdict(F)
    for assignment, value in law.items():
        out[tuple(assignment[i] for i in positions)] += value
    return dict(out)


def parse_task(task):
    expected = {"variables", "bags", "tree_edges", "marginals"}
    if not isinstance(task, dict) or set(task) != expected:
        raise Invalid("invalid join-tree task keys")

    variables = task["variables"]
    if not isinstance(variables, list) or not (2 <= len(variables) <= 8):
        raise Invalid("variables must contain two to eight labels")
    if any(not isinstance(v, str) or not v or len(v) > 40 for v in variables):
        raise Invalid("invalid variable label")
    if len(set(variables)) != len(variables):
        raise Invalid("duplicate variable label")

    bags = task["bags"]
    if not isinstance(bags, list) or not (1 <= len(bags) <= 7):
        raise Invalid("invalid bags")
    index = {value: i for i, value in enumerate(variables)}
    parsed_bags = []
    for bag in bags:
        if not isinstance(bag, list) or not bag:
            raise Invalid("invalid bag")
        if any(not isinstance(v, str) or v not in index for v in bag):
            raise Invalid("bag contains an unknown variable")
        if len(set(bag)) != len(bag):
            raise Invalid("duplicate variable in bag")
        parsed_bags.append(tuple(index[v] for v in bag))

    edges = task["tree_edges"]
    if not isinstance(edges, list) or len(edges) != len(bags) - 1:
        raise Invalid("tree must have bags-1 edges")
    adj = [[] for _ in bags]
    canonical_edges = set()
    parsed_edges = []
    for edge in edges:
        if (not isinstance(edge, list) or len(edge) != 2 or
                any(type(x) is not int or x < 0 or x >= len(bags) for x in edge) or
                edge[0] == edge[1]):
            raise Invalid("invalid tree edge")
        a, b = edge
        canonical = tuple(sorted((a, b)))
        if canonical in canonical_edges:
            raise Invalid("duplicate tree edge")
        canonical_edges.add(canonical)
        parsed_edges.append((a, b))
        adj[a].append(b)
        adj[b].append(a)

    seen = {0}
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    if len(seen) != len(bags):
        raise Invalid("bag graph is not a tree")

    # Running intersection: bags containing each variable induce a connected subtree.
    for variable in range(len(variables)):
        containing = [i for i, bag in enumerate(parsed_bags) if variable in bag]
        if not containing:
            raise Invalid("every variable must occur in a bag")
        allowed = set(containing)
        reached = {containing[0]}
        queue = deque([containing[0]])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v in allowed and v not in reached:
                    reached.add(v)
                    queue.append(v)
        if reached != allowed:
            raise Invalid("running-intersection property fails")

    marginals = task["marginals"]
    if not isinstance(marginals, list) or len(marginals) != len(bags):
        raise Invalid("marginal count mismatch")
    laws = []
    for bag, raw in zip(parsed_bags, marginals):
        if not isinstance(raw, dict):
            raise Invalid("marginal must be an object")
        law = {parse_assignment(assignment, len(bag)): rat(value)
               for assignment, value in raw.items()}
        full_domain = set(product((0, 1), repeat=len(bag)))
        if set(law) != full_domain:
            raise Invalid("marginal must list a full probability table")
        if any(value < 0 for value in law.values()) or sum(law.values(), F(0)) != 1:
            raise Invalid("marginal must be a probability table")
        laws.append(law)

    # Exact separator consistency.
    for a, b in parsed_edges:
        right = set(parsed_bags[b])
        separator = tuple(v for v in parsed_bags[a] if v in right)
        pos_a = [parsed_bags[a].index(v) for v in separator]
        pos_b = [parsed_bags[b].index(v) for v in separator]
        if marginalize(laws[a], pos_a) != marginalize(laws[b], pos_b):
            raise Invalid("separator marginals disagree")

    return (tuple(variables), tuple(parsed_bags), tuple(tuple(row) for row in adj),
            tuple(laws))


def extend(task):
    variables, bags, adj, laws = parse_task(task)
    n = len(variables)
    root = 0
    current = {
        tuple(assignment[bags[root].index(i)] if i in bags[root] else None
              for i in range(n)): probability
        for assignment, probability in laws[root].items()
    }

    parent = {root: -1}
    order = []
    queue = deque([root])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v == parent[u]:
                continue
            parent[v] = u
            order.append(v)
            queue.append(v)

    for child in order:
        bag = bags[child]
        parent_bag = set(bags[parent[child]])
        separator = tuple(v for v in bag if v in parent_bag)
        sep_positions = [bag.index(v) for v in separator]
        sep_law = marginalize(laws[child], sep_positions)
        updated = defaultdict(F)
        for partial, parent_mass in current.items():
            if parent_mass == 0:
                continue
            sep_assignment = tuple(partial[v] for v in separator)
            denominator = sep_law.get(sep_assignment, F(0))
            if denominator == 0:
                raise Invalid("positive parent mass on zero separator")
            for local, local_mass in laws[child].items():
                if tuple(local[i] for i in sep_positions) != sep_assignment:
                    continue
                full = list(partial)
                compatible = True
                for variable, bit in zip(bag, local):
                    if full[variable] is not None and full[variable] != bit:
                        compatible = False
                        break
                    full[variable] = bit
                if compatible:
                    updated[tuple(full)] += parent_mass * local_mass / denominator
        current = dict(updated)

    if any(any(value is None for value in assignment) for assignment in current):
        raise Invalid("extension construction left an unassigned variable")
    if sum(current.values(), F(0)) != 1:
        raise Invalid("extension construction is not normalized")
    current = {assignment: current.get(assignment, F(0))
               for assignment in product((0, 1), repeat=n)}

    for bag, law in zip(bags, laws):
        if marginalize(current, list(bag)) != law:
            raise Invalid("constructed law has wrong marginal")
    return variables, current


def certificate(task):
    variables, law = extend(task)
    return {
        "kind": "join-tree-extension",
        "variables": list(variables),
        "law": {"".join(str(bit) for bit in assignment): str(probability)
                for assignment, probability in sorted(law.items())},
    }


def replay(task, cert):
    variables, expected = extend(task)
    if (not isinstance(cert, dict) or set(cert) != {"kind", "variables", "law"} or
            cert["kind"] != "join-tree-extension" or cert["variables"] != list(variables)):
        raise Invalid("invalid join-tree certificate")
    if not isinstance(cert["law"], dict):
        raise Invalid("certificate law must be an object")
    law = {parse_assignment(assignment, len(variables)): rat(value)
           for assignment, value in cert["law"].items()}
    if law != expected:
        raise Invalid("certificate law mismatch")
    return len(law)


def read_json(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 2**20:
        raise Invalid("missing or oversized file")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise Invalid("duplicate JSON key")
            out[key] = value
        return out

    try:
        return json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Invalid("invalid JSON") from exc


def main():
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != "--verify"):
        print("usage: python src/join_tree.py TASK.json CERT.json [--verify]", file=sys.stderr)
        return 2
    try:
        task = read_json(sys.argv[1])
        if len(sys.argv) == 3:
            cert = certificate(task)
            Path(sys.argv[2]).write_text(json.dumps(cert, indent=2) + "\n", encoding="utf-8")
            print(f"constructed {len(cert['law'])}-cell global law")
        else:
            print(f"ACCEPT: {replay(task, read_json(sys.argv[2]))}-cell exact extension")
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print("REJECT: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
