# NEXTAI — new continuation active; MUC retained as technical test (2026-10-04)

Nowy program NEXTAI-CONTINUATION-20261004-V1 jest zatwierdzony: maksymalnie 17 dodatkowych rejestracji i 69344 s obliczeń, z zachowaniem 3 zużytych rejestracji i 2655.336485 s. Kontrakt: research/plans/NEXTAI-CONTINUATION-PROGRAM-V1.json. Zamknięty MUC03 i jego wyniki pozostają niezmienione. Nowa autoryzacja pozwala na zmianę receptur, uzasadniony nowy benchmark, minimalne prototypy, ablacje i replikacje; porażka jednej receptury nie zamyka programu. Nie ma potrzeby ponownego pytania o działania objęte tym zakresem.

Cykl 304 jest przygotowaniem bez scoringu, EXP lub fitu badawczego. MUC pozostaje testem technicznym: publiczny dokładny klucz umożliwia kontrolę symboliczną 100%. Zapisane sondy8192 pokazują przy K32/128/512 top1=100/95.33/80.44%, a odrzucenie nieznanego podmiotu=88.44/12.44/1.78%. Osobno diagnozujemy ranking i decyzję o braku odpowiedzi; zamknięte progi nie są zmieniane.

Analiza: research/analyses/NEXTAI-CONTINUATION-MUC-DIAGNOSIS-V1.md. Prospektywny kontrakt nowego zadania: research/plans/PVM01-TASK-CONTRACT-V1.json. Dwa surowe obserwacyjne widoki świeżych ciągłych tożsamości, jawne aktualizacje, kontrole zamrożona/permutowana i mocny transport/retrieval klasyczny mają sprawdzić wpływ uczenia. Nie implementowano generatora ani modeli i nie widziano nowych danych. Zmienne rundy aktualizacji nie oznaczają głębokości rozumowania.

Następny ograniczony cykl: prerejestracja PVM01-REFERENCE-V1 przed implementacją, pięć świeżych sparowanych jednostek train/dev, konwencjonalny dense Transformer i attention pointer oraz mocne kontrole. Zamrozić konkretną recepturę, metryki, capy i siatki klasyczne; walidować w niezależnym klonie, potem freeze/preflight/readiness i dokładnie jeden audytowany EXP. Zachować alternatywy przy nieudanej recepturze. Mechanizm, ablacje, trzy skale, trudny wariant i świeży finał pozostają dalszym zakresem programu.

Bramki ekonomiczne pozostają bez osłabienia. Cały fit i czas testów, także nieudanych, obciążają limit; nieukryty pełny koszt obejmuje alokację, parser, kopie, ingest, indeks, aktualizacje, cache, zapytanie i dekodowanie. Bez retry, WT8–9, zewnętrznych modeli/API i zmian harmonogramu. Current benchmark=maintenance, scoring=false. Użyj uv run nextai lab status do weryfikacji kolejki i rozliczenia.

Poniżej zachowano wcześniejsze sekcje jako historię; nie zastępują tej autoryzacji. Stałe niezmienniki naukowe i techniczne nadal obowiązują.

# NEXTAI — MUC03 resolved INCONCLUSIVE at reference gate

## Latest cycle 303 — MUC03 resolution INCONCLUSIVE (2026-10-04)

EXP-20261004-0003 completed once in the independent validation clone: all 11
workers / 135 trials, five fresh paired seed/data units, 768 vs 8192 steps,
unchanged model, 4096 hard pairs and threshold 0.5. Train 98.54 -> 99.87%; dense
top1 84.52 -> 91.93%, both primary paired 97.5% intervals exclude zero. Dense
UNKNOWN is only 53.48%; one top1 seed is 80%. No arm passes all frozen stability
gates. Classical last-write graph has 100% E2E and much lower local cost/state.

The third and last reference recipe fails. The authorized program resolves to
INCONCLUSIVE at the failed reference entry gate, without a fourth recipe or
architecture promotion. Mechanism selection, source-identical ablations,
matched-quality scaling, adverse generalization and fresh final remain
UNEXECUTED. This does not falsify the untested delta-memory family. The global
20-attempt / 72000-second cap was not exhausted. Three tickets include one
failed registration; research fit totals 1216.336485 s. Every test wall is also
conservatively charged, with all failures retained in completion receipts.

