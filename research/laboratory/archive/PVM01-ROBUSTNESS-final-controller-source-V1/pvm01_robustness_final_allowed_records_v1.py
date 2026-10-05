from pathlib import Path
p=Path('research/tmp/pvm01_robustness_final_sync_v1.py');s=p.read_text(encoding='utf-8')
s=s.replace("allowed=('research/REPORT'", "allowed=('research/reviews/PVM01-ROBUSTNESS-integrate-original-','research/reviews/PVM01-ROBUSTNESS-history-original-postrun-','research/REPORT'")
p.write_text(s,encoding='utf-8',newline='\n')
