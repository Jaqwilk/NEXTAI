"""One fresh, bounded replication intake from the preserved public HAR archive."""
import importlib.util
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

import numpy as np

if __package__:
    from .acquire_har01 import data_archive
else:
    _archive_spec = importlib.util.spec_from_file_location(
        "_har01_acquisition_sibling", Path(__file__).with_name("acquire_har01.py"))
    _archive_module = importlib.util.module_from_spec(_archive_spec)
    _archive_spec.loader.exec_module(_archive_module)
    data_archive = _archive_module.data_archive
from nextai_autoresearch.har01_task_v3 import CHANNELS, SCREEN_SUBJECTS, arrays_hash
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

STUDY = "research/plans/HAR01-INDEPENDENT-REPLICATION-V2.json"
STUDY_SHA = "c1ffee7b7856851fc4dc2792f3aa0e6e8502bb465d2244ba0997fa43966f39aa"
TASK = "research/plans/HAR01-REPLICATION-TASK-V2.json"
MANIFEST = "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V2.json"
PARENT_INTAKE_SHA = "331460a24c26d90aece9d54922bc02c0a80a82b1d9d2a73cde59542fa28ee105"
PUBLISHER_SHA = "c00b803081a5c797cd5e4b83700a9810b38d53d9d84e01917e090e1fdbc81031"
CLOCK_PATH = "research/plans/HAR01-REPLICATION-CONTINUATION-CLOCK-V2.json"
CLOCK_SHA = "333fa4ad5d3b408d60d8593c0916560388b4008ddd1b9e0e23b701ad0c5e2e8a"


def collect_selected_signals(archive, intake, receipt):
    """Convert only the fixed fresh subjects; excluded signal lines stay opaque."""
    subjects = tuple(intake["parse_numeric_signals_only_for_screen_subjects"])
    if (subjects != SCREEN_SUBJECTS or tuple(intake["channels"]) != CHANNELS
            or intake["expected_samples_per_window"] != 128):
        raise ValueError("Replication subject/channel/window binding mismatch")
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError("Duplicate publisher member")
    paths = [name for name in names if name.endswith("/train/subject_train.txt")]
    if len(paths) != 1:
        raise ValueError("Exactly one HAR subject root required")
    base = paths[0].removesuffix("train/subject_train.txt")
    signals, rows, all_counts = {s: [] for s in subjects}, {s: [] for s in subjects}, {}
    receipt.update(numeric_signal_rows_converted=0,
                   unselected_signal_rows_skipped_without_numeric_conversion=0,
                   publisher_partition_counts={}, subject_counts={}, converted_subjects=[])
    for split_code, split in enumerate(("train", "test")):
        ids = [int(value) for value in archive.read(f"{base}{split}/subject_{split}.txt").split()]
        receipt["publisher_partition_counts"][split] = len(ids)
        for subject in ids:
            all_counts[subject] = all_counts.get(subject, 0) + 1
        receipt["subject_counts"] = dict(all_counts)
        selected_indices = [index for index, subject in enumerate(ids) if subject in subjects]
        block = np.empty((len(selected_indices), 6, 128), dtype=np.float32)
        for channel, label in enumerate(CHANNELS):
            index, line_count = 0, 0
            receipt["current_partition"], receipt["current_channel"] = split, label
            with archive.open(f"{base}{split}/Inertial Signals/{label}_{split}.txt") as stream:
                for row, line in enumerate(stream):
                    line_count += 1
                    if row >= len(ids):
                        raise ValueError("Signal/subject row count mismatch")
                    if ids[row] in subjects:
                        receipt["current_subject"], receipt["current_publisher_row"] = ids[row], row
                        value = np.fromstring(line.decode("ascii"), sep=" ", dtype=np.float32)
                        if value.shape != (128,) or not np.isfinite(value).all():
                            raise ValueError("Nonfinite/malformed native window")
                        block[index, channel] = value
                        index += 1
                        receipt["numeric_signal_rows_converted"] += 1
                    else:
                        receipt["unselected_signal_rows_skipped_without_numeric_conversion"] += 1
            if line_count != len(ids) or index != len(selected_indices):
                raise ValueError("Signal/subject completeness mismatch")
        for selected_row, original in enumerate(selected_indices):
            signals[ids[original]].append(block[selected_row].copy())
            rows[ids[original]].append((split_code, original))
    if (set(all_counts) != set(intake["all_subject_ids_must_equal"])
            or sum(all_counts.values()) != intake["expected_total_windows"]):
        raise ValueError("Publisher subject/count completeness mismatch")
    arrays, hashes = {}, {}
    for subject in subjects:
        if not signals[subject]:
            raise ValueError("Missing fixed replication subject")
        values = np.stack(signals[subject])
        source_rows = np.asarray(rows[subject], dtype=np.int64)
        if len(set(source_rows[:, 0])) != 1:
            raise ValueError("Publisher subject straddles split")
        if subject <= 10 and len(values) < intake["train_subject_minimum_raw_windows"]:
            raise ValueError("Insufficient preregistered training windows")
        if subject >= 21 and len(values[::2]) < intake["dev_subject_minimum_nonoverlapping_windows"]:
            raise ValueError("Insufficient native evaluation windows")
        arrays[f"subject_{subject}"], arrays[f"rows_{subject}"] = values, source_rows
        hashes[str(subject)] = arrays_hash(values, source_rows)
        receipt["converted_subjects"].append(subject)
    receipt["converted_subject_hashes"] = hashes
    return arrays, hashes


