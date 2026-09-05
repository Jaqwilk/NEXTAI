"""Fail-closed verification for the prospective WT-01 mechanism contract."""
from __future__ import annotations

from functools import lru_cache
from itertools import product
import json
from pathlib import Path
import subprocess

from .ledger import read_jsonl
from .pc01 import require
from .utils import load_json, sha256_bytes, sha256_file


AUTHORITY_PATH = "research/laboratory/WT-01-CONTRACT-20260905-V1.json"
AUTHORITY_SHA256 = "642080a48397cd262aa1e401a5497599f3c4dcd979e4293564089e8d2188d81e"
PLAN_PATH = "research/plans/WT-01-CONTRACT-V1.json"
PLAN_SHA256 = "d4cf2883782789c6e22a4af7739e00c68c54de276d855df67398223c5fbf1f5b"
BUNDLE_PATH = "research/laboratory/WT-01-HISTORICAL-BUNDLE-V1.json"
BUNDLE_SHA256 = "8aabd5126b1cb92af1ff4dd03ce5c320b3dc07c7a362bf3cc97fae4b568b6851"
DESIGN_PATH = "research/laboratory/WT-01-FACTORIAL-DESIGN-V1.json"
DESIGN_SHA256 = "05714559ec385ad08d72edd82e8267788ce7ccfe15702e644dc5cfa7c53ae240"
DATA_PATH = "research/laboratory/WT-01-DATA-INDEPENDENCE-V1.json"
DATA_SHA256 = "7ad5df2ca46a0b2add7eba46f7a84800cc35f53da1bb487ac3685877d7ab8083"
ADDENDUM_PATH = "research/laboratory/WT-01-CONTRACT-V1-INTEGRITY-ADDENDUM.json"
ADDENDUM_SHA256 = "9b0c9fb565ed289ac4ffb4167c29ba5d644e2aecb28effa57fe9458871af09a8"
RECEIPT_PATH = "research/laboratory/WT-01-CONTRACT-V1.receipt.json"


def _git(root: Path, *args: str) -> bytes:
    process = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    require(process.returncode == 0, f"historical WT Git evidence unavailable: {' '.join(args)}")
    return process.stdout


def git_bytes(root: Path, commit: str, relative: str) -> bytes:
    require(relative and "\\" not in relative and not relative.startswith(("/", ".git/")),
            "invalid historical WT evidence path")
    require(".." not in Path(relative).parts and ":" not in relative,
            "invalid historical WT evidence path")
    return _git(root, "show", f"{commit}:{relative}")


def _authorization(root: Path) -> dict:
    require(sha256_file(root / AUTHORITY_PATH) == AUTHORITY_SHA256,
            "WT-01 contract authority missing or changed")
    require(sha256_file(root / PLAN_PATH) == PLAN_SHA256,
            "WT-01 contract plan missing or changed")
    require(sha256_file(root / ADDENDUM_PATH) == ADDENDUM_SHA256,
            "WT-01 integrity identity addendum missing or changed")
    authority = load_json(root / AUTHORITY_PATH)
    plan = load_json(root / PLAN_PATH)
    require(authority.get("training_authorized") is False
            and authority.get("scoring_authorized") is False
            and authority.get("dataset_download_authorized") is False,
            "WT-01 contract authority exceeds no-training/no-scoring scope")
    require(plan.get("authority") == AUTHORITY_PATH
            and plan.get("training_authorized") is False
            and plan.get("scoring_authorized") is False,
            "WT-01 contract plan scope changed")
    parent = authority.get("parent_receipt")
    require(isinstance(parent, str)
            and sha256_file(root / parent) == authority.get("parent_receipt_sha256"),
            "WT-01 parent decision evidence changed")
    events = [event for event in read_jsonl(root / "research/events.jsonl")
              if event.get("event") == "wt01_contract_preparation_authorized"]
    require(len(events) == 1
            and events[0].get("authority_path") == AUTHORITY_PATH
            and events[0].get("authority_sha256") == AUTHORITY_SHA256
            and events[0].get("plan_path") == PLAN_PATH
            and events[0].get("plan_sha256") == PLAN_SHA256
            and events[0].get("training_authorized") is False
            and events[0].get("scoring_authorized") is False,
            "WT-01 authority event missing, changed or repeated")
    addenda = [event for event in read_jsonl(root / "research/events.jsonl")
               if event.get("event") == "wt01_contract_integrity_identity_addendum_registered"]
    require(len(addenda) == 1
            and addenda[0].get("addendum_path") == ADDENDUM_PATH
            and addenda[0].get("addendum_sha256") == ADDENDUM_SHA256
            and addenda[0].get("prospective_benchmark_version") == "wt01_causal_contract_v1"
            and addenda[0].get("prospective_benchmark_status") == "maintenance"
            and addenda[0].get("scientific_design_changed") is False,
            "WT-01 integrity identity addendum event missing, changed or repeated")
    return authority


