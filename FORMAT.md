# Exact task and certificate formats

All scientific numbers are exact integers or rational strings. JSON files are
limited to 1 MiB. Duplicate object keys, unexpected keys, malformed shapes,
floating-point literals where rationals are required, excessive bit lengths,
and invalid probability tables are rejected.

## Finite-poset order task

An order task has exactly four keys:

```json
{
  "boundary": ["all"],
  "poset": {
    "outcomes": ["00", "01", "10", "11"],
    "leq": [[1,1,1,1], [0,1,0,1], [0,0,1,1], [0,0,0,1]]
  },
  "old": {"generators": [{"mass": [["0","0","1/2","1/2"]]}]},
  "new": {"generators": [{"mass": [["0","1/2","1/2","0"]]}]}
}
```

`boundary` contains one through four distinct nonempty labels, each at most 40
characters. `outcomes` contains two through eight distinct nonempty labels.
`leq[i][j]` is a Boolean order matrix and is checked for reflexivity,
antisymmetry, and transitivity.

Each contract has exactly a `generators` list with one through six entries.
Each generator has exactly `mass`, a boundary-by-outcome matrix of nonnegative
rational masses summing to one. Every generator within one contract must have
the same boundary prior, and old and new priors must be equal. The list denotes
its convex hull. The common denominator of all input masses is at most
1,048,576. Rational strings have at most 160 characters.  Whether supplied
as a JSON integer or a rational string, every parsed numerator and denominator
has a 256-bit limit; JSON Booleans are not rational integers.

### Order-coupling certificate

An accepted certificate has exactly:

- `kind`: `"order-coupling-loss"`;
- `value`: the global directed loss;
- `proofs`: one proof in replacement-generator order;
- `worst_generator`: a JSON integer index attaining `value` (Booleans are
  rejected even though Python's `bool` is an `int` subclass);
- `witness`: the target-law contextual witness.

For each replacement generator `n`, a proof contains:

- `value`;
- `lambda`: nonnegative old-generator weights summing to one;
- `row_deficit`: one nonnegative value per boundary row;
- `transport`: one exact old-to-new outcome matrix per boundary row;
- `dual_alpha`: the free dual scalar;
- `dual_weights`: nonnegative weights over the deterministically enumerated
  nonempty upward sets, with row sum at most one.

The checker reconstructs the old mixture `m`, verifies every upward-set
inequality

```
m_s(U) - n_s(U) <= row_deficit[s],
```

checks both marginals of every transport, verifies in every boundary row that
its mass on pairs `x not <= y` equals that row's declared deficit, and then
verifies the total deficiency. It checks each old-generator
dual inequality and verifies exact equality among primal, transport, and dual
objectives. The global value must be the maximum proof value and the selected
index must attain it.

The witness object has exactly:

```json
{
  "frame": "target-law",
  "monitor": "1[x-not-leq-y]",
  "new_floor": "0",
  "old_floor": "<certificate value>"
}
```

This witnesses the declared finite contextual semantics. It does not prove
that an outside application's outcome order or monitor is correct.

## Join-tree dependency task

A join-tree task has exactly `variables`, `bags`, `tree_edges`, and
`marginals`.

- `variables` contains two through eight distinct names.
- `bags` contains one through seven nonempty variable lists.
- `tree_edges` has exactly `bags - 1` distinct valid edges and must form a
  connected tree.
- For every variable, the bags containing it must form a connected subtree
  (running intersection).
- Each marginal is a complete binary table for its bag: every bit string is
  present, all masses are nonnegative rational strings, and the table sums to
  one.
- Adjacent bag tables must agree exactly on their separator marginal.

The output certificate has `kind: "join-tree-extension"`, the unchanged
variable order, and a complete global binary probability table. Verification
reruns the deterministic leaf-gluing construction and compares every exact
cell, after checking all local marginals again. This is a finite acyclic
extension checker, not a solver for arbitrary cyclic marginal problems.

## Binary boundary-success task

The compatibility specialization has exactly `old` and `new`. Each contract
contains:

- `states`: an integer from one through four;
- `vertices`: one through five points;
- for each point, `p` and `a` rational arrays of length `states`.

The masses satisfy `sum(p)=1` and `0 <= a[s] <= p[s]`; `a[s]` is joint mass of
state `s` and success. The vertex list denotes one global convex hull. Old and
new contracts must have the same convex hull of priors. The input common
denominator is at most 65,536; all input and certificate rationals retain the
160-character and 256-bit limits.

A `contextual-loss` certificate records exact prior-hull containment witnesses
and, for every new generator, an old same-prior mixture, positive-part slack,
and a feasible dual. `src/verify.py` checks all primal and dual equations and
the complementary Boolean target tester. Details are mirrored in
`proofs/core.md`.

## Finite source route

`inputs/pipeline-model.json` illustrates the source-format route. Its keys are
`interface`, `old`, `new`, and `frame`. The interface declares disjoint finite
Boolean scopes (`boundary`, `private`, `frame`), one Boolean `success` name,
expectation-interval `constraints`, and a Boolean `monitor`.

Expressions are booleans, variable-name strings, or lists headed by `not`,
`and`, `or`, or `if`. There is no evaluated Python or arbitrary code. Names
are at most 32 characters and expressions at most 256 nodes and depth 24.
`and`/`or` take two through eight children.

The route supports at most two boundary bits, five component-private bits,
eight frame-private bits, and twelve declared bits including success. A joint
law has at most eight variables and 256 explicitly listed assignments; omitted
assignments have zero mass. Each law list denotes a convex hull of complete
finite distributions, not samples and not all models of the optional moment
constraints.

Every constraint's variables must fit wholly inside the component side or the
frame side. The monitor may read boundary, frame, and success but not component
private variables, and it is exhaustively checked for monotonicity in the same
success event. Frame priors must be admitted on both component sides. These
scope checks justify the finite projection used by the example; they do not
infer independence or verify arbitrary programs.

## Evidence containers

Some files under `results/` contain lists or campaign summaries rather than a
single replay object. Replay the individual embedded input/certificate pairs
or use `python3 reproduce.py`. Files ending in `-resources.json` and
`reproduction.json` include volatile measurements; their scientific fields
are checked while timing and peak-memory values are allowed to vary.
