# Generation 1 to 2 transition audit — cycle 64

## Scope and evidence set

This was an early reflection/transition cycle with no experiment plan, candidate implementation, scoring seed, runner invocation, result, dependency, external model/API or protected evaluator change. It audited every scored protocol-v2 result and the associated immutable analyses before selecting the next research direction.

Protocol v2 produced twelve scientifically valid scored results across eight benchmark cohorts: EXP-0038, 0040, 0041, 0042, 0043, 0044, 0048, 0050, 0051, 0052, 0053 and 0056. EXP-0046 and EXP-0047 remain terminally invalid and were excluded. Result-less invalid plans EXP-0036, 0037, 0039, 0045, 0049, 0054 and 0055 are process history, not capability observations. Every valid v2 result is a one-seed quick; none supports promotion.

## Cohort reconstruction

| Frozen cohort | Valid results | Best tested proposed mechanism | Strongest implementable classical/control | Privileged oracle or bound | Gap and diagnosis |
| --- | --- | --- | --- | --- | --- |
| `behavioral_conjugacy_library_transfer_v1` | 0038 | learned relational library `1.0` accuracy | exact relational graph MDL `1.0` at lower fit/state/work | `1.0` | zero capability gap; complete transition tables and exact relational fingerprints make the task a classical canonicalization ceiling |
| `context_specific_probabilistic_circuit_v1` | 0040 | learned SPN `1.0` | contextual Chow–Liu `1.0` with lower work | `1.0` | zero gap; learned route implements the same selector/pair factorization |
| `cross_family_shared_representation_v1` | 0041, 0042 | equivariant pointer learner `0.1771`, minimum family `0` | contextual suite up to `0.9792`, minimum family `0.9167` | `1.0` | only `0.0208` overall oracle gap for the specialist; later audit classified family shape `72/72`, so success cannot isolate shared representation from routing |
| `nonstationary_online_update_battery_v1` | 0043 | shared meta-update `0.0545`, minimum mechanism `0.0088` | LMS `0.1548`; every implementable candidate had worst-phase `0` | `1.0` segmented oracle | large nominal gap, but the oracle receives hidden segmentation and short histories leave the regime unidentifiable; not an earned learnable gap |
| `heldout_repository_sequence_compression_v1` | 0044 | hierarchy `4.3276` mean / `5.0099` worst-file bits per byte | CTW `4.2449` / `4.8951`, lower full work | full-file histogram is `4.6079`, not a sequence oracle | valid natural OOD task, but no calibrated attainable lower bound; hierarchy is coordinate-wise dominated by CTW |
| `cross_family_shared_representation_v3` and `cross_family_relation_fragment_transfer_v4` | 0048, 0050, 0051, 0052 | best shared graph `0.2240`, minimum family `0` | contextual suite `0.9896`, minimum family `0.9583` | `1.0` | specialist gap `0.0104`; public family shape is perfectly routable and three shared representations independently collapse |
| `heldout_parallel_masked_infilling_v2` | 0053 | iterative `5.2871` bits/byte, exact-span `0` | unigram `4.8423` aggregate loss; one-pass `4.8758` and lower cost | privileged conditional oracle `0` bits/byte | large numerical oracle gap, but the oracle directly receives targets and does not prove recoverability from the public masked snapshot; iteration is Pareto-dominated |
| `heldout_mechanism_recombination_v2` | 0056 | shared library `0.125`, minimum combination `0` | exact MDL `0.125` at identical full cost | `1.0` | `0.875` implementable-to-oracle gap; unlike other gaps, the fixed eight-seed design gate proves unique held-out identification from public support while simple controls remain at or below `0.25` |

## Benchmark versus architecture failures

Three benchmark defects recur and must not be confused with architectural evidence.

1. **Classical ceiling:** behavioral conjugacy and probabilistic circuits are solved exactly by compact classical sufficient statistics. Another learned wrapper cannot earn a distinct claim.
2. **Observable routing:** cross-family v1/v3/v4 exposes family identity through public shape or content. Specialist success therefore does not imply a reusable representation, and pooled failure cannot measure clean transfer.
3. **Privileged-only gap:** nonstationary update and masked infilling have a large oracle gap, but their oracles receive hidden segmentation or targets. The gap is not evidence that a public learner can recover the missing information.

