"""Prospective specification only; no task arrays or model execution."""
import copy
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

base = Path.cwd()
relative = "research/plans/PVM01-CAPACITY-EXPOSURE-V1.json"
assert not (base / relative).exists()
study = copy.deepcopy(json.loads((base / "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json").read_text()))
arms = ["exposure_small", "exposure_large", "exposure_frozen", "exposure_shuffled", "exposure_additive",
        "delta", "dense", "dense_cached_cpu", "dense_cached_cuda", "exact_nn_cpu", "ridge", "ridge32",
        "ridge_pca_scan", "ridge_pca_tree", "kernel", "raw"]
study.update(id="PVM01-CAPACITY-EXPOSURE-V1", cohort="paired_view_mutable_memory_v5",
    study_kind="paired_view_capacity_exposure", auxiliary_charge_id_prefix="PVM01-EXPOSURE-",
    study_started_at="2026-10-04T20:50:36Z", study_deadline_at="2026-10-05T00:50:36Z",
    prepared_source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
    question="Does training support-size exposure to K512 rather than K128 improve the same 512-feature/512-step delta memory, beyond frozen/shuffled feature controls, while preserving retained facts against RFF2048 and competent dense and strongest classical controls?")
study["candidates"] = [f"pvm01_{arm}_s{i}" for arm in arms for i in range(5)]
study["roles"] = {name: {"arm": arm, "seed_index": i,
    "fit_steps": 0 if arm.startswith("ridge") or arm in {"kernel", "raw"} else 2048}
    for arm in arms for i in range(5) for name in [f"pvm01_{arm}_s{i}"]}
recipe = study["recipe"]
recipe.update(exposure_small_support_sizes=[32, 128], exposure_large_support_sizes=[32, 512],
    exposure_common_value_draw_size=512,
    compact_feature_training="All roles receive legal T-sets at K32/128/512:128 episodes per K,zero update rounds,8 independent questions. Old K32/128 factory remains unchanged; K512 uses the same episode law. After unchanged correct transport2048 steps, freeze encoder. Precompute and hash normalized writes/aligned queries/target positions for all three K. Feature optimizer remains512 fixed AdamW steps,lr.003,WD0,clip1,batch4,17-class CE with fixed NULL.5 and scale20,untruncated delta writes,final step selected. Small alternates K32/128; large/shuffled/additive alternate K32/512. Every optimizer step draws the same four episode indices and iid16-way value-label table4x512 from one seed-derived generator across all optimized feature arms; use the first K columns. Hash full indices/max-label draws separately from size-specific trace. Queries remain8 each. Frozen feature control skips this optimizer. No T-calibration/D optimizer use,checkpoint selection,gradient truncation,early stopping or dev adaptation. Larger support increases paid training work; equal steps/queries is not equal FLOP budget.",
    compact_feature_controls="Five exposure arms share encoder initialization/final weights,exact alignment losses,feature initialization,512 capacity,all legal arrays and memory code. Only optimizer support curriculum differs small versus large. Shuffled uses one fixed permutation of128 query episode groups per K32/128/512,while support/labels/target positions/common draws and transport remain correct. Frozen skips feature updates. Large/additive feature optimizer/losses/final projection are identical; only inference write subtraction differs. All11 strong control arms use unchanged aliases/cores and recipes; dense training still selects onlyK32/128,with extra legalK512 arrays available but unused. No reference checkpoint reuse.",
    compact_feature_scope="Capacity-exposure diagnosis of known differentiable Fourier fast-weight memory. No new architecture,learned gate,controller,novelty or general-language claim. Changing support exposure also increases training work; causal contrast identifies exposure under this fixed-step recipe,not compute-normalized scaling.")
study["data"].update(tag=study["id"], train_episode_support_sizes=[32, 128, 512],
    legal_training_sets="All80 roles receive the same source-identical128 T-sets episodes perK32/128/512,8 questions,zero updates and legal target positions. K512 is a fresh train-only split of the unchanged episode law,not a dev/calibration observation. Value labels remain independent iid16-way draws; all optimized feature arms draw4x512 each step and truncate to actualK. No hidden identity/maps/nonce exposed.")
study["primary_endpoints"] = ["large_minus_small_full_answer_accuracy", "large_minus_frozen_full_answer_accuracy",
    "large_minus_shuffled_full_answer_accuracy", "large_minus_RFF2048_retained_answer_accuracy_updates1_4"]
study["diagnosis_gates"] = {
    "independent_units": 5, "simultaneous_primary_interval_level": .9875,
    "large_vs_small_mean_full_gain_min": .05, "large_vs_frozen_mean_full_gain_min": .05,
    "large_vs_shuffled_mean_full_gain_min": .05, "all_three_gain_ci_lower_min": .02,
    "all_five_each_gain_positive": True, "retained_vs_RFF2048_ci_lower_min": -.02,
    "interpretation": "Three independent causal contrasts of exposure/feature learning with existing effect thresholds; retained noninferiority. K512 updated accuracy remains a descriptive diagnostic and unchanged competence applies to everyK. New prospective endpoints do not reinterpret or rescue closed0007."}
study["resources"].update(fit_seconds_per_role_cap=180, worker_seconds_cap=204,
    worker_charge_ceiling_with_monitor_margin=208, fit_seconds_study_cap=16640,
    auxiliary_test_seconds_cap=1800)
