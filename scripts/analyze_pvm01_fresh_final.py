"""Prospectively frozen fresh-final analysis of saved outcomes; no model/data run."""
import copy
import json
from pathlib import Path
import sys

from analyze_pvm01_dense_noise import BASE, analyze as frozen_analyze
from analyze_pvm01_confirmation import independent_decision, reuse_cost
from analyze_pvm01_replication import confirm_selected_route
from analyze_pvm01_transport import competence, persist
from nextai_autoresearch.worker_resource_peaks import validate_peak_record
from nextai_autoresearch.utils import sha256_file, sha256_json
from nextai_autoresearch.pvm01_fitted_state import ARMS, load_state, validate_parameters
from nextai_autoresearch.ledger import read_jsonl


def base_reference_confirmation(analysis, study):
    contract = study["unaugmented_reference_guards"]
    assert contract["reference_variants"] == list(BASE)
    assert contract["independent_units"] == 5 and contract["guards"] == 10
    assert contract["base_vs_itself_noninferiority_assay_forbidden"] is True
    arms = analysis["arms"]
    controls = {
        f"{noise}:{arm}": {key: bool(value) for key, value in
            competence(list(arms.get(arm, {}).get(noise, {}).values()), study["reference_gates"]).items()}
        for noise in ("0.02", "0.04") for arm in BASE
    }
    guards = {}
    exact_units = True
    for noise in ("0.02", "0.04"):
        rows = arms.get("dense_cached_cpu", {}).get(noise, {})
        exact_units &= set(rows) == set(map(str, range(5)))
        for index, unit in rows.items():
            guards[f"{noise}:unit{index}:false_abstention"] = bool(
                unit["false_abstention"] <= contract["each_unit_noise_false_abstention_max"])
    competent = bool(exact_units and all(all(g.values()) for g in controls.values()))
    adequate = bool(analysis["valid_comparison"] and competent and len(guards) == 10 and all(guards.values()))
    return {"reference": "dense_cached_cpu", "competence_gates": controls,
            "each_unit_false_abstention_guards": guards, "exact_five_units_at_each_noise": bool(exact_units),
            "base_reference_competent": competent, "adequate_for_economic_comparison": adequate,
            "mixed_assay_used_as_gate": False, "base_vs_itself_assay_used": False,
            "decision": "KEEP fixed base reference for economic comparison" if adequate else
                        "INCONCLUSIVE base-reference controls"}


def qualification(analysis, study, classical_controls):
    reference = base_reference_confirmation(analysis, study)
    routes = {}
    learning_ok = (len(analysis["primary_gates"]) == 9 and analysis["primary_gates"].get("all_eight_endpoints") is True
                   and all(analysis["primary_gates"].values()))
    for arm in ("ridge_pca_scan", "transport_pca"):
        adapted = copy.deepcopy(study)
        contract = copy.deepcopy(study["unaugmented_reference_confirmation"])
        contract["candidate"] = arm
        if arm == "transport_pca":
            contract["non_domination_family"]["fixed_comparators"] = classical_controls
        adapted["selected_classical_route_confirmation"] = contract
        route = confirm_selected_route(analysis, adapted)
        route["screen_qualified"] &= reference["adequate_for_economic_comparison"] and learning_ok
        route["decision"] = ("INCONCLUSIVE base-reference comparison" if not analysis["valid_comparison"] or
            not reference["adequate_for_economic_comparison"] else
            f"KEEP exact {arm} route for separately frozen fresh final" if route["screen_qualified"] else
            f"DISCARD exact {arm} base-reference economic qualification")
        routes[arm] = route
    selected = bool(routes["ridge_pca_scan"]["screen_qualified"])
    neural = bool(routes["transport_pca"]["screen_qualified"])
    valid = bool(analysis["valid_comparison"])
    decision = ("INCONCLUSIVE base-reference comparison" if not valid or not reference["adequate_for_economic_comparison"] else
                "KEEP exact selected route for separately frozen fresh final" if selected else
                "KEEP exact neural route for prospective fresh-final selection" if neural else
                "DISCARD exact base-reference route qualifications")
    return reference, routes, {"valid_comparison": valid,
        "reference_independently_confirmed": reference["adequate_for_economic_comparison"],
        "selected_route_independently_confirmed": selected, "neural_route_independently_confirmed": neural,
        "decision": decision, "no_promotion": True, "selection_outcomes_excluded_from_intervals": True,
        "mixed_assay_used_as_gate": False, "base_vs_itself_assay_used": False}


