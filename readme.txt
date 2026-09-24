This electronic supplement is the standalone artifact for
"Order-Coupling Contracts for Correlated Approximate Pipelines."

Run from the extracted artifact root:

    python3 reproduce.py

The command regenerates and exactly compares 51 scientific files, replays 456
contextual certificates and one join-tree dependency certificate, and runs the
independent all-poset, postprocessing, direct-context, set-contract/minimax,
mutation, representation-invariance, scaling, input-validation, and legacy
campaigns. Python's standard library is sufficient for replay and the exact
oracles. Regenerating the finite-poset order certificates additionally requires
SciPy; every accepted certificate is nevertheless checked by exact rational
replay. The numerical producer is not claimed to be a complete decision
procedure for every syntactically valid input.

See README.md for commands, scope, trust boundaries, and limitations;
FORMAT.md for strict input/certificate schemas; and LICENSE for the terms on
original code and data. No network, model service, GPU, private data, paper
directory, or hidden cache is required.
