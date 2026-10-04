"""Offline operational gates; never register, realize seeds or execute a model."""
import copy
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate, verify_required_baselines
from nextai_autoresearch.gates import ensure_can_create_plan
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.research_program import _study_scope, status
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b=Path.cwd(); commands=[]
for args in (("doctor",),("lab","status")):
    run=subprocess.run(["uv","run","--no-sync","nextai",*args],capture_output=True,text=True,encoding="utf-8")
    print(run.stdout,flush=True); print(run.stderr,flush=True)
    commands.append({"command":list(args),"returncode":run.returncode})
    assert run.returncode==0
ensure_can_create_plan(b)
assert verify_manifest(b)["ok"]
verify_preflight_certificate(b)
study_path="research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"
study=json.loads((b/study_path).read_text())
plan=copy.deepcopy(json.loads((b/"research/plans/EXP-20261004-0006.json").read_text()))
plan.update(benchmark=study["cohort"],candidates=study["candidates"],matrix=study["matrix"])
plan["research_program_protocol"].update(_study_scope(study),study_path=study_path,study_sha256=sha256_file(b/study_path))
validate_document("experiment_plan",plan,b)
verify_required_baselines(plan,b,run_tests=True)
value=status(b)
assert value["ready"] and value["scoring_authorized"] and not value["paid_run_pending"]
assert value["experiment_id"] is None
assert value["unreserved_fit_seconds_remaining"]>=study["resources"]["fit_seconds_study_cap"]
atomic_write_json(b/"research/reviews/PVM01-COMPACT-prepaid-gates-V1.json",{
    "created_at":utc_now(),"commands":commands,"schema_and_all75_semantic_conformance":True,
    "can_create_plan":True,"readiness_integrity_preflight":True,"no_research_seed_data_fit_or_registration":True,
    "new_tickets_before_run":value["continuation_registration_attempts_used"],
    "full_compute_cap":study["resources"]["fit_seconds_study_cap"]})
print("Offline operational, scope, schema and semantic gates: PASS")
