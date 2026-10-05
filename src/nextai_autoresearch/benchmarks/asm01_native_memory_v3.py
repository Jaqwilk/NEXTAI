"""New intake identity; execute the unchanged V2 scientific suite in isolated globals."""
from types import FunctionType

from . import asm01_native_memory_v2 as selected
from ..asm01_task_v5 import load_unit
from ..utils import load_json, project_root

BENCHMARK_VERSION = 'asm01_native_memory_v3'


def _native_json(path):
    if path == project_root() / 'research/data_manifests/ASM01-ACQUISITION-V2.json':
        path = project_root() / 'research/data_manifests/ASM01-ACQUISITION-V3.json'
    return load_json(path)


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    if plan.get('benchmark') != BENCHMARK_VERSION:
        raise ValueError('Verified native serializer cohort mismatch')
    namespace = dict(selected.run_suite.__globals__, BENCHMARK_VERSION=BENCHMARK_VERSION,
                     load_unit=load_unit, project_root=project_root, load_json=_native_json)
    delegated = FunctionType(selected.run_suite.__code__, namespace, selected.run_suite.__name__)
    return delegated(candidate_name, plan, trial_sink, phase_sink, fit_sink, data_sink)
