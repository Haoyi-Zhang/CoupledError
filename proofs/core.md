# Boundary-success contracts and exact contextual loss

This document gives ordinary mathematical proofs. The executable certificate
checker replays finite rational witnesses; it does not mechanize these general
proofs. All probabilities below concern a declared finite success-monitor model.
They are not measurements of an AI system.

## 1. Semantic objects and the direction of comparison

Let S be a finite nonempty boundary alphabet. Write k = |S|. A mass point is a
pair (p,a) of vectors indexed by S such that p_s >= 0, sum_s p_s = 1, and
0 <= a_s <= p_s. Its interpretation is p_s = Pr(S=s) and
 a_s = Pr(S=s and G=1), where G is a distinguished Boolean success event.
The vector a is not a vector of conditional probabilities. This convention
makes states of zero probability unproblematic.

A contract C is a nonempty compact set of mass points. Its admissible-prior
domain is A_C = {p : exists a. (p,a) in C}. Its fiber at p is
C_p = {a : (p,a) in C}. We compare an old contract C and a replacement D only
when A_C = A_D = A. In particular, no implication over an empty fiber is used
to establish refinement. Compactness implies that every nonempty fiber is
compact. Convexity is not needed for the main testing identity; it is needed
for the finite-generator reduction below.

A context at prior p consists of a finite alphabet T, a fixed law q(s,t) with
S-marginal p, and a Boolean function h(s,g,t) that is monotone in g. The allowed
joint laws are *all* laws on S,G,T with (S,G)-marginal represented by some
(p,a) in C and (S,T)-marginal q. They need not make G and T conditionally
independent given S. The robust reliability R_C(q,h) is the minimum of
Pr[h(S,G,T)=1] over these laws. The feasible set is nonempty, as is shown
constructively below, and is compact.

Define the directed loss

  Delta(C,D) = sup_{p in A, q,h at p} (R_C(q,h) - R_D(q,h))_+ .

The old contract is the first argument. Thus improving the success mass never
incurs positive loss. This number compares two *robust certified floors* in
the same context class. It does not upper-bound the difference between two
observed or otherwise more precisely known implementation reliabilities.

## 2. The finite gluing fact

**Lemma 1 (gluing with a prescribed coupling).** Let mu be a law on X,S,G,
and nu a law on S,T. Given any joint law zeta on S,G,T whose (S,G) marginal
is mu's marginal and whose (S,T) marginal is nu, there is a law on X,S,G,T
with marginals mu and zeta.

**Proof.** For each (s,g) with mass m(s,g)>0, set

  omega(x,s,g,t) = mu(x,s,g) zeta(s,g,t) / m(s,g).

For a zero-mass (s,g), set all the corresponding omega cells to zero.
Nonnegativity is immediate. Summing over t gives mu, and summing over x
gives zeta. These identities also show normalization. No claim that the
original variables were independent is made: this is one constructed
extension used to prove existence inside the allowed all-coupling class. QED.

A second application can preserve a frame's hidden variables as well. For
finite spaces, this elementary fact suffices; no regular conditional
probability or measure-theoretic extension theorem is needed.

## 3. Binary overlap and context normalization

**Lemma 2 (exact overlap).** At one boundary state with total mass p, success
masses a,b in [0,p] admit precisely the joint-success masses

  max(0,a+b-p) <= z <= min(a,b).

**Proof.** The four cells (G,H)=(1,1),(1,0),(0,1),(0,0) must have masses
z, a-z, b-z, p-a-b+z respectively. Nonnegativity gives the stated interval.
Conversely those four masses are nonnegative and have the required marginals
for every z in the interval. The interval is nonempty because a,b <= p.
For p=0 all four masses are zero. QED.

Define

  f_p(a,b) = sum_s max(0,a_s+b_s-p_s),
  F_C(p,b) = min_{a in C_p} f_p(a,b),  for 0 <= b <= p.

