"""Write the prospective recipe before any ASM parser/model or coordinate access."""
from copy import deepcopy
import json
from pathlib import Path

from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


root = Path(__file__).resolve().parents[1]
destination = root / 'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json'
assert not destination.exists(), 'Prospective plan is immutable after creation'
task_path = 'research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json'
task = json.loads((root / task_path).read_text(encoding='utf-8'))
plan = deepcopy(json.loads((root / 'research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json').read_text(encoding='utf-8')))
plan.update(id='ASM01-FROZEN-SOURCE-SCREEN-V1', created_at=utc_now(), cycle=321,
            stage='transfer_family_2_screen', study_kind='asm01_frozen_source_transfer',
            cohort='asm01_native_memory_v1', task_contract_path=task_path,
            task_contract_sha256=sha256_file(root / task_path),
            study_started_at='2026-10-05T18:50:32Z', study_deadline_at='2026-10-05T21:50:32Z',
            registration_attempts_for_this_study_cap=1,
            question=task['question'],
            parent_completion_receipt_path='research/laboratory/FAMILY2-CYCLE320-COMPLETION-V1.receipt.json',
            parent_completion_receipt_sha256=sha256_file(root / 'research/laboratory/FAMILY2-CYCLE320-COMPLETION-V1.receipt.json'))
rename = lambda name: name.replace('har01_', 'asm01_').replace('native_shift', 'native_dtw')
plan['candidates'] = [rename(name) for name in plan['candidates']]
plan['roles'] = {rename(name): dict(role, arm='native_dtw' if role['arm']=='native_shift' else role['arm'])
                 for name, role in plan['roles'].items()}
plan['resources'].update(work_minutes_cap=180, auxiliary_test_seconds_cap=3600,
                         startup_charge_included_seconds=222,
                         administration_prepaid_seconds_cap=300,
                         protected_future_tickets=7, protected_future_compute_seconds=47000)
recipe = plan['recipe']
recipe.update(kernel_landmarks=64,
              target_kernel='Same existing RBF Nystrom transport; first64 distinct fit samples, not repeated draw landmarks. Bandwidth/ridge grids unchanged, jitter1e-10, validation MSE and deterministic ascending ties; all grid fits charged.',
              native_raw='No-fit cosine retrieval on the same normalized public32x2 trajectory views; no sample/class/writer ID or private trajectory.',
              native_dtw='Exact band4 DTW on SAME public32x2 unit-L2 views. Local cost32*sum((x_i-y_j)^2). Dynamic program minimizes total squared cost within |i-j|<=4, starts(0,0), ends(31,31), allowed diagonal/up/left with that deterministic tie priority. Track length of selected minimum-sum path; d=sum/length. Similarity=1/(1+d). All distances, DP state/allocation and selection work charged. No private full trajectory.',
              margin_grid=[0., .005, .01, .02, .04, .08, .16, .32],
              score_normalization='For all cosine routes clip score[-1,1] then s=(1+cosine)/2. NativeDTW uses1/(1+d). Stable top1 is lowest insertion slot on ties; margin=top1_score-second_highest_score. Accept iff s>=absolute_threshold AND margin>=margin_threshold. Same two-axis policy for all9arms.',
              threshold_selection='All27 nominal T-calibration episodes (3Kx3updatecountsx3episodes), same144 absolute/margin pairs for all9arms. Eligible iff knownFA<=.02 and UNKNOWN>=.95. Eligible first, then maximize full answer accuracy, higher UNKNOWN, lower absolute threshold, lower margin threshold, in that order. If none eligible retain best same ordered tuple and mark infeasible. No D threshold selection.')
recipe.pop('native_shift')
plan['data'].pop('screen_subjects')
plan['data']['screen_writers'] = [dict(unit=i, train_writer=i+1, dev_writer=i+16, source_unit=i) for i in range(5)]
plan['data'].update(fit_instances=64, validation_instances=24, calibration_instances=95,
                    train_pair_draw_rule='One private permutation of183 sample IDs for each T writer:64fit/24validation/95calibration.4096 training pairs start with those64 distinct fit IDs, then4032 replacement draws.512 validation pairs start with24 distinct validation IDs, then488 replacement draws. Same pairs/all nine arms; repeats do not create independent samples.',
                    legal_inputs='Only normalized64 native coordinates and legal random fact/source/version write metadata and T training labels. No sample, character or writer identifier on queries or in model features; no character-name/class label or Data_Table.pdf.',
                    acquisition=task['intake'], independent_units=task['independent_units'])