Resolution: research/analyses/MUC03-AUTONOMOUS-PROGRAM-RESOLUTION-V1.md.
Last experiment: research/plans/EXP-20261004-0003.json and
research/analyses/EXP-20261004-0003.md. Required 12-result reflection:
research/reviews/MUC03-REFERENCE-PORTFOLIO-CYCLE-303-V1.md. All evaluated source
and runtime bytes are archived before post-run changes. The diagnostic Pareto
front omits classical dense probes; the report now discloses omitted axes,
without changing old results or claiming economic non-dominance.

Final queue after the hash-bound closure: MUC03-PROGRAM-COMPLETE, maintenance,
scoring=false, no pending run or reservation. No retry, WT 8-9, final access,
external model/API, new architecture or schedule change. All sections below
are preserved historical records and cannot authorize another study.

## Historical cycle 303 preparation — final reference calibration (2026-10-04)

Prospective MUC03-REFERENCE-CALIBRATION-V1 is frozen in Git d6f0d0a before
implementation. Compare768 versus8192 steps, unchanged4096 hard pairs/model,
five new paired train/dev units, fixed0.5 threshold and identical stability
gates. This is the third and last tested reference step recipe. At most one
registration/run,3500 s fit,350 s per role,4h bound ending2026-10-04T04:55:06Z.
Keep maintenance until clone tests, integrity/preflight and readiness pass.
No retry, final access, WT8-9, new architecture or implicit economic claim.
If no arm passes all gates, close reference INCONCLUSIVE and report untested
mechanism/ablations/scaling/fresh-final scope; do not add a fourth recipe.

## Latest completed cycle302 — EXP-20261004-0002 (2026-10-04)

Paired hard-negative192/768 diagnostic completed once in the independent clone:
all11 workers /135 trials valid; identical initial/data/pairs and first192 loss.
Train77.32->95.75%; dense top1 22.74->70.15%, primary97.5% paired intervals
exclude zero,5/5 positive. Full-answer accuracy40.41->78.32%; dense UNKNOWN
only23.63%. Namespace gap2.96 pp stays below the frozen10 pp gate. KEEP the
undertraining diagnosis; DISCARD768 as stable reference; no architecture or
cost/transfer claim. Symbolic control100%. Analysis: research/analyses/EXP-20261004-0002.md.

Program remains authorized and active; current study terminal, maintenance,
scoring=false, no same-plan retry. Attempts2/20 include one failed historical
CLI fixture before seed/fit. Research fit149.463 s; auxiliary tests charged
conservatively in the append-only ledger. Post-run budget/hash guard repair
uses research/plans/MUC03-POSTRUN-ACCOUNTING-REPAIR-V1.json with no scored run.
Next cycle: freeze one final reference calibration768 vs8192 steps, same model,
4096 hard pairs, five paired fresh train/dev units and fixed0.5 threshold.
This is the third and last tested reference step recipe; if stability still
fails, close this reference milestone inconclusive with exact untested scope.
No further user approval is needed inside the standing finite program.

## Historical authority record — finite autonomous research program MUC03 (2026-10-04)

The user authorizes MUC03-AUTONOMOUS-20261004-V1: at most 20 new registration
attempts, including failures/invalidations, and 72000 s total fit, including
failed fits and conservative auxiliary test charges. The immutable contract
is research/plans/MUC03-AUTONOMOUS-PROGRAM-V1.json. Old results, attempts and
budgets stay consumed. WT 8-9, external models/APIs and schedule changes remain
forbidden. Choose studies autonomously; no further approval is needed within
this finite program. Register through `uv run nextai program register`; execute
only through `uv run nextai run --plan ...`. A paid attempt cannot be retried.

First study V1 was frozen before implementation. Its sole registration ticket
was consumed by a historical schema fixture before any plan, seed or research fit.
The prospective replacement is research/plans/MUC03-DIAG-UNDERTRAINING-V2.json;
metrics, recipe, budgets and the original deadline remain fixed. It compares hard-negative 192/768 steps, same MUC v2 model and
4096 pairs, for 5 paired fresh seed/data units. Namespace probes on the same
fresh graph separate fit, rejection and generalization. Keep maintenance until
clone conformance, integrity/preflight and readiness receipt pass. No final data
in this study. A competent stable reference precedes mechanism investment;
full-cost advantage additionally needs strong classical controls, ablations,
scaling, adverse generalization and frozen fresh final replications.

