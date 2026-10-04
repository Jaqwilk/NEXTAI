"""Private fresh train/dev units and fixed diagnostics; never imported by a model."""
import hashlib
import random

from .muc02_task import make_world
from .muc_contract import parse_statement

TAG = "MUC02-HARD-NEGATIVES-20261003-V1"


def world_seed(seed, split, k, d, index, proposal=0):
    suffix = f"|proposal={proposal}" if proposal else ""
    raw = f"{TAG}|{seed}|{split}|{k}|{d}|{index}{suffix}".encode()
    return (1 << 128) + int.from_bytes(hashlib.sha256(raw).digest()[:16], "big")


def fresh_worlds(seed, split, k, d, proposal_sink=None):
    if split not in {"T", "D"}:
        raise ValueError("Only fresh train/dev are authorized")
    worlds = []
    for index in range(45 if split == "T" else 15):
        for proposal in range(64):
            actual_seed = world_seed(seed, split, k, d, index, proposal)
            try:
                world = make_world(k, d, actual_seed, split)
            except RuntimeError as exc:
                if "query strata" not in str(exc):
                    raise
                if proposal_sink:
                    proposal_sink({"seed": seed, "split": split, "K": k, "D": d, "world": index,
                                   "proposal": proposal, "world_seed": str(actual_seed), "accepted": False, "reason": str(exc)})
                continue
            if proposal_sink:
                proposal_sink({"seed": seed, "split": split, "K": k, "D": d, "world": index,
                               "proposal": proposal, "world_seed": str(actual_seed), "accepted": True})
            worlds.append(world)
            break
        else:
            raise RuntimeError("All 64 structural world proposals failed; no experiment retry")
    return tuple(worlds)


def diagnostic_queries(world, seed, k, d, index):
    rows = tuple(parse_statement(text) for text in world.statements)
    if any(row is None for row in rows):
        raise ValueError("Malformed dev statement")
    keys = sorted({(row[1], row[2]) for row in rows})
    rng = random.Random(world_seed(seed, "D", k, d, index) ^ 0x44494147)
    known = rng.sample(keys, 2)
    return tuple(known) + (("ED999", known[0][1]), (known[1][0], "violet")), rows
