from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


@dataclass(frozen=True)
class ReactionState:
    next_nodes: tuple[int, ...]
    values: tuple[int, ...]
    active: tuple[int, ...]


@dataclass(frozen=True)
class ReactionEpisode:
    before: ReactionState
    after: ReactionState


Rule = tuple[tuple[int, int], tuple[int, int]]


def _active(state: ReactionState) -> tuple[int | None, int, int]:
    source = None
    for index, flag in enumerate(state.active):
        if flag:
            source = index
    return source, len(state.active), len(state.active)


def extract_rule(episode: ReactionEpisode) -> tuple[Rule, int]:
    source, operations, reads = _active(episode.before)
    if source is None:
        raise ValueError("reaction episode has no active particle")
    successor = episode.before.next_nodes[source]
    key = (episode.before.values[source], episode.before.values[successor])
    output = (episode.after.values[source], episode.after.values[successor])
    return (key, output), operations + reads + 8


def _apply(state: ReactionState, source: int, output: tuple[int, int]) -> ReactionState:
    successor = state.next_nodes[source]
    values, active = list(state.values), list(state.active)
    values[source], values[successor] = output
    active[source], active[successor] = 0, 1
    return ReactionState(state.next_nodes, tuple(values), tuple(active))


class ReactionBase(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_active_events = self.last_full_scans = self.last_bytes_scanned = 0
        self.last_converged = self.last_oscillated = 0

    def _record(self, operations: int, reads: int, events: int, scans: int, converged: bool, oscillated: bool) -> None:
        self.last_ops, self.last_bytes_scanned = operations, 8 * reads
        self.last_active_events, self.last_full_scans = events, scans
        self.last_converged, self.last_oscillated = int(converged), int(oscillated)


class RandomReaction(ReactionBase):
    metadata = CandidateMetadata("random_reaction_guess", "random", "Independent random particle state")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.rng, self.width, self.fit_ops = random.Random(self.seed), universe_size, 0

    def query(self, source: ReactionState, steps: int) -> ReactionState:
        values = tuple(self.rng.randrange(4) for _ in source.values)
        active_index = self.rng.randrange(len(values))
        active = tuple(int(index == active_index) for index in range(len(values)))
        self._record(2 * len(values), 2 * len(values), 0, 0, False, False)
        return ReactionState(source.next_nodes, values, active)

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class TrajectoryMemorizer(ReactionBase):
    metadata = CandidateMetadata("reaction_trajectory_memorizer", "memorizer", "Whole-state transition lookup")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        episodes = tuple(facts)
        self.memory = {episode.before: episode.after for episode in episodes}
        self.fit_ops = len(episodes) * universe_size * 3

    def query(self, source: ReactionState, steps: int) -> ReactionState:
        answer = self.memory.get(source, source) if steps == 1 else source
        found = answer is not source
        width = len(source.values)
        self._record(3 * width, 3 * width, int(found), 1, found, False)
        return answer

    def update(self, source: ReactionEpisode, target: int) -> None:
        self.memory[source.before] = source.after
        self.update_ops = 3 * len(source.before.values)

    def state_bytes(self) -> int:
        return 64 + sum(6 * len(state.values) for state in self.memory) * 8


class LearnedRules(ReactionBase):
    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.rules, self.fit_ops = {}, 0
        for episode in facts:
            (key, output), operations = extract_rule(episode)
            self.rules[key] = output
            self.fit_ops += operations

    def update(self, source: ReactionEpisode, target: int) -> None:
        (key, output), operations = extract_rule(source)
        self.rules[key] = output
        self.update_ops = operations

    def state_bytes(self) -> int:
        return 128 + 112 * len(self.rules)


class LearnedSweep(LearnedRules):
    metadata = CandidateMetadata("learned_reaction_sweep", "message_passing", "Learned rules with dense synchronous sweeps")

    def query(self, source: ReactionState, steps: int) -> ReactionState:
        state, operations, reads, events, visited = source, 0, 0, 0, set()
        for _ in range(steps):
            active, scan_ops, scan_reads = _active(state)
            operations, reads = operations + scan_ops, reads + scan_reads
            if active is None:
                break
            successor = state.next_nodes[active]
            output = self.rules.get((state.values[active], state.values[successor]))
            operations += 9
            reads += 3
            if output is None:
                break
            visited.add(active)
            state = _apply(state, active, output)
            events += 1
        oscillated = len(visited) < events
        self._record(operations, reads, events, events, events == steps, oscillated)
        return state


class PointerReaction(LearnedRules):
    metadata = CandidateMetadata("learned_reaction_recurrent", "recurrent", "Pointer recurrent controller with linear rule selection")
    indexed = False

    def _lookup(self, key: tuple[int, int]) -> tuple[tuple[int, int] | None, int, int]:
        if self.indexed:
            return self.rules.get(key), 3, 2
        operations = reads = 0
        for candidate_key, output in self.rules.items():
            operations += 3
            reads += 2
            if candidate_key == key:
                return output, operations, reads
        return None, operations, reads

    def query(self, source: ReactionState, steps: int) -> ReactionState:
        state = source
        active, operations, reads = _active(state)
        events, visited = 0, set()
        while active is not None and events < steps:
            successor = state.next_nodes[active]
            output, lookup_ops, lookup_reads = self._lookup((state.values[active], state.values[successor]))
            operations += lookup_ops + 6
            reads += lookup_reads + 3
            if output is None:
                break
            visited.add(active)
            state = _apply(state, active, output)
            active = successor
            events += 1
        oscillated = len(visited) < events
        self._record(operations, reads, events, 1, events == steps, oscillated)
        return state


class ReteReaction(PointerReaction):
    metadata = CandidateMetadata("rete_reaction_engine", "production_system", "Compiled indexed production matching")
    indexed = True


class SemanticReactor(ReteReaction):
    metadata = CandidateMetadata("learned_semantic_reactor", "cognitive_chemistry", "Learned indexed local reaction agenda")


class OracleReaction(ReteReaction):
    metadata = CandidateMetadata("oracle_reaction_engine", "oracle", "True local reaction rules")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.rules = dict(tuple(facts)[0])
        self.fit_ops = 0

    def update(self, source: ReactionEpisode, target: int) -> None:
        self.update_ops = 1
