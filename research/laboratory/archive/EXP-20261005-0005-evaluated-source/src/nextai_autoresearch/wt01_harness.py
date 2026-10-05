"""Fail-closed lifecycle checks for the final WT-01 service cycle."""
from __future__ import annotations

from itertools import product
import importlib
from pathlib import Path

from .ledger import read_jsonl
from .pc01 import require
from .utils import load_json, sha256_file


AUTHORITY_PATH = "research/laboratory/WT-01-DATA-HARNESS-20260905-V1.json"
AUTHORITY_SHA256 = "48a251d47cf6f177b74eca863ea63770d1c9a5c3000f49353975f47c26ae9933"
PLAN_PATH = "research/plans/WT-01-DATA-HARNESS-V1.json"
PLAN_SHA256 = "c1b448d454861e231ea2638c9a0c053c0f53889d2dd05b5cde02fa3b2050e4be"
EXECUTION_PATH = "research/laboratory/WT-01-FACTORIAL-EXECUTION-CONTRACT-V1.json"
EXECUTION_SHA256 = "7b0b60963b86234bf0101e730d4bca487cc04baa0a8b076b296101152f90c5cd"
DATA_PATH = "research/laboratory/WT-01-DATA-FREEZE-V1.json"
DATA_SHA256 = "22738453eddf5340c93dfc9863115fe1c2a0a7ff391e178b8e8b0e997277ee5b"
RECEIPT_PATH = "research/laboratory/WT-01-DATA-HARNESS-V1.receipt.json"


def contract(root: Path) -> dict:
    from .wt01_contract import status as parent_status
    require(parent_status(root).get("complete") is True,
            "WT-01 data/harness requires the completed mechanism contract")
    for relative, digest in ((AUTHORITY_PATH, AUTHORITY_SHA256), (PLAN_PATH, PLAN_SHA256),
                             (EXECUTION_PATH, EXECUTION_SHA256), (DATA_PATH, DATA_SHA256)):
        require(sha256_file(root / relative) == digest, f"WT-01 harness artifact changed: {relative}")
    authority, plan = load_json(root / AUTHORITY_PATH), load_json(root / PLAN_PATH)
    execution, data = load_json(root / EXECUTION_PATH), load_json(root / DATA_PATH)
    require(authority.get("training_authorized") is False
            and authority.get("scoring_authorized") is False
            and authority.get("known_historical_data_arrays_authorized") is False,
            "WT-01 harness authority exceeded")
    require(plan.get("authority") == AUTHORITY_PATH
            and plan.get("training_authorized") is False
            and plan.get("scoring_authorized") is False,
            "WT-01 harness plan changed scope")
    require(execution.get("benchmark_status") == "maintenance"
            and execution.get("benchmark_version") == "wt01_causal_factorial_diagnostic_v1"
            and execution["primary_contrast"]["smallest_effect_of_interest"] == 0.03343253453162794
            and execution["decision_logic"]["replication_claim_permitted"] is False,
            "WT-01 execution contract was weakened")
    require(data.get("fresh_same_protocol_physical_recordings") == 0
            and data.get("hidden_holdout_claim_permitted") is False
            and data.get("replication_claim_permitted") is False
            and data["this_service_cycle"]["real_data_arrays_loaded"] is False,
            "WT-01 data scope was relabeled or crossed")
    events = [event for event in read_jsonl(root / "research/events.jsonl")
              if event.get("event") == "wt01_data_harness_authorized"]
    require(len(events) == 1 and events[0].get("authority_sha256") == AUTHORITY_SHA256
            and events[0].get("plan_sha256") == PLAN_SHA256,
            "WT-01 harness authorization event missing, changed or repeated")
    from .wt01_factorial_core import FactorialCandidate
    realized = set()
    for r, u, c in product((0, 1), repeat=3):
        name = f"wt01_r{r}_u{u}_c{c}_v1"
        candidate = importlib.import_module(
            f"nextai_autoresearch.candidates.{name}"
        ).Candidate(0)
        require(type(candidate).__mro__[1] is FactorialCandidate,
                f"WT-01 wrapper does not directly share the frozen core: {name}")
        realized.add(candidate.factors)
    require(realized == set(product((False, True), repeat=3)),
            "WT-01 factorial wrappers are incomplete")
    return {"authority": authority, "plan": plan, "execution": execution, "data": data}


def status(root: Path) -> dict | None:
    path = root / AUTHORITY_PATH
    if not path.exists():
        return None
    contract(root)
    completions = [event for event in read_jsonl(root / "research/events.jsonl")
                   if event.get("event") == "wt01_data_harness_completed"]
    require(len(completions) <= 1, "WT-01 harness completion repeated")
    if not completions:
        return {"complete": False, "next_action_id": "WT-01-DATA-HARNESS"}
    event = completions[0]
    require(event.get("receipt_path") == RECEIPT_PATH
            and sha256_file(root / RECEIPT_PATH) == event.get("receipt_sha256")
            and event.get("training_performed") is False
            and event.get("scoring_performed") is False,
            "WT-01 harness completion changed or exceeded scope")
    receipt = load_json(root / RECEIPT_PATH)
    regression = receipt.get("full_regression", {})
    require(receipt.get("status") == "complete"
            and receipt.get("decision") == "diagnostic_harness_ready_user_review_required"
            and regression.get("passed") is True
            and regression.get("failures") == regression.get("errors") == regression.get("skipped") == 0,
            "WT-01 harness receipt is not complete")
    return {"complete": True, "next_action_id": "WT-01-DEV-1", "receipt": receipt}
