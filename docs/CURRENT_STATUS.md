# NEXTAI — active paired MUC v2 negative-sampling development

## Current authority — MUC v2 hard negatives (2026-10-03)

The user authorized MUC02-HARD-NEGATIVES-20261003-V1: preregister metrics and
thresholds, minimally change only training negatives, then compare random and
hard negatives in the independent Git clone on fresh train/dev for five paired
runner seeds. The MUC v2 model, 4096 pairs and 192 steps stay fixed. Work starts
2026-10-03T21:08:25Z and stops by 2026-10-04T01:08:25Z; total fit <=3600 s.
The immutable contract is research/plans/MUC02-HARD-NEGATIVES-20261003-V1.json,
with user authority in the matching research/laboratory record. The new cohort
is mutable_contact_ledger_hard_negatives_v1. No retry, WT8-9, final/calibration
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
Implementation and the single scored comparison are not yet performed.