@lru_cache(maxsize=4)
def _verify_historical_git(root_text: str) -> None:
    root = Path(root_text)
    value = load_json(root / BUNDLE_PATH)
    commit = value["historical_git_commit"]
    _git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    _git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    for relative, digest in value["historical_files"].items():
        require(sha256_bytes(git_bytes(root, commit, relative)) == digest,
                f"historical WT Git evidence changed: {relative}")


def historical_bundle(root: Path) -> dict:
    _authorization(root)
    require(sha256_file(root / BUNDLE_PATH) == BUNDLE_SHA256,
            "WT-01 historical bundle missing or changed")
    value = load_json(root / BUNDLE_PATH)
    require(value.get("historical_source_executed") is False,
            "historical WT source must remain read-only")
    _verify_historical_git(str(root.resolve()))
    expected_audit = [
        {"path": relative, "sha256": digest}
        for relative, digest in value["historical_files"].items()
    ]
    for experiment_id, record in value["immutable_experiments"].items():
        require(sha256_file(root / record["plan_path"]) == record["plan_file_sha256"],
                f"historical WT plan changed: {experiment_id}")
        require(sha256_file(root / record["result_path"]) == record["result_file_sha256"],
                f"historical WT result changed: {experiment_id}")
        result = load_json(root / record["result_path"])
        candidate = next((item for item in result.get("candidates", [])
                          if item.get("candidate") == "wt_candidate_under_test"), None)
        require(result.get("experiment_id") == experiment_id
                and result.get("status") == "complete"
                and result.get("plan_sha256") == record["registered_plan_sha256"]
                and result.get("evaluator_sha256") == record["evaluator_sha256"]
                and candidate is not None and candidate.get("status") == "complete"
                and candidate.get("audit", {}).get("dependencies") == expected_audit,
                f"historical WT result identity changed: {experiment_id}")
        realized = sorted({trial.get("seed") for trial in candidate.get("trials", [])})
        require(realized == sorted(record["runner_seeds"]),
                f"historical WT runner seeds changed: {experiment_id}")
    dataset = value["historical_dataset"]
    require(sha256_file(root / dataset["manifest_path"]) == dataset["manifest_sha256"]
            and dataset.get("independent_test_files") == 2
            and dataset.get("runner_permutations_are_independent_physical_traces") is False,
            "historical WT data-independence boundary changed")
    identity = value.get("algebraic_identity", {})
    require("VAR(2)/ARX" in identity.get("classical_family", "")
            and identity.get("architectural_novelty_established") is False,
            "historical WT classical interpretation changed")
    return value


