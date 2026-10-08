"""One frozen C intake; complete history/metadata gates precede native bytes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
import uuid

import numpy as np

from nextai_autoresearch.asm01_inventory_members_v3 import screen_members
from nextai_autoresearch.asm01_task import SCREEN_WRITERS, arrays_hash, transform
from nextai_autoresearch.asm01_task_v4 import parse_native_sample as parse_old_sample
from nextai_autoresearch.asm01_task_v6 import (
    parse_native_sample, local_path, _writer_arrays, TASK_PATH, TASK_SHA,
    STUDY_PATH, STUDY_SHA, MANIFEST_PATH, DATASET_PATH, SOURCE_BINDING_PATH,
    PUBLISHER_PATH, PUBLISHER_SHA,
)
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now


_IDENTITIES = tuple((writer, sample) for writer in SCREEN_WRITERS for sample in range(1, 184))
_UIDS = tuple(f'{writer}:{sample}' for writer, sample in _IDENTITIES)
_KEYS = set(_UIDS)
_OLD74 = set(_UIDS[:74])
_OLD75 = set(_UIDS[:75])
_PREVIOUS1171 = set(_UIDS[:1171])
_ATTEMPTED1172 = set(_UIDS[:1172])
_VIEWS = ('write', 'nominal', 'adverse')
_SHA = re.compile(r'[0-9a-f]{64}')
_COUNTS = ('native_files_attempted', 'native_files_converted', 'validated_files',
           'old74_compared', 'previous1171_compared', 'D_samples_opened')
_COMPLETE_COUNTS = (1830, 1830, 1830, 74, 1171, 915)


def _sha_map(mapping, keys):
    if (not isinstance(mapping, dict) or set(mapping) != keys
            or any(not isinstance(value, str) or _SHA.fullmatch(value) is None
                   for value in mapping.values())):
        raise ValueError('metadata')


def _history(expected_sha, old_sha, prior):
    _sha_map(expected_sha, _KEYS)
    _sha_map(old_sha, _OLD75)
    if any(old_sha[key] != expected_sha[key] for key in _OLD75):
        raise ValueError('metadata')
    if (not isinstance(prior, dict) or prior.get('complete') is not False
            or prior.get('native_files_attempted') != 1172
            or prior.get('native_files_converted') != 1171
            or prior.get('old74_compared') != 74 or prior.get('D_samples_opened') != 257
            or prior.get('current_sample') != '17:74' or prior.get('error_category') != 'normalize'):
        raise ValueError('metadata')
    _sha_map(prior.get('attempted_sample_text_sha256'), _ATTEMPTED1172)
    _sha_map(prior.get('sample_array_sha256'), _PREVIOUS1171)
    _sha_map(prior.get('old_array_sha256'), _OLD74)
    if any(prior['attempted_sample_text_sha256'][key] != expected_sha[key] for key in _ATTEMPTED1172):
        raise ValueError('metadata')
    if any(prior['old_array_sha256'][key] != prior['sample_array_sha256'][key] for key in _OLD74):
        raise ValueError('metadata')
    descriptors = prior.get('old_descriptor_sha256')
    if not isinstance(descriptors, dict) or set(descriptors) != _OLD74:
        raise ValueError('metadata')
    for descriptor in descriptors.values():
        _sha_map(descriptor, set(_VIEWS))


def collect(members, expected_sha, old_sha, prior_receipt, receipt, reader=None, *, progress=None):
    """Pure injected-reader engine, one complete fixed collection per receipt.

    Real callers first obtain members from screen_members. The prior receipt is
    the historical completion's native_intake object, never historical arrays.
    Progress callbacks receive only hashes, IDs and categorical/count metadata.
    """
    if receipt.get('collection_started'):
        raise ValueError('collection_consumed')
    receipt.update(collection_started=True, complete=False, attempted_files=0,
                   converted_files=0, validated_files=0, old74_compared=0,
                   previous1171_compared=0, native_files_attempted=0,
                   native_files_converted=0, D_samples_opened=0, T_samples_opened=0,
                   current_UID=None, current_sample=None, error_category=None,
                   attempted_sample_text_sha256={}, sample_array_sha256={},
                   old_array_sha256={}, old_descriptor_sha256={}, sample_stroke_metadata={})
    phase = 'metadata'
    try:
        members = list(members)
        identities, paths = [], []
        if len(members) != 1830:
            raise ValueError(phase)
        for member in members:
            if not isinstance(member, (tuple, list)) or len(member) != 3:
                raise ValueError(phase)
            writer, sample, path = member
            if type(writer) is not int or type(sample) is not int or not isinstance(path, Path):
                raise ValueError(phase)
            identities.append((writer, sample))
            paths.append(path)
        if tuple(identities) != _IDENTITIES or len(set(paths)) != 1830:
            raise ValueError(phase)
        _history(expected_sha, old_sha, prior_receipt)
        if (reader is not None and not callable(reader)) or (progress is not None and not callable(progress)):
            raise ValueError(phase)

        by_writer, seen = {writer: [] for writer in SCREEN_WRITERS}, set()
        for writer, sample, path in members:
            key = f'{writer}:{sample}'
            is_old = key in _OLD74
            if not is_old and receipt['old74_compared'] != 74:
                phase = 'old_array_difference'
                raise ValueError(phase)
            receipt.update(current_UID=key, current_sample=key)
            receipt['attempted_files'] += 1
            receipt['native_files_attempted'] += 1
            receipt['D_samples_opened' if writer >= 16 else 'T_samples_opened'] += 1
            phase = 'read'
            if progress is not None:
                progress(receipt)
            payload = path.read_bytes() if reader is None else reader(path)
            if not isinstance(payload, bytes):
                raise ValueError(phase)
            digest = hashlib.sha256(payload).hexdigest()
            receipt['attempted_sample_text_sha256'][key] = digest
            if progress is not None:
                progress(receipt)
            phase = 'raw_sha'
            if digest != expected_sha[key] or (is_old and digest != old_sha[key]):
                raise ValueError(phase)
            phase = 'native_geometry'
            stroke_metadata = {}
            value = parse_native_sample(payload, metadata=stroke_metadata)
            if (not isinstance(value, np.ndarray) or value.dtype != np.float32
                    or value.ndim != 2 or value.shape[1] != 2 or not value.flags.c_contiguous):
                raise ValueError(phase)
            receipt['converted_files'] += 1
            receipt['native_files_converted'] += 1
            value_digest = arrays_hash(value)
            receipt['sample_array_sha256'][key] = value_digest
            receipt['sample_stroke_metadata'][key] = stroke_metadata
            if is_old:
                phase = 'old_reference'
                previous = parse_old_sample(payload)
                phase = 'old_array_difference'
                if (previous.dtype != value.dtype or previous.shape != value.shape
                        or previous.tobytes() != value.tobytes()
                        or arrays_hash(previous) != prior_receipt['old_array_sha256'][key]):
                    raise ValueError(phase)
                receipt['old_array_sha256'][key] = arrays_hash(previous)
                descriptors = {}
                phase = 'old_view_difference'
                for view in _VIEWS:
                    before, after = transform(previous, view), transform(value, view)
                    if (before.dtype != after.dtype or before.shape != after.shape
                            or before.tobytes() != after.tobytes()
                            or arrays_hash(before) != prior_receipt['old_descriptor_sha256'][key][view]):
                        raise ValueError(phase)
                    descriptors[view] = arrays_hash(before)
                receipt['old_descriptor_sha256'][key] = descriptors
                receipt['old74_compared'] += 1
            if key in _PREVIOUS1171:
                phase = 'previous_array_difference'
                if value_digest != prior_receipt['sample_array_sha256'][key]:
                    raise ValueError(phase)
                receipt['previous1171_compared'] += 1
            phase = 'duplicate'
            if value_digest in seen:
                raise ValueError(phase)
            seen.add(value_digest)
            by_writer[writer].append(value)
            receipt['validated_files'] += 1
            if progress is not None:
                progress(receipt)

        phase = 'serialization'
        if tuple(receipt[key] for key in _COUNTS) != _COMPLETE_COUNTS:
            raise ValueError(phase)
        arrays, writer_hashes = {}, {}
        for writer in SCREEN_WRITERS:
            values = by_writer[writer]
            offsets = np.r_[0, np.cumsum([len(value) for value in values], dtype=np.int64)]
            points = np.concatenate(values)
            rows = np.column_stack((np.arange(1, 184), np.full(183, writer))).astype(np.int64)
            arrays.update({f'points_{writer}': points, f'offsets_{writer}': offsets, f'rows_{writer}': rows})
            writer_hashes[str(writer)] = arrays_hash(points, offsets, rows)
        receipt.update(complete=True, converted_writers=list(SCREEN_WRITERS),
                       converted_writer_hashes=writer_hashes)
        return arrays, writer_hashes
    except BaseException as error:
        receipt.update(complete=False, error_category=phase, error_type=type(error).__name__)
        if progress is not None:
            progress(receipt)
        raise ValueError(phase) from None


def _exclusive_json(path, value):
    temporary = path.with_name(path.name + '.publication.partial')
    with temporary.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, sort_keys=True, separators=(',', ':'))
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    os.link(temporary, path)
    temporary.unlink()


def publish(root, arrays, writerhashes, receipt, *, owned_manifest=False):
    """Exclusive atomic NPZ publication; retain partials on any failure."""
    root = Path(root)
    manifest, dataset = local_path(root, MANIFEST_PATH), local_path(root, DATASET_PATH)
    partial = dataset.with_name(dataset.name + '.partial')
    if dataset.exists() or partial.exists():
        raise ValueError('publication_consumed')
    if owned_manifest:
        previous = load_json(manifest)
        if (not receipt.get('intake_attempt_id') or previous.get('intake_attempt_id') != receipt['intake_attempt_id']
                or previous.get('study_sha256') != STUDY_SHA or previous.get('complete') is not False):
            raise ValueError('manifest_ownership')
    elif manifest.exists():
        raise ValueError('publication_consumed')
    if (receipt.get('complete') is not True
            or tuple(receipt.get(key) for key in _COUNTS) != _COMPLETE_COUNTS
            or set(arrays) != {f'{prefix}_{w}' for w in SCREEN_WRITERS for prefix in ('points', 'offsets', 'rows')}
            or set(writerhashes) != {str(w) for w in SCREEN_WRITERS}):
        raise ValueError('publication_incomplete')
    _sha_map(receipt.get('attempted_sample_text_sha256'), _KEYS)
    _sha_map(receipt.get('sample_array_sha256'), _KEYS)
    for relative, digest in ((TASK_PATH, TASK_SHA), (STUDY_PATH, STUDY_SHA)):
        if sha256_file(local_path(root, relative)) != digest:
            raise ValueError('publication_frozen_binding')
    binding = local_path(root, SOURCE_BINDING_PATH)
    if sha256_file(binding) != receipt.get('source_binding_sha256'):
        raise ValueError('publication_source_binding')
    seen = set()
    for writer in SCREEN_WRITERS:
        paths, _ = _writer_arrays(arrays, writer, {'converted_writer_hashes': writerhashes})
        for sample, path in enumerate(paths, 1):
            digest = arrays_hash(path)
            if digest in seen or digest != receipt['sample_array_sha256'][f'{writer}:{sample}']:
                raise ValueError('publication_array_history')
            seen.add(digest)
    dataset.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with partial.open('xb') as output:
        np.savez_compressed(output, **arrays)
        output.flush()
        os.fsync(output.fileno())
    os.link(partial, dataset)
    partial.unlink()
    receipt.update(complete=True, task_contract_sha256=TASK_SHA, study_sha256=STUDY_SHA,
                   converted_writers=list(SCREEN_WRITERS), converted_writer_hashes=writerhashes,
                   dataset_path=DATASET_PATH, dataset_sha256=sha256_file(dataset),
                   dataset_bytes=dataset.stat().st_size, publisher_sha256=PUBLISHER_SHA,
                   no_future_writer_coordinates_read=True)
    if owned_manifest:
        atomic_write_json(manifest, receipt, compact=True)
    else:
        _exclusive_json(manifest, receipt)
    return dataset


def _deadline(study, effective_deadline=None):
    deadline = datetime.fromisoformat(study['study_deadline_at'].replace('Z', '+00:00'))
    if effective_deadline is not None:
        deadline = min(deadline, datetime.fromisoformat(effective_deadline.replace('Z', '+00:00')))
    if datetime.now(timezone.utc) >= deadline:
        raise ValueError('intake_deadline')


def _source_binding(root, study):
    binding_path = local_path(root, SOURCE_BINDING_PATH)
    binding = load_json(binding_path)
    if (binding.get('study_sha256') != STUDY_SHA or binding.get('task_contract_sha256') != TASK_SHA
            or binding.get('native_intake_authorized') is not True
            or binding.get('synthetic_conformance_complete') is not True
            or not isinstance(binding.get('files'), dict)):
        raise ValueError('source_binding')
    required = dict(study['source_hashes_preserved'])
    for relative in ('src/nextai_autoresearch/asm01_task_v6.py',
                     'src/nextai_autoresearch/benchmarks/asm01_native_memory_v4.py',
                     'scripts/acquire_asm01_c_v1.py'):
        if relative not in binding['files']:
            raise ValueError('source_binding')
    if any(binding['files'].get(relative) != digest for relative, digest in required.items()):
        raise ValueError('source_binding')
    for relative, digest in binding['files'].items():
        if not isinstance(digest, str) or _SHA.fullmatch(digest) is None:
            raise ValueError('source_binding')
        if sha256_file(local_path(root, relative)) != digest:
            raise ValueError('source_binding')
    return sha256_file(binding_path)


def main():
    root = Path.cwd().resolve()
    import nextai_autoresearch
    if (root.name != 'NEXTAI-VALIDATION-20261002'
            or not Path(nextai_autoresearch.__file__).resolve().is_relative_to((root / 'src').resolve())):
        raise ValueError('independent_clone_origin')
    manifest = local_path(root, MANIFEST_PATH)
    dataset = local_path(root, DATASET_PATH)
    if manifest.exists() or dataset.exists() or dataset.with_name(dataset.name + '.partial').exists():
        raise ValueError('intake_consumed')
    started, receipt, phase = time.perf_counter(), {}, 'preflight'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    receipt.update(created_at=utc_now(), complete=False, intake_attempt_id=str(uuid.uuid4()),
                   task_contract_sha256=TASK_SHA, study_sha256=STUDY_SHA,
                   native_files_attempted=0, native_files_converted=0, old74_compared=0,
                   previous1171_compared=0, validated_files=0, D_samples_opened=0,
                   attempted_sample_text_sha256={}, no_future_writer_coordinates_read=True,
                   numeric_values_or_names_emitted=False, new_download_or_extraction=False,
                   research_fit_seconds=0, EXP=0, registration=0, scoring=False)
    _exclusive_json(manifest, receipt)

    def persist(current):
        pending = dict(current, complete=False)
        atomic_write_json(manifest, pending, compact=True)

    try:
        if any((root / relative).exists() for relative in ('STOP', 'PAUSE', 'research/run.lock')):
            raise ValueError('laboratory_not_idle')
        if (sha256_file(local_path(root, TASK_PATH)) != TASK_SHA
                or sha256_file(local_path(root, STUDY_PATH)) != STUDY_SHA):
            raise ValueError('frozen_plan_binding')
        task, study = load_json(root / TASK_PATH), load_json(root / STUDY_PATH)
        if task['cohort'] != 'asm01_native_memory_v4' or study['cohort'] != 'asm01_native_memory_v4':
            raise ValueError('frozen_cohort_binding')
        # Read/hash the C authority once. Per-file gates use its captured deadline,
        # so the append-only historical ledger is not rescanned1830 times.
        from nextai_autoresearch import research_program_c
        if not research_program_c.is_active(root):
            raise ValueError('C_authority_inactive')
        authority = research_program_c.status(root)
        if (not authority or authority['study_path'] != STUDY_PATH
                or authority['study_sha256'] != STUDY_SHA or authority['cohort'] != 'asm01_native_memory_v4'
                or authority['study_terminal'] or authority['program_terminal'] or authority['study_expired']
                or authority['registration_attempts_used'] != 0):
            raise ValueError('C_authority_scope')
        effective_deadline = authority['effective_budget_deadline_at']
        receipt.update(C_program_id=authority['program_id'],
                       C_effective_budget_deadline_at=effective_deadline,
                       C_liability_seconds=authority['historical_liability_seconds'],
                       C_registration_attempts_used_at_intake=0)
        _deadline(study, effective_deadline)
        receipt['source_binding_sha256'] = _source_binding(root, study)
        rules = task['intake']
        if (rules['manifest'] != MANIFEST_PATH or rules['output'] != DATASET_PATH
                or rules['publisher_sha256'] != PUBLISHER_SHA):
            raise ValueError('frozen_intake_binding')
        receipt.update(publisher_sha256=PUBLISHER_SHA, license='CC BY4.0',
                       attribution='Baruah and Hazarika(2015), UCI, DOI10.24432/C50C8Q; native instance memory, not OCR.',
                       within_identity_views_are_dependent=True,
                       no_character_labels_or_Data_Table_read_by_methods=True,
                       no_archive_reacquisition=True, new_download_bytes=0)
        before = shutil.disk_usage(root).free
        receipt['free_space_before_bytes'] = before
        if before - rules['maximum_two_root_total_footprint_bytes'] < rules['minimum_free_bytes_after_operation']:
            raise ValueError('disk_floor')
        if sha256_file(local_path(root, PUBLISHER_PATH)) != PUBLISHER_SHA:
            raise ValueError('publisher_binding')
        phase = 'historical_binding'
        historical = {}
        for name in ('complete_lexical_inventory', 'old75_intake', 'latest_numeric_intake', 'signed_lexical_diagnosis'):
            item = task['prior_exposure'][name]
            path = local_path(root, item['path'])
            if sha256_file(path) != item['sha256']:
                raise ValueError(phase)
            historical[name] = load_json(path)
        proof = rules['metadata_proof']
        if sha256_file(local_path(root, proof['path'])) != proof['sha256']:
            raise ValueError(phase)
        metadata = load_json(root / proof['path'])
        if (metadata.get('complete_metadata_validated_before_payload') is not True
                or metadata.get('files') != 1830 or metadata.get('native_payloads_read') != 0):
            raise ValueError(phase)
        inventory = historical['complete_lexical_inventory']
        if inventory.get('complete') is not True or inventory.get('inventoried_files') != 1830:
            raise ValueError(phase)
        old = historical['old75_intake']
        if (old.get('complete') is not False or old.get('native_files_attempted') != 75
                or old.get('native_files_converted') != 74 or old.get('D_samples_opened') != 0):
            raise ValueError(phase)
        phase = 'metadata'
        listing = local_path(root, rules['listing'])
        if sha256_file(listing) != rules['listing_sha256']:
            raise ValueError(phase)
        members = screen_members(local_path(root, rules['source_directory']), listing.read_text(encoding='ascii'))
        receipt['all1830_metadata_validated_before_bytes'] = True
        phase = 'collection'

        def read(path):
            _deadline(study, effective_deadline)
            checked = local_path(root, path.relative_to(root))
            if not checked.is_file() or checked.stat().st_size > rules['per_file_bytes_cap']:
                raise ValueError('member_changed_before_read')
            return path.read_bytes()

        arrays, hashes = collect(members, inventory['sample_sha256'], old['attempted_sample_text_sha256'],
                                  historical['latest_numeric_intake']['native_intake'], receipt,
                                  reader=read, progress=persist)
        phase = 'publication'
        _deadline(study, effective_deadline)
        receipt['full_intake_wall_seconds'] = time.perf_counter() - started
        publish(root, arrays, hashes, receipt, owned_manifest=True)
    except BaseException as error:
        receipt.update(complete=False, error_category=receipt.get('error_category') or phase,
                       error_type=type(error).__name__)
    finally:
        receipt.update(full_intake_wall_seconds=time.perf_counter() - started,
                       free_space_after_bytes=shutil.disk_usage(root).free)
        atomic_write_json(manifest, receipt, compact=True)
        print(json.dumps({key: receipt.get(key) for key in
                          ('complete', 'native_files_attempted', 'native_files_converted', 'validated_files',
                           'old74_compared', 'previous1171_compared', 'D_samples_opened',
                           'current_sample', 'error_category', 'error_type', 'dataset_sha256',
                           'full_intake_wall_seconds')}, sort_keys=True), flush=True)
    return 0 if receipt['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
