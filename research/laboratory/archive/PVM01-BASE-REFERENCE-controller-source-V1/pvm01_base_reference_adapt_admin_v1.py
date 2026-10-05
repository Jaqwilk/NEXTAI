"""Adapt administrative reports only; no scientific implementation/data execution."""
from pathlib import Path
import ast

b = Path.cwd()
t = b/'research/tmp'
def update(name, old, new):
    p=t/f'pvm01_base_reference_{name}_v1.py'
    s=p.read_text(encoding='utf-8'); assert old in s,(name,old[:70])
    p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')

update('publish', "out=b/'research/tmp/PVM01-BASE-REFERENCE-publication-conformance-V1'", "out=b/'research/tmp/c316p1'")
update('publish', "if label=='good':assert run.returncode==0 and sha256_file(dest/native.name)==metadata['native_sha256']", "if label=='good':\n        assert run.returncode==0 and sha256_file(dest/native.name)==metadata['native_sha256']\n        assert len(resource_rows)==85\n        assert all(sha256_file(root/row['resource_peaks_path'])==row['resource_peaks_sha256'] for row in resource_rows)")
update('original_check', "('restore-confirmation',['python','scripts/restore_pvm01_base_reference_result.py'],o),", "('restore-confirmation',['python','scripts/restore_pvm01_confirmation_result.py'],o),\n ('restore-base-reference',['python','scripts/restore_pvm01_base_reference_result.py'],o),")
update('original_check','all_four_native_hashes_verified','all_five_native_hashes_verified')
update('integrate','PVM01-BASE-REFERENCE-publication-completion-V2','PVM01-BASE-REFERENCE-publication-V1')
for name in ('integrate','close'):
    update(name,"['continuation_registration_attempts_used']==9","['continuation_registration_attempts_used']==10")
for name in ('close','final_sync'):
    update(name,"'EXP-20261005-0003','EXP-20261005-0005'","'EXP-20261005-0003','EXP-20261005-0004','EXP-20261005-0005'")
update('integrate',"'research/analyses/EXP-20261005-0003-CUDA-TELEMETRY-ADDENDUM-V1.md'", "'research/reviews/EXP-20261005-0005-confirmation-diagnosis-V1.json'")
update('integrate','Preserve dense-noise intervention, frozen decisions and complete raw provenance','Preserve base-reference comparison, frozen decisions and complete raw provenance')
update('final_sync','Close paired dense-noise cycle with exact lineage and conserved full costs','Close base-reference cycle with exact lineage and conserved full costs')

p=t/'pvm01_base_reference_report_metadata_v1.py'; s=p.read_text(encoding='utf-8')
start=s.index('# Correct the previous report'); end=s.index('freeze_manifest(b',start)
s=s[:start]+s[end:]; s=s.replace('Current v9 maintenance','Current v10 maintenance').replace('Report/append-only clarification/terminal maintenance','Report/terminal maintenance')
s=s.replace("f'Reference confirmed=", "f'Main UN-AUGMENTED reference confirmed=")
s=s.replace("f'All107 scientific source", "f'Ancillary mixed-reference NI remains separately reported with unchanged gates.\\n'\n        f'All107 scientific source")
p.write_text(s,encoding='utf-8',newline='\n')

