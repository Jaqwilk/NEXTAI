"""Close the completed study without changing paid science or programme authority."""
import json
from pathlib import Path

from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.research_program import status
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
identity = "EXP-20261004-0007"
archive = json.loads((b / "research/reviews/PVM01-COMPACT-scientific-archive-V1.json").read_text())
assert archive["protected_source_verified_before_maintenance"]
assert verify_manifest(b)["ok"]
assert sha256_file(b / f"research/results/{identity}.json") == archive["result_sha256"]
programme = status(b)
assert programme["study_terminal"] and not programme["scoring_authorized"]
assert not programme["paid_run_pending"] and not programme["program_closed"]
header = """# Current cycle309 — EXP-20261004-0007 completed (2026-10-04)

One preregistered compact-feature screen:75/75 workers,675/675 trials,
five fresh paired units. Learned RFF512/512 steps full90.7778% versus
source-identical frozen90.8056%; contrast−0.0278pp simultaneous98.75% CI
[−0.4832,+0.4276]. Retained versus RFF2048−17.0556pp CI[−20.7854,−13.3257].
All four primary criteria fail; compact competence fails, dense/cache pass.
DISCARD this exact recipe; no architecture-family falsification or economic,
novelty, transfer or promotion claim. K512 full73.125%, UNKNOWN77.25%;
compact full service0.45285s versus dense cacheCPU1.44793s and ridge0.08421s;
PCA scan0.10426s and68.25KiB versus compact185KiB with lower quality.
All legal observations, fit identity, seeds and outcomes are preserved.
Fit phase383.3104s; charged full workers594.5230s /15600s. All tests, failures
and bookkeeping are append-only charged; auxiliary cap1800s, deadline23:32:56Z.
Analysis:research/analyses/EXP-20261004-0007.md; final accounting:
research/laboratory/PVM01-CYCLE-309-COMPLETION-V1.receipt.json.
Current v4 study terminal, maintenance/scoring=false; continuation stays active.
4/17 new tickets used; old3 tickets/2655.336485s carried unchanged. No retry,
WT8–9, external models/API or schedule change. Use uv run nextai lab status.
Next bounded cycle: preregister matched memory-training exposure including
K512 versus unchanged K32/128 at fixed512 features/512 steps, frozen/shuffled
controls, optimized dense and strongest classical/retrieval controls, five
fresh paired units. Freeze before implementation/data; no rescue on current D.
If not justified, choose a finite evidence-based alternative. Adverse, scaling,
replication, frozen fresh final and full economic gates remain required.
No second EXP in this completed cycle. Previous sections are preserved history.

"""
for name in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md", "docs/SCIENTIFIC_PROTOCOL.md"):
    path = b / name
    previous = path.read_text(encoding="utf8")
    assert not previous.startswith("# Current cycle309")
    path.write_text(header + previous, encoding="utf8", newline="\n")
config = b / "config/research.toml"
payload = config.read_bytes()
assert payload.count(b'benchmark_status = "active"') == 1
config.write_bytes(payload.replace(b'benchmark_status = "active"', b'benchmark_status = "maintenance"'))
manifest = freeze_manifest(b, overwrite=True)
write_preflight_certificate(b)
assert manifest["candidate_bundle_sha256"] == "ceb0430f4c46b5b0f4da407a85cea32af0ac5cf91afb96663232f7781672a9e2"
assert verify_manifest(b)["ok"]
write_report(b)
atomic_write_json(b / "research/reviews/PVM01-COMPACT-maintenance-transition-V1.json", {
    "created_at": utc_now(), "experiment_id": identity, "completed_result_unchanged": True,
    "evaluated_source_preserved_before_transition": True, "whole_program_complete": False,
    "source_and_runtime_receipt_sha256": sha256_file(b / "research/reviews/PVM01-COMPACT-scientific-archive-V1.json"),
    "candidate_bundle_unchanged": True, "current_evaluator_sha256": manifest["evaluator_sha256"],
    "protected_files": len(manifest["files"]), "maintenance": True, "scoring_authorized": False,
    "no_new_research_data_fit_seed_or_registration": True, "historical_authority_sections_preserved": True})
print("Completed v4 returned to maintenance, all1136 protected; scientific source and global authority preserved.")
