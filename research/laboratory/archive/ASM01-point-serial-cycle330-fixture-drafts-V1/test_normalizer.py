"""The single frozen38-case synthetic conformance matrix; no native intake."""
import ast
import builtins
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import nextai_autoresearch
from nextai_autoresearch.asm01_task_v4 import parse_native_sample as old_parse
from nextai_autoresearch.asm01_task import transform
from nextai_autoresearch.utils import load_json, sha256_file

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = Path(__file__).with_name('normalizer.py')
spec = importlib.util.spec_from_file_location('frozen_serial_normalizer', MODULE_PATH)
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
PLAN_PATH = ROOT / 'research/plans/ASM01-POINT-SERIAL-PREPARATION-V1.json'
PLAN_SHA = '679a82220eeb6c0998038ebdbefbe9b2a988ffe2e4e48e974ce46d6ba48950db'
POINTS = [(10*i, i*i) for i in range(8)]
SECOND = [(70, 49)] + [(200+10*i, 100+i*i) for i in range(1, 8)]


def release(count=1, groups=None):
    groups = groups if groups is not None else {1: POINTS}
    rows = ['CHARACTER_NAME: synthetic', f'STROKE_COUNT: {count}', 'X Y STYLUS_STATE STROKE']
    for serial in range(1, count+1):
        rows.append('PEN_DOWN')
        rows += [f'{x} {y} 1 {serial}' for x, y in groups.get(serial, [])]
        rows.append('PEN_UP 0')
    rows.append('END_CHARACTER: synthetic')
    return ('\n'.join(rows)+'\n').encode('ascii')


def rows_payload(rows):
    return ('\n'.join(rows)+'\n').encode('ascii')


def point_tokens(payload):
    return [row.split() for row in payload.decode('ascii').splitlines()[3:-1] if not row.startswith('PEN_')]


BASE = release()
MULTI = release(2, {1: POINTS, 2: SECOND})
whitespace = MULTI.decode().splitlines()
for index, row in enumerate(whitespace):
    fields = row.split()
    if len(fields) == 4 and fields[0].isdigit():
        whitespace[index] = '\t  '.join([fields[0], fields[1], '01', '0'+fields[3]])
misplaced = BASE.decode().splitlines()
misplaced.remove('PEN_UP 0')
misplaced.insert(8, 'PEN_UP 0')
missing = [r for r in MULTI.decode().splitlines() if not r.startswith('PEN_')]
repeated = BASE.replace(b'PEN_DOWN\n', b'PEN_DOWN\nPEN_DOWN\n', 1)
duplicates = release(2, {1: POINTS[:2]+[POINTS[1]]+POINTS[2:], 2: SECOND})
ACCEPT = [
 ('canonical-single', BASE),
 ('canonical-multi-whitespace-leading-zero-metadata', rows_payload(whitespace)),
 ('misplaced-release', rows_payload(misplaced)),
 ('missing-markers', rows_payload(missing)),
 ('repeated-down', repeated),
 ('leading-middle-trailing-empty-ids', release(5, {2: POINTS, 4: SECOND})),
 ('literal-zero-alias', BASE.replace(b'0 0 1 1', b'-0 -0 1 1', 1)),
 ('duplicates-within-and-across-strokes', duplicates),
]


@pytest.mark.parametrize('identity,payload', ACCEPT, ids=[v[0] for v in ACCEPT])
def test_accept(identity, payload):
    output = normalizer.normalize_release_bytes(payload)
    original = point_tokens(payload)
    expected = [[('0' if token == '-0' else token) if j < 2 else token for j, token in enumerate(row)] for row in original]
    assert point_tokens(output) == expected
    count = int(payload.decode().splitlines()[1].split(':')[1])
    assert output.splitlines().count(b'PEN_DOWN') == count
    assert output.splitlines().count(b'PEN_UP') == count
    assert len(output) <= 262144
    actual = old_parse(output)
    for view in ('write', 'nominal', 'adverse'):
        assert transform(actual, view).shape == (64,)
    if identity in ('canonical-single', 'canonical-multi-whitespace-leading-zero-metadata', 'leading-middle-trailing-empty-ids', 'duplicates-within-and-across-strokes'):
        np.testing.assert_array_equal(actual, old_parse(payload))