Lemma 2 applied separately to each s proves that F_C is the exact lower
probability of G and H when H has boundary-success masses b. Compactness of
C_p and continuity of the hinge function give an attaining a.

**Lemma 3 (normal form for a monotone context).** For a fixed context (q,h),
let U_s = {t : h(s,0,t)=1} and
V_s = {t : h(s,0,t)=0 and h(s,1,t)=1}. Set

  u = sum_{s,t in U_s} q(s,t),
  b_s = sum_{t in V_s} q(s,t).

Then R_C(q,h) = u + F_C(p,b).

**Proof.** Monotonicity excludes the pair of values (h(0),h(1))=(1,0).
Thus h(s,g,t) is exactly the disjoint disjunction of t in U_s and
(g=1 and t in V_s). For any a, Lemma 2 gives the lower bound
u + f_p(a,b). To attain it, put r_s=max(0,a_s+b_s-p_s). Within V_s allocate
G=1 mass r_s proportionally to q(s,t), and within the complement of V_s
allocate G=1 mass a_s-r_s proportionally to q(s,t). Both allocation fractions
are in [0,1]: r_s<=b_s and 0<=a_s-r_s<=p_s-b_s. A zero denominator has zero
required mass and is assigned zero. The resulting law preserves q and has
success mass a_s at s. It attains the lower bound. Minimize over the compact
fiber. If the component and frame have hidden variables, Lemma 1 lifts the
constructed law while preserving their specified local marginals. QED.

Every b with 0<=b<=p is itself a realizable context: take a Boolean H with
Pr(S=s,H=1)=b_s and h=G and H. Therefore the supremum over all finite monotone
contexts equals the supremum over these conjunction testers. This is a claim
about the particular all-coupling semantics defined here, not about arbitrary
probabilistic process calculi or arbitrary observations of component outputs.

Allowing a context to choose from a compact set of fixed laws does not enlarge
the loss. For any family {q_i,h_i}, a uniform inequality R_C(q_i,h_i) <=
R_D(q_i,h_i)+epsilon implies the same inequality after taking both infima.
Fixed contexts already furnish all the separating witnesses needed below.

## 4. Exact directed contextual loss

For vectors in the same fiber write rho(c,a)=sum_s max(0,c_s-a_s), and
 d_C(p,a)=min_{c in C_p} rho(c,a).

**Theorem 4 (exact loss and complement testers).** For nonempty compact
contracts with the same admissible-prior domain,

  Delta(C,D) = sup_{(p,a) in D} d_C(p,a).

For every particular (p,a) in D, the Boolean conjunction tester with b=p-a
has R_D=0 and R_C=d_C(p,a). Consequently every strictly positive lower bound
on the right-hand supremum has a concrete finite separating context.

**Proof, upper bound.** For real x,y,z, (x+z)_+ <= (y+z)_+ + (x-y)_+.
Summing componentwise gives
 f_p(c,b) <= f_p(a,b)+rho(c,a).
For any fixed p,b choose a in D_p attaining F_D(p,b), and then c in C_p
attaining d_C(p,a). It follows that
 F_C(p,b) <= F_D(p,b)+d_C(p,a)
              <= F_D(p,b)+sup_{(p',a') in D} d_C(p',a').
Lemma 3 cancels the same u on both sides for every context. Taking the
positive part and supremum proves the upper bound.

**Proof, lower bound.** Fix (p,a) in D and take b=p-a. Then b is a valid
boundary-success mass vector, f_p(a,b)=0, and all probabilities are
nonnegative, so F_D(p,b)=0. Moreover
 F_C(p,b)=min_{c in C_p} sum_s (c_s-a_s)_+ = d_C(p,a).
Take the supremum over the chosen points of D. QED.

This proof does not exchange a maximum and a minimum. It does not infer
attainment of the joint supremum merely from compactness of D: fibers can
change with p. Attainment is established separately for finitely generated
convex contracts in Theorem 9.