One new scored experiment per cycle. End each cycle with analysis and durable
budget accounting, then select the next bounded question under this standing
program authority. At caps or a decisive resolution, finish with a reproducible
prototype or an explicitly negative/inconclusive report. Do not call diagnostics
an architecture result. All sections below describe preserved historical scope.

## Historical state — MUC v2 hard negatives completed (2026-10-04)

The one actual five-pair comparison completed as EXP-20261004-0001 in the
independent Git clone. The immutable plan is research/plans/EXP-20261004-0001.json;
analysis: research/analyses/EXP-20261004-0001.md. Random to hard: dense top1
10.96% -> 23.11%, dense UNKNOWN 10.00% -> 23.41%; paired simultaneous intervals
include zero, positive pairs are only 3/5 and 2/5, and known false abstention
rises from 0 to 22.89%. DISCARD this exact hard-negative recipe at 4096 pairs /
192 steps; the general mechanism remains inconclusive. Symbolic control: 100%.
All 11 workers completed; trusted supervised fit total83.968 s /3600 s cap.

The stage is terminal: MUC02-HARD-NEGATIVES-DECISION, scoring=false, benchmark
maintenance. No retry, replacement seed, further registration/training, final
access, WT 8-9, new architecture or promotion is authorized. A proposed 192 vs768
hard-negative fit comparison is discussion only and requires fresh authority.
Both registrations are preserved: EXP-20261003-0001 was invalidated pre-seed;
EXP-20261004-0001 was the sole actual execution under the unchanged deadline.
Evaluated protected source and all runtime journals/logs were archived before
terminal maintenance. History, budgets and scientific invariants stay intact.
Use `uv run nextai lab status` for the verified queue. All later stage-specific
sections are historical records and do not reopen execution authority.

## Historical authority — MUC v2 hard negatives (2026-10-03)

The user authorized MUC02-HARD-NEGATIVES-20261003-V1: preregister metrics and
thresholds, minimally change only training negatives, then compare random and
hard negatives in the independent Git clone on fresh train/dev for five paired
runner seeds. The MUC v2 model, 4096 pairs and 192 steps stay fixed. Work starts
2026-10-03T21:08:25Z and stops by 2026-10-04T01:08:25Z; total fit <=3600 s.
The immutable contract is research/plans/MUC02-HARD-NEGATIVES-20261003-V1.json,
with user authority in the matching research/laboratory record. The new cohort
is mutable_contact_ledger_hard_negatives_v2. No retry, WT 8-9, final/calibration
reuse, tuning, new architecture, promotion, external model/API or schedule change.
Any worker failure or cap stops the unstarted scope and preserves all outcomes.
Use `uv run nextai lab status` for the verified queue. All sections below are
historical unless explicitly selected by this new authority.

Metrics and decision thresholds are immutable in the contract before the new
sampler implementation. Primary endpoints are dense latest-record top1 and
UNKNOWN rejection (absent subject / absent relation) at the fixed0.5 threshold.
Five paired independent seed/data units receive simultaneous97.5% paired t
intervals (Bonferroni familywise95% for two endpoints). Minimum effects: +5pp
selection and +10pp rejection, both positive lower bounds, >=4 positive pairs.
Known acceptance/end-to-end quality and false abstention are guarded at2pp.
The unchanged BM25 top4 end-to-end reader and classical last-write graph are
also measured. This is visible development, not a hidden final or architecture
promotion. Old calibration EXP-20261002-0001 remains complete and immutable.

State at authorization:107 completed experiments, cycle300, zero pending.
Implementation and full clone regression (1029/1029) passed. EXP-20261003-0001 was
append-only invalidated before any scoring seed: missing result serializer fields
and stale historical fixtures. MUC02-HARD-NEGATIVES-PRESEED-CONFORMANCE-V1
freezes the correction and permits one corrected registration, preserving both
registration records and allowing only one actual five-pair execution. Metrics,
thresholds, model, data and original deadline/budgets remain unchanged.
This historical paragraph describes the pre-seed state; execution is now closed above.
