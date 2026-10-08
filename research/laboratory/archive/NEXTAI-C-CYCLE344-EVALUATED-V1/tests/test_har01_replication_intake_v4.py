"""Public synthetic-only conformance for the separately frozen HAR replication."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest

from nextai_autoresearch import har01_task as original
from nextai_autoresearch import har01_task_v4 as replication
from nextai_autoresearch.utils import atomic_write_json, sha256_file


ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = tuple(range(6, 11)) + tuple(range(21, 26))
TASK_PATH = "research/plans/HAR01-REPLICATION-TASK-V3.json"
STUDY_PATH = "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json"
MANIFEST_PATH = "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V3.json"
DATASET_PATH = "research/data/har01_replication_v3/replication.npz"
PUBLISHER_PATH = "research/data/har01_native_v1/publisher.zip"


def intake():
    path = ROOT / "scripts/acquire_har01_replication_v3.py"
    spec = importlib.util.spec_from_file_location("har01_replication_intake", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def native_fixture(tmp_path):
    """Every coordinate and archive byte is generated here, never from native data."""
    task = tmp_path / TASK_PATH
    task.parent.mkdir(parents=True)
    task.write_bytes((ROOT / TASK_PATH).read_bytes())
    study = tmp_path / STUDY_PATH
    study.write_bytes((ROOT / STUDY_PATH).read_bytes())
    publisher = tmp_path / PUBLISHER_PATH
    publisher.parent.mkdir(parents=True)
    publisher.write_bytes(b"public synthetic publisher fixture")
    arrays = {}
    for subject in SUBJECTS:
        count = 260 if subject < 11 else 160
        rng = np.random.default_rng(subject)
        arrays[f"subject_{subject}"] = rng.normal(size=(count, 6, 128)).astype(np.float32)
        arrays[f"rows_{subject}"] = np.column_stack((np.full(count, subject % 2, dtype=np.int64),
                                                     np.arange(count, dtype=np.int64)))
    dataset = tmp_path / DATASET_PATH
    dataset.parent.mkdir(parents=True)
    np.savez_compressed(dataset, **arrays)
    manifest = {"complete": True, "task_contract_sha256": sha256_file(task),
                "study_sha256": sha256_file(study),
                "converted_subjects": list(SUBJECTS), "no_unselected_subject_signal_arrays": True,
                "dataset_path": DATASET_PATH, "dataset_sha256": sha256_file(dataset),
                "publisher_sha256": sha256_file(publisher),
                "converted_subject_hashes": {str(s): original.arrays_hash(arrays[f"subject_{s}"],
                                                                           arrays[f"rows_{s}"])
                                             for s in SUBJECTS}}
    atomic_write_json(tmp_path / MANIFEST_PATH, manifest)
    return tmp_path, arrays, manifest


def rewrite_payload(root, arrays, manifest):
    np.savez_compressed(root / DATASET_PATH, **arrays)
    manifest["dataset_sha256"] = sha256_file(root / DATASET_PATH)
    manifest["converted_subject_hashes"] = {
        str(s): original.arrays_hash(arrays[f"subject_{s}"], arrays[f"rows_{s}"])
        for s in SUBJECTS}
    atomic_write_json(root / MANIFEST_PATH, manifest)


def test_replication_reuses_exact_scientific_objects():
    for name in ("CHANNELS", "arrays_hash", "rng_for", "feature", "transform", "pairs", "Episode",
                 "episode", "prepared_calibration", "training_sets", "episode_hash"):
        assert getattr(replication, name) is getattr(original, name), name
    assert original.SCREEN_SUBJECTS == tuple(range(1, 6)) + tuple(range(16, 21))
    task = json.loads((ROOT / TASK_PATH).read_text(encoding="utf-8"))
    assert task["intake"]["parse_numeric_signals_only_for_screen_subjects"] == list(SUBJECTS)
    assert task["acquisition_manifest_path"] == MANIFEST_PATH
    assert task["dataset_path"] == DATASET_PATH


@pytest.mark.parametrize("index", range(5), ids=["p0", "p1", "p2", "p3", "p4"])
def test_five_fresh_pairs_use_exact_partitions_and_train_only_scaler(native_fixture, index):
    root, arrays, manifest = native_fixture
    unit = replication.load_unit(root, index)
    train, dev = index + 6, index + 21
    assert (unit["train_subject"], unit["dev_subject"]) == (train, dev)
    for name, selection in (("T-fit", slice(0, 128)), ("T-validation", slice(130, 178)),
                            ("T-calibration", slice(180, 260))):
        np.testing.assert_array_equal(unit[name][0], arrays[f"subject_{train}"][selection])
        np.testing.assert_array_equal(unit[name][1], arrays[f"rows_{train}"][selection])
    np.testing.assert_array_equal(unit["D"][0], arrays[f"subject_{dev}"][::2])
    np.testing.assert_array_equal(unit["D"][1], arrays[f"rows_{dev}"][::2])
    write_features = np.stack([original.feature(row, "write") for row in arrays[f"subject_{train}"][:128]])
    np.testing.assert_array_equal(unit["mean"], write_features.mean(axis=0).astype(np.float32))
    np.testing.assert_array_equal(unit["scale"], np.maximum(write_features.std(axis=0), 1e-6).astype(np.float32))
    assert unit["unique_counts"] == {"T-fit": 128, "T-validation": 48, "T-calibration": 80, "D": 80}
    assert unit["dataset_sha256"] == manifest["dataset_sha256"]
    assert unit["intake_sha256"] == sha256_file(root / MANIFEST_PATH)


@pytest.mark.parametrize("index", [-1, 5, 10], ids=["neg", "next", "future"])
def test_pair_index_rejected_before_any_io(tmp_path, monkeypatch, index):
    monkeypatch.setattr(replication, "load_json", lambda *_: pytest.fail("Manifest read for forbidden pair"))
    with pytest.raises(ValueError):
        replication.load_unit(tmp_path, index)


@pytest.mark.parametrize("change", ["incomplete", "contract", "study", "subjects", "scope", "dataset", "publisher", "subject"],
                         ids=["done", "task", "study", "ids", "scope", "data", "pub", "row"])
def test_hash_and_scope_binding_fail_closed(native_fixture, change):
    root, _, manifest = native_fixture
    altered = copy.deepcopy(manifest)
    if change == "incomplete":
        altered["complete"] = False
    elif change == "contract":
        altered["task_contract_sha256"] = "0" * 64
    elif change == "study":
        altered["study_sha256"] = "0" * 64
    elif change == "subjects":
        altered["converted_subjects"][-1] = 26
    elif change == "scope":
        altered["no_unselected_subject_signal_arrays"] = False
    elif change == "dataset":
        altered["dataset_sha256"] = "0" * 64
    elif change == "publisher":
        altered["publisher_sha256"] = "0" * 64
    else:
        altered["converted_subject_hashes"]["6"] = "0" * 64
    atomic_write_json(root / MANIFEST_PATH, altered)
    with pytest.raises(ValueError):
        replication.load_unit(root, 0)


def test_payload_path_cannot_escape_repository(native_fixture):
    root, _, manifest = native_fixture
    manifest["dataset_path"] = "../outside.npz"
    atomic_write_json(root / MANIFEST_PATH, manifest)
    with pytest.raises(ValueError):
        replication.load_unit(root, 0)


@pytest.mark.parametrize("subject", [1, 11, 26], ids=["old", "trainfinal", "devfinal"])
def test_extra_old_or_future_npz_member_rejected_even_with_valid_file_hash(native_fixture, subject):
    root, arrays, manifest = native_fixture
    arrays[f"subject_{subject}"] = np.zeros((1, 6, 128), dtype=np.float32)
    arrays[f"rows_{subject}"] = np.zeros((1, 2), dtype=np.int64)
    rewrite_payload(root, arrays, manifest)
    with pytest.raises(ValueError):
        replication.load_unit(root, 0)


@pytest.mark.parametrize("subject,count", [(6, 259), (21, 158)], ids=["trainshort", "devshort"])
def test_insufficient_fixed_windows_are_not_replaced(native_fixture, subject, count):
    root, arrays, manifest = native_fixture
    arrays[f"subject_{subject}"] = arrays[f"subject_{subject}"][:count]
    arrays[f"rows_{subject}"] = arrays[f"rows_{subject}"][:count]
    rewrite_payload(root, arrays, manifest)
    with pytest.raises(ValueError):
        replication.load_unit(root, 0)


def synthetic_intake():
    return {"channels": list(original.CHANNELS), "expected_samples_per_window": 128,
            "parse_numeric_signals_only_for_screen_subjects": list(SUBJECTS),
            "all_subject_ids_must_equal": list(range(1, 31)), "expected_total_windows": 30,
            "train_subject_minimum_raw_windows": 1, "dev_subject_minimum_nonoverlapping_windows": 1}


def synthetic_archive(problem=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for split, ids in (("train", list(range(1, 16))), ("test", list(range(16, 31)))):
            base = f"UCI HAR Dataset/{split}/"
            archive.writestr(base + f"subject_{split}.txt", "\n".join(map(str, ids)))
            for channel, label in enumerate(original.CHANNELS):
                lines = []
                for subject in ids:
                    if subject in SUBJECTS:
                        values = np.arange(128, dtype=np.float32) + subject + channel * 1000
                        line = " ".join(map(str, values))
                    else:
                        line = "UNSELECTED_PAYLOAD_IS_NOT_NUMERIC"
                    if subject == 6 and channel == 0 and problem in {"malformed", "nonfinite"}:
                        line = "1 2" if problem == "malformed" else " ".join(["nan"] * 128)
                    lines.append(line)
                if split == "train" and channel == 0 and problem == "short":
                    lines.pop()
                if split == "train" and channel == 0 and problem == "extra":
                    lines.append("EXTRA_ROW")
                archive.writestr(base + f"Inertial Signals/{label}_{split}.txt", "\n".join(lines) + "\n")
        archive.writestr("UCI HAR Dataset/train/y_train.txt", "ACTIVITY_LABELS_MUST_REMAIN_CLOSED")
        archive.writestr("UCI HAR Dataset/test/y_test.txt", "ACTIVITY_LABELS_MUST_REMAIN_CLOSED")
    stream.seek(0)
    return zipfile.ZipFile(stream)


def test_selected_zip_rows_only_are_converted_and_labels_stay_closed(monkeypatch):
    module = intake()
    original_conversion = np.fromstring
    converted = []

    def checked_conversion(value, *args, **kwargs):
        assert "UNSELECTED" not in value
        converted.append(value)
        return original_conversion(value, *args, **kwargs)

    monkeypatch.setattr(np, "fromstring", checked_conversion)
    receipt = {}
    with synthetic_archive() as archive:
        original_read, original_open = archive.read, archive.open

        def checked_read(name, *args, **kwargs):
            assert str(name).rsplit("/", 1)[-1] not in ("y_train.txt", "y_test.txt")
            return original_read(name, *args, **kwargs)

        def checked_open(name, *args, **kwargs):
            assert str(name).rsplit("/", 1)[-1] not in ("y_train.txt", "y_test.txt")
            return original_open(name, *args, **kwargs)

        monkeypatch.setattr(archive, "read", checked_read)
        monkeypatch.setattr(archive, "open", checked_open)
        arrays, hashes = module.collect_selected_signals(archive, synthetic_intake(), receipt)
    assert set(arrays) == {f"{prefix}_{s}" for s in SUBJECTS for prefix in ("subject", "rows")}
    assert len(converted) == receipt["numeric_signal_rows_converted"] == 60
    assert receipt["unselected_signal_rows_skipped_without_numeric_conversion"] == 120
    assert receipt["converted_subjects"] == list(SUBJECTS)
    assert receipt["publisher_partition_counts"] == {"train": 15, "test": 15}
    for subject in SUBJECTS:
        expected = np.stack([np.arange(128, dtype=np.float32) + subject + channel * 1000
                             for channel in range(6)])[None]
        np.testing.assert_array_equal(arrays[f"subject_{subject}"], expected)
        np.testing.assert_array_equal(arrays[f"rows_{subject}"],
                                      [[0, subject - 1]] if subject < 16 else [[1, subject - 16]])
        assert hashes[str(subject)] == original.arrays_hash(expected, arrays[f"rows_{subject}"])


@pytest.mark.parametrize("problem", ["malformed", "nonfinite", "short", "extra"],
                         ids=["shape", "nan", "short", "extra"])
def test_selected_zip_grammar_and_completeness_fail_without_filtering(problem):
    receipt = {}
    with synthetic_archive(problem) as archive, pytest.raises(ValueError):
        intake().collect_selected_signals(archive, synthetic_intake(), receipt)
    assert "numeric_signal_rows_converted" in receipt
    assert "unselected_signal_rows_skipped_without_numeric_conversion" in receipt


@pytest.mark.parametrize("change", ["channels", "subjects", "width"], ids=["channels", "scope", "width"])
def test_zip_intake_bindings_rejected_before_selected_numeric_conversion(monkeypatch, change):
    rules = synthetic_intake()
    if change == "channels":
        rules["channels"][-1] = "total_acc_z"
    elif change == "subjects":
        rules["parse_numeric_signals_only_for_screen_subjects"][-1] = 26
    else:
        rules["expected_samples_per_window"] = 127
    monkeypatch.setattr(np, "fromstring", lambda *_args, **_kwargs: pytest.fail("Numeric conversion before binding"))
    with synthetic_archive() as archive, pytest.raises(ValueError):
        intake().collect_selected_signals(archive, rules, {})


def test_benchmark_manifest_dispatch_preserves_original_module(tmp_path, monkeypatch):
    from nextai_autoresearch.benchmarks import har01_native_memory_v1 as old_benchmark
    from nextai_autoresearch.benchmarks import har01_native_memory_v4 as new_benchmark

    old_path = tmp_path / "research/data_manifests/HAR01-ACQUISITION-V1.json"
    new_path = tmp_path / MANIFEST_PATH
    atomic_write_json(old_path, {"fixture": "original"})
    atomic_write_json(new_path, {"fixture": "replication"})
    monkeypatch.setattr(new_benchmark, "project_root", lambda: tmp_path)
    assert new_benchmark._native_json(old_path) == {"fixture": "replication"}
    assert old_benchmark.load_json(old_path) == {"fixture": "original"}
    assert new_benchmark.selected is old_benchmark
    assert new_benchmark.load_unit is replication.load_unit
    for name in ("source_state", "copy_service_state", "measure", "scores"):
        assert old_benchmark.run_suite.__globals__[name] is getattr(new_benchmark.selected, name), name
    assert old_benchmark.BENCHMARK_VERSION == "har01_native_memory_v1"
    assert new_benchmark.BENCHMARK_VERSION == "har01_native_memory_v4"
