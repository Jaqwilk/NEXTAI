# PC-01-FINAL-SERIES-V1 — authenticated three-seed decision

Frozen series canonical SHA-256:
ed34b36af69d30cb7f0c9c60473ab3ccd8f107428614a56167053fde0b8ad691.
Selected development source: EXP-20260905-0002 (v2 selection only). Final
measurement cohort: pc01_byte_lm_learning_measurement_v3. Final replicas:
EXP-20260905-0003, EXP-20260905-0004 and EXP-20260905-0005. This series is a
positive-control calibration, never architecture evidence.

## OBSERVATION

All three preregistered final attempts completed once through the audited runner
with unique seeds 1239391372, 51543814 and 285038327. Every run used 5000 updates,
fresh initialization, the same source/recipe/data/evaluator/series identity, all
ten controls, and a valid ordered pair of GPU metadata snapshots. No result was
omitted, retried or replaced.

| Experiment | Trained bpb | Frozen bpb | Frozen−trained bpb | Unigram−trained bpb |
|---|---:|---:|---:|---:|
| EXP-20260905-0003 | 2.480890632850043 | 8.040790604705470 | 5.559899971855426 | 2.348978021552171 |
| EXP-20260905-0004 | 2.484464204871435 | 8.118558934898177 | 5.634094730026742 | 2.345404449530779 |
| EXP-20260905-0005 | 2.514378141022578 | 8.042679257173068 | 5.528301116150491 | 2.315490513379636 |

Authenticated preregistered statistics for frozen-minus-trained:

- mean: 5.574098606010886 bpb;
- sample standard deviation: 0.054307210323858456 bpb;
- range: [5.528301116150491, 5.634094730026742] bpb;
- lower 95% paired t bound, df=2: 5.439192016820712 bpb.

Every trained loss is <=3.5 bpb, every learning contrast is >=1 bpb, and the
lower t bound is strictly above zero. The secondary minimum unigram contrast is
2.315490513379636 bpb, above 0.1. The authenticated decision is therefore
`positive_control_pass`. Runner authenticity is true. The decision explicitly
sets architecture promotion, economic advantage and transfer to false.

The three final fits used 294.42879940000057, 301.6966133999995 and
297.7194793000017 seconds (893.8448921000017 total), all below 1200 seconds.
Workers used 925.7557370999966 seconds total, each below 1800 seconds. Peak sampled
RSS was at most 1,502,879,744 bytes; CUDA allocated/reserved maxima were
1,768,945,152 / 2,174,746,624 bytes. All three used the same RTX 4070 UUID and
driver 551.78. No energy was measured.

## INTERPRETATION

PC-01 succeeds at its narrow purpose: the apparatus detects stable learning by
a competent conventional small transformer versus its source-identical frozen
control under the declared local budget. This resolves the external audit's
measurement-control concern and makes later candidate failures more interpretable.
It does not demonstrate that NEXTAI has found a better architecture; the positive
control is itself a dense autoregressive model.

## CONFIDENCE

High confidence in the local causal learned-versus-frozen effect under this
frozen protocol: the effect is large relative to seed variation, all controls
passed and the lower paired bound is far above zero. Confidence is deliberately
narrow. The three seeds share one corpus and evaluator, so they do not establish
independent-corpus transfer or a blind external holdout. They also do not prove
deployment economics, scaling or general intelligence.

## ALTERNATIVE EXPLANATIONS

Ordinary gradient learning, memorization and statistical regularities in this
corpus are the intended explanation. Byte targets and windows are dependent;
the t interval describes seed variation conditional on one corpus, not population
uncertainty across corpora. Final bpb is worse than selected dev bpb and the late
dev curves deteriorate, consistent with overfitting. Post-final tuning is forbidden.
Classical unigram/bigram controls are quality references, not matched-quality
economic competitors; no claim is made that the transformer beats PPM/CTW in cost.

## DECISION

KEEP and close PC-01 with decision `positive_control_pass`. Do not add replicas,
tune this version, promote an architecture or reinterpret the outcome as transfer
or economic advantage. Return to explicit user review before WT-01 preparation.

## INTEGRITY AND BUDGET

All plans, results, runtime artifacts, source/evaluator commitments and prior
failed/dev outcomes remain append-only. Total PC-01 charged fit, including the
conservatively charged failed dev, is 2394.270825300002 / 7200 seconds. Exactly
two dev attempts and three final attempts were consumed; no replacement remains.
The fixed 3600-second final reservation was respected. Post-run full regression,
doctor, receipt hashes and Git publication are recorded at cycle closure. Large
checkpoints and corpus bytes remain local and ignored; scientific records are pushed.

## NEXT DISCRIMINATING EXPERIMENT

No further PC-01 experiment. The exact next step is a no-scoring WT-01 contract
cycle, only after explicit user authorization: resolve the historical WT source
by hash, freeze the 2x2x2 recurrence/RLS/clipping factorial, add algebraically
equivalent VAR(2) and target-adaptive/recycling alternatives, acquire independent
same-class traces, and preregister causal, cost and adversarial decisions. Do not
start WT scoring or a language-system prototype from this PC-01 result alone.
