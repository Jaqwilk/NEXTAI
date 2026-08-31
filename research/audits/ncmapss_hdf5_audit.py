"""Minimal read-only HDF5 bridge for the acquired N-CMAPSS audit."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path

import numpy as np


class H5:
    def __init__(self, library: Path, path: Path) -> None:
        os.add_dll_directory(str(library.parent))
        self.lib = ctypes.CDLL(str(library))
        self._bind()
        self.file = self.H5Fopen(os.fsencode(path), 0, 0)
        if self.file < 0:
            raise RuntimeError(f"H5Fopen failed: {path}")

    def _fn(self, name: str, result, *args):
        fn = getattr(self.lib, f"vtkhdf5_{name}")
        fn.restype = result
        fn.argtypes = list(args)
        setattr(self, name, fn)

    def _bind(self) -> None:
        hid = ctypes.c_longlong
        size = ctypes.c_size_t
        ptr = ctypes.c_void_p
        self._fn("H5Fopen", hid, ctypes.c_char_p, ctypes.c_uint, hid)
        self._fn("H5Fclose", ctypes.c_int, hid)
        self._fn("H5Dopen2", hid, hid, ctypes.c_char_p, hid)
        self._fn("H5Dclose", ctypes.c_int, hid)
        self._fn("H5Dget_space", hid, hid)
        self._fn("H5Dget_type", hid, hid)
        self._fn("H5Dread", ctypes.c_int, hid, hid, hid, hid, hid, ptr)
        self._fn("H5Sget_simple_extent_ndims", ctypes.c_int, hid)
        self._fn("H5Sget_simple_extent_dims", ctypes.c_int, hid, ptr, ptr)
        self._fn("H5Sclose", ctypes.c_int, hid)
        self._fn("H5Tget_class", ctypes.c_int, hid)
        self._fn("H5Tget_order", ctypes.c_int, hid)
        self._fn("H5Tget_sign", ctypes.c_int, hid)
        self._fn("H5Tget_size", size, hid)
        self._fn("H5Tclose", ctypes.c_int, hid)

    def close(self) -> None:
        if self.file >= 0:
            self.H5Fclose(self.file)
            self.file = -1

    def _open(self, name: str):
        dataset = self.H5Dopen2(self.file, name.encode(), 0)
        if dataset < 0:
            raise KeyError(name)
        space = self.H5Dget_space(dataset)
        dtype = self.H5Dget_type(dataset)
        if min(space, dtype) < 0:
            raise RuntimeError(f"metadata open failed: {name}")
        rank = self.H5Sget_simple_extent_ndims(space)
        dims = (ctypes.c_ulonglong * rank)()
        self.H5Sget_simple_extent_dims(space, dims, None)
        return dataset, space, dtype, tuple(int(x) for x in dims)

    def schema(self, name: str) -> dict:
        dataset, space, dtype, shape = self._open(name)
        try:
            kind = self.H5Tget_class(dtype)
            return {
                "shape": list(shape),
                "class": kind,
                "size": int(self.H5Tget_size(dtype)),
                "order": self.H5Tget_order(dtype),
                "sign": self.H5Tget_sign(dtype) if kind == 0 else None,
            }
        finally:
            self.H5Tclose(dtype)
            self.H5Sclose(space)
            self.H5Dclose(dataset)

    def read_numeric(self, name: str) -> np.ndarray:
        dataset, space, dtype, shape = self._open(name)
        try:
            kind = {0: "u" if self.H5Tget_sign(dtype) == 0 else "i", 1: "f"}.get(
                self.H5Tget_class(dtype)
            )
            if kind is None:
                raise TypeError(f"non-numeric dataset: {name}")
            byte_order = "<" if self.H5Tget_order(dtype) in (0, 4) else ">"
            array = np.empty(shape, dtype=np.dtype(f"{byte_order}{kind}{self.H5Tget_size(dtype)}"))
            if self.H5Dread(dataset, dtype, 0, 0, 0, array.ctypes.data) < 0:
                raise RuntimeError(f"H5Dread failed: {name}")
            return array
        finally:
            self.H5Tclose(dtype)
            self.H5Sclose(space)
            self.H5Dclose(dataset)

    def read_strings(self, name: str) -> list[str]:
        dataset, space, dtype, shape = self._open(name)
        try:
            width = int(self.H5Tget_size(dtype))
            array = np.empty(shape, dtype=f"S{width}")
            if self.H5Dread(dataset, dtype, 0, 0, 0, array.ctypes.data) < 0:
                raise RuntimeError(f"H5Dread failed: {name}")
            return [value.decode().rstrip("\x00 ") for value in array.reshape(-1)]
        finally:
            self.H5Tclose(dtype)
            self.H5Sclose(space)
            self.H5Dclose(dataset)


def _engine_rows(aux: np.ndarray, unit: int, count: int) -> np.ndarray:
    rows = np.flatnonzero(aux[:, 0] == unit)
    if rows.size < count:
        raise ValueError(f"unit {unit} has only {rows.size} rows")
    return rows[:count]


def _transitions(aux: np.ndarray, unit: int, count: int, stride: int) -> np.ndarray:
    rows = np.flatnonzero(aux[:, 0] == unit)
    starts = rows[:-1]
    consecutive = (aux[starts, 1] == aux[starts + 1, 1])
    starts = starts[consecutive][::stride]
    if starts.size < count:
        raise ValueError(f"unit {unit} has only {starts.size} sampled transitions")
    return starts[:count]


def _ridge(train_x: np.ndarray, train_y: np.ndarray, query_x: np.ndarray) -> np.ndarray:
    x_mean, x_std = train_x.mean(0), train_x.std(0)
    y_mean, y_std = train_y.mean(0), train_y.std(0)
    x_std[x_std < 1e-12] = 1.0
    y_std[y_std < 1e-12] = 1.0
    x = (train_x - x_mean) / x_std
    y = (train_y - y_mean) / y_std
    design = np.column_stack((np.ones(x.shape[0]), x))
    gram = design.T @ design
    gram.flat[:: gram.shape[0] + 1] += 0.001
    weights = np.linalg.solve(gram, design.T @ y)
    query = np.column_stack((np.ones(query_x.shape[0]), (query_x - x_mean) / x_std))
    return (query @ weights) * y_std + y_mean


def _nrmse(truth: np.ndarray, prediction: np.ndarray) -> float:
    scale = truth.std(0)
    active = scale >= 1e-12
    if not active.any():
        raise ValueError("all query targets are constant")
    return float(np.sqrt(np.mean(((truth[:, active] - prediction[:, active]) / scale[active]) ** 2)))


def export_portable(h5: H5, directory: Path) -> dict:
    arrays = {
        f"{name}.npy": (name, np.int16 if name.startswith("A_") else np.float32)
        for name in ("A_dev", "A_test", "W_dev", "W_test", "X_s_dev", "X_s_test")
    }
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory / name).exists() for name in arrays):
        raise FileExistsError("portable export target already exists")
    result = {}
    for filename, (source, dtype) in arrays.items():
        values = h5.read_numeric(source)
        if not np.isfinite(values).all():
            raise ValueError(f"nonfinite values in {source}")
        converted = values.astype(dtype)
        if dtype is np.int16 and not np.array_equal(values, converted):
            raise ValueError(f"lossy integer conversion in {source}")
        error = np.abs(values - converted.astype(values.dtype))
        scaled = error / np.maximum(1.0, np.abs(values))
        target = directory / filename
        temporary = target.with_suffix(target.suffix + ".tmp")
        with temporary.open("wb") as stream:
            np.save(stream, converted, allow_pickle=False)
        os.replace(temporary, target)
        result[filename] = {
            "source": source,
            "shape": list(converted.shape),
            "dtype": converted.dtype.name,
            "max_absolute_cast_error": float(error.max(initial=0.0)),
            "max_scaled_cast_error": float(scaled.max(initial=0.0)),
            "bytes": target.stat().st_size,
        }
    return result


def semantic_gate(h5: H5, variables: dict[str, list[str]], spec: dict) -> dict:
    data, unit_source = {}, {}
    for source, suffix in (("development", "dev"), ("test", "test")):
        aux = h5.read_numeric(f"A_{suffix}")
        entry = {
            "aux": aux,
            "xs": h5.read_numeric(f"X_s_{suffix}"),
            "private_t": h5.read_numeric(f"T_{suffix}"),
            "private_y": h5.read_numeric(f"Y_{suffix}"),
        }
        entry["visible"] = np.column_stack((h5.read_numeric(f"W_{suffix}"), entry["xs"]))
        observed = set(np.unique(aux[:, 0]).astype(int))
        expected = set(spec["source_units"][source])
        if observed != expected:
            raise ValueError(f"{source} unit mismatch: {sorted(observed)} != {sorted(expected)}")
        data[source] = entry
        unit_source.update({unit: source for unit in observed})

    role_units = spec["roles"]
    all_role_units = role_units["training"] + role_units["holdout"]
    if len(set(all_role_units)) != len(all_role_units) or set(all_role_units) != set(unit_source):
        raise ValueError("roles must be disjoint and cover every source unit")

    summaries, labels, units = [], [], []
    leak_visible, leak_private = [], []
    prefix = spec["router"]["prefix_rows_per_unit"]
    if prefix != spec["leakage"]["rows_per_unit"]:
        raise ValueError("router and leakage prefixes must match")
    for label, role in enumerate(("training", "holdout")):
        for unit in role_units[role]:
            source = data[unit_source[unit]]
            rows = _engine_rows(source["aux"], unit, prefix)
            sample = source["visible"][rows]
            summaries.append(np.concatenate((sample.mean(0), sample.std(0))))
            labels.append(label)
            units.append(unit)
            leak_visible.append(sample)
            leak_private.append(np.column_stack((
                source["aux"][rows, 2:4], source["private_t"][rows], source["private_y"][rows]
            )))

    summaries, labels = np.asarray(summaries), np.asarray(labels)
    predictions = []
    for held_out in range(len(units)):
        train = np.arange(len(units)) != held_out
        mean, std = summaries[train].mean(0), summaries[train].std(0)
        std[std < 1e-12] = 1.0
        scaled = (summaries - mean) / std
        centroids = [scaled[train & (labels == label)].mean(0) for label in (0, 1)]
        distances = [float(np.linalg.norm(scaled[held_out] - centroid)) for centroid in centroids]
        predictions.append(1 if distances[1] < distances[0] else 0)
    router_accuracy = float(np.mean(np.asarray(predictions) == labels))

    leak_visible, leak_private = np.vstack(leak_visible), np.vstack(leak_private)
    exact, maximum_correlation = [], 0.0
    private_names = ["Fc", "hs", *variables["T_var"], "Y"]
    visible_names = [*variables["W_var"], *variables["X_s_var"]]
    for left, visible_name in enumerate(visible_names):
        for right, private_name in enumerate(private_names):
            if np.array_equal(leak_visible[:, left], leak_private[:, right]):
                exact.append([visible_name, private_name])
            if min(leak_visible[:, left].std(), leak_private[:, right].std()) >= 1e-12:
                correlation = abs(float(np.corrcoef(leak_visible[:, left], leak_private[:, right])[0, 1]))
                maximum_correlation = max(maximum_correlation, correlation)

    control = spec["no_adaptation_control"]
    pooled_x, pooled_y = [], []
    for unit in role_units["training"]:
        source = data[unit_source[unit]]
        rows = _transitions(
            source["aux"], unit, control["training_transitions_per_unit"], control["sampling_stride"]
        )
        pooled_x.append(source["visible"][rows])
        pooled_y.append(source["xs"][rows + 1])
    pooled_x, pooled_y = np.vstack(pooled_x), np.vstack(pooled_y)

    adaptation_count = control["holdout_adaptation_transitions_per_unit"]
    query_count = control["holdout_query_transitions_per_unit"]
    query_truth, persistence, pooled, adapted = [], [], [], []
    for unit in role_units["holdout"]:
        source = data[unit_source[unit]]
        rows = _transitions(
            source["aux"], unit, adaptation_count + query_count, control["sampling_stride"]
        )
        adaptation, query = rows[:adaptation_count], rows[adaptation_count:]
        query_truth.append(source["xs"][query + 1])
        persistence.append(source["xs"][query])
        pooled.append(_ridge(pooled_x, pooled_y, source["visible"][query]))
        adapted.append(_ridge(
            source["visible"][adaptation], source["xs"][adaptation + 1], source["visible"][query]
        ))
    query_truth = np.vstack(query_truth)
    controls = {
        "persistence_nrmse": _nrmse(query_truth, np.vstack(persistence)),
        "training_pooled_no_adaptation_nrmse": _nrmse(query_truth, np.vstack(pooled)),
        "per_unit_prefix_adaptation_nrmse": _nrmse(query_truth, np.vstack(adapted)),
    }
    finite_controls = all(np.isfinite(value) for value in controls.values())
    router_max = spec["router"]["pass_max_accuracy"]
    correlation_max = spec["leakage"]["reject_absolute_pearson_correlation_at_or_above"]
    passed = router_accuracy <= router_max and not exact and maximum_correlation < correlation_max and finite_controls
    return {
        "units": role_units,
        "flight_classes": {
            role: {
                str(unit): np.unique(data[unit_source[unit]]["aux"][
                    data[unit_source[unit]]["aux"][:, 0] == unit, 2
                ]).tolist()
                for unit in role_units[role]
            }
            for role in ("training", "holdout")
        },
        "router": {
            "units": units,
            "truth": labels.tolist(),
            "predictions": predictions,
            "accuracy": router_accuracy,
            "pass_max_accuracy": router_max,
        },
        "leakage": {
            "exact_matches": exact,
            "maximum_absolute_correlation": maximum_correlation,
            "pass_max_absolute_correlation": correlation_max,
        },
        "no_adaptation_controls": controls,
        "pass": passed,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("library", type=Path)
    parser.add_argument("--semantic-output", type=Path)
    parser.add_argument("--semantic-spec", type=Path)
    parser.add_argument("--portable-dir", type=Path)
    args = parser.parse_args()
    names = [
        "A_dev", "A_test", "A_var", "T_dev", "T_test", "T_var",
        "W_dev", "W_test", "W_var", "X_s_dev", "X_s_test", "X_s_var",
        "X_v_dev", "X_v_test", "X_v_var", "Y_dev", "Y_test",
    ]
    h5 = H5(args.library.resolve(), args.file.resolve())
    try:
        schema = {name: h5.schema(name) for name in names}
        variables = {name: h5.read_strings(name) for name in names if name.endswith("_var")}
        auxiliaries = {}
        for name in ("A_dev", "A_test"):
            values = h5.read_numeric(name)
            summaries = []
            for column in range(values.shape[1]):
                unique = np.unique(values[:, column])
                summaries.append(
                    {"values": unique.tolist()} if unique.size <= 16 else
                    {"count": int(unique.size), "minimum": float(unique[0]), "maximum": float(unique[-1])}
                )
            auxiliaries[name] = {
                "shape": list(values.shape),
                "columns": variables["A_var"],
                "unique": summaries,
            }
        result = {"schema": schema, "variables": variables, "auxiliaries": auxiliaries}
        if args.portable_dir:
            result["portable_export"] = export_portable(h5, args.portable_dir)
        if args.semantic_output:
            if not args.semantic_spec:
                parser.error("--semantic-output requires --semantic-spec")
            spec = json.loads(args.semantic_spec.read_text(encoding="utf-8"))
            result["semantic_gate"] = semantic_gate(h5, variables, spec)
            payload = json.dumps(result, indent=2) + "\n"
            temporary = args.semantic_output.with_suffix(args.semantic_output.suffix + ".tmp")
            temporary.write_text(payload, encoding="utf-8")
            os.replace(temporary, args.semantic_output)
        print(json.dumps(result, indent=2))
    finally:
        h5.close()


if __name__ == "__main__":
    main()
