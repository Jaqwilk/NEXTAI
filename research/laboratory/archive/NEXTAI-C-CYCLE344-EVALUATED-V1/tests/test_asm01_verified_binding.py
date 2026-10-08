"""Synthetic scope/integrity checks before any remaining publisher content."""
from pathlib import Path

import numpy as np
import pytest

from nextai_autoresearch import asm01_task, asm01_task_v2, asm01_task_v5
from nextai_autoresearch.benchmarks import asm01_native_memory_v2, asm01_native_memory_v3
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = 'research/data_manifests/ASM01-ACQUISITION-V3.json'


@pytest.fixture
def synthetic_intake(tmp_path):
    for relative in ('research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json',
                     'research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json'):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    publisher = tmp_path / 'research/data/asm01_native_v1/publisher.rar'
    publisher.parent.mkdir(parents=True)
    publisher.write_bytes(b'synthetic publisher bytes; no native content')
    arrays = {}
    digests = {}
    for writer in asm01_task.SCREEN_WRITERS:
        sample = np.array([[0, 0], [2, 3], [4, 1], [5, 5]], dtype=np.float32)
        points = np.concatenate([sample + np.array([character, writer], dtype=np.float32)
                                 for character in range(183)])
        offsets = np.arange(184, dtype=np.int64) * 4
        rows = np.column_stack((np.arange(1, 184), np.full(183, writer))).astype(np.int64)
        arrays.update({f'points_{writer}': points, f'offsets_{writer}': offsets, f'rows_{writer}': rows})
        digests[str(writer)] = asm01_task.arrays_hash(points, offsets, rows)
    dataset = publisher.parent / 'synthetic-screen.npz'
    np.savez_compressed(dataset, **arrays)
    manifest = dict(complete=True,
                    task_contract_sha256=sha256_file(tmp_path / 'research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json'),
                    study_sha256=sha256_file(tmp_path / 'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json'),
                    converted_writers=list(asm01_task.SCREEN_WRITERS), converted_writer_hashes=digests,
                    no_future_writer_coordinates_read=True, dataset_path=dataset.relative_to(tmp_path).as_posix(),
                    dataset_sha256=sha256_file(dataset), publisher_sha256=sha256_file(publisher))
    atomic_write_json(tmp_path / RECEIPT, manifest)
    return tmp_path, arrays, manifest


def test_v3_uses_identical_descriptor_episode_and_pair_functions():
    for name in ('transform', 'pairs', 'episode', 'prepared_calibration', 'training_sets', 'arrays_hash', 'episode_hash'):
        assert getattr(asm01_task_v5, name) is getattr(asm01_task, name)
    assert asm01_native_memory_v3.selected.run_suite.__code__ is asm01_native_memory_v2.run_suite.__code__
    with pytest.raises(ValueError, match='cohort mismatch'):
        asm01_native_memory_v3.run_suite('unused', {'benchmark': 'asm01_native_memory_v2'})
    assert asm01_native_memory_v2.load_unit is asm01_task_v2.load_unit


@pytest.mark.parametrize('index', range(5))
def test_five_fixed_pairs_and_disjoint_64_24_95_training_partition(synthetic_intake, index):
    root, _, _ = synthetic_intake
    unit = asm01_task_v5.load_unit(root, index, 'a' * 64)
    assert (unit['train_writer'], unit['dev_writer']) == (index + 1, index + 16)
    partitions = [set(unit[name][1][:, 0]) for name in ('T-fit', 'T-validation', 'T-calibration')]
    assert [len(values) for values in partitions] == [64, 24, 95]
    assert not (partitions[0] & partitions[1] or partitions[0] & partitions[2] or partitions[1] & partitions[2])
    assert set.union(*partitions) == set(range(1, 184))
    assert len(unit['D'][0]) == 183 and np.all(unit['D'][1][:, 1] == index + 16)
    assert np.array_equal(unit['mean'], np.zeros(64, dtype=np.float32))
    assert np.array_equal(unit['scale'], np.ones(64, dtype=np.float32))


@pytest.mark.parametrize('alter', ['incomplete', 'task', 'study', 'writers', 'future-flag', 'payload', 'writer-hash'])
def test_native_scope_and_hash_failures_stop_before_serving(synthetic_intake, alter):
    root, _, manifest = synthetic_intake
    if alter == 'incomplete':
        manifest['complete'] = False
    elif alter == 'task':
        manifest['task_contract_sha256'] = '0' * 64
    elif alter == 'study':
        manifest['study_sha256'] = '0' * 64
    elif alter == 'writers':
        manifest['converted_writers'][-1] = 31
    elif alter == 'future-flag':
        manifest['no_future_writer_coordinates_read'] = False
    elif alter == 'payload':
        manifest['dataset_sha256'] = '0' * 64
    else:
        manifest['converted_writer_hashes']['1'] = '0' * 64
    atomic_write_json(root / RECEIPT, manifest)
    with pytest.raises(ValueError):
        asm01_task_v5.load_unit(root, 0, 'a' * 64)


def test_unselected_writer_member_is_rejected_even_with_matching_payload_hash(synthetic_intake):
    root, arrays, manifest = synthetic_intake
    dataset = root / manifest['dataset_path']
    arrays['points_21'] = np.zeros((4, 2), dtype=np.float32)
    np.savez_compressed(dataset, **arrays)
    manifest['dataset_sha256'] = sha256_file(dataset)
    atomic_write_json(root / RECEIPT, manifest)
    with pytest.raises(ValueError, match='Unexpected future writer'):
        asm01_task_v5.load_unit(root, 0, 'a' * 64)


def test_old_acquisition_cannot_stand_in_for_new_version(synthetic_intake):
    root, _, manifest = synthetic_intake
    old = root / 'research/data_manifests/ASM01-ACQUISITION-V2.json'
    atomic_write_json(old, manifest)
    (root / RECEIPT).unlink()
    with pytest.raises(FileNotFoundError):
        asm01_task_v5.load_unit(root, 0, 'a' * 64)
    with pytest.raises(ValueError, match='five fixed ASM'):
        asm01_task_v5.load_unit(root, 5, 'a' * 64)


def test_v3_terminal_manifest_dispatch_keeps_historical_module_unchanged(synthetic_intake, monkeypatch):
    root, _, _ = synthetic_intake
    monkeypatch.setattr(asm01_native_memory_v3, 'project_root', lambda: root)
    new = root / RECEIPT
    requested = root / 'research/data_manifests/ASM01-ACQUISITION-V2.json'
    assert asm01_native_memory_v3._native_json(requested) == load_json(new)
    assert asm01_native_memory_v2.load_json is load_json
