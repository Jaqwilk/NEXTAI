from pathlib import Path
p=Path('research/tmp/pvm01_fresh_final_report_v1.py');s=p.read_text()
for old,new in (
 ('independent unaugmented-reference economic comparison','frozen fresh-final quality and full-cost comparison'),
 ('Five NEW paired independent train/dev data/model-seed units','Five NEW paired independent train/frozen-final data/model-seed units'),
 ('source guards107 unchanged; full regression1301 and targeted98 passed','source guards112 unchanged; full regression1310 and targeted112 passed'),
 ('A passing independent comparison justifies a separately frozen fresh final,not promotion.','This frozen five-pair final can confirm the exact route within the visible same-law local task; it does not justify promotion,blinded generalization or transfer.'),
 ('Strong classical controls,three scales and the separate fresh final are required to distinguish these explanations.','The completed three-scale fresh final and earlier independent replication address repeatability here; two independently sourced task families are still required for transfer.'),
 ('V10 uses unchanged V9','V11 delegates unchanged V10/V9 and uses'),
 ('Fresh checkout restores all five exact complete native records','Fresh checkout restores all six exact complete native records'),
 ('## DECISION AND NEXT DISCRIMINATING EXPERIMENT','## DECISION')):
 s=s.replace(old,new)
needle="    '    uv run --no-sync python scripts/restore_pvm01_fresh_final_result.py',"
s=s.replace(needle,"    '    uv run --no-sync python scripts/restore_pvm01_base_reference_result.py',\n"+needle,1)
start=s.index("if confirmed['selected_route_independently_confirmed'] or confirmed['neural_route_independently_confirmed']:")
end=s.index("path=b/f'research/analyses/{eid}.md'",start)
s=s[:start]+'''next_step='In a separate bounded no-scoring cycle,close and hash-bind complete stage A usage and this exact final resolution before activating authorized B12/72000s. Preregister source-frozen transport/PCA versus its preserved untrained/shuffled source controls,competent Transformer and strong classical methods on the first independently sourced transfer family; five paired fresh target units,three scales,ranking/source,retained/updated answers and UNKNOWN separated,legal target-only calibration/adaptation and every preprocessing/fit/service/copy/restore cost disclosed. A second independent family must use licensed public real data. Do not refit source weights or select favorable final/source units. Independently replicate and freeze fresh target finals before an evidence-selected minimal local fact/source/update/UNKNOWN prototype. Each bounded cycle permits one audited EXP; a negative is preserved,not rescued.'
lines += ['', '## NEXT DISCRIMINATING EXPERIMENT','',next_step,'',
    'A remains active until explicit durable resolution/accounting after all current charges. Authorized B is unspent and inactive. Local fresh-final execution is complete;transfer and the prototype remain outstanding and the whole goal stays active.']
fitted=a['fitted_source_states']
lines += ['', '## FITTED SOURCE STATE PROVENANCE','',
    f"All25 fixed source fits preserved before final arrays;complete={fitted['complete']}; bytes={fitted['total_bytes']}; copy/serialization/hash wall={fitted['export_seconds_in_fit_phase']:.6f}s,already included in trusted fit-phase and full worker charges.",
    'Five exact units for transport/PCA,untrained/shuffled transport controls,ridge/PCA-scan and CPU-cache Transformer. Parameter/PCA/ridge hashes match the unchanged fit reports;T-calibrated thresholds and public recipe are included. Source training/final arrays,labels,private nonce,optimizer and episode memory are excluded. Future transfer uses these exact weights without replaying source fit. This artifact preservation is not itself transfer evidence.',
    'Auxiliary failed fixtures and the first maintenance manifest/test-coverage mismatch were recorded before any research seed/data/fit. PVM01-FRESH-FINAL-PRESEED-CONFORMANCE-V1 preserves the old manifest/archive and binds distinct V2 conformance;no scientific recipe,threshold,deadline or budget changed.']
'''+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
p=Path('research/tmp/pvm01_fresh_final_report_metadata_v1.py');s=p.read_text().replace('independent confirmation','frozen fresh final').replace('Current v10 maintenance','Current v11 maintenance').replace('Expanded final/transfer/prototype goal remains open','Local same-law final completed;expanded transfer/prototype goal remains open');p.write_text(s,encoding='utf-8',newline='\n')
print('Final-specific report and next-cycle A closure/B proposal; no new experimental claims from formatter')