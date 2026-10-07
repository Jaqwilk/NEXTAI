"""Five new, public synthetic checks; no prior conformance or native intake."""
import importlib.util
import io
from pathlib import Path
import runpy
import shutil
import sys
from types import ModuleType
import urllib.request
import zipfile

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/acquire_har01_replication.py"
SIBLING = ROOT / "scripts/acquire_har01.py"
CHANNELS = ("body_acc_x", "body_acc_y", "body_acc_z", "body_gyro_x", "body_gyro_y", "body_gyro_z")
SUBJECTS = tuple(range(6, 11)) + tuple(range(21, 26))


def _isolated_path(monkeypatch):
    forbidden = {ROOT.resolve(), SCRIPT.parent.resolve()}
    monkeypatch.setattr(sys, "path", [item for item in sys.path if Path(item or ".").resolve() not in forbidden])


def _closed_intake(monkeypatch):
    def closed(*_args, **_kwargs):
        pytest.fail("Import-only check crossed a native/intake boundary")

    for name in ("load", "fromstring", "savez_compressed"):
        monkeypatch.setattr(np, name, closed)
    monkeypatch.setattr(zipfile, "ZipFile", closed)
    monkeypatch.setattr(urllib.request, "urlopen", closed)
    monkeypatch.setattr(shutil, "disk_usage", closed)
    monkeypatch.setattr(Path, "read_text", closed)
    monkeypatch.setattr(Path, "read_bytes", closed)


def _load(name, monkeypatch):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def _exact_sibling(helper):
    assert callable(helper)
    assert Path(helper.__code__.co_filename).resolve() == SIBLING.resolve()


def test_package_relative_identity(monkeypatch):
    _isolated_path(monkeypatch)
    _closed_intake(monkeypatch)
    package_name = "_har01_conformance_package"
    package = ModuleType(package_name)
    package.__path__ = [str(SCRIPT.parent)]
    monkeypatch.setitem(sys.modules, package_name, package)
    sibling_name = package_name + ".acquire_har01"
    try:
        module = _load(package_name + ".acquire_har01_replication", monkeypatch)
        assert module.__package__ == package_name
        assert module.data_archive is sys.modules[sibling_name].data_archive
        _exact_sibling(module.data_archive)
        assert callable(module.main) and callable(module.collect_selected_signals)
    finally:
        sys.modules.pop(sibling_name, None)


def test_dynamic_without_paths_ignores_ambient_module(monkeypatch):
    _isolated_path(monkeypatch)
    _closed_intake(monkeypatch)
    ambient = ModuleType("acquire_har01")
    ambient.data_archive = object()
    monkeypatch.setitem(sys.modules, "acquire_har01", ambient)
    module = _load("_har01_conformance_dynamic", monkeypatch)
    assert not module.__package__
    assert module.data_archive is not ambient.data_archive
    _exact_sibling(module.data_archive)
    assert module.SCREEN_SUBJECTS == SUBJECTS and module.CHANNELS == CHANNELS


def test_direct_main_context_stops_before_main_body(monkeypatch):
    _isolated_path(monkeypatch)
    _closed_intake(monkeypatch)
    ambient = ModuleType("acquire_har01")
    ambient.data_archive = object()
    monkeypatch.setitem(sys.modules, "acquire_har01", ambient)
    saved = {}

    class MainBoundary(Exception):
        pass

    def stop_before_body(frame, event, _arg):
        if (event == "call" and frame.f_code.co_name == "main"
                and Path(frame.f_code.co_filename).resolve() == SCRIPT.resolve()):
            saved.update(frame.f_globals)
            raise MainBoundary
        return stop_before_body

    previous_trace = sys.gettrace()
    try:
        sys.settrace(stop_before_body)
        with pytest.raises(MainBoundary):
            runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.settrace(previous_trace)
    assert sys.gettrace() is previous_trace
    assert saved["__name__"] == "__main__" and not saved["__package__"]
    assert saved["data_archive"] is not ambient.data_archive
    _exact_sibling(saved["data_archive"])
    assert callable(saved["collect_selected_signals"])


def _synthetic_rules():
    return {"channels": list(CHANNELS), "expected_samples_per_window": 128,
            "parse_numeric_signals_only_for_screen_subjects": list(SUBJECTS),
            "all_subject_ids_must_equal": list(range(1, 31)), "expected_total_windows": 30,
            "train_subject_minimum_raw_windows": 1, "dev_subject_minimum_nonoverlapping_windows": 1}


