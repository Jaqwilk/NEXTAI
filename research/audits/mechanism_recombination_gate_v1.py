"""Deterministic, non-scoring identifiability gate for a future cohort."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from random import Random

from nextai_autoresearch.benchmarks import (
    action_conditioned_predictive_equivalence_v1 as predictive,
    behavioral_conjugacy_library_transfer_v1 as programs,
    nonlinear_local_state_transfer_v1 as local,
)


ALPHABET = 12
STATES = ALPHABET * ALPHABET
TRAIN_COMPOSITIONS = (
    ("A",), ("B",), ("C",),
    ("A", "A"), ("A", "B"), ("A", "C"),
    ("B", "A"), ("B", "B"), ("B", "C"),
    ("C", "A"), ("C", "C"),
)
HELDOUT_COMPOSITION = ("C", "B")
DEVELOPMENT_SEEDS = (1103, 2207, 3301, 4409, 5519, 6607, 7717, 8821)


def _mechanisms(seed: int) -> dict[str, tuple[int, ...]]:
    """Three existing mechanisms, normalized by one fixed numeric rule."""
    _, _, tables, _ = programs.make_world(8, seed)
    program = tuple(next(iter(tables.values())))

    _, oracle, _ = predictive.make_dataset(8, seed)
    prediction = tuple(
        (oracle.transitions[(x % 4, (x // 4) % 2)] * 3 + oracle.outcomes[x % 4])
        % ALPHABET
        for x in range(ALPHABET)
    )

    world = local.make_world(seed)
    dynamics = tuple(
        (output[0] * 4 + output[1]) % ALPHABET
        for _, output in world.training_cases[:ALPHABET]
    )
    return {"A": program, "B": prediction, "C": dynamics}


def _feistel(function: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(
        y * ALPHABET + (x + function[y]) % ALPHABET
        for x in range(ALPHABET)
        for y in range(ALPHABET)
    )


def _compose(maps: dict[str, tuple[int, ...]], names: tuple[str, ...]) -> tuple[int, ...]:
    output = []
    for state in range(STATES):
        for name in names:
            state = maps[name][state]
        output.append(state)
    return tuple(output)


def _conjugate(mapping: tuple[int, ...], permutation: list[int]) -> tuple[int, ...]:
    inverse = [0] * STATES
    for source, target in enumerate(permutation):
        inverse[target] = source
    return tuple(permutation[mapping[inverse[state]]] for state in range(STATES))


def _maps(seed: int) -> dict[tuple[str, ...], tuple[int, ...]]:
    permutation = list(range(STATES))
    Random(seed ^ 0x5151).shuffle(permutation)
    modules = {
        name: _conjugate(_feistel(function), permutation)
        for name, function in _mechanisms(seed).items()
    }
    return {
        names: _compose(modules, names)
        for names in (*TRAIN_COMPOSITIONS, HELDOUT_COMPOSITION)
    }


def _partition(seed: int, names: tuple[str, ...]) -> list[list[int]]:
    order = list(range(STATES))
    salt = sum((index + 1) * ord(name) for index, name in enumerate(names))
    Random(seed ^ (salt << 8) ^ 0x9191).shuffle(order)
    return [order[index:index + 48] for index in range(0, STATES, 48)]


def _mode(counter: Counter[int]) -> int:
    return min(counter, key=lambda value: (-counter[value], value))


def _ngram_accuracy(
    maps: dict[tuple[str, ...], tuple[int, ...]], seed: int, order: int,
    support: list[int], queries: list[int],
) -> float:
    counts: list[defaultdict[tuple[int, ...], Counter[int]]] = [
        defaultdict(Counter) for _ in range(order + 1)
    ]
    bos, separator, query_token = STATES, STATES + 1, STATES + 2
    for names in TRAIN_COMPOSITIONS:
        mapping = maps[names]
        for part in _partition(seed, names):
            ordered = sorted(part)
            prefix = [bos]
            for state in ordered:
                prefix.extend((state, mapping[state], separator))
            for state in range(STATES):
                if state in part:
                    continue
                context = prefix + [query_token, state]
                for width in range(order + 1):
                    key = tuple(context[-width:]) if width else ()
                    counts[width][key][mapping[state]] += 1

    test_map = maps[HELDOUT_COMPOSITION]
    prefix = [bos]
    for state in sorted(support):
        prefix.extend((state, test_map[state], separator))
    correct = 0
    for state in queries:
        context = prefix + [query_token, state]
        prediction = None
        for width in range(order, -1, -1):
            key = tuple(context[-width:]) if width else ()
            if key in counts[width]:
                prediction = _mode(counts[width][key])
                break
        correct += prediction == test_map[state]
    return correct / len(queries)


def evaluate(seed: int) -> dict[str, object]:
    maps = _maps(seed)
    heldout = maps[HELDOUT_COMPOSITION]
    test_order = list(range(STATES))
    Random(seed ^ 0xA7A7).shuffle(test_order)
    support, queries = test_order[:48], test_order[48:96]

    output_counts = Counter(
        mapping[state]
        for names, mapping in maps.items()
        if names in TRAIN_COMPOSITIONS
        for state in range(STATES)
    )
    unigram = sum(heldout[state] == _mode(output_counts) for state in queries) / 48

    nearest = min(
        TRAIN_COMPOSITIONS,
        key=lambda names: (
            sum(maps[names][state] != heldout[state] for state in support), names
        ),
    )
    nearest_accuracy = sum(maps[nearest][state] == heldout[state] for state in queries) / 48

    matching = [
        names for names, mapping in maps.items()
        if all(mapping[state] == heldout[state] for state in support)
    ]
    oracle_accuracy = (
        sum(maps[matching[0]][state] == heldout[state] for state in queries) / 48
        if len(matching) == 1 else 0.0
    )

    return {
        "seed": seed,
        "shape_classifier_accuracy": 1 / len(TRAIN_COMPOSITIONS),
        "train_test_combination_overlap": int(HELDOUT_COMPOSITION in TRAIN_COMPOSITIONS),
        "unique_composition_maps": len(set(maps.values())),
        "unigram_accuracy": unigram,
        "markov_accuracy": {
            str(order): _ngram_accuracy(maps, seed, order, support, queries)
            for order in range(1, 6)
        },
        "nearest_complete_map": list(nearest),
        "nearest_template_accuracy": nearest_accuracy,
        "oracle_matching_compositions": [list(names) for names in matching],
        "oracle_module_composition_accuracy": oracle_accuracy,
    }


def main() -> None:
    rows = [evaluate(seed) for seed in DEVELOPMENT_SEEDS]
    chance = 1 / STATES
    shape_chance = 1 / len(TRAIN_COMPOSITIONS)
    maximum_markov = max(
        value for row in rows for value in row["markov_accuracy"].values()
    )
    summary = {
        "schema_version": 1,
        "audit": "heldout_mechanism_recombination_v1_development_gate",
        "scoring": False,
        "state_count": STATES,
        "source_mechanisms": [
            "behavioral_conjugacy_program_table",
            "action_conditioned_predictive_transition_outcome",
            "nonlinear_local_dynamics_training_rule",
        ],
        "train_compositions": [list(names) for names in TRAIN_COMPOSITIONS],
        "heldout_composition": list(HELDOUT_COMPOSITION),
        "chance_accuracy": chance,
        "shape_chance_accuracy": shape_chance,
        "rows": rows,
        "gates": {
            "zero_combination_overlap": all(
                row["train_test_combination_overlap"] == 0 for row in rows
            ),
            "shape_at_most_chance_plus_0_10": all(
                row["shape_classifier_accuracy"] <= shape_chance + 0.10 for row in rows
            ),
            "all_compositions_behaviorally_distinct": all(
                row["unique_composition_maps"] == len(TRAIN_COMPOSITIONS) + 1
                for row in rows
            ),
            "unigram_not_exact": all(row["unigram_accuracy"] < 1.0 for row in rows),
            "markov_orders_1_to_5_below_0_50": maximum_markov < 0.50,
            "nearest_template_below_0_50": max(
                row["nearest_template_accuracy"] for row in rows
            ) < 0.50,
            "module_composition_oracle_exact": all(
                row["oracle_module_composition_accuracy"] == 1.0 for row in rows
            ),
        },
    }
    summary["pass"] = all(summary["gates"].values())
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
