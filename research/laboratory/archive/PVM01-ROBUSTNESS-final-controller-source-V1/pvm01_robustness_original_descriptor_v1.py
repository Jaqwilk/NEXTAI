from pathlib import Path
p=Path('research/tmp/pvm01_robustness_original_check_v1.py');s=p.read_text().replace("'both_native_hashes_verified':True", "'all_three_native_hashes_verified':True");p.write_text(s,encoding='utf-8',newline='\n')
