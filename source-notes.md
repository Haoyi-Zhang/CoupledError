# Source attribution and evidence boundaries

The literature inventory was assembled on 16 September 2026. On 19 September
2026, the load-bearing historical and closest-work records, the supplied ACM
class record, and the current policy/venue endpoints listed with that date in
`external_resources.csv` were rechecked. The TOPLAS author-guide endpoint still
did not yield a complete readable primary-source page in this environment, so
its external-submission details remain a named human recheck hold. This file
records the technical relationship actually used to bound the manuscript's
claims; it does not claim that every cited publication was independently
reproduced. No third-party article bytes are distributed in this repository.

## Historical quantitative reliability

**Carbin, Misailovic, and Rinard, “Verifying Quantitative Reliability for
Programs that Execute on Unreliable Hardware,” OOPSLA 2013,
DOI 10.1145/2509136.2509546.**

Rely defines reliability relative to agreement with an ideal execution under
an unreliable environment and develops reliability predicates and a sound
analysis. Its distributions are joint distributions; nothing in the result
supports a novelty statement that prior work required independent input
variables. The appendix also uses a union-bound argument in its proof
structure. The present paper therefore cites Rely as the historical point of
departure and does not claim that merely allowing correlated approximation
events is new. No Rely code, benchmark, experiment, theorem text, or proof
artifact is reused.

Approximate-language systems including EnerJ, Chisel, and `Uncertain<T>` are
cited for making approximation or uncertainty explicit in language and
systems design. The current artifact does not compare energy, optimization,
accuracy, or type-system performance with them.

## Existing probabilistic contracts

**Delahaye, Caillaud, and Legay, “Probabilistic Contracts,” FMSD 2011,
DOI 10.1007/s10703-010-0107-8; Xu, Gössler, and Girault, ATVA 2010 and FMSD
2012; Hampus and Nyberg, ISoLA 2024 and Formal Aspects of Computing 2026.**

These works establish that probabilistic contracts, quantitative refinement,
compositional satisfaction, stochastic specifications, and additive loss
reasoning are not new contributions of this project. The Hampus--Nyberg line
is particularly broad: the 2026 journal metadata and abstract describe a
fully trace-based theory with general probability measures, continuous time,
and continuous state spaces, together with deductive decomposition rules.
The present finite one-step semantics is not claimed to subsume that theory,
and the paper does not assert a formal non-encoding in either direction.

The retained result is narrower: under one explicitly stated robust-context
quantifier pattern, the paper identifies the exact quotient as a directed
order-coupling deficiency and gives a target-law relational context that
attains it for set-valued contracts. This is an exact scoped characterization,
not the invention of probabilistic contracts.

**Hypercontracts** and general assume--guarantee contract literature are cited
because a sufficiently expressive hyperproperty formalism can represent much
richer structures than the finite laws here. No impossibility or expressivity
separation against those frameworks is claimed.

## Stochastic order, coupling, and optimization

**Strassen 1965; Lindvall 1999; Fill and Machida 2001; Thorisson 2000;
Villani 2003.**

The existence of monotone couplings, upward-set characterizations of finite
stochastic order, coupling constructions, and optimal-transport viewpoints
are established mathematics. The manuscript's point-law dual specializes
these facts to boundary-preserving finite rows. It gives a self-contained
finite proof so that the exact sign and boundary decomposition are auditable,
but does not claim Strassen's theorem, max-flow/min-cut, or coupling as new.

**Schrijver 1986 and Rockafellar 1970.**

Finite LP strong duality, convexity, and extreme-point facts are standard. The
certificate producer may use a numerical LP only to find a candidate;
acceptance requires exact rational primal, transport, and dual feasibility
with equal objectives. Thus a replay does not trust numerical solver status,
although the mathematical generator-reduction theorem still relies on
standard convex analysis.

## Probabilistic testing and relational reasoning

**Deng, van Glabbeek, Hennessy, and Morgan 2008; earlier probabilistic testing
work; Barthe and collaborators on probabilistic relational Hoare logic and
coupling product programs.**

Tests, behavioral preorders/metrics, relational reasoning, and coupling proofs
all predate this project. The manuscript's phrase “relational test” is a
description of the concrete target-law frame, not a priority claim for
relational testing. The paper proves completeness only for its finite
one-step monotone robust-floor semantics. It does not reconstruct a process
calculus, scheduler model, temporal logic, or general probabilistic program
logic.

The Boolean-square separation establishes a precise local fact: lower
probabilities of all fixed one-sample upward events do not determine the
chosen set-contract quotient, whereas a target-dependent correlated frame
witnesses loss `1/4`. It is not an impossibility theorem for richer testing or
contract languages.

## Information order and outcome observations

Finite posets and upward-closed sets are standard order-theoretic objects.
The outcome order in the paper is part of the contract: it says which declared
observations count as improvement. The artifact does not learn this order
from data and does not claim that coordinatewise order is universally correct
for AI infrastructure. Principal-upset separation is used to explain why the
full finite joint law is recoverable from all upward-event probabilities; it
is not presented as a new order-theory theorem.

