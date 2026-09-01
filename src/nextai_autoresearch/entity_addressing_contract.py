from __future__ import annotations

from dataclasses import dataclass


OBSERVATION_DIMENSION = 24
KNOWLEDGE_SIZES = (32, 320, 3200)
DEPTHS = (1, 4, 8)


@dataclass(frozen=True)
class TransitionBurst:
    observations: tuple[tuple[float, ...], ...]
    value: int


@dataclass(frozen=True)
class RawQuery:
    observation: tuple[float, ...]
    signature: int


@dataclass(frozen=True)
class PrivateQuery(RawQuery):
    entity: int


@dataclass(frozen=True)
class PrivateSpec:
    transitions: dict[int, int]
    values: dict[int, int]


ROLE_CONTRACT = {
    "learned_discrete_address_index_v1": "learned encoder -> discrete key -> bounded index -> verifier -> fallback",
    "source_identical_dense_scan_v1": "same learned encoder and verifier with dense access",
    "source_identical_frozen_encoder_index_v1": "same bounded index with frozen encoder",
    "source_identical_shuffled_representation_index_v1": "same bounded index with shuffled representation",
    "raw_nearest_neighbour_scan_v1": "classical raw-space nearest-neighbour scan",
    "local_dense_transition_gru_v1": "small locally trained dense GRU transition model without external memory",
    "privileged_exact_entity_key_v1": "evaluator-private exact-key control",
}
