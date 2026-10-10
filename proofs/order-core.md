# Order-coupling contracts for correlated approximate pipelines

This file contains ordinary finite mathematical proofs.  The executable
certificate checker establishes exact rational equalities for finite inputs;
it does not mechanize these general proofs.  The semantics concerns declared
success observations, not measurements of a trained model or deployed service.

## 1. Point laws, contracts, and contexts

Let `S` be a finite nonempty boundary alphabet and let `(X, <=)` be a finite
partially ordered outcome space.  A point law is a probability mass function
`m(s,x)` on `S x X`.  Write `p_m(s) = sum_x m(s,x)`.  A contract is a nonempty
compact set of point laws.  Its prior domain contains every `p` that occurs as
the `S` marginal of one of its laws, and `C_p` is the fiber with marginal `p`.
Old and replacement contracts are compared only when their prior domains are
equal.

At prior `p`, a context consists of a finite frame alphabet `R`, a law `q(s,r)`
with `S` marginal `p`, and a reward `h(s,x,r)` in `[0,1]` that is monotone in
`x`: if `x <= y`, then `h(s,x,r) <= h(s,y,r)`.  The context fixes no further
dependence between the component outcome and the frame.  For a contract `C`,
its robust floor is

    R_C(q,h) = min E_gamma h(S,X,R),

where the minimum ranges over `m in C_p` and every coupling `gamma` whose
`(S,X)` marginal is `m` and whose `(S,R)` marginal is `q`.  Finite compactness
makes the minimum attain.  The directed contextual replacement loss is

    Delta(C,D) = sup_(p,q,h) (R_C(q,h) - R_D(q,h))_+.

The old contract is the first argument.  The same context law is used on both
sides, but its worst compatible coupling may differ.

## 2. Boundary-preserving order-coupling deficiency

For point laws `m,n` with the same boundary prior, define

    delta(m,n) = min_pi Pr_pi[X not<= Y],

where `pi(s,x,y)` ranges over couplings with `(S,X)` marginal `m`, `(S,Y)`
marginal `n`, and no cross-boundary transport.  This is a directed quantity:
`delta(m,n)=0` means that the replacement law `n` can be coupled above the old
law `m` in the outcome order.

**Lemma 1 (finite gluing).**  Let `pi(s,x,y)` couple `m` and `n`, and let
`eta(s,y,r)` couple `n` and `q`.  There is a law `omega(s,x,y,r)` with
`(S,X,Y)` marginal `pi` and `(S,Y,R)` marginal `eta`.

**Proof.**  For each `(s,y)` with `n(s,y)>0`, set

    omega(s,x,y,r) = pi(s,x,y) eta(s,y,r) / n(s,y).

Put zero in every cell over a zero-mass `(s,y)`.  Summing over `r` gives `pi`;
summing over `x` gives `eta`.  All entries are nonnegative and the total mass
is one.  No independence premise is used.  QED.

**Lemma 2 (one-step monotonicity bound).**  For every `[0,1]`-valued monotone reward,

    h(s,x,r) <= h(s,y,r) + 1[x not<= y].

**Proof.**  If `x<=y`, monotonicity gives the inequality with a zero second
term.  Otherwise the right side is at least one.  QED.

## 3. Exact contextual characterization

**Theorem 3 (order-coupling contextual characterization).**  For nonempty compact
contracts with equal prior domains,

    Delta(C,D) = sup_(n in D) inf_(m in C_{p_n}) delta(m,n).       (1)

For each selected target law `n`, one finite correlated frame realizes the
inner value: take the frame outcome `Y` to have law `n` and use the monitor
`1[X not<=Y]`.

**Proof, upper bound.**  Fix a context `(q,h)` and choose a target law `n in D`
and coupling `eta` attaining `R_D(q,h)`.  Choose `m in C_{p_n}` minimizing
`delta(m,n)`, and let `pi` be an optimal order coupling.  Glue `pi` and `eta`
by Lemma 1.  Its `(S,X,R)` marginal is a feasible old-component/context
coupling.  Lemma 2 therefore gives

    R_C(q,h)
      <= E_omega h(S,X,R)
      <= E_eta h(S,Y,R) + Pr_pi[X not<=Y]
      = R_D(q,h) + delta(m,n).

