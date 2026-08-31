from __future__ import annotations

import hashlib
import math
import random
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..masked_refinement_contract import (
    MASK, ByteFile, MaskedQuery, MaskedTraining, PrivilegedMaskedQuery,
)
from ..utils import project_root


BENCHMARK_VERSION = "heldout_parallel_masked_infilling_v1"
CONTEXT = 64
PRIVILEGED = {"oracle_conditional_masked_byte"}
CORPUS = (
    ("train", "src/nextai_autoresearch/benchmarks/action_conditioned_predictive_equivalence_v1.py", 10246, "502653ab333cd438d02a14b6798740dd6971238e17d5cb0a64768179a06085dc"),
    ("train", "src/nextai_autoresearch/benchmarks/active_information_acquisition_v1.py", 8167, "37383f289fe7482dc74253abdabc330da434de4655044157a9db7cfca1b1005a"),
    ("train", "src/nextai_autoresearch/benchmarks/adaptive_depth_v1.py", 4166, "680742fc572e3aabae7531fc972215fa6a7fc97b3cab9f212f5f632733ef65f5"),
    ("train", "src/nextai_autoresearch/benchmarks/ambiguous_cross_task_energy_transfer_v1.py", 8344, "82be3693be9ce13c7e53bc03c83d45791ca0595126b7d3cd3a4675797af8911e"),
    ("train", "src/nextai_autoresearch/benchmarks/asynchronous_temporal_binding_v1.py", 9365, "78a533cf6341ac79060b9989130a61b9464556197b0b907e4f4824ca65290f9f"),
    ("train", "src/nextai_autoresearch/benchmarks/cellular_propagation_v1.py", 6370, "19adf10d2460849c120cfa6ff31417d28fabd1cf68b37b190469214630d1a34e"),
    ("train", "src/nextai_autoresearch/benchmarks/context_specific_probabilistic_circuit_v1.py", 11809, "4bca212cdabaa813ad77fb529f679c967e9eb050982ffa77f7faffa6cccf9b3d"),
    ("train", "src/nextai_autoresearch/benchmarks/continuous_event_predictive_state_v1.py", 10483, "b5b1d46a5c6e9cb0688cb8735c786eb7476d54e41ebc04517888d9d84f904865"),
    ("train", "src/nextai_autoresearch/benchmarks/heterogeneous_module_composition_v1.py", 6551, "10150864716119b381f8f7f6dfd94d07ac588d12c60ce59ffcab771502430738"),
    ("train", "src/nextai_autoresearch/benchmarks/latent_causal_transfer_adversarial_v2.py", 12316, "a2065c848742720aa98c63d5826b08ca36c8fcc7ec3e0db387aa63b6ede69ddc"),
    ("train", "src/nextai_autoresearch/benchmarks/latent_causal_transfer_v1.py", 10002, "b85553423205e5b7ad453d4a7017b557a26edf2365f1af3ea020aca8c060b109"),
    ("train", "src/nextai_autoresearch/benchmarks/noisy_nonexhaustive_causal_transfer_v3.py", 9259, "1ef3be0366d28df1c7f917261a973a31295042f05a1817ed43b97d6d93b4014a"),
    ("train", "src/nextai_autoresearch/benchmarks/pointer_machine_composition_v1.py", 8515, "72c25890e6104b942c3b2b83b00c91d1e832f4c21e3e52997a360a54509f08e7"),
    ("train", "src/nextai_autoresearch/benchmarks/program_library_identifiable_v3.py", 5212, "4c3e305c815dee84746725f73bc3c622ec421ef501d023ac1fa4e950dbf6b3ae"),
    ("train", "src/nextai_autoresearch/benchmarks/program_library_v1.py", 5598, "ac0b2fee20189843d659b2ecc9149b27853b392b7807380c3eabd38d1e1a8ffb"),
    ("train", "src/nextai_autoresearch/benchmarks/raw_byte_motif_composition_v1.py", 10174, "38d4c68818c1c8820bdaab5a76a5a88eb05ee443897558e9c26a6facf50b18ca"),
    ("train", "src/nextai_autoresearch/benchmarks/routed_vsa_capacity_scaling_v2.py", 5867, "8d248e7a28402e80c1d28711a20e71f07615ce2af8e48251d02cfbccf7653305"),
    ("train", "src/nextai_autoresearch/benchmarks/semantic_trace_compilation_v1.py", 8396, "a6c6de425151fdf6d448685472b1ce4dfbf6b5e12c008fffe17895dc4376697c"),
    ("train", "src/nextai_autoresearch/benchmarks/successor_graph_v1.py", 6298, "40ca861de2dfacafefc9b22e6e19a13bdf7cb657451adf56be0d7687a12f5df2"),
    ("train", "tests/test_active_information_acquisition.py", 2204, "665a9c748ef2c2df1024a6bc3593051429cdec54f3dcfadbc85104ac7dba7ae1"),
    ("train", "tests/test_ambiguous_cross_task_energy_transfer.py", 2146, "afb609da8f0c50a61248dada7360129faa144d4ec9443e992303f2a0f4380bb4"),
    ("train", "tests/test_associative_relational_relaxation.py", 2603, "03f6ae6dbb9c43632a36dc832222c656c7b1c2f3d97a064cea04589f816e2a8a"),
    ("train", "tests/test_associative_relational_relaxation_adversarial.py", 3023, "b8dd256e12d72a34d60555234fcad39c40c862f83bc02a84f6ee624bcca78867"),
    ("train", "tests/test_asynchronous_temporal_binding.py", 2616, "05f53c9df2adcb39de282e5cf010cacd5ba64f9e46d91813847379535cd457bf"),
    ("train", "tests/test_causal_intervention_adversarial.py", 2024, "66334e3d97c3611cf06d44a56eb9fa3b10d80a435b820e15ef99e5a0bd06a87d"),
    ("train", "tests/test_context_specific_probabilistic_circuit.py", 2929, "4809c7702e4bb663a60af741e17d9c89af622478a9d2b083e83750ee40ca3296"),
    ("train", "tests/test_cross_family_contract.py", 4137, "9248436690d8cf6c2546696b515c9f451d5eb6b5ea371d8f0ebe68ed41aa1965"),
    ("train", "tests/test_cross_family_transfer_v2.py", 2451, "4c739c1c0024a010b4ca2163f946bbacddb19a81d300de54d900f142344237bd"),
    ("train", "tests/test_failure_controls.py", 3406, "b91d7d78534bfbef15d07ec8dc45c88e15d83a1ebdf19e72d792bcfa615231b5"),
    ("train", "tests/test_integrity_and_schemas.py", 4458, "02f1a7d1941740687386928e86a4ce3cb931d2cafddd97b06c4efa9daa68fd6a"),
    ("train", "tests/test_metrics_and_pareto.py", 4143, "c881ec7c606b4eaf024ae6bf3fc12bf4348fc45a0d152070f153822aa45ba854"),
    ("train", "tests/test_nonstationary_online_update.py", 5923, "ac8efecc22ea8d13c1e75f365bce362d679b0f234fd2fd96dcf4a6a14b39dbab"),
    ("train", "tests/test_raw_byte_motif_composition.py", 2725, "22d6b385d34ec784888e7f5ec9b76690ba3814dd42e0f15f66f876ac8aec670f"),
    ("train", "tests/test_semantic_trace_compilation.py", 2126, "15726a636ea79ec248a08ce90084539ca086a53e83e5149a8cd1859376451bcf"),
    ("train", "tests/test_shared_transition_adaptive_compute.py", 2334, "3312e5aa7e757617ec7f890705ae7d5d0fad2c0cc7ab74763822837e2c622636"),
    ("validation", "src/nextai_autoresearch/benchmarks/associative_relational_relaxation_v1.py", 7527, "1be82afbf03f53bedcb4c6e5b572e3d40af0b763d8e05f18fd3dc524aadfa850"),
    ("validation", "src/nextai_autoresearch/benchmarks/cross_family_shared_representation_v1.py", 13773, "891c143fcbcf8847cb183fb0c5dba0a64afbc227a3d3c4a3e896490f03d2ad4f"),
    ("validation", "src/nextai_autoresearch/benchmarks/opaque_alias_acquisition_v1.py", 12946, "89a9b9a98696148c95d45b6bb942aaa6965a5ee0c35b036e838d6ab50745db34"),
    ("validation", "src/nextai_autoresearch/benchmarks/shared_transition_adaptive_compute_v2.py", 7226, "7f299a1a80cabc8fcd380baa443d3380f7ab192d378a6d73eca4942414c33168"),
    ("test", "src/nextai_autoresearch/benchmarks/behavioral_conjugacy_library_transfer_v1.py", 9635, "94eb80698cdad77d16fa0c67a096eef4cb54c099c93703a71c9196cd1eff4e51"),
    ("test", "src/nextai_autoresearch/benchmarks/latent_entity_binding_retrieval_v1.py", 7283, "4e3c8c810d33e9a4dbe7d98fba253f2689637827d8befb52ed2020fcd4b08ac7"),
    ("test", "src/nextai_autoresearch/benchmarks/nonlinear_local_state_transfer_v1.py", 6843, "1c0d0c81c0278aee5fd24d93cf0bfe4cdacdf9b980dab24b3b13f0902697dce4"),
    ("test", "src/nextai_autoresearch/benchmarks/nonstationary_online_update_battery_v1.py", 11049, "3a602152211b95201282c3201864c45ca68aee25d4437e761687ae655a8c2c72"),
    ("test", "src/nextai_autoresearch/benchmarks/semantic_trace_compilation_adversarial_v2.py", 11860, "80a4fc94726f3042489e109f9a2778a503d4d1a4ca69a8d06e308818b75cadaf"),
    ("test", "tests/test_heterogeneous_module_composition.py", 2648, "6d01c2d92d0d3df39af55a406d88a64fdf7c4b27428c8ba4290a9241102be01d"),
    ("test", "tests/test_noisy_nonexhaustive_causal_transfer.py", 2348, "0815b785b6117d1bc6dbf07826f797abd82004b3094c5474ca86b1c61015645e"),
    ("test", "tests/test_semantic_reaction_composition.py", 3257, "a9d73e5a9c446d4642daabe5def64658ee8bd7d7cd9ddc605f651b0a9b93d4d0"),
    ("test", "tests/test_semantic_trace_compilation_adversarial.py", 2433, "8a46ea5df4d1d39b8e66920ea29c94a61630407a0bb7f08fe490dce7ddd2521e"),
)


