"""Verify terminal maintenance and programme accounting, without scoring."""
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate, verify_required_baselines
from nextai_autoresearch.config import load_config
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.research_program import scope_problems, status
from nextai_autoresearch.utils import atomic_write_json, utc_now

b = Path.cwd()
assert not any((b / name).exists() for name in ("STOP", "PAUSE", ".nextai.lock"))
assert load_config(b).raw["project"]["benchmark_status"] == "maintenance"
for args in (("doctor",), ("lab", "status")):
    run = subprocess.run(["uv", "run", "--no-sync", "nextai", *args], capture_output=True)
    print(run.stdout.decode("utf8", errors="replace"), flush=True)
    print(run.stderr.decode("utf8", errors="replace"), flush=True)
    assert run.returncode == 0
value = status(b)
assert value["study_terminal"] and not value["scoring_authorized"]
assert not value["paid_run_pending"] and not value["program_terminal"]
assert value["registration_attempts_used"] == 7 and value["continuation_registration_attempts_used"] == 4
assert value["prior_registration_attempts_used"] == 3 and value["prior_program_closed"]
carry = json.loads((b / "research/plans/NEXTAI-CONTINUATION-PROGRAM-V1.json").read_text())["carry_forward"]
assert value["prior_compute_seconds_charged"] == carry["fit_seconds_charged"]
assert value["pending_fit_reservation_seconds"] == 0
assert scope_problems(b)
integrity = verify_manifest(b)
assert integrity["ok"] and integrity["checked_files"] == 1136
verify_preflight_certificate(b)
plan = json.loads((b / "research/plans/EXP-20261004-0007.json").read_text())
semantics = verify_required_baselines(plan, b, run_tests=False)
assert len(semantics["required"]) == 75
state = json.loads((b / "research/state.json").read_text())
assert state["cycle_number"] == 309 and state["completed_experiments"] == 114 and state["active_experiment_id"] is None
atomic_write_json(b / "research/reviews/PVM01-COMPACT-postrun-state-integrity-V1.json", {
    "created_at": utc_now(), "doctor_and_lab_status_pass": True, "maintenance_and_no_new_scoring": True,
    "programme_active": True, "programme": value, "state": state, "integrity": integrity,
    "all75_semantic_records_valid": True, "prior_consumed_budget_unchanged": True})
print("Terminal maintenance, no pending paid run, active continuation, old budgets and all75 semantics: PASS")