Two architecture failures are separable from those benchmark defects. The repository hierarchy loses directly to CTW on a valid natural task. The mechanism-recombination learner loses to an exact-MDL control even though the public task passed an explicit identifiability gate. These are genuine negative mechanism results.

## Generation-2 task selection

The transition gate required four properties: a nontrivial implementable-baseline gap, hidden OOD structure, no supplied ontology/task label, and exact full-system accounting.

`heldout_mechanism_recombination_v2` is the only frozen cohort that currently satisfies all four. Its held-out ordered `CB` composition is absent from training, all state IDs and world order are runner-random, public shapes are identical, the eight-seed design audit uniquely identifies the held-out map from support, and every acquisition/search/fit/query/update/state/bytes/R16 field is already frozen. The best nonprivileged control reaches only `0.125` against an exact oracle, leaving a real `0.875` capability gap.

This selection does not revive HYP-0021. HYP-0021's pair-selection/MDL library is discarded. Generation 2 changes the causal principle: infer a global anonymous operator algebra from consistency equations among all partial maps, and use those equations to complete missing operator actions before composing them. The learner may not know mechanism names, composition labels, the number `12`, Feistel structure, source generator modules or the held-out pair.

## New hypothesis and semantic discriminator

HYP-0022, `anonymous_operator_algebra_completion`, is proposed at confidence `0.14`.

The hand-verifiable pre-score fixture contains three anonymous partial permutations `P`, `Q`, `R` and partial observed compositions. The direct `Q` edge for query state `s` and direct `R` edge for `Q(s)` are withheld. An observed `P∘Q(s)` plus an invertible observed `P` edge identifies `Q(s)`; an observed `R∘P` edge identifies `R(Q(s))`. Global relation-equation propagation therefore recovers the held-out `R∘Q(s)`, while direct pair selection and nearest-map lookup lack both required edges and must fail. The fixture is repeated after a bijection of state IDs and a permutation of world order.

This discriminator is necessary but not sufficient. Spectral/Hankel and constrained matrix-completion methods are direct prior art for learning finite operators from observable statistics and incomplete matrices. A positive result must beat their classical interpretation through full cost and cannot be described as a novel general learning principle merely because it discovers an algebra.

## Decision

Select a generation-2 research direction and move the current state to phase `breadth`, with HYP-0022 as the only new proposed mechanism. Keep the administrative generation at `1`: `config/research.toml` freezes that value inside the protected protocol, and changing it would require a separately authorized service migration. This bookkeeping boundary does not prevent the new hypothesis from being preregistered and falsified on the already frozen evaluator. Preserve all generation-1 hypotheses and evidence unchanged. Do not reopen ceilinged cross-family, masked-iteration, repository-hierarchy or pair-selection variants.

Confidence is `0.98` in the cohort reconstruction and exclusion of invalid evidence, `0.95` that seven cohorts fail at least one transition property, `0.90` that mechanism recombination v2 meets the four task-selection properties, and only `0.14` that operator-algebra completion will survive the exact-MDL and full-cost controls.

## Exact next discriminating experiment

In the next wake, preregister `EXP-20260830-0057` quick before candidate implementation. The single changed factor is global anonymous composition-equation propagation versus direct pair selection. Implement the smallest `operator_algebra_completion` and source-identical `operator_algebra_no_relations` ablation under `candidates/`; add only the two semantic fixture invariances above. Compare them with the frozen EXP-0056 shared learner, exact MDL, independent/no-cross, unigram, Markov-5, nearest-template and privileged oracle at K=`8/32`, D=`1/4/6`, Q=`8`, one runner-random seed.

Kill HYP-0022 if the semantic fixture fails, any hidden generator constant enters the candidate, overall accuracy is below `0.95`, minimum-combination accuracy is below `0.90`, advantage over exact MDL and the no-relations ablation is below `0.10`, or a simpler implementable control Pareto-dominates it after full accounting. One quick seed can only discard or authorize a three-seed adversarial screen; it cannot promote.