study["freshness_policy"] = "Five fresh runner-random model seeds and256bit nonces,disjoint from every consumed0004..0007 before any arrays. Collision invalidates without replacement. Same T/D across16 arms; no old weights/arrays/calibration reuse."
study["uncertainty"] = "Five independent combined seed/data units,equal cell weights; updated/retained averaged only updates1/4. Four two-sided98.75% paired Student-t df4 intervals provide familywise95% Bonferroni: full large-small,large-frozen,large-shuffled,and retained large-RFF2048. Preserve all five unit values/directional counts. Other cell/absence/cost metrics are descriptive paired95%,no query/episode pseudoreplication. Outer economic and competence gates unchanged."
study["decision_policy"] = "Validity first:80 workers/720 trials,legal array pairing/source/hash integrity,all feature transport identity,common draw pairing and exact large/additive feature fit equivalence. Dense and both cache controls must meet unchanged competence. KEEP exact large-exposure512/512 recipe for further validation only if all four primary gates plus large/dense competence pass. Valid failure DISCARD this exact exposure recipe without erasing narrower effects. Crash/dense incompetence INCONCLUSIVE,stop unstarted scope,no retry. Strong classics may dominate. No economic/novelty/transfer promotion or fresh final in this screen. This is the last compact Fourier exposure recipe in this branch if it fails; do not automatically grow steps or retune. Whole program remains active for distinct alternatives/adverse/fresh-final scope."
study["implementation_scope"] = "Add one capacity-exposure core reusing unchanged Fourier/unroll/loss/inference functions,25 thin aliases,a v5 evaluator reusing unchanged binding/scoring/timing and episode law,stored-only analyzer/tests. Extend exact cohort/schema/runner dispatch and consumed-unit guard to0007. Preserve v1-v4 task/cores/evaluators and all closed plans/results/archives. Only tiny fixed CPU fixtures before audited random units; no research fit outside runner."
study["diagnostics"]["reproducibility"] = [
    "legal T-fit/T-validation/T-sets32/128/512/T-calibration/D array hashes",
    "all feature transport initialization/final weights and exact alignment loss identity",
    "same initial Fourier projection and capacity",
    "common max-label/index draw digest across small/large/shuffled/additive",
    "size-specific fitting digest and all512 feature losses/gradient norms",
    "exact large/additive final features and losses",
    "frozen frequency identity and fixed shuffled episode permutations",
    "all dense/cache exact final encoder/decoder identity and PCA scan/tree identity",
    "all actual inference components/full worker wall/RSS/CUDA state and raw predictions"]
study["diagnostics"]["logging"] = "Full fit_report appears once per worker in first trial and fit journal; later trials reference its canonical SHA256. All predictions/losses/grids/components preserved; v5 may compact whitespace without dropping values. Old result bytes unchanged."
study["next_alternatives"] = "If this second feature branch alternative fails,close exact compactFourier branch for this task. Evaluate a distinct structural route or the already strong learned-transport indexed solver against strongest classical controls,with prospective adverse/scale/fresh-final contracts. No silent fourth recipe or whole-program closure."
study["prospective_feasibility"] = {
    "parameters": "16384 frequency parameters plus unchanged transport,W8192 floats; same inference512 capacity.",
    "training_bound_estimate": "Large mean support272 vs small80.512 steps*4*272=557056 differentiable per-episode writes; max512 sequential nodes roughly64MiB W intermediates plus gradient buffers and other allocations. Expected fit comfortably under180s based on prior small timings scaled analytically,but not measured for new data. Actual4GiBCUDA/8GiBRSS and180s fit/204s worker limits override this estimate.",
    "paired_draw_difference_from_closed0007": "New full512 value draws consume a different RNG stream than closed0007 small training. Marginal value distribution unchanged. Exact causal pairing is only withinv5; do not claim bit-identical small replication or combine cross-study units.",
    "cost_tradeoff": "Inference architecture/state unchanged; training work larger and fully charged. No assumption of advantage over ridge/PCA/indexed retrieval."}
atomic_write_json(base / relative, study)
append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_frozen", "created_at": utc_now(),
    "program_id": "NEXTAI-CONTINUATION-20261004-V1", "study_path": relative,
    "study_sha256": sha256_file(base/relative), "scoring": False, "before_implementation": True, "next_cycle": 310})
path = base / "config/research.toml"
raw = path.read_bytes()
old = b'study_path = "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"'
assert raw.count(old) == 1
path.write_bytes(raw.replace(old, f'study_path = "{relative}"'.encode()))
header = ("# Prospective cycle310 — capacity exposure (2026-10-04)\n\n"
    "PVM01-CAPACITY-EXPOSURE-V1 is frozen before scientific implementation.\n"
    "Same512 Fourier features and512 optimizer steps; compare K32/128 with K32/512\n"
    "training exposure and frozen/shuffled/additive controls. Larger fit work is charged.\n"
    "Five fresh paired units,80 workers/720 trials,unchanged task law and strong classics.\n"
    "Four simultaneous98.75% primary intervals; competence/economic gates unchanged.\n"
    "Start20:50:36Z,deadline2026-10-05T00:50:36Z,180s fit/204s worker,\n"
    "full worker cap16640s,auxiliary1800s including106s startup.\n"
    "Keep v4 maintenance/scoring=false until clone conformance,v5 freeze,preflight/readiness.\n"
    "Exactly one audited EXP,no retry,WT8-9/API/schedule changes. Closed science stays fixed.\n"
    "Previous sections are preserved history; continuation program remains active.\n\n")
for name in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/SCIENTIFIC_PROTOCOL.md", "docs/CURRENT_STATUS.md"):
    path = base/name
    path.write_bytes(header.encode()+path.read_bytes())
print(json.dumps({"study":relative, "raw_sha256":sha256_file(base/relative), "roles":len(study["roles"]),
    "science_implementation_or_new_arrays":False}))
