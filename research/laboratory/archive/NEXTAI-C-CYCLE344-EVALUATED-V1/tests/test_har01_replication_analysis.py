"""Synthetic replication bindings preserve the parent's calculations and gates."""
import copy
import json
from pathlib import Path

import pytest

from nextai_autoresearch.har01_analysis import analyze as parent
from nextai_autoresearch.har01_analysis_v2 import analyze
from test_har01_analysis_contract import fixture_result, STUDY as ORIGINAL

STUDY = json.loads((Path(__file__).resolve().parents[1] / "research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json").read_text(encoding="utf-8"))


def replication_fixture(**kwargs):
    result = fixture_result(**kwargs)
    for outcome in result["candidates"]:
        for trial in outcome["trials"]:
            report = trial["fit_report"]
            report.update(train_subject=report["seed_index"] + 6, dev_subject=report["seed_index"] + 21)
    return result


@pytest.mark.parametrize("reference,effect", [(False, True), (True, False), (True, True)], ids=["bad-ref", "null", "effect"])
def test_replication_statistics_equal_unchanged_parent(reference, effect):
    old = parent(fixture_result(reference_good=reference, source_effect=effect), ORIGINAL)
    original = replication_fixture(reference_good=reference, source_effect=effect)
    before = copy.deepcopy(original)
    new = analyze(original, STUDY)
    assert original == before
    for key in ("valid", "problems", "primary", "reference", "economics", "means", "source_information_transfer", "economic_decision"):
        assert new[key] == old[key]
    assert new["replication_or_final"] is True and new["parent_results_pooled"] is False
    assert new["unseen_numeric_reserved_subjects"] == list(range(11, 16)) + list(range(26, 31))


@pytest.mark.parametrize("fault", ["old-subject", "future-subject", "source-drift", "missing-role"], ids=["old", "future", "drift", "missing"])
def test_replication_binding_failure_is_inconclusive(fault):
    result = replication_fixture(reference_good=True)
    report = result["candidates"][0]["trials"][0]["fit_report"]
    if fault == "old-subject":
        report.update(train_subject=report["seed_index"] + 1, dev_subject=report["seed_index"] + 16)
    elif fault == "future-subject":
        report.update(train_subject=report["seed_index"] + 11, dev_subject=report["seed_index"] + 26)
    elif fault == "source-drift":
        report["source_after"] = {"sha": "changed"}
    else:
        result["candidates"].pop()
    answer = analyze(result, STUDY)
    assert not answer["valid"] and answer["problems"]
    assert answer["source_information_transfer"] == answer["economic_decision"] == "INCONCLUSIVE"
