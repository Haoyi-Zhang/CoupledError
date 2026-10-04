# Order-coupling contract artifact

This standalone repository supports the paper *Order-Coupling Contracts for
Correlated Approximate Pipelines*. It contains exact finite inputs, rational
proof certificates, optimizer-free replay code, independent exact oracles,
dependency-scope checks, negative controls, and the raw results reported in the
paper.
It does not depend on the paper directory.

The artifact addresses a finite mathematical claim. It does not run a learned
model, contact a service, measure a deployed pipeline, inject physical faults,
or establish empirical AI-system accuracy.

## Main result represented by the artifact

For a finite boundary `S`, a finite poset of outcomes `X`, and same-prior point
laws `m,n`, the order-coupling deficiency is the minimum mass of pairs
`(x,y)` with `x` not below `y` over all boundary-preserving couplings. The
paper proves that the directed contextual replacement loss between compact
contracts is

```
sup_{n in new} inf_{m in old with prior p_n} deficiency(m,n).
```

The order certificates in this repository give, for every supplied
replacement generator, three exact descriptions of the same value:

1. an old-contract convex mixture and its row-wise upward-set deficits;
2. a boundary-preserving transport whose bad mass has that value; and
3. a feasible upward-set dual with the same objective.

The target-law witness records the finite relational context that attains the
value. `src/order_verify.py` checks the certificate with `fractions.Fraction`
and imports no optimizer.

The older `p/a` interface remains as a binary specialization. There `a[s]`
is joint mass of boundary state `s` and Boolean success, not a conditional
probability. Its certificates are replayed by `src/verify.py`.

## Requirements

Replay-only verification, join-tree construction/replay, the legacy binary
producer, and the self-contained finite enumerators use Python 3 and its
standard library.  A Linux-like environment supplies the optional resource
limits used by `reproduce.py`.

The full `python3 reproduce.py` command additionally requires SciPy because it
regenerates finite-poset order certificates and runs the differential
set-contract driver.  That driver independently implements the expected-value
and minimax mathematics, but deliberately imports and calls the production
certificate generator and replay checker for comparison; the producer calls
`scipy.optimize.linprog` to locate a candidate optimum.  The candidate is
rationalized and checked exactly.  Retained certificates can be replayed
without SciPy:

```sh
python3 src/order_verify.py \
  inputs/order-relational.json \
  results/order-relational.certificate.json
```

The dependency boundary is command-specific:

| Command or command family | Runtime dependency | What it establishes |
|---|---|---|
| `python3 src/order_verify.py TASK CERT` | Python standard library | Exact replay of a retained order-coupling certificate; imports no producer or optimizer |
| `python3 src/verify.py TASK CERT` | Python standard library | Exact replay of the binary specialization |
| `python3 src/join_tree.py TASK CERT --verify` | Python standard library | Exact replay of a retained join-tree extension |
| `python3 src/join_tree.py TASK CERT` | Python standard library | Deterministic construction of the finite join-tree extension |
| `python3 tests/all_posets_exhaustive.py`, `tests/data_processing_exhaustive.py`, `tests/context_exhaustive.py`, and `tests/poset_sweep.py` | Python standard library | Self-contained finite enumeration using independently coded exact mathematics |
| `python3 src/run.py ...` | Python standard library | Legacy binary projection/production followed by exact replay |
| `python3 src/order_run.py TASK CERT` | Python plus SciPy | Numerical candidate location for an order certificate, followed by exact rational certificate construction |
| `python3 tests/order_campaign.py` | Python plus SciPy | Regeneration/differential campaign that calls the order producer, alongside exact replay and finite controls |
| `python3 tests/independent_contract_oracle.py` | Python plus SciPy | Independently implemented expectation/minimax calculation, plus a differential driver that imports and calls the production generator and checker |
| `python3 reproduce.py` | Python plus SciPy | Full generation, differential testing, replay, enumeration, mutation testing, and retained-file comparison |

Thus “independent oracle” describes the expectation/minimax algorithm, not an
absence of production imports from its differential-test driver. Conversely,
the driver's SciPy dependency does not make its independently coded exact
mathematics a call-through to the production objective.

No network, GPU, model API, external solver process, private data, paper
source, or hidden cache is required.

## One-command reproduction

From this repository root:

```sh
python3 reproduce.py
```

The command runs one child at a time, applies a 40 CPU-second and 3,500-MiB
address-space limit, regenerates all finite reference results, compares every
scientific JSON/CSV file while excluding only volatile runtime fields, and
exits nonzero on any mismatch or timeout. It also exercises the documented
producer/replay command-line routes in temporary files.

The frozen clean run reported:

