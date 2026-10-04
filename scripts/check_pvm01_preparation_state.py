"""Read-only source, history and laboratory gates for the technical preparation."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--label", choices=("clone", "original"), required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    evidence_root = Path(__file__).resolve().parents[1]
    before = json.loads((evidence_root / "research/reviews/PVM01-REPRO-startup-history-V1.json").read_text())
    startup = json.loads((evidence_root / "research/reviews/PVM01-REPRO-startup-V1.json").read_text())
    mutable = {".gitattributes", "AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
               "research/REPORT.md", "research/REPORT.provenance.json", "research/state.json", "research/eval_manifest.json",
               "research/laboratory/preflight_certificate.json", "research/events.jsonl", "research/sources.jsonl"}
    preserved = 0
    for relative, expected in before["original_files"].items():
        if relative not in mutable:
            assert sha256_file(root / relative) == expected, relative
            preserved += 1
    for relative, prefix in before["append_only_prefixes"].items():
        raw = (root / relative).read_bytes()[:prefix["bytes"]]
        assert hashlib.sha256(raw).hexdigest() == prefix["sha256"], relative
    previous_source = evidence_root / "research/laboratory/archive/PVM01-REPRO-previous-source-V1"
    for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
        previous = previous_source / relative
        if not previous.is_file():
            previous = evidence_root / "research/laboratory/archive/PVM01-REPRO-history-context-V1" / relative
        assert sha256_file(previous) == before["original_files"][relative], relative
        assert (root / relative).read_bytes().endswith(previous.read_bytes()), relative
    assert (root / ".gitattributes").read_bytes().startswith((previous_source / "root.gitattributes.raw").read_bytes())
    manifest, preflight, programme = verify_manifest(root), verify_preflight_certificate(root), status(root)
    assert manifest["ok"], manifest  # The preflight verifier raises on any mismatch.
    state = json.loads((root / "research/state.json").read_text())
    assert state["completed_experiments"] == 115 and state["active_experiment_id"] is None
    assert state["last_experiment_id"] == "EXP-20261004-0008"
    assert programme["registration_attempts_used"] == 8 and not programme["paid_run_pending"]
    assert programme["experimental_fit_seconds"] == startup["programme_before"]["experimental_fit_seconds"]
    assert programme["stage_registration_attempts"] == startup["programme_before"]["stage_registration_attempts"]
    assert not programme["program_terminal"] and not programme["scoring_authorized"]
    assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(root / "src"), NEXTAI_PROJECT_ROOT=str(root), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    deadline = time.monotonic() + 190.
    commands = []
    for command in (("doctor",), ("lab", "status")):
        stem = evidence_root / "research/reviews" / ("PVM01-REPRO-" + args.label + "-" + "-".join(command) + "-V1")
        result = run_bounded([shutil.which("uv"), "run", "--no-sync", "nextai", *command], cwd=root, env=environment,
                             stdout_path=stem.with_suffix(".stdout.txt"), stderr_path=stem.with_suffix(".stderr.txt"),
                             timeout_seconds=min(160., deadline - time.monotonic() - 5.))
        commands.append({"command": command, "process": asdict(result),
                         "raw_stdout_sha256": sha256_file(stem.with_suffix(".stdout.txt")),
                         "raw_stderr_sha256": sha256_file(stem.with_suffix(".stderr.txt"))})
        atomic_write_json(evidence_root / f"research/reviews/PVM01-REPRO-{args.label}-state-V1.checkpoint.json",
                          {"created_at": utc_now(), "commands": commands, "old_raw_files_preserved": preserved,
                           "all_append_only_prefixes_preserved": True, "previous_doc_content_preserved": True,
                           "manifest": manifest, "preflight": preflight, "programme": programme,
                           "state": state, "source_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip(),
                           "free_disk_bytes": shutil.disk_usage(root).free})
        if result.returncode != 0:
            return result.returncode
    print(f"{args.label}: doctor/lab/source/history PASS; {preserved} prior raw files unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
