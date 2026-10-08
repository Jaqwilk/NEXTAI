"""C development intake: signed release coordinates, unchanged public geometry."""
from pathlib import Path
import re

import numpy as np

from .asm01_task import (SCREEN_WRITERS, transform, pairs, episode, prepared_calibration,
                         training_sets, episode_hash, arrays_hash, rng_for)
from .utils import load_json, sha256_file


TASK_PATH = 'research/plans/ASM01-C-SIGNED-SERIAL-TASK-V1.json'
TASK_SHA = '66cb7521a72e3485c8738d0f46cfe64bad3d773755fcc15c5db23a4cde9afa85'
STUDY_PATH = 'research/plans/ASM01-C-STABILIZED-SCREEN-V1.json'
STUDY_SHA = '297357e54f271bebe8fdf8da0d6a31c6d2c7a3fea5251ad9f1008eb9b26b8c1d'
MANIFEST_PATH = 'research/data_manifests/ASM01-C-ACQUISITION-V1.json'
DATASET_PATH = 'research/data/asm01_c_v1/screen.npz'
SOURCE_BINDING_PATH = 'research/reviews/ASM01-C-source-binding-V1.json'
PUBLISHER_PATH = 'research/data/asm01_native_v1/publisher.rar'
PUBLISHER_SHA = 'd6ad543e65269d53e38fdac6a32dd20bcd942e7616891a6cf95986894b454a4d'
SAMPLE_BYTES_CAP = 262144
POINTS_CAP = 32768
STROKES_CAP = 16384
_UNSIGNED = re.compile(r'[0-9]+')
_SIGNED = re.compile(r'-?[0-9]+')
_COUNT = re.compile(r'STROKE_COUNT:\s*([1-9][0-9]*)')
_COLUMNS = ['X', 'Y', 'STYLUS_STATE', 'STROKE']


def _bounded_decimal(token, limit, *, signed=False):
    """Check length/value lexically before converting a small bounded integer."""
    if (_SIGNED if signed else _UNSIGNED).fullmatch(token) is None:
        raise ValueError('coordinate_lexical' if signed else 'metadata_lexical')
    negative = token.startswith('-')
    magnitude = (token[1:] if negative else token).lstrip('0') or '0'
    ceiling = str(limit)
    if len(magnitude) > len(ceiling) or (len(magnitude) == len(ceiling) and magnitude > ceiling):
        raise ValueError('coordinate_bounds' if signed else 'metadata_bounds')
    value = int(magnitude)
    return -value if negative else value


def parse_native_sample(payload, *, metadata=None):
    """Parse the frozen release-only law; no fallback to historical grammars.

    Optional metadata contains only stroke IDs/counts, never names or X/Y values.
    Recognized release annotations do not determine point stroke boundaries.
    """
    if not isinstance(payload, bytes) or len(payload) > SAMPLE_BYTES_CAP:
        raise ValueError('native_byte_cap_type')
    try:
        lines = [line.strip() for line in payload.decode('ascii').splitlines() if line.strip()]
    except UnicodeDecodeError:
        raise ValueError('native_ascii') from None
    if (len(lines) < 7 or not lines[0].startswith('CHARACTER_NAME:')
            or not lines[-1].startswith('END_CHARACTER:')):
        raise ValueError('native_envelope')
    count_match = _COUNT.fullmatch(lines[1])
    if count_match is None:
        raise ValueError('native_stroke_count')
    count = _bounded_decimal(count_match[1], STROKES_CAP)
    positions = [index for index, line in enumerate(lines) if line.split() == _COLUMNS]
    if positions != [2]:
        raise ValueError('native_column_header')
    points, previous, last_serial = [], None, 0
    serial_counts = {}
    for line in lines[3:-1]:
        fields = line.split()
        if fields == ['PEN_DOWN'] or fields == ['PEN_UP', '0']:
            continue
        if len(fields) != 4:
            raise ValueError('native_point_arity')
        x = _bounded_decimal(fields[0], 4392, signed=True)
        y = _bounded_decimal(fields[1], 4868, signed=True)
        state = _bounded_decimal(fields[2], 1)
        serial = _bounded_decimal(fields[3], count)
        if state != 1 or serial == 0 or serial < last_serial:
            raise ValueError('native_point_state_serial')
        if serial != last_serial:
            previous = None
        serial_counts[str(serial)] = serial_counts.get(str(serial), 0) + 1
        position = (x, y)
        if position != previous:
            points.append(position)
            previous = position
        last_serial = serial
        if len(points) > POINTS_CAP:
            raise ValueError('native_point_cap')
    if len(points) < 4:
        raise ValueError('native_minimum_points')
    result = np.asarray(points, dtype=np.float32)
    try:
        for view in ('write', 'nominal', 'adverse'):
            transform(result, view)
    except (ValueError, FloatingPointError):
        raise ValueError('native_geometry') from None
    if metadata is not None:
        metadata.update(declared_strokes=count, point_serial_counts=serial_counts,
                        empty_stroke_ids=[serial for serial in range(1, count + 1)
                                          if str(serial) not in serial_counts],
                        raw_point_rows=sum(serial_counts.values()), retained_points=len(points))
    return result


