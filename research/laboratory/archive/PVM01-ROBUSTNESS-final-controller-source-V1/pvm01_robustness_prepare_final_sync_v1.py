from pathlib import Path
b=Path.cwd()
s=(b/'research/tmp/pvm01_replication_final_sync_v1.py').read_text().replace('PVM01-REPLICATION-','PVM01-ROBUSTNESS-').replace('PVM01-CYCLE-313-','PVM01-CYCLE-314-').replace('closed_cycle\':313','closed_cycle\':314').replace('EXP-20261005-0002','EXP-20261005-0003')
start=s.index("for name in ['pvm01_replication_integrate_v1.py'")
end=s.index("    target=b/",start)
s=s[:start]+"for name in [p.name for p in sorted((b/'research/tmp').glob('pvm01_robustness_*.py'))]:\n"+s[end:]
s=s.replace("    pub=json.loads((root/'research/laboratory/EXP-20261005-0003-publication-V2.json').read_text())\n    assert sha256_file(root/pub['native_path'])==pub['native_sha256']", "    for identity in ('EXP-20261005-0001','EXP-20261005-0002','EXP-20261005-0003'):\n        pub=json.loads((root/f'research/laboratory/{identity}-publication-V2.json').read_text())\n        assert sha256_file(root/pub['native_path'])==pub['native_sha256']")
s=s.replace('Close valid replica and completed lifecycle checks with conserved full costs','Close paired dense-noise cycle with exact lineage and conserved full costs')
(b/'research/tmp/pvm01_robustness_final_sync_v1.py').write_text(s,encoding='utf-8',newline='\n')
print('Conditional final sync controller prepared; no GitHub call made')