plan['native_parser'] = {
    'primary_format_source': 'https://archive.ics.uci.edu/dataset/208/online+handwritten+assamese+characters+dataset',
    'reviewed_before_coordinate_content': True,
    'filename_identity': 'Publisher M.N.txt has CHARACTER M(1..183), WRITER N(1..45). Require exactly8235 unique pairs,45 writer IDs and183 native samples/writer. Directory names are ancillary, never identity features. All path/size metadata may be inspected; decode ONLY screen writers1..5/16..20.',
    'sample_bytes_cap': 262144, 'points_per_sample_cap': 32768,
    'grammar': 'ASCII text; ignore blank lines. First CHARACTER_NAME: suffix discarded without matching names/classes. STROKE_COUNT: positive integer. PEN_DOWN/PEN_UP may be standalone markers or tab/space-delimited records with empty coordinate/state fields; any supplied stroke serial must match the current1-based stroke. Numeric point rows exactly4 integer fields X,Y,STYLUS_STATE,STROKE: X0..4392,Y0..4868, state1, current stroke. PEN_UP state if supplied must be0. PEN_DOWN state if supplied blank. Require alternating DOWN/UP, declared count matches strokes, terminal END_CHARACTER: suffix ignored; reject unknown rows/nonfinite/out-of-range/unsafe sizes. No after-content schema rescue.',
    'trajectory': 'Concatenate only pen-down coordinates in stroke order after removing consecutive duplicates WITHIN each stroke. At least4 remaining points required. Even zero-based indices =>write, odd=>query. Adverse query drops index3,7,11,... of its selected query points before resampling. Each required view needs>=2 distinct positions and positive arc length; otherwise intake invalid. Never drop/replace selected native sample.',
    'resampling': 'After separators removed, cumulative Euclidean arc length includes straight chords between strokes, a disclosed deterministic representation rather than physical pen movement. Interpolate X and Y at32 uniformly spaced cumulative distances inclusive endpoints. Remove zero-length intervals for interpolation. Subtract each view centroid; RMS=sqrt(mean(sum(centered_xy^2,axis=1))); divide by RMS*sqrt(32), flatten64 float32. This fixed unit-L2 rescaling makes the proposed RMS representation compatible with frozen source64D inputs; same for every arm. No fitted target normalizer; transform is per-observation only.',
    'dependence': task['native_views']['within_identity_dependence'],
    'invalidity': task['native_views']['invalidity_policy']}
publication_path = 'research/laboratory/EXP-20261005-0006-fitted-state-publication-V1.json'
plan['source_evidence'] = dict(experiment_id='EXP-20261005-0006', publication_path=publication_path,
                               publication_sha256=sha256_file(root / publication_path),
                               pairing='Actual exported source unit i to fixed writer pair i. All25 source/PCA/ridge arrays exactly preserved; no source fit replay, source nonces/data or cache.',
                               no_source_refit=True)
plan['diagnosis_gates']['economic_qualification']['strong_classical_nondomination'] = plan['diagnosis_gates']['economic_qualification']['strong_classical_nondomination'].replace('native_shift','native_dtw')
plan['cost_boundary'] = dict(service='Raw pen-down paths already in memory -> descriptor, copies, service-state construction/restoration, ingest/index/cache, all updates, warmup, query and current value/source/UNKNOWN decode. Cold cost additionally includes bounded acquisition, archive decompression, text parsing, all grids/fit/calibration, process supervision and copied/compressed file reads.',
                             attribution='Same acquisition shared once in aggregate and disclosed separately; per-route amortized totals include it. Sunk original source fit disclosed without replay/charging it again to B; all new work and failures charged.',
                             energy_measured=False)
plan['storage_recovery'] = dict(method='Transparent NTFS LZX with every file path and SHA256 preserved; no deletion or OS setting changes.',
                              scope='Only JSON/JSONL/TXT/LOG files>=256KiB inside completed EXP-20261005-0001..0007-runtime archives in original/clone and matching closed clone research/tmp/EXP folders; no source NPZ, WT, other projects or fresh-data files.',
                              file_count_cap=12000, total_logical_bytes_cap=20000000000,
                              before_after_hash_required=True, auxiliary_cap_seconds=650)
plan['intake_failure_policy'] = 'Stop unstarted fitting/scoring on archive/identity/grammar/degeneracy/resource/deadline/source invalidity; retain exact bytes, costs and partial evidence. No paid retry or new source/writer replacement. Conformance fixes on synthetic public fixtures only before real content; no after-content recipe changes.'
plan['forbidden'] = ['paid retry','source refit','future writer coordinate access','WT8-9','external model/API','schedule changes','weakened gates','completed scientific artifact modification']
atomic_write_json(destination, plan)
append_jsonl(root / 'research/events.jsonl', dict(event='research_study_preregistered',created_at=utc_now(),cycle=321,
             study_path=str(destination.relative_to(root)).replace('\\','/'),study_sha256=sha256_file(destination),
             before_implementation=True,before_native_coordinate_content=True,program_id='NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1'))
print(json.dumps(dict(path=str(destination),sha256=sha256_file(destination),roles=len(plan['roles']),deadline=plan['study_deadline_at'],all_new_native_arrays_unseen=True)))
