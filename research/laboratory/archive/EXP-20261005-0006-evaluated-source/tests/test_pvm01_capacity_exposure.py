"""Fixed synthetic conformance; never draw new research seed/data units."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.pvm01_exposure_core import Candidate
from nextai_autoresearch.research_program import _study_scope
from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json

ROOT = Path(__file__).resolve().parents[1]
STUDY_PATH = ROOT / "research/plans/PVM01-CAPACITY-EXPOSURE-V1.json"
STUDY = json.loads(STUDY_PATH.read_text())


def analyzer():
    spec = importlib.util.spec_from_file_location("exposure_analysis_fixture", ROOT/"scripts/analyze_pvm01_capacity_exposure.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_same_transport_paired_draws_curriculum_and_additive_fit_on_fixed_cpu_fixture():
    recipe = {**STUDY["recipe"], "alignment_steps":2, "alignment_batch":8,
              "compact_feature_steps":2, "compact_feature_batch":2}
    rng = np.random.default_rng(317)
    query = rng.normal(size=(32,64)).astype(np.float32)
    write = query[:,::-1].copy()
    sets = {k:(rng.normal(size=(4,k,64)).astype(np.float32),rng.normal(size=(4,8,64)).astype(np.float32),
               np.tile(np.array([0,1,2,3,4,5,k,k]),(4,1))) for k in (32,128,512)}
    reports, systems = {}, {}
    for arm in ("exposure_small","exposure_large","exposure_frozen","exposure_shuffled","exposure_additive"):
        system = Candidate(331,arm,recipe)
        system.model = system.model.cpu()
        system.device = torch.device("cpu")
        reports[arm] = system.fit(write,query,write[:8],query[:8],sets)
        systems[arm] = system
    for key in ("initial_parameters_sha256","final_encoder_sha256","alignment_losses",
                "compact_initial_features_sha256","compact_precomputed_sha256"):
        assert len({json.dumps(r[key]) for r in reports.values()}) == 1
    optimized = [reports[a] for a in ("exposure_small","exposure_large","exposure_shuffled","exposure_additive")]
    assert len({r["exposure_common_draws_sha256"] for r in optimized}) == 1
    for key in ("compact_final_features_sha256","compact_feature_losses","compact_feature_gradient_norms","compact_batch_value_draws_sha256"):
        assert reports["exposure_large"][key] == reports["exposure_additive"][key]
    assert reports["exposure_small"]["compact_batch_value_draws_sha256"] != reports["exposure_large"]["compact_batch_value_draws_sha256"]
    assert reports["exposure_small"]["exposure_training_write_count"] == 320
    assert reports["exposure_large"]["exposure_training_write_count"] == 1088
    frozen = reports["exposure_frozen"]
    assert frozen["compact_initial_features_sha256"] == frozen["compact_final_features_sha256"]
    assert frozen["exposure_training_write_count"] == 0
    assert all(r["compact_initial_features_sha256"] != r["compact_final_features_sha256"] for r in optimized)
    assert reports["exposure_large"]["compact_final_features_sha256"] != reports["exposure_shuffled"]["compact_final_features_sha256"]
    assert not any(p.requires_grad for p in systems["exposure_large"].model.parameters())
    assert systems["exposure_large"].new_session(4).memory.shape == (512,16)
    assert systems["exposure_additive"].arm == "additive"


def test_training_extension_preserves_old_sets_and_calls_only_legal_train_split(monkeypatch):
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v5 as benchmark
    old = {32:object(),128:object()}
    calls = []
    monkeypatch.setattr(benchmark,"training_sets",lambda nonce,count:old.copy())
    def fixture(nonce,split,k,updates,index,query_count):
        calls.append((nonce,split,k,updates,index,query_count))
        writes = tuple((i,1000+i,np.full(64,i,np.float32),i%16) for i in range(k))
        return SimpleNamespace(writes=writes,queries=np.zeros((8,64),np.float32),
                               target_handles=(1000,1001,1002,1003,1004,1005,None,None))
    monkeypatch.setattr(benchmark,"episode",fixture)
    result = benchmark.exposure_training_sets("fixed-fixture",2)
    assert result[32] is old[32] and result[128] is old[128]
    assert calls == [("fixed-fixture","T-sets",512,0,i,8) for i in range(2)]
    assert result[512][0].shape == (2,512,64)
    np.testing.assert_array_equal(result[512][2],[[0,1,2,3,4,5,512,512]]*2)


def test_v5_schema_and_all80_roles_audited_before_registration():
    from nextai_autoresearch.audit import audit_benchmark_boundary
    from nextai_autoresearch.schemas import validate_document
    from jsonschema import ValidationError
    plan = json.loads((ROOT/"research/plans/EXP-20261004-0007.json").read_text())
    plan.update(benchmark=STUDY["cohort"],matrix=STUDY["matrix"],candidates=STUDY["candidates"])
    plan["research_program_protocol"].update(_study_scope(STUDY),study_path=STUDY_PATH.relative_to(ROOT).as_posix(),study_sha256=sha256_file(STUDY_PATH))
    validate_document("experiment_plan",plan,ROOT)
    assert audit_benchmark_boundary(STUDY["cohort"],ROOT) == ()
    wrong = copy.deepcopy(plan)
    wrong["matrix"]["knowledge_sizes"] = [32,128,256]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan",wrong,ROOT)
    wrong = copy.deepcopy(plan)
    del wrong["research_program_protocol"]["compute_charge_basis"]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan",wrong,ROOT)
    for name in STUDY["candidates"]:
        audit = audit_candidate(name,load_config(ROOT),ROOT)
        assert audit.ok,(name,audit.problems)
    assert len(STUDY["roles"]) == 80
    assert 80*STUDY["resources"]["worker_charge_ceiling_with_monitor_margin"] == STUDY["resources"]["fit_seconds_study_cap"]
    assert STUDY["economic_gates"] == json.loads((ROOT/"research/plans/NEXTAI-CONTINUATION-PROGRAM-V1.json").read_text())["economic_claim_gates"]


def test_real_v5_worker_rejects_private_binding_before_arrays_or_model(tmp_path,monkeypatch):
    from nextai_autoresearch import worker_resources
    from nextai_autoresearch.worker import run_worker
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v3 as common
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v5 as benchmark
    identity = "EXP-20990101-9905"
    monkeypatch.setattr(common,"project_root",lambda:tmp_path)
    private = tmp_path/"research/tmp"/identity/"pvm01-private-data.json"
    atomic_write_json(private,{"experiment_id":identity,"unit_nonces":["fixed-fixture"]*5})
    plan = {"benchmark":STUDY["cohort"],"experiment_id":identity,
        "matrix":{**STUDY["matrix"],"seeds":list(range(1001,1006))},"research_program_protocol":_study_scope(STUDY),
        "pvm01_private_data_path":str(private),"pvm01_private_data_sha256":"0"*64}
    def forbidden(*args,**kwargs):
        pytest.fail("Private binding failure accessed arrays or model")
    for name in ("pairs","exposure_training_sets","episode"):
        monkeypatch.setattr(benchmark,name,forbidden)
    monkeypatch.setattr(worker_resources.WorkerResources,"start",lambda self:None)
    monkeypatch.setattr(worker_resources.WorkerResources,"close",lambda self:None)
    monkeypatch.setattr(worker_resources.WorkerResources,"phase",lambda self,phase:None)
    path,output = tmp_path/"fixture-plan.json",tmp_path/"output.json"
    atomic_write_json(path,plan)
    assert run_worker(path,STUDY["candidates"][0],output) == 1
    value = json.loads(output.read_text())
    assert value["error_type"] == "ValueError" and "binding" in value["error"]
    assert not value["trials"]


def test_frozen_exposure_primary_gates_and_immutable_analysis(tmp_path):
    module = analyzer()
    good = {name:module.interval([.1]*5,.9875) for name in ("small","frozen","shuffled")}
    good["retained"] = module.interval([0]*5,.9875)
    assert all(module.primary_gates(good,STUDY["diagnosis_gates"]).values())
    good["small"] = module.interval([0]*5,.9875)
    assert not module.primary_gates(good,STUDY["diagnosis_gates"])["small"]
    good["retained"] = module.interval([-.03]*5,.9875)
    assert not module.primary_gates(good,STUDY["diagnosis_gates"])["retention_noninferiority"]
    path = tmp_path/"analysis.json"
    module.persist(path,{1:{"sample":None}})
    before = path.read_bytes()
    module.persist(path,{1:{"sample":None}})
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        module.persist(path,{1:{"sample":1}})


def test_stored_analyzer_checks_actual_field_names_and_rejects_broken_dense_pairing(tmp_path):
    module = analyzer()
    relative = STUDY_PATH.relative_to(ROOT)
    atomic_write_json(tmp_path/relative,STUDY)
    plan = json.loads((ROOT/"research/plans/EXP-20261004-0007.json").read_text())
    plan["research_program_protocol"].update(_study_scope(STUDY),study_path=relative.as_posix(),study_sha256=sha256_file(tmp_path/relative))
    plan["candidates"] = STUDY["candidates"]
    identity = "EXP-20990101-9906"
    plan["experiment_id"] = identity
    atomic_write_json(tmp_path/f"research/plans/{identity}.json",plan)
    outcomes = []
    for name,role in STUDY["roles"].items():
        arm = role["arm"]
        feature = arm.startswith("exposure_")
        optimized = feature and arm != "exposure_frozen"
        accuracy = .85 if arm in {"exposure_small","exposure_frozen","exposure_shuffled"} else .99
        report = {"train_pairs_sha256":"T","training_validation_sha256":"Tv","calibration_sha256":"Tc",
            "training_sets_sha256":{"32":"s32","128":"s128","512":"s512"},"fit_seconds":1.,
            "calibration_choice":{"threshold":.5},"initial_parameters_sha256":"init","final_encoder_sha256":"encoder",
            "alignment_losses":[.1,.05],"compact_initial_features_sha256":"init-phi",
            "compact_final_features_sha256":"trained-phi" if optimized else "init-phi","compact_precomputed_sha256":"precomputed",
            "exposure_common_draws_sha256":"draws","compact_batch_value_draws_sha256":"sized-draws",
            "compact_feature_losses":[.1]*512 if optimized else [],"compact_feature_gradient_norms":[.1]*512 if optimized else [],
            "compact_feature_steps":512 if optimized else 0,
            "exposure_support_sizes":[32,128] if arm == "exposure_small" else [32,512],
            "final_decoder_sha256":"decoder","dense_set_losses":[.2,.1],
            "fp32_ridge_weights_sha256":"ridge","pca_projection_sha256":"PCA","pca_choice":{"rank":16},"pca_grid":[{"rank":16}]}
        rows = []
        for k in (32,128,512):
            for rounds in (0,1,4):
                rows.append({"fit_report_sha256":sha256_json(report),"dev_sha256":f"D{k}-{rounds}",
                    "accuracy":accuracy,"known_false_abstention":0.,"dense_unknown_rejection":.99,
                    "nonabstaining_known_value_accuracy":.99,"fact_top1_accuracy":None if feature else .99,
                    "update_rounds":rounds,"updated_known_accuracy":.99,"retained_known_accuracy":.99,
                    "knowledge_size":k,"full_workload_seconds":.01,"state_bytes":100,"runtime_device":"cpu",
                    "component_seconds":{"query_seconds":.005}})
        rows[0]["fit_report"] = report
        outcomes.append({"candidate":name,"status":"complete","trials":rows,"summary":{"p95_latency_us":10.},
            "execution":{"supervised_fit_seconds":1.,"research_compute_seconds":2.,"peak_rss_bytes":1000}})
    result = {"plan_sha256":sha256_json(plan),"candidates":outcomes}
    path = tmp_path/f"research/results/{identity}.json"
    atomic_write_json(path,result)
    value = module.analyze(tmp_path,identity)
    assert value["all_workers_and_trials_complete"] and value["decision"].startswith("KEEP")
    item = next(v for v in outcomes if v["candidate"] == "pvm01_dense_cached_cpu_s0")
    item["trials"][0]["fit_report"]["final_decoder_sha256"] = "wrong-decoder"
    for row in item["trials"]:
        row["fit_report_sha256"] = sha256_json(item["trials"][0]["fit_report"])
    atomic_write_json(path,result)
    value = module.analyze(tmp_path,identity)
    assert not value["source_fit_identity"]["0"]["dense_cache_identical_weights"]
    assert value["decision"] == "INCONCLUSIVE comparison"
