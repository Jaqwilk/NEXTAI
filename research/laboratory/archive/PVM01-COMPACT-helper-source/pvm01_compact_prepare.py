"""Author prospective records only; no candidate, generator or research array access."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import sha256_file, utc_now

BASE = Path(__file__).resolve().parents[2]
ORIGINAL = BASE.parent / "NEXTAI"
STUDY_PATH = "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"
study = copy.deepcopy(json.loads((BASE / "research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json").read_text()))
assert not (BASE / STUDY_PATH).exists()
study.update(id="PVM01-COMPACT-FEATURE-SCREEN-V1", cohort="paired_view_mutable_memory_v4",
             study_kind="paired_view_compact_feature_memory", auxiliary_charge_id_prefix="PVM01-COMPACT-",
             study_started_at="2026-10-04T19:32:56Z", study_deadline_at="2026-10-04T23:32:56Z",
             question="Does learning a 512-dimensional Fourier feature map through a fixed sequential delta memory improve fact-value answers and absence detection over source-identical frozen and shuffled feature learning, while retaining quality against RFF2048 and competent dense/cache and strongest fitted retrieval/classical controls?")
arms = ["compact_learned", "compact_frozen", "compact_shuffled", "compact_additive", "delta", "dense",
        "dense_cached_cpu", "dense_cached_cuda", "exact_nn_cpu", "ridge", "ridge32",
        "ridge_pca_scan", "ridge_pca_tree", "kernel", "raw"]
study["candidates"] = [f"pvm01_{arm}_s{i}" for arm in arms for i in range(5)]
study["roles"] = {name: {"arm": arm, "seed_index": i,
                         "fit_steps": 0 if arm.startswith("ridge") or arm in {"kernel", "raw"} else 2048}
                  for arm in arms for i in range(5) for name in [f"pvm01_{arm}_s{i}"]}
recipe = study["recipe"]
recipe.update(compact_feature_dimension=512, compact_frequencies=256, compact_feature_steps=512,
              compact_feature_learning_rate=.003, compact_feature_weight_decay=0.,
              compact_feature_gradient_clip=1., compact_feature_batch=4,
              compact_feature_batch_seed_xor=0x43464D31, compact_feature_shuffle_seed_xor=0x43465331,
              compact_null_score=.5, compact_logit_scale=20.,
              compact_feature_equations="Shared trained transport frozen after the exact reference2048 alignment steps. R[64,256] initialized from the same Gaussian sigma.35 and projection seed xor as RFF2048, with phi(x)=concat(cos(unit(x)R),sin(unit(x)R))/sqrt256, norm1. The same R is used for write and transported query. W[512,16]=0 per episode; beta1 sequential delta update, differentiable through all writes during training. No learned write gate, query handle, key/value store or replay. Inference CPU fp32 and NumPy trigonometry as prior delta; all copies included.",
              compact_feature_training="Only unchanged legal T-sets (128 episodes at K32 and128,8 independent queries, target position including NULL) used after transport. Precompute normalized writes and transported queries with frozen encoder; preserve/hash precomputation.512 fixed AdamW steps, lr.003,WD0,gradient norm clip1. Alternate K32/128, batch4 sampled with replacement using seed xor compact batch constant. Draw fresh independent16-way support value labels each step from the SAME generator, gather query targets from legal training target positions; NULL target class16. All batch indices/value-label draws are preserved as a SHA256 digest with the source/seed. Unroll delta W through every initial write, read all8 independent questions, concatenate fixed NULL score.5, scale20, mean CE over17 classes. No gradient truncation, early stopping or dev adaptation; last step selected. T-sets have zero updates; update generalization on D is explicitly out-of-training, not trained overwrite. No new private generator or task change.",
              compact_feature_controls="All four compact arms share exact encoder init/final weights/alignment losses, feature init, capacity, data and memory code. Frozen feature map skips feature optimizer only. Shuffled feature learning uses one fixed permutation of128 query episode groups per K, while supports/targets/batch/value-label draws remain unchanged; alignment remains correct. Learned and additive have identical feature fitting and all512 losses, and differ only in online write subtraction during inference. Frozen/shuffled are controls of feature learning, not transport training. Delta2048 comparator uses its unchanged existing alias/core; no old data/checkpoint reused.",
              compact_feature_scope="Trainable Fourier features and known differentiable fast-weight memory; a minimal causal feature-learning test, not novelty or faithful paper reproduction. The update rule and beta remain classical and fixed. No general-language or learned-controller claim.")
study["data"]["tag"] = study["id"]
study["data"]["legal_training_sets"] = "Same source-identical T-sets as dense,128 episodes per K32/128, zero update rounds; supervised target positions legal at training only. Generated value labels are independent of observations and new each optimizer step. No T-calibration/D query or label used by optimizer."
study["diagnosis_gates"] = {
    "independent_units": 5, "simultaneous_primary_interval_level": .9875,
    "feature_vs_frozen_mean_full_gain_min": .05, "feature_vs_shuffled_mean_full_gain_min": .05,
    "both_feature_gain_ci_lower_min": .02, "all_five_feature_gains_positive": True,
    "K512_updated_gain_mean_min": .05, "K512_updated_gain_ci_lower_min": .02,
    "all_five_K512_updated_gains_positive": True, "retained_vs_RFF2048_ci_lower_min": -.02,
    "interpretation": "Causal feature learning through a fixed delta rule at matched512 capacity; update generalization beyond zero-update T-sets. A passing screen is not economic or architectural promotion."}
study["resources"].update(fit_seconds_per_role_cap=180, worker_seconds_cap=204,
                          worker_charge_ceiling_with_monitor_margin=208, fit_seconds_study_cap=15600,
                          auxiliary_test_seconds_cap=1800)
study["freshness_policy"] = "Five fresh runner-random seeds and independent256bit nonces after the one paid preregistration; disjoint from consumed0004,0005,0006 before any arrays. Collision invalidates without replacement. Same legal T/D across15 arms; no old fit/arrays/calibration reuse."
study["uncertainty"] = "Five fresh independent combined seed/data units, equal cell weights; updated/retained only rounds1/4. Four two-sided98.75% paired Student-t df4 intervals give familywise95% Bonferroni: full learned-frozen, full learned-shuffled, K512 updated learned-frozen, retained learned-RFF2048. All unit values and four directional counts retained. Other metrics/costs paired descriptive95%; no episode/query pseudoreplication. Existing outer economic gates unchanged."
study["decision_policy"] = "Validity first:75 workers/675 trials, integrity, all legal pairing and source/encoder/feature-fit equivalence required. Dense competence remains unchanged. KEEP compact feature recipe for further validation only if all four primary gates and compact/dense competence pass. Valid primary failure DISCARD exact512/512-step feature recipe, preserve narrower observed effects without economic claim. Competence failure also DISCARD this economic recipe, not entire feature/fast-weight family. Failed dense comparison or crash INCONCLUSIVE and stop unstarted scope; no retry. All strong classics may win. No economic/transfer/novelty promotion or fresh final in this screen; whole program remains active."
study["implementation_scope"] = "Add one compact feature core,20 thin aliases, one v4 evaluator delegating unchanged scoring/timing/private binding and task generator, plus stored-only claim-specific analyzer/tests. Minimally extend cohort/schema/dispatch and consumed-unit freshness guard to0006. Preserve v1-v3 generator, cores, evaluator, plans/results/raw archives. Frozen synthetic CPU fixtures only before audited seeds; no research training outside runner."
study["diagnostics"]["reproducibility"] += ["compact initial/final frequency hashes", "compact learned/additive exact feature losses and hashes", "all compact identical transport/loss identity", "feature batch/value-label digest", "fixed shuffled episode permutations", "precomputed training input hashes", "complete512 feature loss and gradient norm traces"]
study["diagnostics"]["raw_predictions"] += " Same NULL fact-handle policy applies to all compact_* arms; no handle reconstruction. Retrieval/classical arms preserve actual handle diagnostics."
study["prospective_feasibility"] = {"parameters": "16384 feature frequencies plus unchanged transport; W8192 floats, no nonlinear feature hidden network or dependency.",
    "training_bound_estimate": "512 steps x batch4 x mean80 writes =163840 differentiable per-episode updates; each W has8192 floats. Batched unroll has at most128 sequential nodes, ~16MiB W intermediates plus autograd buffers per step. This is an analytical estimate, not benchmark observation. GPU/CPU process caps and180s fit timer override prediction.",
    "cost_tradeoff": "Feature/W storage is four times smaller than RFF2048. No assumption it beats explicit retrieval/PCA; training objective/capacity may fail at extrapolated K512. This question is distinct from increasing transport steps."
}
(BASE / STUDY_PATH).write_text(json.dumps(study, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
append_jsonl(BASE / "research/events.jsonl", {"event":"research_program_study_frozen", "created_at":utc_now(),
    "program_id":"NEXTAI-CONTINUATION-20261004-V1", "study_path":STUDY_PATH, "study_sha256":sha256_file(BASE/STUDY_PATH),
    "scoring":False, "before_implementation":True, "next_cycle":309})
source = {"source_id":"SRC-0445", "checked_at":utc_now(), "year":2021, "primary_source":True,
    "url":"https://arxiv.org/abs/2106.02795", "title":"Learnable Fourier Features for Multi-Dimensional Spatial Positional Encoding",
    "source_type":"paper", "authors":["Yang Li", "Si Si", "Gang Li", "Cho-Jui Hsieh", "Samy Bengio"],
    "claims_supported":["Trained Fourier feature maps with MLP modulation for multidimensional positional encoding."],
    "relevance":"Our inference: trainable frequencies are a justified small alternative to fixed RFF in memory; this study is not positional encoding or a faithful reproduction, and makes no novelty claim."}
append_jsonl(BASE / "research/sources.jsonl", source)
config = BASE / "config/research.toml"
raw = config.read_bytes()
old = b'study_path = "research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json"'
assert raw.count(old)==1
config.write_bytes(raw.replace(old, f'study_path = "{STUDY_PATH}"'.encode()))
header = ("# Prospective cycle309 — compact feature learning (2026-10-04)\n\n"
    "PVM01-COMPACT-FEATURE-SCREEN-V1 is preregistered before implementation.\n"
    "Trainable Fourier512 features through fixed delta memory versus frozen/shuffled\n"
    "source-identical controls; unchanged correct transport and T-sets, no trained gate.\n"
    "Five fresh paired units,75 workers/675 trials, K32/128/512, updates0/1/4.\n"
    "Dense with CPU/CUDA cache and strongest ridge/PCA/tree/Nystrom/exact retrieval\n"
    "remain controls. Four simultaneous98.75% primary intervals, outer economic\n"
    "gates unchanged. Start19:32:56Z, deadline23:32:56Z,180s fit/204s worker,\n"
    "full worker cap15600s and auxiliary1800s including startup checks.\n"
    "Maintain v3 maintenance/scoring=false until clone conformance and v4 freeze,\n"
    "preflight/readiness. Exactly one audited EXP, no retry,WT8-9/API/schedule change.\n"
    "Closed evidence unchanged; global continuation and later adverse/final remain.\n"
    "Previous sections are preserved history.\n\n")
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/SCIENTIFIC_PROTOCOL.md", "docs/CURRENT_STATUS.md"):
    path=BASE/relative
    path.write_bytes(header.encode()+path.read_bytes())
assert not subprocess.check_output(["git","status","--porcelain"],cwd=ORIGINAL).strip()
tracked = subprocess.check_output(["git","ls-files","-z"], cwd=ORIGINAL).decode().split("\0")
snapshot = {name:sha256_file(ORIGINAL/name) for name in tracked if name and (ORIGINAL/name).is_file()}
prefixes = {}
for name in ("research/events.jsonl", "research/experiments.tsv", "research/plan_registry.jsonl", "research/sources.jsonl", "research/hypothesis_events.jsonl"):
    payload=(BASE/name).read_bytes()
    original=(ORIGINAL/name).read_bytes()
    # Freeze snapshot records before the newly authorized append records.
    prefixes[name]={"bytes":len(original), "sha256":hashlib.sha256(original).hexdigest()}
snapshot_path=BASE/"research/reviews/PVM01-COMPACT-startup-history-V1.json"
snapshot_path.write_text(json.dumps({"original_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ORIGINAL).decode().strip(),
    "files":snapshot,"append_only_prefixes":prefixes,"no_research_arrays_or_models":True},indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"study":STUDY_PATH,"sha256":sha256_file(BASE/STUDY_PATH),"roles":len(study["roles"]),"original_files":len(snapshot)}))
