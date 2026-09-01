# GEN-1 WT predictive-state v3 activation — cycle 166

This was the second and final consecutive no-scoring service cycle. It created
no hypothesis, plan, scoring seed or result. It implemented only the two
mandatory classical controls that blocked honest activation of WT v3.

## Coverage-aware spectral PSR

The registered control is a train-only, action-conditioned two-stage spectral
predictive-state estimator. It balances exact public-control strata, constructs
the weighted history/future cross moment, retains its first four left singular
directions, and fits a ridge readout from predictive state, control and their
interaction to the first 32 future residual samples. H96 uses the same frozen
hold-last extension as historical fixed controls. Reveals update only a
slot-local readout through normalized LMS.

The semantic fixture reproduces the weighted cross moment directly and proves
that duplicating every example in one overrepresented control stratum does not
change its prediction. It also proves anonymous-channel permutation equivariance,
slot isolation and real-file completion.

## Train-only discretized CSSR

The registered finite-sample CSSR variant discretizes each anonymous response
channel and public control with train-only quartiles. It estimates next-symbol
morphs for suffixes of lengths one through three, groups morphs at frozen total-
variation threshold `0.15`, and iteratively splits states until every empirically
supported symbol-labelled successor is deterministic. Emissions are train-only
mean residual curves by control bin and causal state; reveals update only a
slot-local emission bank and never rebuild the causal partition.

The hand-checkable fixture contains two histories with the same control and
last symbol but different two-symbol contexts and next-symbol distributions.
CSSR separates them while a first-order key aliases them. Permutation, slot
isolation and real-file completion also pass. Zero-count transitions are not
invented during determinization and therefore do not add unobserved support.

## Activation decision

All ten mandatory baseline registry records and their hashed tests passed.
The candidate source audit passed, all ten frozen WT file hashes matched, all
447 repository tests passed before activation, and integrity, preflight and
doctor passed after activating `heldout_wt_changepoints_prequential_v3`.

The next wake must score. It may create HYP-0040 as an exact low-confidence
child/revival of HYP-0008, preregister one immutable quick before implementing
the causal learner, freeze rank/windows/control conditioning/update/effect gates,
and run one runner-random seed through the audited harness. A positive can only
authorize unchanged replication; a negative ends the exact rule without tuning.