def trusted_resource_checks(base, identity, outcomes, protocol):
    checks = {}
    for outcome in outcomes:
        execution = outcome.get("execution") or {}
        try:
            relative = Path(execution["resource_peaks_path"])
            assert relative.parent == Path("research/tmp") / identity
            assert relative.suffixes[-2:] == [".resources", ".json"]
            path = (base / relative).resolve()
            assert path.is_relative_to(base.resolve()) and sha256_file(path) == execution["resource_peaks_sha256"]
            record = json.loads(path.read_text(encoding="utf-8"))
            assert record == execution["resource_peaks"]
            validate_peak_record(record, protocol)
            checks[outcome["candidate"]] = True
        except (OSError, ValueError, TypeError, KeyError, AssertionError):
            checks[outcome["candidate"]] = False
    return checks


def fitted_source_checks(base, identity, outcomes, protocol):
    checks, exports = {}, {}
    expected = {name for name, role in protocol["roles"].items() if role["arm"] in ARMS}
    for outcome in outcomes:
        name = outcome["candidate"]
        if name not in expected:
            continue
        try:
            rows = read_jsonl(base/f"research/tmp/{identity}/{name}.fits.jsonl")
            assert len(rows) == 1
            row = rows[0]
            report = outcome["trials"][0]["fit_report"]
            assert row["candidate"] == name and row["fit_report"] == report
            assert row["fit_report_sha256"] == sha256_json(report)
            descriptor = row["source_state_export"]
            assert descriptor["directory_name"] == name
            directory = base/f"research/tmp/{identity}/fitted-source/{name}"
            metadata, arrays = load_state(directory)
            assert sha256_file(directory/"metadata.json") == descriptor["metadata_sha256"]
            assert metadata["parameters_sha256"] == descriptor["parameters_sha256"]
            assert metadata["fit_report_sha256"] == row["fit_report_sha256"]
            assert metadata["study_sha256"] == protocol["study_sha256"]
            assert metadata["recipe_sha256"] == sha256_json(protocol["recipe"])
            role = protocol["roles"][name]
            assert metadata["arm"] == role["arm"] and metadata["seed_index"] == role["seed_index"]
            assert metadata["seed"] == report["seed"] and metadata["threshold"] == report["calibration_choice"]["threshold"]
            validate_parameters(arrays, report)
            size = sum(p.stat().st_size for p in directory.iterdir())
            assert size == descriptor["total_bytes"] and descriptor["copied_before_final_arrays"] and descriptor["all_cost_in_fit_phase"]
            assert 0 <= descriptor["export_seconds"] <= outcome["execution"]["supervised_fit_seconds"]
            exports[name] = descriptor
            checks[name] = True
        except (OSError, ValueError, KeyError, TypeError, AssertionError):
            checks[name] = False
    complete = set(checks) == expected and len(expected) == 25 and all(checks.values())
    complete &= sum(e["total_bytes"] for e in exports.values()) <= 54067200
    return {"checks": checks, "exports": exports, "complete": bool(complete),
            "total_bytes": sum(e["total_bytes"] for e in exports.values()),
            "export_seconds_in_fit_phase": sum(e["export_seconds"] for e in exports.values()),
            "source_refit_or_final_arrays_used_by_analysis": False}


