# Cycle 193: stack-depth v9 identifiability correction

## Scope

This is one service-only cycle. No HYP-0050, EXP-20260901-0039 plan, candidate,
runner seed or score was created. The mandatory pre-preregistration audit found
that active v8 could not distinguish its intended mechanism from a first-order
control, so scoring it would have produced non-discriminating evidence.

## Observation

V8 selects the first closing delimiter observed while the true stack has its
maximum depth. In the evaluator's delimiter-only trace there are no intervening
events between that deepest opener and its closer. The frozen fixture
`([{}])` therefore becomes `([{MASK}])` with the single target `}` and visible
left neighbor `{`. A learned bigram pair table can answer it exactly without
representing nesting. This is a structural proof, not a post-score inference.

The flaw affects the scientific interpretation, not corpus integrity. The 48
hashed whole-file roles, tokenization, runner-random permutation, shallow train
boundary and 54/21/6 eligible test traces remain usable.

## Minimal correction

`heldout_parallel_masked_infilling_v9` masks every matching closer along the
first opener chain that reaches exact depth D. The same fixture now masks all
three positions and has simultaneous targets `}])`. At D=`3/4/5`, a candidate
must retain three, four or five opener identities and pop them in order. A
source-identical stack capped at the observed training depth two loses outer
state, while a genuine pushdown representation can extrapolate its learned
transition without a new depth-specific rule.

V9 changes no corpus, file split, tokenization, permutation, training examples,
K values, D values, query allocation, metrics, cost formulas, baselines or
state budget. It changes only the target-position tuple and records D targets
instead of one. Historical v8 is archived and remains unscored.

## Interpretation, confidence and decision

Confidence is high (`0.99`) that v8 is a first-order alias: its selected target
is immediately adjacent to the sufficient opener by construction. Confidence
is high (`0.95`) that v9 separates a two-entry bounded stack from a full stack
on D>2; the exact fixture and corpus regression test this directly. V9 still
tests a narrow real-source syntax signature and cannot support broad language
or intelligence claims.

Decision: activate v9 only after full tests, semantic baselines, preflight,
integrity and doctor pass. The next wake must preregister HYP-0050, implement
the one frozen learned-pair pushdown rule and its two source-identical nulls,
and score exactly one quick. No further no-scoring wake is permitted before
that experiment absent a new integrity failure.
