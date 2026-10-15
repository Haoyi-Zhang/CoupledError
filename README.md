# Order-coupling contracts

This artifact contains exact finite tasks, rational certificates, optimizer-free
replay, finite reference oracles, and dependency-scope checks for
*Order-Coupling Contracts for Correlated Approximate Pipelines*.
It runs independently of the manuscript directory.

## Requirements

Retained-certificate replay and join-tree construction/replay require Python 3
and its standard library on Windows or Linux. Full regeneration requires Linux
for POSIX limits and SciPy for numerical candidate location; the scientific CI
pins SciPy/NumPy and uses one numerical thread.

The order producer rationalizes a numerical candidate and checks it exactly.
Failure to recover such a witness is inconclusive. Replay itself imports no
optimizer or producer. No network, GPU, model service or private data is needed.

## Quick replay and tests

From this directory:

```sh
python3 -B src/order_verify.py inputs/order-relational.json results/order-relational.certificate.json
python3 -B tests/semantic_boundaries.py
python3 -B tests/coefficient_regression.py
python3 -B -m unittest discover -s tests -p test_reproduction_comparison.py -v
```

The replay checks primal, transport and dual conditions with exact rational
arithmetic. Focused tests cover semantic boundaries, checker-owned coefficients,
and scientific comparison of equivalent optimal witnesses.

## Reproduction

On Linux with SciPy, use an absent output directory outside the artifact:

```sh
python3 -B reproduce.py --output-dir /tmp/order-coupling-run
```

The runner regenerates finite reference results, performs exact replay and
oracle/mutation/representation checks, and compares scientific outputs.
It retains commands, stdout/stderr, exits and the isolated worktree on both
success and failure. Resource limits are 40 CPU seconds and 3,500 MiB per
child; raw wall/RSS measurements vary by machine.

For a host without all full-run dependencies:

```sh
python3 -B reproduce_available.py --portable --output-dir /path/to/private/order-coupling-run
```

This route records which stages actually ran and which are unavailable.
On Windows it records affinity and peak working set without claiming POSIX
CPU/address-space enforcement or child CPU accounting. Missing SciPy leaves
four numerical stages and the order-producer CLI unavailable; the available
route is not full regeneration.

The scientific workflow runs the Linux/SciPy route on Ubuntu with a 240-second
wall deadline, preserves comparison/count/exit gates, and uploads raw outputs
after failure as well as success. Consult Actions for current hosted outcomes.

## Additional commands

```sh
python3 src/order_run.py inputs/order-relational.json /tmp/order-cert.json
python3 src/order_verify.py inputs/order-relational.json /tmp/order-cert.json
python3 src/join_tree.py inputs/join-tree.json /tmp/join-cert.json
python3 src/join_tree.py inputs/join-tree.json /tmp/join-cert.json --verify
python3 src/run.py inputs/boundary-sensitive.json /tmp/binary-cert.json
python3 src/verify.py inputs/boundary-sensitive.json /tmp/binary-cert.json
```

Order production needs SciPy; join-tree and binary production/replay use the
standard library. The binary `a[s]` value is joint boundary-and-success mass.
The source-model route `src/run.py --source INPUT OUTPUT` also emits projected
task/scope companions. That translation is a separate trusted finite front end.

`src/transport_verify.py TASK CERT --convert-to NEW_FILE` converts an admitted
order certificate to ordinary transport potentials for the same optimum;
replay the converted certificate with `src/transport_verify.py TASK NEW_FILE`.
[tests/transport_cost.py](tests/transport_cost.py) measures the complete
conversion, serialization and replay against direct upset replay. The retained
conversion route is slower on the measured cohort; both use the same finite
information and guarantee.

## Objects and interpretation

The order certificate combines, for each replacement generator, an old-contract
mixture, upward-set deficits, a boundary-preserving transport and an equal-value
dual witness. Exact mixtures/transports/duals can be nonunique: comparison checks
both witnesses and requires equal scientific values, target optima, inputs,
coverage and seeds, rather than identical proof coordinates.

The parser admits one to four boundary labels, two to eight outcomes and one to
six generators per side. Upward sets are explicitly enumerated. The theorem
uses same-prior contracts, compatible component/frame couplings and monotone
[0,1]-valued rewards. These assumptions and the directed contextual formula are
developed in [proofs/order-core.md](proofs/order-core.md).
Ordinary transport LPs and directed set lifting are attributed foundations.

## Material map

- `src/`: strict parsing, producer, exact checkers, transport and finite front end.
- `inputs/`: every exact task consumed by the retained campaigns.
- `results/`: reference certificates, finite summaries, truth tables and resource records.
- `evidence/current/`: retained normal/optimized available-run logs and paired cost inputs.
- `tests/`: finite oracles, mutations, invariance, admission and reproduction comparisons.
- [FORMAT.md](FORMAT.md): strict task/certificate schemas, limits and equations.
- `proofs/`: order characterization, binary specialization and finite-oracle arguments.
- `claim_evidence_ledger.csv`, `external_resources.csv`, and
  [source-notes.md](source-notes.md): claim, attribution and redistribution records.

The order producer/checker share strict parsing and finite-poset utilities.
The all-poset, postprocessing and direct-context oracles use self-contained
mathematics; the set-contract differential driver calls the production
generator/checker alongside separately implemented expectation/minimax logic.
Written proofs supply universal arguments; finite runs check admitted instances.

## License

Original code and finite data use the included [MIT license](LICENSE).
Third-party articles are cited rather than redistributed.
