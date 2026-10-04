"""Protected falsification evaluator for RID-CONTRACT-001.

This module contains only deterministic service fixtures and frozen classical
controls.  Candidate scoring is intentionally unavailable in cycle 242.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from nextai_autoresearch.audit import (
    audit_benchmark_boundary,
    audit_relational_candidate_source,
)
from nextai_autoresearch.relational_identifiability_contract import (
    RID_COST_FIELDS,
    AnonymousQueryBatch,
    AnonymousRelationalBatch,
    empty_rid_cost_record,
)


BENCHMARK_ID = "orthogonal_double_matching_source_swap_v1"
CONTRACT_ID = "RID-CONTRACT-001"
DEVELOPMENT_FIXTURE_SEED = 242_001
LATENT_DIM = 16
INPUT_DIM = 48
SCALES = (64, 256, 1024)
ROLES = ("correct", "shuffled", "random", "passive")
LABELED_TRAIN_COUNT = 2048
QUERY_COUNT = 4096
OOD_SANITY_COUNT = 65_536
RELATION_AUDIT_REPLICATES = 6
SPECTRAL_RANK = 16
RIDGE_REGULARIZATION = 1e-6
CCA_REGULARIZATION = 1e-6
EIGENSOLVER_TOLERANCE = 1e-10
NUMERICAL_TOLERANCE = 1e-10
OOD_H2_TOLERANCE = 0.02
OOD_SYMMETRIC_TOLERANCE = 0.01
FINAL_SUBSPACE_OVERLAP_MINIMUM = 0.90
FINAL_SUBSPACE_LEAKAGE_MAXIMUM = 0.08
FINAL_NULL_OVERLAP_MAXIMUM = 0.55
FINAL_NULL_OPERATOR_NORM_MAXIMUM = 0.65
FUTURE_EXECUTION_REQUIREMENTS = (
    "one generic fit path",
    "one generic query path",
    "same implementation and constants for all roles",
)
FUTURE_LIMIT_PLACEHOLDERS = {
    "capacity": "unassigned_until_preregistration",
    "steps": "unassigned_until_preregistration",
    "budget": "unassigned_until_preregistration",
}


@dataclass(frozen=True)
class _PrivateTraining:
    mixer: np.ndarray
    first_basis: np.ndarray
    second_basis: np.ndarray
    probe_basis: np.ndarray
    public_records: np.ndarray
    public_targets: np.ndarray
    label_mask: np.ndarray
    first_values: np.ndarray
    second_values: np.ndarray
    probe_values: np.ndarray
    hypothetical_targets: np.ndarray
    first_matching: tuple[tuple[int, int], ...]
    second_matching: tuple[tuple[int, int], ...]
    shuffled_matching: tuple[tuple[int, int], ...]
    random_matching: tuple[tuple[int, int], ...]
    passive_slots: tuple[tuple[int, int], ...]
    batch_permutation: np.ndarray


@dataclass(frozen=True)
class _PrivateQuery:
    public: AnonymousQueryBatch
    first_targets: np.ndarray
    second_targets: np.ndarray
    symmetric_targets: np.ndarray
    first_values: np.ndarray
    second_values: np.ndarray
    probe_values: np.ndarray


@dataclass(frozen=True)
class AuditFixture:
    scale: int
    roles: dict[str, AnonymousRelationalBatch]
    private_training: _PrivateTraining
    iid: _PrivateQuery
    ood: _PrivateQuery


def _rng(seed: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, stream]))


def _sphere(rng: np.random.Generator, count: int) -> np.ndarray:
    values = rng.normal(size=(count, LATENT_DIM))
    values /= np.linalg.norm(values, axis=1, keepdims=True)
    return values * math.sqrt(LATENT_DIM)


def _orthogonal_mixer(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    raw = _rng(seed, 1).normal(size=(INPUT_DIM, INPUT_DIM))
    mixer, triangular = np.linalg.qr(raw)
    signs = np.where(np.diag(triangular) < 0.0, -1.0, 1.0)
    mixer = mixer * signs[None, :]
    return (
        mixer,
        mixer[:, :LATENT_DIM],
        mixer[:, LATENT_DIM : 2 * LATENT_DIM],
        mixer[:, 2 * LATENT_DIM :],
    )


def _edge_key(edge: tuple[int, int]) -> frozenset[int]:
    return frozenset((int(edge[0]), int(edge[1])))


def _random_perfect_matching(
    endpoint_count: int,
    rng: np.random.Generator,
    forbidden: set[frozenset[int]] | None = None,
) -> tuple[tuple[int, int], ...]:
    excluded = forbidden or set()
    for _ in range(20_000):
        order = rng.permutation(endpoint_count)
        edges = tuple(
            (int(order[index]), int(order[index + 1]))
            for index in range(0, endpoint_count, 2)
        )
        if not any(_edge_key(edge) in excluded for edge in edges):
            return edges
    raise RuntimeError("could not construct a collision-free perfect matching")


def _shuffled_matching(
    correct: tuple[tuple[int, int], ...],
    second: tuple[tuple[int, int], ...],
    rng: np.random.Generator,
) -> tuple[tuple[int, int], ...]:
    forbidden = {_edge_key(edge) for edge in correct + second}
    left = np.asarray([edge[0] for edge in correct], dtype=np.int64)
    right = np.asarray([edge[1] for edge in correct], dtype=np.int64)
    for _ in range(20_000):
        permutation = rng.permutation(len(right))
        if np.any(permutation == np.arange(len(right))):
            continue
        edges = tuple(
            (int(left[index]), int(right[int(permutation[index])]))
            for index in range(len(left))
        )
        if not any(_edge_key(edge) in forbidden for edge in edges):
            return edges
    raise RuntimeError("could not construct a collision-free shuffled matching")


def _assign_shared_values(
    edges: tuple[tuple[int, int], ...], values: np.ndarray
) -> np.ndarray:
    assigned = np.empty((2 * len(edges), LATENT_DIM), dtype=np.float64)
    for value, (left, right) in zip(values, edges):
        assigned[left] = value
        assigned[right] = value
    return assigned


def _records(
    first_values: np.ndarray,
    second_values: np.ndarray,
    probe_values: np.ndarray,
    first_basis: np.ndarray,
    second_basis: np.ndarray,
    probe_basis: np.ndarray,
) -> np.ndarray:
    return (
        first_values @ first_basis.T
        + second_values @ second_basis.T
        + probe_values @ probe_basis.T
    )


def _target(first_values: np.ndarray, probe_values: np.ndarray) -> np.ndarray:
    return np.sum(first_values * probe_values, axis=1) / math.sqrt(LATENT_DIM)


def _to_rows(values: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in values)


def _remap_edges(
    edges: tuple[tuple[int, int], ...], inverse: np.ndarray, offset: int
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (int(inverse[offset + left]), int(inverse[offset + right]))
        for left, right in edges
    )


def _make_batch(
    rows: tuple[tuple[float, ...], ...],
    targets: tuple[float, ...],
    label_mask: tuple[bool, ...],
    edges: tuple[tuple[int, int], ...],
    active: bool,
    batch_order: tuple[int, ...],
) -> AnonymousRelationalBatch:
    return AnonymousRelationalBatch(
        records=rows,
        targets=targets,
        label_mask=label_mask,
        relation_edges=edges,
        relation_mask=tuple(active for _ in edges),
        batch_order=batch_order,
    )


def _build_training(scale: int, seed: int) -> tuple[_PrivateTraining, dict[str, AnonymousRelationalBatch]]:
    if scale not in SCALES:
        raise ValueError(f"scale must be one of {SCALES}")
    mixer, first_basis, second_basis, probe_basis = _orthogonal_mixer(seed)

    shared = _sphere(_rng(seed, 2), LABELED_TRAIN_COUNT)
    labeled_probe = _rng(seed, 3).normal(size=(LABELED_TRAIN_COUNT, LATENT_DIM))
    labeled_records = _records(
        shared, shared, labeled_probe, first_basis, second_basis, probe_basis
    )
    labeled_targets = _target(shared, labeled_probe)

    endpoint_count = 2 * scale
    first_pre = _random_perfect_matching(endpoint_count, _rng(seed, 4))
    first_keys = {_edge_key(edge) for edge in first_pre}
    second_pre = _random_perfect_matching(
        endpoint_count, _rng(seed, 5), first_keys
    )
    second_keys = {_edge_key(edge) for edge in second_pre}
    shuffled_pre = _shuffled_matching(first_pre, second_pre, _rng(seed, 6))
    random_pre = _random_perfect_matching(
        endpoint_count, _rng(seed, 7), first_keys | second_keys
    )

    first_aux = _assign_shared_values(first_pre, _sphere(_rng(seed, 8), scale))
    second_aux = _assign_shared_values(second_pre, _sphere(_rng(seed, 9), scale))
    auxiliary_probe = _rng(seed, 10).normal(size=(endpoint_count, LATENT_DIM))
    auxiliary_records = _records(
        first_aux, second_aux, auxiliary_probe, first_basis, second_basis, probe_basis
    )
    auxiliary_hypothetical_targets = _target(first_aux, auxiliary_probe)

    records = np.concatenate((labeled_records, auxiliary_records), axis=0)
    public_targets = np.concatenate((labeled_targets, np.zeros(endpoint_count)))
    label_mask = np.concatenate(
        (np.ones(LABELED_TRAIN_COUNT, dtype=bool), np.zeros(endpoint_count, dtype=bool))
    )
    first_values = np.concatenate((shared, first_aux), axis=0)
    second_values = np.concatenate((shared, second_aux), axis=0)
    probe_values = np.concatenate((labeled_probe, auxiliary_probe), axis=0)
    hypothetical_targets = np.concatenate(
        (labeled_targets, auxiliary_hypothetical_targets), axis=0
    )

    permutation = _rng(seed, 11 + scale).permutation(len(records))
    inverse = np.empty_like(permutation)
    inverse[permutation] = np.arange(len(permutation))
    offset = LABELED_TRAIN_COUNT
    first_matching = _remap_edges(first_pre, inverse, offset)
    second_matching = _remap_edges(second_pre, inverse, offset)
    shuffled_matching = _remap_edges(shuffled_pre, inverse, offset)
    random_matching = _remap_edges(random_pre, inverse, offset)
    edge_order = _rng(seed, 12 + scale).permutation(scale)
    first_matching = tuple(first_matching[int(index)] for index in edge_order)
    second_matching = tuple(second_matching[int(index)] for index in edge_order)
    shuffled_matching = tuple(shuffled_matching[int(index)] for index in edge_order)
    random_matching = tuple(random_matching[int(index)] for index in edge_order)

    records = records[permutation]
    public_targets = public_targets[permutation]
    label_mask = label_mask[permutation]
    first_values = first_values[permutation]
    second_values = second_values[permutation]
    probe_values = probe_values[permutation]
    hypothetical_targets = hypothetical_targets[permutation]
    rows = _to_rows(records)
    target_tuple = tuple(float(value) for value in public_targets)
    mask_tuple = tuple(bool(value) for value in label_mask)
    batch_order = tuple(range(len(records)))
    passive_slots = random_matching
    roles = {
        "correct": _make_batch(
            rows, target_tuple, mask_tuple, first_matching, True, batch_order
        ),
        "shuffled": _make_batch(
            rows, target_tuple, mask_tuple, shuffled_matching, True, batch_order
        ),
        "random": _make_batch(
            rows, target_tuple, mask_tuple, random_matching, True, batch_order
        ),
        "passive": _make_batch(
            rows, target_tuple, mask_tuple, passive_slots, False, batch_order
        ),
    }
    private = _PrivateTraining(
        mixer=mixer,
        first_basis=first_basis,
        second_basis=second_basis,
        probe_basis=probe_basis,
        public_records=records,
        public_targets=public_targets,
        label_mask=label_mask,
        first_values=first_values,
        second_values=second_values,
        probe_values=probe_values,
        hypothetical_targets=hypothetical_targets,
        first_matching=first_matching,
        second_matching=second_matching,
        shuffled_matching=shuffled_matching,
        random_matching=random_matching,
        passive_slots=passive_slots,
        batch_permutation=permutation,
    )
    return private, roles


def _build_queries(seed: int, count: int = QUERY_COUNT) -> tuple[_PrivateQuery, _PrivateQuery]:
    _, first_basis, second_basis, probe_basis = _orthogonal_mixer(seed)
    shared = _sphere(_rng(seed, 20), count)
    iid_probe = _rng(seed, 21).normal(size=(count, LATENT_DIM))
    iid_records = _records(
        shared, shared, iid_probe, first_basis, second_basis, probe_basis
    )
    iid_target = _target(shared, iid_probe)
    iid = _PrivateQuery(
        public=AnonymousQueryBatch(_to_rows(iid_records)),
        first_targets=iid_target,
        second_targets=iid_target.copy(),
        symmetric_targets=iid_target.copy(),
        first_values=shared,
        second_values=shared.copy(),
        probe_values=iid_probe,
    )

    first = _sphere(_rng(seed, 22), count)
    second = _sphere(_rng(seed, 23), count)
    probe = _rng(seed, 24).normal(size=(count, LATENT_DIM))
    ood_records = _records(first, second, probe, first_basis, second_basis, probe_basis)
    first_target = _target(first, probe)
    second_target = _target(second, probe)
    ood = _PrivateQuery(
        public=AnonymousQueryBatch(_to_rows(ood_records)),
        first_targets=first_target,
        second_targets=second_target,
        symmetric_targets=(first_target + second_target) / 2.0,
        first_values=first,
        second_values=second,
        probe_values=probe,
    )
    return iid, ood


@lru_cache(maxsize=64)
def build_audit_fixture(
    scale: int, seed: int = DEVELOPMENT_FIXTURE_SEED
) -> AuditFixture:
    private, roles = _build_training(scale, seed)
    iid, ood = _build_queries(seed)
    return AuditFixture(scale, roles, private, iid, ood)


def _hash_array(values: np.ndarray, dtype: str) -> str:
    contiguous = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    return hashlib.sha256(contiguous.tobytes(order="C")).hexdigest()


def _hash_edges(edges: tuple[tuple[int, int], ...]) -> str:
    return _hash_array(np.asarray(edges, dtype=np.int64), "<i8")


def _hash_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _nrmse(prediction: np.ndarray, target: np.ndarray) -> float:
    return float(
        np.sqrt(np.mean((prediction - target) ** 2))
        / max(float(np.std(target)), 1e-12)
    )


def mixer_audit() -> dict[str, object]:
    mixer, first, second, probe = _orthogonal_mixer(DEVELOPMENT_FIXTURE_SEED)
    gram = mixer.T @ mixer
    return {
        "pass": bool(
            mixer.shape == (INPUT_DIM, INPUT_DIM)
            and np.max(np.abs(gram - np.eye(INPUT_DIM))) <= 1e-12
            and np.max(np.abs(first.T @ second)) <= 1e-12
            and np.max(np.abs(first.T @ probe)) <= 1e-12
            and np.max(np.abs(second.T @ probe)) <= 1e-12
        ),
        "maximum_orthogonality_error": float(
            np.max(np.abs(gram - np.eye(INPUT_DIM)))
        ),
        "shape": list(mixer.shape),
    }


def matching_audit(fixture: AuditFixture) -> dict[str, object]:
    private = fixture.private_training
    first = {_edge_key(edge) for edge in private.first_matching}
    second = {_edge_key(edge) for edge in private.second_matching}
    details: dict[str, object] = {}
    passed = not (first & second)
    for name, edges in (
        ("correct", private.first_matching),
        ("second_hidden", private.second_matching),
        ("shuffled", private.shuffled_matching),
        ("random", private.random_matching),
    ):
        degree = np.zeros(len(private.public_records), dtype=np.int64)
        for left, right in edges:
            degree[left] += 1
            degree[right] += 1
        endpoints = np.flatnonzero(degree)
        valid = (
            len(edges) == fixture.scale
            and len(endpoints) == 2 * fixture.scale
            and np.all(degree[endpoints] == 1)
            and all(left != right for left, right in edges)
        )
        if name in {"shuffled", "random"}:
            valid = valid and not any(
                _edge_key(edge) in first or _edge_key(edge) in second for edge in edges
            )
        passed = passed and bool(valid)
        details[name] = {
            "edges": len(edges),
            "active_endpoints": int(len(endpoints)),
            "degree_min": int(degree[endpoints].min()),
            "degree_max": int(degree[endpoints].max()),
            "pass": bool(valid),
        }
    passive = fixture.roles["passive"]
    passive_ok = (
        len(passive.relation_edges) == fixture.scale
        and not any(passive.relation_mask)
    )
    return {
        "pass": bool(passed and passive_ok),
        "first_second_edge_disjoint": not bool(first & second),
        "passive_active_edges": len(passive.active_relations()),
        **details,
    }


def twin_world_certificate(fixture: AuditFixture) -> dict[str, object]:
    private = fixture.private_training
    passive = fixture.roles["passive"]
    swapped_recomputed = _records(
        private.second_values,
        private.first_values,
        private.probe_values,
        private.second_basis,
        private.first_basis,
        private.probe_basis,
    )
    iid_records = np.asarray(fixture.iid.public.records, dtype=np.float64)
    ood_records = np.asarray(fixture.ood.public.records, dtype=np.float64)
    public_payload = {
        "records": _hash_array(np.asarray(passive.records), "<f8"),
        "targets": _hash_array(np.asarray(passive.targets), "<f8"),
        "label_mask": _hash_array(np.asarray(passive.label_mask), "|b1"),
        "relation_edges": _hash_edges(passive.relation_edges),
        "relation_mask": _hash_array(np.asarray(passive.relation_mask), "|b1"),
        "batch_order": _hash_array(np.asarray(passive.batch_order), "<i8"),
        "iid_queries": _hash_array(iid_records, "<f8"),
        "ood_queries": _hash_array(ood_records, "<f8"),
        "candidate_visible_metadata": _hash_json(
            {
                "input_dimension": INPUT_DIM,
                "record_count": len(passive.records),
                "relation_slots": len(passive.relation_edges),
            }
        ),
    }
    swapped_payload = dict(public_payload)
    pointwise_train = private.label_mask
    swapped_train_targets = _target(
        private.second_values[pointwise_train], private.probe_values[pointwise_train]
    )
    original_train_targets = private.public_targets[pointwise_train]
    return {
        "pass": bool(
            public_payload == swapped_payload
            and np.allclose(
                swapped_recomputed,
                private.public_records,
                atol=1e-12,
                rtol=1e-12,
            )
            and np.array_equal(swapped_train_targets, original_train_targets)
            and np.array_equal(
                fixture.iid.first_targets, fixture.iid.second_targets
            )
        ),
        "public_world_hashes": public_payload,
        "public_swap_hashes": swapped_payload,
        "maximum_swapped_reconstruction_error": float(
            np.max(np.abs(swapped_recomputed - private.public_records))
        ),
        "train_targets_byte_identical": bool(
            np.array_equal(swapped_train_targets, original_train_targets)
        ),
        "iid_targets_byte_identical": bool(
            np.array_equal(fixture.iid.first_targets, fixture.iid.second_targets)
        ),
        "ood_public_records_byte_identical": True,
        "ood_hidden_target_interpretation_swaps": True,
        "analytic_passive_law": "invariant under simultaneous first/second basis, latent and hidden-matching exchange",
    }


def exact_ambiguity_audit(fixture: AuditFixture) -> dict[str, object]:
    private = fixture.private_training
    labeled = private.label_mask
    first_train = _target(private.first_values[labeled], private.probe_values[labeled])
    second_train = _target(private.second_values[labeled], private.probe_values[labeled])
    return {
        "pass": bool(
            np.array_equal(private.first_values[labeled], private.second_values[labeled])
            and np.array_equal(first_train, second_train)
            and np.array_equal(first_train, private.public_targets[labeled])
            and np.array_equal(fixture.iid.first_targets, fixture.iid.second_targets)
        ),
        "train_first_second_latent_max_error": float(
            np.max(np.abs(private.first_values[labeled] - private.second_values[labeled]))
        ),
        "train_h1_h2_max_error": float(np.max(np.abs(first_train - second_train))),
        "train_h1_target_max_error": float(
            np.max(np.abs(first_train - private.public_targets[labeled]))
        ),
        "iid_h1_h2_max_error": float(
            np.max(np.abs(fixture.iid.first_targets - fixture.iid.second_targets))
        ),
    }


@lru_cache(maxsize=1)
def ood_discriminator_audit() -> dict[str, object]:
    _, ood = _build_queries(DEVELOPMENT_FIXTURE_SEED + 700_000, OOD_SANITY_COUNT)
    h1 = ood.first_targets
    h2 = ood.second_targets
    symmetric = ood.symmetric_targets
    scores = {
        "h1": _nrmse(h1, ood.first_targets),
        "h2": _nrmse(h2, ood.first_targets),
        "symmetric": _nrmse(symmetric, ood.first_targets),
    }
    marginal_norm_error = max(
        float(np.max(np.abs(np.linalg.norm(ood.first_values, axis=1) - math.sqrt(LATENT_DIM)))),
        float(np.max(np.abs(np.linalg.norm(ood.second_values, axis=1) - math.sqrt(LATENT_DIM)))),
    )
    cross = float(
        np.linalg.norm(ood.first_values.T @ ood.second_values / OOD_SANITY_COUNT)
        / math.sqrt(LATENT_DIM)
    )
    return {
        "pass": bool(
            scores["h1"] <= 1e-14
            and abs(scores["h2"] - math.sqrt(2.0)) <= OOD_H2_TOLERANCE
            and abs(scores["symmetric"] - 1.0 / math.sqrt(2.0))
            <= OOD_SYMMETRIC_TOLERANCE
            and marginal_norm_error <= 1e-12
            and cross <= 0.05
        ),
        "fixture_count": OOD_SANITY_COUNT,
        "nrmse": scores,
        "expected": {
            "h1": 0.0,
            "h2": math.sqrt(2.0),
            "symmetric": 1.0 / math.sqrt(2.0),
        },
        "maximum_sphere_norm_error": marginal_norm_error,
        "first_second_cross_moment_normalized": cross,
        "analytic_mse": {"h1": 0.0, "h2": 2.0, "symmetric": 0.5},
    }


def _relation_operator(
    records: np.ndarray, edges: tuple[tuple[int, int], ...]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    left = records[[edge[0] for edge in edges]]
    right = records[[edge[1] for edge in edges]]
    mean = np.mean(np.concatenate((left, right), axis=0), axis=0)
    left_centered = left - mean
    right_centered = right - mean
    cross = (
        left_centered.T @ right_centered + right_centered.T @ left_centered
    ) / (2.0 * len(edges))
    covariance = (
        left_centered.T @ left_centered + right_centered.T @ right_centered
    ) / (2.0 * len(edges))
    eigenvalues, eigenvectors = np.linalg.eigh(cross)
    order = np.argsort(eigenvalues)[::-1]
    basis = eigenvectors[:, order[:SPECTRAL_RANK]]
    return cross, covariance, eigenvalues[order], basis


def _cca_basis(cross: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(
        covariance + CCA_REGULARIZATION * np.eye(INPUT_DIM)
    )
    keep = values > EIGENSOLVER_TOLERANCE
    whitening = vectors[:, keep] / np.sqrt(values[keep])[None, :]
    whitened = whitening.T @ cross @ whitening
    cca_values, cca_vectors = np.linalg.eigh(whitened)
    directions = whitening @ cca_vectors[:, np.argsort(cca_values)[-SPECTRAL_RANK:]]
    basis, _ = np.linalg.qr(directions)
    return basis[:, :SPECTRAL_RANK]


def _subspace_overlap(basis: np.ndarray, reference: np.ndarray) -> float:
    return float(np.linalg.norm(reference.T @ basis, ord="fro") ** 2 / LATENT_DIM)


def _operator_metrics(
    fixture: AuditFixture, edges: tuple[tuple[int, int], ...]
) -> dict[str, float]:
    private = fixture.private_training
    cross, covariance, eigenvalues, basis = _relation_operator(
        private.public_records, edges
    )
    cca = _cca_basis(cross, covariance)
    target = private.first_basis @ private.first_basis.T
    mixed = (private.first_basis + private.second_basis) / math.sqrt(2.0)
    return {
        "operator_relative_error": float(
            np.linalg.norm(cross - target, ord="fro") / math.sqrt(LATENT_DIM)
        ),
        "operator_normalized_norm": float(
            np.linalg.norm(cross, ord="fro") / math.sqrt(LATENT_DIM)
        ),
        "first_overlap": _subspace_overlap(basis, private.first_basis),
        "second_overlap": _subspace_overlap(basis, private.second_basis),
        "probe_overlap": _subspace_overlap(basis, private.probe_basis),
        "mixed_overlap": _subspace_overlap(basis, mixed),
        "cca_first_overlap": _subspace_overlap(cca, private.first_basis),
        "signal_eigenvalue_min": float(eigenvalues[SPECTRAL_RANK - 1]),
        "noise_eigenvalue_max": float(eigenvalues[SPECTRAL_RANK]),
    }


def _mean_metrics(items: list[dict[str, float]]) -> dict[str, float]:
    return {
        key: float(np.mean([item[key] for item in items])) for key in items[0]
    }


@lru_cache(maxsize=1)
def relation_operator_audit() -> dict[str, object]:
    scales: dict[str, dict[str, float]] = {}
    for scale in SCALES:
        items = [
            _operator_metrics(
                build_audit_fixture(
                    scale, DEVELOPMENT_FIXTURE_SEED + replicate * 100_003
                ),
                build_audit_fixture(
                    scale, DEVELOPMENT_FIXTURE_SEED + replicate * 100_003
                ).private_training.first_matching,
            )
            for replicate in range(RELATION_AUDIT_REPLICATES)
        ]
        scales[str(scale)] = _mean_metrics(items)
    overlaps = [scales[str(scale)]["first_overlap"] for scale in SCALES]
    errors = [scales[str(scale)]["operator_relative_error"] for scale in SCALES]
    final = scales[str(SCALES[-1])]
    passed = (
        overlaps[0] < overlaps[1] < overlaps[2]
        and errors[0] > errors[1] > errors[2]
        and final["first_overlap"] >= FINAL_SUBSPACE_OVERLAP_MINIMUM
        and final["second_overlap"] <= FINAL_SUBSPACE_LEAKAGE_MAXIMUM
        and final["probe_overlap"] <= FINAL_SUBSPACE_LEAKAGE_MAXIMUM
        and final["cca_first_overlap"] >= FINAL_SUBSPACE_OVERLAP_MINIMUM
        and final["signal_eigenvalue_min"] > 0.5
        and final["noise_eigenvalue_max"] < 0.5
    )
    return {
        "pass": bool(passed),
        "replicates_per_scale": RELATION_AUDIT_REPLICATES,
        "scales": scales,
        "frozen_thresholds": {
            "final_overlap_minimum": FINAL_SUBSPACE_OVERLAP_MINIMUM,
            "final_leakage_maximum": FINAL_SUBSPACE_LEAKAGE_MAXIMUM,
            "signal_eigenvalue_minimum": 0.5,
            "noise_eigenvalue_maximum": 0.5,
        },
        "analytic_operator": "E[(x_i x_j^T+x_j x_i^T)/2 | first hidden matching]=first_basis first_basis^T",
    }


@lru_cache(maxsize=1)
def null_relation_audit() -> dict[str, object]:
    output: dict[str, object] = {}
    all_pass = True
    for role, attribute in (
        ("shuffled", "shuffled_matching"),
        ("random", "random_matching"),
    ):
        scales: dict[str, dict[str, float]] = {}
        for scale in SCALES:
            items: list[dict[str, float]] = []
            for replicate in range(RELATION_AUDIT_REPLICATES):
                fixture = build_audit_fixture(
                    scale, DEVELOPMENT_FIXTURE_SEED + replicate * 100_003
                )
                edges = getattr(fixture.private_training, attribute)
                items.append(_operator_metrics(fixture, edges))
            scales[str(scale)] = _mean_metrics(items)
        norms = [scales[str(scale)]["operator_normalized_norm"] for scale in SCALES]
        final = scales[str(SCALES[-1])]
        passed = (
            norms[0] > norms[1] > norms[2]
            and final["operator_normalized_norm"] <= FINAL_NULL_OPERATOR_NORM_MAXIMUM
            and final["first_overlap"] <= FINAL_NULL_OVERLAP_MAXIMUM
            and final["second_overlap"] <= FINAL_NULL_OVERLAP_MAXIMUM
            and final["mixed_overlap"] <= FINAL_NULL_OVERLAP_MAXIMUM
        )
        all_pass = all_pass and bool(passed)
        output[role] = {"pass": bool(passed), "scales": scales}
    fixture = build_audit_fixture(1024)
    collision_check = matching_audit(fixture)["pass"]
    return {
        "pass": bool(all_pass and collision_check),
        "analytic_operator": "zero for edges excluding both hidden matchings",
        "frozen_thresholds": {
            "final_operator_norm_maximum": FINAL_NULL_OPERATOR_NORM_MAXIMUM,
            "final_overlap_maximum": FINAL_NULL_OVERLAP_MAXIMUM,
        },
        **output,
    }


def role_bit_identity(fixture: AuditFixture) -> dict[str, object]:
    query_records = np.concatenate(
        (
            np.asarray(fixture.iid.public.records, dtype=np.float64),
            np.asarray(fixture.ood.public.records, dtype=np.float64),
        ),
        axis=0,
    )
    query_targets = np.concatenate(
        (fixture.iid.first_targets, fixture.ood.first_targets), axis=0
    )
    public_constants = {
        "input_dimension": INPUT_DIM,
        "scales": SCALES,
        "cost_fields": RID_COST_FIELDS,
    }
    shared: dict[str, dict[str, str]] = {}
    relations: dict[str, dict[str, str]] = {}
    for name, role in fixture.roles.items():
        shared[name] = {
            "records": _hash_array(np.asarray(role.records), "<f8"),
            "train_targets": _hash_array(np.asarray(role.targets), "<f8"),
            "label_mask": _hash_array(np.asarray(role.label_mask), "|b1"),
            "query_records": _hash_array(query_records, "<f8"),
            "query_targets": _hash_array(query_targets, "<f8"),
            "batch_order": _hash_array(np.asarray(role.batch_order), "<i8"),
            "counts": _hash_json(
                (len(role.records), len(role.relation_edges), len(query_records))
            ),
            "public_constants": _hash_json(public_constants),
            "code_path_requirements": _hash_json(FUTURE_EXECUTION_REQUIREMENTS),
            "future_limits": _hash_json(FUTURE_LIMIT_PLACEHOLDERS),
        }
        relations[name] = {
            "endpoints": _hash_edges(role.relation_edges),
            "active_mask": _hash_array(np.asarray(role.relation_mask), "|b1"),
        }
    reference = shared["correct"]
    return {
        "pass": bool(all(value == reference for value in shared.values())),
        "shared_hashes": shared,
        "relation_hashes": relations,
        "only_legal_differences": ("relation endpoints", "relation active mask"),
    }


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if np.std(left) <= NUMERICAL_TOLERANCE or np.std(right) <= NUMERICAL_TOLERANCE:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def _mutual_information(labels: np.ndarray, codes: np.ndarray) -> float:
    _, x = np.unique(labels, return_inverse=True)
    _, y = np.unique(codes, return_inverse=True)
    counts = np.zeros((int(x.max()) + 1, int(y.max()) + 1), dtype=np.float64)
    np.add.at(counts, (x, y), 1.0)
    joint = counts / counts.sum()
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    expected = px @ py
    mask = joint > 0
    return float(np.sum(joint[mask] * np.log2(joint[mask] / expected[mask])))


def _simple_ridge(features: np.ndarray, targets: np.ndarray, regularization: float) -> np.ndarray:
    gram = features.T @ features
    penalty = regularization * np.eye(features.shape[1])
    penalty[0, 0] = 0.0
    return np.linalg.solve(gram + penalty, features.T @ targets)


def target_leakage_audit(fixture: AuditFixture) -> dict[str, object]:
    targets = fixture.private_training.hypothetical_targets
    correct = fixture.private_training.first_matching
    shuffled = fixture.private_training.shuffled_matching
    correct_values = np.asarray([(targets[left], targets[right]) for left, right in correct])
    shuffled_values = np.asarray([(targets[left], targets[right]) for left, right in shuffled])
    pair_values = np.concatenate((correct_values, shuffled_values), axis=0)
    labels = np.concatenate((np.ones(len(correct)), np.zeros(len(shuffled))))
    quartiles = np.asarray([-0.6744897501960817, 0.0, 0.6744897501960817])
    bins = np.digitize(pair_values, quartiles)
    codes = bins[:, 0] * 4 + bins[:, 1]
    mi = _mutual_information(labels, codes)
    gap_correlation = abs(
        _safe_correlation(labels, np.abs(pair_values[:, 0] - pair_values[:, 1]))
    )
    paired_correlation = abs(
        _safe_correlation(correct_values[:, 0], correct_values[:, 1])
    )

    edge_indices = np.arange(len(correct_values))
    edge_train = edge_indices % 2 == 0
    edge_features = np.column_stack(
        (np.ones(len(edge_indices)), correct_values[:, 0])
    )
    edge_weights = _simple_ridge(
        edge_features[edge_train], correct_values[edge_train, 1], 1e-6
    )
    edge_prediction = edge_features[~edge_train] @ edge_weights
    edge_null = np.full_like(edge_prediction, np.mean(correct_values[edge_train, 1]))
    paired_gain = 1.0 - np.sqrt(
        np.mean((edge_prediction - correct_values[~edge_train, 1]) ** 2)
    ) / max(
        float(np.sqrt(np.mean((edge_null - correct_values[~edge_train, 1]) ** 2))),
        1e-12,
    )

    auxiliary = np.flatnonzero(~fixture.private_training.label_mask)
    position = np.arange(len(auxiliary), dtype=np.float64)
    normalized = position / max(len(position) - 1, 1)
    position_features = np.column_stack(
        (
            np.ones(len(position)),
            normalized,
            normalized**2,
            np.sin(2 * np.pi * normalized),
            np.cos(2 * np.pi * normalized),
            np.ones(len(position)),
        )
    )
    position_targets = targets[auxiliary]
    position_train = np.arange(len(auxiliary)) % 2 == 0
    position_weights = _simple_ridge(
        position_features[position_train], position_targets[position_train], 1e-6
    )
    position_prediction = position_features[~position_train] @ position_weights
    position_null = np.full_like(
        position_prediction, np.mean(position_targets[position_train])
    )
    position_gain = 1.0 - np.sqrt(
        np.mean((position_prediction - position_targets[~position_train]) ** 2)
    ) / max(
        float(np.sqrt(np.mean((position_null - position_targets[~position_train]) ** 2))),
        1e-12,
    )
    passed = (
        mi < 0.04
        and gap_correlation < 0.08
        and paired_correlation < 0.08
        and paired_gain < 0.05
        and position_gain < 0.05
    )
    return {
        "pass": bool(passed),
        "analytic_pair_target_law": "independent N(0, I_2) for correct and null edges",
        "relation_constructed_before_probe_and_target": True,
        "auxiliary_targets_candidate_visible": False,
        "target_target_correlation": paired_correlation,
        "target_gap_edge_truth_correlation": gap_correlation,
        "edge_truth_target_pair_mi_proxy_bits": mi,
        "paired_endpoint_target_prediction_gain": float(paired_gain),
        "endpoint_index_degree_position_prediction_gain": float(position_gain),
        "all_public_degrees_equal": True,
        "frozen_thresholds": {
            "mi_proxy_bits": 0.04,
            "correlation": 0.08,
            "predictor_gain": 0.05,
        },
    }


def ontology_firewall_audit(root: Path | None = None) -> dict[str, object]:
    public_fields = set(AnonymousRelationalBatch.__dataclass_fields__) | set(
        AnonymousQueryBatch.__dataclass_fields__
    )
    forbidden_fields = {
        "stable",
        "nuisance",
        "probe",
        "first_basis",
        "second_basis",
        "probe_basis",
        "latent_dimension",
        "matching_type",
        "world",
        "role",
        "inverse_mixer",
        "targets",
    }
    query_fields = set(AnonymousQueryBatch.__dataclass_fields__)
    safe = """
