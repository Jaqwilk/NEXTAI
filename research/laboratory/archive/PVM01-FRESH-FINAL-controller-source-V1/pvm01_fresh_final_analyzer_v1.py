from pathlib import Path
p=Path('scripts/analyze_pvm01_base_reference.py');s=p.read_text()
s=s.replace('Prospectively frozen base-reference analysis','Prospectively frozen fresh-final analysis')
s=s.replace('"paired_view_unaugmented_reference_confirmation"','"paired_view_frozen_fresh_final"').replace('"paired_view_mutable_memory_v10"','"paired_view_mutable_memory_v11"')
s=s.replace('from nextai_autoresearch.utils import sha256_file','from nextai_autoresearch.utils import sha256_file, sha256_json\nfrom nextai_autoresearch.pvm01_fitted_state import ARMS, load_state, validate_parameters\nfrom nextai_autoresearch.ledger import read_jsonl')
needle='def analyze(base, identity):';assert s.count(needle)==1
block='''def fitted_source_checks(base, identity, outcomes, protocol):
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


'''
s=s.replace(needle,block+needle,1)
needle='    assert study["independent_confirmation"]["selected_reference"] == "dense_cached_cpu"'
s=s.replace(needle,'    assert protocol["evaluation_data_role"] == study["evaluation_data_role"] == "frozen_fresh_final_v1"\n'+needle,1)
needle='    analysis["valid_comparison"] = bool(analysis["valid_comparison"] and resources_ok)'
s=s.replace(needle,'    fitted = fitted_source_checks(base, identity, result["candidates"], protocol)\n    analysis["fitted_source_states"] = fitted\n    analysis["valid_comparison"] = bool(analysis["valid_comparison"] and resources_ok and fitted["complete"])',1)
s=s.replace('    analysis["decision"] = confirmation["decision"]','''    confirmation["fitted_source_states_complete"] = fitted["complete"]
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
    analysis["transfer_or_novel_architecture_claim"] = False''',1)
s=s.replace('-PVM01-base-reference-analysis.json','-PVM01-fresh-final-analysis.json')
Path('scripts/analyze_pvm01_fresh_final.py').write_text(s,encoding='utf-8',newline='\n')
print('Frozen saved-outcome analysis and25 fitted-source provenance guards written')