misplaced_header = BASE.decode().splitlines()
misplaced_header[2], misplaced_header[3] = misplaced_header[3], misplaced_header[2]
REJECT = [
 ('missing-header', BASE.replace(b'X Y STYLUS_STATE STROKE\n', b'')),
 ('misplaced-header', rows_payload(misplaced_header)),
 ('duplicate-header', BASE.replace(b'PEN_DOWN\n', b'X Y STYLUS_STATE STROKE\nPEN_DOWN\n', 1)),
 ('malformed-header', BASE.replace(b'X Y STYLUS_STATE STROKE', b'Y X STYLUS_STATE STROKE')),
 ('stroke-count-zero', BASE.replace(b'STROKE_COUNT: 1', b'STROKE_COUNT: 0')),
 ('stroke-count-negative', BASE.replace(b'STROKE_COUNT: 1', b'STROKE_COUNT: -1')),
 ('serial-zero', BASE.replace(b'0 0 1 1', b'0 0 1 0', 1)),
 ('serial-out-of-range', BASE.replace(b'0 0 1 1', b'0 0 1 2', 1)),
 ('serial-decrease', MULTI.replace(b'0 0 1 1', b'0 0 1 2', 1)),
 ('state-zero', BASE.replace(b'0 0 1 1', b'0 0 0 1', 1)),
 ('negative-x', BASE.replace(b'0 0 1 1', b'-1 0 1 1', 1)),
 ('negative-y', BASE.replace(b'0 0 1 1', b'0 -1 1 1', 1)),
 ('plus-x', BASE.replace(b'0 0 1 1', b'+0 0 1 1', 1)),
 ('negative-double-zero', BASE.replace(b'0 0 1 1', b'0 -00 1 1', 1)),
 ('decimal-y', BASE.replace(b'0 0 1 1', b'0 0.0 1 1', 1)),
 ('unknown-row', BASE.replace(b'PEN_DOWN\n', b'UNKNOWN_ROW\nPEN_DOWN\n', 1)),
 ('point-arity', BASE.replace(b'0 0 1 1', b'0 0 1', 1)),
 ('down-extra-operand', BASE.replace(b'PEN_DOWN\n', b'PEN_DOWN 1\n', 1)),
 ('up-wrong-release', BASE.replace(b'PEN_UP 0\n', b'PEN_UP 1\n', 1)),
 ('too-few-point-rows', release(1, {1: POINTS[:3]})),
]


@pytest.mark.parametrize('identity,payload', REJECT, ids=[v[0] for v in REJECT])
def test_reject(identity, payload):
    with pytest.raises(ValueError):
        normalizer.normalize_release_bytes(payload)


CAPS = [
 ('wrong-type', bytearray(BASE)),
 ('oversize-input', b'x'*262145),
 ('non-ascii', BASE.replace(b'synthetic', b'\xc3\xa9', 1)),
 ('oversize-normalized', BASE.replace(b'STROKE_COUNT: 1', b'STROKE_COUNT: 20000')),
]


@pytest.mark.parametrize('identity,payload', CAPS, ids=[v[0] for v in CAPS])
def test_caps(identity, payload):
    with pytest.raises(ValueError):
        normalizer.normalize_release_bytes(payload)


def test_coordinate_conversion_trap(monkeypatch):
    coordinates = {'1234567', '7654321'}
    def guarded_int(value):
        assert value not in coordinates, 'Coordinate numeric conversion forbidden'
        return builtins.int(value)
    monkeypatch.setattr(normalizer, 'int', guarded_int, raising=False)
    payload = release(1, {1: [(1234567, 7654321)]*8})
    assert point_tokens(normalizer.normalize_release_bytes(payload)) == point_tokens(payload)


def test_old_accepted_arrays_and_all_three_views():
    payload = release(5, {2: POINTS[:2]+[POINTS[1]]+POINTS[2:], 4: SECOND})
    before, after = old_parse(payload), old_parse(normalizer.normalize_release_bytes(payload))
    # Independent expected row count: one intra-stroke duplicate removed; cross-stroke identical point retained.
    assert before.shape == after.shape == (16, 2)
    assert before.dtype == after.dtype == np.float32
    np.testing.assert_array_equal(before[7], before[8])
    np.testing.assert_array_equal(before, after)
    for view in ('write', 'nominal', 'adverse'):
        np.testing.assert_array_equal(transform(before, view), transform(after, view))


def test_all_parent_protected_files_unchanged():
    manifest = load_json(ROOT / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1/research/eval_manifest.json')
    assert not any('asm01_native_v1/' in name for name in manifest['files'])
    for name, digest in manifest['files'].items():
        assert sha256_file(ROOT / name) == digest, name
    parent = load_json(ROOT / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1/parent-bindings.json')
    for name, digest in parent['files'].items():
        assert sha256_file(ROOT / name) == digest, name


def test_pure_imports_and_no_file_model_access():
    tree = ast.parse(MODULE_PATH.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name == 're' for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module == '__future__'
        if isinstance(node, ast.Name):
            assert node.id not in {'open', 'exec', 'eval', 'float', 'Decimal', 'Path', 'numpy', 'np', 'torch', 'requests', 'subprocess'}


def test_no_native_authority_or_scoring():
    plan = load_json(PLAN_PATH)
    assert plan['execution_authority'] and not plan['native_execution_authority']
    assert plan['fit_seconds_cap'] == plan['EXP_cap'] == plan['registration_cap'] == 0
    assert plan['known_exposures']['new_native_bytes_this_scope'] == 0
    assert not plan['known_exposures']['old74_array_hashes_persisted']
    assert plan['budget_at_freeze']['protected_future_compute_seconds'] == 47000
    assert plan['budget_at_freeze']['protected_future_registration_attempts'] == 7


def test_exact_plan_source_fixture_bindings():
    assert ROOT.name == 'NEXTAI-VALIDATION-20261002'
    assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(ROOT / 'src')
    assert sha256_file(PLAN_PATH) == PLAN_SHA
    binding = load_json(ROOT / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V1.json')
    assert binding['plan_sha256'] == PLAN_SHA
    assert binding['source_sha256'] == sha256_file(MODULE_PATH)
    assert binding['fixture_sha256'] == sha256_file(Path(__file__))
    cases = load_json(PLAN_PATH)['frozen_cases']
    assert [v[0] for v in ACCEPT] == cases['accept']
    assert [v[0] for v in REJECT] == cases['reject']
    assert [v[0] for v in CAPS] == cases['caps']
    assert len(ACCEPT)+len(REJECT)+len(CAPS)+len(cases['invariants']) == cases['total'] == 38
