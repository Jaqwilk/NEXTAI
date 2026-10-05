"""Exact user-authorized three-replica scope; old dev authority stays immutable."""
from pathlib import Path

from .config import load_config
from .ledger import read_jsonl, latest_plan_statuses
from .pc01 import require
from .utils import load_json, sha256_file, sha256_json

PATH = "research/laboratory/PC-01-FINAL-ACTIVATION-20260905-V1.json"
SHA256 = "6512cc0f9a0967e48087db2935effd420eed5b60d792cae84da539c009232506"


def authority(root: Path) -> dict | None:
    from .laboratory import final_preparation_status
    from .pc01_execution import registered_plans, attempt_history, SERIES
    from .pc01_closure import closure
    from .pc01_final_transition import selected_transition
    events = [e for e in read_jsonl(root / "research/events.jsonl") if e.get("event") == "pc01_final_authorized"]
    path = root / PATH
    if not path.exists() and not events:
        return None
    require(path.is_file() and sha256_file(path) == SHA256 and len(events) == 1,
            "final authority missing, changed or repeated")
    require(events[0].get("authorization_path") == PATH and events[0].get("authorization_sha256") == SHA256,
            "final authority event mismatch")
    policy = load_json(path)
    require(sha256_file(root / policy["preparation_receipt"]) == policy["preparation_receipt_sha256"], "final preparation receipt changed")
    require(final_preparation_status(root)["complete"], "final preparation incomplete")
    historical = closure(root)
    if historical is None:
        selected_transition(root, policy["selected_dev_id"])
    else:
        require(historical["terminal_decision"]["decision"] == "positive_control_pass",
                "terminal PC-01 closure decision changed")
        require(load_json(root / SERIES)["selected_dev_id"] == policy["selected_dev_id"],
                "terminal PC-01 closure selected development changed")
    plans = registered_plans(root)
    require({p["experiment_id"]: sha256_json(p) for p in plans if p["phase"] == "dev"} == policy["dev_plans"],
            "final authority cannot add/omit/change dev")
    history = attempt_history(root)
    dev = [a for a in history if a["phase"] == "dev"]
    require(sha256_json(dev) == policy["dev_history_sha256"], "historical dev accounting changed")
    finals = [p for p in plans if p["phase"] == "final"]
    require(len(finals) <= 3, "final registration cap exceeded")
    for plan in finals:
        require(plan["candidate"] == policy["candidate"] and plan["benchmark"] == policy["cohort"]
                and plan["recipe_sha256"] == policy["recipe_sha256"], "final registration scope changed")
        require((root / SERIES).is_file() and plan["series_sha256"] == sha256_json(load_json(root / SERIES)),
                "final registration series mismatch")
    terminal = latest_plan_statuses(root)
    failed = any(p["experiment_id"] in terminal for p in finals)
    complete = 0
    for plan in finals:
        result_path = root / "research/results" / f"{plan['experiment_id']}.json"
        if result_path.exists():
            result = load_json(result_path)
            complete += 1
            failed |= result["status"] != "complete" or not result["integrity_after"]["ok"]
    return {**policy, "finals": finals, "completed": complete, "failed": failed,
            "terminal": failed or complete == 3, "series_frozen": (root / SERIES).exists()}


def scope(root: Path, policy: dict, *, candidate=None, phase=None, experiment_id=None, series_freeze=False) -> list[str]:
    if load_config(root).benchmark_version != policy["cohort"]:
        return ["Final authority cannot activate another cohort"]
    if policy["terminal"]:
        return ["Final series terminal; review required, no replacement or retry"]
    if series_freeze:
        return [] if not policy["series_frozen"] and not policy["finals"] else ["Final series freeze is single-use"]
    if experiment_id is not None:
        return [] if experiment_id in {p["experiment_id"] for p in policy["finals"]} else ["Only a registered final replica is authorized"]
    if candidate != policy["candidate"] or phase != "final":
        return ["Final authority forbids dev, legacy and different candidates"]
    if not policy["series_frozen"]:
        return ["Freeze the approved series before final registration"]
    if len(policy["finals"]) >= 3:
        return ["Three final registrations consumed; no replacement"]
    return []
