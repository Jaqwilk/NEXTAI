# Append-only clarification after EXP-20260905-0001 registration

The activation validator passed BEFORE registration. A repeated invocation
after registration failed because the inherited service snapshot lists
research/plan_registry.jsonl both as a whole-file immutable entry and as an
append-only prefix. Whole-file equality is appropriate only before a new plan.
This auxiliary script is therefore a pre-registration check, not a valid
post-registration history check. Its failure is retained; the protected script,
certificate, EXP plan and evaluator have NOT been edited or re-frozen to hide it.

Independent byte-level verification found 348/349 whole files identical; the
only full-file change is the registry's legitimate 205-byte registration for
EXP-20260905-0001. Its original 26856 bytes retain SHA-256
4f6dac87f113d90d1360e05e18c5433b2734791bcf2cb65a49786756f91260c2.
Every ledger prefix was checked separately, including events. Proof is stored
in PC-01-ACTIVATION-PREFIX-PROOF-V1.json. Normal lifecycle, run authorization,
manifest and certificate checks all pass after registration.

Interpretation: this is an overly restrictive service validator classification,
not a rewritten historical plan or evaluator change. Continue the already
registered one dev attempt under unchanged evaluator and normal audited runner.
A future authorized maintenance revision should distinguish append-only ledgers
from permanently completed artifacts in the auxiliary validator. Do not modify
the currently pending EXP or replenish the one-attempt allowance.
