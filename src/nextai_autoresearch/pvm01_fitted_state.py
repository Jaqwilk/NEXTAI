"""Bounded, non-pickle copies of already fitted source parameters; never fit."""
import hashlib
import json
import math
from pathlib import Path
import re
import time
import zipfile

import numpy as np
import torch

from .utils import atomic_write_json, sha256_file, sha256_json

VERSION = "PVM01-FITTED-SOURCE-STATE-V1"
ARMS = ("transport_pca", "transport_pca_untrained", "transport_pca_shuffled",
        "ridge_pca_scan", "dense_cached_cpu")
MAX_PARAMETERS = 2 * 1024 * 1024
MAX_METADATA = 64 * 1024


def parameter_arrays(system):
    arrays = {}
    for prefix in ("model", "decoder"):
        module = getattr(system, prefix, None)
        if module is not None:
            for key, value in module.state_dict().items():
                arrays[prefix + "." + key] = value.detach().cpu().numpy().copy()
    for key in ("weights", "projection"):
        value = getattr(system, key, None)
        if value is not None:
            arrays[key] = value.copy()
    if not arrays or sum(a.nbytes for a in arrays.values()) > MAX_PARAMETERS - 65536:
        raise ValueError("Fitted parameter payload missing or exceeds frozen bound")
    for key, array in arrays.items():
        if (not re.fullmatch(r"(?:model|decoder)\.[A-Za-z0-9_.]+|weights|projection", key)
                or array.dtype != np.float32 or not np.isfinite(array).all()):
            raise ValueError("Only whitelisted finite float32 fitted parameters are legal")
    return arrays


def _group_hash(arrays, prefix):
    values = [a for k, a in arrays.items() if k.startswith(prefix + ".")]
    if not values:
        return None
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.tobytes())
    return digest.hexdigest()


def validate_parameters(arrays, report):
    for prefix, field in (("model", "final_encoder_sha256"), ("decoder", "final_decoder_sha256")):
        if _group_hash(arrays, prefix) != report.get(field):
            raise ValueError("Fitted parameter hash differs from the frozen fit report")
    for key, field in (("weights", "fp32_ridge_weights_sha256"),
                       ("projection", "pca_projection_sha256")):
        if key in arrays and hashlib.sha256(arrays[key].tobytes()).hexdigest() != report.get(field):
            raise ValueError("Fitted classical/PCA hash differs from the fit report")


def export_state(system, directory, record, protocol, candidate, arm, seed_index):
    started = time.perf_counter()
    if arm not in ARMS or not re.fullmatch(r"pvm01_tc_[a-z_]+_s[0-4]", candidate):
        raise ValueError("Unselected fitted-source export")
    if candidate != f"pvm01_tc_{arm}_s{seed_index}" or not 0 <= seed_index < 5:
        raise ValueError("Fitted-source role mismatch")
    report = record["fit_report"]
    if record["candidate"] != candidate or sha256_json(report) != record["fit_report_sha256"]:
        raise ValueError("Fitted-source report provenance mismatch")
    if report["arm"] != arm or report["seed_index"] != seed_index or report["seed"] != system.seed:
        raise ValueError("Fitted-source unit mismatch")
    arrays = parameter_arrays(system)
    validate_parameters(arrays, report)
    threshold = float(system.threshold)
    if not math.isfinite(threshold) or threshold != report["calibration_choice"]["threshold"]:
        raise ValueError("Fitted threshold is not the T-calibrated choice")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    parameter_path = directory / "parameters.npz"
    with parameter_path.open("xb") as handle:
        np.savez(handle, **arrays)
    if parameter_path.stat().st_size > MAX_PARAMETERS:
        raise ValueError("Fitted parameter file exceeds frozen bound")
    metadata = {"version": VERSION, "candidate": candidate, "arm": arm,
        "seed": system.seed, "seed_index": seed_index, "threshold": threshold,
        "recipe": protocol["recipe"], "recipe_sha256": sha256_json(protocol["recipe"]),
        "study_path": protocol["study_path"], "study_sha256": protocol["study_sha256"],
        "fit_report_sha256": record["fit_report_sha256"],
        "parameters_sha256": sha256_file(parameter_path),
        "parameters_bytes": parameter_path.stat().st_size,
        "arrays": [{"key": key, "shape": list(a.shape), "dtype": a.dtype.str,
                    "sha256": hashlib.sha256(a.tobytes()).hexdigest()} for key, a in arrays.items()],
        "copied_before_final_arrays": True, "training_or_final_arrays_included": False,
        "copy_and_parameter_serialization_seconds": time.perf_counter() - started,
        "all_export_cost_in_trusted_fit_phase_and_worker_wall": True}
    metadata_path = directory / "metadata.json"
    atomic_write_json(metadata_path, metadata)
    if metadata_path.stat().st_size > MAX_METADATA:
        raise ValueError("Fitted metadata exceeds frozen bound")
    return {"version": VERSION, "directory_name": candidate,
        "metadata_sha256": sha256_file(metadata_path),
        "parameters_sha256": metadata["parameters_sha256"],
        "total_bytes": parameter_path.stat().st_size + metadata_path.stat().st_size,
        "export_seconds": time.perf_counter() - started,
        "copied_before_final_arrays": True, "all_cost_in_fit_phase": True}


