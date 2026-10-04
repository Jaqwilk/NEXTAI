"""Private v2 task: balanced, semantically computed composition strata."""
from __future__ import annotations

import random

from .muc_contract import parse_statement
from .muc01_task import PublicQuestion, PublicWorld, TRAIN_TUPLES, HELDOUT_TUPLES, make_world as old_world, _answer


def make_world(knowledge_size: int, depth: int, seed: int, split: str) -> PublicWorld:
    original = old_world(knowledge_size, depth, seed, split)
    mapping, replaced = {}, set()
    for text in original.statements:
        step, subject, relation, target = parse_statement(text)
        key = (subject, relation)
        if key in mapping:
            replaced.add(key)
        mapping[key] = target
    entities = sorted({key[0] for key in mapping})
    rng = random.Random(seed ^ 0x4D554332)
    groups = [(False, 6, 8, 2)]
    if split == "F" and depth > 1:
        groups = [(False, 3, 4, 1), (True, 3, 4, 1)]
    questions = []
    for unseen, replacements, retention, unknowns in groups:
        pool = HELDOUT_TUPLES[depth] if unseen else TRAIN_TUPLES[depth]
        for kind in ["replacement"] * replacements + ["retention"] * retention + ["unknown"] * unknowns:
            chosen = None
            for _ in range(4000):
                start = f"E{split}999" if kind == "unknown" else rng.choice(entities)
                relations = rng.choice(pool)
                answer, path = _answer(mapping, start, relations)
                affected = any(key in replaced for key in path)
                if kind == "unknown" or affected == (kind == "replacement"):
                    chosen = start, relations, answer, affected
                    break
            if chosen is None:
                raise RuntimeError("Cannot satisfy v2 query strata")
            start, relations, answer, affected = chosen
            semantic_unseen = relations not in TRAIN_TUPLES[depth]
            questions.append(PublicQuestion(
                f"Starting at {start}, follow {', then '.join(relations)}. Which contact is reached now?",
                answer, affected, kind == "retention", kind == "unknown", semantic_unseen))
    rng.shuffle(questions)
    return PublicWorld(original.statements, tuple(questions))


def training_worlds(k: int, d: int):
    train = tuple(make_world(k, d, 1103_000 + k * 100 + d * 10 + i, "T") for i in range(45))
    dev = tuple(make_world(k, d, 2207_000 + k * 100 + d * 10 + i, "D") for i in range(15))
    return train, dev


def calibration_worlds(k: int, d: int, seed: int):
    return tuple(make_world(k, d, seed * 1000 + k * 100 + d * 10 + i, "F") for i in range(15))
