from pathlib import Path
import ast
paths=sorted(Path('research/tmp').glob('pvm01_confirmation_*.py'))
for path in paths:
    source=path.read_text(encoding='utf-8');compile(source,str(path),'exec')
    if path.name=='pvm01_confirmation_publish_v1.py':
        values=[node.value for node in ast.walk(ast.parse(source)) if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('"""Restore the exact independent-confirmation')]
        assert len(values)==1;compile(values[0],'prospective_restore_pvm01_confirmation_result.py','exec')
assert len(paths)>=20
print('All administrative controllers and prospective embedded lossless/resource restorer parse:',len(paths),flush=True)