**Corollary 5 (zero-loss criterion).** Delta(C,D)=0 exactly when for every
(p,a) in D there is c in C_p with c<=a componentwise.

**Proof.** Each minimum defining d_C is attained and has a nonnegative
objective. Its value is zero exactly when all the positive differences vanish.
Theorem 4 completes the argument. QED.

At each p this is containment of D_p in the upward closure of C_p, restricted
to [0,p]. It is not ordinary containment in C_p. For example the singleton
success mass 3/4 has zero loss relative to the singleton 1/4 at k=1, although
neither singleton contains the other.

**Corollary 6 (triangle inequality).** Delta(C,E) <=
min(1, Delta(C,D)+Delta(D,E)) whenever all three prior domains coincide.

**Proof.** The scalar positive-part inequality gives
rho(c,e)<=rho(c,d)+rho(d,e). For a fixed (p,e) in E, choose a minimizing
witness d in D_p and a minimizing witness c in C_p for that d. Their two
costs are bounded by the corresponding global deltas. Minimize over c and
then take the supremum over E. The independent bound 1 follows from
rho(c,e)<=sum_s c_s<=1. QED.

Reflexivity follows by choosing c=a. Symmetry does not hold. Mutual zero
loss identifies contracts with the same fiberwise upward closure, not
necessarily the same set of distributions.

## 5. Composition, hiding, and fanout

For contracts C,K define C tensor K to contain (p,z) exactly when there are
(p,a) in C and (p,b) in K such that, for every s,

  max(0,a_s+b_s-p_s) <= z_s <= min(a_s,b_s).

Its prior domain is the intersection of the two prior domains. An empty
intersection is an incompatible composition, not a valid contract. This is
the success-monitor AND operator under all compatible couplings; it is not
an assertion that two source-language computations may be reordered.

**Lemma 7 (exact composition).** C tensor K is exactly the set of mass points
of G and H for joint laws with the two specified local marginal contracts.
It is compact, and is convex when the two inputs are convex.

**Proof.** Necessity and sufficiency follow from Lemma 2 at every state.
The defining extended set is a closed subset of a compact product, and the
projection to (p,z) preserves compactness. The same constraints can be written
as linear inequalities z>=0, z>=a+b-p, z<=a, z<=b, so the extended set and
its projection are convex when the input contracts are convex. QED.

**Theorem 8 (nonexpansive frame and structural laws).** On a nonempty common
prior-domain intersection,
 Delta(C tensor K, D tensor K) <= Delta(C,D).
The operator is associative and commutative. The contract {(p,p):p in A}
is its identity on domain A, and {(p,0):p in A} is absorbing.

