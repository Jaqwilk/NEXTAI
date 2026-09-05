"""Read-only design/data consistency checks, NOT a learning or scoring evaluator."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def check_contract(contract: dict, acquisition: dict) -> None:
    assert contract["artifact_kind"] == "prospective_design_contract_not_EXP_plan"
    assert not contract["scoring_authorized"] and not contract["executable_now"]
    assert not contract["training_performed"]
    previous_end = 0
    for name in ("train", "dev", "final"):
        part = acquisition["splits"][name]
        assert part["start_inclusive"] == previous_end, "split overlap or gap"
        assert part["bytes"] == part["end_exclusive"] - part["start_inclusive"]
        assert part["bytes"] > 256
        n = part["bytes"]
        assert sum(min(256, n - 1 - a) for a in range(0, n - 1, 256)) == n - 1
        previous_end = part["end_exclusive"]
    assert previous_end == acquisition["bytes"]
    model = contract["model"]
    d, layers = model["embedding_width"], model["layers"]
    parameters = (model["vocab_size"] + model["context_bytes"]) * d + layers * (12*d*d + 2*d) + d
    assert parameters == model["expected_unique_parameter_count"], "parameter count"
    assert model["embedding_width"] % model["heads"] == 0
    budget = contract["budget"]
    assert (budget["max_development_attempts"] + budget["max_final_replicates"]) * budget["per_fit_wall_seconds_including_dev_and_checkpointing"] <= budget["max_aggregate_fit_wall_seconds_including_final"]
    assert budget["max_aggregate_fit_wall_seconds_including_final"] <= 7200
    assert budget["per_fit_wall_seconds_including_dev_and_checkpointing"] + 600 <= budget["max_worker_wall_seconds"] <= 1800
    assert budget["max_worker_rss_bytes"] <= 10 * 1024**3
    assert budget["max_cuda_reserved_bytes"] <= 10 * 1024**3
    assert budget["service_cycle_this_artifact"] + budget["remaining_service_cycles"] == budget["max_service_cycles"] == 2
    assert budget["service_minutes_charged_this_cycle"] + budget["remaining_service_tool_minutes"] <= 120
    evaluation = contract["evaluation"]
    seeds = evaluation["final_seed_policy"]
    assert seeds["count_per_plan"] == 1 and seeds["replicate_count"] == 3
    assert seeds["unique_across_series"] and seeds["minimum"] > budget["development_seed"]
    assert evaluation["learning_pass_required_replicates"] == seeds["replicate_count"]
    assert evaluation["independent_dataset_units"] == 1


def main() -> None:
    contract = read("research/plans/PC-01-CONTRACT-V1.json")
    acquisition = read(contract["data_manifest"])
    check_contract(contract, acquisition)
    payload = (ROOT / acquisition["path"]).read_bytes()
    assert len(payload) == acquisition["bytes"]
    assert hashlib.sha256(payload).hexdigest() == acquisition["sha256"]
    for part in acquisition["splits"].values():
        subset = payload[part["start_inclusive"]:part["end_exclusive"]]
        assert hashlib.sha256(subset).hexdigest() == part["sha256"]
    history = read("research/laboratory/PC-01-HISTORY-BEFORE.json")
    for relative, digest in history["immutable_files"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    for relative, prefix in history["append_only_prefixes"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()[:prefix["bytes"]]).hexdigest() == prefix["sha256"], relative
    receipt_path = ROOT / "research/laboratory/PC-01-CONTRACT-V1.receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for relative, digest in receipt["artifact_sha256"].items():
            path = (ROOT / relative).resolve()
            assert path.is_relative_to(ROOT) and path.is_file(), relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
    rejected = []
    mutations = [
        ("overlapping_split", lambda c, a: a["splits"]["dev"].update(start_inclusive=0)),
        ("unbudgeted_training", lambda c, a: c["budget"].update(per_fit_wall_seconds_including_dev_and_checkpointing=1800)),
        ("parameter_mismatch", lambda c, a: c["model"].update(expected_unique_parameter_count=1)),
        ("missing_replication", lambda c, a: c["evaluation"]["final_seed_policy"].update(replicate_count=1)),
        ("premature_scoring", lambda c, a: c.update(scoring_authorized=True)),
    ]
    for name, mutate in mutations:
        c, a = copy.deepcopy(contract), copy.deepcopy(acquisition)
        mutate(c, a)
        try:
            check_contract(c, a)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError(f"Negative consistency control unexpectedly passed: {name}")
    print(json.dumps({"contract_consistency": "PASS", "data_hashes": "PASS",
                      "history_files_unchanged": len(history["immutable_files"]),
                      "ledger_prefixes_preserved": True, "negative_controls_rejected": rejected,
                      "candidate_training": False, "learning_measurement_validated": False}))


if __name__ == "__main__":
    main()
