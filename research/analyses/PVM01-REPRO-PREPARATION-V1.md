# PVM01-REPRO-PREPARATION-V1 — cycle311

Preparation-only technical conformance. No new EXP, research split, scored run
or paid retry. Last scientific result remains EXP-20261004-0008, INCONCLUSIVE.
The parent preregistration was committed at4cc5f20 before implementation;
one bounded implementation correction was committed at5f3fa61 before V2.
Primary contract: research/plans/PVM01-REPRO-PREPARATION-V1.json.
Correction: research/plans/PVM01-REPRO-PREPARATION-IMPLEMENTATION-REPAIR-V1.json.
Started2026-10-04T22:23:55Z; original deadline2026-10-05T00:23:55Z;
2400s auxiliary cap, no extension. Every failed check and fixed auxiliary fit is paid.

OBSERVATION

- The corrected matrix completed36/36 independent child processes:3 fixed model
  seeds,2 repetitions,3 existing roles and2 execution policies. All roles fit on
  the same GPU; the CPU-cache role copies unchanged fitted weights afterward.
- Same154240-parameter model, optimizer, loss and batches:64 encoder steps and
  64 decoder steps per child. Public NumPy seed730119,128 train pairs,32 validation
  pairs and8 K32/K128 episodes. This is a technical fixture, not fresh research
  train/dev or an assessment of competence. No private generator was imported.
- Default encoder/losses reproduced exactly. Default decoder hashes and loss
  sequences differed in all3 seeds:6 distinct versions for6 same-seed runs.
- Explicit deterministic algorithms plus FIT-only attention MATH produced
  exact initial/final encoder/decoder hashes and all128 losses in18/18 children.
  Both parameter groups changed; all losses finite. No epsilon was allowed here.
- Dispatch profiling recorded256 efficient SDPA forward and256 efficient backward
  calls per default fit; deterministic fits recorded256 math SDPA calls and no
  efficient/flash FIT dispatch. This is CPU ATen dispatch tracing, not physical
  CUDA kernel tracing. Global flags are restored on success and failure.
- All360 deterministic inference records (20 known/absent/update fixture queries
  per child) have the same discrete decisions within each seed across roles.
  Maximum score difference1.7881393432617188e-7 is below the existing1e-5
  inference tolerance. This does not relax exact fitted-weight/loss identity.

| Profile | Seed | Runs | Encoder hashes | Decoder hashes | Dense loss sequences | Max inference difference |
|---|---:|---:|---:|---:|---:|---:|
| existing_default | 1103 | 6 | 1 | 6 | 6 | 1.788139343e-07 |
| existing_default | 1709 | 6 | 1 | 6 | 6 | 1.788139343e-07 |
| existing_default | 2909 | 6 | 1 | 6 | 6 | 1.788139343e-07 |
| deterministic_math | 1103 | 6 | 1 | 1 | 1 | 1.192092896e-07 |
| deterministic_math | 1709 | 6 | 1 | 1 | 1 | 1.788139343e-07 |
| deterministic_math | 2909 | 6 | 1 | 1 | 1 | 1.788139343e-07 |

