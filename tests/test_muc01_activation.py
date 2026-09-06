import json
from pathlib import Path

from nextai_autoresearch.laboratory import laboratory_progress, pc01_scope_problems
from nextai_autoresearch.schemas import validate_document


ROOT = Path(__file__).resolve().parents[1]


def test_authority_is_one_attempt_and_forbids_candidate_and_wt_scope() -> None:
    value = json.loads((ROOT / "research/laboratory/MUC-01-CALIBRATION-20260906-V1.json").read_text(encoding="utf-8"))
    assert value["experiment_registrations_cap"] == 1
    assert value["runner_random_seeds"] == 1
    assert value["automatic_retry"] is False
    assert value["candidate_mechanism_implementation_authorized"] is False
    assert value["wt_files_8_9_access_authorized"] is False


def test_live_queue_authorizes_only_muc_calibration() -> None:
    progress = laboratory_progress(ROOT)
    assert progress["next_action_id"] in {"MUC-01-CALIBRATION", "MUC-01-CALIBRATION-DECISION"}
    if progress["next_action_id"] == "MUC-01-CALIBRATION":
        assert progress["scoring_authorized"] is True
        assert pc01_scope_problems(ROOT) == []


def test_frozen_plan_schema_accepts_only_exact_matrix_and_roles() -> None:
    plans = sorted((ROOT / "research/plans").glob("EXP-*.json"))
    muc = [json.loads(path.read_text(encoding="utf-8")) for path in plans if json.loads(path.read_text(encoding="utf-8")).get("benchmark") == "mutable_contact_ledger_v1"]
    for plan in muc:
        validate_document("experiment_plan", plan, ROOT)
        assert plan["matrix"]["knowledge_sizes"] == [32, 128, 512]
        assert plan["matrix"]["reasoning_depths"] == [1, 2, 4]
        assert plan["candidates"] == ["dense_transformer_v1", "bm25_iterative_reader_v1", "symbolic_last_write_graph_v1"]
