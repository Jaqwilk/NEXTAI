"""Exact release-name aliases only; validate every metadata item before content."""
from pathlib import Path

from .asm01_grammar_inventory import WRITERS, inventory_bytes

PER_FILE_BYTES_CAP = 262144
TOTAL_BYTES_CAP = 479723520
DATASET_DIRECTORY = "Online Handwritten Assamese Characters Dataset"


def _canonical(name):
    return name[:-4] + ".txt" if name.endswith(".TXT") else name


def screen_members(directory: Path, listing: str):
    expected = {f"{DATASET_DIRECTORY}/W{w}/{c}.{w}.txt"
                for w in WRITERS for c in range(1, 184)}
    names = listing.splitlines()
    normalized = [_canonical(name) for name in names]
    if len(names) != 1830 or len(set(normalized)) != 1830 or set(normalized) != expected:
        raise ValueError("Exactly1830 unique frozen canonical members required")
    # Inspect links before resolving/traversing; never follow a future directory.
    for ancestor in (directory, *directory.parents):
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError("Linked inventory root/ancestor forbidden")
    if not directory.is_dir():
        raise ValueError("Inventory root must be a directory")
    base = directory.resolve()
    allowed_directories = {DATASET_DIRECTORY} | {f"{DATASET_DIRECTORY}/W{w}" for w in WRITERS}
    stack, actual, paths = [directory], set(), {}
    while stack:
        parent = stack.pop()
        for path in parent.iterdir():
            if path.is_symlink() or path.is_junction():
                raise ValueError("Linked inventory member/directory forbidden")
            if not path.resolve().is_relative_to(base):
                raise ValueError("Inventory member outside frozen scope")
            name = path.relative_to(directory).as_posix()
            if path.is_dir():
                if name not in allowed_directories:
                    raise ValueError("Unexpected inventory directory; do not descend")
                stack.append(path)
            elif path.is_file():
                key = _canonical(name)
                if key not in expected or key in paths or name in actual:
                    raise ValueError("Foreign or colliding extracted inventory member")
                actual.add(name)
                paths[key] = path
            else:
                raise ValueError("Nonregular inventory member forbidden")
    # Raw strings matter: Windows Path equality can case-fold names.
    if len(paths) != 1830 or set(paths) != expected or actual != set(names):
        raise ValueError("Extracted raw membership differs from frozen listing")
    total, members = 0, []
    for writer in WRITERS:
        for sample in range(1, 184):
            path = paths[f"{DATASET_DIRECTORY}/W{writer}/{sample}.{writer}.txt"]
            size = path.stat().st_size
            if type(size) is not int or size < 0 or size > PER_FILE_BYTES_CAP:
                raise ValueError("Inventory per-file byte cap")
            total += size
            members.append((writer, sample, path))
    if total > TOTAL_BYTES_CAP:
        raise ValueError("Inventory aggregate byte cap")
    return members
