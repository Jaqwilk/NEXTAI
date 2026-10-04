"""Prospective source metadata; preserves earlier record text except scoped hashes."""
import json
from pathlib import Path

from nextai_autoresearch.utils import sha256_file

BASE = Path(__file__).resolve().parents[2]
study_path = BASE / "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"
study = json.loads(study_path.read_text())
for arm in ("compact_learned", "compact_frozen", "compact_shuffled", "compact_additive"):
    for index in range(5):
        path = BASE / f"src/nextai_autoresearch/candidates/pvm01_{arm}_s{index}.py"
        source = "from .pvm01_compact_core import Candidate as Reference\n\n\nclass Candidate(Reference):\n    pass\n"
        if path.exists():
            assert path.read_text() == source
        else:
            path.write_text(source, encoding="utf-8", newline="\n")
schema = BASE / "schemas/experiment_plan.schema.json"
raw = schema.read_text()
old = '"paired_view_mutable_memory_v1","paired_view_mutable_memory_v2","paired_view_mutable_memory_v3"'
if old in raw:
    assert raw.count(old) == 1
    raw = raw.replace(old, old + ',"paired_view_mutable_memory_v4"')
    schema.write_text(raw, encoding="utf-8", newline="\n")
registry_path = BASE / "config/baseline_semantics.json"
raw = registry_path.read_text()
registry = json.loads(raw)
old_test = "tests/test_pvm01_delta_memory.py"
old_hash = registry["baselines"]["pvm01_delta_s0"]["conformance_tests"][0]["sha256"]
new_hash = sha256_file(BASE / old_test)
raw = raw.replace(old_hash, new_hash)
entries = []
test = "tests/test_pvm01_compact_features.py"
nodes = ["test_feature_unroll_matches_numpy_write_inference_and_overwrite",
         "test_gradient_through_early_writes_and_queries_matches_finite_difference",
         "test_fourier_unit_norm_and_torch_numpy_inference_agree",
         "test_same_transport_features_draws_and_additive_fit_on_fixed_cpu_fixture",
         "test_null_supervision_distinguishes_correct_from_corrupt_value_or_abstention",
         "test_v4_schema_and_all_roles_are_audited_before_registration",
         "test_real_v4_worker_rejects_private_binding_before_arrays_or_model",
         "test_latest_consumed_units_reject_collisions_and_tampering",
         "test_frozen_primary_gates_detect_feature_capacity_and_retention_failures"]
for name, role in study["roles"].items():
    if not role["arm"].startswith("compact_"):
        continue
    files = [f"src/nextai_autoresearch/candidates/{name}.py",
             "src/nextai_autoresearch/candidates/pvm01_compact_core.py",
             "src/nextai_autoresearch/candidates/pvm01_delta_core.py",
             "src/nextai_autoresearch/candidates/pvm01_core.py"]
    record = {"baseline_id":name, "version":1,
              "implementation_files":{path:sha256_file(BASE/path) for path in files},
              "conformance_tests":[{"path":test,"node_id":f"{test}::{node}","sha256":sha256_file(BASE/test)} for node in nodes],
              "specification":{"arm":role["arm"], "cohort":study["cohort"],
                  "prospective_study_sha256":sha256_file(study_path), "no_privileged_generator_inputs":True,
                  "no_architecture_novelty_claim":True,"full_cost_and_capacity_frozen":True}}
    assert name not in registry["baselines"]
    entries.append("    " + json.dumps(name) + ": " + json.dumps(record, ensure_ascii=False, separators=(",",":")))
ending = "\n  }\n}\n"
assert raw.endswith(ending)
raw = raw[:-len(ending)] + ",\n" + ",\n".join(entries) + ending
registry_path.write_text(raw,encoding="utf-8",newline="\n")
print("Added20 compact aliases and semantic records; v4 schema extended; prior test hashes refreshed.")
