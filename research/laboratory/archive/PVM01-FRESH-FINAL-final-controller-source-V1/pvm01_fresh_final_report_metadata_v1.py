from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import sha256_file,atomic_write_json,utc_now
b=Path.cwd();eid='EXP-20261005-0006'
subprocess.run(['uv','run','--no-sync','python','research/tmp/pvm01_fresh_final_report_v1.py'],check=True)
a=json.loads((b/f'research/reviews/{eid}-PVM01-fresh-final-analysis.json').read_text(encoding='utf-8')); confirmation=a['independent_confirmation']
d=json.loads((b/f'research/reviews/{eid}-confirmation-diagnosis-V1.json').read_text(encoding='utf-8'))
header=(f'# Completed cycle317 - frozen fresh final {eid}\n\n'
        f'Five NEW paired units,17 fixed arms; valid={a["valid_comparison"]}.\n'
        f'Main UN-AUGMENTED reference confirmed={confirmation["reference_independently_confirmed"]}; selected classical route confirmed={confirmation["selected_route_independently_confirmed"]}.\n'
        f'Decision: {confirmation["decision"]}. No promotion,transfer or augmentation-benefit claim from adequacy.\n'
        f'Ancillary mixed-reference NI remains separately reported with unchanged gates.\n'
        f'All112 scientific source bytes,recipes,data law,metrics,grids and thresholds unchanged.\n'
        f'Trusted cumulative CUDA allocator peaks,RSS,full fit/service and descriptive reuse costs reported.\n'
        f'Analysis:research/analyses/{eid}.md; full frozen machine analysis/diagnosis preserved.\n'
        f'Current v11 maintenance,scoring=false; A active,B authorized/unspent/inactive.\n'
        f'Next prospective question: {d["exact_next_discriminating_experiment_proposal"]}\n'
        f'No second EXP this cycle; no retry,WT8-9,external models/APIs or schedule change.\n'
        f'Local same-law final completed;expanded transfer/prototype goal remains open. Previous sections preserved history.\n\n')
for rel in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'):
    p=b/rel; p.write_bytes(header.encode('utf-8')+p.read_bytes())
freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
print('Report/terminal maintenance documentation frozen',flush=True)
