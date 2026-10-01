This electronic supplement is the standalone artifact for
"Order-Coupling Contracts for Correlated Approximate Pipelines."

Run from the extracted artifact root:

    python3 reproduce.py

The command regenerates and exactly compares all retained scientific files,
replays 456 contextual certificates, replays both the generated and retained
representations of one join-tree certificate object, requires them to be equal,
and rejects an isolated one-cell corruption.  It also runs the all-poset,
postprocessing, direct-context, set-contract/minimax, mutation,
representation-invariance, scaling, input-validation, and legacy campaigns.
Replay-only commands and self-contained enumerators use Python's standard
library.  Full reproduction requires SciPy because it regenerates order
certificates and runs the differential contract driver that calls the
production generator and checker; the driver’s expectation/minimax arithmetic
is independently implemented.  Every accepted certificate is checked by exact
rational replay. The numerical producer is not claimed complete for every
syntactically valid input.

See README.md for commands, scope, trust boundaries, and limitations;
FORMAT.md for strict input/certificate schemas; and LICENSE for the terms on
original code and data. No network, model service, GPU, private data, paper
directory, or hidden cache is required.
