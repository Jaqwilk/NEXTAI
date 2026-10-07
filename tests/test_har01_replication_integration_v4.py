"""Focused V4 integration checks using source and synthetic metadata only."""
import ast
import copy
import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch import har01_task as original_task
from nextai_autoresearch import har01_task_v4 as task
from nextai_autoresearch.benchmarks import har01_native_memory_v1 as original_benchmark
from nextai_autoresearch.benchmarks import har01_native_memory_v4 as benchmark
from nextai_autoresearch import research_program
from nextai_autoresearch import integrity
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json, sha256_file


ROOT = Path(__file__).resolve().parents[1]
STUDY_PATH = "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json"
STUDY_SHA = "9cf2153945a322e9c0e47c6d20287a9286e544a62ca0f711b64c797bcb493400"
STUDY = json.loads((ROOT / STUDY_PATH).read_text(encoding="utf-8"))


def test_independent_clone_package_provenance():
    import nextai_autoresearch

    assert ROOT.name == "NEXTAI-VALIDATION-20261002"
    assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(ROOT / "src")


def synthetic_plan():
    plan = json.loads((ROOT / "research/plans/EXP-20261005-0006.json").read_text(encoding="utf-8"))
    plan.update(benchmark=STUDY["cohort"], candidates=copy.deepcopy(STUDY["candidates"]),
                matrix=copy.deepcopy(STUDY["matrix"]))
    plan["research_program_protocol"] = {
        "authority_path": "research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1.json",
        "program_contract_path": STUDY["program_contract_path"],
        "program_contract_sha256": STUDY["program_contract_sha256"],
        "study_path": STUDY_PATH, "study_sha256": STUDY_SHA, "registration_ticket": 2,
        **research_program._study_scope(STUDY)}
    return plan


def test_v4_schema_accepts_frozen_plan_and_rejects_scientific_mutations():
    plan = synthetic_plan()
    assert "seeds" not in plan["matrix"]
    validate_document("experiment_plan", plan, ROOT)
    mutations = [
        (("matrix", "knowledge_sizes", 2), 512),
        (("matrix", "reasoning_depths", 2), 4),
        (("research_program_protocol", "recipe", "alignment_steps"), 2049),
        (("research_program_protocol", "recipe", "dense_set_steps"), 1025),
        (("research_program_protocol", "data", "train_pairs"), 4095),
        (("research_program_protocol", "roles", "har01_source_trained_s0", "seed_index"), 1),
        (("research_program_protocol", "task_contract_path"), "research/plans/HAR01-REPLICATION-TASK-V1.json"),
        (("research_program_protocol", "task_contract_sha256"), "0" * 64),
        (("research_program_protocol", "study_sha256"), "0" * 64),
        (("research_program_protocol", "fit_seconds_total_cap"), 501),
    ]
    for path, replacement in mutations:
        changed = copy.deepcopy(plan)
        target = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = replacement
        with pytest.raises(ValidationError):
            validate_document("experiment_plan", changed, ROOT)


def test_v4_private_intake_and_analysis_imports_are_rejected(tmp_path):
    directory = tmp_path / "src/nextai_autoresearch/candidates"
    directory.mkdir(parents=True)
    config = load_config(ROOT)
    for index, module in enumerate(("har01_task_v4", "har01_analysis_v4")):
        name = f"private_leak_{index}"
        (directory / f"{name}.py").write_text(
            f"from nextai_autoresearch.{module} import *\nclass Candidate: pass\n", encoding="utf-8")
        result = audit_candidate(name, config, tmp_path)
        assert not result.ok and any("evaluator" in problem for problem in result.problems)


