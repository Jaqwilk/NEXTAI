from pathlib import Path

import pytest

from nextai_autoresearch import wt01_contract
from nextai_autoresearch.benchmarks import wt01_causal_contract_v1
from nextai_autoresearch.utils import project_root


def test_real_contract_preserves_historical_identity_and_scope():
    value = wt01_contract.contract(project_root())
    bundle = value["historical_bundle"]
    assert bundle["historical_git_commit"] == "49525156586e765c07f96e2f41ea17c709a3debb"
    assert bundle["historical_files"][
        "src/nextai_autoresearch/candidates/wt_candidate_under_test.py"
    ] == "4471f2a999f9432e9d2e6fb56d309ebe7af52cca6dff246ab1b439b38f035104"
    assert bundle["algebraic_identity"]["architectural_novelty_established"] is False
    assert value["authority"]["training_authorized"] is False
    assert value["authority"]["scoring_authorized"] is False


def test_factorial_is_complete_and_keeps_seed_replication_separate():
    design = wt01_contract.factorial_design(project_root())
    assert len(design["cells"]) == 8
    assert design["equivalence_controls"]["historical_cell"] == "R1-U1-C1"
    assert design["seed_policy"]["runner_random_count"] == 3
    assert design["seed_policy"]["independent_replication_count"] == 0
    assert design["effect_threshold"]["status"] == "not_yet_frozen"


def test_data_receipt_blocks_false_replication_and_classifies_walks_as_adversarial():
    receipt = wt01_contract.data_independence(project_root())
    assert receipt["same_class_replication"]["decision"] == "hard_blocker_for_replication_claim"
    assert receipt["adversarial_candidate"]["dataset"] == "wt_walks_v1"
    assert receipt["adversarial_candidate"]["same_task_replication"] is False
    assert receipt["archive_downloaded_in_this_cycle"] is False
    assert receipt["outcomes_inspected_in_this_cycle"] is False


def test_historical_git_substitution_fails_closed(monkeypatch):
    root = project_root()
    actual = wt01_contract.git_bytes
    wt01_contract._verify_historical_git.cache_clear()

    def substituted(base: Path, commit: str, relative: str) -> bytes:
        value = actual(base, commit, relative)
        if relative.endswith("wt_candidate_under_test.py"):
            return value + b"substitution"
        return value

    monkeypatch.setattr(wt01_contract, "git_bytes", substituted)
    with pytest.raises(ValueError, match="historical WT Git evidence changed"):
        wt01_contract.historical_bundle(root)


def test_contract_status_is_never_scoring_authority():
    value = wt01_contract.status(project_root())
    assert value is not None
    assert value["artifacts_ready"] is True
    assert value["next_action_id"] in {"WT-01-CONTRACT", "WT-01-DATA-HARNESS"}


def test_maintenance_benchmark_has_no_scoring_entry_point():
    assert wt01_causal_contract_v1.BENCHMARK_VERSION == "wt01_causal_contract_v1"
    with pytest.raises(RuntimeError, match="not executable"):
        wt01_causal_contract_v1.run_suite(None, None)
