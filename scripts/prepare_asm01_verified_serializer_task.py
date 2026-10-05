"""Version the prospective native task; grant no scientific execution authority."""
import json
from pathlib import Path

from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI"
parent_path = "research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json"
path = "research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json"
native_path = "research/reviews/ASM01-EXPOSED-T1-SERIALIZER-CONFORMANCE-V1.json"
repair_path = "research/plans/ASM01-SERIALIZER-METADATA-REPAIR-V1.json"
assert not (root / path).exists()
native = json.loads((root / native_path).read_text())
assert native["complete"] and native["independent_point_reference_equal"] and native["all3_descriptors_equal"]
assert native["new_samples_opened"] == native["D_samples_opened"] == native["fit"] == 0
old = json.loads((root / parent_path).read_text())
task = json.loads(json.dumps(old))
task.update(id="ASM01-VERIFIED-SERIALIZER-TASK-V3", cohort="asm01_native_memory_v3", created_at=utc_now(),
            execution_authority=False, status="prospective_task_requires_separate_study_and_finished_clone_validation",
            invalid_parent_task_path=parent_path, invalid_parent_task_sha256=sha256_file(root / parent_path),
            revision_reason="Preserve failed V1/V2 intake and V3 technical header result. Exact exposed T1 now passes separately preregistered singleton-zero metadata normalization; numeric/geometry/model/metrics/threshold/grids unchanged. T1 is already exposed, not fresh or blinded; new scientific intake/cohort still required.",
            preparation_parent_path="research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json",
            preparation_parent_sha256=sha256_file(root / "research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json"))
task["serializer"] = {
    "module": "nextai_autoresearch.asm01_task_v4", "source_path": "src/nextai_autoresearch/asm01_task_v4.py",
    "source_sha256": sha256_file(root / "src/nextai_autoresearch/asm01_task_v4.py"),
    "repair_path": repair_path, "repair_sha256": sha256_file(root / repair_path),
    "known_T1_conformance_path": native_path, "known_T1_conformance_sha256": sha256_file(root / native_path),
    "grammar": "Exact public column header once immediately after STROKE_COUNT enables singleton PEN_UP0 release annotation; remove only that zero. All other marker forms keep V3 semantics. Delegate all points, current positive stroke serial/state1/XY bounds, byte/point caps, alternating pen/count checks and geometry to unchanged V3/V1. No unfamiliar-row inference or sample dropping.",
    "scope_limit": "Technical conformance on ONE already-exposed T1; no guarantee of remaining writers or array feasibility. New scientific intake stops on any required unknown/missing/degenerate native sample without rescue or replacement.",
}
task["source"].update(arrays_seen=True, already_exposed_T1_processed_in_technical_conformance=True,
                      all_other_native_coordinate_arrays_seen=False,
                      coordinate_values_emitted_to_assistant=False)
task["intake"]["sequence"] = (
    "Freeze a NEW complete scientific study/cohort and versioned delegated wrappers before remaining native T/D "
    "content. Reuse exact preserved publisher; verify canonical archive map, bounded footprint/disk gate and "
    "frozen V4 parser. Process all1830 screen samples without dropping/replacing any; disclose previously exposed "
    "T1 and never call its bytes fresh. D remains numerically unopened until that study. Future replication/final "
    "files and Data_Table.pdf remain unopened. Clone/preflight/readiness before one audited EXP, no paid retry.")
task["next_action"] = (
    "Separate bounded ASM01-FROZEN-SOURCE-SCREEN-V3 preregistration with exact unchanged source states/models, "
    "4096pairs/2048alignment/1024decoder, all9arms, five fixed writer pairs,3K/updates/nominal-adverse, "
    "grids,metrics and gates; explicit remaining global/protected budgets. Then minimal delegated cohort/loader "
    "and acquisition adapters, independent-clone conformance, complete native feasibility,freeze/preflight/readiness "
    "before exactly one audited EXP. This task artifact grants no fit,registration,scoring or new-data access.")
for key in ("comparison", "metrics", "training", "native_views", "independent_units"):
    assert task[key] == old[key], key
atomic_write_json(root / path, task)
append_jsonl(root / "research/events.jsonl", {
    "event": "prospective_task_contract_prepared", "created_at": utc_now(), "cycle": 323,
    "task_path": path, "task_sha256": sha256_file(root / path), "execution_authority": False,
    "known_T1_only": True, "scientific_recipes_metrics_gates_unchanged": True,
})
print(json.dumps({"prospective_task_path": path, "task_sha256": sha256_file(root / path),
                  "execution_authority": False, "science_unchanged": True}), flush=True)