- 51 scientific files compared;
- zero scientific mismatches;
- 456 contextual certificates replayed;
- one join-tree certificate object represented by both a generated canonical
  file and a retained evidence file; both replayed and compared exactly;
- one isolated single-cell join-tree corruption rejected;
- one worker throughout;
- approximately 29.73 aggregate CPU seconds and 29.75 wall seconds;
- peak child RSS 122,536 KiB and peak parent RSS 101,412 KiB.

Resource measurements vary by machine and are not included in the exact
scientific comparison.

## Focused commands

Produce and replay an order-coupling certificate:

```sh
python3 src/order_run.py inputs/order-relational.json /tmp/order-cert.json
python3 src/order_verify.py inputs/order-relational.json /tmp/order-cert.json
```

Construct and replay the acyclic dependency extension:

```sh
python3 src/join_tree.py inputs/join-tree.json /tmp/join-cert.json
python3 src/join_tree.py inputs/join-tree.json /tmp/join-cert.json --verify
```

Produce and replay the binary boundary-success specialization:

```sh
python3 src/run.py inputs/boundary-sensitive.json /tmp/binary-cert.json
python3 src/verify.py inputs/boundary-sensitive.json /tmp/binary-cert.json
```

Validate and project the retained source-format toy pipeline before producing
its binary certificate:

```sh
python3 src/run.py --source inputs/pipeline-model.json /tmp/pipeline-cert.json
python3 src/verify.py /tmp/pipeline-cert.task.json /tmp/pipeline-cert.json
```

The source route creates `.task.json` and `.scope.json` companions. The
certificate checker proves arithmetic facts about the projected task; the
front end remains a separate trusted transformation, tested on finite valid
and invalid inputs rather than mechanically verified.

## Frozen evidence map

| Evidence | Exact retained scope |
|---|---|
| Order cases | Four named certificates, each value `1/4`, plus 20 seeded random exact certificates |
| Order point oracle | 35 denominator-four Boolean-square laws; 1,225 ordered pairs; zero transport/upward-set mismatches |
| Triangle oracle | 42,875 ordered Boolean-square triples; zero violations |
| Multi-poset regression oracle | Six selected posets; 1,116 ordered pairs and 19,064 triples; zero duality, triangle, or target-monitor-upwardness violations |
| All-poset exhaustive oracle | Every labeled poset on two, three, and four outcomes (241 total); 22,611 law pairs and 223,185 triples; zero mismatches or violations |
| Data-processing oracle | All labeled two/three-outcome source and target posets; 4,732 monotone maps with 159,957 checks and 24,972 denominator-two monotone kernels with 864,081 checks; zero violations |
| Direct contextual oracle | Four point laws, 15 nonempty finite contracts, 225 ordered contract pairs, 144 three-level reward contexts (including 36 Boolean contexts); zero formula/semantics mismatches |
| Independent set-contract/minimax oracle | 50 exact two-generator tasks; 99 targets; 11 require an interior mixture by strict endpoint comparison; 58 admit an interior optimum; 31 breakpoint lists contain an interior minimizer and 20 of those also have an optimal endpoint; nine strict pure-test gaps; zero primal or mixed-dual mismatches |
| Representation invariance | 18 transformed named tasks permuting/renaming boundaries and outcomes and reordering generators; zero value or replay failures |
| Structural profile | Exact production and replay for chains and antichains with two through eight outcomes; 14 cases; 255 maximum nonempty upward sets; zero failures |
| Strict input validation | 14 parser/CLI cases; 12 invalid cases rejected, including `worst_generator=false` and a 257-bit JSON integer; two valid controls accepted |
| Relational witness | Fixed-upset robust gap `0`; target-law contextual loss `1/4` |
| Dependency scopes | Three variables with two pair bags `AB`/`BC`; generated and retained eight-cell certificates both replayed and forced equal; an isolated one-cell mutation plus cycle and separator-mismatch inputs rejected |
| Binary specialization | 432 replayed certificates in total |
| Legacy grid | 405 point certificates and 2,025 derived contract comparisons; zero integer-cell oracle disagreement |
| Rational legacy stress | 20 fixed-seed cases within the declared bounds |
| Toy source/circuit | Four-valued payload `x` and Boolean `hit/pre/cache/idx/srv`: `4*2^5=128` rows; 12 monitor successes; 64 correct outputs; 52 correct but uncertified rows; zero false positives |
| Negative controls | 1,636 systematic single-field order-certificate mutations, 12 corrupted legacy certificates, eight invalid source/domain inputs, two invalid dependency inputs, and 12 invalid parser/CLI cases rejected |

These are finite checks. They do not prove the universal semantic theorem,
which is established by the written paper proof and mirrored in
`proofs/order-core.md` and `proofs/core.md`.

