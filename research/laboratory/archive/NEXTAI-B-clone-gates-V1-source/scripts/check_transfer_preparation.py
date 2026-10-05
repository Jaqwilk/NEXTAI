"""Verify the no-scoring B transition against the pristine pre-cycle checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate, write_preflight_certificate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now


PARENT = "a3d2e86e20dcdd30411e9cc435cce00be93942d7"
SNAPSHOT = "research/checks/NEXTAI-B-history-snapshot-V1.json"
HEADERS = {"AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"}
MUTABLE = {".gitattributes", "config/research.toml", "src/nextai_autoresearch/research_program.py",
    "src/nextai_autoresearch/integrity.py", "schemas/source.schema.json", "research/eval_manifest.json",
    "research/laboratory/preflight_certificate.json", "research/REPORT.md", "research/REPORT.provenance.json",
    "research/state.json", *HEADERS}


def git(root, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=root)


def make_snapshot(root):
    original = root.parent / "NEXTAI"
    assert git(original, "rev-parse", "HEAD").decode().strip() == PARENT
    assert not git(original, "status", "--porcelain")
    paths = git(original, "ls-files", "-z").decode("utf-8").split("\0")
    prefixes = load_json(root / "research/checks/PVM01-FRESH-FINAL-history-snapshot-V1.json")["prefixes"]
    records = {}
    for relative in paths:
        if not relative:
            continue
        path = original / relative
        assert path.is_file(), relative
        records[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    snapshot = {"created_at": utc_now(), "parent_commit": PARENT, "source": str(original),
        "raw_files": records, "prefixes": {path: records[path] for path in prefixes}}
    assert not (root / SNAPSHOT).exists()
    atomic_write_json(root / SNAPSHOT, snapshot)
    print(json.dumps({"snapshot_files": len(records), "parent": PARENT}), flush=True)


def check(root, *, original=False, seal=False):
    target = root.parent / "NEXTAI" if original else root
    if seal:
        assert not original
        freeze_manifest(target, overwrite=True)
        write_preflight_certificate(target)
        from nextai_autoresearch.report import write_report
        write_report(target)
    snapshot = load_json(root / SNAPSHOT)
    eol = {row["path"]: row for row in load_json(root / "research/laboratory/PVM01-TRANSPORT-original-checkout-EOL-V1.json")["differences"]}
    prefixes = set(snapshot["prefixes"])
    checked = 0
    for relative, record in snapshot["raw_files"].items():
        if relative in MUTABLE or relative in prefixes:
            continue
        expected = record["sha256"]
        if not original and relative in eol:
            assert expected == eol[relative]["original_raw_sha256"]
            expected = eol[relative]["clone_raw_sha256"]
            assert git(target, "rev-parse", "HEAD:" + relative).decode().strip() == eol[relative]["unchanged_git_blob"]
        assert sha256_file(target / relative) == expected, relative
        checked += 1
    for relative, record in snapshot["prefixes"].items():
        raw = (target / relative).read_bytes()
        assert len(raw) >= record["bytes"] and hashlib.sha256(raw[:record["bytes"]]).hexdigest() == record["sha256"], relative
        if relative.endswith(".jsonl"):
            read_jsonl(target / relative)
    parent = root / "research/laboratory/archive/NEXTAI-B-parent-harness-V1"
    for relative in HEADERS:
        assert (target / relative).read_bytes().endswith((parent / relative).read_bytes()), relative
    assert (target / ".gitattributes").read_bytes().startswith((parent / ".gitattributes.raw").read_bytes())
    schema_archive = root / "research/laboratory/archive/NEXTAI-B-source-schema-before-repair-V1/source.schema.json"
    assert sha256_file(schema_archive) == snapshot["raw_files"]["schemas/source.schema.json"]["sha256"]
    science = load_json(target / "research/plans/PVM01-FRESH-FINAL-V1.json")["parent_evidence"]["scientific_source_sha256_unchanged"]
    for relative, digest in science.items():
        assert sha256_file(target / relative) == digest, relative
    publication = load_json(target / "research/laboratory/EXP-20261005-0006-fitted-state-publication-V1.json")
    assert publication["before_final_data"] and publication["no_source_refit"]
    assert publication["no_training_final_arrays_labels_nonce_optimizer_episode_memory"]
    assert len(publication["exports"]) == 25 and len(publication["files"]) == 50
    assert sha256_file(target / publication["bundle_path"]) == publication["bundle_sha256"]
    actual_states = target / "research/laboratory/archive/EXP-20261005-0006-runtime/research/tmp/EXP-20261005-0006/fitted-source"
    with zipfile.ZipFile(target / publication["bundle_path"]) as bundle:
        assert set(bundle.namelist()) == set(publication["files"])
        for relative, record in publication["files"].items():
            raw = bundle.read(relative)
            assert len(raw) == record["bytes"] and hashlib.sha256(raw).hexdigest() == record["sha256"]
            assert sha256_file(actual_states / relative) == record["sha256"]
    value = status(target)
    assert value["id"] == "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1"
    assert value["stage_a_accounting"]["program_closed"] and value["prior_registration_attempts_used"] == 14
    assert value["stage_a_accounting"]["registration_attempts_used"] == 11
    assert value["stage_a_accounting"]["fit_seconds_charged"] == 35649.98936010008
    assert value["stage_b_registration_attempts_used"] == 0 and value["protected_future_registration_attempts"] == 7
    assert value["protected_future_compute_seconds"] == 47000 and not value["scoring_authorized"]
    assert not value["paid_run_pending"] and value["pending_fit_reservation_seconds"] == 0
    assert load_config(target).benchmark_status == "maintenance"
    assert verify_manifest(target)["ok"]
    verify_preflight_certificate(target)
    for marker in ("STOP", "PAUSE", "research/run.lock"):
        assert not (target / marker).exists(), marker
    for commit in ("7344683c2c358de262b3e6b26ece0839c234a96a", "905ed709ad18d3fdc2dac863deb121cefbf1b874"):
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=target, check=True)
    label = "original" if original else "clone"
    receipt = {"created_at": utc_now(), "target": str(target), "parent_commit": PARENT,
        "old_nonmutable_raw_files": checked, "all_old_candidate_test_and_scientific_records_preserved": True,
        "append_only_prefixes_preserved": True, "old_authority_headers_preserved": True,
        "all112_scientific_source_bytes_preserved": True, "actual25_fitted_states_and50_files_verified": True,
        "no_source_fit_replay_or_new_target_data": True, "stage_a_closed_and_bound": True,
        "stage_b_tickets_used": 0, "protected_future_tickets": 7, "protected_future_compute_seconds": 47000,
        "integrity_preflight": True, "scoring": False, "program_status": value}
    path = root / f"research/reviews/NEXTAI-B-history-{label}-V1.json"
    assert not path.exists()
    atomic_write_json(path, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != "program_status"}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--original", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.snapshot:
        make_snapshot(root)
    check(root, original=args.original, seal=args.seal)


if __name__ == "__main__":
    main()
