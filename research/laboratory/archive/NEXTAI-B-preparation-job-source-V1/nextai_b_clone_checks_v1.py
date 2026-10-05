import subprocess
for command in (["uv","run","--no-sync","python","scripts/check_transfer_preparation.py","--snapshot","--seal"],["uv","run","--no-sync","nextai","doctor"],["uv","run","--no-sync","nextai","lab","status"]):
    subprocess.run(command,check=True)
