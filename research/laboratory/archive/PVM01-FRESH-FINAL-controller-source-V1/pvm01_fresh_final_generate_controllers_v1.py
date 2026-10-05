from pathlib import Path
b=Path.cwd();source=b/'research/laboratory/archive/PVM01-BASE-REFERENCE-final-controller-source-V1'
helpers=('history','commit_validated','freeze','prepaid','commit_certified','execute','post','publish','report','report_metadata','integrate','original_check','close','final_sync','final_administration')
for name in helpers:
    p=b/f'research/tmp/pvm01_fresh_final_{name}_v1.py';assert not p.exists()
    s=(source/f'pvm01_base_reference_{name}_v1.py').read_text(encoding='utf-8')
    for old,new in (
        ('PVM01-BASE-REFERENCE-CONFIRMATION-V1','PVM01-FRESH-FINAL-V1'),('PVM01-BASE-REFERENCE-','PVM01-FRESH-FINAL-'),
        ('pvm01_base_reference_','pvm01_fresh_final_'),('paired_view_mutable_memory_v10','paired_view_mutable_memory_v11'),
        ('EXP-20261005-0005','EXP-20261005-0006'),('PVM01-CYCLE-316','PVM01-CYCLE-317'),
        ('cycle316','cycle317'),("'cycle':316","'cycle':317"),("'closed_cycle':316","'closed_cycle':317"),
        ('109f421bbae55f436224d97b7c9a9d22ecc6f340','28cff0932543303de1c065ba01205c3096125757'),
        ('1272','1301'),('all107','all112'),('All107','All112'),('all 107','all 112'),
        ("scientific_sources_unchanged':107","scientific_sources_unchanged':112"),("scientific_source_files_unchanged':107","scientific_source_files_unchanged':112"),
        ('-PVM01-base-reference-analysis.json','-PVM01-fresh-final-analysis.json'),
        ('analyze_pvm01_base_reference.py','analyze_pvm01_fresh_final.py'),('run_pvm01_base_reference_check.py','run_pvm01_fresh_final_check.py'),
        ('test_pvm01_base_reference.py','test_pvm01_fresh_final.py'),('restore_pvm01_base_reference_result.py','restore_pvm01_fresh_final_result.py'),
        ('c316p1','c317p1'),('>=24000','>=20800')):
        s=s.replace(old,new)
    if name=='freeze':s=s.replace("old=b'benchmark_version = \"paired_view_mutable_memory_v9\"'","old=b'benchmark_version = \"paired_view_mutable_memory_v10\"'")
    if name=='commit_validated':s=s.replace("exact={", "exact={'src/nextai_autoresearch/pvm01_fitted_state.py',",1)
    if name=='post':s=s.replace("'fresh_final_executed':False","'fresh_final_executed':True")
    if name in ('original_check','final_sync'):
        # Add the fifth preceding result; no old restorer may be omitted.
        needle="'scripts/restore_pvm01_fresh_final_result.py'"
        if needle in s:s=s.replace(needle,"'scripts/restore_pvm01_base_reference_result.py',"+needle,1)
        # Some helpers use bare script names in a tuple.
        needle="'restore_pvm01_fresh_final_result.py'"
        if needle in s:s=s.replace(needle,"'restore_pvm01_base_reference_result.py',"+needle,1)
        s=s.replace("range(1,6)","range(1,7)").replace("range(1, 6)","range(1, 7)")
    if name=='prepaid':s=s.replace("'fresh_final_executed':False","'fresh_final_executed':False")
    p.write_text(s,encoding='utf-8',newline='\n')
for p in (b/'research/tmp').glob('pvm01_fresh_final_*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
print('Administrative controllers adapted; post-run formatters still require current final-specific review')