def _load_corpus(root: Path | None = None):
    roles = {"train": [], "validation": [], "test": []}
    acquisition = 0
    for role, relative, size, digest in CORPUS:
        data = ((root or project_root()) / relative).read_bytes()
        acquisition += len(data)
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"immutable corpus mismatch: {relative}")
        roles[role].append((relative, data))
    return roles, acquisition


def _allocate(files, budget: int, slots: list[int], permutation: tuple[int, ...]):
    remaining, offsets = budget, [0] * len(files)
    chunks = [bytearray() for _ in files]
    while remaining and any(offset < len(item[1]) for offset, item in zip(offsets, files)):
        for index, (_, data) in enumerate(files):
            if not remaining:
                break
            take = min(128, remaining, len(data) - offsets[index])
            chunks[index].extend(permutation[value] for value in data[offsets[index]:offsets[index] + take])
            offsets[index] += take
            remaining -= take
    return tuple(ByteFile(slot, tuple(data)) for slot, data in zip(slots, chunks) if data)


def make_training(knowledge_size: int, seed: int):
    roles, acquisition = _load_corpus()
    rng = random.Random(seed ^ 0x5A17ED)
    permutation = list(range(256))
    rng.shuffle(permutation)
    permutation = tuple(permutation)
    slots = rng.sample(range(10_000, 99_999), len(roles["train"]) + len(roles["validation"]))
    train = _allocate(roles["train"], knowledge_size * 1024,
                      slots[:len(roles["train"])], permutation)
    validation = _allocate(roles["validation"], min(4096, knowledge_size * 128),
                           slots[len(roles["train"]):], permutation)
    tests = [(relative, bytes(permutation[value] for value in data))
             for relative, data in roles["test"]]
    selected = sum(len(item.data) for item in train + validation)
    return MaskedTraining(train, validation, 2 * acquisition + selected), tests