## Directed Kantorovich liftings, powerdomains, and coalgebraic metrics

**Goubault-Larrecq's Kantorovich--Rubinstein quasi-metric series (2021--2023),
Fritz and Perrone's ordered Kantorovich monad (2020), Wild and Schröder's fuzzy
lax extensions (2022), Goncharov and collaborators' characteristic logics
(2023), and Wild and collaborators' generalized duality (2026).**

These papers are the strongest close mathematical boundary found after the
initial draft. They establish asymmetric Kantorovich liftings, Hoare/Smyth and
convex powerdomain constructions, coalgebraic behavioural hemimetrics and
logics, and a generalized duality for convex sets of distributions. The
manuscript therefore does not claim novelty for a directed point cost, a
sup--inf lifting over contract sets, convex distribution sets, or
Kantorovich-style duality by themselves.

The retained scoped result is the representation theorem for the paper's
specific robust contextual floor: shared boundary state, arbitrary compatible
component--frame dependence, bounded monotone use of the outcome, set-valued
old and new contracts, and a target-law relational frame attaining the inner
value. The certificate stack and dependency-scope calculus are an integration
for that semantics, not a claim to subsume the cited general frameworks.
No priority, non-encodability, or strict expressiveness theorem is asserted.

## Dependency scopes and marginal extension

**Vorob'ev 1962; Beeri, Fagin, Maier, and Yannakakis 1983; Lauritzen and
Spiegelhalter 1988; Lauritzen 1996; Shafer and Shenoy 1990.**

Consistent marginal extension on acyclic scope structures, running
intersection, join trees, and the failure of pairwise consistency on cycles
are established. The paper uses the join-tree theorem as the exact sufficient
scope condition for gluing finite component/frame laws. Its three-variable
parity cycle is a transparent negative control, not a new complexity result.

The source-format front end checks one finite closed-scope discipline. It does
not infer graphical-model structure, solve arbitrary cyclic marginal
problems, or prove a compiler correct.

## Convexity, credal sets, and contract meaning

Troffaes and de Cooman's 2014 book *Lower Previsions* (DOI
`10.1002/9781118762622`, print ISBN `9780470723777`) is the explicit
imprecise-probability anchor. Its finite-space development records the
one-to-one correspondence between coherent lower previsions and closed convex
subsets of the probability simplex. The manuscript therefore treats sets of
laws, lower expectations, and event-wise lower probabilities as inherited.
Its specific object is the additional minimization over all shared-boundary
component--frame couplings and the resulting target-dependent relational
substitution quotient.

A list of generators in the order task denotes one global convex hull. This is
not a neutral compression of an arbitrary nonconvex contract: it asserts that
global randomized implementations belong to the contract. The paper's
interior-mixture examples and exact checks distinguish global convex mixtures,
boundary-wise rectangular mixtures, and fresh per-execution modes. Existing
convex powerdomain and probabilistic-nondeterminism work is cited; convex sets,
lower previsions, and Kantorovich/Hausdorff liftings are not claimed as new
mechanisms.

## Venue calibration versus scientific evidence

The `research-plan.md` calibration corpus contains 12 full TOPLAS articles,
five influential theory anchors, and five adjacent full papers. That corpus
was used to calibrate exposition: concrete motivating failures, explicit
semantic choices, theorem dependency, proof architecture, practical examples,
appendix use, bibliography breadth, and the role of figures/tables. It is not
used as evidence for the main theorem and is not a statistical sample of
accepted-paper quality. No award status, bibliography median, or acceptance
probability is inferred.

## Current official and software resources

The paper uses the unmodified supplied `acmart` 2.20 class, dated 16 August
2026, and the unmodified ACM bibliography style. The class and its LPPL notice
are retained in the paper package; no fonts are included. The scientific
artifact is independent of TeX.

`src/order_run.py` uses SciPy's `linprog` only to locate a candidate. The
order replay checker imports neither SciPy nor the producer and checks every
rational equation.  The expectation/minimax mathematics inside
`tests/independent_contract_oracle.py` is independently implemented with exact
fractions, but that script's differential driver imports and calls both the
SciPy-backed producer and the replay checker. Python and SciPy are software
dependencies, not scholarly baselines.

## AI-use and review boundary


A proof in this package supports a mathematical statement only under the
stated assumptions. A finite replay supports a finite implementation result.
Neither one establishes novelty, acceptance, deployed reliability, or human
authorship approval.

## Minimax source

Maurice Sion's 1958 minimax theorem (DOI `10.2140/pjm.1958.8.171`) is used
only for the compact-convex/finite-action interchange in the pure-versus-mixed
upward-test theorem. The paper states the instantiated payoff and preserves
the distinction between the algebraic mixed dual witness and an admissible
independently randomized client.