The final term is at most the right side of (1).  Taking the positive part and
the supremum over contexts proves the upper bound.

**Proof, lower bound.**  Fix `n in D`.  Let the frame alphabet be a disjoint
copy of `X`, let `q(s,y)=n(s,y)`, and set

    h_n(s,x,y) = 1[x not<=y].

For fixed `y`, this monitor is monotone in `x`: if `x<=x'` and `x not<=y`, then
`x'<=y` would imply `x<=y`, a contradiction.  The replacement contract has
floor zero because it may select `n` and use the identity coupling `x=y`.
The old floor is exactly `inf_(m in C_{p_n}) delta(m,n)` by the definition of
`delta`.  Thus this one context realizes the inner value.  Taking the supremum
over `n` proves the lower bound.  QED.

The lower-bound context is relational: it correlates a frame sample with the
replacement target.  This is why a fixed list of ordinary outcome predicates
is not, in general, complete for set-valued contracts.

**Corollary 4 (zero loss).**  `Delta(C,D)=0` exactly when, for every `n in D`,
there exists `m in C_{p_n}` that is stochastically below `n`, equivalently an
order-preserving coupling with `X<=Y` almost surely.

**Corollary 5 (directed triangle).**  If `C,D,E` have the same prior domain,

    Delta(C,E) <= min(1, Delta(C,D)+Delta(D,E)).

**Proof.**  Glue an optimal `m--n` coupling to an optimal `n--ell` coupling.
Transitivity of the order gives

    1[x not<=z] <= 1[x not<=y] + 1[y not<=z].

Minimize over the first law, choose an intermediate law, and take the supremum
over the final contract.  The independent bound one follows because every
cost is Boolean.  QED.

Thus `Delta` is a directed contract hemimetric after quotienting mutual
zero-loss contracts.  It is not symmetric.

## 4. Max-flow and upward-set duality for point laws

Call `U subseteq X` upward closed when `x in U` and `x<=y` imply `y in U`.
For a row subprobability `m_s`, write `m_s(U)=sum_(x in U)m(s,x)`.

**Theorem 6 (finite Strassen deficiency).**  Point laws with common prior obey

    delta(m,n) = sum_(s in S) max_(U upward) (m_s(U)-n_s(U)).      (2)

The empty set supplies zero, so an additional positive-part operator is not
needed.

**Proof.**  Rows do not exchange mass, so optimize each `s` independently.
For one row of total mass `p`, form a network with source capacity `m(x)` into
left outcome `x`, capacity-`p` edges from left `x` to right `y` exactly when
`x<=y`, and capacity `n(y)` from right `y` to the sink.  A flow of value `v`
is precisely an ordered subcoupling of mass `v`; the remaining mass can be
coupled arbitrarily and is the violation probability `p-v`.

A trivial cut has capacity `p`.  Any cut crossing an order edge already pays
`p`, so some minimum cut crosses none: if a crossing cut ties at `p`, replace
it by the trivial cut.  Such a cut is determined by left nodes `A` and right
nodes `B` on the source side and must contain `up(A)` in `B`.  Its capacity is
`m(X\A)+n(B)` and is minimized, for fixed `A`, by `B=up(A)`.  Therefore

    p - maxflow = max_A (m(A)-n(up(A))).

Replacing `A` by `up(A)` cannot decrease the displayed difference, and every
upward set can itself be chosen as `A`.  Max-flow/min-cut gives (2).  Summing
rows completes the proof.  QED.

Equation (2) identifies zero deficiency with the usual stochastic order on a
finite poset.  The paper does not claim this max-flow/min-cut fact as new; its
role is to make the contextual theorem computable and to expose the precise
quantity that set-valued replacement must optimize.

**Binary specialization.**  Let `X={0<1}` and write `c_s=m(s,1)`,
`a_s=n(s,1)`.  The only informative upward set is `{1}`, so

    delta(m,n) = sum_s max(c_s-a_s,0).

