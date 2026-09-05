import json
from pathlib import Path

from nextai_autoresearch.laboratory import laboratory_progress


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "research/laboratory/REVIEW-01-20260906-V1.json"
PLAN = ROOT / "research/plans/REVIEW-01-V1.json"
CONTRACT = ROOT / "research/plans/MUC-01-PROPOSED-CONTRACT-V1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_review01_authority_is_preparation_only() -> None:
    authority = load(AUTHORITY)
    assert authority["service_cycles_authorized"] == 1
    assert authority["stage_minutes_cap"] == 60
    assert authority["candidate_implementation_authorized"] is False
    assert authority["candidate_training_authorized"] is False
    assert authority["experiment_registration_authorized"] is False
    assert authority["scoring_authorized"] is False
    assert authority["dataset_or_model_download_authorized"] is False
    assert authority["wt_files_8_9_access_authorized"] is False
    assert authority["schedule_change_authorized"] is False


def test_muc01_contract_freezes_axes_roles_and_exact_scoring() -> None:
    contract = load(CONTRACT)
    assert contract["status"] == "proposal_for_user_decision"
    assert contract["task"]["knowledge_sizes"] == [32, 128, 512]
    assert contract["task"]["reasoning_depths"] == [1, 2, 4]
    assert contract["task"]["axes_are_full_cross_product"] is True
    assert contract["task"]["answer_format"].startswith("Exactly one canonical entity token")
    roles = {system["role"] for system in contract["systems"]}
    assert roles == {
        "competent learned full-context baseline",
        "retrieval baseline",
        "strong classical control",
        "candidate",
        "source-identical mechanism ablation",
    }
    candidate = next(s for s in contract["systems"] if s["role"] == "candidate")
    ablation = next(s for s in contract["systems"] if s["role"] == "source-identical mechanism ablation")
    assert "delta correction" in candidate["fixed_mechanism_under_test"]
    assert "isolates local delta overwrite" in ablation["isolated_contrast"]


def test_muc01_contract_charges_full_boundary_and_stops_closed() -> None:
    contract = load(CONTRACT)
    costs = " ".join(contract["measurement"]["cost"])
    for required in ("tokenizer", "training", "index", "update", "query", "RSS", "CUDA", "bytes"):
        assert required.lower() in costs.lower()
    budget = contract["future_execution_budget_if_separately_authorized"]
    assert budget["complete_development_attempts_cap"] == 2
    assert budget["final_registered_screens_cap"] == 1
    assert budget["automatic_retry"] is False
    assert budget["external_models_or_apis"] == 0
    assert budget["downloads"] == 0
    assert contract["authorization"]["next_stage_requires_new_user_approval"] is True
    assert "Stop at REVIEW-01-DECISION" in contract["stop_condition"]


def test_review01_plan_has_zero_execution_budget() -> None:
    plan = load(PLAN)
    assert plan["kind"] == "bounded_preparation_review_not_an_experiment"
    assert plan["budget"]["experiment_registrations"] == 0
    assert plan["budget"]["scoring_runs"] == 0
    assert plan["budget"]["training_runs"] == 0
    assert plan["budget"]["downloads"] == 0
    assert plan["budget"]["wt_files_8_9_reads"] == 0


def test_live_queue_stops_for_review01_decision() -> None:
    progress = laboratory_progress(ROOT)
    assert progress["next_action_id"] == "REVIEW-01-DECISION"
    assert progress["scoring_authorized"] is False
    assert progress["user_decision_required"] is True
