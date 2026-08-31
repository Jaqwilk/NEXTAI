# GEN-1 — family-blind latent-variable identifiability gate, cycle 54

## Scope

This was one design/service-only cycle after valid negative EXP-0053. No experiment plan, candidate implementation, scoring seed, runner invocation, scored result, dependency, external model/API or protected evaluator change was created. The active `heldout_parallel_masked_infilling_v2` cohort and its manifest remain unchanged.

The question was whether the four existing probabilistic, predictive-state, local-dynamics and behavioral-program generators can support a scientifically identifiable test of one family-blind latent-variable learner without constructing a new data-generating contract.

## Observation

The lossless v2 support boundary was audited at every quick cell: K=`8/32`, D=`1/4/6`, fixed training seeds `1103/2207/3301`. A profile containing only support length, counts of the seven public structural markers, example count and query/target arities was evaluated with leave-one-training-seed-out nearest-profile classification.

Every cell classified family identity `12/12`; across all six cells the result was `72/72`. Within each K/D cell there were exactly four profiles among twelve worlds, one constant profile per family across all three seeds. Thus the public boundary omits the family name but deterministically exposes an equivalent router through shape.

Target arity supplies an additional shortcut. At D=4 the four target lengths are `1/5/3/4`; at D=6 they are `1/7/3/6`. At D=1, predictive and local remain distinct at `2/3`, while probabilistic and program both have length 1 but are already separated perfectly by support shape.

The generator audit also found no evaluator-hidden module variable shared across families. Training and test worlds vary seeds inside four independently authored builders. There is no factorial coverage of reusable mechanisms and no held-out combination of mechanisms. Consequently a pooled latent representation can be independently permuted inside each family without changing the likelihood, and apparent success can be implemented as discovered family routing plus four specialists.

## Interpretation

The current four-family boundary cannot discriminate portable latent mechanism discovery from hidden family identification. A low-rank tensor, mixture, slot, set encoder or modular library fitted here would either exploit the shape router or be penalized for pooling unrelated sufficient statistics. Positive and negative outcomes would both be ambiguous, so freezing a v5 wrapper over the same worlds would violate the preregistered identifiability requirement rather than increase information.

This is a defect in the proposed research question/evaluator pairing, not a defect in the frozen v2/v3/v4 historical results. Those cohorts and results remain immutable and interpretable only for their registered mechanisms.

## Rejected design

`shared_low_rank_relation_factorizer` was rejected before implementation. Its proposed family-neutral tensor features and pooled factorization cannot establish sharing when the data contain no repeated latent factors across held-out combinations. Adding padding alone would hide one shape cue but would not create mechanism sharing, and a hand-written cross-family alignment would move the answer into the evaluator ontology.

No HYP-0021 was created and no confidence was changed from this infrastructure observation.

## Minimum valid future contract

A future shared-mechanism cohort must satisfy all of the following before candidate code or preregistration:

1. Reuse at least three existing generator mechanisms, but expose each mechanism in multiple independently relabeled compositions rather than treating a whole family as one module.
2. Provide factorial training coverage and hold out complete mechanism combinations while retaining every constituent mechanism in training.
3. Balance public support, query and target envelopes so the cycle-54 shape classifier is at chance; padding/masks must not encode module or family identity.
4. Hide module IDs, family labels, native types, field names, oracle objects and composition graphs from implementable candidates.
5. Apply runner-random atom relabeling and anonymous-world permutation after source/integrity audit.
6. Include an analytic fixture with two individually observed mechanisms and one unseen composition whose answer cannot be emitted by unigram, finite-order Markov, complete-example nearest-template or a family router.
7. Compare one source-identical pooled learner with independent fitting, a no-cross-mechanism ablation, exact MDL/module-library and contextual Chow–Liu, empirical-joint, autoregressive specialist controls; report the oracle composition graph separately.
8. Charge acquisition, common serialization, structure search/factorization, support adaptation, every query/update, bytes moved, resident/peak state and R1/R4/R16 workload.
9. Require overall and minimum-combination capability, a material pooled advantage over both independent and no-cross-mechanism ablations, and implementable Pareto non-dominance. One seed can only discard or authorize replication.

## Decision

`blocked-by-identifiability` for a latent-variable experiment on the unchanged four-family evaluator. Do not create EXP-0054, do not reactivate v3/v4, and do not implement the rejected factorizer. The active benchmark remains masked-infilling v2 solely as historical active infrastructure; no further HYP-0017 tuning is authorized.

## Exact next discriminating step

Use the next wake as a second service-only cycle, with no plan or scoring, to determine whether `heldout_mechanism_recombination_v1` can be constructed from at least three existing generator mechanisms while satisfying the nine conditions above. The first gate is mechanical: generate fixed development compositions, verify zero train/test combination overlap, run the same shape-only classifier and require accuracy no greater than chance plus `0.10`, then prove the two-mechanism held-out fixture is unsolvable by unigram, order-1 through order-5 Markov and complete-example nearest-template controls. If any gate fails without introducing a hand-written alignment ontology, document the failure and do not freeze the cohort.