The earlier boundary-success theorem is exactly this specialization, not a
separate probability model.

## 5. Why joint outcomes are semantically necessary

For a finite poset, the probabilities of principal upward sets determine the
entire distribution.  Indeed, `F(x)=m(up(x))` is the zeta transform on the
poset incidence algebra; after any linear extension, its matrix is triangular
with diagonal one and is invertible by Möbius inversion.

**Proposition 7 (separation and explicit-state lower bound).**  If two point
laws on the same boundary differ, then a boundary-indexed monotone predicate
distinguishes them.  Consequently, an interface that is fully abstract for all
monotone contexts cannot identify distinct joint outcome laws.  On
`X={0,1}^k`, an explicit tabular or linear-summary representation therefore
needs, in the worst case, the `2^k-1` degrees of freedom of the joint law;
coordinate marginals alone are incomplete.

The qualification about explicit or linear summaries is essential: the claim
is not a bit-complexity lower bound against arbitrary encodings of real
numbers.

A two-bit example makes the semantic issue concrete.  The old retrieval law
puts probability one half on `01` and one half on `10`; the replacement puts
one half on `00` and one half on `11`.  Both coordinate success probabilities
are one half.  The monotone disjunction succeeds with probabilities one and
one half, respectively, so a marginal-only contract misses a loss of one half
within that boundary row.

## 6. Set-valued contracts need relational witnesses

For one fixed upward event `U`, a set contract exposes the floor
`inf_(m in C)m(U)`.  Even the entire family of such one-sample floors can be
strictly less discriminating than Theorem 3 because the minimizing old law may
change with `U`.

Let the outcome order be the Boolean square `00,01,10,11`.  Define

    c1 = 1/2 delta_10 + 1/2 delta_11,
    c2 = delta_01,
    n  = 1/2 delta_01 + 1/2 delta_10,
    C  = conv{c1,c2},       D={n}.

Every fixed upward event has `inf_(c in C)c(U)-n(U) <= 0`; hence direct
one-sample event testing reports zero positive gap.  Write
`c_lambda=lambda c1+(1-lambda)c2`.  Theorem 6 gives

    delta(c_lambda,n)
      = max(lambda/2, (1-lambda)/2, lambda-1/2, 0).

Its minimum is `1/4` at `lambda=1/2`.  The target-law frame of Theorem 3
therefore witnesses contextual loss `1/4`.  If the demonic old contract is the
nonconvex two-point set `{c1,c2}`, its floor in this same target-law context is
`1/2`; enlarging it to `conv{c1,c2}` can only make that old-contract floor
nonincreasing, and here lowers it to `1/4`.  The replacement floor remains
zero, so the contextual loss to the target decreases from `1/2` to `1/4`.
This is a weakening of the old guarantee under a larger demonic contract, not
an improvement of its robust floor.  The example simultaneously shows that
correlated frames add observational power for set contracts and that treating
convexification as a semantic no-op is unsound.

## 7. Pure-versus-mixed upward-test minimax

For a compact convex old fiber and fixed target, choose one upward set per
boundary row as a pure test. The deficiency is the minimum over old laws of
the maximum pure-test payoff. Sion's finite-action minimax theorem equals
this to the maximum over distributions on pure tests of the minimum old-law
payoff. A single fixed test is complete exactly when a pure strategy attains
the mixed game value. The mixed test is an algebraic LP dual witness; under
the all-compatible-coupling semantics, it is not claimed to be an independently
sampled client.

## 8. Convex contracts and exact certificates

Fix a boundary prior.  Let the old contract be the convex hull of generators
`m_1,...,m_g`, and fix a target point law `n`.  Joint convexity of optimal
transport implies that

    f_C(n)=min_(m in C) delta(m,n)

is convex in `n`: its epigraph is the projection of the convex epigraph of
`delta(m,n)` with `m in C`.  Hence for a replacement polytope
`D=conv{n_1,...,n_h}`,

    sup_(n in D) f_C(n) = max_j f_C(n_j).                        (3)

