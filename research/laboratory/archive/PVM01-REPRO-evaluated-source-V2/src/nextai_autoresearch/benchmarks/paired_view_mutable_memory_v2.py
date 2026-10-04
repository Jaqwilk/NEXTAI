"""Versioned repair of the runner-private JSON path binding; v1 stays intact."""
from pathlib import Path
import re

from ..utils import project_root
from .paired_view_mutable_memory_v1 import run_suite as reference_suite

BENCHMARK_VERSION = "paired_view_mutable_memory_v2"


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    experiment_id = plan["experiment_id"]
    if not re.fullmatch(r"EXP-\d{8}-\d{4}", experiment_id):
        raise ValueError("Invalid runner-private experiment identity")
    temporary_root = (project_root() / "research" / "tmp").resolve()
    expected = temporary_root / experiment_id / "pvm01-private-data.json"
    private_path = Path(plan["pvm01_private_data_path"]).resolve(strict=True)
    if not private_path.is_relative_to(temporary_root) or private_path != expected:
        raise ValueError("Runner-private path must match this experiment")
    return reference_suite(
        candidate_name, {**plan, "pvm01_private_data_path": private_path},
        trial_sink=trial_sink, phase_sink=phase_sink, fit_sink=fit_sink, data_sink=data_sink,
    )
