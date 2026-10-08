"""Frozen V3 synthetic metadata cases; never access native sample payloads."""
import hashlib
from pathlib import Path

import pytest

from nextai_autoresearch import asm01_grammar_inventory as original
from nextai_autoresearch import asm01_inventory_members_v3 as members
from nextai_autoresearch import asm01_inventory_v3 as entrypoint


SCANNER_SHA = "cd5759386fa5f412ea125c849c5958b7d284dec91e811f93f173a6ccb544eb86"
STUDY = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.json"
STUDY_SHA = "730a9e6843eaf085970bad82e5878dc404f400634e0c8ff18ab9af0e4c46888d"
ADAPTER_CASES = (
    "accept-lower", "accept-mixed-actual-paths", "listing-missing",
    "listing-extra", "listing-duplicate", "listing-alias-collision",
    "listing-future", "listing-traversal", "listing-absolute",
    "listing-backslash", "listing-mixedcase", "listing-dircase", "listing-uid",
    "disk-missing", "disk-extra", "disk-alias-collision", "disk-rawcase-mismatch",
    "disk-foreign-dir", "root-symlink", "root-junction", "ancestor-link",
    "file-link", "directory-link", "resolved-escape", "per-file-cap",
    "aggregate-cap", "scanner-identity", "metadata-before-payload",
)


def listing_names(mixed=False):
    return [
        f"Online Handwritten Assamese Characters Dataset/W{writer}/{sample}.{writer}"
        + (".TXT" if mixed and writer == 5 and sample <= 153 else ".txt")
        for writer in original.WRITERS for sample in range(1, 184)
    ]


def synthetic_tree(directory, names):
    for name in names:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"Synthetic fixture only; no native payload.\n")


def trap_payload_methods(monkeypatch):
    calls = []

    def forbidden(path, *args, **kwargs):
        calls.append(str(path))
        pytest.fail("Metadata adapter attempted payload access")

    for method in ("open", "read_bytes", "read_text"):
        monkeypatch.setattr(Path, method, forbidden)
    return calls


def fake_link(monkeypatch, method, target):
    real = getattr(Path, method)
    target_string = target.as_posix()

    def linked(path):
        return path.as_posix() == target_string or real(path)

    monkeypatch.setattr(Path, method, linked)


