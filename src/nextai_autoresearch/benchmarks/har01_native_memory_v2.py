"""Fresh target binding around the unchanged, hash-bound HAR scientific suite."""
from pathlib import Path
from types import FunctionType

from . import har01_native_memory_v1 as selected
from ..har01_task_v2 import load_unit, MANIFEST_PATH
from ..utils import load_json, project_root, sha256_file

BENCHMARK_VERSION = "har01_native_memory_v2"
_PARENT_SOURCES = {
    "src/nextai_autoresearch/har01_task.py": "52c905470c46f10c28bf79872ab15454316a3560f880eb058cf7576b8d94cd6d",
    "src/nextai_autoresearch/candidates/har01_core.py": "8e7e10b4779e40565cec140882df61d25517f92945d499d7df17d3f844179336",
    "src/nextai_autoresearch/benchmarks/har01_native_memory_v1.py": "afcf66879c05e5ac1ea650a07c07fd8d45ab5f531a1b191d29d8787c5383c8f8",
}


def _native_json(path):
    root = project_root()
    if Path(path) == root / "research/data_manifests/HAR01-ACQUISITION-V1.json":
        path = root / MANIFEST_PATH
    return load_json(path)


def _verify_parent_sources(root):
    for relative, digest in _PARENT_SOURCES.items():
        if sha256_file(root / relative) != digest:
            raise ValueError("Frozen HAR source changed")


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    if plan.get("benchmark") != BENCHMARK_VERSION:
        raise ValueError("Native replication cohort mismatch")
    root = project_root()
    _verify_parent_sources(root)
    namespace = dict(selected.run_suite.__globals__, BENCHMARK_VERSION=BENCHMARK_VERSION,
                     load_unit=load_unit, load_json=_native_json, project_root=project_root)
    delegated = FunctionType(selected.run_suite.__code__, namespace, selected.run_suite.__name__)
    try:
        return delegated(candidate_name, plan, trial_sink, phase_sink, fit_sink, data_sink)
    finally:
        _verify_parent_sources(root)
