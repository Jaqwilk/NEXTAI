# Scope

Cycle 187 was exactly one protected service-only correction. It created no
hypothesis, experiment plan, scoring seed, candidate or scored result and did
not change confidence. Immutable EXP-0035 and EXP-0036 artifacts were not
edited or recomputed. This is the first consecutive no-scoring cycle after the
valid negative EXP-0036.

# Defect and minimal correction

All complete EXP-0036 raw trials contained `program_induction_accuracy`,
`length_extrapolation_accuracy` and `mean_search_ops`, but the shared manual
aggregate list omitted those fields. The runner consequently filtered every
complete row before Pareto computation and stored an empty frontier.

`aggregate_trials` now carries exactly those three already schema-admitted
fields. The frontier contract now reads `whole_io_search_protocol` like the
other protocol-specific Pareto contracts. Before dominance, it rejects a
complete summary that omitted a declared metric present in every complete raw
trial. A genuinely missing raw metric, timeout or failed outcome is still
recorded and excluded without erasing the frontier of complete candidates.

# Immutable-history boundary

The regression loads the immutable EXP-0036 plan and result, re-aggregates deep
copies in memory and proves that its complete raw shape yields a nonempty exact-
capability frontier. It also deletes one copied summary field and proves the
new gate stops before Pareto. The checked-in EXP-0036 result deliberately
retains its historical empty frontier and the analysis remains the official
interpretation; no post-seed score, ranking or evidence was regenerated.

Because this is a generic protected reporting correction, the active task/data
identifier remains `program_induction_from_whole_io_v3` for maintenance only.
Any future scored comparison that depends on the corrected aggregation must
use a new role/cohort version and a fresh immutable plan; v3 may not be rerun or
used to rescue HYP-0047.

# Verification and decision

The focused historical-shape regression and all 510 repository tests passed.
Integrity verified 685 protected files. Evaluator digest is
`7745ba17bd20ce294aa01ba3cba5bce971832b31e790468b8b5718fc8ba39fe3`,
candidate bundle is
`5a0172cf4f0e2c8768db0d6777b902a007ab66f5ef10d1b90e983926a702d3ef`,
and preflight certificate is
`7f16cb78ea0eb27c7b3c0e089fc0a7c63057a5d5b2e821098043d1ade595fa94`.
Doctor passed with zero pending plans.

Decision: keep the correction as prospective infrastructure. It changes no
scientific evidence. Do not spend another wake auditing this defect.

# Exact next discriminating cycle

Cycle 188 must be one bounded breadth-selection and role-only activation, not
another generic audit and not HYP-0047 tuning. It must test whether a shared
reversible phase-coded operator representation is genuinely distinct from
exact operator tables, macro caches, grammar induction, pair-energy relaxation
and spectral PSR on the existing held-out mechanism-recombination worlds. The
pre-seed development gate must reject the direction immediately if the phase
code is merely a reparameterized full transition table or cannot represent the
noncommuting held-out compositions under anonymous state conjugation.

If distinct, freeze only one shared implementation identity plus independent
and frozen source-identical ablations on a versioned successor, with the same
data, controls, length-4/8/16 OOD programs and full R1/R4/R16 accounting. Create
no hypothesis, plan, seed or score in cycle 188. Cycle 189 is then mandatory
scoring with one runner-random quick; a valid negative ends the exact phase-code
rule without rank, dimension or loss tuning. If the identifiability gate rejects
it, cycle 188 must activate the cheapest already-audited orthogonal role contract
in the same service wake so cycle 189 still scores. This keeps the no-scoring
streak below the user's maximum of three.
