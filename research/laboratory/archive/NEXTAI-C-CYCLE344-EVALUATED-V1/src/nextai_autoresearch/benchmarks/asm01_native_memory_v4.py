"""C signed-release intake binding; unchanged V2 scientific suite and methods."""
from types import FunctionType

from . import asm01_native_memory_v2 as selected
from ..asm01_task_v6 import load_unit, MANIFEST_PATH
from ..utils import load_json, project_root


BENCHMARK_VERSION = 'asm01_native_memory_v4'


def _native_json(path):
    if path == project_root() / 'research/data_manifests/ASM01-ACQUISITION-V2.json':
        path = project_root() / MANIFEST_PATH
    return load_json(path)


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    if plan.get('benchmark') != BENCHMARK_VERSION:
        raise ValueError('C signed-release native cohort mismatch')
    namespace = dict(selected.run_suite.__globals__, BENCHMARK_VERSION=BENCHMARK_VERSION,
                     load_unit=load_unit, project_root=project_root, load_json=_native_json)
    delegated = FunctionType(selected.run_suite.__code__, namespace, selected.run_suite.__name__)
    return delegated(candidate_name, plan, trial_sink, phase_sink, fit_sink, data_sink)