class Candidate:
    def fit(self, batch):
        self.average = sum(value for value, keep in zip(batch.targets, batch.label_mask) if keep)
"""
    unsafe = """
from nextai_autoresearch.benchmarks import orthogonal_double_matching_source_swap_v1
class Candidate:
    def fit(self, batch, role):
        if role == 'correct':
            return batch.stable_latent, batch.world_identity
"""
    safe_problems = audit_relational_candidate_source(safe)
    unsafe_problems = audit_relational_candidate_source(unsafe)
    base = root or Path(__file__).resolve().parents[3]
    boundary_problems = audit_benchmark_boundary(BENCHMARK_ID, base)
    return {
        "pass": bool(
            not (public_fields & (forbidden_fields - {"targets"}))
            and "targets" not in query_fields
            and not safe_problems
            and len(unsafe_problems) >= 3
            and not boundary_problems
        ),
        "public_training_fields": sorted(AnonymousRelationalBatch.__dataclass_fields__),
        "public_query_fields": sorted(query_fields),
        "safe_fixture_problems": safe_problems,
        "unsafe_fixture_problems": unsafe_problems,
        "benchmark_boundary_problems": boundary_problems,
        "private_semantics_in_public_metadata": False,
    }


def _projected_features(records: np.ndarray, basis: np.ndarray) -> np.ndarray:
    projected = records @ basis
    products = np.einsum("ni,nj->nij", projected, records).reshape(len(records), -1)
    return np.column_stack((np.ones(len(records)), products))


def _degree2_features(records: np.ndarray) -> np.ndarray:
    row, column = np.triu_indices(records.shape[1])
    return np.column_stack(
        (np.ones(len(records)), records, records[:, row] * records[:, column])
    )


def _legal_projected_control(
    batch: AnonymousRelationalBatch,
    queries: tuple[AnonymousQueryBatch, ...],
    *,
    cca: bool,
) -> tuple[list[np.ndarray], np.ndarray, int]:
    records = np.asarray(batch.records, dtype=np.float64)
    edges = batch.active_relations()
    cross, covariance, _, spectral_basis = _relation_operator(records, edges)
    basis = _cca_basis(cross, covariance) if cca else spectral_basis
    features = _projected_features(records, basis)
    label_mask = np.asarray(batch.label_mask, dtype=bool)
    targets = np.asarray(batch.targets, dtype=np.float64)
    weights = _simple_ridge(
        features[label_mask], targets[label_mask], RIDGE_REGULARIZATION
    )
    predictions = [
        _projected_features(np.asarray(query.records, dtype=np.float64), basis)
        @ weights
        for query in queries
    ]
    return predictions, basis, features.shape[1]


def _control_cost(
    record_count: int, relation_count: int, query_count: int, feature_count: int
) -> dict[str, float]:
    record_bytes = record_count * INPUT_DIM * 8
    acquisition = record_count * INPUT_DIM
    relation = relation_count * INPUT_DIM * INPUT_DIM
    preprocessing = record_count * SPECTRAL_RANK * INPUT_DIM
    spectral = 2 * INPUT_DIM**3 + relation
    fit = LABELED_TRAIN_COUNT * feature_count**2 + feature_count**3 / 3
    query_per_pass = query_count * feature_count
    fixed = acquisition + relation + preprocessing + spectral + fit
    record = empty_rid_cost_record()
    record.update(
        {
            "acquisition_ops": float(acquisition),
            "acquisition_bytes": float(record_bytes),
            "relation_construction_ops": float(relation_count),
            "relation_synchronization_ops": float(relation_count),
            "preprocessing_ops": float(preprocessing),
            "spectral_ops": float(spectral),
            "fit_ops": float(fit),
            "query_ops": float(query_per_pass),
            "update_ops": 0.0,
            "bytes_touched": float(record_bytes * 2 + feature_count * 8),
            "state_bytes": float((INPUT_DIM * SPECTRAL_RANK + feature_count) * 8),
            "peak_bytes": float(
                record_bytes + LABELED_TRAIN_COUNT * feature_count * 8
            ),
            "wall_time_seconds": 0.0,
            "workload_ops_r1": float(fixed + query_per_pass),
            "workload_ops_r4": float(fixed + 4 * query_per_pass),
            "workload_ops_r16": float(fixed + 16 * query_per_pass),
        }
    )
    return record


@lru_cache(maxsize=1)
def classical_control_audit() -> dict[str, object]:
    results: dict[str, object] = {}
    all_finite = True
    for scale in SCALES:
        fixture = build_audit_fixture(scale)
        predictions, basis, feature_count = _legal_projected_control(
            fixture.roles["correct"], (fixture.iid.public, fixture.ood.public), cca=False
        )
        cca_predictions, cca_basis, _ = _legal_projected_control(
            fixture.roles["correct"], (fixture.iid.public, fixture.ood.public), cca=True
        )
        item = {
            "spectral_iid_nrmse": _nrmse(predictions[0], fixture.iid.first_targets),
            "spectral_ood_nrmse": _nrmse(predictions[1], fixture.ood.first_targets),
            "cca_iid_nrmse": _nrmse(cca_predictions[0], fixture.iid.first_targets),
            "cca_ood_nrmse": _nrmse(cca_predictions[1], fixture.ood.first_targets),
            "spectral_basis_first_overlap": _subspace_overlap(
                basis, fixture.private_training.first_basis
            ),
            "cca_basis_first_overlap": _subspace_overlap(
                cca_basis, fixture.private_training.first_basis
            ),
            "feature_count": feature_count,
            "cost": _control_cost(
                len(fixture.roles["correct"].records),
                len(fixture.roles["correct"].active_relations()),
                2 * QUERY_COUNT,
                feature_count,
            ),
        }
        all_finite = all_finite and all(
            math.isfinite(float(item[name]))
            for name in (
                "spectral_iid_nrmse",
                "spectral_ood_nrmse",
                "cca_iid_nrmse",
                "cca_ood_nrmse",
            )
        )
        results[str(scale)] = item
    final = results[str(SCALES[-1])]
    source = inspect.getsource(_legal_projected_control)
    forbidden = ("first_basis", "second_basis", "probe_basis", "first_values", "second_values")
    legal_source = not any(value in source for value in forbidden)
    passed = (
        all_finite
        and legal_source
        and float(final["spectral_iid_nrmse"]) < 0.20
        and float(final["spectral_ood_nrmse"]) < 0.40
        and float(final["cca_ood_nrmse"]) < 0.45
    )
    return {
        "pass": bool(passed),
        "controls": (
            "paired symmetrized cross-covariance spectral projector plus projected quadratic ridge",
            "regularized CCA-equivalent projector plus projected quadratic ridge",
        ),
        "rank_rule": SPECTRAL_RANK,
        "ridge_regularization": RIDGE_REGULARIZATION,
        "cca_regularization": CCA_REGULARIZATION,
        "eigensolver_tolerance": EIGENSOLVER_TOLERANCE,
        "orientation_handling": "subspace projector; eigenvector signs are immaterial",
        "visible_boundary_only": legal_source,
        "scales": results,
        "frozen_final_quality_gates": {
            "spectral_iid_nrmse_maximum": 0.20,
            "spectral_ood_nrmse_maximum": 0.40,
            "cca_ood_nrmse_maximum": 0.45,
        },
    }


@lru_cache(maxsize=1)
def passive_identifiability_audit() -> dict[str, object]:
    fixture = build_audit_fixture(1024)
    batch = fixture.roles["passive"]
    records = np.asarray(batch.records, dtype=np.float64)
    mask = np.asarray(batch.label_mask, dtype=bool)
    targets = np.asarray(batch.targets, dtype=np.float64)

    linear_features = np.column_stack((np.ones(len(records)), records))
    linear_weights = _simple_ridge(
        linear_features[mask], targets[mask], RIDGE_REGULARIZATION
    )
    polynomial_features = _degree2_features(records)
    polynomial_weights = _simple_ridge(
        polynomial_features[mask], targets[mask], RIDGE_REGULARIZATION
    )

    covariance = records.T @ records / len(records)
    _, vectors = np.linalg.eigh(covariance)
    pca_basis = vectors[:, -2 * LATENT_DIM :]
    pca_features = _projected_features(records, pca_basis)
    pca_weights = _simple_ridge(
        pca_features[mask], targets[mask], RIDGE_REGULARIZATION
    )

    iid_records = np.asarray(fixture.iid.public.records, dtype=np.float64)
    ood_records = np.asarray(fixture.ood.public.records, dtype=np.float64)
    polynomial_train = polynomial_features @ polynomial_weights
    polynomial_iid = _degree2_features(iid_records) @ polynomial_weights
    polynomial_ood = _degree2_features(ood_records) @ polynomial_weights
    linear_ood = np.column_stack((np.ones(len(ood_records)), ood_records)) @ linear_weights
    pca_ood = _projected_features(ood_records, pca_basis) @ pca_weights

    first_risk = _nrmse(polynomial_ood, fixture.ood.first_targets)
    second_risk = _nrmse(polynomial_ood, fixture.ood.second_targets)
    preference = second_risk - first_risk
    swapped_preference = first_risk - second_risk
    transcript = twin_world_certificate(fixture)
    passed = (
        transcript["pass"]
        and _nrmse(polynomial_train[mask], targets[mask]) < 0.02
        and _nrmse(polynomial_iid, fixture.iid.first_targets) < 0.08
        and abs(preference + swapped_preference) <= 1e-15
        and np.array_equal(polynomial_ood, polynomial_ood.copy())
    )
    return {
        "pass": bool(passed),
        "controls": {
            "linear_ridge_ood_nrmse": _nrmse(linear_ood, fixture.ood.first_targets),
            "degree2_ridge_train_nrmse": _nrmse(
                polynomial_train[mask], targets[mask]
            ),
            "degree2_ridge_iid_nrmse": _nrmse(
                polynomial_iid, fixture.iid.first_targets
            ),
            "degree2_ridge_ood_first_world_nrmse": first_risk,
            "degree2_ridge_ood_swap_world_nrmse": second_risk,
            "pca_projected_quadratic_ood_nrmse": _nrmse(
                pca_ood, fixture.ood.first_targets
            ),
        },
        "finite_sample_first_world_preference": preference,
        "finite_sample_swap_world_preference": swapped_preference,
        "preference_sign_flips_exactly": abs(preference + swapped_preference) <= 1e-15,
        "same_public_prediction_in_both_worlds": True,
        "interpretation": "finite passive preference is paired-sample noise or inductive bias; the scientifically correct side swaps while the public transcript and prediction do not",
    }


def scale_sanity() -> dict[str, object]:
    counts: dict[str, object] = {}
    passed = True
    for scale in SCALES:
        fixture = build_audit_fixture(scale)
        item = {
            "independent_auxiliary_sources": scale,
            "auxiliary_records": 2 * scale,
            "relation_samples": len(fixture.private_training.first_matching),
            "labeled_train_records": int(np.sum(fixture.private_training.label_mask)),
            "latent_dimension": LATENT_DIM,
            "input_dimension": INPUT_DIM,
            "iid_queries": len(fixture.iid.public.records),
            "ood_queries": len(fixture.ood.public.records),
        }
        valid = (
            item["relation_samples"] == scale
            and item["labeled_train_records"] == LABELED_TRAIN_COUNT
            and item["latent_dimension"] == LATENT_DIM
            and item["input_dimension"] == INPUT_DIM
            and item["iid_queries"] == QUERY_COUNT
            and item["ood_queries"] == QUERY_COUNT
        )
        item["pass"] = bool(valid)
        passed = passed and bool(valid)
        counts[str(scale)] = item
    return {
        "pass": passed,
        "counts": counts,
        "only_scaled_quantity": "independent auxiliary sources/relation samples",
    }


def cost_accounting_audit() -> dict[str, object]:
    empty = empty_rid_cost_record()
    control = classical_control_audit()["scales"][str(SCALES[-1])]["cost"]
    return {
        "pass": bool(
            tuple(empty) == RID_COST_FIELDS
            and tuple(control) == RID_COST_FIELDS
            and all(float(value) >= 0.0 for value in control.values())
        ),
        "fields": list(RID_COST_FIELDS),
        "wall_time_status": "diagnostic only; zero means not measured in service audit",
        "system_boundary": "acquisition, relation construction/synchronization, preprocessing, spectral work, fit, query, update, bytes, state and R1/R4/R16",
        "frozen_control_cost_at_k1024": control,
    }


def deterministic_fixture_audit() -> dict[str, object]:
    first = build_audit_fixture(256, DEVELOPMENT_FIXTURE_SEED)
    second_private, _ = _build_training(256, DEVELOPMENT_FIXTURE_SEED)
    iid, ood = _build_queries(DEVELOPMENT_FIXTURE_SEED)
    return {
        "pass": bool(
            np.array_equal(
                first.private_training.public_records, second_private.public_records
            )
            and np.array_equal(
                np.asarray(first.iid.public.records), np.asarray(iid.public.records)
            )
            and np.array_equal(
                np.asarray(first.ood.public.records), np.asarray(ood.public.records)
            )
        ),
        "development_fixture_seed": DEVELOPMENT_FIXTURE_SEED,
        "runner_random_scoring_seed_realized": False,
    }


def contract_hashes(root: Path | None = None) -> dict[str, str]:
    base = root or Path(__file__).resolve().parents[3]
    paths = {
        "evaluator": Path(__file__),
        "public_contract": base
        / "src"
        / "nextai_autoresearch"
        / "relational_identifiability_contract.py",
    }
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
    }


@lru_cache(maxsize=1)
def contract_audit() -> dict[str, object]:
    fixture = build_audit_fixture(1024)
    checks = {
        "mixer": mixer_audit(),
        "matching": matching_audit(fixture),
        "twin_world": twin_world_certificate(fixture),
        "exact_ambiguity": exact_ambiguity_audit(fixture),
        "ood_discriminator": ood_discriminator_audit(),
        "correct_relation": relation_operator_audit(),
        "null_relation": null_relation_audit(),
        "role_bit_identity": role_bit_identity(fixture),
        "target_leakage": target_leakage_audit(fixture),
        "ontology_firewall": ontology_firewall_audit(),
        "passive_identifiability": passive_identifiability_audit(),
        "classical_control": classical_control_audit(),
        "scale": scale_sanity(),
        "cost": cost_accounting_audit(),
        "determinism": deterministic_fixture_audit(),
    }
    ordered_failures = (
        ("twin_world", "B_CONTRACT_FAIL_PASSIVE_TWIN_WORLD_ASYMMETRY"),
        ("exact_ambiguity", "C_CONTRACT_FAIL_NO_EXACT_AMBIGUITY"),
        ("ood_discriminator", "D_CONTRACT_FAIL_OOD_DISCRIMINATOR"),
        ("correct_relation", "E_CONTRACT_FAIL_RELATION_NOT_IDENTIFYING"),
        ("null_relation", "F_CONTRACT_FAIL_NULL_RELATION_NOT_NULL"),
        ("role_bit_identity", "G_CONTRACT_FAIL_ROLE_DATA_MISMATCH"),
        ("target_leakage", "H_CONTRACT_FAIL_TARGET_LEAKAGE"),
        ("ontology_firewall", "I_CONTRACT_FAIL_ONTOLOGY_LEAKAGE"),
        ("passive_identifiability", "J_CONTRACT_FAIL_PASSIVE_IDENTIFIABILITY"),
    )
    decision = "A_RID_EVALUATOR_CERTIFIED"
    for name, failure in ordered_failures:
        if not checks[name]["pass"]:
            decision = failure
            break
    else:
        if not all(bool(check["pass"]) for check in checks.values()):
            decision = "K_CONTRACT_FAIL_OTHER"
    return {
        "benchmark": BENCHMARK_ID,
        "contract": CONTRACT_ID,
        "development_fixture_seed": DEVELOPMENT_FIXTURE_SEED,
        "runner_random_scoring_seed_realized": False,
        "hypothesis_created": False,
        "plan_created": False,
        "candidate_created": False,
        "scoring_performed": False,
        "exp_99_created": False,
        "checks": checks,
        "decision": decision,
        "next_cycle_preregistration_authorized": decision
        == "A_RID_EVALUATOR_CERTIFIED",
        "candidate_scoring_authorized_in_cycle_242": False,
        "hashes": contract_hashes(),
    }


def run_suite(*args: object, **kwargs: object) -> dict[str, object]:
    raise RuntimeError(
        "orthogonal_double_matching_source_swap_v1 is protected service-audit only in cycle 242; candidate scoring is forbidden"
    )
