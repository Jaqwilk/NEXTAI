from __future__ import annotations

from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.utils import project_root


def test_post_exp0059_g1_window_is_durable_and_calibration_precedes_microbenchmarks() -> None:
    root = project_root()
    events = [
        event
        for event in read_jsonl(root / "research" / "events.jsonl")
        if event.get("event") == "g1_decision_window_started"
    ]
    assert len(events) == 1
    event = events[0]
    assert event["window_id"] == "G1-POST-EXP-0059-V1"
    assert event["start_after_experiment_id"] == "EXP-20260901-0059"
    assert event["qualifying_experiment_count"] == 0
    assert event["maximum_qualifying_experiments"] == 8
    assert event["calibration_due_cycle"] == 228
    assert event["calibration_required_before_new_microbenchmark"] is True

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    program = (root / "program.md").read_text(encoding="utf-8")
    roadmap = (root / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    for text in (agents, program, roadmap):
        assert "G1-POST-EXP-0059-V1" in text
        assert "eight" in text.lower() or "osiem" in text.lower()
    assert "cycle 228" in agents
    assert "Cycle 228" in program
    assert "cykl 228" in roadmap.lower()
