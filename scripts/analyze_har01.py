"""Apply frozen native decisions to saved outcomes, with trusted journals and costs."""
import json
import math
from pathlib import Path
import sys

from nextai_autoresearch.har01_analysis import analyze, ARMS
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.pc01_telemetry import read_device_sample
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def main(identity):
    root = Path(__file__).resolve().parents[1]
    plan_path = root / f"research/plans/{identity}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    protocol = plan["research_program_protocol"]
    study_path = root / protocol["study_path"]
    study = json.loads(study_path.read_text(encoding="utf-8"))
    assert sha256_file(study_path) == protocol["study_sha256"]
    assert sha256_file(root / protocol["task_contract_path"]) == protocol["task_contract_sha256"]
    assert plan["benchmark"] == study["cohort"] == "har01_native_memory_v1"
    result_path = root / f"research/results/{identity}.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    analysis = analyze(result, study)
    checks, journal_hashes, resource_values = {}, {}, {}
    for outcome in result["candidates"]:
        name = outcome["candidate"]
        directory = root / "research/tmp" / identity
        try:
            execution = outcome["execution"]
            assert outcome["status"] == "complete" and outcome["audit"]["ok"] is True
            assert execution["return_code"] == 0 and execution["termination_reason"] is None
            assert execution["research_compute_charge_basis"] == "full_worker_wall_v1"
            assert execution["environment_sanitized"] is True
            assert 0 < execution["peak_rss_bytes"] <= protocol["max_rss_bytes"]
            assert 0 <= execution["supervised_fit_seconds"] <= protocol["fit_seconds_cap"]
            assert 0 < execution["research_compute_seconds"] == execution["wall_seconds"] <= study["resources"]["worker_charge_ceiling_with_monitor_margin"]
            device = read_device_sample(directory / f"{name}.device.json")
            assert device is not None and 0 <= device["allocated"] <= device["reserved"] <= protocol["max_cuda_reserved_bytes"]
            phase = json.loads((directory / f"{name}.phase.json").read_text(encoding="utf-8"))
            assert phase["phase"] == "complete" and phase["fit_elapsed"] == execution["supervised_fit_seconds"]
            fitted = read_jsonl(directory / f"{name}.fits.jsonl")
            assert len(fitted) == 1 and fitted[0]["candidate"] == name
            assert fitted[0]["fit_report"] == outcome["trials"][0]["fit_report"]
            data = read_jsonl(directory / f"{name}.data.jsonl")
            assert len(data) == 19 and data[0]["split"] == "T"
            dev = {(r["condition"], r["K"], r["update_rounds"]): r["episodes_sha256"] for r in data[1:]}
            assert len(dev) == 18
            assert all(dev[r["condition"], r["knowledge_size"], r["update_rounds"]] == r["dev_sha256"] for r in outcome["trials"])
            raw = read_jsonl(directory / f"{name}.trials.jsonl")
            assert raw == outcome["trials"]
            for suffix in ("fits.jsonl", "data.jsonl", "trials.jsonl", "device.json", "phase.json", "supervisor.json"):
                path = directory / f"{name}.{suffix}"
                journal_hashes[str(path.relative_to(root)).replace("\\", "/")] = sha256_file(path)
            resource_values[name] = {"supervised_fit_seconds": execution["supervised_fit_seconds"],
                "full_worker_seconds": execution["wall_seconds"], "sampled_tree_peak_rss_bytes": execution["peak_rss_bytes"],
                "cuda_allocator_peak_allocated_bytes": device["allocated"], "cuda_allocator_peak_reserved_bytes": device["reserved"]}
            checks[name] = True
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
            checks[name] = False
            analysis["problems"].append(f"Trusted resource/journal check failed {name}: {exc}")
    analysis["trusted_resource_journal_checks"] = checks
    analysis["resource_measurements"] = resource_values
    analysis["journal_sha256"] = journal_hashes
    total = sum((r.get("execution") or {}).get("research_compute_seconds", 0.) for r in result["candidates"])
    fit = sum((r.get("execution") or {}).get("supervised_fit_seconds", 0.) for r in result["candidates"])
    if not math.isfinite(total) or total > study["resources"]["fit_seconds_study_cap"]:
        analysis["problems"].append("Full workers exceed study budget or contain nonfinite costs")
    analysis["valid"] = bool(analysis["valid"] and len(checks) == 45 and all(checks.values()) and not analysis["problems"])
    if not analysis["valid"]:
        analysis.update(source_information_transfer="INCONCLUSIVE", economic_decision="INCONCLUSIVE", qualified_routes=[])
    analysis.update(plan_sha256=sha256_file(plan_path), result_sha256=sha256_file(result_path),
        study_sha256=protocol["study_sha256"], task_sha256=protocol["task_contract_sha256"],
        supervised_fit_seconds=fit, full_worker_seconds=total,
        hardware_boundary="Same machine/load protocol; CUDA allocator peaks exclude driver/context and energy; CPU tree RSS is sampled. Timing is not an algorithmic complexity claim.")
    target = root / f"research/analyses/{identity}-har01.json"
    if target.exists():
        assert json.loads(target.read_text(encoding="utf-8")) == analysis, "Immutable analysis already exists with different bytes"
    else:
        atomic_write_json(target, analysis)
    lines = [f"# {identity} — frozen-source native HAR screen", "",
        f"Immutable plan: research/plans/{identity}.json; study: {protocol['study_path']}.", "",
        "## OBSERVATION", "", f"Valid complete comparison: {analysis['valid']}. Independent units: five fixed disjoint subject/source-seed pairs; repeated queries/windows are not independent observations.",
        f"Workers: {len(result['candidates'])}/45; trials: {sum(len(r.get('trials', [])) for r in result['candidates'])}/810. Supervised fit {fit:.6f}s; charged full worker wall {total:.6f}s, including native intake/preparation, all grids, calibration, evaluation and failed workers.",
        "UCI HAR physical windows, T subjects1–5/D16–20; publisher metadata only for other subjects. Numeric future subjects6–15/21–30 remain unopened. T fit128 unique windows, validation48, calibration80 with two-window gaps;4096 sampled fit pairs are not4096 independent recordings. D uses every second window to avoid direct adjacent overlap.",
        "Native features use alternate physical samples with a frozen adverse temporal shift/gyro-channel dropout. Latest-write logic is hand-written. A full answer requires both the value and actual current source; numeric value alone does not establish fact/source correctness.", "",
        "| arm | nominal full / top1 / UNKNOWN / false abstention % | adverse full / top1 / UNKNOWN / false abstention % | nominal/adverse service s | nominal/adverse p95 us | state bytes |",
        "|---|---|---|---|---|---|"]
    if analysis.get("means"):
        import statistics
        for arm in ARMS:
            summaries = []
            for condition in ("nominal", "adverse"):
                rows = [analysis["means"][arm][f"{condition}:K{k}"] for k in (16, 32, 64)]
                summaries.append({key: statistics.mean(r[key] for r in rows) for key in rows[0]})
            a, b = summaries
            quality = lambda x: " / ".join(f"{100*x[key]:.3f}" for key in ("accuracy", "fact_top1_accuracy", "dense_unknown_rejection", "known_false_abstention"))
            lines.append(f"| {arm} | {quality(a)} | {quality(b)} | {a['full_workload_seconds']:.6f}/{b['full_workload_seconds']:.6f} | {a['p95_latency_us']:.2f}/{b['p95_latency_us']:.2f} | {a['state_bytes']:.0f} |")
    lines += ["", "Primary nominal paired contrasts; intervals are98.75% per endpoint with Bonferroni95% over the four fixed endpoints:", ""]
    for key, row in analysis.get("primary", {}).items():
        lines.append(f"- {key}: {100*row['mean']:.4f}pp; CI[{100*row['lower']:.4f},{100*row['upper']:.4f}]pp; positive {row['positive_pairs']}/5; pass={row['pass']}.")
    lines += ["", "## INTERPRETATION / CONFIDENCE / DECISION", "",
        f"Source-information transfer: **{analysis['source_information_transfer']}**. Qualified economic comparison: **{analysis['economic_decision']}**.",
        f"Competent target dense reference at all fixed condition/scale cells: {analysis.get('reference_competent', False)}. Qualified routes: {analysis.get('qualified_routes', [])}.",
        "A failed competent-reference gate makes the qualified comparison inconclusive; it does not falsify an architectural family. Narrow ranking/UNKNOWN effects are retained separately. Target-only readout fitting is not evidence of source-information transfer. This is visible public development screening, without blinded holdout, independent replication or promotion.",
        "All18 economic guards/route and108 fixed strong-comparator contrasts/route retain their frozen simultaneous intervals; candidate service and p95, preprocessing, copies, restoration, allocations, ingest, updates, caches, query and output decoding are charged. Matched quality and strong-classical non-domination are mandatory.",
        "", "## INTEGRITY / BUDGET / NEXT DISCRIMINATING EXPERIMENT", "",
        f"Integrity before/after: {result.get('integrity_before', {}).get('ok')}/{result.get('integrity_after', {}).get('ok')}; trusted resource/journal checks {sum(checks.values())}/45. Problems: {analysis['problems']}.",
        "The cycle completion receipt adds startup/intake/conformance failures, analysis and controller overhead to full worker wall, with all reserves settled. No paid retry, WT8–9, external model/API or schedule change.",
        "Next question must be selected prospectively from this exact evidence. If the reference/absence separation fails, preserve this recipe and test a separately justified native task/view or independently sourced second family; do not weaken the gates or recycle these D subjects as fresh evidence. If qualified, use reserved subject pairs for separately preregistered independent replication and fresh final before prototype selection.",
        "", "Dataset attribution: [UCI HAR dataset, DOI10.24432/C54S4K](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones); Reyes-Ortiz, Anguita, Ghio, Oneto and Parra (2013). Publisher archive README and current web licensing statements conflict; both raw declarations are preserved under HAR01-LICENSE-CONFORMANCE-V1. This run uses local noncommercial scientific research with attribution and does not publish the raw data.", ""]
    report = root / f"research/analyses/{identity}.md"
    text = "\n".join(lines)
    if report.exists():
        assert report.read_text(encoding="utf-8") == text, "Immutable report changed"
    else:
        report.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({key: analysis[key] for key in ("id", "valid", "source_information_transfer", "economic_decision", "supervised_fit_seconds", "full_worker_seconds", "problems")}), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