def main():
    root = Path(__file__).resolve().parents[1]
    assert root.name == "NEXTAI-VALIDATION-20261002", "Independent clone intake only"
    study_path, task_path = root / STUDY, root / TASK
    assert sha256_file(study_path) == STUDY_SHA
    study, contract = json.loads(study_path.read_text()), json.loads(task_path.read_text())
    assert sha256_file(root / CLOCK_PATH) == CLOCK_SHA
    clock = json.loads((root / CLOCK_PATH).read_text(encoding="utf-8"))
    assert clock["study_sha256"] == STUDY_SHA
    prep_deadline = datetime.fromisoformat(clock["hard_preparation_deadline_at"].replace("Z", "+00:00"))
    assert datetime.now(timezone.utc) < prep_deadline, "Earlier hard preparation clock exhausted"
    receipt_path = root / MANIFEST
    assert not receipt_path.exists(), "Replication intake consumed; no retry"
    assert not any((root / path).exists() for path in ("STOP", "PAUSE", "research/run.lock"))
    assert sha256_file(task_path) == study["task_contract_sha256"]
    for name, digest in study["parent_bindings"].items():
        assert sha256_file(root / name) == digest, "Frozen parent binding changed"
    rules = contract["download"]
    before = shutil.disk_usage(root).free
    if before - rules["maximum_all_local_copies_and_derived_footprint_bytes"] < rules["free_space_floor_bytes"]:
        raise RuntimeError("Replication disk floor")
    parent_intake_path = root / "research/data_manifests/HAR01-ACQUISITION-V1.json"
    assert sha256_file(parent_intake_path) == PARENT_INTAKE_SHA
    prior = json.loads(parent_intake_path.read_text())
    publisher = root / contract["publisher_path"]
    receipt = dict(created_at=utc_now(), complete=False, study_sha256=sha256_file(study_path),
                   clock_path=CLOCK_PATH, clock_sha256=CLOCK_SHA,
                   task_contract_sha256=sha256_file(task_path),
                   preserved_parent_intake_sha256=sha256_file(root / "research/data_manifests/HAR01-ACQUISITION-V1.json"),
                   publisher_sha256=prior["publisher_sha256"], license=contract["license"],
                   license_url=contract["license_url"], attribution=contract["source_attribution"],
                   free_space_before_bytes=before,
                   footprint_bound_bytes=rules["maximum_all_local_copies_and_derived_footprint_bytes"],
                   no_download_retry=True, new_download_bytes=0, download_bytes=0,
                   download_seconds=0.0, prior_download_seconds=prior["download_seconds"],
                   no_new_download_or_extraction=True, new_registration_or_model_fit=False,
                   no_unselected_subject_signal_arrays=True, no_activity_labels_read=True)
    started = time.perf_counter()
    try:
        if (not prior["complete"] or prior["publisher_sha256"] != PUBLISHER_SHA
                or sha256_file(publisher) != PUBLISHER_SHA):
            raise ValueError("Preserved publisher archive changed")
        archive, nested = data_archive(publisher, rules)
        with archive:
            arrays, hashes = collect_selected_signals(archive, contract["intake"], receipt)
        dataset = root / contract["dataset_path"]
        dataset.parent.mkdir(parents=True, exist_ok=True)
        with dataset.open("xb") as output:
            np.savez_compressed(output, **arrays)
        for name, digest in study["parent_bindings"].items():
            if sha256_file(root / name) != digest:
                raise ValueError("Frozen parent binding changed")
        if sha256_file(publisher) != prior["publisher_sha256"]:
            raise ValueError("Preserved publisher archive changed")
        if datetime.now(timezone.utc) >= prep_deadline:
            raise RuntimeError("Earlier preparation deadline reached; preserve intake and stop")
        receipt.update(complete=True, nested_archive=nested, converted_subjects=list(SCREEN_SUBJECTS),
                       converted_subject_hashes=hashes, dataset_path=contract["dataset_path"],
                       dataset_sha256=sha256_file(dataset), dataset_bytes=dataset.stat().st_size,
                       unselected_subject_numeric_signal_reads=0)
    except BaseException as error:
        receipt.update(complete=False, error_type=type(error).__name__, error_category="replication_intake")
        raise RuntimeError("Replication intake failed; preserve receipt and stop") from None
    finally:
        receipt.update(full_intake_wall_seconds=time.perf_counter() - started,
                       free_space_after_bytes=shutil.disk_usage(root).free)
        atomic_write_json(receipt_path, receipt)
        print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
