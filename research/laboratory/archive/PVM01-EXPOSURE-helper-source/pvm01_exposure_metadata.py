"""Register only prospective source/fixture semantics, never execute models."""
import json
from pathlib import Path

from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import sha256_file, utc_now

base = Path.cwd()
study_path = base/"research/plans/PVM01-CAPACITY-EXPOSURE-V1.json"
study = json.loads(study_path.read_text())
registry_path = base/"config/baseline_semantics.json"
raw = registry_path.read_text()
registry = json.loads(raw)
for test in ("tests/test_pvm01_delta_memory.py","tests/test_pvm01_compact_features.py"):
    hashes = {t["sha256"] for r in registry["baselines"].values() for t in r.get("conformance_tests",[]) if t["path"] == test}
    assert len(hashes) == 1
    raw = raw.replace(hashes.pop(),sha256_file(base/test))
test = "tests/test_pvm01_capacity_exposure.py"
nodes = ["test_same_transport_paired_draws_curriculum_and_additive_fit_on_fixed_cpu_fixture",
         "test_training_extension_preserves_old_sets_and_calls_only_legal_train_split",
         "test_v5_schema_and_all80_roles_audited_before_registration",
         "test_real_v5_worker_rejects_private_binding_before_arrays_or_model",
         "test_frozen_exposure_primary_gates_and_immutable_analysis",
         "test_stored_analyzer_checks_actual_field_names_and_rejects_broken_dense_pairing"]
entries = []
for name,role in study["roles"].items():
    if not role["arm"].startswith("exposure_"):
        continue
    assert name not in registry["baselines"]
    files = [f"src/nextai_autoresearch/candidates/{name}.py",
             "src/nextai_autoresearch/candidates/pvm01_exposure_core.py",
             "src/nextai_autoresearch/candidates/pvm01_compact_core.py",
             "src/nextai_autoresearch/candidates/pvm01_delta_core.py",
             "src/nextai_autoresearch/candidates/pvm01_core.py"]
    tests = [{"path":test,"node_id":f"{test}::{n}","sha256":sha256_file(base/test)} for n in nodes]
    old = "tests/test_pvm01_compact_features.py"
    tests += [{"path":old,"node_id":f"{old}::{n}","sha256":sha256_file(base/old)} for n in
              ("test_gradient_through_early_writes_and_queries_matches_finite_difference",
               "test_fourier_unit_norm_and_torch_numpy_inference_agree")]
    record = {"baseline_id":name,"version":1,"implementation_files":{p:sha256_file(base/p) for p in files},
        "conformance_tests":tests,"specification":{"arm":role["arm"],"cohort":study["cohort"],
        "prospective_study_sha256":sha256_file(study_path),"no_privileged_generator_inputs":True,
        "same_inference_capacity_and_larger_training_work_charged":True,"no_architecture_novelty_claim":True}}
    entries.append("    "+json.dumps(name)+": "+json.dumps(record,ensure_ascii=False,separators=(",",":")))
ending = "\n  }\n}\n"
assert raw.endswith(ending)
registry_path.write_text(raw[:-len(ending)]+",\n"+",\n".join(entries)+ending,encoding="utf-8",newline="\n")
manifest = freeze_manifest(base,overwrite=True)
write_preflight_certificate(base)
append_jsonl(base/"research/events.jsonl",{"event":"research_program_preparation_source_frozen",
    "created_at":utc_now(),"program_id":"NEXTAI-CONTINUATION-20261004-V1",
    "study_path":study_path.relative_to(base).as_posix(),"scoring":False,
    "evaluator_sha256":manifest["evaluator_sha256"],"before_new_research_seed_or_fit":True})
print(json.dumps({"new_aliases":len(entries),"protected_files":len(manifest["files"]),"benchmark_status":"maintenance"}))