def local_path(root, relative):
    """Refuse linked/escaping artifacts before opening their bytes."""
    root = Path(root)
    path = root / relative
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError('linked_local_artifact')
        if ancestor == root:
            break
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('escaping_local_artifact')
    return path


def _writer_arrays(archive, writer, manifest):
    points, offsets, rows = (archive[f'{prefix}_{writer}'].copy()
                            for prefix in ('points', 'offsets', 'rows'))
    if (points.dtype != np.float32 or points.ndim != 2 or points.shape[1] != 2
            or not np.isfinite(points).all() or np.any(points[:, 0] < -4392) or np.any(points[:, 0] > 4392)
            or np.any(points[:, 1] < -4868) or np.any(points[:, 1] > 4868)
            or not np.equal(points, np.trunc(points)).all()
            or offsets.dtype != np.int64 or offsets.shape != (184,)
            or offsets[0] != 0 or offsets[-1] != len(points)
            or np.any(np.diff(offsets) < 4) or np.any(np.diff(offsets) > POINTS_CAP)
            or rows.dtype != np.int64 or rows.shape != (183, 2)
            or not np.array_equal(rows[:, 0], np.arange(1, 184))
            or not np.all(rows[:, 1] == writer)):
        raise ValueError('native_writer_array_structure')
    if arrays_hash(points, offsets, rows) != manifest['converted_writer_hashes'].get(str(writer)):
        raise ValueError('native_writer_array_hash')
    return tuple(points[offsets[index]:offsets[index + 1]].copy() for index in range(183)), rows


def load_unit(root, index, nonce):
    """Same fixed pairs and partitions, bound exclusively to the complete C intake."""
    if type(index) is not int or index not in range(5):
        raise ValueError('Only the five fixed ASM screen pairs are accessible')
    root = Path(root)
    task, study = local_path(root, TASK_PATH), local_path(root, STUDY_PATH)
    if sha256_file(task) != TASK_SHA or sha256_file(study) != STUDY_SHA:
        raise ValueError('ASM C frozen task/study changed')
    manifest_path = local_path(root, MANIFEST_PATH)
    manifest = load_json(manifest_path)
    counts = ('native_files_attempted', 'native_files_converted', 'validated_files',
              'old74_compared', 'previous1171_compared', 'D_samples_opened')
    if (manifest.get('complete') is not True or manifest.get('task_contract_sha256') != TASK_SHA
            or manifest.get('study_sha256') != STUDY_SHA
            or manifest.get('converted_writers') != list(SCREEN_WRITERS)
            or manifest.get('no_future_writer_coordinates_read') is not True
            or manifest.get('dataset_path') != DATASET_PATH
            or manifest.get('publisher_sha256') != PUBLISHER_SHA
            or tuple(manifest.get(key) for key in counts) != (1830, 1830, 1830, 74, 1171, 915)
            or set(manifest.get('converted_writer_hashes', {})) != {str(w) for w in SCREEN_WRITERS}):
        raise ValueError('ASM C native acquisition/scope binding mismatch')
    source_binding = local_path(root, SOURCE_BINDING_PATH)
    if sha256_file(source_binding) != manifest.get('source_binding_sha256'):
        raise ValueError('ASM C intake source binding changed')
    dataset = local_path(root, DATASET_PATH)
    if sha256_file(dataset) != manifest.get('dataset_sha256'):
        raise ValueError('ASM screen payload changed/outside repository')
    if sha256_file(local_path(root, PUBLISHER_PATH)) != PUBLISHER_SHA:
        raise ValueError('Preserved ASM publisher archive changed')
    selected, seen = {}, set()
    with np.load(dataset, allow_pickle=False) as archive:
        if set(archive.files) != {f'{prefix}_{w}' for w in SCREEN_WRITERS
                                 for prefix in ('points', 'offsets', 'rows')}:
            raise ValueError('Unexpected future writer in native screen payload')
        for writer in SCREEN_WRITERS:
            paths, rows = _writer_arrays(archive, writer, manifest)
            for path in paths:
                digest = arrays_hash(path)
                if digest in seen:
                    raise ValueError('Duplicate native trajectory')
                seen.add(digest)
            if writer in (index + 1, index + 16):
                selected[writer] = (paths, rows)
    (train, train_rows), (dev, dev_rows) = selected[index + 1], selected[index + 16]
    order = rng_for(nonce, 'native-fit-validation-calibration').permutation(183)
    result = {}
    for name, indices in (('T-fit', order[:64]), ('T-validation', order[64:88]), ('T-calibration', order[88:])):
        result[name] = (tuple(train[i] for i in indices), train_rows[indices].copy())
    result.update(D=(dev, dev_rows), mean=np.zeros(64, dtype=np.float32), scale=np.ones(64, dtype=np.float32),
                  train_subject=index + 1, dev_subject=index + 16, train_writer=index + 1, dev_writer=index + 16,
                  intake_sha256=sha256_file(manifest_path), dataset_sha256=manifest['dataset_sha256'],
                  publisher_sha256=manifest['publisher_sha256'],
                  unique_counts={'T-fit': 64, 'T-validation': 24, 'T-calibration': 95, 'D': 183})
    return result