def load_state(directory):
    directory = Path(directory)
    metadata_path, parameter_path = directory / "metadata.json", directory / "parameters.npz"
    if metadata_path.stat().st_size > MAX_METADATA or parameter_path.stat().st_size > MAX_PARAMETERS:
        raise ValueError("Fitted-state file exceeds bound")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (metadata["version"] != VERSION or metadata["arm"] not in ARMS
            or metadata["parameters_sha256"] != sha256_file(parameter_path)
            or metadata["parameters_bytes"] != parameter_path.stat().st_size
            or metadata["recipe_sha256"] != sha256_json(metadata["recipe"])
            or metadata["training_or_final_arrays_included"] is not False
            or metadata["copied_before_final_arrays"] is not True):
        raise ValueError("Fitted-state provenance mismatch")
    with zipfile.ZipFile(parameter_path) as archive:
        if (len(archive.infolist()) > 128 or
                sum(item.file_size for item in archive.infolist()) > MAX_PARAMETERS):
            raise ValueError("Expanded fitted-state payload exceeds bound")
    with np.load(parameter_path, allow_pickle=False) as archive:
        expected = [row["key"] for row in metadata["arrays"]]
        if len(set(expected)) != len(expected) or archive.files != expected:
            raise ValueError("Fitted parameter key/order mismatch")
        arrays = {}
        for row in metadata["arrays"]:
            if not re.fullmatch(r"(?:model|decoder)\.[A-Za-z0-9_.]+|weights|projection", row["key"]):
                raise ValueError("Unexpected fitted-state field")
            array = archive[row["key"]]
            if (array.dtype != np.float32 or not np.isfinite(array).all()
                    or list(array.shape) != row["shape"] or array.dtype.str != row["dtype"]
                    or hashlib.sha256(array.tobytes()).hexdigest() != row["sha256"]):
                raise ValueError("Fitted array integrity mismatch")
            arrays[row["key"]] = array.copy()
    return metadata, arrays


def restore_state(system, metadata, arrays):
    """Copy compatible parameters without optimization, calibration, or source data."""
    declared_arm = getattr(system, "transport_arm", getattr(system, "optimized_arm", system.arm))
    if (declared_arm != metadata["arm"] or system.seed != metadata["seed"]
            or sha256_json(system.recipe) != metadata["recipe_sha256"]):
        raise ValueError("Fitted-state restoration recipe/role mismatch")
    expected = set()
    for prefix in ("model", "decoder"):
        module = getattr(system, prefix, None)
        if module is not None:
            state = module.state_dict()
            expected.update(prefix + "." + k for k in state)
            for key, tensor in state.items():
                array = arrays.get(prefix + "." + key)
                if array is None or array.shape != tuple(tensor.shape):
                    raise ValueError("Fitted model shape mismatch")
    expected.update(k for k in ("weights", "projection") if k in arrays)
    if set(arrays) != expected:
        raise ValueError("Unexpected fitted restoration array")
    for prefix in ("model", "decoder"):
        module = getattr(system, prefix, None)
        if module is not None:
            module = module.to("cpu")
            module.load_state_dict({key: torch.as_tensor(arrays[prefix + "." + key])
                for key in module.state_dict()}, strict=True)
            module.eval()
            setattr(system, prefix, module)
    for key in ("weights", "projection"):
        if key in arrays:
            setattr(system, key, arrays[key].copy())
    system.threshold = metadata["threshold"]
    system.arm, system.device = metadata["arm"], torch.device("cpu")
