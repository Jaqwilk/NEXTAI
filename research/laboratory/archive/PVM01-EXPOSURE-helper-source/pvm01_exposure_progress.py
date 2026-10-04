"""Read durable worker completion/phase counts only; never execute a model."""
import json
from pathlib import Path

b = Path.cwd()
identity = "EXP-20261004-0008"
directory = b/f"research/tmp/{identity}"
study = json.loads((b/"research/plans/PVM01-CAPACITY-EXPOSURE-V1.json").read_text())
complete, failed, phases = [], [], []
for name in study["candidates"]:
    path = directory/f"{name}.json"
    if path.exists():
        value = json.loads(path.read_text())
        (complete if value["status"] == "complete" else failed).append({"candidate":name,"trials":len(value.get("trials",[])),"status":value["status"]})
    phase = directory/f"{name}.phase.json"
    if phase.exists() and not path.exists():
        phases.append({"candidate":name,"phase":json.loads(phase.read_text())["phase"]})
print(json.dumps({"experiment":identity,"workers_complete":len(complete),"total_workers":len(study["candidates"]),
    "trials_complete":sum(v["trials"] for v in complete),"failed":failed,"current_phases":phases,
    "result_present":(b/f"research/results/{identity}.json").exists()}))
