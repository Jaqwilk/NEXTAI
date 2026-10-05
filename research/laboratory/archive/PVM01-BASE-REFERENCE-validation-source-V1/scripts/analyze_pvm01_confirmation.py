"""Fixed independent confirmation; reuse immutable scientific calculations."""
import json
import math
from pathlib import Path
import sys

from analyze_pvm01_dense_noise import analyze as frozen_analyze
from analyze_pvm01_transport import persist
from nextai_autoresearch.worker_resource_peaks import validate_peak_record
from nextai_autoresearch.utils import sha256_file


def reuse_cost(candidate_fit, reference_fit, candidate_service, reference_service, reuse_counts):
    values=(candidate_fit,reference_fit,candidate_service,reference_service)
    if any(not isinstance(v,(float,int)) or not math.isfinite(v) or v<0 for v in values):
        raise ValueError("Invalid fit/service cost")
    if any(type(r) is not int or r<1 for r in reuse_counts):
        raise ValueError("Reuse counts must be positive whole workloads")
    savings=reference_service-candidate_service
    return {"by_reuse":{str(r):{"candidate_seconds":candidate_fit+r*candidate_service,
                                  "reference_seconds":reference_fit+r*reference_service}
                        for r in reuse_counts},
            "faster_service_break_even_workloads":max(0.,(candidate_fit-reference_fit)/savings) if savings>0 else None}


def independent_decision(analysis, resource_checks):
    resources_ok = len(resource_checks) == 85 and all(resource_checks.values())
    valid = bool(analysis["valid_comparison"] and resources_ok)
    reference = bool(valid and analysis["reference_selection"]["adequate_for_prospective_selection"])
    selected = bool(reference and analysis["selected_classical_route_confirmation"]["screen_qualified"])
    return {"valid_comparison":valid,"trusted_resources_complete":resources_ok,
            "reference_independently_confirmed":reference,"selected_route_independently_confirmed":selected,
            "decision":"INCONCLUSIVE comparison" if not valid else "KEEP exact selected route for separately frozen fresh final" if selected else "DISCARD exact selected-route independent qualification",
            "no_promotion":True,"selection_outcomes_excluded_from_intervals":True}


def analyze(base, identity):
    plan=json.loads((base/f"research/plans/{identity}.json").read_text(encoding="utf-8"))
    protocol=plan["research_program_protocol"]
    study=json.loads((base/protocol["study_path"]).read_text(encoding="utf-8"))
    assert study["study_kind"]=="paired_view_dense_noise_confirmation" and plan["benchmark"]=="paired_view_mutable_memory_v9"
    assert study["independent_confirmation"]["selection_outcomes_excluded_from_intervals"] is True
    for name,digest in study["parent_evidence"]["scientific_source_sha256_unchanged"].items():
        assert sha256_file(base/name)==digest,name
    result=json.loads((base/f"research/results/{identity}.json").read_text(encoding="utf-8"))
    analysis=frozen_analyze(base,identity)
    checks={}
    for outcome in result["candidates"]:
        execution=outcome.get("execution") or {}
        try:
            record=execution["resource_peaks"]
            path=(base/execution["resource_peaks_path"]).resolve()
            assert path.is_relative_to(base.resolve()) and sha256_file(path)==execution["resource_peaks_sha256"]
            assert json.loads(path.read_text(encoding="utf-8"))==record
            validate_peak_record(record,protocol)
            checks[outcome["candidate"]]=True
        except (OSError,ValueError,TypeError,KeyError,AssertionError):
            checks[outcome["candidate"]]=False
    analysis["independent_confirmation"]=independent_decision(analysis,checks)
    analysis["trusted_resource_checks"]=checks
    analysis["valid_comparison"]=analysis["independent_confirmation"]["valid_comparison"]
    analysis["decision"]=analysis["independent_confirmation"]["decision"]
    amortization={}
    reference=study["independent_confirmation"]["selected_reference"]
    for arm in (study["independent_confirmation"]["selected_route"],"transport_pca"):
        for noise in ("0.02","0.04"):
            left,right=(analysis["arms"].get(a,{}).get(noise,{}) for a in (arm,reference))
            for index in sorted(set(left)&set(right)):
                lfit=analysis["resources"][arm][index]["supervised_fit_seconds"]
                rfit=analysis["resources"][reference][index]["supervised_fit_seconds"]
                amortization[f"{noise}:{arm}:unit{index}"]=reuse_cost(lfit,rfit,left[index]["full_workload_seconds"],right[index]["full_workload_seconds"],study["amortization_report"]["reuse_counts"])
    analysis["descriptive_fit_amortization"]={"frozen_scope":study["amortization_report"],"units":amortization,"used_as_gate":False}
    if not analysis["valid_comparison"]:
        analysis["reference_selection"]["adequate_for_prospective_selection"]=False
        analysis["reference_selection"]["causal_false_abstention_improvement"]=False
        for key in ("neural_economics_against_mixed_reference","selected_classical_route_confirmation"):
            analysis[key]["screen_qualified"]=False; analysis[key]["decision"]="INCONCLUSIVE comparison"
    return analysis


if __name__=="__main__":
    root,identity=Path(__file__).resolve().parents[1],sys.argv[1]
    analysis=analyze(root,identity)
    persist(root/f"research/reviews/{identity}-PVM01-confirmation-analysis.json",analysis)
    print(json.dumps({"experiment_id":identity,**analysis["independent_confirmation"]},indent=2))