def _number(candidate: Any, name: str, default: float = 0.0) -> float:
    value = getattr(candidate, name, default)
    return float(value() if callable(value) else value)


def _distributions(value: Any, count: int) -> tuple[tuple[float, ...], ...]:
    if not isinstance(value, (tuple, list)) or len(value) != count:
        raise ValueError("candidate must return one distribution per masked position")
    output = []
    for row in value:
        if not isinstance(row, (tuple, list)) or len(row) != 256:
            raise ValueError("each masked-position prediction must have 256 probabilities")
        probabilities = tuple(float(item) for item in row)
        total = sum(probabilities)
        if any(not math.isfinite(item) or item < 0 for item in probabilities) or total <= 0:
            raise ValueError("invalid byte distribution")
        output.append(tuple(item / total for item in probabilities))
    return tuple(output)


def _cases(tests, span: int, count: int, seed: int):
    rng = random.Random(seed ^ (span << 12))
    order = list(range(len(tests)))
    rng.shuffle(order)
    slots = rng.sample(range(100, 9_999), len(tests))
    cases = []
    for index in range(count):
        file_index = order[index % len(order)]
        _, data = tests[file_index]
        offset = rng.randrange(CONTEXT, len(data) - span - CONTEXT + 1)
        segment = data[offset - CONTEXT:offset + span + CONTEXT]
        positions = tuple(range(CONTEXT, CONTEXT + span))
        target = tuple(segment[position] for position in positions)
        snapshot = tuple(MASK if position in positions else value
                         for position, value in enumerate(segment))
        cases.append((slots[file_index], snapshot, positions, target))
    return cases


