from __future__ import annotations

from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v4 as bench
from nextai_autoresearch.config import load_config
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.runner import _frontier


SEED = 1_501_103


def test_v5_final_summary_and_universal_frontier_are_complete() -> None:
    config = load_config()
    protocol = config.raw["recombination"]
    axes = list(protocol["pareto_capability_metrics"])
    directions = {
        metric: "maximize" if metric in config.raw["metrics"]["maximize"] else "minimize"
        for metric in axes
    }
    plan = {
        "benchmark": "heldout_mechanism_recombination_v5",
        "primary_metrics": [*axes, "reuse_coverage"],
        "metric_directions": {**directions, "reuse_coverage": "maximize"},
        "mechanism_recombination_protocol": {"pareto_capability_metrics": axes},
    }
    names = [
        "experience_operator_compiler", "experience_operator_independent",
        "experience_operator_no_pairing", *bench.BASELINES,
    ]
    rows = []
    for name in names:
        trials = [
            bench._run_cell(name, size, exposure, 2, SEED, 1103, 4_194_304)
            for size in (8, 32, 128) for exposure in bench.EXPOSURES
        ]
        summary = aggregate_trials(trials)
        rows.append({"candidate": name, "status": "complete", "summary": summary})
        assert all(summary[metric] is not None for metric in axes)

    frontier, contract = _frontier(rows, plan, config)
    assert contract == {
        "maximize": axes[:6],
        "minimize": axes[6:],
    }
    assert frontier
    assert "operator_interpreter" in frontier
    assert "experience_operator_compiler" not in frontier
    assert "reuse_coverage" not in contract["maximize"]