Only supplied replacement generators need certificates.  An old interior
mixture may still be optimal and must not be replaced by endpoint inspection.
For the retained two-generator oracle, “interior required” means that both
endpoint objective values are strictly larger than the minimum.  This holds
for 11 of 99 targets.  A weaker statement, “some interior optimum exists,”
holds for 58 targets because it includes flat minimizer intervals touching one
or both endpoints.  The implementation records both notions, the 31 targets
whose finite breakpoint list explicitly contains an interior minimizer, and
the 20 of those 31 for which an endpoint is also optimal.  Seed 813 and a
constant objective are regression cases for the flat-interval classification.

Enumerate the nonempty upward sets of `X`.  For a target generator, the exact
primal linear program is

    minimize    sum_s t_s
    subject to  lambda_i >= 0, sum_i lambda_i = 1,
                t_s >= 0,
                t_s >= sum_i lambda_i m_i(s,U) - n(s,U)
                    for every boundary row s and upward set U.             (P)

Its dual is

    maximize    alpha - sum_(s,U) z_(s,U) n(s,U)
    subject to  z_(s,U) >= 0,
                sum_U z_(s,U) <= 1               for every s,
                alpha <= sum_(s,U) z_(s,U)m_i(s,U) for every generator i.  (D)

The producer uses a numerical LP only to locate a small rational optimum, then
reconstructs rational values.  A certificate contains the convex weights,
row deficits, a complete transport plan, and dual variables.  The independent
checker, which imports no optimizer, verifies all primal inequalities, both
transport marginals, every order-violation cell, every dual inequality, and
exact equality of the three objectives.  Weak duality then proves optimality.

The implementation enumerates upward sets.  This is practical for its declared
small explicit fragment but can be exponential: Boolean outcome lattices have
Dedekind-many upward sets.  No scalability claim for implicit large component
graphs follows from the finite checker.

## 9. Monotone postprocessing and replacement rules

A monotone map `f:X->Y` preserves order.  Pushing a coupling through `f` cannot
turn an ordered pair into a violation, so

    delta(f_*m,f_*n) <= delta(m,n).                              (4)

More generally, a Markov kernel `K(x)` on `Y` is stochastically monotone when
`x<=x'` implies `K(x)` is stochastically below `K(x')`.  Couple the two output
kernels monotonically on every ordered input pair and arbitrarily on a bad
input pair.  Finite gluing then proves the same nonexpansive inequality for
`K_*`.

These facts yield a small replacement calculus.  Write `C <=_eps D` when
`Delta(C,D)<=eps`.

* every contract satisfies `C <=_0 C`;
* `C <=_eps D` and `D <=_eta E` imply `C <=_(min(1,eps+eta)) E`;
* monotone deterministic and stochastically monotone postprocessing preserve
  the budget;
* every admitted context satisfies `R_C(q,h) <= R_D(q,h)+eps`;
* a sequence of component replacements can be charged by adding their budgets,
  provided each step preserves the declared boundary and dependency scope.

Conjunction, disjunction, threshold voting, projection, and hiding of success
coordinates are monotone maps on Boolean outcome lattices.  Equation (4)
therefore gives their nonexpansivity without multiplying marginal reliability
numbers or assuming independent faults.


### 9.1 Separate binary interfaces and arbitrary overlap

When two binary components are specified separately, their conjunction cannot
be assigned an independent-product probability.  In a boundary row of mass
`p`, success masses `a` and `b` admit exactly the overlap interval

    max(0,a+b-p) <= z <= min(a,b).

Let `C tensor K` contain every conjunction law obtained from `C` and `K` using
an overlap in that interval.  Then

    Delta(C tensor K, D tensor K) <= Delta(C,D).                  (5)

