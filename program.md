# Codex-native autoresearch program

This file is the operational contract for one autonomous research cycle. `AGENTS.md` contains the non-negotiable rules; this file contains the procedure.

The active Codex heartbeat schedules one discrete wakeup every two hours in this same task. It does not keep a process computing between wakeups and cannot guarantee uninterrupted 24/7 execution; durable repository state is the recovery mechanism.

## 1. Start gate

1. Read the required files listed in `AGENTS.md`.
2. Run `uv run nextai doctor`.
3. Stop the autonomous cycle without modifying research state if `STOP`, `PAUSE`, an active non-stale lock, schema failure, or evaluation-integrity failure is present. Explicit user-authorized maintenance may repair the failed gate, but may not score an experiment and must append a maintenance event.
4. Inspect `git status`. Preserve unrelated user changes. Do not use reset/checkout to erase work.
5. Identify whether a plan is already pending. Run it or append an explicit invalidation with `nextai plan invalidate`; never delete or edit it. The CLI permits only one pending plan.

## 2. Observe

Summarize only evidence already in the ledger:

- current Pareto frontier;
- strongest and weakest scaling signatures;
- failed replications and crashes;
- portfolio imbalance;
- unresolved confounds;
- hypotheses awaiting the cheapest decisive test.

Do not treat an interpretation from an earlier run as a fact.

## 3. Select one question

Choose the experiment with the highest expected information gain per bounded cost. Priority order:

1. verify a surprising positive;
2. falsify the current leading explanation;
3. resolve an ambiguity that blocks several hypotheses;
4. test a genuinely different architecture family;
5. improve a promising implementation only when the principle has earned exploitation.

Avoid superficial hyperparameter search unless needed as a control.

## 4. Preregister before implementation

Create the immutable plan with `uv run nextai plan new`. The plan must state:

- hypothesis and causal research question;
- candidate and matched baselines;
- budget tier, scoring-seed policy/count, K values and D values;
- primary metrics and their explicit directions;
- predicted result;
- explicit kill/promotion evidence;
- plausible alternative explanations and confounds;
- what will be concluded for positive, null, and negative outcomes.

Before registration, freeze the evaluator/contract and obtain its evaluator digest. After the plan is registered, do not edit it. If it is wrong, invalidate it append-only and create a new plan with a parent ID. Implement the tested candidate only after registration, keep all new candidate support code under `candidates/`, and re-freeze the full bundle; this is accepted only while the evaluator digest remains unchanged. Fixed development seeds live in configuration; runner-random scoring seeds are realized only after integrity checks and the transitive candidate audit.

## 5. Implement minimally

- Implement the smallest candidate able to test the registered principle.
- Keep benchmark/oracle/evaluator files untouched.
- Add focused tests for candidate semantics and instrumentation.
- Run `uv run pytest` before the scored experiment.
- If the source audit rejects the candidate, fix the design; never bypass the audit.

## 6. Execute within budget

Run only through:

```powershell
uv run nextai run --plan research/plans/EXP-....json
```

The runner enforces lifecycle and cadence gates, verifies the harness and plan hash, transitively audits all candidate dependencies, then realizes blinded scoring seeds and starts each candidate in a sanitized subprocess. It monitors time and memory and appends the result. A timeout, memory breach, audit failure, or integrity change is a recorded outcome.

Begin with `quick`. Use `screen` only after the cheap test survives. Use `deep` only for replicated, non-dominated principles or a deliberately registered scaling test.

## 7. Analyze without rewriting history

Create `research/analyses/<experiment_id>.md` containing exactly these top-level sections:

```text
OBSERVATION
INTERPRETATION
CONFIDENCE
ALTERNATIVE EXPLANATIONS
DECISION
NEXT DISCRIMINATING EXPERIMENT
```

Quantify uncertainty. A slope from fewer than three distinct scale points is labeled screening-only. Compare slopes and the implementable Pareto position, not only averages; report oracle controls separately as lower bounds. Distinguish a candidate implementation failure from evidence against the general principle.

Append a hypothesis update with `nextai hypothesis update`; do not delete the old event. Machine-enforced `promising`/`promoted` transitions require replicated screen/deep evidence, seed stability, integrity, checked primary prior art and an implementable non-dominated candidate. Then run `nextai report`.

## 8. Reflection cadence

After the configured number of completed experiments, use the entire cycle for a review instead of a mutation. Write `research/reviews/GEN-<n>-REVIEW-<date>.md` answering:

1. What was objectively learned?
2. Which assumptions were falsified?
3. Which results replicated?
4. Is the portfolio trapped in one family?
5. Are we optimizing implementation details rather than principles?
6. What result would most change current beliefs?
7. Which prior work already contains the apparent novelty?
8. Which next test has the highest expected information gain?

## 9. End gate

Run `uv run nextai doctor` and `uv run pytest`. Report the experiment ID, decision, budget/integrity status and one next experiment. End the scheduled run after this single bounded cycle. The next Codex wakeup continues from durable repository state.
