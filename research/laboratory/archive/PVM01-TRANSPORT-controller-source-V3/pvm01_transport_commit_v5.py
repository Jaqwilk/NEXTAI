from pathlib import Path
import hashlib,json,subprocess
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();snapshot=json.loads((b/"research/checks/PVM01-TRANSPORT-history-snapshot-V1.json").read_text());manifest=json.loads((b/"research/eval_manifest.json").read_text())
paths=subprocess.check_output(["git","status","--porcelain","-z","--untracked-files=all"],cwd=b).decode("utf-8").split("\0")
selected=[]
prefixes=("research/reviews/PVM01-TRANSPORT","research/checks/PVM01-TRANSPORT","research/laboratory/archive/PVM01-TRANSPORT","research/manifests/","research/laboratory/certificates/","src/nextai_autoresearch/candidates/pvm01_tc_")
allowed={"config/research.toml","config/baseline_semantics.json","research/REPORT.md","research/REPORT.provenance.json","research/eval_manifest.json","research/events.jsonl","research/laboratory/preflight_certificate.json","schemas/experiment_plan.schema.json","src/nextai_autoresearch/integrity.py","src/nextai_autoresearch/research_program.py","src/nextai_autoresearch/runner.py","src/nextai_autoresearch/candidates/pvm01_transport_compression_core.py","src/nextai_autoresearch/pvm01_adverse_task.py","src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v6.py","tests/test_pvm01_transport_compression.py","scripts/analyze_pvm01_transport.py","scripts/run_pvm01_transport_check.py",".gitattributes","AGENTS.md","program.md","research/LAB_PLAN.md","docs/CURRENT_STATUS.md"}
for entry in paths:
 if not entry:continue
 name=entry[3:];assert name in allowed or name.startswith(prefixes),(entry,"Unrelated change preserved; stop staging")
 selected.append(name)
for start in range(0,len(selected),150):subprocess.run(["git","add","--",*selected[start:start+150]],cwd=b,check=True)
tree=subprocess.check_output(["git","ls-tree","-rz","--full-tree","905ed709ad18d3fdc2dac863deb121cefbf1b874"],cwd=b)
historical_blobs={}
for line in tree.split(b"\0"):
 if line:
  meta,name=line.split(b"\t",1);historical_blobs[name.decode("utf-8")]=meta.split()[2].decode("ascii")
names=list(manifest["files"]);output=subprocess.check_output(["git","cat-file","--batch"],input="".join(":"+n+"\n" for n in names).encode("utf-8"),cwd=b)
cursor=0;native=[]
for name in names:
 end=output.index(b"\n",cursor);oid,kind,length=output[cursor:end].decode("ascii").split();assert kind=="blob"
 cursor=end+1;length=int(length);raw=output[cursor:cursor+length];cursor+=length;assert output[cursor:cursor+1]==b"\n";cursor+=1
 digest=manifest["files"][name]
 if hashlib.sha256(raw).hexdigest()!=digest:
  assert name in snapshot["raw_files"] and snapshot["raw_files"][name]==digest
  assert oid==historical_blobs[name] and sha256_file(b/name)==digest
  assert raw.replace(b"\r\n",b"\n")== (b/name).read_bytes().replace(b"\r\n",b"\n"),name
  native.append(name)
assert cursor==len(output)
from nextai_autoresearch.utils import atomic_write_json,utc_now
receipt=b/"research/reviews/PVM01-TRANSPORT-protected-index-bytes-V3.json"
atomic_write_json(receipt,{"created_at":utc_now(),"protected_files":len(names),"raw_index_exact":len(names)-len(native),"historical_native_newline_only":native,"all_new_or_changed_protected_raw_bytes_exact":True,"historical_working_raw_and_Git_blobs_unchanged":True,"native_bytes_in_full_source_V4_archive":True})
subprocess.run(["git","add","--",receipt.relative_to(b).as_posix()],cwd=b,check=True)
immutable=["research/BELIEFS.json","research/checks/AUDIT-REPAIR-harness-first.junit.xml","research/checks/dronepropa_protocol_gate_cycle75.json","research/checks/dronepropa_routing_sensitivity_cycle76.json","research/checks/heldout_wt_changepoints_prequential_v1_development_smoke.json","research/checks/ncmapss_ds02_semantic_gate_v2_result.json","research/checks/ncmapss_ds08a_semantic_gate_v1_result.json","research/checks/real_system_calibration_cycle_228.json","research/data/suitesparse_real_pde_v1/audit_attempt_001.json","research/reviews/EXTERNAL-AUDIT-2026-09-03.md"]
for name in immutable:
 assert sha256_file(b/name)==snapshot["raw_files"][name]
 assert subprocess.check_output(["git","rev-parse",":"+name],cwd=b)==subprocess.check_output(["git","rev-parse","905ed709ad18d3fdc2dac863deb121cefbf1b874:"+name],cwd=b)
subprocess.run(["git","-c","core.whitespace=-blank-at-eof","diff","--cached","--check","--","config","src","schemas","tests","scripts","docs/CURRENT_STATUS.md"],cwd=b,check=True)
subprocess.run(["git","commit","-q","-m","Validate preregistered transport compression and adverse comparison before private execution"],cwd=b,check=True)
assert not subprocess.check_output(["git","status","--porcelain"],cwd=b).strip()
print("Source/evidence committed; changed protected raw hashes exact, old native/Git bytes preserved",subprocess.check_output(["git","rev-parse","HEAD"],cwd=b).decode().strip())
