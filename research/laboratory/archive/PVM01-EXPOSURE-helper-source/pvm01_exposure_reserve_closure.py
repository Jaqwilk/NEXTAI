"""Retire a conservative allowance only after all closure checks complete."""
from pathlib import Path

from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import auxiliary_reserve

b = Path.cwd()
events = read_jsonl(b/"research/events.jsonl")
paid = {e["charge_id"]:e["seconds"] for e in events
        if e.get("event") == "research_program_aux_fit_charged"}
used = sum(paid.get(e["charge_id"],e["seconds_cap"]) for e in events
           if e.get("event") == "research_program_aux_fit_reserved"
           and e.get("charge_id", "").startswith("PVM01-EXPOSURE-"))
identity = "PVM01-EXPOSURE-final-accounting-allowance-V1"
assert not any(e.get("charge_id") == identity for e in events)
assert used + 120 <= 1800
auxiliary_reserve(b, identity, 120)
write_report(b)
print("Reserved final closure/accounting allowance120s; stage used or reserved",used+120)