def analyze(base, identity):
    plan = json.loads((base/f"research/plans/{identity}.json").read_text(encoding="utf-8"))
    protocol = plan["research_program_protocol"]
    study = json.loads((base/protocol["study_path"]).read_text(encoding="utf-8"))
    assert study["study_kind"] == "paired_view_frozen_fresh_final"
    assert plan["benchmark"] == "paired_view_mutable_memory_v11"
    assert protocol["evaluation_data_role"] == study["evaluation_data_role"] == "frozen_fresh_final_v1"
    assert study["independent_confirmation"]["selected_reference"] == "dense_cached_cpu"
    assert study["independent_confirmation"]["selection_outcomes_excluded_from_intervals"] is True
    for name, digest in study["parent_evidence"]["scientific_source_sha256_unchanged"].items():
        assert sha256_file(base/name) == digest, name
    result = json.loads((base/f"research/results/{identity}.json").read_text(encoding="utf-8"))
    analysis = frozen_analyze(base, identity)
    checks = trusted_resource_checks(base, identity, result["candidates"], protocol)
    resources_ok = len(checks) == 85 and all(checks.values())
    fitted = fitted_source_checks(base, identity, result["candidates"], protocol)
    analysis["fitted_source_states"] = fitted
    analysis["valid_comparison"] = bool(analysis["valid_comparison"] and resources_ok and fitted["complete"])
    analysis["trusted_resource_checks"] = checks
    analysis["ancillary_mixed_independent_confirmation"] = independent_decision(analysis, checks)
    addon = json.loads((base/protocol["classical_economic_contract_path"]).read_text(encoding="utf-8"))
    reference, routes, confirmation = qualification(analysis, study, addon["controls"])
    confirmation["trusted_resources_complete"] = resources_ok
    analysis["base_reference_confirmation"] = reference
    analysis["unaugmented_reference_economics"] = routes
    analysis["independent_confirmation"] = confirmation
    confirmation["fitted_source_states_complete"] = fitted["complete"]
    confirmation["fresh_final_executed"] = True
    confirmation["independently_blinded_evaluation"] = False
    for arm, route in routes.items():
        route["decision"] = (f"KEEP exact {arm} locally validated frozen fresh-final route" if route["screen_qualified"] else
            "INCONCLUSIVE frozen fresh-final comparison" if not analysis["valid_comparison"] or not reference["adequate_for_economic_comparison"] else
            f"DISCARD exact {arm} frozen fresh-final qualification")
    confirmation["decision"] = ("INCONCLUSIVE frozen fresh-final comparison" if not analysis["valid_comparison"] or not reference["adequate_for_economic_comparison"] else
        "KEEP locally validated fixed routes for separately preregistered transfer" if any(r["screen_qualified"] for r in routes.values()) else
        "DISCARD exact frozen fresh-final route qualifications")
    analysis["decision"] = confirmation["decision"]
    analysis["fresh_final_executed"] = True
    analysis["whole_program_complete"] = False
    analysis["transfer_or_novel_architecture_claim"] = False
    amortization = {}
    for arm in ("ridge_pca_scan", "transport_pca"):
        for noise in ("0.02", "0.04"):
            left, right = (analysis["arms"].get(a, {}).get(noise, {}) for a in (arm, "dense_cached_cpu"))
            for index in sorted(set(left) & set(right)):
                lfit, rfit = (analysis["resources"][a][index]["supervised_fit_seconds"] for a in (arm, "dense_cached_cpu"))
                amortization[f"{noise}:{arm}:unit{index}"] = reuse_cost(lfit, rfit,
                    left[index]["full_workload_seconds"], right[index]["full_workload_seconds"],
                    study["amortization_report"]["reuse_counts"])
    analysis["descriptive_fit_amortization"] = {"frozen_scope": study["amortization_report"],
        "reference": "dense_cached_cpu", "units": amortization, "used_as_gate": False}
    return analysis


if __name__ == "__main__":
    root, identity = Path(__file__).resolve().parents[1], sys.argv[1]
    analysis = analyze(root, identity)
    persist(root/f"research/reviews/{identity}-PVM01-fresh-final-analysis.json", analysis)
    print(json.dumps({"experiment_id": identity, **analysis["independent_confirmation"]}, indent=2))