The supervisor starts a suspended root, assigns it to a non-inherited Windows
Job Object and only then resumes it. It uses direct output files and closes the
owned job on every exit or exception. Timeout includes construction, with<=3s
bounded cleanup. An actual live descendant after early parent exit is failure.
PID membership and signaled process handles distinguish live descendants from
accounting notifications. Synchronous OS creation itself cannot be preempted
by Python; no general security sandbox or externally delegated service/WMI
containment is claimed. [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Targeted V1:28 passed; corrected V2:29 passed, including success/nonzero output,
parent/child/grandchild timeout, early parent exit, actual uv wrapper, pre-resume
failure and24 rapid redirector exits. Full regression:1127 passed,0 failed,
0 errors,0 skipped. Clone doctor/lab/history gates passed with1171 protected
files and702 audited candidate modules;21463 pre-existing nonmutable files
match the exact original raw bytes, with all append-only prefixes preserved.

PRESERVED FAILURES AND CORRECTIONS

- Preregistration import mistake before any plan/source mutation:5s charged.
- Source staging named a nonexistent archive path:5s charged; freeze had passed.
- Fixture V1 stopped at5/36 with an output-writing fifth child root exit0 but
  lingering accounting. Full raw fit reports including the failed fifth remain;
 66s charged. Its actual live member PIDs were not logged, so stale notifications
  are a possible explanation, not a proven retrospective cause. No deterministic
  child started. Missing explicit inherited environment enforcement was also
  corrected before V2. V1 remains INCONCLUSIVE and incomplete.
- The prospective correction permitted ONE new36-child auxiliary matrix under
  the unchanged2400s/2h caps; total41 fitted children including the failed5.
  No source/seed/data/loss/metric selection followed a scientific result.
- Clone history guard V1 failed on BELIEFS.json raw byte comparison:9s charged.
  Diagnosis found exactly10 pre-existing CRLF/LF checkout representation
  differences. Exact original raw bytes were restored in the clone; Git content
  remains unchanged for all10, and no manifest/scientific gate was relaxed.
  BELIEFS and the original files were never edited. Failure output is preserved.
- The auxiliary controller additionally clips child time to the remaining original
 2h deadline; the previously evaluated controller is archived separately.

INTERPRETATION

KEEP the technical supervisor and deterministic FIT policy, conditional on the
original-source verification recorded in the completion addendum. The default
fixture reproduces decoder drift and the explicit policy resolves it here.
This is compatible with numerical/nondeterministic attention as the EXP-0008
explanation; its backend was not recorded, and this bundled policy does not
isolate which flag/operator caused that historical drift. EXP-0008 remains
INCONCLUSIVE without changed gates, results, recipes, thresholds or analysis.
[PyTorch2.6 SDPA](https://docs.pytorch.org/docs/2.6/generated/torch.nn.functional.scaled_dot_product_attention.html),
[reproducibility](https://docs.pytorch.org/docs/2.6/notes/randomness.html).

CONFIDENCE AND COST

High confidence for these finite same-host fixed-fixture checks. No scientific
confidence interval is warranted: the3 model seeds share one public fixture,
not5 independent research units. The64+64-step probe does not establish exact
full2048/1024-step conformance on fresh units, competence, economics, transfer,
novelty or another hardware/software platform. Future scored comparisons must
retain their own exact source/data/weight/loss and discrete-prediction gates.

GPU RTX4070, PyTorch2.6.0+cu124, float32; required CUBLAS workspace4096:8 and
thread counts1 are explicitly verified and recorded. CUBLAS workspace was
already set by the historical audited runner; it is not a newly discovered
missing setting in EXP-0008. Profile means below include dispatch overhead
and fixed serial role order; they are not end-to-end economic comparisons.

- Default profiled fit mean2.671518s; whole child mean11.946323s.
- Deterministic profiled fit mean3.546980s; whole child mean14.487159s.

All full wall costs, including failures, source checks and output/initialization,
are conservatively charged in research/events.jsonl. Matrix V1 charged66s,
V2 charged485s; regression316s. Final aggregate, remaining budget and original
source confirmation are append-only completion records, not substitutions for
these earlier reports. No scientific ticket or completed-EXP counter changes.

NEXT DISCRIMINATING EXPERIMENT

Select and preregister a distinct learned-transport plus mutable-memory/index
alternative on a justified adverse paired-view task, with5 fresh paired units,
unchanged strong dense/cache and classical controls and the exact FIT policy.
Freeze the concrete recipe, metrics, grids, full system boundary and cost caps
before any generator/model implementation or fresh data. Require full-recipe
identity in that new audited comparison, not a tolerance rescue of EXP-0008.
The three-scale economic comparison, adverse generalization, independent
replication and frozen fresh final still remain in the standing programme.
No second research experiment is started in this preparation cycle.
