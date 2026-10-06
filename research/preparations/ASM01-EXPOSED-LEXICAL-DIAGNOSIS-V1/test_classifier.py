import ast
import importlib.util
from pathlib import Path
import pytest
import nextai_autoresearch
from nextai_autoresearch.utils import load_json,sha256_file
ROOT=Path(__file__).resolve().parents[3];SOURCE=Path(__file__).with_name('classifier.py')
spec=importlib.util.spec_from_file_location('opaque_classifier',SOURCE);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def payload(rows):return ('CHARACTER_NAME: synthetic\nSTROKE_COUNT: 2\nX Y STYLUS_STATE STROKE\nPEN_DOWN\n'+'\n'.join(rows)+'\nPEN_UP 0\nEND_CHARACTER: synthetic\n').encode('ascii')
@pytest.mark.parametrize('case',['categories','metadata','malformed','provenance'],ids=['categories','metadata','malformed','provenance'])
def test_classifier(case):
 if case=='categories':
  expected={'0':'unsigned','000':'unsigned','-0':'exact_minus_zero','-00':'other_minus_zero','-000':'other_minus_zero','-1':'minus_nonzero','-001':'minus_nonzero','+0':'other','0.1':'other','-':'other'}
  assert {s:mod.coordinate_kind(s) for s in expected}==expected
  out=mod.classify_release(payload(['0 -0 01 001','1 -00 1 1','2 -001 1 2','3 7 1 2']))
  assert out['point_rows']==4 and out['coordinates']['X']['unsigned']==4
  assert out['coordinates']['Y']=={'unsigned':1,'exact_minus_zero':1,'other_minus_zero':1,'minus_nonzero':1,'other':0}
 elif case=='metadata':
  out=mod.classify_release(payload(['0 0 0 1','1 1 1 3','2 2 1 1','3 3 1 0']))
  assert out['invalid_state']==1 and out['invalid_serial']==2 and out['serial_decrease']==1
 elif case=='malformed':
  for p in (bytearray(),b'x'*262145,b'\xff'):
   with pytest.raises(ValueError):mod.classify_release(p)
  out=mod.classify_release(payload(['UNKNOWN','PEN_UP 1']).replace(b'STROKE_COUNT: 2',b'STROKE_COUNT: 0').replace(b'X Y STYLUS_STATE STROKE',b'BAD HEADER'))
  assert out['invalid_count']==out['invalid_column_header']==out['invalid_marker']==out['unknown_rows']==1
 else:
  assert ROOT.name=='NEXTAI-VALIDATION-20261002' and Path(nextai_autoresearch.__file__).resolve().is_relative_to(ROOT/'src')
  binding=load_json(ROOT/'research/reviews/ASM01-LEXICAL-DIAG-SOURCE-BINDING-V1.json')
  for name,digest in binding['files'].items():assert sha256_file(ROOT/name)==digest
  tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
  for node in ast.walk(tree):
   if isinstance(node,ast.Import):assert all(a.name=='re' for a in node.names)
   if isinstance(node,ast.Name):assert node.id not in {'int','float','Decimal','open','Path','np','numpy','torch','exec','eval'}
