"""Single bounded licensed acquisition; convert only the preregistered screen subjects."""
import io
import json
from pathlib import Path
import shutil
import time
import urllib.request
import zipfile

import numpy as np

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now
from nextai_autoresearch.pvm01_task import arrays_hash


def data_archive(path, rules):
    archive = zipfile.ZipFile(path)
    if sum(p.file_size for p in archive.infolist()) > rules["maximum_expanded_bytes"]:
        archive.close()
        raise ValueError("Archive exceeds preregistered expanded bound")
    if any(p.filename.endswith("/train/subject_train.txt") for p in archive.infolist()):
        return archive, False
    nested = [p for p in archive.infolist() if p.filename.endswith("UCI HAR Dataset.zip")]
    if len(nested) != 1 or nested[0].file_size > rules["maximum_download_bytes"]:
        archive.close()
        raise ValueError("Expected one bounded native HAR archive")
    payload = archive.read(nested[0])
    archive.close()
    inner = zipfile.ZipFile(io.BytesIO(payload))
    if sum(p.file_size for p in inner.infolist()) > rules["maximum_expanded_bytes"]:
        inner.close()
        raise ValueError("Expanded native archive exceeds cap")
    return inner, True


def main():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "research/plans/HAR01-NATIVE-TASK-CONTRACT-V1.json").read_text(encoding="utf-8"))
    rules, intake = contract["download"], contract["intake"]
    receipt_path = root / "research/data_manifests/HAR01-ACQUISITION-V1.json"
    assert not receipt_path.exists(), "Acquisition already consumed; no retry"
    assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
    before = shutil.disk_usage(root).free
    if before - rules["maximum_all_local_copies_and_derived_footprint_bytes"] < rules["free_space_floor_bytes"]:
        raise RuntimeError(f"Disk blocker: {before} bytes free; bounded footprint exceeds floor")
    directory = root / "research/data/har01_native_v1"
    directory.mkdir(parents=True, exist_ok=True)
    archive_path, partial = directory / "publisher.zip", directory / "publisher.zip.partial"
    assert not archive_path.exists() and not partial.exists(), "Existing acquisition bytes; no retry"
    start = time.perf_counter()
    receipt = {"created_at": utc_now(), "task_contract_sha256": sha256_file(root / "research/plans/HAR01-NATIVE-TASK-CONTRACT-V1.json"),
               "url": rules["url"], "license": contract["license"], "license_url": contract["license_url"],
               "attribution": contract["source_attribution"], "free_space_before_bytes": before,
               "footprint_bound_bytes": rules["maximum_all_local_copies_and_derived_footprint_bytes"],
               "new_registration_or_model_fit": False, "no_download_retry": True}
    try:
        request = urllib.request.Request(rules["url"], headers={"User-Agent": "NEXTAI licensed local research"})
        count = 0
        with urllib.request.urlopen(request, timeout=45) as response, partial.open("xb") as output:
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > rules["maximum_download_bytes"]:
                raise ValueError("Declared archive exceeds download cap")
            receipt["resolved_url"] = response.url
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > rules["maximum_download_bytes"]:
                    raise ValueError("Downloaded archive exceeds bound")
                output.write(chunk)
        partial.rename(archive_path)
        receipt.update(download_bytes=count, publisher_sha256=sha256_file(archive_path),
                       download_seconds=time.perf_counter() - start)
        archive, nested = data_archive(archive_path, rules)
        subjects = set(intake["parse_numeric_signals_only_for_screen_subjects"])
        signals, rows, all_counts = {s: [] for s in subjects}, {s: [] for s in subjects}, {}
        numeric_rows, skipped_rows, partitions = 0, 0, {}
        with archive:
            names = archive.namelist()
            paths = [n for n in names if n.endswith("/train/subject_train.txt")]
            assert len(paths) == 1
            base = paths[0].removesuffix("train/subject_train.txt")
            for split_code, split in enumerate(("train", "test")):
                ids = [int(x) for x in archive.read(f"{base}{split}/subject_{split}.txt").split()]
                partitions[split] = len(ids)
                for subject in ids:
                    all_counts[subject] = all_counts.get(subject, 0) + 1
                selected_indices = [i for i, s in enumerate(ids) if s in subjects]
                block = np.empty((len(selected_indices), 6, 128), dtype=np.float32)
                for channel, label in enumerate(intake["channels"]):
                    index = 0
                    with archive.open(f"{base}{split}/Inertial Signals/{label}_{split}.txt") as stream:
                        for row, line in enumerate(stream):
                            if row >= len(ids):
                                raise ValueError("Signal/subject row count mismatch")
                            if ids[row] in subjects:
                                value = np.fromstring(line.decode("ascii"), sep=" ", dtype=np.float32)
                                if value.shape != (128,) or not np.isfinite(value).all():
                                    raise ValueError("Nonfinite/malformed native window")
                                block[index, channel] = value
                                index += 1
                                numeric_rows += 1
                            else:
                                skipped_rows += 1
                    if row + 1 != len(ids) or index != len(selected_indices):
                        raise ValueError("Signal/subject completeness mismatch")
                for selected_row, original in enumerate(selected_indices):
                    signals[ids[original]].append(block[selected_row].copy())
                    rows[ids[original]].append((split_code, original))
            assert set(all_counts) == set(intake["all_subject_ids_must_equal"])
            assert sum(all_counts.values()) == intake["expected_total_windows"]
            arrays, hashes = {}, {}
            for subject in sorted(subjects):
                values = np.stack(signals[subject])
                source_rows = np.array(rows[subject], dtype=np.int64)
                if len(set(source_rows[:, 0])) != 1:
                    raise ValueError("Publisher subject straddles split")
                if subject <= 5 and len(values) < intake["train_subject_minimum_raw_windows"]:
                    raise ValueError(f"Subject {subject} lacks preregistered training windows")
                if subject >= 16 and len(values[::2]) < intake["dev_subject_minimum_nonoverlapping_windows"]:
                    raise ValueError(f"Subject {subject} lacks native nonoverlapping evaluation windows")
                arrays[f"subject_{subject}"] = values
                arrays[f"rows_{subject}"] = source_rows
                hashes[str(subject)] = arrays_hash(values, source_rows)
            dataset = directory / "screen.npz"
            with dataset.open("xb") as output:
                np.savez_compressed(output, **arrays)
            readmes = [n for n in names if n.endswith("README.txt") or n.endswith("UCI HAR Dataset.names")]
            for index, name in enumerate(readmes):
                payload = archive.read(name)
                assert len(payload) <= 65536
                (directory / f"publisher-document-{index}.txt").write_bytes(payload)
            receipt.update(nested_archive=nested, publisher_partition_counts=partitions,
                           subject_counts=all_counts, converted_subjects=sorted(subjects),
                           converted_subject_hashes=hashes, numeric_signal_rows_converted=numeric_rows,
                           unselected_signal_rows_skipped_without_numeric_conversion=skipped_rows,
                           no_unselected_subject_signal_arrays=True, no_activity_labels_read=True,
                           dataset_path=dataset.relative_to(root).as_posix(), dataset_sha256=sha256_file(dataset),
                           dataset_bytes=dataset.stat().st_size, complete=True)
    except BaseException as exc:
        receipt.update(complete=False, error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt.update(full_intake_wall_seconds=time.perf_counter() - start,
                       free_space_after_bytes=shutil.disk_usage(root).free)
        atomic_write_json(receipt_path, receipt)
        print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
