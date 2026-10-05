from pathlib import Path
b = Path.cwd()
for part in ('child', 'controller'):
    old = b / 'research/tmp' / f'pvm01_robustness_startup_{part}_v1.py'
    new = b / 'research/tmp' / f'pvm01_confirmation_startup_{part}_v1.py'
    assert not new.exists()
    text = old.read_text(encoding='utf-8').replace('PVM01-ROBUSTNESS-', 'PVM01-CONFIRMATION-').replace('pvm01_robustness_', 'pvm01_confirmation_').replace('41c82e2ea25b6d9c96ddee4520975304c4258da3', 'ecbbb2b3cfebb331944350766e49b3f5f62d23f0').replace("'proposed_cycle':314", "'proposed_cycle':315").replace('dense-reference robustness', 'independent fixed-recipe confirmation').replace('anticipated robustness auxiliary cost', 'anticipated confirmation auxiliary cost')
    new.write_text(text, encoding='utf-8', newline='\n')
