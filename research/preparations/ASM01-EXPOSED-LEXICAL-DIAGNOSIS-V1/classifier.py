"""Opaque-coordinate lexical counts only; no normalization or numeric parsing."""
import re

KINDS=('unsigned','exact_minus_zero','other_minus_zero','minus_nonzero','other')

def coordinate_kind(token):
 if re.fullmatch(r'[0-9]+',token):return 'unsigned'
 if token=='-0':return 'exact_minus_zero'
 if re.fullmatch(r'-[0-9]+',token):
  return 'other_minus_zero' if set(token[1:])=={'0'} else 'minus_nonzero'
 return 'other'

def classify_release(payload):
 if not isinstance(payload,bytes) or len(payload)>262144:raise ValueError('bytes_cap_type')
 try:lines=[s.strip() for s in payload.decode('ascii').splitlines() if s.strip()]
 except UnicodeDecodeError:raise ValueError('ascii') from None
 out={'point_rows':0,'coordinates':{axis:{kind:0 for kind in KINDS} for axis in ('X','Y')},'invalid_envelope':0,'invalid_count':0,'invalid_column_header':0,'invalid_marker':0,'unknown_rows':0,'invalid_state':0,'invalid_serial':0,'serial_decrease':0}
 if len(lines)<4 or not lines[0].startswith('CHARACTER_NAME:') or not lines[-1].startswith('END_CHARACTER:'):out['invalid_envelope']=1
 match=re.fullmatch(r'STROKE_COUNT:\s*([1-9][0-9]*)',lines[1]) if len(lines)>1 else None
 count=match.group(1) if match else '0';out['invalid_count']=0 if match else 1
 if [i for i,s in enumerate(lines) if s.split()==['X','Y','STYLUS_STATE','STROKE']]!=[2]:out['invalid_column_header']=1
 previous='0'
 for line in lines[3:-1]:
  fields=line.split()
  if fields in (['PEN_DOWN'],['PEN_UP','0']):continue
  if fields and fields[0] in ('PEN_DOWN','PEN_UP'):out['invalid_marker']+=1;continue
  if len(fields)!=4:out['unknown_rows']+=1;continue
  out['point_rows']+=1
  for axis,token in zip(('X','Y'),fields[:2]):out['coordinates'][axis][coordinate_kind(token)]+=1
  state,serial=fields[2:];serial=serial.lstrip('0') or '0'
  if not re.fullmatch(r'[0-9]+',state) or (state.lstrip('0') or '0')!='1':out['invalid_state']+=1
  if not re.fullmatch(r'[0-9]+',serial) or serial=='0' or (len(serial),serial)>(len(count),count):out['invalid_serial']+=1
  elif (len(serial),serial)<(len(previous),previous):out['serial_decrease']+=1
  previous=serial
 return out
