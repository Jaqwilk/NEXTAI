"""Synthetic C loader/publisher provenance; no publisher/native content reads."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import nextai_autoresearch

from nextai_autoresearch import asm01_task as old_task
from nextai_autoresearch import asm01_task_v6 as task
from nextai_autoresearch import asm01_task_v2, asm01_task_v5
from nextai_autoresearch.benchmarks import asm01_native_memory_v2 as old_benchmark
from nextai_autoresearch.benchmarks import asm01_native_memory_v4 as benchmark
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file


ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("asm01_c_synthetic_publisher", ROOT / "scripts/acquire_asm01_c_v1.py")
intake = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(intake)
TASK_SHA = "66cb7521a72e3485c8738d0f46cfe64bad3d773755fcc15c5db23a4cde9afa85"
STUDY_SHA = "297357e54f271bebe8fdf8da0d6a31c6d2c7a3fea5251ad9f1008eb9b26b8c1d"
COUNTS = {"native_files_attempted": 1830, "native_files_converted": 1830,
          "validated_files": 1830, "old74_compared": 74,
          "previous1171_compared": 1171, "D_samples_opened": 915}
_DELEGATION = {}


def synthetic_method(candidate, plan, *sinks):
    # A module-level code object has no closure, just like the real old suite.
    # Its globals are supplied by the new wrapper's FunctionType delegation.
    _DELEGATION.update(loader=load_unit, version=BENCHMARK_VERSION,
                       manifest=load_json(project_root() / "research/data_manifests/ASM01-ACQUISITION-V2.json"))
    return ["synthetic delegation"]


@pytest.fixture
def synthetic_binding(tmp_path, monkeypatch):
    """Frozen task/study bytes, fake publisher and entirely independent arrays.

    Only the publisher hash reader is virtualized, because a synthetic archive
    cannot have the preregistered native archive's SHA. All task/study/source,
    dataset and writer hashes are computed from their actual fixture bytes.
    """
    for relative in (task.TASK_PATH, task.STUDY_PATH):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    atomic_write_json(tmp_path / task.SOURCE_BINDING_PATH,
                      {"fixture_only": True, "task_sha256": TASK_SHA, "study_sha256": STUDY_SHA})
    publisher = tmp_path / task.PUBLISHER_PATH
    publisher.parent.mkdir(parents=True, exist_ok=True)
    publisher.write_bytes(b"public synthetic publisher placeholder; no native data")
    native_hash = task.sha256_file
    def virtual_publisher_hash(path):
        if Path(path).resolve() == publisher.resolve():
            return task.PUBLISHER_SHA
        return native_hash(path)
    monkeypatch.setattr(task, "sha256_file", virtual_publisher_hash)
    arrays, hashes, raw_hashes, sample_hashes = {}, {}, {}, {}
    for writer_index, writer in enumerate(old_task.SCREEN_WRITERS):
        values = []
        for sample in range(1, 184):
            ordinal = writer_index * 183 + sample - 1
            base = ordinal if ordinal < 1171 else -(ordinal - 1170)
            values.append(np.asarray([(base + 10 * point, 100 + point * point)
                                      for point in range(8)], dtype=np.float32))
            uid = f"{writer}:{sample}"
            raw_hashes[uid] = hashlib.sha256(f"public synthetic payload {uid}".encode("ascii")).hexdigest()
            sample_hashes[uid] = old_task.arrays_hash(values[-1])
        points = np.concatenate(values)
        offsets = np.arange(184, dtype=np.int64) * 8
        rows = np.asarray([(sample, writer) for sample in range(1, 184)], dtype=np.int64)
        arrays.update({f"points_{writer}": points, f"offsets_{writer}": offsets, f"rows_{writer}": rows})
        hashes[str(writer)] = old_task.arrays_hash(points, offsets, rows)
    receipt = {"complete": True, "task_contract_sha256": TASK_SHA, "study_sha256": STUDY_SHA,
               "converted_writers": list(old_task.SCREEN_WRITERS), "converted_writer_hashes": hashes,
               "no_future_writer_coordinates_read": True, "publisher_sha256": task.PUBLISHER_SHA,
               "source_binding_sha256": sha256_file(tmp_path / task.SOURCE_BINDING_PATH),
               "attempted_sample_text_sha256": raw_hashes, "sample_array_sha256": sample_hashes,
               **COUNTS}
    return tmp_path, arrays, hashes, receipt


def write_bundle(root, arrays, receipt):
    dataset = root / task.DATASET_PATH
    dataset.parent.mkdir(parents=True, exist_ok=True)
    with dataset.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    receipt.update(dataset_path=task.DATASET_PATH, dataset_sha256=sha256_file(dataset))
    atomic_write_json(root / task.MANIFEST_PATH, receipt)


@pytest.fixture
def synthetic_bundle(synthetic_binding):
    root, arrays, hashes, receipt = synthetic_binding
    write_bundle(root, arrays, receipt)
    return root, arrays, hashes, receipt


def test_clone_origin_and_exact_new_frozen_task_study():
    assert ROOT.name == "NEXTAI-VALIDATION-20261002"
    assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(ROOT / "src")
    assert Path(task.__file__).resolve().is_relative_to(ROOT / "src")
    assert sha256_file(ROOT / task.TASK_PATH) == task.TASK_SHA == TASK_SHA
    assert sha256_file(ROOT / task.STUDY_PATH) == task.STUDY_SHA == STUDY_SHA
    study = load_json(ROOT / task.STUDY_PATH)
    assert study["task_contract_sha256"] == TASK_SHA
    assert "seed_policy" in study["matrix"] and "seeds" not in study["matrix"]
    assert len(study["candidates"]) == 45 and study["matrix"]["seed_policy"]["count"] == 5


@pytest.mark.parametrize("index", range(5), ids=["pair0", "pair1", "pair2", "pair3", "pair4"])
def test_complete_loader_all_five_pairs_and_disjoint_T_partitions(synthetic_bundle, index):
    root, _, _, _ = synthetic_bundle
    before = {name: sha256_file(root / name) for name in (task.MANIFEST_PATH, task.DATASET_PATH)}
    unit = task.load_unit(root, index, "a" * 64)
    assert (unit["train_writer"], unit["dev_writer"]) == (index + 1, index + 16)
    parts = [set(unit[name][1][:, 0]) for name in ("T-fit", "T-validation", "T-calibration")]
    assert [len(value) for value in parts] == [64, 24, 95]
    assert not (parts[0] & parts[1] or parts[0] & parts[2] or parts[1] & parts[2])
    assert set.union(*parts) == set(range(1, 184))
    assert len(unit["D"][0]) == 183 and np.all(unit["D"][1][:, 1] == index + 16)
    assert unit["unique_counts"] == {"T-fit": 64, "T-validation": 24, "T-calibration": 95, "D": 183}
    assert unit["mean"].tobytes() == np.zeros(64, dtype=np.float32).tobytes()
    assert unit["scale"].tobytes() == np.ones(64, dtype=np.float32).tobytes()
    assert {name: sha256_file(root / name) for name in before} == before


@pytest.mark.parametrize("index", [-1, 5, True, 1.0], ids=["negative", "future", "bool", "float"])
def test_loader_refuses_noncanonical_pair_before_manifest_read(tmp_path, index):
    with pytest.raises(ValueError):
        task.load_unit(tmp_path, index, "a" * 64)


@pytest.mark.parametrize("field", ["complete", "task_contract_sha256", "study_sha256",
                                   "converted_writers", "converted_writer_hashes",
                                   "no_future_writer_coordinates_read", "publisher_sha256",
                                   "source_binding_sha256", "dataset_sha256", "dataset_path", *COUNTS],
                         ids=["incomplete", "task", "study", "writers", "hash-keys", "future-flag",
                              "publisher", "source", "payload", "path", "attempted", "converted",
                              "validated", "old74", "previous1171", "D915"])
def test_manifest_scope_integrity_and_complete_counters_are_mandatory(synthetic_bundle, field):
    root, _, _, receipt = synthetic_bundle
    if field in COUNTS:
        receipt[field] -= 1
    elif field in ("complete", "no_future_writer_coordinates_read"):
        receipt[field] = False
    elif field == "converted_writers":
        receipt[field][-1] = 21
    elif field == "converted_writer_hashes":
        del receipt[field]["20"]
    elif field == "dataset_path":
        receipt[field] = "research/data/asm01_native_v1/screen-v3.npz"
    else:
        receipt[field] = "0" * 64
    atomic_write_json(root / task.MANIFEST_PATH, receipt)
    with pytest.raises(ValueError):
        task.load_unit(root, 0, "a" * 64)


@pytest.mark.parametrize("relative", [task.TASK_PATH, task.STUDY_PATH, task.SOURCE_BINDING_PATH],
                         ids=["task-bytes", "study-bytes", "source-bytes"])
def test_bound_input_bytes_changed_are_rejected(synthetic_bundle, relative):
    root, _, _, _ = synthetic_bundle
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        task.load_unit(root, 0, "a" * 64)


def test_changed_publisher_hash_is_rejected_without_native_archive(synthetic_bundle, monkeypatch):
    root, _, _, _ = synthetic_bundle
    original = task.sha256_file
    publisher = root / task.PUBLISHER_PATH
    monkeypatch.setattr(task, "sha256_file", lambda path: "0" * 64 if Path(path) == publisher else original(path))
    with pytest.raises(ValueError, match="publisher"):
        task.load_unit(root, 0, "a" * 64)


def refresh_hashes(arrays, receipt):
    receipt["converted_writer_hashes"] = {
        str(writer): old_task.arrays_hash(*(arrays[f"{prefix}_{writer}"] for prefix in ("points", "offsets", "rows")))
        for writer in old_task.SCREEN_WRITERS}


@pytest.mark.parametrize("alter", ["keys", "point-dtype", "offset-dtype", "row-dtype", "offset-start",
                                   "offset-end", "short-path", "sample-row", "future-row", "nan",
                                   "fraction", "x-bound", "y-bound", "duplicate"],
                         ids=["keys", "point-dtype", "offset-dtype", "row-dtype", "offset-start",
                              "offset-end", "short-path", "sample-row", "future-row", "nan",
                              "fraction", "x-bound", "y-bound", "duplicate"])
def test_every_writer_structure_is_checked_even_with_recomputed_hashes(synthetic_bundle, alter):
    root, arrays, _, receipt = synthetic_bundle
    # Writer20 is unselected by pair0. Integrity must cover the complete intake.
    if alter == "keys":
        arrays["points_21"] = arrays["points_20"].copy()
    elif alter == "point-dtype":
        arrays["points_20"] = arrays["points_20"].astype(np.float64)
    elif alter == "offset-dtype":
        arrays["offsets_20"] = arrays["offsets_20"].astype(np.int32)
    elif alter == "row-dtype":
        arrays["rows_20"] = arrays["rows_20"].astype(np.int32)
    elif alter == "offset-start":
        arrays["offsets_20"][0] = 1
    elif alter == "offset-end":
        arrays["offsets_20"][-1] -= 1
    elif alter == "short-path":
        arrays["offsets_20"][1] = 3
    elif alter == "sample-row":
        arrays["rows_20"][[0, 1]] = arrays["rows_20"][[1, 0]]
    elif alter == "future-row":
        arrays["rows_20"][0, 1] = 21
    elif alter == "nan":
        arrays["points_20"][0, 0] = np.nan
    elif alter == "fraction":
        arrays["points_20"][0, 0] += np.float32(.5)
    elif alter == "x-bound":
        arrays["points_20"][0, 0] = -4393
    elif alter == "y-bound":
        arrays["points_20"][0, 1] = 4869
    else:
        arrays["points_20"][:8] = arrays["points_1"][:8]
    refresh_hashes(arrays, receipt)
    write_bundle(root, arrays, receipt)
    with pytest.raises(ValueError):
        task.load_unit(root, 0, "a" * 64)


def test_legacy_manifest_cannot_replace_missing_C_binding(synthetic_bundle):
    root, _, _, receipt = synthetic_bundle
    for name in ("ASM01-ACQUISITION-V1.json", "ASM01-ACQUISITION-V2.json", "ASM01-ACQUISITION-V3.json"):
        atomic_write_json(root / "research/data_manifests" / name, receipt)
    (root / task.MANIFEST_PATH).unlink()
    with pytest.raises(FileNotFoundError):
        task.load_unit(root, 0, "a" * 64)


def test_wrapper_uses_old_method_code_and_new_intake_cost_binding(synthetic_bundle, monkeypatch):
    root, _, _, receipt = synthetic_bundle
    _DELEGATION.clear()
    assert synthetic_method.__code__.co_freevars == ()
    assert benchmark.selected.run_suite is old_benchmark.run_suite
    # Replace only the imported old suite function in this isolated fixture;
    # FunctionType should rebind its globals to the new loader/cost manifest.
    monkeypatch.setattr(old_benchmark, "run_suite", synthetic_method)
    monkeypatch.setattr(benchmark, "project_root", lambda: root)
    assert benchmark.run_suite("unused", {"benchmark": benchmark.BENCHMARK_VERSION}) == ["synthetic delegation"]
    assert _DELEGATION["loader"] is task.load_unit and _DELEGATION["version"] == "asm01_native_memory_v4"
    assert _DELEGATION["manifest"] == receipt
    assert old_benchmark.load_unit is asm01_task_v2.load_unit
    assert old_benchmark.load_json is load_json
    assert asm01_task_v5.transform is old_task.transform
    with pytest.raises(ValueError, match="cohort mismatch"):
        benchmark.run_suite("unused", {"benchmark": "asm01_native_memory_v3"})


def test_publisher_requires_complete_evidence_and_creates_exclusively(synthetic_binding):
    root, arrays, hashes, receipt = synthetic_binding
    intake.publish(root, arrays, hashes, receipt)
    manifest = load_json(root / task.MANIFEST_PATH)
    assert manifest["complete"] is True
    assert manifest["dataset_path"] == task.DATASET_PATH
    assert manifest["task_contract_sha256"] == TASK_SHA and manifest["study_sha256"] == STUDY_SHA
    assert {key: manifest[key] for key in COUNTS} == COUNTS
    assert manifest["dataset_sha256"] == sha256_file(root / task.DATASET_PATH)
    before = {name: (root / name).read_bytes() for name in (task.DATASET_PATH, task.MANIFEST_PATH)}
    with pytest.raises((ValueError, FileExistsError)):
        intake.publish(root, arrays, hashes, copy.deepcopy(receipt))
    assert {name: (root / name).read_bytes() for name in before} == before


@pytest.mark.parametrize("field", ["complete", *COUNTS],
                         ids=["incomplete", "attempted", "converted", "validated", "old74", "previous1171", "D915"])
def test_publisher_cannot_create_NPZ_from_partial_intake(synthetic_binding, field):
    root, arrays, hashes, receipt = synthetic_binding
    if field == "complete":
        receipt[field] = False
    else:
        receipt[field] -= 1
    with pytest.raises(ValueError):
        intake.publish(root, arrays, hashes, receipt)
    assert not (root / task.DATASET_PATH).exists()
    assert not (root / task.MANIFEST_PATH).exists()


@pytest.mark.parametrize("alter", ["raw-map", "array-map", "array-proof", "writer-hashes", "keys", "source"],
                         ids=["raw-map", "array-map", "array-proof", "writer-hashes", "keys", "source"])
def test_publisher_rejects_incomplete_or_foreign_proof_before_NPZ(synthetic_binding, alter):
    root, arrays, hashes, receipt = synthetic_binding
    if alter == "raw-map":
        del receipt["attempted_sample_text_sha256"]["20:183"]
    elif alter == "array-map":
        del receipt["sample_array_sha256"]["20:183"]
    elif alter == "array-proof":
        receipt["sample_array_sha256"]["20:183"] = "0" * 64
    elif alter == "writer-hashes":
        del hashes["20"]
    elif alter == "keys":
        arrays["points_21"] = arrays["points_20"].copy()
    else:
        receipt["source_binding_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        intake.publish(root, arrays, hashes, receipt)
    assert not (root / task.DATASET_PATH).exists()
    assert not (root / task.MANIFEST_PATH).exists()


@pytest.mark.parametrize("failure", ["serialize", "dataset-link", "manifest-link"],
                         ids=["serialize", "dataset-link", "manifest-link"])
def test_publication_failure_preserves_partial_and_no_complete_manifest(synthetic_binding, monkeypatch, failure):
    root, arrays, hashes, receipt = synthetic_binding
    dataset = root / task.DATASET_PATH
    partial = dataset.with_name(dataset.name + ".partial")
    manifest = root / task.MANIFEST_PATH
    if failure == "serialize":
        def failed_save(output, **values):
            output.write(b"public synthetic serialization partial")
            raise RuntimeError("synthetic serialization failure")
        monkeypatch.setattr(intake.np, "savez_compressed", failed_save)
        expected_error = RuntimeError
    else:
        original_link = intake.os.link
        def failed_link(source, destination, *args, **kwargs):
            target = dataset if failure == "dataset-link" else manifest
            if Path(destination) == target:
                raise OSError("synthetic atomic publication failure")
            return original_link(source, destination, *args, **kwargs)
        monkeypatch.setattr(intake.os, "link", failed_link)
        expected_error = OSError
    with pytest.raises(expected_error):
        intake.publish(root, arrays, hashes, receipt)
    assert not manifest.exists(), "Failed publication cannot serve a complete manifest"
    if failure == "manifest-link":
        assert dataset.is_file()
        assert manifest.with_name(manifest.name + ".publication.partial").is_file()
    else:
        assert not dataset.exists() and partial.is_file() and partial.stat().st_size > 0


@pytest.mark.parametrize("alter", ["valid", "native-flag", "conformance-flag", "task", "study",
                                   "preserved-entry", "new-module", "old-hash", "file-bytes"],
                         ids=["valid", "native-flag", "conformance-flag", "task", "study",
                              "preserved-entry", "new-module", "old-hash", "file-bytes"])
def test_source_binding_metadata_precedes_any_native_reader(synthetic_binding, monkeypatch, alter):
    root, _, _, _ = synthetic_binding
    study = load_json(ROOT / task.STUDY_PATH)
    required = dict(study["source_hashes_preserved"])
    new_paths = ("src/nextai_autoresearch/asm01_task_v6.py",
                 "src/nextai_autoresearch/benchmarks/asm01_native_memory_v4.py",
                 "scripts/acquire_asm01_c_v1.py")
    files = dict(required)
    files.update({relative: sha256_file(ROOT / relative) for relative in new_paths})
    for relative in files:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    binding = {"study_sha256": STUDY_SHA, "task_contract_sha256": TASK_SHA,
               "native_intake_authorized": True, "synthetic_conformance_complete": True, "files": files}
    first_old = next(iter(required))
    if alter == "native-flag":
        del binding["native_intake_authorized"]
    elif alter == "conformance-flag":
        binding["synthetic_conformance_complete"] = False
    elif alter == "task":
        binding["task_contract_sha256"] = "0" * 64
    elif alter == "study":
        binding["study_sha256"] = "0" * 64
    elif alter == "preserved-entry":
        del binding["files"][first_old]
    elif alter == "new-module":
        del binding["files"][new_paths[0]]
    elif alter == "old-hash":
        binding["files"][first_old] = "0" * 64
    elif alter == "file-bytes":
        target = root / new_paths[0]
        target.write_bytes(target.read_bytes() + b"\n")
    atomic_write_json(root / task.SOURCE_BINDING_PATH, binding)
    def forbidden_reader(*args, **kwargs):
        raise AssertionError("Source metadata verification must not open any native payload")
    monkeypatch.setattr(intake, "collect", forbidden_reader)
    if alter == "valid":
        assert intake._source_binding(root, study) == sha256_file(root / task.SOURCE_BINDING_PATH)
    else:
        with pytest.raises(ValueError, match="source_binding"):
            intake._source_binding(root, study)
    assert not (root / task.DATASET_PATH).exists()


def test_main_rejects_clone_name_spoof_before_any_payload_or_publication(tmp_path, monkeypatch):
    fake_clone = tmp_path / "NEXTAI-VALIDATION-20261002"
    fake_clone.mkdir()
    monkeypatch.chdir(fake_clone)
    with pytest.raises(ValueError, match="independent_clone_origin"):
        intake.main()
    assert not (fake_clone / task.MANIFEST_PATH).exists()
    assert not (fake_clone / task.DATASET_PATH).exists()