def _synthetic_zip():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        for split, ids in (("train", range(1, 16)), ("test", range(16, 31))):
            base = f"Public HAR fixture/{split}/"
            archive.writestr(base + f"subject_{split}.txt", "\n".join(map(str, ids)))
            for channel, label in enumerate(CHANNELS):
                lines = []
                for subject in ids:
                    if subject in SUBJECTS:
                        values = np.arange(128, dtype=np.float32) + subject + channel * 1000
                        lines.append(" ".join(map(str, values)).encode("ascii") + b"\n")
                    else:
                        lines.append(b"\xff\xfeOPAQUE_EXCLUDED_ROW\n")
                archive.writestr(base + f"Inertial Signals/{label}_{split}.txt", b"".join(lines))
            archive.writestr(base + f"y_{split}.txt", b"ACTIVITY_LABELS_CLOSED")
    payload.seek(0)
    return zipfile.ZipFile(payload)


def test_synthetic_selected_only_60numeric_120opaque_no_labels(monkeypatch):
    module = _load("_har01_conformance_synthetic", monkeypatch)
    original_conversion = np.fromstring
    converted = []

    def conversion(value, *args, **kwargs):
        assert "OPAQUE" not in value
        converted.append(value)
        return original_conversion(value, *args, **kwargs)

    monkeypatch.setattr(np, "fromstring", conversion)
    receipt = {}
    with _synthetic_zip() as archive:
        original_read, original_open = archive.read, archive.open

        def read(name, *args, **kwargs):
            assert not str(name).endswith(("y_train.txt", "y_test.txt"))
            return original_read(name, *args, **kwargs)

        def open_member(name, *args, **kwargs):
            assert not str(name).endswith(("y_train.txt", "y_test.txt"))
            return original_open(name, *args, **kwargs)

        monkeypatch.setattr(archive, "read", read)
        monkeypatch.setattr(archive, "open", open_member)
        arrays, hashes = module.collect_selected_signals(archive, _synthetic_rules(), receipt)
    assert set(arrays) == {f"{prefix}_{s}" for s in SUBJECTS for prefix in ("subject", "rows")}
    assert len(converted) == receipt["numeric_signal_rows_converted"] == 60
    assert receipt["unselected_signal_rows_skipped_without_numeric_conversion"] == 120
    assert receipt["converted_subjects"] == list(SUBJECTS)
    assert receipt["publisher_partition_counts"] == {"train": 15, "test": 15}
    assert receipt["subject_counts"] == {subject: 1 for subject in range(1, 31)}
    assert set(hashes) == {str(subject) for subject in SUBJECTS}
    assert receipt["converted_subject_hashes"] == hashes
    for subject in SUBJECTS:
        expected = np.stack([np.arange(128, dtype=np.float32) + subject + channel * 1000
                             for channel in range(6)])[None]
        np.testing.assert_array_equal(arrays[f"subject_{subject}"], expected)
        expected_rows = np.asarray([[0, subject - 1]] if subject < 16 else [[1, subject - 16]], dtype=np.int64)
        np.testing.assert_array_equal(arrays[f"rows_{subject}"], expected_rows)
        assert hashes[str(subject)] == module.arrays_hash(expected, expected_rows)


def test_three_closed_scope_bindings_rejected_before_bytes(monkeypatch):
    module = _load("_har01_conformance_scope", monkeypatch)

    def closed(*_args, **_kwargs):
        pytest.fail("Closed-scope rejection accessed archive bytes or converted a numeric row")

    class ClosedArchive:
        namelist = read = open = closed

    monkeypatch.setattr(np, "fromstring", closed)
    for change in ("subject", "channel", "width"):
        rules = _synthetic_rules()
        if change == "subject":
            rules["parse_numeric_signals_only_for_screen_subjects"][-1] = 26
        elif change == "channel":
            rules["channels"][-1] = "total_acc_z"
        else:
            rules["expected_samples_per_window"] = 127
        receipt = {}
        with pytest.raises(ValueError, match="binding mismatch"):
            module.collect_selected_signals(ClosedArchive(), rules, receipt)
        assert receipt == {}
