from pathlib import Path
import json
b=Path.cwd();source=b/'research/laboratory/archive/PVM01-CONFIRMATION-final-controller-source-V1'
helpers=('history','commit_validated','freeze','prepaid','commit_certified','execute','post','publish','report','report_metadata','integrate','original_check','close','final_sync')
for name in helpers:
    old=source/f'pvm01_confirmation_{name}_v1.py';p=b/f'research/tmp/pvm01_base_reference_{name}_v1.py';assert not p.exists()
    s=old.read_text(encoding='utf-8')
    for old_text,new_text in (
        ('PVM01-DENSE-NOISE-CONFIRMATION-V1','PVM01-BASE-REFERENCE-CONFIRMATION-V1'),
        ('PVM01-CONFIRMATION-','PVM01-BASE-REFERENCE-'),('pvm01_confirmation_','pvm01_base_reference_'),
        ('paired_view_mutable_memory_v9','paired_view_mutable_memory_v10'),
        ('EXP-20261005-0004','EXP-20261005-0005'),('PVM01-CYCLE-315','PVM01-CYCLE-316'),
        ('cycle315','cycle316'),("'cycle':315","'cycle':316"),("'closed_cycle':315","'closed_cycle':316"),
        ('ecbbb2b3cfebb331944350766e49b3f5f62d23f0','109f421bbae55f436224d97b7c9a9d22ecc6f340'),
        ('1238','1272'),('all102','all107'),('All102','All107'),('all 102','all 107'),('files_unchanged\':102','files_unchanged\':107'),
        ('scientific_sources_unchanged\':102','scientific_sources_unchanged\':107'),
        ('PVM01-BASE-REFERENCE-full-V2','PVM01-BASE-REFERENCE-full-V1'),
        ('PVM01-BASE-REFERENCE-history-source-V2','PVM01-BASE-REFERENCE-history-source-V1'),
        ('analyze_pvm01_confirmation.py','analyze_pvm01_base_reference.py'),
        ('run_pvm01_confirmation_check.py','run_pvm01_base_reference_check.py'),
        ('test_pvm01_confirmation.py','test_pvm01_base_reference.py'),
        ('restore_pvm01_confirmation_result.py','restore_pvm01_base_reference_result.py'),
        ('-PVM01-confirmation-analysis.json','-PVM01-base-reference-analysis.json'),
        ('PVM01-BASE-REFERENCE-CLASSICAL','PVM01-BASE-REFERENCE-CLASSICAL'),
        ('PVM01-BASE-REFERENCE-prepaid-V2','PVM01-BASE-REFERENCE-prepaid-V1')):
        s=s.replace(old_text,new_text)
    if name=='history':s=s.replace("'all107_scientific_source_bytes_preserved'","'all107_scientific_source_bytes_preserved'")
    if name=='freeze':s=s.replace("old=b'benchmark_version = \"paired_view_mutable_memory_v8\"'","old=b'benchmark_version = \"paired_view_mutable_memory_v9\"'")
    if name=='commit_validated':
        s=s.replace("'src/nextai_autoresearch/worker_resource_peaks.py','tests/test_pvm01_base_reference.py'", "'scripts/analyze_pvm01_base_reference.py','tests/test_pvm01_base_reference.py','research/reviews/PVM01-BASE-REFERENCE-startup-observation-V1.json'")
        s=s.replace("exact={'config/research.toml'", "exact={'.gitattributes','research/reviews/PVM01-BASE-REFERENCE-startup-observation-V1.json','config/research.toml'")
    if name=='prepaid':
        s=s.replace("value['continuation_registration_attempts_cap']-value['continuation_registration_attempts_used']-1", "value['continuation_registration_attempts_cap']-value['continuation_registration_attempts_used']-1")
        start=s.index("charged=sum(e['seconds']")
        end=s.index("reserves=study['programme_reserves']",start)
        s=s[:start]+'''events=read_jsonl(b/'research/events.jsonl')
charges={e['charge_id']:e['seconds'] for e in events if e.get('event')=='research_program_aux_fit_charged'}
reservations=[e for e in events if e.get('event')=='research_program_aux_fit_reserved' and str(e.get('charge_id','')).startswith('PVM01-BASE-REFERENCE-')]
effective=sum(charges.get(e['charge_id'],e['seconds_cap']) for e in reservations)
assert effective<=3600
assert value['fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']-(3600-effective)>=24000
'''+s[end:]
        s=s.replace("scientific_sources_unchanged':102","scientific_sources_unchanged':107")
        s=s.replace("'PVM01-BASE-REFERENCE-history-source-V1'", "'PVM01-BASE-REFERENCE-history-source-V1'")
    if name=='commit_certified':
        s=s.replace("'research/checks/PVM01-BASE-REFERENCE-'", "'research/checks/PVM01-BASE-REFERENCE-'")
    p.write_text(s,encoding='utf-8',newline='\n')
# Do not execute copied post-run formatters until adapted to the new frozen question.
for p in (b/'research/tmp').glob('pvm01_base_reference_*.py'):
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
print('Prospective administrative controllers generated and parsed; no scored data/model execution')