"""Freeze the newly authorized independent development replication before code/data."""
import copy
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from nextai_autoresearch.utils import atomic_write_json, sha256_file

root = Path(__file__).resolve().parents[1]
tag = "MUC02-NEGATIVES-REPLICATION-20261006-V1"
relative = f"research/plans/{tag}.json"
assert not (root / relative).exists()
parent_path = "research/plans/MUC02-HARD-NEGATIVES-20261003-V1.json"
parent = json.loads((root / parent_path).read_text(encoding="utf-8"))
plan = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
sources = ["src/nextai_autoresearch/candidates/muc02_core.py",
           "src/nextai_autoresearch/candidates/muc02_negatives.py",
           "src/nextai_autoresearch/muc03_task.py",
           "src/nextai_autoresearch/benchmarks/mutable_contact_ledger_hard_negatives_v1.py",
           "src/nextai_autoresearch/muc02_negatives_analysis.py",
           "scripts/analyze_muc02_hard_negatives.py"]
sources += [f"src/nextai_autoresearch/candidates/{name}.py" for name in parent["candidates"]]
plan.update(id=tag, created_at=now, stage_started_at="2026-10-06T01:50:00Z",
            deadline_at="2026-10-06T05:50:00Z",
            new_cohort="mutable_contact_ledger_negatives_replication_v1",
            claim="Independent visible-development replication of the previously discarded exact MUC02 sampling comparison; no pooled confirmation, architecture, transfer or economic claim",
            parent_contract_path=parent_path, parent_contract_sha256=sha256_file(root / parent_path),
            prior_experiment="EXP-20261004-0001",
            prior_result_sha256=sha256_file(root / "research/results/EXP-20261004-0001.json"),
            prior_completion_path="research/laboratory/MUC02-HARD-NEGATIVES-COMPLETION-V1.receipt.json",
            prior_completion_sha256=sha256_file(root / "research/laboratory/MUC02-HARD-NEGATIVES-COMPLETION-V1.receipt.json"),
            prior_model_core_sha256=sha256_file(root / sources[0]),
            unchanged_implementation_files={p: sha256_file(root / p) for p in sources},
            parent_git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip())
plan["data"]["seed_derivation"] = f"integer SHA256 of {tag}|seed|split|K|D|index, optional |proposal=n; first16 bytes plus2**128; parametric unchanged muc03_task, no old/calibration/final worlds"
plan["data"]["source"] = "unchanged MUC v2 task grammar and strata; fresh TAG for all five paired train/dev units; ED dev and ET train prefixes preserved"
plan["data"].update(maximum_structural_proposals_per_world=64,
    structural_construction="Same prospectively frozen conditional law as the old comparison: accept first graph satisfying fixed query strata among at most64 hash-bound proposals; every rejected proposal fsynced. Only query-strata RuntimeError permits another construction proposal. No model/outcome selection, runner seed substitution, fit/execution retry or sample filtering. Exhaustion/other failure stops all unstarted roles.",
    realized_seed_policy="five runner_random_v1 seeds sampled once after source freeze; reject any historical MUC seed collision before fit; no resampling")
plan["resources"].update(auxiliary_test_seconds_cap=1800,
    budget_authority="New human-authorized separate4h/3600fit stage; all stage wall including admin/tests/failures counted from01:50Z. Old A/MUC and B wallets remain consumed and unchanged; protected B7tickets/47000s untouched.")
plan["implementation_scope"] = {
    "model_and_sampler": "Reuse exact unchanged ten role modules, Reader, LearnedSystem, training_pairs, optimizer and192-step fit; no new candidate code",
    "benchmark": "New fresh-TAG run_suite orchestration reuses unchanged run_trial, selection_diagnostics and diagnostic_metrics with explicit fresh-world/query providers",
    "authorization": "New immutable sidecar authority, one registration/start, readiness and terminal guards; explicit config overlay takes priority only for this stage in LAB scope/contract/progress/problems. Preserve B authority/current study and old MUC terminal scope.",
    "runner": "Canonical registered run_experiment and existing independent worker/resource supervision; same muc02_negatives_protocol schema. No scope-gate bypass.",
    "analysis": "Reuse unchanged paired analysis and gates; no old/new pooling; descriptive comparison to preserved old experiment only",
    "freshness": "Record historical MUC seeds in protocol and abort before any fit on collision; newTAG distinguishes every world. Unit fixtures use separate fixtureTAG; no scoring seed or train/dev content before source freeze."
}
plan["validation"] = {
    "independent_clone": "Existing normalGit clone NEXTAI-VALIDATION-20261002, explicit PYTHONPATH=clone/src and package-origin assertion; all new scientific workers execute there only",
    "required": ["unchanged model/source hashes", "fresh TAG/splits/world seeds", "balanced paired negative types/anchor/positive/order coverage", "authority/hash/readiness/terminal/one-registration/no-retry gates", "primaries and known-answer safety threshold conformance", "existing MUC02 candidate/harness/baseline tests", "clone manifest/preflight/Doctor/Lab/lifecycle readiness before seed realization"],
    "failure": "First required check/worker failure stops unstarted scientific scope; preserve receipts and report INCONCLUSIVE. No corrective execution retry in this stage."
}
plan["frozen_metrics_and_gates_equal_to_parent"] = True
for key in ("recipe", "negative_sampling", "metrics", "decision_gates", "candidates", "roles"):
    assert plan[key] == parent[key]
atomic_write_json(root / relative, plan)
authority_relative = f"research/laboratory/{tag}.json"
assert not (root / authority_relative).exists()
authority = {
    "schema_version": 1, "id": tag, "created_at": now,
    "plan_path": relative, "plan_sha256": sha256_file(root / relative),
    "human_instruction": "prawdź, czy trening na trudnych negatywach poprawia wybór faktów i rozpoznawanie braku odpowiedzi w MUC v2. Zatwierdzam nowy etap: prerejestrację, minimalną implementację i eksperyment w klonie na świeżych train/dev, porównujący losowe i trudne negatywy dla 5 sparowanych seedów. Zachowaj ten sam model, 4096 par i 192 kroki; przed implementacją zamroź metryki i progi. Limit etapu: 4 godziny pracy i 3600 sekund łącznego fitu. Pracuj autonomicznie do ukończenia testów i raportu z wynikami, kosztami, niepewnością oraz decyzją. Zachowaj historię i ograniczenia AGENTS.md; bez retry, WT 8–9 i nowych architektur. Przy awarii lub wyczerpaniu limitu zachowaj wyniki i zgłoś niedokończony zakres.",
    "separate_budget": True, "registration_cap": 1, "execution_attempt_cap": 1,
    "fit_seconds_cap": 3600, "work_seconds_cap": 14400,
    "reopens_old_authority": False, "consumes_or_changes_B_wallet": False,
    "architecture_change": False, "WT8_9": False, "external_model_API": False,
    "schedule_change": False, "automatic_retry": False
}
atomic_write_json(root / authority_relative, authority)
print(json.dumps({"plan": relative, "sha256": sha256_file(root / relative),
                  "authority": authority_relative, "deadline": plan["deadline_at"],
                  "fresh_content": False, "implementation": False}))