def factorial_design(root: Path) -> dict:
    require(sha256_file(root / DESIGN_PATH) == DESIGN_SHA256,
            "WT-01 factorial design missing or changed")
    value = load_json(root / DESIGN_PATH)
    cells = value.get("cells", [])
    actual = {(cell.get("R"), cell.get("U"), cell.get("C")) for cell in cells}
    require(len(cells) == 8 and actual == set(product((False, True), repeat=3)),
            "WT-01 factorial is not the complete 2x2x2 design")
    require(value.get("status") == "mechanism_semantics_frozen_not_executable"
            and value.get("scoring_authorized") is False,
            "WT-01 factorial was activated without authority")
    require(value.get("equivalence_controls", {}).get("historical_cell") == "R1-U1-C1"
            and "1e-12" in value["equivalence_controls"]["classical_control"],
            "WT-01 historical/VAR equivalence control changed")
    require(value.get("effect_threshold", {}).get("status") == "not_yet_frozen"
            and value["effect_threshold"].get("historical_threshold_reused") is False,
            "WT-01 effect threshold was invented or inherited")
    require(value.get("seed_policy", {}).get("independent_replication_count") == 0,
            "WT-01 runner seeds were misclassified as physical replication")
    return value


def data_independence(root: Path) -> dict:
    require(sha256_file(root / DATA_PATH) == DATA_SHA256,
            "WT-01 data-independence receipt missing or changed")
    value = load_json(root / DATA_PATH)
    known = value.get("historical_diagnostic", {})
    require(sha256_file(root / known["manifest_path"]) == known["manifest_sha256"],
            "WT-01 known-data manifest changed")
    replication = value.get("same_class_replication", {})
    adversarial = value.get("adversarial_candidate", {})
    require(replication.get("decision") == "hard_blocker_for_replication_claim"
            and replication.get("minimum_independent_physical_recordings") >= 5,
            "WT-01 independent replication requirement weakened")
    require(adversarial.get("dataset") == "wt_walks_v1"
            and adversarial.get("same_task_replication") is False
            and adversarial.get("role") == "possible different-operation adversarial evaluation only",
            "WT-01 adversarial source was misclassified")
    require(value.get("outcomes_inspected_in_this_cycle") is False
            and value.get("archive_downloaded_in_this_cycle") is False
            and value.get("data_arrays_loaded_in_this_cycle") is False,
            "WT-01 contract cycle crossed its data boundary")
    sources = read_jsonl(root / "research/sources.jsonl")
    require(sum(source.get("source_id") == adversarial.get("source_id") for source in sources) == 1,
            "WT-01 primary adversarial source missing or repeated")
    return value


def contract(root: Path) -> dict:
    authority = _authorization(root)
    return {
        "authority": authority,
        "historical_bundle": historical_bundle(root),
        "factorial_design": factorial_design(root),
        "data_independence": data_independence(root),
    }


def status(root: Path) -> dict | None:
    path = root / AUTHORITY_PATH
    events_path = root / "research/events.jsonl"
    if not path.exists() and (not events_path.exists() or not any(
            event.get("event") == "wt01_contract_preparation_authorized"
            for event in read_jsonl(events_path))):
        return None
    contract(root)
    completions = [event for event in read_jsonl(events_path)
                   if event.get("event") == "wt01_contract_preparation_completed"]
    require(len(completions) <= 1, "WT-01 contract completion repeated")
    if not completions:
        return {"complete": False, "artifacts_ready": True,
                "next_action_id": "WT-01-CONTRACT"}
    event = completions[0]
    require(event.get("receipt_path") == RECEIPT_PATH
            and sha256_file(root / RECEIPT_PATH) == event.get("receipt_sha256")
            and event.get("training_performed") is False
            and event.get("scoring_performed") is False,
            "WT-01 contract completion changed or exceeded scope")
    receipt = load_json(root / RECEIPT_PATH)
    regression = receipt.get("full_regression", {})
    require(receipt.get("status") == "complete"
            and receipt.get("decision") == "mechanism_contract_ready_replication_data_blocked"
            and regression.get("passed") is True
            and regression.get("failures") == 0
            and regression.get("errors") == 0
            and regression.get("skipped") == 0,
            "WT-01 contract receipt is not complete")
    return {"complete": True, "artifacts_ready": True,
            "next_action_id": "WT-01-DATA-HARNESS", "receipt": receipt}
