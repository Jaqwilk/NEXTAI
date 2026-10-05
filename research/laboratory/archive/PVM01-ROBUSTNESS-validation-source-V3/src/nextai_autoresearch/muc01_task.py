"""Public data contract for the MUC-01 calibration cohort.

The module owns deterministic text generation only.  Systems receive serialized
statements and questions; private maps and query strata stay in the evaluator.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


RELATIONS = ("amber", "copper", "jade", "coral", "indigo", "pearl", "silver", "umber")
TRAIN_TUPLES = {
    1: tuple((r,) for r in RELATIONS),
    2: tuple((RELATIONS[i], RELATIONS[(i + 1) % 8]) for i in range(8)),
    4: tuple(tuple(RELATIONS[(i + j) % 8] for j in range(4)) for i in range(8)),
}
HELDOUT_TUPLES = {
    1: TRAIN_TUPLES[1],
    2: tuple((RELATIONS[i], RELATIONS[(i + 3) % 8]) for i in range(8)),
    4: tuple(tuple(RELATIONS[(i + 2 * j) % 8] for j in range(4)) for i in range(8)),
}


@dataclass(frozen=True)
class PublicQuestion:
    text: str
    answer: str
    replacement_affected: bool
    unchanged_retention: bool
    unknown: bool
    unseen_composition: bool


@dataclass(frozen=True)
class PublicWorld:
    statements: tuple[str, ...]
    questions: tuple[PublicQuestion, ...]


def _entity(split: str, index: int) -> str:
    return f"E{split}{index:03d}"


def _answer(mapping: dict[tuple[str, str], str], start: str, relations: tuple[str, ...]) -> tuple[str, tuple[tuple[str, str], ...]]:
    current = start
    path: list[tuple[str, str]] = []
    for relation in relations:
        key = (current, relation)
        path.append(key)
        if key not in mapping:
            return "UNKNOWN", tuple(path)
        current = mapping[key]
    return current, tuple(path)


def make_world(knowledge_size: int, depth: int, seed: int, split: str) -> PublicWorld:
    if knowledge_size not in (32, 128, 512) or depth not in (1, 2, 4):
        raise ValueError("MUC-01 uses K={32,128,512} and D={1,2,4}")
    if split not in {"T", "D", "F"}:
        raise ValueError("split must be T, D or F")
    rng = random.Random(seed)
    entity_count = knowledge_size // len(RELATIONS)
    entities = [_entity(split, i) for i in range(entity_count)]
    mapping: dict[tuple[str, str], str] = {}
    for subject in entities:
        for relation in RELATIONS:
            mapping[(subject, relation)] = rng.choice(entities)

    replaced = set(rng.sample(list(mapping), knowledge_size // 4))
    rows: list[tuple[int, str]] = []
    timestamp = 0
    for subject, relation in mapping:
        if (subject, relation) in replaced:
            old = rng.choice([entity for entity in entities if entity != mapping[(subject, relation)]])
            rows.append((timestamp, f"At step {timestamp:04d}, {subject}'s {relation} contact became {old}."))
            timestamp += 1
        rows.append((timestamp, f"At step {timestamp:04d}, {subject}'s {relation} contact became {mapping[(subject, relation)]}."))
        timestamp += 1
    rows.sort()

    tuples = HELDOUT_TUPLES[depth] if split == "F" and depth > 1 else TRAIN_TUPLES[depth]
    requested = [(True, False)] * 6 + [(False, False)] * 8 + [(False, True)] * 2
    questions: list[PublicQuestion] = []
    for question_index, (want_replaced, want_unknown) in enumerate(requested):
        unseen = bool(split == "F" and depth > 1 and question_index < 8)
        relation_pool = HELDOUT_TUPLES[depth] if unseen else tuples
        chosen = None
        for _ in range(4000):
            start = rng.choice(entities)
            relations = rng.choice(relation_pool)
            answer, path = _answer(mapping, start, relations)
            affected = any(key in replaced for key in path)
            if want_unknown:
                # A public but absent relation creates an unambiguous UNKNOWN path.
                relations = tuple(relations[:-1]) + ("violet",)
                answer, path = _answer(mapping, start, relations)
                affected = any(key in replaced for key in path)
            if (answer == "UNKNOWN") == want_unknown and (not want_replaced or affected):
                if want_replaced or want_unknown or not affected:
                    chosen = (start, relations, answer, affected)
                    break
        if chosen is None:
            raise RuntimeError("Could not satisfy frozen MUC-01 query strata")
        start, relations, answer, affected = chosen
        chain = ", then ".join(relations)
        text = f"Starting at {start}, follow {chain}. Which contact is reached now?"
        questions.append(PublicQuestion(text, answer, affected, not affected and not want_unknown, want_unknown, unseen))
    return PublicWorld(tuple(text for _, text in rows), tuple(questions))


def split_worlds(knowledge_size: int, depth: int, scoring_seed: int) -> tuple[tuple[PublicWorld, ...], tuple[PublicWorld, ...], tuple[PublicWorld, ...]]:
    train = tuple(make_world(knowledge_size, depth, 1103_000 + knowledge_size * 100 + depth * 10 + i, "T") for i in range(45))
    development = tuple(make_world(knowledge_size, depth, 2207_000 + knowledge_size * 100 + depth * 10 + i, "D") for i in range(15))
    calibration = tuple(make_world(knowledge_size, depth, scoring_seed * 1000 + knowledge_size * 100 + depth * 10 + i, "F") for i in range(15))
    return train, development, calibration