def test_exact_45_roles_original_science_and_source_bindings():
    assert sha256_file(ROOT / STUDY_PATH) == STUDY_SHA
    arms = ("source_trained", "source_untrained", "source_shuffled", "source_ridge", "target_dense",
            "target_ridge_pca", "target_kernel", "native_raw", "native_shift")
    expected = [f"har01_{arm}_s{index}" for arm in arms for index in range(5)]
    assert STUDY["candidates"] == expected and len(set(expected)) == 45
    assert STUDY["roles"] == {f"har01_{arm}_s{index}": {"arm": arm, "seed_index": index}
                               for arm in arms for index in range(5)}
    config = load_config(ROOT)
    for candidate in expected:
        result = audit_candidate(candidate, config, ROOT)
        assert result.ok, (candidate, result.problems)
    parent = json.loads((ROOT / STUDY["parent_study_path"]).read_text(encoding="utf-8"))
    for key in ("recipe", "diagnostics", "diagnosis_gates", "reference_gates"):
        assert STUDY[key] == parent[key]
    for relative, digest in STUDY["parent_bindings"].items():
        if relative.startswith(("src/", "scripts/")):
            assert sha256_file(ROOT / relative) == digest, relative
    for name in ("CHANNELS", "arrays_hash", "rng_for", "feature", "transform", "pairs", "Episode",
                 "episode", "prepared_calibration", "training_sets", "episode_hash"):
        assert getattr(task, name) is getattr(original_task, name), name
    assert benchmark.selected is original_benchmark
    assert benchmark.load_unit is task.load_unit
    source_keys = ("src/nextai_autoresearch/har01_task.py", "src/nextai_autoresearch/candidates/har01_core.py",
                   "src/nextai_autoresearch/benchmarks/har01_native_memory_v1.py")
    assert benchmark._PARENT_SOURCES == {key: STUDY["parent_bindings"][key] for key in source_keys}


def test_v4_manifest_dispatch_does_not_mutate_old_cohort(tmp_path, monkeypatch):
    old = tmp_path / "research/data_manifests/HAR01-ACQUISITION-V1.json"
    fresh = tmp_path / task.MANIFEST_PATH
    atomic_write_json(old, {"synthetic": "old"})
    atomic_write_json(fresh, {"synthetic": "fresh"})
    monkeypatch.setattr(benchmark, "project_root", lambda: tmp_path)
    assert benchmark._native_json(old) == {"synthetic": "fresh"}
    assert original_benchmark.load_json(old) == {"synthetic": "old"}
    assert benchmark.BENCHMARK_VERSION == "har01_native_memory_v4"
    assert original_benchmark.BENCHMARK_VERSION == "har01_native_memory_v1"
    assert task.STUDY_PATH == STUDY_PATH
    assert task.TASK_PATH == STUDY["task_contract_path"]