**Proof.**  Fix a target conjunction law with witnesses `a in D_p`, `b in K_p`
and overlap `z'`.  Write `L_p(x,b)=max(0,x+b-p)`, so `z'>=L_p(a,b)`.  For any
`c in C_p`, use the same frame witness `b` and choose the least old overlap
`z=L_p(c,b)`.  This is a valid point of `C tensor K`.  Because `L_p` is
nondecreasing and one-Lipschitz in its first argument,

    max(z-z',0)
      <= max(L_p(c,b)-L_p(a,b),0)
      <= max(c-a,0).

Sum over boundary rows, minimize over `c`, and maximize over target conjunction
laws.  The binary specialization of Theorem 6 yields (5).  No independence
assumption is used.  QED.

## 10. Closed scopes and dependency hypergraphs

### 10.1 Lifting an outcome coupling

Suppose a component has a full law on `(B,L,X)`, where `L` is private, and a
frame has a law on `(B,R)`, where `R` is private. Every law constraint must lie
wholly within `(B,L,X)` or wholly within `(B,R)`, with no additional
outcome-to-frame or private-to-frame law relation. The monitor may separately
read `(B,X,R)` and must be monotone in `X`. Under this complete closed-scope
premise, every coupling of the projected `(B,X)` and `(B,R)` laws
lifts to a full law: multiply the coupling by the component conditional law of
`L` given `(B,X)`, taking zero on zero-mass cells.  Thus the order-coupling
semantics is exact at the declared interface.  A hidden crossing constraint
would invalidate this lifting argument and must be exposed or conservatively
forgotten.

### 10.2 Join-tree extension

Let variables be covered by bags `B_i` arranged as a tree.  Assume the
running-intersection property: bags containing each variable form a connected
subtree.  Give each bag a finite marginal law `mu_i`, and require adjacent bag
laws to agree on their separator.

**Theorem 8 (acyclic local consistency is sufficient).**  These local laws
have a global extension whose marginal on every bag is `mu_i`.

**Proof.**  Root the bag tree.  Start with the root law.  When adding a child
bag, glue the current law and the child law over their common separator.
Separator consistency supplies identical overlap marginals.  If a separator
cell has positive mass, multiply by the child's conditional distribution of
its new variables; if it has zero mass, the current law also assigns zero to
that cell and contributes nothing.  Running intersection ensures that the
child shares with the accumulated variables exactly information already in
the separator, so no previously assigned variable can conflict.  Induction
preserves every installed bag marginal and terminates with a global law.  QED.

Acyclicity is sufficient, not necessary.  In cyclic scope families, pairwise
separator consistency is not sufficient.  For three uniform binary variables,
require `A=B` almost surely on bag `AB`, `B=C` almost surely on `BC`, and
`A!=C` almost surely on `AC`.  All singleton marginals agree, but a global law
would imply both `A=C` and `A!=C`.  The artifact rejects this scope family by
the running-intersection check and separately rejects inconsistent separator
marginals.

The semantic contract of a dependency representation is the set of all global
extensions, not a product distribution.  The join-tree theorem identifies one
important condition under which local probability tables and separator checks
are enough to show that this set is nonempty and construct an exact witness.
For cyclic scopes, a full marginal-polytope method or additional constraints
are required.

## 11. Finite evidence and its limits

The retained campaign performs the following exact checks.

* Four named order-coupling cases (binary specialization, correlated retrieval
  pipeline, relational-witness separation, and a multi-generator convex case)
  replay at loss `1/4`.
* Twenty deterministic rational contracts, seeds 710--729, receive exact
  primal/transport/dual certificates.
* All 35 probability laws with denominator four on the Boolean square produce
  1,225 ordered pairs.  A unit-token exhaustive transport oracle agrees with
  the upward-set formula on every pair.  All 42,875 ordered triples satisfy the
  directed triangle inequality.
* Four independently corrupted order certificates are rejected.
* In the relational-witness example, every direct fixed upward event has gap
  zero while the correlated frame certificate proves loss `1/4`.
* The join-tree constructor builds and replays an eight-cell global law; a
  running-intersection violation and a separator inconsistency are rejected.
* The legacy binary campaign remains intact: 432 exact certificates, an
  integer-table grid oracle, payload truth table, and randomization controls.

These finite checks validate the implementations and selected boundary cases.
They do not prove Theorems 3, 6, 7, or 8, do not constitute an independent
formalization, and do not estimate reliability of any real AI infrastructure.
