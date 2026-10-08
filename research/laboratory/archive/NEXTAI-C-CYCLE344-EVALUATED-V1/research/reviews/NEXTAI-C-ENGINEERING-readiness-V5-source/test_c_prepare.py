"""Public synthetic prerequisites for the C preparation controller.

These are controller fixtures, not native intake or a scientific dry-run. The
shared builder itself is exercised separately by the engineering full-path
fixtures. Every receipt and ledger written here belongs to pytest's temporary
root; the canonical wallet and data are never touched.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import re

import pytest

from nextai_autoresearch import ledger, research_program_c as c, runner
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file


ROOT = project_root()
_SPEC = importlib.util.spec_from_file_location("c_prepare_synthetic_fixture", ROOT / "scripts/prepare_c_science.py")
prepare = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prepare)
NATIVE = "research/data_manifests/ASM01-C-ACQUISITION-V1.json"
CONFORMANCE = "research/checks/public-conformance.json"
FREEZE = "research/reviews/NEXTAI-C-SOURCE-DATA-FREEZE-V1.json"
PREFLIGHT = "research/laboratory/preflight_certificate.json"
SOURCE_PROOF = "tests/public-conformance-source.py"
RAW_PROOF = "research/checks/public-conformance-raw.xml"
COHORT = "asm01_native_memory_v4"
COUNTS = {"native_files_attempted": 1830, "native_files_converted": 1830,
          "validated_files": 1830, "old74_compared": 74,
          "previous1171_compared": 1171, "D_samples_opened": 915}
MATRIX = {"knowledge_sizes": [16, 32, 64], "reasoning_depths": [1, 2, 3],
          "queries_per_cell": 128,
          "seed_policy": {"method": "runner_random_v1", "count": 5,
                          "minimum": 1_000_000, "maximum": 2_147_483_647}}


def _bytes(root, relative, payload=b"public synthetic metadata\n"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256_file(path)


def _ledger_hashes(root):
    return {name: sha256_file(root / name) if (root / name).is_file() else None
            for name in prepare.LEDGERS}


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    from test_research_program_c import _fixture

    root, clock, contract, study = _fixture(tmp_path, monkeypatch)
    study.update(cohort=COHORT, stage="transfer_family_2_screen", matrix=copy.deepcopy(MATRIX),
                 study_deadline_at="2026-10-08T11:32:00Z")
    atomic_write_json(root / prepare.STUDY, study)
    monkeypatch.setattr(prepare, "STUDY_SHA", sha256_file(root / prepare.STUDY))
    config = root / "config/research.toml"
    source = config.read_text(encoding="utf-8").replace("c_engineering_fixture_v1", COHORT)
    config.write_text(source, encoding="utf-8")
    c.activate(root)
    c.freeze_scientific_study(root)
    source = re.sub(r'(\[research_program_c\]\s*study_path\s*=\s*)"[^"]*"',
                    lambda match: match[1] + '"' + prepare.STUDY + '"', source)
    config.write_text(source, encoding="utf-8")
    dataset = "research/data/asm01_c_v1/screen.npz"
    digest = _bytes(root, dataset, b"This is a public synthetic fixture, never a native array.")
    native = {**COUNTS, "complete": True, "study_sha256": prepare.STUDY_SHA,
              "task_contract_sha256": "66cb7521a72e3485c8738d0f46cfe64bad3d773755fcc15c5db23a4cde9afa85",
              "no_future_writer_coordinates_read": True,
              "dataset_path": dataset, "dataset_sha256": digest}
    atomic_write_json(root / NATIVE, native)
    source_digest = _bytes(root, SOURCE_PROOF, b"# Public synthetic source identity only.\n")
    raw_digest = _bytes(root, RAW_PROOF, b"<testsuite name='public-synthetic' tests='1'/>\n")
    atomic_write_json(root / CONFORMANCE, {**prepare.binding(root), "status": "PASS",
                                          "all_required_conformance_passed": True,
                                          "source_files": {SOURCE_PROOF: source_digest},
                                          "evidence_files": {RAW_PROOF: raw_digest},
                                          "fixture_only": True, "native_payloads_read": 0})
    atomic_write_json(root / "research/eval_manifest.json", {"fixture_only": True, "protocol_version": 3})
    atomic_write_json(root / "research/reviews/ASM01-C-source-binding-V1.json", {"fixture_only": True})
    native.update(task_contract_sha256=prepare.TASK_SHA, publisher_sha256=prepare.PUBLISHER_SHA,
                  C_program_id=c.PROGRAM_ID,
                  source_binding_sha256=sha256_file(root / prepare.SOURCE_BINDING))
    atomic_write_json(root / NATIVE, native)
    atomic_write_json(root / PREFLIGHT, {"status": "PASS", "fixture_only": True})
    _bytes(root, "research/plans/public-plan.json")
    (root / "research/tmp").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prepare, "verify_manifest", lambda base: {"ok": True, "fixture_only": True})

    def preflight(base):
        if load_json(base / PREFLIGHT).get("status") != "PASS":
            raise ValueError("Synthetic preflight failure")
        return {"ok": True, "fixture_only": True}

    monkeypatch.setattr(prepare, "verify_preflight_certificate", preflight)
    baseline_calls = []
    monkeypatch.setattr(prepare, "verify_required_baselines",
                        lambda plan, base, *, run_tests: baseline_calls.append((copy.deepcopy(plan), run_tests)))
    plan = {"benchmark": COHORT,
            "matrix": copy.deepcopy(MATRIX),
            "research_program_protocol": {"program_id": c.PROGRAM_ID,
                                          "program_contract_sha256": c.CONTRACT_SHA256,
                                          "study_path": prepare.STUDY,
                                          "study_sha256": prepare.STUDY_SHA,
                                          "registration_ticket": 1}}
    calls = []

    def synthetic_builder(base):
        calls.append(base)
        assert base == root
        assert c.status(base)["registration_attempts_used"] == 0
        assert not c.status(base)["scoring_authorized"]
        assert c.prospective_admission_problems(base) == []
        return copy.deepcopy(plan)

    monkeypatch.setattr(prepare, "dry_run_plan", synthetic_builder)
    return root, clock, plan, calls, baseline_calls


def _inputs(prepared):
    root = prepared[0]
    prepare.input_receipt(root, CONFORMANCE)
    return root


def _dry(prepared):
    root = _inputs(prepared)
    prepare.dry_receipt(root)
    return root


def test_complete_inputs_and_actual_controller_dry_proof_release_only_exact_unused_scope(prepared, monkeypatch):
    root, _, plan, calls, baseline_calls = prepared
    canonical_before = _ledger_hashes(ROOT)
    root = _inputs(prepared)
    before = _ledger_hashes(root)

    def forbidden(*args, **kwargs):
        pytest.fail("A preparation dry-run must not realize scoring entropy or consume a ticket")

    monkeypatch.setattr(runner.secrets, "SystemRandom", forbidden)
    monkeypatch.setattr(runner.secrets, "token_hex", forbidden)
    monkeypatch.setattr(runner, "_realize_evaluation_matrix", forbidden)
    monkeypatch.setattr(c, "reserve_registration", forbidden)
    monkeypatch.setattr(ledger, "register_plan", forbidden)
    prepare.dry_receipt(root)
    dry = load_json(root / prepare.DRY)
    assert dry["plan"] == plan and "seeds" not in dry["plan"]["matrix"]
    assert dry["private_entropy_realized"] is False
    assert dry["ledger_sha256_before"] == dry["ledger_sha256_after"] == before
    assert _ledger_hashes(root) == before
    assert calls == [root] and not c.status(root)["scoring_authorized"]
    prepare.ready_receipt(root)
    ready = load_json(root / prepare.READY)
    assert ready["gate_evidence"]["same_builder_dry_run"]["sha256"] == sha256_file(root / prepare.DRY)
    assert set(ready["gate_evidence"]) == set(c.RELEASE_CHECKS)
    assert baseline_calls == [(plan, False)]
    assert c.status(root)["scoring_authorized"] and c.status(root)["registration_attempts_used"] == 0
    assert _ledger_hashes(ROOT) == canonical_before


@pytest.mark.parametrize("alter", ["missing", "complete", *COUNTS, "study", "future", "dataset",
                                   "task", "dataset-path", "publisher", "C-program", "source-binding", "source-file"],
                         ids=["missing", "incomplete", "attempted", "converted", "validated",
                              "old74", "previous1171", "D915", "study", "future", "dataset",
                              "task", "dataset-path", "publisher", "C-program", "source-binding", "source-file"])
def test_missing_partial_or_changed_native_proof_cannot_mark_inputs(prepared, alter):
    root = prepared[0]
    native = load_json(root / NATIVE)
    if alter == "missing":
        (root / NATIVE).unlink()
    else:
        if alter == "complete":
            native[alter] = False
        elif alter in COUNTS:
            native[alter] -= 1
        elif alter == "study":
            native["study_sha256"] = "0" * 64
        elif alter == "future":
            native["no_future_writer_coordinates_read"] = False
        elif alter == "dataset":
            _bytes(root, native["dataset_path"], b"Changed public synthetic fixture")
        elif alter == "source-file":
            _bytes(root, prepare.SOURCE_BINDING, b"Changed public synthetic source binding")
        else:
            field = {"task": "task_contract_sha256", "dataset-path": "dataset_path",
                     "publisher": "publisher_sha256", "C-program": "C_program_id",
                     "source-binding": "source_binding_sha256"}[alter]
            native[field] = "foreign"
        atomic_write_json(root / NATIVE, native)
    before = _ledger_hashes(root)
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        prepare.input_receipt(root, CONFORMANCE)
    assert not (root / prepare.INPUTS).exists() and not (root / FREEZE).exists()
    assert _ledger_hashes(root) == before


@pytest.mark.parametrize("alter", ["missing", "status", "partial", "integrity", "preflight"],
                         ids=["missing", "failed", "partial", "integrity", "preflight"])
def test_all_conformance_and_integrity_preflight_are_required_before_inputs(prepared, monkeypatch, alter):
    root = prepared[0]
    if alter == "missing":
        (root / CONFORMANCE).unlink()
    elif alter in {"status", "partial"}:
        value = load_json(root / CONFORMANCE)
        value["status" if alter == "status" else "all_required_conformance_passed"] = "FAIL" if alter == "status" else False
        atomic_write_json(root / CONFORMANCE, value)
    elif alter == "integrity":
        monkeypatch.setattr(prepare, "verify_manifest", lambda _: {"ok": False})
    else:
        atomic_write_json(root / PREFLIGHT, {"status": "FAIL"})
    before = _ledger_hashes(root)
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare.input_receipt(root, CONFORMANCE)
    assert not (root / prepare.INPUTS).exists() and not (root / FREEZE).exists()
    assert _ledger_hashes(root) == before


@pytest.mark.parametrize("alter", [
    "program", "contract", "study-path", "study-sha", "cohort", "stage",
    "source-map-missing", "source-empty", "source-file-missing", "source-bytes", "source-sha", "source-escape",
    "evidence-map-missing", "evidence-empty", "evidence-file-missing", "evidence-bytes", "evidence-sha", "evidence-escape"],
    ids=["program", "contract", "study-path", "study-sha", "cohort", "stage",
         "source-map-missing", "source-empty", "source-file-missing", "source-bytes", "source-sha", "source-escape",
         "evidence-map-missing", "evidence-empty", "evidence-file-missing", "evidence-bytes", "evidence-sha", "evidence-escape"])
def test_foreign_or_incomplete_conformance_source_and_raw_evidence_prevents_inputs(prepared, alter):
    root = prepared[0]
    document = load_json(root / CONFORMANCE)
    context_fields = {"program": "program_id", "contract": "contract_sha256", "study-path": "study_path",
                      "study-sha": "study_sha256", "cohort": "cohort", "stage": "stage"}
    if alter in context_fields:
        document[context_fields[alter]] = "foreign"
    else:
        source = alter.startswith("source-")
        field, path = ("source_files", SOURCE_PROOF) if source else ("evidence_files", RAW_PROOF)
        operation = alter.split("-", 1)[1]
        if operation == "map-missing":
            del document[field]
        elif operation == "empty":
            document[field] = {}
        elif operation == "file-missing":
            (root / path).unlink()
        elif operation == "bytes":
            _bytes(root, path, b"Changed public synthetic proof bytes")
        elif operation == "sha":
            document[field][path] = "0" * 64
        else:
            document[field] = {"../../outside-public-fixture": "0" * 64}
    atomic_write_json(root / CONFORMANCE, document)
    before = _ledger_hashes(root)
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare.input_receipt(root, CONFORMANCE)
    assert not (root / prepare.INPUTS).exists() and not (root / FREEZE).exists()
    assert _ledger_hashes(root) == before


def test_protocol3_binds_actual_laboratory_certificate_without_legacy_fallback(prepared):
    root = prepared[0]
    # A plausible legacy certificate must not become the protocol3 proof.
    legacy = "research/checks/preflight_certificate.json"
    atomic_write_json(root / legacy, {"status": "PASS", "fixture_only": True, "legacy": True})
    _inputs(prepared)
    proof = load_json(root / prepare.INPUTS)["gate_evidence"]["preflight"]
    assert proof == {"path": PREFLIGHT, "sha256": sha256_file(root / PREFLIGHT)}
    assert proof["sha256"] != sha256_file(root / legacy)
    prepare.dry_receipt(root)
    prepare.ready_receipt(root)
    assert load_json(root / prepare.READY_CHECK)["preflight"] == proof
    assert load_json(root / prepare.READY)["gate_evidence"]["preflight"] == proof


@pytest.mark.parametrize("field", ["study_path", "study_sha256", "cohort", "program_terminal",
                                   "study_terminal", "study_expired", "registration_attempts_used", "stage"],
                         ids=["path", "sha", "cohort", "terminal", "study-terminal", "expired", "used-ticket", "stage"])
def test_exact_live_unexpired_unused_scope_is_required_before_any_receipt(prepared, monkeypatch, field):
    root = prepared[0]
    value = c.status(root)
    value[field] = True if field in {"program_terminal", "study_terminal", "study_expired"} else (
        1 if field == "registration_attempts_used" else "foreign")
    monkeypatch.setattr(c, "status", lambda _: value)
    before = _ledger_hashes(root)
    with pytest.raises(ValueError):
        prepare.input_receipt(root, CONFORMANCE)
    assert not (root / prepare.INPUTS).exists() and not (root / FREEZE).exists()
    assert _ledger_hashes(root) == before


def test_absent_C_authority_cannot_create_any_success_evidence(prepared, monkeypatch):
    root = prepared[0]
    monkeypatch.setattr(c, "status", lambda _: None)
    before = _ledger_hashes(root)
    with pytest.raises(ValueError):
        prepare.input_receipt(root, CONFORMANCE)
    assert not (root / prepare.INPUTS).exists() and not (root / FREEZE).exists()
    assert _ledger_hashes(root) == before


@pytest.mark.parametrize("relative", list(prepare.LEDGERS),
                         ids=["events", "C-events", "registry", "plan-status", "hypothesis", "experiments", "state"])
def test_mutated_ledger_prevents_PASS_dry_receipt_without_erasing_failure(prepared, monkeypatch, relative):
    root = _inputs(prepared)
    original = prepare.dry_run_plan
    before = _ledger_hashes(root)

    def mutating(base):
        plan = original(base)
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as stream:
            stream.write(b"synthetic forbidden mutation\n")
        return plan

    monkeypatch.setattr(prepare, "dry_run_plan", mutating)
    with pytest.raises(ValueError):
        prepare.dry_receipt(root)
    assert not (root / prepare.DRY).exists()
    assert _ledger_hashes(root)[relative] != before[relative]
    assert (root / relative).read_bytes().endswith(b"synthetic forbidden mutation\n")


@pytest.mark.parametrize("alter", ["new-plan", "runtime", "rename", "remove", "seeds", "raise"],
                         ids=["new-plan", "runtime", "rename", "remove", "seeds", "builder-error"])
def test_mutated_file_names_or_seed_realization_never_receive_PASS(prepared, monkeypatch, alter):
    root = _inputs(prepared)
    original = prepare.dry_run_plan

    def bad_builder(base):
        plan = original(base)
        if alter == "new-plan":
            _bytes(root, "research/plans/EXP-SYNTHETIC.json")
        elif alter == "runtime":
            _bytes(root, "research/tmp/public-runtime.json")
        elif alter == "rename":
            (root / "research/plans/public-plan.json").rename(root / "research/plans/renamed.json")
        elif alter == "remove":
            (root / "research/plans/public-plan.json").unlink()
        elif alter == "seeds":
            plan["matrix"]["seeds"] = [17]
        else:
            raise RuntimeError("Synthetic shared-builder rejection")
        return plan

    before = _ledger_hashes(root)
    monkeypatch.setattr(prepare, "dry_run_plan", bad_builder)
    with pytest.raises((ValueError, RuntimeError)):
        prepare.dry_receipt(root)
    assert not (root / prepare.DRY).exists()
    assert _ledger_hashes(root) == before and c.status(root)["registration_attempts_used"] == 0


@pytest.mark.parametrize("alter", ["missing", "status", "ticket", "program", "contract", "study-path",
                                   "study-sha", "cohort", "stage", "entropy", "names", "ledger", "seeds"],
                         ids=["missing", "failed", "ticket", "program", "contract", "study-path",
                              "study-sha", "cohort", "stage", "entropy", "names", "ledger", "seeds"])
def test_readiness_requires_complete_actual_dry_proof_for_same_scope(prepared, alter):
    root = _dry(prepared)
    if alter == "missing":
        (root / prepare.DRY).unlink()
    else:
        dry = load_json(root / prepare.DRY)
        key = {"status": "status", "ticket": "scientific_registration_attempts_used",
               "program": "program_id", "contract": "contract_sha256", "study-path": "study_path",
               "study-sha": "study_sha256", "cohort": "cohort", "stage": "stage",
               "entropy": "private_entropy_realized", "names": "plan_and_runtime_file_names_unchanged"}.get(alter)
        if alter == "ledger":
            dry["ledger_sha256_after"][prepare.LEDGERS[0]] = "0" * 64
        elif alter == "seeds":
            dry["plan"]["matrix"]["seeds"] = [19]
        else:
            dry[key] = (1 if alter == "ticket" else True if alter == "entropy" else
                        False if alter == "names" else "foreign")
        atomic_write_json(root / prepare.DRY, dry)
    before = _ledger_hashes(root)
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare.ready_receipt(root)
    assert not (root / prepare.READY).exists() and not (root / prepare.READY_CHECK).exists()
    assert _ledger_hashes(root) == before and not c.status(root)["scoring_authorized"]


@pytest.mark.parametrize("alter", [
    "ledger-before-missing", "ledger-after-missing", "ledger-before-keys", "ledger-after-keys",
    "ledger-before-extra", "ledger-after-extra", "ledger-sha-malformed", "ledger-sha-type",
    "ledger-map-type", "current-ledger", "names-before-missing", "names-after-missing",
    "names-before-type", "names-after-type", "names-mismatch", "current-names", "benchmark",
    "protocol-missing", "protocol-type", "protocol-program", "protocol-contract",
    "protocol-study-path", "protocol-study-sha", "matrix-missing", "matrix-type", "policy-missing",
    "ticket-bool", "entropy-number", "names-flag-number"], ids=[
    "ledger-before-missing", "ledger-after-missing", "ledger-before-keys", "ledger-after-keys",
    "ledger-before-extra", "ledger-after-extra", "ledger-sha-malformed", "ledger-sha-type",
    "ledger-map-type", "current-ledger", "names-before-missing", "names-after-missing",
    "names-before-type", "names-after-type", "names-mismatch", "current-names", "benchmark",
    "protocol-missing", "protocol-type", "protocol-program", "protocol-contract",
    "protocol-study-path", "protocol-study-sha", "matrix-missing", "matrix-type", "policy-missing",
    "ticket-bool", "entropy-number", "names-flag-number"])
def test_malformed_or_stale_recorded_dry_state_cannot_become_ready(prepared, alter):
    root = _dry(prepared)
    dry = load_json(root / prepare.DRY)
    before_key, after_key = "ledger_sha256_before", "ledger_sha256_after"
    names_before, names_after = "plan_and_runtime_file_names_before", "plan_and_runtime_file_names_after"
    if alter in {"ledger-before-missing", "ledger-after-missing"}:
        del dry[before_key if alter == "ledger-before-missing" else after_key]
    elif alter in {"ledger-before-keys", "ledger-after-keys"}:
        del dry[before_key if alter == "ledger-before-keys" else after_key][prepare.LEDGERS[0]]
    elif alter in {"ledger-before-extra", "ledger-after-extra"}:
        dry[before_key if alter == "ledger-before-extra" else after_key]["research/foreign-ledger.jsonl"] = "a" * 64
    elif alter in {"ledger-sha-malformed", "ledger-sha-type"}:
        # Equal malformed maps must fail even without a before/after difference.
        invalid = "not-a-sha256" if alter == "ledger-sha-malformed" else 7
        dry[before_key][prepare.LEDGERS[0]] = invalid
        dry[after_key][prepare.LEDGERS[0]] = invalid
    elif alter == "ledger-map-type":
        dry[before_key] = dry[after_key] = []
    elif alter == "current-ledger":
        path = root / "research/experiments.tsv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.write(b"public synthetic external ledger drift\n")
    elif alter in {"names-before-missing", "names-after-missing"}:
        del dry[names_before if alter == "names-before-missing" else names_after]
    elif alter in {"names-before-type", "names-after-type"}:
        dry[names_before if alter == "names-before-type" else names_after] = "not-a-list"
    elif alter == "names-mismatch":
        dry[names_after] = [*dry[names_before], "research/tmp/foreign.json"]
    elif alter == "current-names":
        _bytes(root, "research/tmp/public-external-drift.json")
    elif alter == "benchmark":
        dry["plan"]["benchmark"] = "asm01_native_memory_v3"
    elif alter == "protocol-missing":
        del dry["plan"]["research_program_protocol"]
    elif alter == "protocol-type":
        dry["plan"]["research_program_protocol"] = []
    elif alter.startswith("protocol-"):
        key = {"protocol-program": "program_id", "protocol-contract": "program_contract_sha256",
               "protocol-study-path": "study_path", "protocol-study-sha": "study_sha256"}[alter]
        dry["plan"]["research_program_protocol"][key] = "foreign"
    elif alter == "matrix-missing":
        del dry["plan"]["matrix"]
    elif alter == "matrix-type":
        dry["plan"]["matrix"] = []
    elif alter == "policy-missing":
        del dry["plan"]["matrix"]["seed_policy"]
    elif alter == "ticket-bool":
        dry["scientific_registration_attempts_used"] = False
    elif alter == "entropy-number":
        dry["private_entropy_realized"] = 0
    else:
        dry["plan_and_runtime_file_names_unchanged"] = 1
    atomic_write_json(root / prepare.DRY, dry)
    ledgers = _ledger_hashes(root)
    with pytest.raises(ValueError):
        prepare.ready_receipt(root)
    assert not (root / prepare.READY).exists() and not (root / prepare.READY_CHECK).exists()
    assert _ledger_hashes(root) == ledgers
    assert c.status(root)["registration_attempts_used"] == 0 and not c.status(root)["scoring_authorized"]


@pytest.mark.parametrize("alter", ["inputs", "native", "conformance", "freeze", "preflight", "integrity"],
                         ids=["inputs", "native", "conformance", "freeze", "preflight", "integrity"])
def test_readiness_rechecks_bound_input_hashes_and_preflight(prepared, monkeypatch, alter):
    root = _dry(prepared)
    if alter == "integrity":
        monkeypatch.setattr(prepare, "verify_manifest", lambda _: {"ok": False})
    else:
        relative = {"inputs": prepare.INPUTS, "native": NATIVE, "conformance": CONFORMANCE,
                    "freeze": FREEZE, "preflight": PREFLIGHT}[alter]
        with (root / relative).open("ab") as handle:
            handle.write(b"\n ")
    before = _ledger_hashes(root)
    with pytest.raises(ValueError):
        prepare.ready_receipt(root)
    assert not (root / prepare.READY).exists()
    assert _ledger_hashes(root) == before


@pytest.mark.parametrize("phase", ["inputs", "dry", "ready"], ids=["inputs", "dry", "ready"])
def test_existing_phase_evidence_is_preserved_exclusively(prepared, phase):
    root = prepared[0]
    if phase == "inputs":
        _inputs(prepared)
        operation = lambda: prepare.input_receipt(root, CONFORMANCE)
        paths = [FREEZE, prepare.INPUTS]
    elif phase == "dry":
        _dry(prepared)
        operation = lambda: prepare.dry_receipt(root)
        paths = [prepare.DRY]
    else:
        _dry(prepared)
        prepare.ready_receipt(root)
        operation = lambda: prepare.ready_receipt(root)
        paths = [prepare.READY_CHECK, prepare.READY]
    before = {name: (root / name).read_bytes() for name in paths}
    ledgers = _ledger_hashes(root)
    with pytest.raises((ValueError, FileExistsError)):
        operation()
    assert {name: (root / name).read_bytes() for name in paths} == before
    assert _ledger_hashes(root) == ledgers


def test_exclusive_serialization_failure_retains_partial_and_never_overwrites(tmp_path):
    relative = "research/reviews/public-exclusive.json"
    with pytest.raises(ValueError):
        prepare.exclusive(tmp_path, relative, {"invalid": float("nan")})
    path = tmp_path / relative
    retained = path.read_bytes()
    assert b"PASS" not in retained
    with pytest.raises(FileExistsError):
        prepare.exclusive(tmp_path, relative, {"status": "PASS"})
    assert path.read_bytes() == retained
