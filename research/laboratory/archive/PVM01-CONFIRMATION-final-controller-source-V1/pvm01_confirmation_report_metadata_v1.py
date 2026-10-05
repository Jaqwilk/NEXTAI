from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import sha256_file,atomic_write_json,utc_now
b=Path.cwd();eid='EXP-20261005-0004'
subprocess.run(['uv','run','--no-sync','python','research/tmp/pvm01_confirmation_report_v1.py'],check=True)
a=json.loads((b/f'research/reviews/{eid}-PVM01-confirmation-analysis.json').read_text(encoding='utf-8')); confirmation=a['independent_confirmation']
d=json.loads((b/f'research/reviews/{eid}-confirmation-diagnosis-V1.json').read_text(encoding='utf-8'))
header=(f'# Completed cycle315 - independent confirmation {eid}\n\n'
        f'Five NEW paired units,17 fixed arms; valid={a["valid_comparison"]}.\n'
        f'Reference confirmed={confirmation["reference_independently_confirmed"]}; selected classical route confirmed={confirmation["selected_route_independently_confirmed"]}.\n'
        f'Decision: {confirmation["decision"]}. No promotion,transfer or augmentation-benefit claim from adequacy.\n'
        f'All102 scientific source bytes,recipes,data law,metrics,grids and thresholds unchanged.\n'
        f'Trusted cumulative CUDA allocator peaks,RSS,full fit/service and descriptive reuse costs reported.\n'
        f'Analysis:research/analyses/{eid}.md; full frozen machine analysis/diagnosis preserved.\n'
        f'Current v9 maintenance,scoring=false; A active,B authorized/unspent/inactive.\n'
        f'Next prospective question: {d["exact_next_discriminating_experiment_proposal"]}\n'
        f'No second EXP this cycle; no retry,WT8-9,external models/APIs or schedule change.\n'
        f'Expanded final/transfer/prototype goal remains open. Previous sections preserved history.\n\n')
for rel in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'):
    p=b/rel; p.write_bytes(header.encode('utf-8')+p.read_bytes())
# Correct the previous report's overbroad absence-of-VRAM statement append-only.
arc=b/'research/laboratory/archive/EXP-20261005-0003-runtime/research/tmp/EXP-20261005-0003'
paths=sorted(arc.glob('*.device.json'))
values=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
text=('# EXP-20261005-0003 - append-only CUDA telemetry clarification\n\nThe completed analysis said the PVM harness did not measure peak CUDA allocator/reservation bytes. That wording was too broad: the trusted WorkerResources source reset cumulative peaks at worker start and sampled torch.cuda.max_memory_allocated/max_memory_reserved every0.1s. The preserved device journals contain these observations. They were omitted from the previous report and lack a guaranteed synchronized final boundary sample. Treat them as sampled cumulative observations,not exact final peaks,inference-only memory,total driver/context VRAM or energy. No completed plan,result,gate or decision changes.\n\n'
      f'Archived device records={len(paths)}; maximum last-sample allocated={max((x["allocated"] for x in values),default=0)}bytes; reserved={max((x["reserved"] for x in values),default=0)}bytes. Full raw bytes remain in the immutable0003 runtime archive.\n\n'
      'New prospectively frozen v9 adds synchronized phase/final allocator snapshots and distinct RSS reporting. Its measured timings,models and scientific gates remain unchanged; instrumentation overhead is charged.\n')
p=b/'research/analyses/EXP-20261005-0003-CUDA-TELEMETRY-ADDENDUM-V1.md'; assert not p.exists(); p.write_text(text,encoding='utf-8',newline='\n')
atomic_write_json(b/'research/reviews/PVM01-CONFIRMATION-prior-CUDA-clarification-V1.json',{'created_at':utc_now(),'completed_prior_result_unchanged':True,'completed_prior_analysis_unchanged':True,'completed_gates_decisions_unchanged':True,'addendum_path':p.relative_to(b).as_posix(),'addendum_sha256':sha256_file(p),'preserved_device_records':{x.relative_to(b).as_posix():sha256_file(x) for x in paths}})
freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
print('Report/append-only clarification/terminal maintenance documentation frozen',flush=True)
