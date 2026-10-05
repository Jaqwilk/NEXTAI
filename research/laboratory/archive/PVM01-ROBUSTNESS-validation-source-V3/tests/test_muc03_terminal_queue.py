from nextai_autoresearch import laboratory, research_program


def test_terminal_program_queue_cannot_suggest_another_study(tmp_path, monkeypatch):
    program = {
        "id": "MUC03-test", "program_terminal": False, "study_terminal": True,
        "study_expired": False, "ready": True, "scoring_authorized": False,
    }
    monkeypatch.setattr(laboratory, "_historical_laboratory_progress", lambda unused: {})
    monkeypatch.setattr(research_program, "status", lambda unused: dict(program))
    active = laboratory.laboratory_progress(tmp_path)
    assert active["next_action_id"] == "MUC03-STUDY-REVIEW"
    assert "select the next preregistered study" in active["next_action"]
    program["program_terminal"] = True
    closed = laboratory.laboratory_progress(tmp_path)
    assert closed["next_action_id"] == "MUC03-PROGRAM-COMPLETE"
    assert "no further study or scoring" in closed["next_action"]
    assert "select the next" not in closed["next_action"]
    assert closed["scoring_authorized"] is False
    assert closed["research_program"] == program
