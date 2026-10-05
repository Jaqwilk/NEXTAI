import runpy

from nextai_autoresearch.utils import project_root


def test_stored_diagnosis_separates_ranking_abstention_and_unknown():
    summarize = runpy.run_path(str(project_root() / "scripts/analyze_muc_ranking_absence.py"))["summarize"]
    common = {"known": True, "query": "ED001 amber", "selected_key": "ED001 amber", "top1_correct": True,
        "accepted_correct": True, "rejected": False, "rows_scored": 40,
        "pair_negatives": 38, "pair_fp": 1, "subject_negatives": 8, "subject_fp": 1,
        "relation_negatives": 4, "relation_fp": 0, "unknown_type": None}
    observations = [common, {**common, "selected_key": "ED002 amber", "top1_correct": False,
        "accepted_correct": False, "rejected": True},
        {**common, "known": False, "query": "ED999 amber", "unknown_type": "subject", "top1_correct": False,
        "accepted_correct": False, "rejected": False}]
    result = summarize(observations)
    assert result["known_count"] == 2 and result["unknown_count"] == 1
    assert result["known_top1_correct_rate"] == .5 and result["known_rejected_rate"] == .5
    assert result["known_wrong_key"] == 1 and result["known_right_key_wrong_timestamp"] == 0
    assert result["unknown_subject_rejection_rate"] == 0 and result["unknown_relation_rejection_rate"] is None
    assert result["known_pair_negative_pairs"] == 76 and result["known_pair_false_positive_pairs"] == 2
