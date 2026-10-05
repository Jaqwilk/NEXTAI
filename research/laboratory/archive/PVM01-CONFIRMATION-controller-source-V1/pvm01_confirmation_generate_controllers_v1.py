from pathlib import Path
b=Path.cwd()
for part in ('commit_certified','execute','post','publish','integrate','original_check','final_sync'):
    original=b/'research/tmp'/f'pvm01_robustness_{part}_v1.py'; target=b/'research/tmp'/f'pvm01_confirmation_{part}_v1.py'
    assert not target.exists()
    text=original.read_text(encoding='utf-8')
    for old,new in (('pvm01_robustness_','pvm01_confirmation_'),('PVM01-ROBUSTNESS-','PVM01-CONFIRMATION-'),('PVM01-DENSE-NOISE-ROBUSTNESS-','PVM01-DENSE-NOISE-CONFIRMATION-'),('PVM01-CYCLE-314-','PVM01-CYCLE-315-'),('paired_view_mutable_memory_v8','paired_view_mutable_memory_v9'),('EXP-20261005-0003','EXP-20261005-0004'),('analyze_pvm01_dense_noise.py','analyze_pvm01_confirmation.py'),('run_pvm01_dense_noise_check.py','run_pvm01_confirmation_check.py'),('PVM01-dense-noise-analysis','PVM01-confirmation-analysis'),('41c82e2ea25b6d9c96ddee4520975304c4258da3','ecbbb2b3cfebb331944350766e49b3f5f62d23f0'),('e2342788c37e9bcb7d80db9331e9c2e825c695cf','460db82529e7030791b740a79bedac124bf7abf5')):
        text=text.replace(old,new)
    text=text.replace('.read_text()',".read_text(encoding='utf-8')")
    if part=='post': text=text.replace('validation-source-V3','validation-source-V1')
    if part=='integrate':
        text=text.replace("value['continuation_registration_attempts_used']==8","value['continuation_registration_attempts_used']==9")
        text=text.replace("'pvm01_confirmation_history_postrun_v1.py'","'pvm01_confirmation_history_v1.py'")
        text=text.replace('restore_pvm01_dense_noise_result.py','restore_pvm01_confirmation_result.py')
    if part=='publish':
        text=text.replace('restore_pvm01_dense_noise_result.py','restore_pvm01_confirmation_result.py')
        text=text.replace('pvm01_dense_noise_result','pvm01_confirmation_result')
        text=text.replace('dense-noise','independent-confirmation')
    if part=='original_check':
        # All four complete native records remain hash-verified before doctor.
        text=text.replace("('restore-dense-noise',['python','scripts/restore_pvm01_dense_noise_result.py'],o),", "('restore-dense-noise',['python','scripts/restore_pvm01_dense_noise_result.py'],o),\n ('restore-confirmation',['python','scripts/restore_pvm01_confirmation_result.py'],o),")
        text=text.replace('pvm01_confirmation_history_postrun_v1.py','pvm01_confirmation_history_v1.py').replace("'--original'],b)","'--original','--postrun'],b)")
        text=text.replace('all_three_native_hashes_verified','all_four_native_hashes_verified')
    if part=='final_sync':
        text=text.replace("('EXP-20261005-0001','EXP-20261005-0002','EXP-20261005-0004')","('EXP-20261005-0001','EXP-20261005-0002','EXP-20261005-0003','EXP-20261005-0004')")
        text=text.replace("'closed_cycle':314","'closed_cycle':315")
    target.write_text(text,encoding='utf-8',newline='\n')
print('Generated separate confirmation-only controllers; old scripts/receipts unchanged',flush=True)
