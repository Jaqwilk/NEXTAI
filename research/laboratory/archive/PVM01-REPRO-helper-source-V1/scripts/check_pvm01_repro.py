"""One finite fixed-fixture matrix under a whole-tree auxiliary deadline."""
from dataclasses import asdict
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import sys
import time

from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "research/plans/PVM01-REPRO-PREPARATION-V1.json"
PLAN_SHA = "54bb174dc4cc6f01b5e4229f0da377c096d526a26f5925258d950f1748ac59ea"


def analyze(runs, frozen):
    profiles = {}
    for profile in frozen["profiles"]:
        by_seed = []
        for seed in frozen["model_seeds"]:
            selected = [r for r in runs if r["profile"] == profile and r["seed"] == seed and r.get("data")]
            records = [r["data"] for r in selected]
            fields = ("fixture_sha256", "initial_encoder_sha256", "initial_decoder_sha256",
                      "final_encoder_sha256", "final_decoder_sha256")
            equal = {field: len({r[field] for r in records}) == 1 and len(records) == 6 for field in fields}
            for field in ("alignment_losses", "dense_set_losses"):
                equal[field] = len({json.dumps(r["fit_report"][field]) for r in records}) == 1 and len(records) == 6
            observations = [r["observations"] for r in records]
            valid_answers = len(records) == 6 and all(len(x) == 20 for x in observations)
            predictions_same = valid_answers and all(
                all((a["handle"], a["value"], a["answer"]) == (b["handle"], b["value"], b["answer"])
                    for a, b in zip(observations[0], obs, strict=True)) for obs in observations[1:])
            max_score_delta = max((abs(a["score"] - b["score"]) for obs in observations[1:]
                                   for a, b in zip(observations[0], obs, strict=True)), default=0.) if valid_answers else None
            losses_valid = len(records) == 6 and all(
                len(r["fit_report"][field]) == 64 and all(math.isfinite(x) for x in r["fit_report"][field])
                for r in records for field in ("alignment_losses", "dense_set_losses"))
            changed = len(records) == 6 and all(r["initial_encoder_sha256"] != r["final_encoder_sha256"] and
                      r["initial_decoder_sha256"] != r["final_decoder_sha256"] for r in records)
            math_only = len(records) == 6 and all(
                any("_scaled_dot_product_attention_math" in key for key in r["dispatch_operators"]) and
                not any("efficient" in key or "flash" in key or "cudnn" in key for key in r["dispatch_operators"])
                for r in records)
            accepted = all(equal.values()) and losses_valid and changed and math_only and predictions_same and max_score_delta <= 1e-5
            by_seed.append({"seed": seed, "children": len(records), "exact_identity": equal,
                            "finite_losses_and_step_counts": losses_valid, "encoder_decoder_changed": changed,
                            "actual_math_only_fit_dispatch": math_only, "same_discrete_predictions": predictions_same,
                            "max_inference_score_delta": max_score_delta, "acceptance_passed": accepted})
        profiles[profile] = by_seed
    all_complete = len(runs) == frozen["maximum_children"] and all(r["process"]["returncode"] == 0 and r.get("data") for r in runs)
    passed = all_complete and all(r["acceptance_passed"] for r in profiles["deterministic_math"])
    return {"all_36_children_complete": bool(all_complete), "profiles": profiles,
            "decision": "KEEP technical policy" if passed else "INCONCLUSIVE technical policy",
            "technical_acceptance_passed": passed, "historical_EXP_0008_reinterpreted": False}


def main():
    assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == PLAN_SHA
    frozen = json.loads(PLAN.read_text())["cuda_fixture"]
    directory = ROOT / "research/reviews/PVM01-REPRO-fixture-V1"
    directory.mkdir(exist_ok=False)
    started = time.monotonic()
    runs = []
    for profile, seed, repeat, arm in itertools.product(frozen["profiles"], frozen["model_seeds"], range(2), frozen["arms"]):
        stem = f"{profile}-{seed}-{repeat}-{arm}"
        remaining = min(frozen["child_wall_seconds_cap"], 940 - (time.monotonic() - started))
        if remaining <= 0:
            break
        output = directory / f"{stem}.json"
        result = run_bounded([sys.executable, str(ROOT / "scripts/pvm01_repro_fixture.py"), "--seed", str(seed),
                              "--repeat", str(repeat), "--arm", arm, "--profile", profile, "--output", str(output)],
                             cwd=ROOT, env=os.environ.copy(), stdout_path=directory / f"{stem}.stdout.txt",
                             stderr_path=directory / f"{stem}.stderr.txt", timeout_seconds=remaining)
        record = {"profile": profile, "seed": seed, "repeat": repeat, "arm": arm, "process": asdict(result),
                  "data": json.loads(output.read_text()) if output.exists() and result.returncode == 0 else None,
                  "output_hashes": {p.name: sha256_file(p) for p in directory.glob(stem + ".*")}}
        runs.append(record)
        atomic_write_json(directory / "checkpoint.json", {"runs": runs, "elapsed_seconds": time.monotonic() - started})
        print(f"{len(runs)}/36 {stem}: {result.reason}, code={result.returncode}, wall={result.elapsed_seconds:.3f}", flush=True)
        if result.returncode != 0:
            break
    analysis = analyze(runs, frozen)
    analysis.update(created_at=utc_now(), plan_raw_sha256=PLAN_SHA, elapsed_seconds=time.monotonic() - started,
                    runs=runs, source_hashes={p.relative_to(ROOT).as_posix(): sha256_file(p) for p in
                    (PLAN, ROOT / "scripts/pvm01_repro_fixture.py", Path(__file__), ROOT / "src/nextai_autoresearch/candidates/pvm01_repro_core.py")})
    atomic_write_json(ROOT / "research/reviews/PVM01-REPRO-fixture-analysis-V1.json", analysis)
    print(json.dumps({key: analysis[key] for key in ("decision", "technical_acceptance_passed", "all_36_children_complete", "elapsed_seconds")}), flush=True)
    return 0 if analysis["technical_acceptance_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