p=t/'pvm01_base_reference_report_v1.py';s=p.read_text(encoding='utf-8')
s=s.replace("selection=a['reference_selection']; neural=a['neural_economics_against_mixed_reference']; classic=a['selected_classical_route_confirmation']", "mixed=a['reference_selection']; selection=a['base_reference_confirmation']; neural=a['unaugmented_reference_economics']['transport_pca']; classic=a['unaugmented_reference_economics']['ridge_pca_scan']")
s=s.replace('independent selected-reference and classical-route confirmation','independent unaugmented-reference economic comparison')
s=s.replace("for arm in ('dense_cached_cpu_mixed','transport_pca','ridge_pca_scan'):","for arm in ('dense_cached_cpu','dense_cached_cpu_mixed','transport_pca','ridge_pca_scan'):")
s=s.replace('Reference6 endpoints use99.166667% intervals','Ancillary mixed-reference6 endpoints use99.166667% intervals')
s=s.replace('each mixed unit/noise FA<=2%; all six dense variants competent','each mixed unit/noise FA<=2%; all six dense variants competent for the ancillary augmentation qualification. The distinct main base-reference question requires all three base variants competent and each base CPU-cache unit/noise FA<=2%,without a base-versus-itself NI test')
s=s.replace("for key,value in selection['primary_simultaneous_intervals'].items(): lines.append(f\"| {key} | {bounds(value,100.)} | {selection['primary_gates'][key]} |\")", "for key,value in mixed['primary_simultaneous_intervals'].items(): lines.append(f\"| ancillary mixed {key} | {bounds(value,100.)} | {mixed['primary_gates'][key]} |\")")
s=s.replace('vs mixed CPU-cache endpoint','vs UN-AUGMENTED CPU-cache endpoint')
start=s.index("    f\"Reference: {selection['decision']}");end=s.index("    'A learned alignment effect",start)
s=s[:start]+'''    f"Main base reference: {selection['decision']}; competent={selection['base_reference_competent']}; all ten unit/noise guards={all(selection['each_unit_false_abstention_guards'].values())}.",
    f"Ancillary augmentation: {mixed['decision']}; causal false-abstention improvement={mixed['causal_false_abstention_improvement']}; failed NI gates={[k for k,v in mixed['primary_gates'].items() if not v]}.",
    f"Neural economics vs BASE: {neural['decision']}; fixed matched-quality dominators={neural['matched_quality_dominators']}.",
    f"Classical economics vs BASE: {classic['decision']}; fixed matched-quality dominators={classic['matched_quality_dominators']}.",
    'Reference adequacy alone does not establish augmentation benefit. The separately preregistered main question compares fixed routes with the competent unaugmented Transformer; all earlier mixed-reference qualifications and failures remain unchanged. No prior unit or weight is pooled into this new five-unit result.',
    'Joint qualification uses the original eight learning/compression endpoints,18 economic and60 fixed-comparator checks plus competent base controls and ten unit/noise FA guards. The old six mixed NI endpoints are ancillary in this prospectively distinct study and retain their own interpretation. The main economic result does not rescue the completed mixed-reference qualification.',
''' + s[end:]
s=s.replace("    '', '## CONFIDENCE'", "    '', '## ALTERNATIVE EXPLANATIONS','', 'The public synthetic identity law may favour linear transport/retrieval. Exact cache parity checks inference implementation,not generalization. Fresh units address seed/data repeatability in one family; they do not establish cross-family transfer. Rare abstention errors and hardware/load-dependent timings remain possible. Strong classical controls,three scales and the separate fresh final are required to distinguish these explanations.',\n    '', '## CONFIDENCE'")
s=s.replace('V9 trusted CUDA snapshots','V10 uses unchanged V9 trusted CUDA snapshots')
s=s.replace('source guards102 unchanged; full regression1272 and targeted102 passed','source guards107 unchanged; full regression1272 and targeted98 passed')
start=s.index("    'Failed pre-data full-V1 timeout");end=s.index("    f\"A remaining at report creation",start)
s=s[:start]+"    'Every auxiliary check,including a failed check if one occurred,is retained and charged. Current-cycle failed receipts are listed in the completion record. No paid-plan retry or scientific gate change is permitted. The readiness reserve counts completed charges OR live reserved caps once.',\n"+s[end:]
s=s.replace('Full worker cap20400s,per-fit210s,per-worker236s with external240s','Full worker cap10200s,per-fit90s,per-worker116s with external120s')
s=s.replace('all four exact','all five exact').replace("    '    uv run --no-sync python scripts/restore_pvm01_base_reference_result.py',", "    '    uv run --no-sync python scripts/restore_pvm01_confirmation_result.py',\n    '    uv run --no-sync python scripts/restore_pvm01_base_reference_result.py',")
start=s.index('next_step=(');end=s.index('lines += [next_step',start)
s=s[:start]+'''if confirmed['selected_route_independently_confirmed'] or confirmed['neural_route_independently_confirmed']:
    selected='ridge/PCA-scan' if confirmed['selected_route_independently_confirmed'] else 'neural transport/PCA'
    next_step=f'Preregister a separately frozen fresh-final five-pair comparison of exact {selected} against the UN-AUGMENTED dense_cached_cpu reference,all17 arms,three scales,both noises,updates0/1/4,strong controls and unchanged scientific thresholds. Exclude ALL prior selecting/replication/confirmation train/dev units,seeds,nonces and weights. Validate in clone,freeze/preflight/readiness before fresh arrays and exactly one audited EXP in a NEW cycle. Keep the ancillary mixed NI assay distinct. Use the remaining final-stage ticket and at least24000s reserved; no promotion from this cohort.'
else:
    next_step='Close this exact base-reference qualification as negative or inconclusive according to the frozen controls. The reference_and_alternatives cap is exhausted; do not add steps or silently weaken a failed gate. Explicitly account for stage A and all consumed tickets/costs,including the exact unexecuted final scope,before activating authorized stage B for alternative task/prototype routes. Preserve existing final funds and all outcomes; a new distinct question needs a prospective contract and fresh data.'
''' +s[end:]
s=s.replace("'reference_failed_gates':[k for k,v in selection['primary_gates'].items() if not v]", "'base_reference_failed_competence':[k for k,v in selection['competence_gates'].items() if not all(v.values())],'ancillary_mixed_failed_gates':[k for k,v in mixed['primary_gates'].items() if not v]")
p.write_text(s,encoding='utf-8',newline='\n')