@pytest.mark.parametrize("case", ADAPTER_CASES, ids=ADAPTER_CASES)
def test_frozen_adapter_cases(monkeypatch, tmp_path, case):
    assert members.PER_FILE_BYTES_CAP == 262144
    assert members.TOTAL_BYTES_CAP == 479723520
    if case == "scanner-identity":
        assert members.inventory_bytes is original.inventory_bytes
        assert entrypoint.inventory_bytes is original.inventory_bytes
        assert hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest() == SCANNER_SHA
        return

    names = listing_names(mixed=case == "accept-mixed-actual-paths")
    directory = tmp_path / "screen"
    directory.mkdir()
    if case.startswith("listing-"):
        if case == "listing-missing":
            names.pop()
        elif case == "listing-extra":
            names.append("foreign.txt")
        elif case == "listing-duplicate":
            names[-1] = names[0]
        elif case == "listing-alias-collision":
            names[-1] = names[0][:-4] + ".TXT"
        elif case == "listing-future":
            names[-1] = names[-1].replace("W20/183.20", "W21/183.21")
        elif case == "listing-traversal":
            names[-1] = "../outside.txt"
        elif case == "listing-absolute":
            names[-1] = "/" + names[-1]
        elif case == "listing-backslash":
            names[-1] = names[-1].replace("/", "\\")
        elif case == "listing-mixedcase":
            names[-1] = names[-1][:-4] + ".TxT"
        elif case == "listing-dircase":
            names[-1] = names[-1].replace("/W20/", "/w20/")
        elif case == "listing-uid":
            names[-1] = names[-1].replace("183.20.txt", "183.19.txt")
        calls = trap_payload_methods(monkeypatch)
        with pytest.raises(ValueError):
            members.screen_members(directory, "\n".join(names) + "\n")
        assert calls == []
        return

    synthetic_tree(directory, names)
    first, last = directory / names[0], directory / names[-1]
    dataset = directory / "Online Handwritten Assamese Characters Dataset"
    if case == "disk-missing":
        last.unlink()
    elif case == "disk-extra":
        (directory / "foreign.txt").write_bytes(b"Synthetic extra file.\n")
    elif case == "disk-alias-collision":
        real_iterdir = Path.iterdir
        alias = first.with_suffix(".TXT")

        def with_alias(path):
            entries = list(real_iterdir(path))
            if path.as_posix() == first.parent.as_posix():
                entries.append(alias)
            return iter(entries)

        monkeypatch.setattr(Path, "iterdir", with_alias)
    elif case == "disk-rawcase-mismatch":
        # Keep canonical identity identical while changing the listed raw alias.
        names[0] = names[0][:-4] + ".TXT"
    elif case == "disk-foreign-dir":
        foreign = dataset / "W21"
        foreign.mkdir()
        real_iterdir = Path.iterdir

        def no_foreign_descent(path):
            assert path.as_posix() != foreign.as_posix(), "Entered forbidden directory"
            return real_iterdir(path)

        monkeypatch.setattr(Path, "iterdir", no_foreign_descent)
    elif case == "root-symlink":
        fake_link(monkeypatch, "is_symlink", directory)
    elif case == "root-junction":
        fake_link(monkeypatch, "is_junction", directory)
    elif case == "ancestor-link":
        fake_link(monkeypatch, "is_symlink", directory.parent)
    elif case == "file-link":
        fake_link(monkeypatch, "is_symlink", first)
    elif case == "directory-link":
        fake_link(monkeypatch, "is_junction", first.parent)
        real_iterdir = Path.iterdir

        def no_link_descent(path):
            assert path.as_posix() != first.parent.as_posix(), "Entered linked directory"
            return real_iterdir(path)

        monkeypatch.setattr(Path, "iterdir", no_link_descent)
    elif case == "resolved-escape":
        real_resolve = Path.resolve

        def escaped(path, *args, **kwargs):
            if path.as_posix() == first.as_posix():
                return tmp_path / "outside.txt"
            return real_resolve(path, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", escaped)
    elif case == "per-file-cap":
        last.write_bytes(b"x" * (members.PER_FILE_BYTES_CAP + 1))
    elif case == "aggregate-cap":
        # Every file remains within the unchanged production per-file bound.
        monkeypatch.setattr(members, "TOTAL_BYTES_CAP", 1)

    seen = set()
    if case == "metadata-before-payload":
        real_stat = Path.stat
        raw_names = set(names)

        def counted_stat(path, *args, **kwargs):
            try:
                relative = path.relative_to(directory).as_posix()
            except ValueError:
                relative = ""
            if relative in raw_names:
                seen.add(relative)
            return real_stat(path, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", counted_stat)

    calls = trap_payload_methods(monkeypatch)
    if case in {"accept-lower", "accept-mixed-actual-paths", "metadata-before-payload"}:
        result = members.screen_members(directory, "\n".join(names) + "\n")
        expected_uids = [(w, s) for w in original.WRITERS for s in range(1, 184)]
        assert [(w, s) for w, s, _ in result] == expected_uids
        assert [path.relative_to(directory).as_posix() for _, _, path in result] == names
        assert len(result) == 1830
        if case == "accept-mixed-actual-paths":
            assert sum(path.suffix == ".TXT" for _, _, path in result) == 153
        if case == "metadata-before-payload":
            assert seen == set(names)
    else:
        with pytest.raises(ValueError):
            members.screen_members(directory, "\n".join(names) + "\n")
    assert calls == []


def synthetic_checkout(monkeypatch, tmp_path, name="NEXTAI-VALIDATION-20261002"):
    root = tmp_path / name
    root.mkdir()
    monkeypatch.setattr(entrypoint, "__file__", str(root / "src/nextai_autoresearch/asm01_inventory_v3.py"))
    monkeypatch.setattr(entrypoint, "inventory_bytes", lambda *_: pytest.fail("Native payload reached"))
    monkeypatch.setattr(entrypoint, "screen_members", lambda *_: pytest.fail("Native enumeration reached"))
    return root


def test_wrong_checkout_rejected_before_payload(monkeypatch, tmp_path):
    synthetic_checkout(monkeypatch, tmp_path, "OTHER-CHECKOUT")
    with pytest.raises(AssertionError):
        entrypoint.main()


@pytest.mark.parametrize("sentinel", ["STOP", "PAUSE", "research/run.lock"], ids=["stop", "pause", "run-lock"])
def test_stop_rejected_before_payload(monkeypatch, tmp_path, sentinel):
    root = synthetic_checkout(monkeypatch, tmp_path)
    path = root / sentinel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic sentinel", encoding="ascii")
    with pytest.raises(AssertionError):
        entrypoint.main()


def test_wrong_study_hash_rejected_before_payload(monkeypatch, tmp_path):
    root = synthetic_checkout(monkeypatch, tmp_path)
    path = root / entrypoint.STUDY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"synthetic_wrong_plan":true}', encoding="ascii")
    with pytest.raises(AssertionError):
        entrypoint.main()


def test_fixed_v3_binding_and_unchanged_scanner_identity():
    assert entrypoint.STUDY == STUDY
    assert entrypoint.STUDY_SHA == STUDY_SHA
    assert entrypoint.inventory_bytes is members.inventory_bytes is original.inventory_bytes
    assert entrypoint.screen_members is members.screen_members
    assert hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest() == SCANNER_SHA
