"""Prospective scoring, uncertainty, data and abort controls; no experimental fit."""
from datetime import datetime, timedelta, timezone

import pytest

from nextai_autoresearch.muc02_negatives_analysis import paired_interval, evaluate_gates
from nextai_autoresearch.muc02_negatives_stage import PLAN
from nextai_autoresearch.muc02_negatives_task import world_seed, fresh_worlds, diagnostic_queries
from nextai_autoresearch.muc_contract import parse_statement
from nextai_autoresearch.runner import _stage_halt_reason
from nextai_autoresearch.utils import load_json, project_root


def test_fresh_seed_split_and_coverage():
    values = {world_seed(seed, split, k, d, i) for seed in (901, 902, 903, 904, 905)
              for split in ("T", "D") for k in (32, 128, 512) for d in (1, 2, 4) for i in range(45 if split == "T" else 15)}
    assert len(values) == 2700 and min(values) >= 2**128
    with pytest.raises(ValueError, match="Only fresh"):
        fresh_worlds(901, "F", 32, 1)
    train, dev = fresh_worlds(901, "T", 32, 1), fresh_worlds(901, "D", 32, 1)
    assert len(train) == 45 and len(dev) == 15
    assert {w.statements for w in train}.isdisjoint(w.statements for w in dev)
    assert dev[0] == fresh_worlds(901, "D", 32, 1)[0]
    assert dev[0] != fresh_worlds(902, "D", 32, 1)[0]
    queries, rows = diagnostic_queries(dev[0], 901, 32, 1, 0)
    keys = {(row[1], row[2]) for row in rows}
    assert len(queries) == 4 and queries[0] != queries[1]
    assert all(q in keys for q in queries[:2]) and all(q not in keys for q in queries[2:])
    assert queries[2][0] == "ED999" and queries[3][1] == "violet"
    assert all(parse_statement(s)[1].startswith("ED") for s in dev[0].statements)


def test_paired_intervals_and_frozen_effect_gates():
    assert paired_interval([.1] * 5, .975)["lower"] == pytest.approx(.1)
    assert paired_interval([-.1, -.05, 0., .05, .1], .975)["lower"] < 0
    with pytest.raises(ValueError, match="five"):
        paired_interval([.1] * 4)
    with pytest.raises(ValueError, match="finite"):
        paired_interval([.1] * 4 + [float("nan")])
    thresholds = load_json(project_root() / PLAN)["decision_gates"]
    contrast = {"fact_top1_accuracy": paired_interval([.1] * 5, .975), "dense_unknown_rejection": paired_interval([.2] * 5, .975),
                "accepted_fact_accuracy": paired_interval([0.] * 5), "e2e_known_accuracy": paired_interval([0.] * 5),
                "known_false_abstention": paired_interval([0.] * 5)}
    assert evaluate_gates(contrast, 1., thresholds)["decision"] == "keep_dev_recipe"
    contrast["known_false_abstention"] = paired_interval([.03] * 5)
    result = evaluate_gates(contrast, 1., thresholds)
    assert result["decision"] == "discard_proposed_recipe" and not result["architecture_promotion"]


def test_stage_failure_deadline_and_total_fit_stop_remaining_work():
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    plan = {"muc02_negatives_protocol": {"deadline_at": future, "fit_seconds_total_cap": 3600}}
    assert _stage_halt_reason(plan, {"status": "complete"}, 10) is None
    assert _stage_halt_reason(plan, {"status": "crash"}, 10) == "previous_worker_failure"
    assert _stage_halt_reason(plan, {"status": "complete"}, 3600) == "total_fit_budget"
    plan["muc02_negatives_protocol"]["deadline_at"] = "2000-01-01T00:00:00Z"
    assert _stage_halt_reason(plan) == "stage_deadline"
    assert _stage_halt_reason({}, {"status": "crash"}) is None


@pytest.mark.parametrize("k", [32, 128, 512])
@pytest.mark.parametrize("d", [1, 2, 4])
def test_symbolic_control_solves_fresh_raw_dev_and_costs(k, d):
    from nextai_autoresearch.candidates.muc02_core import SymbolicSystem
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_hard_negatives_v1 import run_trial
    system = SymbolicSystem(937, {})
    trial = run_trial(system, k, d, 937, {}, learned=False)
    assert trial["accuracy"] == trial["e2e_known_accuracy"] == trial["e2e_unknown_rejection"] == 1.
    assert len(trial["latency_samples_us"]) == trial["query_count"] == 240
    assert len(trial["world_costs"]) == 15 and trial["diagnostics"] == []
    assert all(c["query_count"] == 16 for c in trial["world_costs"])
    assert trial["fit_seconds"] == 0 and trial["calibration"]["parser_failures"] == 0


def test_dense_diagnostic_detects_wrong_ranking_and_unknown_acceptance():
    from types import SimpleNamespace
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_hard_negatives_v1 import selection_diagnostics, diagnostic_metrics
    worlds = fresh_worlds(938, "D", 32, 1)
    perfect = SimpleNamespace(synchronize=lambda: None, model=SimpleNamespace(length=96, estimated_forward_flops=lambda n: n * 100),
                              scores=lambda query, keys: [float(key == query) for key in keys])
    diagnostics = [selection_diagnostics(perfect, w, 938, 32, 1, i) for i, w in enumerate(worlds)]
    metrics = diagnostic_metrics(diagnostics)
    assert metrics["fact_top1_accuracy"] == metrics["dense_unknown_rejection"] == metrics["accepted_fact_accuracy"] == 1
    assert metrics["known_false_abstention"] == metrics["pair_false_positive_rate"] == metrics["pair_false_negative_rate"] == 0
    wrong = SimpleNamespace(synchronize=perfect.synchronize, model=perfect.model, scores=lambda query, keys: [float(key != query) for key in keys])
    broken = diagnostic_metrics([selection_diagnostics(wrong, w, 938, 32, 1, i) for i, w in enumerate(worlds)])
    assert broken["fact_top1_accuracy"] == broken["dense_unknown_rejection"] == 0
    wrong.scores = lambda query, keys: [float("nan")] * len(keys)
    with pytest.raises(ValueError, match="validity"):
        selection_diagnostics(wrong, worlds[0], 938, 32, 1, 0)
    with pytest.raises(ValueError, match="coverage"):
        diagnostic_metrics(diagnostics[:-1])
