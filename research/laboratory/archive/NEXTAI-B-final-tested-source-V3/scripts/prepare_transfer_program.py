"""One-way, no-scoring closure of A and activation of the user-approved B authority."""
from pathlib import Path
import json
import time

from nextai_autoresearch import research_program as program
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, sha256_json, utc_now


PREPARATION = "research/plans/NEXTAI-A-CLOSURE-B-PREPARATION-V1.json"
B_PREPARATION = "research/plans/NEXTAI-TRANSFER-PREPARATION-V1.json"
A_RECEIPT = "research/laboratory/NEXTAI-A-CONTINUATION-PROGRAM-COMPLETION-V1.receipt.json"
A_ANALYSIS = "research/analyses/NEXTAI-A-CONTINUATION-PROGRAM-RESOLUTION-V1.md"
RESULT = "research/results/EXP-20261005-0006.json"
STATE_PUBLICATION = "research/laboratory/EXP-20261005-0006-fitted-state-publication-V1.json"


def write_new(root, relative, value):
    assert not (root / relative).exists(), f"Immutable document already exists: {relative}"
    atomic_write_json(root / relative, value)


def main():
    started = time.monotonic()
    root = Path(__file__).resolve().parents[1]
    prep = load_json(root / PREPARATION)
    assert sha256_file(root / PREPARATION) == "9c91c15cbf19bb5019189a35a2a0b65a1372fdf805cf101049a6c221e6018e58"
    assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
    assert sha256_file(root / RESULT) == "f71073703ceabb1c0062e9f817bb56e440758d13380bddacff0377b4cc6f24a8"
    assert sha256_file(root / "research/results/EXP-20261005-0006.fitted-state.zip") == "3576935b401f6c9324f2f4ed426de104b632a22ba74fb04da55757421f7632a8"
    before = program.status(root)
    assert before["id"] == prep["program_id"] and before["study_path"] == PREPARATION
    assert not before["program_closed"] and not before["paid_run_pending"]
    assert before["pending_fit_reservation_seconds"] == 0 and not before["scoring_authorized"]
    events = read_jsonl(root / "research/events.jsonl")
    assert not any(e.get("event") == "research_program_transfer_prototype_authorized" for e in events)
    current_events = [e for e in events if e.get("program_id") == before["id"]]
    assert {e["charge_id"] for e in current_events if e.get("event") == "research_program_aux_fit_reserved"} == {
        e["charge_id"] for e in current_events if e.get("event") == "research_program_aux_fit_charged"}
    scope = load_json(root / program.TRANSFER_SOURCE_AUTHORITY)
    assert scope["stage_b"]["additional_registration_attempts_cap"] == 12
    assert scope["stage_b"]["additional_compute_seconds_cap"] == 72000
    charge_id = "NEXTAI-B-A-closure-administration-prepaid-V1"
    program.auxiliary_reserve(root, charge_id, 450)
    program.auxiliary_charge(root, charge_id, 450)
    a = program._status_for(root, authority_path=program.CONTINUATION_AUTHORITY,
        contract_path=program.CONTINUATION_CONTRACT, study_path=PREPARATION,
        expected_caps=(17, 69344), authorization_event="research_program_continuation_authorized")
    cumulative = program._continuation_status(root, study_path=PREPARATION)
    events = read_jsonl(root / "research/events.jsonl")
    registrations = [e for e in events if e.get("program_id") == a["id"]
                     and e.get("event") == "research_program_registered"]
    assert len(registrations) == a["registration_attempts_used"] == 11
    evidence = []
    for event in registrations:
        experiment = event["experiment_id"]
        row = {"experiment_id": experiment, "plan_path": event["plan_path"],
               "result_path": f"research/results/{experiment}.json",
               "analysis_path": f"research/analyses/{experiment}.md"}
        row["sha256"] = {path: sha256_file(root / path) for key, path in row.items() if key.endswith("_path")}
        evidence.append(row)
    analysis = f"""# NEXTAI A: verified fresh-final resolution and immutable accounting

## OBSERVATION

A used{a['registration_attempts_used']}/17 tickets and{a['fit_seconds_charged']:.9f}/69344 seconds including{a['experimental_fit_seconds']:.9f} seconds of experiment compute and{a['auxiliary_fit_seconds_conservative']:.9f} conservatively charged auxiliary seconds. The earlier closed MUC03 remains3 tickets/2655.336484700005 seconds. Cumulative usage is{cumulative['registration_attempts_used']} tickets/{cumulative['fit_seconds_charged']:.9f} seconds. All fit, evaluation, failed checks and controller charges remain consumed. Exact figures and all11 immutable plan/result/analysis hashes are in the completion receipt. Unused6 A tickets and{a['fit_seconds_remaining']:.9f} seconds are not added to B.

EXP-20261004-0004 failed before data/fit at runtime path binding.0005 established a competent learned positive control and strong ridge alternative.0006 supported a narrow delta update effect but classical methods remained stronger economically.0007 discarded the exact compact RFF512 recipe.0008 was invalid for its intended capacity/exposure comparison because FIT identity failed; it remains INCONCLUSIVE. EXP-20261005-0001 supported learned transport/PCA, while ridge/PCA-scan was cheaper.0002 did not qualify against its adverse dense reference.0003 tested a distinct dense-noise intervention without proving its causal benefit.0004 failed the selected mixed-reference false-abstention qualification.0005 separately qualified the preregistered unaugmented base-reference comparison.0006 independently tested that frozen selection on five fresh final units. No failed recipe or result was retried, hidden or reinterpreted as a positive.

In0006 all85 workers/1530 trials/489600 answers completed. K32/128/512, updates0/1/4 and both noise levels were frozen. All112 scientific source guards and cache/FIT/data-pairing checks passed. Adverse full-answer means were99.9792% for dense_cached_cpu, transport/PCA and ridge/PCA-scan. Neural transport versus its untrained control improved full answers by75.034722pp,99.375% paired df4 interval[74.953027,75.116417],5/5 positive. The separately controlled confidence families do not establish joint95% coverage across every endpoint. These are five local data/model units, not independent queries or blinded evidence.

Adverse full service per unit was1.920287s dense CPU-cache,0.260759s neural transport/PCA and0.105935s ridge/PCA-scan. Respective p95 query latencies were349.16/65.06/10.50 microseconds; logical states1288704/136192/69888 bytes. Service includes copies/parser/normalization/allocation/ingest/indices/updates/cache/warm-up/query/decode/synchronization/Python outputs. Source fit/calibration/grid/startup costs are separate, fully disclosed and charged. CUDA cumulative allocator/reserved peaks are not total physical VRAM or energy. Public timestamp updates are not learned reasoning.

## INTERPRETATION

Learning the paired coordinate relation is causally supported on the exact local PVM family. Its cheap classical structure is also supported. All8 neural learning/compression gates and competent unaugmented reference guards passed in the final, but all18 neural economic qualification gates did not pass because ridge/PCA-scan is a matched-quality dominator under the fixed-2pp rule. This is not strict accuracy-greater mathematical Pareto dominance. Ridge/PCA-scan passed its18 qualification and60 non-domination gates with no matched-quality dominator. No neural family is falsified, no new architecture or scaling law established, and no LLM/general-intelligence claim justified.

## CONFIDENCE AND DECISION

KEEP the exact learned alignment mechanism as a local control. DISCARD the exact neural end-to-end economic qualification claim against strong classical methods. KEEP the frozen ridge/PCA-scan route for separately preregistered transfer and possible evidence-selected prototype. Closed MUC remains a technical symbolic-control task, not evidence that training is necessary.

A terminates at its contract's verified fresh-final resolution before its global cap. Distinct compact, delta, kernel/ridge, source/cache and observation-exposure alternatives have been assessed; this is not closure from one failed recipe. Transfer to two independent native families and the local fact/source/update/UNKNOWN prototype are unexecuted and transferred to the separately authorized B programme. Whole goal remains ACTIVE. B receives exactly12 additional tickets/72000 seconds, no recycled A credit.

## INTEGRITY AND NEXT DISCRIMINATING EXPERIMENT

Cycle318 is preparation only: no new registration, scored EXP, target content/download or source fit replay. The first full maintenance regression's1335 passes/two failures are preserved and charged; its source-schema DOI/license typing and stale generated-report causes receive an append-only conformance repair. Activation is no scoring; technical completion requires subsequent clone/original conformance receipts. Old evaluated source/manifests/preflight, plans/results and append-only prefixes are preserved. No WT8-9, external models/APIs or schedule changes.

The next separate bounded cycle preregisters one independently sourced native transfer task before implementation/data, five paired units and three justified scales, actual preserved source states versus untrained/shuffled states with identical permitted adaptation, competent target Transformer and strong native classical methods, adverse cases, full costs and fixed simultaneous decision rules. Replication/fresh finals are reserved before acquisition. The cycle318 metadata-only feasibility analysis explicitly preserves subject/writer and finite-data uncertainties. No positive transfer or project-completion inference follows from closing A.
"""
    assert not (root / A_ANALYSIS).exists()
    (root / A_ANALYSIS).write_text(analysis, encoding="utf-8", newline="\n")
    write_new(root, A_RECEIPT, {"id":"NEXTAI-A-CONTINUATION-PROGRAM-COMPLETION-V1", "created_at":utc_now(),
        "program_id":a["id"], "status":"complete_at_verified_fresh_final_resolution",
        "termination_basis":load_json(root/program.CONTINUATION_CONTRACT)["termination"],
        "terminal_study_path":PREPARATION, "terminal_study_sha256":sha256_file(root/PREPARATION),
        "stage_a_budget_before_completion_event":a, "cumulative_budget_before_completion_event":cumulative,
        "unspent_A_credit_added_to_B":False, "unused_A_registration_attempts":17-a["registration_attempts_used"],
        "unused_A_compute_seconds":a["fit_seconds_remaining"], "all_outcomes":evidence,
        "analysis_path":A_ANALYSIS, "analysis_sha256":sha256_file(root/A_ANALYSIS),
        "all_auxiliary_reservations_resolved":True, "research_fit_cycle318":0, "new_registrations_cycle318":0,
        "closure_administration_prepaid_seconds":450,
        "scientific_decisions":{"local_learned_alignment":"KEEP","exact_neural_economics":"DISCARD",
            "local_ridge_pca_fresh_final":"KEEP","transfer_and_prototype":"UNEXECUTED"},
        "technical_B_validation_completed":False, "extended_goal_completed":False})
    append_jsonl(root/"research/events.jsonl", {"event":"research_program_preparation_completed", "created_at":utc_now(),
        "program_id":a["id"], "study_path":PREPARATION, "study_sha256":sha256_file(root/PREPARATION),
        "receipt_path":A_RECEIPT, "receipt_sha256":sha256_file(root/A_RECEIPT), "no_scoring":True})
    append_jsonl(root/"research/events.jsonl", {"event":"research_program_completed", "created_at":utc_now(),
        "program_id":a["id"], "receipt_path":A_RECEIPT, "receipt_sha256":sha256_file(root/A_RECEIPT),
        "completion_reason":"verified_fresh_final_resolution", "extended_goal_completed":False})
    # No event belonging to A may be appended after this point.
    previous = program._continuation_status(root, study_path=PREPARATION, include_raw_current=True)
    a = previous.pop("_raw_current_program")
    assert previous["program_closed"] and a["program_closed"] and a["study_terminal"]
    documents = {program.CONTINUATION_AUTHORITY, program.CONTINUATION_CONTRACT,
        program.TRANSFER_SOURCE_AUTHORITY, PREPARATION, A_RECEIPT, A_ANALYSIS, RESULT, STATE_PUBLICATION,
        "research/results/EXP-20261005-0006.fitted-state.zip",
        "research/laboratory/PVM01-CYCLE-317-COMPLETION-V1.receipt.json",
        "research/analyses/NEXTAI-B-TASK-FEASIBILITY-V1.md",
        "research/plans/NEXTAI-B-METADATA-CONFORMANCE-ADDENDUM-V1.json"}
    for row in evidence:
        documents.update(row["sha256"])
    now = utc_now()
    contract = {"schema_version":1, "id":prep["B_contract_shape_frozen"]["program_id"], "created_at":now,
        "objective":scope["exact_user_objective"], "registration_attempts_cap":12, "fit_seconds_total_cap":72000,
        "prior_budgets_reset":False, "unspent_A_credit_added":False, "no_retry":True,
        "one_new_experiment_per_cycle":True, "schedule_change_authorized":False,
        "wt_files_8_9_access_authorized":False, "external_model_api_authorized":False,
        "stages":[{"id":key,"registration_cap":value} for key,value in program.TRANSFER_STAGES.items()],
        "protected_allocations":program.TRANSFER_RESERVES, "deliverables":scope["deliverables"],
        "economic_claim_gates":load_json(root/program.CONTINUATION_CONTRACT)["economic_claim_gates"],
        "source_result_path":RESULT, "source_state_publication_path":STATE_PUBLICATION,
        "carry_forward":{"program_id":previous["id"], "authority_path":program.CONTINUATION_AUTHORITY,
            "contract_path":program.CONTINUATION_CONTRACT, "terminal_study_path":PREPARATION,
            "completion_receipt_path":A_RECEIPT, "document_sha256":{p:sha256_file(root/p) for p in sorted(documents)},
            "program_events_sha256":sha256_json([e for e in read_jsonl(root/"research/events.jsonl")
                                                   if e.get("program_id")==previous["id"]]),
            **{k:previous[k] for k in ("registration_attempts_used","experimental_fit_seconds",
                "auxiliary_fit_seconds_conservative","fit_seconds_charged")}, "stage_a_accounting":a},
        "auxiliary_fit_accounting":"Reserve before checks; include full process tree wall, failures and conservative overhead; no outside compute",
        "registration_accounting":"Current B tickets1..12; cumulative previous usage displayed; failures/invalidations consume tickets; no paid-plan retry",
        "source_state_rule":"Use actual exported source unit i for paired target unit i, no source fit replay, favorable selection, source arrays/nonces or episode cache",
        "transfer_rule":"Native independent families require their own prospective data/recipe/threshold and source-information controls; target refitting alone is not transfer",
        "alternative_policy":"Preserve each failure; prospectively assess distinct justified alternatives without rescuing a completed test or weakening gates",
        "termination":"Verified final comparisons and reproducible evidence-selected prototype, or documented infeasibility after concrete alternatives; caps report unexecuted scope and do not mean whole-goal completion",
        "first_study_path":B_PREPARATION}
    write_new(root, program.TRANSFER_CONTRACT, contract)
    authority = {"schema_version":1,"id":contract["id"],"created_at":now,
        "program_contract_path":program.TRANSFER_CONTRACT,"program_contract_sha256":sha256_file(root/program.TRANSFER_CONTRACT),
        "source_authority_path":program.TRANSFER_SOURCE_AUTHORITY,"source_authority_sha256":sha256_file(root/program.TRANSFER_SOURCE_AUTHORITY),
        "registration_attempts_cap":12,"fit_seconds_total_cap":72000,
        "user_authorization":scope["exact_user_objective"], "prior_A_closed_and_accounted":True,
        "scoring_requires_independent_frozen_study_readiness":True, "extended_goal_completed":False}
    write_new(root, program.TRANSFER_AUTHORITY, authority)
    completed_aux = sum(e["seconds"] for e in read_jsonl(root/"research/events.jsonl")
        if e.get("event")=="research_program_aux_fit_charged" and str(e.get("charge_id","")).startswith("NEXTAI-B-"))
    b_prep = {"schema_version":1,"id":"NEXTAI-TRANSFER-PREPARATION-V1","created_at":now,"cycle":318,
        "program_id":contract["id"],"program_contract_path":program.TRANSFER_CONTRACT,
        "program_contract_sha256":sha256_file(root/program.TRANSFER_CONTRACT),"cohort":prep["cohort"],
        "study_kind":"preparation_only","stage":"task_design","registration_attempts_for_this_study_cap":0,
        "study_started_at":prep["study_started_at"],"study_deadline_at":prep["study_deadline_at"],
        "resources":{"fit_seconds_study_cap":0,"fit_seconds_per_role_cap":0,
            "auxiliary_test_seconds_cap":4800-completed_aux,"shared_cycle318_auxiliary_cap":4800,"work_minutes_cap":240},
        "parent_preparation_path":PREPARATION,"parent_preparation_sha256":sha256_file(root/PREPARATION),
        "question":"Validate immutable B activation and native-task metadata feasibility; no target data or research execution",
        "forbidden":prep["forbidden"], "decision_rule":prep["decision_rule"],
        "next_discriminating_experiment":"Separate native-family prospective contract before target data/implementation;five paired units,three scales,strong classical and competent dense controls,actual-source/untrained/shuffled controls and one audited EXP"}
    write_new(root,B_PREPARATION,b_prep)
    config=root/"config/research.toml"
    text=config.read_text(encoding="utf-8")
    assert text.count(f'study_path = "{PREPARATION}"') == 1
    config.write_text(text.replace(f'study_path = "{PREPARATION}"',f'study_path = "{B_PREPARATION}"'),encoding="utf-8",newline="\n")
    append_jsonl(root/"research/events.jsonl",{"event":"research_program_study_frozen","created_at":utc_now(),
        "program_id":contract["id"],"study_path":B_PREPARATION,"study_sha256":sha256_file(root/B_PREPARATION),"no_scoring":True})
    append_jsonl(root/"research/events.jsonl",{"event":"research_program_transfer_prototype_authorized","created_at":utc_now(),
        "program_id":contract["id"],"authority_sha256":sha256_file(root/program.TRANSFER_AUTHORITY),
        "contract_sha256":sha256_file(root/program.TRANSFER_CONTRACT),"prior_A_closed":True,"scoring":False})
    after=program.status(root)
    assert after["stage_b_registration_attempts_used"]==0 and after["stage_b_compute_seconds_charged"]==0
    assert after["protected_future_registration_attempts"]==7 and after["protected_future_compute_seconds"]==47000
    assert after["registration_attempts_used"]==14 and not after["scoring_authorized"]
    write_new(root,"research/reviews/NEXTAI-B-one-way-activation-V1.json",{"created_at":utc_now(),
        "program_status":after,"active_authority_sha256":sha256_file(root/program.TRANSFER_AUTHORITY),
        "active_contract_sha256":sha256_file(root/program.TRANSFER_CONTRACT),
        "new_target_data_seen":False,"source_fit_replayed":False,"new_research_EXP":False,
        "elapsed_seconds":time.monotonic()-started,"prepaid_A_administration_bound":450})
    assert time.monotonic()-started<400
    print(json.dumps({"status":"A closed; B preparation active","raw_A_charged":a["fit_seconds_charged"],
        "cumulative_charged":previous["fit_seconds_charged"],"B_charged":0,"B_protected_seconds":47000,
        "elapsed_seconds":time.monotonic()-started}),flush=True)


if __name__=="__main__":
    main()
