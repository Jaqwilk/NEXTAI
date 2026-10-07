"""Fresh replication intake binding; unchanged physical features and episodes."""
import numpy as np

from .har01_task import (CHANNELS, Episode, arrays_hash, rng_for, feature, transform,
                         pairs, episode, prepared_calibration, training_sets, episode_hash)
from .utils import load_json, sha256_file

SCREEN_SUBJECTS = tuple(range(6, 11)) + tuple(range(21, 26))
MANIFEST_PATH = "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V3.json"
TASK_PATH = "research/plans/HAR01-REPLICATION-TASK-V3.json"
STUDY_PATH = "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json"


def load_unit(root, index):
    if index not in range(5):
        raise ValueError("Only preregistered five replication pairs are accessible")
    manifest_path = root / MANIFEST_PATH
    manifest = load_json(manifest_path)
    if (manifest.get("complete") is not True
            or manifest["task_contract_sha256"] != sha256_file(root / TASK_PATH)
            or manifest["study_sha256"] != sha256_file(root / STUDY_PATH)
            or manifest["converted_subjects"] != list(SCREEN_SUBJECTS)
            or manifest.get("no_unselected_subject_signal_arrays") is not True):
        raise ValueError("Native replication acquisition/scope binding mismatch")
    path = (root / manifest["dataset_path"]).resolve()
    if not path.is_relative_to(root.resolve()) or sha256_file(path) != manifest["dataset_sha256"]:
        raise ValueError("Native replication payload changed or outside repository")
    publisher = root / "research/data/har01_native_v1/publisher.zip"
    if sha256_file(publisher) != manifest["publisher_sha256"]:
        raise ValueError("Preserved publisher archive changed")
    with np.load(path, allow_pickle=False) as archive:
        expected = {f"{prefix}_{s}" for s in SCREEN_SUBJECTS for prefix in ("subject", "rows")}
        if set(archive.files) != expected:
            raise ValueError("Unexpected reserved subject in replication payload")
        values = []
        for subject in (index + 6, index + 21):
            signals, rows = archive[f"subject_{subject}"].copy(), archive[f"rows_{subject}"].copy()
            if arrays_hash(signals, rows) != manifest["converted_subject_hashes"][str(subject)]:
                raise ValueError("Native subject arrays changed")
            values.append((signals, rows))
    train, dev = values
    fit, validation, calibration = train[0][0:128], train[0][130:178], train[0][180:260]
    if (len(fit), len(validation), len(calibration)) != (128, 48, 80) or len(dev[0][::2]) < 80:
        raise ValueError("Preregistered finite-data intake not feasible")
    raw_write = np.stack([feature(row, "write") for row in fit])
    mean = raw_write.mean(axis=0).astype(np.float32)
    scale = np.maximum(raw_write.std(axis=0), 1e-6).astype(np.float32)
    return {"T-fit": (fit, train[1][0:128]), "T-validation": (validation, train[1][130:178]),
            "T-calibration": (calibration, train[1][180:260]), "D": (dev[0][::2], dev[1][::2]),
            "mean": mean, "scale": scale, "train_subject": index + 6, "dev_subject": index + 21,
            "intake_sha256": sha256_file(manifest_path), "dataset_sha256": manifest["dataset_sha256"],
            "publisher_sha256": manifest["publisher_sha256"],
            "unique_counts": {"T-fit": 128, "T-validation": 48, "T-calibration": 80, "D": len(dev[0][::2])}}
