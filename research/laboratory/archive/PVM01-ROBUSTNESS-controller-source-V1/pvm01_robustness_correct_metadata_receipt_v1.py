from pathlib import Path
for name in ['pvm01_robustness_commit_validated_v2.py','pvm01_robustness_prepaid_v1.py']:
 p=Path('research/tmp')/name;s=p.read_text().replace('PVM01-ROBUSTNESS-checkout-metadata-tests-V1','PVM01-ROBUSTNESS-checkout-metadata-tests-V2');p.write_text(s,encoding='utf-8',newline='\n')
