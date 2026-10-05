"""Conformance for the last reference recipe; no research training."""
from nextai_autoresearch.utils import project_root, load_json, sha256_file


def test_last_recipe_preserves_frozen_metrics_and_stability_gates():
    root = project_root()
    old = load_json(root / "research/plans/MUC03-DIAG-UNDERTRAINING-V2.json")
    new = load_json(root / "research/plans/MUC03-REFERENCE-CALIBRATION-V1.json")
    for field in ("matrix", "primary_endpoints", "diagnostics", "reference_gates", "diagnosis_gates", "resources"):
        assert new[field] == old[field]
    for field in old["recipe"]:
        if field not in ("updates", "sampling"):
            assert new["recipe"][field] == old["recipe"][field]
    assert new["data"]["tag"] != old["data"]["tag"]
    assert {v["fit_steps"] for v in new["roles"].values()} == {0, 768, 8192}
    assert new["last_reference_recipe"]["fourth_recipe_authorized"] is False
    assert sha256_file(root / "src/nextai_autoresearch/candidates/muc02_core.py") == "1a33b1e1181ba50290ec1037d00def39173290c9676976a759e3d68bc12e4c63"


def test_last_recipe_uses_unchanged_evaluator_and_candidate_implementation():
    import importlib
    from nextai_autoresearch.benchmarks import muc03_undertraining_v1, muc03_reference_calibration_v1
    from nextai_autoresearch.candidates.muc03_reference import Candidate
    assert muc03_reference_calibration_v1.run_suite is muc03_undertraining_v1.run_suite
    for i in range(5):
        module = importlib.import_module(f"nextai_autoresearch.candidates.muc03_hard_8192_s{i}")
        assert module.Candidate.__bases__ == (Candidate,)
        assert module.Candidate.fit is Candidate.fit
        assert module.Candidate.new_session is Candidate.new_session
