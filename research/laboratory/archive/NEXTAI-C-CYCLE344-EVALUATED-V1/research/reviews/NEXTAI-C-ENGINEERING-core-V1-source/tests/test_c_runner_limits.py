"""C admission separates total cold workers from aggregate trusted fit."""
import time
import pytest
from nextai_autoresearch.runner import _c_worker_remaining_limits, _stage_halt_reason
from nextai_autoresearch.worker_resources import resource_problem
from nextai_autoresearch.utils import atomic_write_json


def limits():
    return {"program_id": "NEXTAI-C-STABILIZATION-ASM-SCREEN-20261008-V1",
            "fit_seconds_total_cap": 9000, "supervised_fit_total_cap": 3600,
            "fit_seconds_cap": 120, "worker_seconds_cap": 180,
            "max_cuda_reserved_bytes": 1024}


def test_fit_and_full_worker_limits_are_independent():
    plan = {"research_program_protocol": limits()}
    assert _stage_halt_reason(plan, fit_charged=500, supervised_fit_charged=3600) == "total_supervised_fit_budget"
    assert _stage_halt_reason(plan, fit_charged=9000, supervised_fit_charged=100) == "total_fit_budget"
    assert _stage_halt_reason(plan, fit_charged=500, supervised_fit_charged=3599) is None


def test_legacy_protocol_does_not_gain_c_fit_semantics():
    old = {"fit_seconds_total_cap": 6000}
    assert _stage_halt_reason({"research_program_protocol": old}, fit_charged=1, supervised_fit_charged=9999) is None
    assert _c_worker_remaining_limits(old, -1, False) == old


@pytest.mark.parametrize("bad", [0, -1, True, float("inf"), float("nan")], ids=["zero","negative","bool","infinite","nan"])
def test_exhausted_or_invalid_budget_cannot_admit_worker(bad):
    with pytest.raises(ValueError):
        _c_worker_remaining_limits(limits(), bad, 180)
    with pytest.raises(ValueError):
        _c_worker_remaining_limits(limits(), 120, bad)


def test_remaining_fit_changes_parent_clock_without_mutating_recipe(tmp_path):
    original = limits()
    bounded = _c_worker_remaining_limits(original, .1, 2)
    assert original["fit_seconds_cap"] == 120 and original["worker_seconds_cap"] == 180
    output = tmp_path / "worker.json"
    now = time.monotonic()
    atomic_write_json(output.with_suffix(".phase.json"), {"phase": "fit", "fit_started": now-.2, "fit_elapsed": 0.})
    assert resource_problem(output, bounded, now-1, now)[0] == "fit_timeout"
    assert resource_problem(output, original, now-1, now)[0] is None