**Proof of the inequality.** Take an arbitrary (p,z) in D tensor K, and
witness it by (p,a) in D and (p,b) in K. Choose c in C_p minimizing
rho(c,a), and let z'_s=max(0,c_s+b_s-p_s). Lemma 2 makes (p,z') a member
of C tensor K. The hinge inequality and the lower bound on z give
 (z'_s-z_s)_+ <= (c_s-a_s)_+.
Sum and apply Theorem 4. Restricting the prior domain can only lower the
supremum, which handles frames whose prior domain is smaller than A. QED.

**Proof of the laws.** Commutativity and the identity/absorbing laws follow
directly from the overlap interval. For associativity, interpret either
parenthesization as a law on S and three success bits. An outer coupling
of the prefix-AND bit with the third bit can be lifted to the two original
prefix bits by Lemma 1, using (S,prefix-AND) as the gluing coordinate.
Conversely any full three-bit law gives both intermediate marginals. Both
parenthesizations therefore project precisely the same set of full laws
onto the three-way conjunction. QED.

Successive replacements incur at most min(1,sum_i epsilon_i) loss by
Theorems 8 and 6. This accumulation is sharp even at k=1: let every old
component always succeed and let replacement i have failure probability
epsilon_i. Failure events can occupy consecutive intervals of lengths
epsilon_i on the unit circle. If their lengths sum to at most 1 they are
disjoint; if the sum is at least 1 their union covers the circle. The worst
new conjunction probability is max(0,1-sum_i epsilon_i). This construction
is simply sharpness of the classical marginal-only union bound, not a new
probabilistic inequality.

For a deterministic boundary map pi:S->T, push forward p and a by summing
over pi's fibers, and push forward the whole contract without separately
mixing its rows. Then
 Delta(pi_* C,pi_* D) <= Delta(C,D).
Indeed a new pushed-forward point has a preimage (p,a) in D. Push forward
an old witness c at that same p. The inequality
 (sum_{pi(s)=t}(c_s-a_s))_+ <= sum_{pi(s)=t}(c_s-a_s)_+
shows that the deficit cannot increase. This theorem applies only when the
outside context observes the coarser boundary. It does not justify hiding a
variable that the unchanged context still observes.

One underlying success event G may occur syntactically many times in h.
As long as the resulting Boolean function is monotone in that *same* bit,
Lemma 3 still applies and the replacement charge is incurred once. Separate
executions with distinct success events are not aliases and must be composed
as distinct events. In particular G or G has probability Pr(G), not the
probability computed by substituting two independently drawn bits.

## 6. Exact finite-generator reduction

A rational V-contract is the convex hull of a finite nonempty list of
rational mass points. The list need not be irredundant and its entries need
not be extreme points. All coordinates of a point use the same convex
weights, including its prior coordinates.

**Theorem 9 (new generators suffice).** Let C,D be convex compact contracts,
and let D=conv{(p^i,a^i):1<=i<=n}. Then

  Delta(C,D) = max_i d_C(p^i,a^i).

**Proof.** For two feasible points (p,a),(p',a'), take minimizing old
witnesses c,c'. Convexity of C puts theta*c+(1-theta)*c' in the fiber at
 theta*p+(1-theta)*p'. Convexity of the positive-part function gives

 d_C(theta*(p,a)+(1-theta)*(p',a'))
 <= theta*d_C(p,a)+(1-theta)*d_C(p',a').

Iterating proves that the value at every convex combination of D's
supplied generators is bounded by the largest generator value. Every
supplied generator belongs to D, so equality follows from Theorem 4. This
also proves attainment, including when admissible priors vary. QED.

There is no corresponding rule that minimizes over only old supplied
generators. At p=(1/2,1/2), take old successes (1/2,0) and (0,1/2), and a
new success vector (1/4,1/4). Either old generator has deficit 1/4, but their
midpoint has deficit zero. The old minimization must retain convex mixtures.

Prior domains are convex hulls of the supplied p-generators. Equality of
two such domains is established by convex-combination witnesses placing
every generator of each domain in the other one. Necessity follows from
containment; sufficiency follows by composing the convex weights.

## 7. Linear programs and replay certificates

For old generators (p^j,c^j), fixed (p,a), and m old generators, the primal is

  minimize sum_s t_s
  subject to lambda_j>=0, sum_j lambda_j=1,
             sum_j lambda_j p^j_s=p_s,
             t_s>=0, t_s>=sum_j lambda_j c^j_s-a_s.

Its value is exactly d_C(p,a). Its dual, with free y_0,y_s and box-constrained
w_s, is

  maximize y_0 + sum_s p_s y_s - sum_s a_s w_s
  subject to 0<=w_s<=1,
             y_0 + sum_s p^j_s y_s <= sum_s c^j_s w_s  for every j.

**Lemma 10 (weak-duality replay).** For any primal-feasible and dual-feasible
vectors, the dual objective is at most the primal objective. Equality
certifies their common optimal value.

**Proof.** Multiply the j-th dual inequality by lambda_j and sum. The
normalization and prior equalities yield
 y_0+p*y <= sum_s w_s(sum_j lambda_j c^j_s).
Subtract a*w. Since 0<=w_s<=1 and t_s is nonnegative and bounds the
corresponding difference from above,
 w_s(sum_j lambda_j c^j_s-a_s) <= t_s.
Summing proves the inequality. Any feasible pair with equal objectives
therefore sandwiches the infimum and supremum at that value. QED.

The replay checker tests these explicit equalities and inequalities using
rational arithmetic. It checks domain equality, one primal-dual pair per
new generator, the maximum of all certified values, and b=p^i-a^i for a
maximizing generator. It does not trust the search procedure's branching,
linear-system enumeration, or search counters. The proof of its mathematical
meaning is Lemma 10 followed by Theorems 9, 4, and 3. The current Python
implementation is not itself verified in a proof assistant.

**Theorem 11 (termination and completeness of the exact search).** For
finite rational V-contracts of equal prior domain, the unbounded-arithmetic
arrangement search followed by dual active-set search terminates and finds
such a certificate.

**Proof.** Fix a target new generator. The lambda-feasible set is a
nonempty compact polytope. Subdivide it by the hyperplanes
sum_j lambda_j c^j_s=a_s. On every resulting cell the hinge objective is
linear. It attains its minimum at a vertex of some nonempty cell. After
selecting independent prior/normalization equalities, a cell vertex is
specified by enough linearly independent active hyperplanes chosen from
lambda_j=0 and the hinge hyperplanes. Exhaustively enumerating those
square systems and checking *all* original equalities therefore finds an
optimal lambda, including a mixture interior to the old-generator hull.

The corresponding linear program has an attaining finite optimum, so
finite-dimensional linear-programming strong duality gives an attaining
dual optimum. For completeness of active-set enumeration, let E contain
only independent equality rows and use y only for those rows. Any lineality
direction in this reduced dual polyhedron must have zero w-coordinate
because w lies in a box, and must satisfy E^T dy=0 because both directions
obey all generator inequalities. Full row rank of E implies dy=0. Thus
the dual polyhedron is pointed. A nonempty optimal face of a pointed
polyhedron contains a vertex. That vertex is specified by an independent
set of as many active inequalities as variables. The dual search enumerates
all such sets and recognizes the exact primal-dual equality. Restore zero
multipliers for discarded dependent equality rows. There are finitely many
systems in both searches and exact Gaussian elimination terminates on
each. Domain-containment witnesses are found by the same vertex argument
on the simplex/prior equality polytope. QED.

Strong linear-programming duality and elementary polyhedral vertex facts
are standard ingredients. The source implementation has explicit resource
and representation limits, stated next; this theorem is not a claim that
large finite contracts are computationally small.

## 8. The bounded executable fragment

The runner accepts one to four boundary states, one to five supplied
generators per contract, and rational strings. The least common multiple Q
of all reduced input denominators across *both* contracts must be at most
65536. Certificate rationals have at most 256 numerator and denominator
bits and textual length at most 160. Each JSON file is at most one MiB.
Duplicate keys and malformed shapes are rejected.

**Lemma 12 (certificate-size sufficiency).** Every valid equal-domain input
in this fragment has a certificate whose rational fields fit those limits.

**Proof.** All input masses lie in [0,1]. Multiplying any row of a square
basic system by Q produces integer coefficients and right-hand sides
bounded in absolute value by Q. The primal and prior-witness systems have
order at most 5. The reduced dual has at most r+k<=9 variables; this loose
bound already suffices. A nonzero integer determinant has absolute value
at least 1. By the Leibniz formula, a determinant of order n is at most
n! Q^n in absolute value. Cramer's rule therefore bounds each numerator
and denominator of a basic dual coordinate by 9! (2^16)^9 < 2^163.
For primal coordinates the bound is 5! (2^16)^5 < 2^87.

All basic coordinates for one system share its determinant as a common
denominator before reduction. Primal slacks and their sum have denominator
dividing Q times that determinant, hence fewer than 103 bits; their values
are in [0,1]. A dual objective can be represented with denominator Q times
its basic determinant and also equals a number in [0,1]. These quantities
are comfortably below 256 bits. Restored equality multipliers are either
basic coordinates or zero. The countercontext has denominator dividing Q.
A signed numerator/denominator pair of at most 256 bits each needs at most
158 characters, including a sign and slash. The actual finite certificate
contains at most five proof records with at most nineteen rational vector
entries each, plus short domain witnesses and metadata, far below one MiB.
QED.

The maximum primal arrangement count is at most binomial(9,4)=126. The
dual search uses at most thirteen inequalities in at most nine variables;
its number of candidate square systems is at most max_r binomial(13,r)=1716.
These are encoding-specific bounds, not asymptotic claims for unrestricted
polytope representations. Process limits can still stop a damaged or
unexpectedly slow run; a stopped search is not a negative theorem result.

## 9. From finite dependency specifications to the interface

Let B,L,R be disjoint sets of finite-valued variables, with a distinguished
Boolean interface variable G outside them. A local specification constrains
a law on B,L,G, and a frame specification constrains a law on B,R. A constraint
is an interval on an expectation of a finite Boolean expression; its scope
is the set of variables read by that expression. Hard relations are the
special case whose expected truth value is one. The local specification
may define G as a deterministic success predicate of B,L.

The closure condition requires every law constraint to lie wholly inside
B,L,G or wholly inside B,R. The frame's *monitor* may read G, but its law
constraints may not impose a further relation between G and R. Every
boundary variable shared across the two specifications remains in B. Local
private variables are not read directly by the frame monitor. The monitor
must be monotone in G; it can otherwise be arbitrary on B,R.

**Theorem 13 (closed-interface adequacy).** Let C be the exact projection of
the local feasible-law set to (Pr(B=b),Pr(B=b,G=1)). Fix any feasible frame
law. Under the closure condition, the feasible joint laws projected to B,G,R
are exactly all the compatible couplings of a point of C with that frame
law. Thus the contextual-loss theorem gives a sound replacement rule for
this finite specification language.

**Proof.** Any full feasible law has local and frame marginals satisfying
their respective constraints, because each constraint reads variables on
only its side. This proves one inclusion. Conversely, choose a local law
witnessing a point of C and any compatible coupling with the frame law.
Lemma 1 extends the coupling to L while preserving the whole local marginal
and whole frame marginal. Every constraint is preserved by the closure
condition, proving the other inclusion. The monitor normal-form lemma and
Theorem 4 now apply. QED.

The condition is a sufficient syntactic test, not a characterization of all
possible semantically valid abstractions. A crossing constraint may be
redundant, in which case the simple test still rejects it. Mere freshness
of variable names never proves probabilistic independence. Conversely,
unspecified correlation is fully admitted by the all-coupling class and is
not a reason to reject otherwise closed scopes.

The executable front end validates finite Boolean expression scopes,
checks the monitor's monotonicity exhaustively on its declared finite
Boolean inputs, and projects explicitly supplied rational joint-law
generators. It does not discover all vertices of arbitrary expectation-
constraint polytopes. Theorem 13 covers exact projections mathematically;
the implementation's exact input route is the supplied-generator route.

## 10. Necessary distinctions and explicit counterexamples

**Lost boundary.** At p=(1/2,1/2), old a=(1/2,0) and new a=(0,1/2) have the
same scalar success probability 1/2, but Delta=1/2. The tester b=(1/2,0)
attains the difference. Hiding both states into one yields zero loss only
for contexts that also lose access to the original distinction.

**Nonmonotone use.** At k=1, old success 1/4 and new success 3/4 have zero
loss, but the context not G loses 1/2. Its violation of monotonicity is
essential, not a numerical defect in the certificate.

**Unrecorded crossing dependence.** Let F be a fair shared bit. One local
implementation has G=F and another G=not F, while the frame has H=F.
Without exposing F both local scalar contracts say success 1/2 and their
all-coupling AND floors are both zero. With the actual crossing relations,
old G and H succeeds with probability 1/2 and new G and H with probability
zero. It is invalid to transfer the old extra-information floor through a
contract that forgot the crossing relation. Exposing F distinguishes the
mass vectors and restores a loss of 1/2.

**Product estimate.** Two success events of probability 3/4 each can have
joint success 1/2 (disjoint failures), below the product 9/16. Therefore
the product is not a generally sound AND lower bound. For one fair success
bit reused twice, G or G has probability 1/2, whereas replacing its two
occurrences by independent fair bits gives 3/4. The latter changes the
program's event identity as well as its dependence assumption.

**Row rectangularization.** The old convex hull with generators (1/2,0)
and (0,1/2) at fixed p contains no zero-success vector: every point has
scalar success 1/2. Taking independent coordinatewise intervals adds
(0,0). This is a sound outer relaxation of the set of laws but can strictly
weaken reliability guarantees and hide harmful replacements. It is not
an exact representation of the original contract.

**Actual outcomes versus sufficient monitors.** A finite payload circuit
can have two errors cancel. Its all-stage success monitor remains false
on that run although its final output equals the reference. The monitor
probability is a sound lower bound but is not then the actual probability
of output equality. The included pipeline oracle checks the implication
pointwise rather than equating these quantities.

**Changed prior domain.** If old allows only p=(1,0) and new only p=(0,1),
comparing no shared fibers would establish nothing. The checker rejects the
comparison instead of interpreting a vacuous condition as zero loss.

These examples delimit the result. They do not demonstrate a deployed
cache, a real index, empirical model accuracy, operational reliability,
or a general proof-assistant-verified calculus.

## 11. When convexification is a valid abstraction

Fix one boundary prior p. For a nonempty compact set C of success vectors in
[0,p], let U(C)={u in [0,p] : some c in C satisfies c<=u}. In this section
contracts have only this one prior. This is not a claim about arbitrary
changing-prior domains or arbitrary source-language probabilistic choice.

**Theorem 14 (convexification and generator checking).** The following are
 equivalent:

1. U(C) is convex.
2. C and conv(C) have the same robust floor in every finite monotone context.
3. For every finite nonempty list E of success vectors in [0,p], the exact
   loss from C to conv(E) is the largest loss from C to a singleton in E.

**Proof.** Convexity of U(C) implies conv(C) is contained in U(C). Conversely,
if conv(C) is contained in U(C), take u,v in U(C) with witnesses c,d in C.
Every mixture of c,d has a witness in C below it. The same witness is below
the corresponding mixture of u,v, which therefore lies in U(C). Hence
these two conditions are equivalent.

In finite dimensions conv(C) is compact. This follows, for example, by
representing every convex combination by at most k+1 points: if more have
positive weights, affine dependence permits shifting the weights until
one becomes zero without changing the combination, and iteration reduces
the number. The resulting image of C^(k+1) times the compact simplex is
compact. Theorem 4 and its zero-loss criterion can therefore be applied.
Since C is included in conv(C), the latter has no larger floor. Equality
of all floors is equivalent to zero loss in the other direction, which
is precisely conv(C) being contained in U(C). This proves 1 iff 2.

If 1 holds, then d_C(a)=d_conv(C)(a). For any c' in conv(C), choose c in C
with c<=c'; this never increases rho(c,a). The reverse inequality follows
from set inclusion. Theorem 9 applied to conv(C) now proves 3.

For the converse, apply 3 to any two points c,d in C. Both singleton losses
are zero, so every mixture of c,d must belong to U(C), by Theorem 4. For
u,v in U(C), choose such c<=u and d<=v. The witness for each mixture of c,d
also witnesses the corresponding mixture of u,v. Thus U(C) is convex. QED.

The distinction is operationally consequential even with only two boundary
states. Let C consist of the two points (1/2,0),(0,1/2), without their
mixtures, and p=(1/2,1/2). For a(lambda)=(lambda/2,(1-lambda)/2),

 d_C(a(lambda)) = min(lambda,1-lambda)/2.

The two supplied endpoints each have zero loss, whereas their midpoint
has loss 1/4. For b=(1/4,1/4), the old floor is 1/4 and the convexified
floor is zero. Thus new-generator checking is unsound when the old
contract denotes a nonconvex set of alternatives. The implemented V-format
always denotes a convex hull; interpreting its list as pure demonic
alternatives would change its semantics, not reveal a numerical bug.
The theorem gives an exact boundary for this particular abstraction but
does not establish its originality relative to existing testing semantics.

## 12. Fresh and ambient-correlated randomization differ

Let c^1,...,c^m be success vectors at the same prior p. Fix a probability
vector lambda and a context law q(S,T). Introduce a mode M with
Pr(M=j,S=s,G=1)=lambda_j c^j_s and Pr(M=j,S=s)=lambda_j p_s.
An additional fresh-mode condition requires

 Pr(M=j,S=s,T=t)=lambda_j q(s,t).

This condition explicitly rules out correlation between M and the frame
conditional on S; absence of a shared variable name would not establish it.

**Lemma 15 (fresh-mode floor).** Under this condition, for any monotone
monitor h the robust floor equals sum_j lambda_j R_{c^j}(q,h). If lambda
may be chosen nondeterministically, its minimum equals min_j R_{c^j}(q,h).

**Proof.** For every positive lambda_j, condition the full law on M=j.
The resulting local success marginal is c^j and the resulting context law
is q. Its monitor probability is at least R_{c^j}(q,h). Taking the weighted
sum gives the lower bound. Conversely take a minimizing compatible coupling
for each positive-weight mode, tag it with M=j, and mix with weights lambda.
The resulting law has the prescribed local and frame marginals and the
fresh-mode property, and attains the bound. Zero-weight modes have no cells.
Minimizing a convex combination of finitely many numbers over the simplex
selects their smallest one. QED.

Dropping the fresh-mode condition and retaining only the averaged success
vector generally gives a smaller floor: every fresh-mode law is admitted
by the relaxed coupling class, but not conversely. With the two-point C
above, lambda=(1/2,1/2), and a tester fair at both boundary states, the
fresh-mode floor is 1/4 while the averaged all-coupling floor is zero.

The distinction can also be retained by the exposed boundary. Let S,M be
independent fair bits, let G be the indicator of S=M, and let the frame
success H be a fair bit independent of both in the declared frame law.
With (S,M) exposed, p=(1/4,1/4,1/4,1/4), a=(1/4,0,0,1/4), and
b=(1/8,1/8,1/8,1/8); the exact conjunction floor is 1/4. Hiding M yields
p=(1/2,1/2), a=b=(1/4,1/4) and an all-coupling floor of zero. The
coarser contract remains a sound relaxation; it is not a precision-preserving
abstraction of the original fresh-mode specification. No claim is made
that associativity of the abstract AND operator permits moving or deleting
random draws in executable code.


## Binary frame nonexpansivity

For row mass `p`, define `L_p(x,b)=max(0,x+b-p)`.  If a target
conjunction law uses success masses `a,b` and overlap `z'`, then
`z'>=L_p(a,b)`.  For any old success mass `c`, the overlap
`z=L_p(c,b)` is feasible.  Monotonicity and one-Lipschitzness of `L_p` give

    max(z-z',0) <= max(L_p(c,b)-L_p(a,b),0) <= max(c-a,0).

Summing rows, minimizing over the old contract, and maximizing over target
conjunction laws proves `Delta(C tensor K,D tensor K)<=Delta(C,D)`.  This
proof permits every Frechet-compatible overlap and never assumes independence.
