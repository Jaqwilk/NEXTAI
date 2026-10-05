"""Private fresh graphs and paired namespace intervention, never model imports."""
from dataclasses import replace
import hashlib
import random

from .muc02_task import make_world
from .muc_contract import parse_statement


def world_seed(tag, seed, split, k, d, index, proposal=0):
    suffix = f"|proposal={proposal}" if proposal else ""
    raw = f"{tag}|{seed}|{split}|{k}|{d}|{index}{suffix}".encode()
    return (1 << 128) + int.from_bytes(hashlib.sha256(raw).digest()[:16], "big")


def fresh_worlds(tag, seed, split, k, d, count, proposal_sink=None):
    if split not in {"T", "D"}:
        raise ValueError("This diagnostic authorizes fresh train/dev only")
    worlds = []
    for index in range(count):
        for proposal in range(64):
            actual = world_seed(tag, seed, split, k, d, index, proposal)
            try:
                world = make_world(k, d, actual, split)
            except RuntimeError as exc:
                if "query strata" not in str(exc):
                    raise
                if proposal_sink:
                    proposal_sink({"seed": seed, "split": split, "K": k, "D": d, "world": index,
                                   "proposal": proposal, "world_seed": str(actual), "accepted": False, "reason": str(exc)})
                continue
            if proposal_sink:
                proposal_sink({"seed": seed, "split": split, "K": k, "D": d, "world": index,
                               "proposal": proposal, "world_seed": str(actual), "accepted": True})
            worlds.append(world)
            break
        else:
            raise RuntimeError("All64 structural proposals failed; no scored retry")
    return tuple(worlds)


def iid_namespace(world):
    return replace(world, statements=tuple(s.replace("ED", "ET") for s in world.statements),
                   questions=tuple(replace(q, text=q.text.replace("ED", "ET"), answer=q.answer.replace("ED", "ET")) for q in world.questions))


def diagnostic_queries(tag, world, seed, k, d, index):
    rows = tuple(parse_statement(s) for s in world.statements)
    if any(row is None for row in rows):
        raise ValueError("Malformed public diagnostic statements")
    keys = sorted({(row[1], row[2]) for row in rows})
    # Renamed graphs have identical key ordering, so the numeric known probes match.
    rng = random.Random(world_seed(tag, seed, "D", k, d, index) ^ 0x44494147)
    known = rng.sample(keys, 2)
    namespace = known[0][0][:2]
    return tuple(known) + ((namespace + "999", known[0][1]), (known[1][0], "violet"))
