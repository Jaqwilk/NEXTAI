"""Append-only correction of exploratory PCA field names; no primary gate change."""
import json
from pathlib import Path
import shutil

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
identity = "EXP-20261004-0007"
previous = b / f"research/reviews/{identity}-PVM01-full-diagnostics-V1.json"
value = json.loads(previous.read_text(encoding="utf8"))
result = json.loads((b / f"research/results/{identity}.json").read_text(encoding="utf8"))
assert sha256_file(b / f"research/results/{identity}.json") == value["result_sha256"]
archive = b / "research/laboratory/archive/PVM01-COMPACT-helper-source/diagnostics-V1.py"
source = b / "research/tmp/pvm01_compact_diagnostics.py"
free = shutil.disk_usage(b).free
assert free - source.stat().st_size > 10 * 1024**3
assert not archive.exists()
archive.write_bytes(source.read_bytes())
assert sha256_file(archive) == sha256_file(source)
reports = {c["candidate"]: c["trials"][0]["fit_report"] for c in result["candidates"]}
for i in range(5):
    scan = reports[f"pvm01_ridge_pca_scan_s{i}"]
    tree = reports[f"pvm01_ridge_pca_tree_s{i}"]
    fields = ("fp32_ridge_weights_sha256", "pca_projection_sha256", "pca_choice", "pca_grid")
    assert all(scan.get(key) is not None and scan[key] == tree.get(key) for key in fields)
    value["identity_checks"][str(i)]["PCA_scan_tree_common_fit"] = True
    value["identity_checks"][str(i)]["PCA_actual_compared_fields"] = list(fields)
value.update(created_at=utc_now(), previous_diagnostic_path=previous.relative_to(b).as_posix(),
             previous_diagnostic_sha256=sha256_file(previous),
             correction="V1 looked up absent ridge_weights_sha256/projection_sha256 and reported false. Actual stored fields fp32_ridge_weights_sha256/pca_projection_sha256, choice and grid agree in all five paired units. All other V1 calculations retained; primary analysis, completed result, source and gates unchanged.",
             failed_assumption_preserved=True, diagnostic_source_V1_raw_sha256=sha256_file(archive))
target = b / f"research/reviews/{identity}-PVM01-full-diagnostics-V2.json"
assert not target.exists()
atomic_write_json(target, value)
print("Actual PCA scan/tree weights, projection, choice and grid: five units identical; V1 preserved.")
for arm in value["descriptive_95_percent_intervals"]:
    row = value["descriptive_95_percent_intervals"][arm]
    print(arm, "Kfull/U%", {k:[round(row["by_K"][k][m]["mean"]*100,4) for m in ("accuracy","dense_unknown_rejection")] for k in row["by_K"]},
          "fit/service/p95/RSSMiB", [round(row["costs"][k]["mean"]/(1024**2 if k=="peak_rss_bytes" else 1),6)
                                   for k in ("fit_phase_seconds","full_workload_seconds","p95_query_us","peak_rss_bytes")])
print("Totals", {key:value[key] for key in value if key.startswith("total_") or key=="full_charged_worker_seconds"})
print("Learned feature loss first50 / last50", {key:[round(trace["first50_mean"],6),round(trace["last50_mean"],6)]
                                               for key,trace in value["feature_training_traces"].items() if key.startswith("compact_learned/")})