p=t/'pvm01_base_reference_close_v1.py';s=p.read_text(encoding='utf-8')
s=s.replace("neural=a['neural_economics_against_mixed_reference'];classic=a['selected_classical_route_confirmation'];selection=a['reference_selection']", "neural=a['unaugmented_reference_economics']['transport_pca'];classic=a['unaugmented_reference_economics']['ridge_pca_scan'];selection=a['base_reference_confirmation'];mixed=a['reference_selection']")
s=s.replace("'targeted_tests_passed':102","'targeted_tests_passed':98")
start=s.index("    'failed_postrun_checks_preserved':");end=s.index("    'all107_parent_scientific_source",start)
s=s[:start]+'''    'failed_current_cycle_checks_preserved':[p.relative_to(b).as_posix() for p in sorted((b/'research/reviews').glob('PVM01-BASE-REFERENCE-*.json')) if isinstance((v:=json.loads(p.read_text(encoding='utf-8'))).get('result'),dict) and (v['result'].get('returncode') not in (None,0) or v.get('error'))],
    'native_checkout_conformance':'research/checks/PVM01-BASE-REFERENCE-native-checkout-V1.json',
''' +s[end:]
s=s.replace("'old_nonmutable_raw_files':45355", "'old_nonmutable_raw_files':read('research/reviews/PVM01-BASE-REFERENCE-history-clone-postrun-V1.json')['old_nonmutable_raw_files']")
s=s.replace("'reference_qualified':selection['adequate_for_prospective_selection'],'causal_false_abstention_improvement':selection['causal_false_abstention_improvement']", "'reference_qualified':selection['adequate_for_economic_comparison'],'ancillary_mixed_reference_qualification':mixed['adequate_for_prospective_selection'],'ancillary_causal_false_abstention_improvement':mixed['causal_false_abstention_improvement']")
s=s.replace("'reference_failed_primary_gates':[k for k,v in selection['primary_gates'].items() if not v]", "'reference_failed_competence':[k for k,v in selection['competence_gates'].items() if not all(v.values())],'ancillary_mixed_failed_primary_gates':[k for k,v in mixed['primary_gates'].items() if not v]")
p.write_text(s,encoding='utf-8',newline='\n')

source=b/'research/laboratory/archive/PVM01-CONFIRMATION-final-controller-source-V1/pvm01_confirmation_final_administration_v1.py'
s=source.read_text(encoding='utf-8').replace('PVM01-CONFIRMATION-','PVM01-BASE-REFERENCE-').replace('pvm01_confirmation_','pvm01_base_reference_').replace('c315-admin','c316-admin')
(t/'pvm01_base_reference_final_administration_v1.py').write_text(s,encoding='utf-8',newline='\n')
for p in t.glob('pvm01_base_reference_*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
print('Administrative controllers adapted and parsed; no scientific files changed')
