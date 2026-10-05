"""Frozen fresh-final role; unchanged service law with charged source-state copies."""
import importlib

from . import paired_view_mutable_memory_v10 as selected
from .paired_view_mutable_memory_v3 import bound_private_path
from ..pvm01_fitted_state import ARMS, export_state
from ..utils import project_root

BENCHMARK_VERSION = "paired_view_mutable_memory_v11"


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    protocol = plan["research_program_protocol"]
    if (plan.get("benchmark") != BENCHMARK_VERSION
            or protocol.get("evaluation_data_role") != "frozen_fresh_final_v1"):
        raise ValueError("Frozen fresh-final cohort/role binding mismatch")
    if fit_sink is None:
        raise ValueError("Audited fitted-source journal is required")
    bound_private_path(plan)
    index, arm = protocol["roles"][candidate_name]["seed_index"], protocol["roles"][candidate_name]["arm"]
    adapted = dict(plan, benchmark=selected.BENCHMARK_VERSION)
    if arm not in ARMS:
        return selected.run_suite(candidate_name, adapted, trial_sink, phase_sink, fit_sink, data_sink)
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    original = module.Candidate
    instances = []

    def capture(*args, **kwargs):
        if instances:
            raise ValueError("A final worker may initialize its model only once")
        system = original(*args, **kwargs)
        instances.append(system)
        return system

    def preserve(record):
        if len(instances) != 1:
            raise ValueError("Missing unique fitted source system")
        directory = project_root() / "research" / "tmp" / plan["experiment_id"] / "fitted-source" / candidate_name
        descriptor = export_state(instances[0], directory, record, protocol, candidate_name, arm, index)
        fit_sink(dict(record, source_state_export=descriptor))

    module.Candidate = capture
    try:
        return selected.run_suite(candidate_name, adapted, trial_sink, phase_sink, preserve, data_sink)
    finally:
        module.Candidate = original
