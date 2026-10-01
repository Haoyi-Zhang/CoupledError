# Completeness of the declared finite oracle

This is a proof of the validation oracle's *restricted grid*, not an alternative
proof of the general contextual-loss identity.

Fix p=(1/2,1/2). Each supplied success vector and each tester b has coordinates
in {0,1/4,1/2}; a contract has one or two such generators. On a two-generator
segment a(lambda)=(1-lambda)a(0)+lambda a(1), the objective for a fixed tester
is piecewise affine. Each possible change of slope satisfies

  a_s(0)+lambda(a_s(1)-a_s(0)) = 1/2-b_s.

A nonconstant coordinate has difference plus/minus 1/4 or plus/minus 1/2.
Both the target and initial coordinate are quarter multiples. Consequently
an interior breakpoint can only be lambda=1/2. A minimum on [0,1] occurs
at 0, 1/2, or 1. These candidate success masses are eighth multiples.

For each state, enumerate all integer quadruples (n11,n10,n01,n00) summing
to four eighths and satisfying the two marginal equalities. This is complete
for the required row minimum: the real feasible interval has endpoints
max(0,a+b-p) and min(a,b), both eighth multiples. Enumerating integer cells
therefore includes its minimum. The implementation explicitly enumerates
quadruples and checks marginals; it does not call the hinge optimizer.

To check directed contextual loss between two grid contracts, the main
mathematical theorem reduces the outer extremum to a supplied new generator.
The complement tester of every such generator belongs to the same nine-point
grid. Thus the largest floor difference among these nine testers equals the
unrestricted contextual loss. This last conclusion uses the proved general
identity; it is not an independently mechanized theorem. The separate oracle
checks the computed floors and the resulting finite comparisons independently
of primal/dual active-set search.

There are 9 points, 9+binomial(9,2)=45 contracts, 45*9=405 old-contract versus
new-singleton certificates, and 45*45=2025 contract-pair comparisons. These are
structured finite validation cases, not independent samples of a population,
and their count is not workload breadth or statistical confidence.

## Independent multi-poset sweep

`tests/poset_sweep.py` is a second finite oracle that imports no production
order module.  It enumerates denominator-three laws over six shapes: the
2-chain, 3-chain, 3-element vee, 3-element wedge, 4-element diamond, and
4-element antichain.  For every ordered pair it independently computes the
maximum upward-set deficit and the minimum bad mass using an integer
maximum-flow construction.  It also enumerates every law triple for the
directed triangle inequality and checks directly that `{x : x not <= y}` is
upward for every target outcome `y`.

The retained scope is 1,116 ordered pairs and 19,064 triples, with zero
mismatches or violations.  This broadens finite shape coverage but remains a
bounded check, not a proof of stochastic-order duality or the triangle law.

## Direct contextual enumeration

`tests/context_exhaustive.py` independently checks the contextual formula on a
small complete semantic universe.  There is one boundary, the outcome order
is the chain `0 < 1`, component and binary-frame laws use denominator three,
and the oracle enumerates every monotone reward in {0, 1/2, 1} of component outcome
and frame outcome.  It enumerates all compatible integer coupling tables
rather than calling the production deficiency code.

There are four point laws, 15 nonempty finite contracts, 225 ordered contract
pairs, four frame laws, 36 monotone three-level rewards, and 144 frame/reward contexts; the nine Boolean rewards and 36 Boolean contexts are checked separately.
For every contract pair, direct robust-floor subtraction agrees exactly with
the contract deficiency formula.  The enumeration is complete only for this
declared tiny universe and does not replace the paper's general proof.


## Pure-versus-mixed test game cross-check

The two-generator oracle independently implements upward-set enumeration,
piecewise-affine expected-value minimization, and the two-payoff mixed game.
Its differential driver then imports and calls the SciPy-backed production
certificate generator and the exact replay checker.  Across 50 tasks and 99
target laws, all mixed values equal the independently computed primal minima.
Nine targets have a strict pure-test gap (largest `1/4`).  Exactly 11 targets
*require* an interior old mixture, meaning both endpoint objective values are
strictly above the minimum.  An interior optimum exists for 58 targets when
flat intervals touching an endpoint are included; 31 breakpoint lists name an
interior minimizer explicitly, and 20 of those also have an optimal endpoint.
Seed 813 and a constant objective are retained classification regressions.
This is finite evidence only; the general equality uses the written minimax
proof, and the differential command requires SciPy even though the independent
expectation calculation itself uses exact standard-library arithmetic.

## Exhaustive labeled-poset oracle

`tests/all_posets_exhaustive.py` removes the six-shape selection from the
preceding regression sweep. It independently enumerates every reflexive,
antisymmetric, and transitive relation on labeled sets of sizes two, three,
and four. The resulting counts are 3, 19, and 219, respectively. For each of
the 241 orders it enumerates every denominator-two law, compares an integer
maximum-flow deficiency with independently enumerated upward-set deficits,
checks every ordered law triple for the directed triangle inequality, and
checks target-monitor monotonicity pointwise. The retained 22,611 ordered law
pairs and 223,185 triples have zero mismatches or violations. This is complete
for that bounded labeled universe, not for arbitrary finite orders.

## Exhaustive finite postprocessing oracle

`tests/data_processing_exhaustive.py` independently enumerates all 22 labeled
orders on two or three outcomes as both source and target. It checks every
monotone deterministic map and every denominator-two Markov kernel whose rows
are stochastically monotone, against every denominator-two source-law pair.
The resulting 4,732 maps induce 159,957 checks, and 24,972 kernels induce
864,081 checks; none increases directed deficiency. The code contains its own
integer-flow implementation and imports no production order module. The
written proof, not this grid, covers arbitrary rational kernels and larger
orders.

## Adversarial and metamorphic implementation checks

`tests/certificate_mutation.py` changes exactly one checked field at a time in
all 24 retained order certificates: it deletes required top-level fields,
adds an unknown field, corrupts every numeric leaf, injects a JSON float, and
shortens a required list. All 1,636 variants are rejected. This demonstrates
that replay consumes the witness rather than trusting case names or objective
labels; it is not a proof of parser or checker correctness.

`tests/metamorphic_invariance.py` attacks representation overfitting in the
production path. It permutes and renames boundary/outcome labels and reverses
old/new generator enumeration in 18 transformed variants of the four named
tasks. Each fresh certificate replays exactly and preserves the value. This
checks representation invariance on the retained tasks; it does not establish
producer completeness.

`tests/scaling_profile.py` exercises exact production and replay on chains and
antichains at every supported outcome size from two through eight. All 14
cases replay. The recorded maximum of 255 nonempty upward sets for the
eight-element antichain makes the limitation explicit: the reference encoding
has exponential upward-set growth and is not a scalability result.