def _run_case(candidate: Any, candidate_name: str, case, rounds: int):
    slot, initial, positions, target = case
    truth = dict(zip(positions, target))
    snapshot, remaining = list(initial), list(positions)
    losses, correct, latency = [], 0, []
    query_ops = bytes_touched = critical = probabilities_count = 0.0
    for round_index in range(rounds):
        public = MaskedQuery(slot, tuple(snapshot), tuple(remaining), round_index, rounds)
        source = PrivilegedMaskedQuery(public, target) if candidate_name in PRIVILEGED else public
        tick = time.perf_counter_ns()
        distributions = _distributions(candidate.query(source, rounds), len(remaining))
        latency.append((time.perf_counter_ns() - tick) / 1000.0)
        candidate_ops = _number(candidate, "last_ops")
        query_ops += candidate_ops + len(remaining) * 256
        bytes_touched += _number(candidate, "last_bytes_touched", candidate_ops * 8)
        critical += (max(1.0, _number(candidate, "last_critical_path_steps", 1.0))
                     + math.ceil(math.log2(max(2, len(remaining)))) + 1)
        probabilities_count += len(remaining) * 256
        ranked = sorted(range(len(remaining)),
                        key=lambda i: max(distributions[i]), reverse=True)
        take = math.ceil(len(remaining) / (rounds - round_index))
        selected = set(ranked[:take])
        query_ops += len(remaining) * math.log2(max(2, len(remaining))) + take * 256
        next_remaining = []
        for index, position in enumerate(remaining):
            if index not in selected:
                next_remaining.append(position)
                continue
            distribution = distributions[index]
            prediction = max(range(256), key=distribution.__getitem__)
            probability = max(1e-12, distribution[truth[position]])
            losses.append(-math.log2(probability))
            correct += prediction == truth[position]
            snapshot[position] = prediction
        remaining = next_remaining
    return {
        "bits": statistics.fmean(losses), "accuracy": correct / len(positions),
        "exact": float(all(snapshot[position] == truth[position] for position in positions)),
        "query_ops": query_ops, "bytes": bytes_touched, "critical": critical,
        "probabilities": probabilities_count, "latency": latency,
        "input_ops": len(initial) * rounds,
    }