## Repository map

- `src/order_common.py` — strict rational task parser and finite-poset helpers.
- `src/order_run.py` — numerical locator plus exact rational certificate
  producer for convex order contracts.
- `src/order_verify.py` — optimizer-free exact replay checker; it shares strict
  task parsing and poset utilities with the producer but imports no optimizer.
- `src/join_tree.py` — exact finite join-tree extension and replay.
- `src/exact.py`, `src/run.py`, `src/verify.py` — binary specialization
  producer and optimizer-free replay.
- `src/front_end.py` — finite Boolean source-model validation and projection.
- `tests/order_campaign.py` — Boolean-square order oracle, triangle checks,
  random cases, dependency checks, and corrupted-certificate controls.
- `tests/poset_sweep.py` — independent transport/upward-set, triangle, and
  target-monitor regression checks across six finite order shapes.
- `tests/all_posets_exhaustive.py` — self-contained exhaustive duality,
  triangle, and target-monitor checks for every labeled poset through four
  outcomes.
- `tests/data_processing_exhaustive.py` — self-contained exhaustive checks of
  deterministic and denominator-two stochastic monotone postprocessing across
  all labeled two- and three-outcome source/target orders.
- `tests/context_exhaustive.py` — independent direct enumeration of tiny
  contracts, compatible couplings, and all monotone {0, 1/2, 1}-valued rewards, with Boolean monitors checked separately.
- `tests/independent_contract_oracle.py` — independently implemented exact
  expected-value minimization and pure-versus-mixed test-game mathematics;
  its differential driver imports and calls the production generator/checker
  and therefore needs SciPy.
- `tests/certificate_mutation.py` — systematic single-field mutations of every
  retained order certificate.
- `tests/metamorphic_invariance.py` — production/replay checks under label,
  index, boundary, and generator-order transformations.
- `tests/scaling_profile.py` — exact structural profile at every supported
  outcome size on chains and antichains; it records exponential upward-set
  growth rather than claiming scalability.
- `tests/input_validation.py` — duplicate-key, type, bound, schema, and CLI
  negative controls with valid controls.
- `tests/campaign.py`, `tests/pilot.py`, `tests/randomization.py` — binary
  specialization, source, convexity, and negative-control campaigns.
- `proofs/order-core.md` — proof mirror for the poset characterization,
  duality, calculus, convexity, and dependency scope.
- `proofs/core.md` — binary specialization and source-scope proof notes.
- `proofs/finite-oracle.md` — completeness argument for the legacy finite
  integer-cell oracle.
- `inputs/` — every consumed exact task.
- `results/` — reference certificates, raw summaries, truth table, and measured
  resource records.
- `FORMAT.md` — strict syntax, limits, and certificate equations.
- `claim_evidence_ledger.csv` — material claim-to-proof/test mapping.
- `external_resources.csv` and `source-notes.md` — attribution, licenses, and
  novelty boundaries.

## Trust boundaries and limitations

The replay checkers are ordinary Python programs, not a proof assistant. The
order producer and checker share the task parser and finite-poset utility
module, but the checker does not import the optimizer or producer. The
all-poset, postprocessing, and direct-context oracles are self-contained.  The
two-generator oracle independently reimplements its expectation/minimax
mathematics, while its differential test driver intentionally imports and
calls the production generator and checker. Systematic mutations and
representation-preserving transformations exercise different failure modes.
All paths still share the Python runtime and integer/rational arithmetic. The
join-tree replay reconstructs the declared finite extension; it is not a
general marginal-polytope solver.

The parser permits one to four boundary labels, two to eight outcomes, and one
to six convex generators per side. The numerical producer is a reference
certificate locator, not a complete decision procedure: a failure to recover
an exact rational primal/dual witness is inconclusive, whereas every accepted
certificate is replayed exactly. The implementation explicitly enumerates all
nonempty upward sets, so it is not intended for large Boolean products; an
eight-element antichain already has 255. The binary source route consumes
complete finite laws supplied in the input and does not verify arbitrary
source programs or implicit moment classes.

All contexts in the theorem use [0,1]-valued rewards monotonically and admit
all compatible component--frame couplings. Independent-only clients, known
shared seeds, temporal behavior, changed boundary priors, nonmonotone
observations, and signed or unbounded utilities require different semantics. A true monitor is only
a sufficient condition for the retained toy output; it is not a claim that the
monitor captures every correct execution or any real application.


## License

Original source code and finite input/result data in this repository are
released under the included MIT license. Third-party articles are cited, not
redistributed. The repository contains no publisher class, font, credential,
private data, or invented public repository address.