def test_controller_rejects_wrong_clone_and_foreign_package_before_metadata(tmp_path, monkeypatch):
    script = ROOT / "scripts/run_har01_replication_experiment_v3.py"
    spec = importlib.util.spec_from_file_location("_har01_v4_controller_fixture", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def closed(*_args, **_kwargs):
        pytest.fail("Clone-origin guard read metadata before rejecting wrong origin")

    monkeypatch.setattr(module, "sha256_file", closed)
    monkeypatch.setattr(module, "__file__", str(tmp_path / "WRONG-CLONE/scripts/controller.py"))
    with pytest.raises(AssertionError, match="Independent clone"):
        module.main()
    clone = tmp_path / "NEXTAI-VALIDATION-20261002"
    monkeypatch.setattr(module, "__file__", str(clone / "scripts/controller.py"))
    monkeypatch.setattr(module.nextai_autoresearch, "__file__", str(tmp_path / "foreign/package/__init__.py"))
    with pytest.raises(AssertionError):
        module.main()


def test_fresh_units_reject_duplicates_and_bad_nonces_before_history_io(tmp_path, monkeypatch):
    def closed(*_args, **_kwargs):
        pytest.fail("Invalid fresh unit realization read history")

    monkeypatch.setattr(research_program, "load_json", closed)
    seeds, nonces = list(range(100, 105)), [f"{index:064x}" for index in range(5)]
    for bad_seeds, bad_nonces in ((seeds[:4], nonces), ([100] * 5, nonces),
                                  (seeds, nonces[:4]), (seeds, [nonces[0]] * 5),
                                  (seeds, ["not-a-nonce"] + nonces[1:])):
        with pytest.raises(ValueError, match="five independent"):
            research_program.verify_pvm01_fresh_realization(tmp_path, bad_seeds, bad_nonces)


def test_separate_v4_runner_history_branch_rejects_seed_and_nonce_collisions(tmp_path):
    source = (ROOT / "src/nextai_autoresearch/runner.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    common = [node for node in ast.walk(tree) if isinstance(node, ast.If)
              and isinstance(node.test, ast.Compare) and isinstance(node.test.comparators[0], ast.Set)
              and "har01_native_memory_v4" in {item.value for item in node.test.comparators[0].elts
                                              if isinstance(item, ast.Constant)}]
    assert len(common) == 1
    common_source = ast.unparse(common[0])
    assert "Consumed source seed/data collision; no replacement" in common_source
    assert "previous_private['unit_nonces']" in common_source
    assert "previous['matrix']['seeds']" in common_source
    fresh_calls = [node for node in ast.walk(common[0]) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Name) and node.func.id == "verify_pvm01_fresh_realization"]
    assert len(fresh_calls) == 1
    assert {keyword.arg: ast.literal_eval(keyword.value) for keyword in fresh_calls[0].keywords} == {
        "include_latest": True, "include_transport": True, "include_replication": True,
        "include_dense_noise": True, "include_confirmation": True, "include_base_reference": True}
    branches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and ast.unparse(node.test) == "plan['benchmark'] == 'har01_native_memory_v4'"]
    assert len(branches) == 1
    branch = branches[0]
    statements = ast.Module(body=copy.deepcopy(branch.body), type_ignores=[])
    executable = compile(ast.fix_missing_locations(statements), "<synthetic-v4-history-branch>", "exec")
    old_seeds, old_nonces = [200], ["a" * 64]
    expected_directory = tmp_path / "research/laboratory/archive/EXP-20261005-0007-runtime/research/tmp/EXP-20261005-0007"
    for seeds, nonces, rejects in (([300], ["b" * 64], False), ([200], ["b" * 64], True),
                                   ([300], ["a" * 64], True)):
        reads = []

        def metadata(path):
            reads.append(path)
            assert path.parent == expected_directory
            if path.name == "runtime-plan.json":
                return {"matrix": {"seeds": old_seeds}}
            assert path.name == "har01-private-data.json"
            return {"unit_nonces": old_nonces}

        namespace = {"base": tmp_path, "load_json": metadata,
                     "evaluation_matrix": {"seeds": seeds}, "unit_nonces": nonces}
        if rejects:
            with pytest.raises(ValueError, match="Consumed native seed/data collision"):
                exec(executable, namespace)
        else:
            exec(executable, namespace)
        assert [path.name for path in reads] == ["runtime-plan.json", "har01-private-data.json"]


OLD_INTAKES = (
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V1.json",
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V2.json",
)
NEW_INTAKE = "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V3.json"


def integrity_fixture(root):
    for relative in (STUDY_PATH, *(entry["receipt_path"] for entry in
                                 STUDY["historical_unstarted_intake_manifest_exemptions"].values())):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    assert sha256_file(root / STUDY_PATH) == STUDY_SHA
    for entry in STUDY["historical_unstarted_intake_manifest_exemptions"].values():
        assert sha256_file(root / entry["receipt_path"]) == entry["receipt_sha256"]
    return root


def test_exact_unstarted_receipts_exempt_only_absent_old_intakes(tmp_path):
    root = integrity_fixture(tmp_path)
    protected = set(integrity.protected_files(root))
    assert not set(OLD_INTAKES) & protected
    assert NEW_INTAKE in protected
    for relative in OLD_INTAKES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"public synthetic present intake")
        protected = set(integrity.protected_files(root))
        assert relative in protected
        assert NEW_INTAKE in protected
    assert set(OLD_INTAKES) <= protected


def test_absent_new_study_grants_no_historical_exemption(tmp_path):
    protected = set(integrity.protected_files(tmp_path))
    assert set(OLD_INTAKES) <= protected
    assert NEW_INTAKE in protected


def test_changed_plan_or_missing_or_changed_receipt_rejects_exemption(tmp_path):
    entries = list(STUDY["historical_unstarted_intake_manifest_exemptions"].values())
    for name in ("plan", "missing0", "missing1", "changed0", "changed1"):
        root = integrity_fixture(tmp_path / name)
        if name == "plan":
            path = root / STUDY_PATH
            path.write_bytes(path.read_bytes() + b"\n")
        else:
            entry = entries[int(name[-1])]
            path = root / entry["receipt_path"]
            if name.startswith("missing"):
                path.unlink()
            else:
                path.write_bytes(path.read_bytes() + b"\n")
        with pytest.raises(ValueError):
            integrity.protected_files(root)