def _run_cell(candidate_name: str, size: int, rounds: int, count: int, seed: int,
              maximum_rounds: int, protocol: dict[str, Any]):
    training, tests = make_training(size, seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, maximum_rounds)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    state = _number(candidate, "state_bytes")
    if state > int(protocol["state_budget_bytes"]):
        raise ValueError("state budget exceeded")

    by_span, all_cases = {}, []
    effective_rounds = 1 if candidate_name == "one_pass_masked_learner" else rounds
    for span in protocol["span_lengths"]:
        observations = [_run_case(candidate, candidate_name, case, effective_rounds)
                        for case in _cases(tests, int(span), count, seed)]
        by_span[int(span)] = observations
        all_cases.extend(observations)
    query_ops = sum(row["query_ops"] for row in all_cases)
    fit_ops = _number(candidate, "fit_ops")
    meta_fit_ops = _number(candidate, "meta_fit_ops", fit_ops)
    base = training.acquisition_ops + fit_ops
    workloads = {horizon: base + horizon * query_ops for horizon in (1, 4, 16)}
    latencies = [value for row in all_cases for value in row["latency"]]
    rows = []
    for span, observations in by_span.items():
        rows.append({
            "status": "complete", "world_family": f"span_{span}",
            "span_length": span, "knowledge_size": size,
            "reasoning_depth": rounds, "refinement_rounds": effective_rounds,
            "seed": seed, "query_count": count * span,
            "accuracy": statistics.fmean(row["accuracy"] for row in observations),
            "warm_accuracy": statistics.fmean(row["accuracy"] for row in observations),
            "continual_retention": statistics.fmean(row["exact"] for row in observations),
            "exact_span_accuracy": statistics.fmean(row["exact"] for row in observations),
            "bits_per_byte": statistics.fmean(row["bits"] for row in observations),
            "critical_path_steps": max(row["critical"] for row in observations),
            "total_position_probabilities": sum(row["probabilities"] for row in observations),
            "fit_seconds": fit_seconds, "fit_ops": fit_ops,
            "meta_fit_ops": meta_fit_ops,
            "data_acquisition_ops": float(training.acquisition_ops),
            "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": query_ops / (count * sum(protocol["span_lengths"])),
            "mean_warm_query_ops": query_ops / (count * sum(protocol["span_lengths"])),
            "mean_input_ops": statistics.fmean(row["input_ops"] for row in observations),
            "mean_bytes_touched": statistics.fmean(row["bytes"] for row in observations),
            "p50_latency_us": percentile(latencies, 0.5),
            "p95_latency_us": percentile(latencies, 0.95),
            "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
            "update_ops": 0.0, "update_latency_us": 0.0,
            "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
            "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        })
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]):
    matrix, protocol = plan["matrix"], plan["masked_refinement_protocol"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [row for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for rounds in matrix["reasoning_depths"]
            for row in _run_cell(candidate_name, int(size), int(rounds),
                                 int(matrix["queries_per_cell"]), int(seed),
                                 maximum, protocol)]
