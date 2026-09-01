from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import ResearchConfig, load_config
from .doctor import run_doctor
from .gates import (
    enforce_hypothesis_transition,
    ensure_can_create_plan,
    stop_gate_problems,
)
from .integrity import freeze_manifest, manifest_path, verify_manifest
from .ledger import (
    append_jsonl,
    append_plan_status,
    ensure_layout,
    latest_hypotheses,
    next_experiment_id,
    read_jsonl,
    register_plan,
    research_dir,
)
from .report import write_report
from .runner import run_experiment
from .schemas import validate_document
from .scientific_validity import invalid_experiment_ids
from .utils import atomic_write_json, load_json, project_root, sha256_json, utc_now


def _git_value(root: Path, *arguments: str) -> str | None:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def command_init(args: argparse.Namespace) -> int:
    root = project_root()
    ensure_layout(root)
    state_path = research_dir(root) / "state.json"
    if not state_path.exists():
        atomic_write_json(
            state_path,
            {
                "schema_version": 1,
                "protocol_version": 2,
                "generation": 0,
                "phase": "infrastructure",
                "cycle_number": 0,
                "completed_experiments": 0,
                "active_experiment_id": None,
                "last_experiment_id": None,
                "last_reflection_cycle": 0,
                "last_reflection_completed_experiments": 0,
                "last_literature_review_completed_experiments": 0,
                "updated_at": utc_now(),
            },
        )
    print(f"Initialized {research_dir(root)}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    report = run_doctor()
    for fact in report.facts:
        print(f"[OK] {fact}")
    for warning in report.warnings:
        print(f"[WARN] {warning}")
    for error in report.errors:
        print(f"[ERROR] {error}")
    print("Doctor: PASS" if report.ok else "Doctor: FAIL")
    return 0 if report.ok else 1


def command_integrity_freeze(args: argparse.Namespace) -> int:
    manifest = freeze_manifest(overwrite=args.overwrite)
    print(
        f"Frozen {len(manifest['files'])} files for {manifest['benchmark_version']}"
    )
    return 0


def command_integrity_verify(args: argparse.Namespace) -> int:
    result = verify_manifest()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


def _compression_protocol(config: ResearchConfig) -> dict[str, Any]:
    compression = config.raw["compression"]
    protocol = {
        "corpus_id": str(compression["corpus_id"]),
        "split_unit": "whole_files_sha256",
        "test_file_access": "evaluator_only",
        "predict_then_reveal": True,
        "shared_candidate": str(compression["shared_candidate"]),
        "classical_baselines": list(compression["classical_baselines"]),
        "shared_slow_state_updates": "forbidden",
        "test_tuning": "forbidden",
        "declared_horizons": list(compression["declared_horizons"]),
        "state_budget_bytes": int(compression["state_budget_bytes"]),
        "invalidation_rules": list(compression["invalidation_rules"]),
    }
    if config.benchmark_version == "heldout_repository_sequence_compression_v2":
        protocol.update({
            "credit_assignment_roles": [
                str(compression["shared_candidate"]),
                str(compression["global_credit_ablation"]),
                str(compression["frozen_hidden_ablation"]),
            ],
            "source_identical_contract": "topology_constants_initialization_data_order_update_count_input_output_identical_v1",
        })
    elif config.benchmark_version in {
        "heldout_repository_sequence_compression_v3",
        "heldout_repository_sequence_compression_v4",
        "heldout_repository_sequence_compression_v5",
    }:
        protocol.update({
            "causal_roles": [
                str(compression["shared_candidate"]),
                str(compression["causal_ablation_1"]),
                str(compression["causal_ablation_2"]),
            ],
            "source_identical_contract": (
                "state_width_transition_map_constants_initialization_data_order_context_input_update_output_identical_except_preregistered_surprise_gate_dense_clock_and_transition_learning_v1"
                if config.benchmark_version.endswith("_v5") else
                "expert_bank_constants_initialization_data_order_input_update_output_identical_except_preregistered_router_learning_and_active_expert_count_v1"
                if config.benchmark_version.endswith("_v4") else
                "topology_constants_initialization_data_order_input_output_identical_except_preregistered_recurrence_and_readout_learning_v1"
            ),
        })
    if config.benchmark_version in {
        "heldout_repository_sequence_compression_v2",
        "heldout_repository_sequence_compression_v3",
        "heldout_repository_sequence_compression_v4",
        "heldout_repository_sequence_compression_v5",
    }:
        protocol.update({
            "pareto_capability_metrics": [
                "bits_per_byte", "worst_file_bits_per_byte", "cold_bits_per_byte",
                "accuracy", "data_acquisition_ops", "fit_ops", "meta_fit_ops",
                "mean_query_ops", "update_ops", "state_bytes", "peak_state_bytes",
                "mean_bytes_touched", "workload_ops_r1", "workload_ops_r4",
                "workload_ops_r16",
            ],
        })
    return protocol


def _wt_prequential_protocol(config: ResearchConfig) -> dict[str, Any]:
    wt = config.raw["wt_prequential"]
    protocol = {
        "corpus_id": str(wt["corpus_id"]),
        "manifest_sha256": str(wt["manifest_sha256"]),
        "split_unit": "whole_csv_file_sha256",
        "train_files": list(wt["train_files"]),
        "development_files": list(wt["development_files"]),
        "test_files": list(wt["test_files"]),
        "candidate_metadata": "anonymous_permuted_tensors_and_random_slot_only",
        "predict_then_atomic_artifact_then_reveal": True,
        "shared_candidate": str(wt["shared_candidate"]),
        "classical_baselines": list(wt["classical_baselines"]),
        "knowledge_sizes": list(wt["knowledge_sizes"]),
        "fit_depth": int(wt["fit_depth"]),
        "fit_horizon": int(wt["fit_horizon"]),
        "declared_horizons": list(wt["horizons"]),
        "runner_random_channel_permutation": True,
        "normalization": "train_files_only_mechanical_partition",
        "state_budget_bytes": int(wt["state_budget_bytes"]),
        "declared_reuses": list(wt["declared_reuses"]),
        "minimum_meaningful_nrmse_effect": 0.1325268421060828,
        "saturation_nrmse": float(wt["saturation_nrmse"]),
        "saturation_worst_file_nrmse": float(wt["saturation_worst_file_nrmse"]),
        "pareto_capability_metrics": [
            "stable_rollout_rate", "normalized_rmse", "worst_file_normalized_rmse",
            "worst_transition_normalized_rmse", "rollout_16_nrmse",
            "rollout_32_nrmse", "rollout_96_nrmse", "data_acquisition_ops",
            "preprocessing_ops", "fit_ops", "adaptation_ops", "mean_query_ops",
            "update_ops", "state_bytes", "peak_state_bytes", "mean_bytes_touched",
            "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
        ],
        "invalidation_rules": list(wt["invalidation_rules"]),
    }
    if config.benchmark_version == "heldout_wt_changepoints_prequential_v2":
        protocol.update({
            "causal_roles": [
                str(wt["shared_candidate"]), str(wt["causal_ablation_1"]),
                str(wt["causal_ablation_2"]),
            ],
            "source_identical_contract":
                "dyadic_representation_constants_initialization_fit_order_update_schedule_output_identical_except_preregistered_cross_scale_composition_and_lifting_learning_v1",
        })
    elif config.benchmark_version == "heldout_wt_changepoints_prequential_v3":
        protocol.update({
            "causal_roles": [
                str(wt["shared_candidate"]), str(wt["causal_ablation_1"]),
                str(wt["causal_ablation_2"]),
            ],
            "source_identical_contract":
                "history_future_windows_rank_features_control_conditioning_constants_initialization_fit_order_update_schedule_and_output_identical_except_preregistered_predictive_state_learning_freeze_or_observation_history_projection_v1",
        })
    return protocol


def _active_sensor_protocol(config: ResearchConfig) -> dict[str, Any]:
    active = config.raw["active_sensor"]
    return {
        "training_world_seeds": list(active["training_world_seeds"]),
        "test_world_seed_source": "runner_scoring_seeds",
        "raw_sensor_values": "anonymous_continuous_single_probe_access",
        "shared_candidate": str(active["shared_candidate"]),
        "support_only_ablation": str(active["support_only_ablation"]),
        "frozen_representation_ablation": str(active["frozen_representation_ablation"]),
        "classical_baselines": list(active["classical_baselines"]),
        "sensor_count": int(active["sensor_count"]),
        "support_repetitions": int(active["support_repetitions"]),
        "noise_std": float(active["noise_std"]),
        "source_identical_contract": str(active.get(
            "source_identical_contract",
            "encoder_probe_policy_constants_support_order_query_update_output_identical_except_meta_world_access_and_preregistered_representation_learning_or_freezing_v1",
        )),
        "state_budget_bytes": int(active["state_budget_bytes"]),
        "pareto_capability_metrics": list(active["pareto_capability_metrics"]),
        "scout_only_no_promotion": True,
        "invalidation_rules": list(active["invalidation_rules"]),
    }


def command_plan_new(args: argparse.Namespace) -> int:
    root = project_root()
    ensure_layout(root)
    ensure_can_create_plan(root)
    config = load_config(root)
    hypotheses = latest_hypotheses(root)
    if args.hypothesis not in hypotheses:
        raise ValueError(f"Unknown hypothesis: {args.hypothesis}")
    if args.parent in invalid_experiment_ids(root):
        raise ValueError("A scientifically invalid experiment cannot be a replication parent")
    budget = config.budget(args.budget)
    experiment_id = next_experiment_id(root)
    manifest = load_json(manifest_path(root))
    evaluator_sha256 = manifest.get("evaluator_sha256")
    if not evaluator_sha256:
        raise ValueError("Active manifest has no protocol-v2 evaluator digest")
    primary_metrics = args.primary_metric or [
        "accuracy",
        "mean_query_ops",
        "knowledge_compute_slope",
    ]
    configured_directions = {
        **{name: "maximize" for name in config.raw["metrics"]["maximize"]},
        **{name: "minimize" for name in config.raw["metrics"]["minimize"]},
    }
    unknown_metrics = [name for name in primary_metrics if name not in configured_directions]
    if unknown_metrics:
        raise ValueError(f"Primary metrics have no configured direction: {unknown_metrics}")
    plan = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "parent_experiment_id": args.parent,
        "created_at": utc_now(),
        "status": "planned",
        "hypothesis_id": args.hypothesis,
        "title": args.title,
        "research_question": args.question,
        "architecture_family": args.family,
        "candidates": args.candidates,
        "benchmark": config.benchmark_version,
        "evaluator_sha256": evaluator_sha256,
        "budget": args.budget,
        "matrix": {
            "knowledge_sizes": list(budget.knowledge_sizes),
            "reasoning_depths": list(budget.reasoning_depths),
            "queries_per_cell": budget.queries_per_cell,
            "seed_policy": {
                "method": "runner_random_v1",
                "count": budget.scoring_seed_count,
                "minimum": 1_000_000,
                "maximum": 2_147_483_647,
            },
        },
        "primary_metrics": primary_metrics,
        "metric_directions": {
            name: configured_directions[name] for name in primary_metrics
        },
        "predicted_outcome": args.prediction,
        "falsification_criteria": args.kill_criterion,
        "promotion_criteria": args.promotion_criterion,
        "alternative_explanations": args.alternative,
        "confounds": args.confound,
        "outcome_policy": {
            "positive": args.positive_conclusion,
            "null": args.null_conclusion,
            "negative": args.negative_conclusion,
        },
        "git_before": {
            "commit": _git_value(root, "rev-parse", "HEAD"),
            "branch": _git_value(root, "branch", "--show-current"),
            "dirty": bool(_git_value(root, "status", "--porcelain")),
        },
    }
    if config.benchmark_version in {
        "heldout_raw_sensor_active_identification_v1",
        "heldout_raw_sensor_active_identification_v2",
    }:
        active = config.raw["active_sensor"]
        plan["matrix"]["knowledge_sizes"] = list(active["knowledge_sizes"])
        plan["matrix"]["reasoning_depths"] = list(active["probe_budgets"])
        plan["matrix"]["queries_per_cell"] = int(active["queries_per_cell"])
        plan["active_sensor_protocol"] = _active_sensor_protocol(config)
    if config.benchmark_version in {
        "heldout_three_family_continuous_transfer_v1",
        "heldout_three_family_continuous_transfer_v2",
        "heldout_three_family_continuous_transfer_v3",
        "heldout_three_family_continuous_transfer_v4",
        "heldout_three_family_continuous_transfer_v5",
        "heldout_three_family_continuous_transfer_v6",
        "heldout_three_family_continuous_transfer_v7",
        "heldout_three_family_continuous_transfer_v8",
    }:
        protocol = config.raw["three_family_continuous"]
        plan["matrix"]["knowledge_sizes"] = list(protocol["knowledge_sizes"])
        plan["matrix"]["reasoning_depths"] = list(protocol["reasoning_depths"])
        plan["continuous_transfer_protocol"] = {
            "families": list(protocol["families"]),
            "tensor_contract_sha256": str(protocol["tensor_contract_sha256"]),
            "shared_candidate": str(protocol["shared_candidate"]),
            "independent_ablation": str(protocol["independent_ablation"]),
            "cross_family_only_ablation": str(protocol["cross_family_only_ablation"]),
            "support_only_ablation": str(protocol["support_only_ablation"]),
            "classical_baselines": list(protocol["classical_baselines"]),
            "privileged_support_control": str(protocol["privileged_support_control"]),
            "family_labels": "evaluator_private",
            "semantic_channel_alignment": "forbidden",
            "normalization": "masked_training_worlds_only",
            "loss": "family_balanced_masked_normalized_mse",
            "state_budget_bytes": int(protocol["state_budget_bytes"]),
            "declared_reuses": list(protocol["declared_reuses"]),
            "invalidation_rules": list(protocol["invalidation_rules"]),
        }
        if config.benchmark_version.endswith(("_v2", "_v3", "_v4", "_v5", "_v6", "_v7", "_v8")):
            pareto_metrics = [
                "transfer_accuracy", "minimum_family_accuracy",
                "stable_rollout_rate", "normalized_rmse",
                "data_acquisition_ops", "preprocessing_ops", "fit_ops",
                "adaptation_ops", "mean_query_ops", "state_bytes",
                "peak_state_bytes", "mean_bytes_touched",
                "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
            ]
            if config.benchmark_version.endswith(("_v7", "_v8")):
                pareto_metrics.insert(pareto_metrics.index("state_bytes"), "update_ops")
            plan["continuous_transfer_protocol"].update({
                "pareto_capability_metrics": pareto_metrics,
                "causal_promotion_gates": [
                    "shared_vs_independent_gain", "cross_family_transfer_gain",
                ],
            })
    if config.benchmark_version.startswith("heldout_wt_changepoints_prequential_v"):
        wt = config.raw["wt_prequential"]
        plan["matrix"]["knowledge_sizes"] = list(wt["knowledge_sizes"])
        plan["matrix"]["reasoning_depths"] = list(wt["horizons"])
        plan["matrix"]["queries_per_cell"] = 18
        plan["wt_prequential_protocol"] = _wt_prequential_protocol(config)
    if config.benchmark_version.startswith("cross_family_"):
        transfer = config.raw["transfer"]
        plan["transfer_protocol"] = {
            "families": list(transfer["families"]),
            "training_world_seeds": list(transfer["training_world_seeds"]),
            "test_world_seed_source": "runner_scoring_seeds",
            "shared_candidate": str(transfer["shared_candidate"]),
            "independent_ablation": str(transfer["independent_ablation"]),
            "specialist_baselines": list(transfer["specialist_baselines"]),
            "family_specific_rules": "forbidden",
            "family_labels": "forbidden",
            "test_tuning": "forbidden",
            "representation_interface": str(transfer["representation_interface"]),
            "learner_contract": str(transfer["learner_contract"]),
            "shared_slow_fit_scope": str(transfer["shared_slow_fit_scope"]),
            "test_support_adaptation": str(transfer["test_support_adaptation"]),
            "test_result_access_during_fit": "forbidden",
            "declared_horizons": list(transfer["declared_horizons"]),
            "state_budget_bytes": int(transfer["state_budget_bytes"]),
            "invalidation_rules": list(transfer["invalidation_rules"]),
        }
        for key in ("fragment_capacity", "composition_rule", "permutation_equivariance"):
            if key in transfer:
                plan["transfer_protocol"][key] = transfer[key]
    if config.benchmark_version.startswith("nonstationary_online_update_"):
        online = config.raw["online_update"]
        plan["online_update_protocol"] = {
            "mechanisms": list(online["mechanisms"]),
            "training_stream_seeds": list(online["training_stream_seeds"]),
            "test_stream_seed_source": "runner_scoring_seeds",
            "predict_then_reveal": True,
            "shared_candidate": str(online["shared_candidate"]),
            "classical_baselines": list(online["classical_baselines"]),
            "mechanism_labels": "forbidden",
            "test_tuning": "forbidden",
            "declared_horizons": list(online["declared_horizons"]),
            "state_budget_bytes_per_slot": int(online["state_budget_bytes_per_slot"]),
            "shared_state_budget_bytes": int(online["shared_state_budget_bytes"]),
            "invalidation_rules": list(online["invalidation_rules"]),
        }
    if config.benchmark_version.startswith("heldout_repository_sequence_"):
        if config.benchmark_version in {
            "heldout_repository_sequence_compression_v2",
            "heldout_repository_sequence_compression_v3",
            "heldout_repository_sequence_compression_v4",
            "heldout_repository_sequence_compression_v5",
        }:
            compression = config.raw["compression"]
            plan["matrix"]["knowledge_sizes"] = list(compression["knowledge_sizes"])
            plan["matrix"]["reasoning_depths"] = list(compression["context_depths"])
            plan["matrix"]["queries_per_cell"] = int(compression["queries_per_cell"])
        plan["compression_protocol"] = _compression_protocol(config)
        if config.benchmark_version in {
            "heldout_repository_sequence_compression_v2",
            "heldout_repository_sequence_compression_v3",
            "heldout_repository_sequence_compression_v4",
            "heldout_repository_sequence_compression_v5",
        }:
            metrics = list(plan["compression_protocol"]["pareto_capability_metrics"])
            plan["primary_metrics"] = metrics
            plan["metric_directions"] = {
                name: configured_directions[name] for name in metrics
            }
    if config.benchmark_version.startswith("heldout_parallel_masked_"):
        masked = config.raw["masked_refinement"]
        stack = config.raw.get("stack_depth", {})
        is_stack = config.benchmark_version.endswith(("_v8", "_v9", "_v10", "_v11"))
        active = stack if is_stack else masked
        if config.benchmark_version in {
            "heldout_parallel_masked_infilling_v3",
            "heldout_parallel_masked_infilling_v4",
            "heldout_parallel_masked_infilling_v5",
            "heldout_parallel_masked_infilling_v6",
            "heldout_parallel_masked_infilling_v7",
            "heldout_parallel_masked_infilling_v8",
            "heldout_parallel_masked_infilling_v9",
            "heldout_parallel_masked_infilling_v10",
            "heldout_parallel_masked_infilling_v11",
        }:
            plan["matrix"]["knowledge_sizes"] = list(active["knowledge_sizes"])
            plan["matrix"]["reasoning_depths"] = list(
                active["stack_depths"]
                if is_stack
                else masked["refinement_rounds"]
            )
            plan["matrix"]["queries_per_cell"] = int(active["queries_per_cell"])
        protocol = {
            "corpus_id": str(active["corpus_id"]),
            "split_unit": "whole_files_sha256",
            "test_file_access": "evaluator_only",
            "simultaneous_snapshot_rounds": True,
            "span_lengths": list(masked["span_lengths"]),
            "context_bytes": int(masked["context_bytes"]),
            "runner_random_masks_and_permutation": True,
            "shared_candidate": str(active["shared_candidate"]),
            "classical_baselines": list(masked["classical_baselines"]),
            "declared_horizons": list(masked["declared_horizons"]),
            "state_budget_bytes": int(active["state_budget_bytes"]),
            "invalidation_rules": list(active["invalidation_rules"]),
        }
        if config.benchmark_version in {
            "heldout_parallel_masked_infilling_v4",
            "heldout_parallel_masked_infilling_v5",
            "heldout_parallel_masked_infilling_v6",
            "heldout_parallel_masked_infilling_v7",
            "heldout_parallel_masked_infilling_v8",
            "heldout_parallel_masked_infilling_v9",
            "heldout_parallel_masked_infilling_v10",
            "heldout_parallel_masked_infilling_v11",
        }:
            if is_stack:
                contract = (
                    "delimiter_trace_representation_constants_initialization_"
                    "training_order_query_alignment_and_output_identical_except_"
                    "learned_pushdown_finite_state_and_frozen_transition_v1"
                )
                protocol.update({
                    "training_max_depth": int(stack["training_max_depth"]),
                    "test_depths": list(stack["stack_depths"]),
                    "task_unit": (
                        "balanced_real_python_closure_chain"
                        if config.benchmark_version.endswith(("_v9", "_v10", "_v11"))
                        else "balanced_real_python_delimiter_trace"
                    ),
                })
            elif config.benchmark_version.endswith(("_v6", "_v7")):
                contract = (
                    "equality_byte_representation_grammar_extractor_constants_"
                    "initialization_training_order_query_alignment_and_output_"
                    "identical_except_preregistered_recursion_flattening_and_"
                    "grammar_learning_v1"
                )
            elif config.benchmark_version.endswith("_v5"):
                contract = (
                    "factor_graph_byte_representation_constants_initialization_"
                    "training_order_update_rule_and_output_identical_except_"
                    "preregistered_factor_learning_one_sweep_and_freeze_v1"
                )
            else:
                contract = (
                    "tensor_rank_token_representation_initialization_training_"
                    "order_update_count_and_probabilities_identical_except_"
                    "preregistered_contraction_schedule_and_tensor_learning_v1"
                )
            protocol.update({
                "causal_ablation_1": str(active["causal_ablation_1"]),
                "causal_ablation_2": str(active["causal_ablation_2"]),
                "source_identical_contract": contract,
            })
        else:
            protocol["one_pass_ablation"] = str(masked["one_pass_ablation"])
        if config.benchmark_version == "heldout_parallel_masked_infilling_v3":
            protocol["causal_ablation_2"] = str(
                masked["causal_ablation_2"]
            )
        plan["masked_refinement_protocol"] = protocol
    if config.benchmark_version.startswith("heldout_mechanism_recombination_"):
        recombination = config.raw["recombination"]
        if config.benchmark_version in {
            "heldout_mechanism_recombination_v4",
            "heldout_mechanism_recombination_v5",
            "heldout_mechanism_recombination_v6",
        }:
            plan["matrix"]["knowledge_sizes"] = list(recombination["knowledge_sizes"])
            plan["matrix"]["reasoning_depths"] = list(
                recombination[
                    "composition_lengths_v6"
                    if config.benchmark_version.endswith("_v6")
                    else "exposure_counts"
                ]
            )
            plan["matrix"]["queries_per_cell"] = int(recombination["queries_per_cell"])
        plan["mechanism_recombination_protocol"] = {
            "state_count": int(recombination["state_count"]),
            "mechanism_source_seed": int(recombination["mechanism_source_seed"]),
            "source_mechanisms": list(recombination["source_mechanisms"]),
            "train_compositions": list(recombination["train_compositions"]),
            "heldout_compositions": list(recombination["heldout_compositions"]),
            "runner_random_state_conjugation": True,
            "equal_public_shapes": True,
            "shared_candidate": str(recombination["shared_candidate"]),
            "independent_ablation": str(recombination["independent_ablation"]),
            "no_cross_mechanism_ablation": str(recombination["no_cross_mechanism_ablation"]),
            "classical_baselines": list(recombination["classical_baselines"]),
            "declared_horizons": list(recombination["declared_horizons"]),
            "state_budget_bytes": int(recombination["state_budget_bytes"]),
            "invalidation_rules": list(recombination["invalidation_rules"]),
        }
        if "pareto_capability_metrics" in recombination:
            plan["mechanism_recombination_protocol"]["pareto_capability_metrics"] = list(
                recombination["pareto_capability_metrics"]
            )
        if config.benchmark_version == "heldout_mechanism_recombination_v6":
            protocol = plan["mechanism_recombination_protocol"]
            protocol.update({
                "heldout_compositions": list(recombination["heldout_compositions_v6"]),
                "composition_lengths": list(recombination["composition_lengths_v6"]),
                "exposure_count": 16,
                "shared_candidate": str(recombination["shared_candidate_v6"]),
                "independent_ablation": str(recombination["independent_ablation_v6"]),
                "no_cross_mechanism_ablation": str(recombination["no_cross_mechanism_ablation_v6"]),
                "source_identical_contract": str(recombination["source_identical_contract_v6"]),
                "invalidation_rules": list(recombination["invalidation_rules_v6"]),
            })
    if config.benchmark_version in {
        "continuous_local_cellular_v1", "continuous_local_cellular_v2",
        "continuous_local_cellular_v3", "continuous_local_cellular_v4",
    }:
        local = config.raw["continuous_local_cellular"]
        plan["matrix"]["knowledge_sizes"] = list(local["knowledge_sizes"])
        plan["matrix"]["reasoning_depths"] = list(local["reasoning_depths"])
        plan["matrix"]["queries_per_cell"] = int(local["queries_per_cell"])
        metrics = list(local["pareto_capability_metrics"])
        plan["primary_metrics"] = metrics
        plan["metric_directions"] = {
            name: configured_directions[name] for name in metrics
        }
        plan["continuous_local_protocol"] = {
            "shared_candidate": str(local["shared_candidate"]),
            "dense_ablation": str(local["dense_ablation"]),
            "frozen_ablation": str(local["frozen_ablation"]),
            "classical_baselines": list(local["classical_baselines"]),
            "source_identical_contract": {
                "continuous_local_cellular_v1": "anonymous_channels_constants_fit_update_output_identical_except_sparse_dense_or_frozen_learning_v1",
                "continuous_local_cellular_v2": "anonymous_inputs_constants_rows_initialization_update_order_output_bounds_identical_except_factorized_monolithic_or_frozen_learning_v2",
                "continuous_local_cellular_v3": "anonymous_inputs_constants_lift_features_fit_update_output_identical_except_dyadic_sequential_or_frozen_propagation_v3",
                "continuous_local_cellular_v4": "anonymous_inputs_program_language_population_constants_proposals_execution_output_identical_except_true_shuffled_or_frozen_fitness_selection_v4",
            }[config.benchmark_version],
            "state_budget_bytes": int(local["state_budget_bytes"]),
            "minimum_nrmse_gain": float(local["minimum_nrmse_gain"]),
            "pareto_capability_metrics": metrics,
            "invalidation_rules": list(local["invalidation_rules"]),
        }
    if config.benchmark_version == "program_induction_from_whole_io_v3":
        search = config.raw["whole_io_search"]
        plan["matrix"]["knowledge_sizes"] = list(search["knowledge_sizes"])
        plan["matrix"]["reasoning_depths"] = list(search["reasoning_depths"])
        plan["matrix"]["queries_per_cell"] = int(search["queries_per_cell"])
        metrics = list(search["pareto_capability_metrics"])
        plan["primary_metrics"] = metrics
        plan["metric_directions"] = {
            name: configured_directions[name] for name in metrics
        }
        plan["whole_io_search_protocol"] = {
            "shared_candidate": str(search["shared_candidate"]),
            "support_only_ablation": str(search["support_only_ablation"]),
            "frozen_ablation": str(search["frozen_ablation"]),
            "classical_baselines": list(search["classical_baselines"]),
            "source_identical_contract": "complete_solver_objective_ties_support_execution_output_identical_except_meta_support_or_frozen_search_priority_v1",
            "state_budget_bytes": int(search["state_budget_bytes"]),
            "pareto_capability_metrics": metrics,
            "invalidation_rules": list(search["invalidation_rules"]),
        }
    if config.benchmark_version.startswith("heldout_dronepropa_"):
        drone = config.raw["dronepropa"]
        plan["dronepropa_protocol"] = {
            "corpus_id": str(drone["corpus_id"]),
            "split_unit": "whole_mat_file_sha256",
            "split_manifest_sha256": str(drone["split_manifest_sha256"]),
            "candidate_metadata": "anonymous_slots_only",
            "shared_candidate": str(drone["shared_candidate"]),
            "independent_ablation": str(drone["independent_ablation"]),
            "no_sharing_ablation": str(drone["no_sharing_ablation"]),
            "classical_baselines": list(drone["classical_baselines"]),
            "privileged_support_control": str(drone["privileged_support_control"]),
            "history_samples": int(drone["history_samples"]),
            "train_anchors_per_file": int(drone["train_anchors_per_file"]),
            "adaptation_anchors_per_file": int(drone["adaptation_anchors_per_file"]),
            "evaluation_anchors_per_file": int(drone["evaluation_anchors_per_file"]),
            "teacher_forced_horizon": int(drone["teacher_forced_horizon"]),
            "rollout_horizons": list(drone["rollout_horizons"]),
            "runner_random_evaluation_anchors": True,
            "future_controls": "evaluator_supplied_identically",
            "future_targets": "forbidden",
            "test_tuning": "forbidden",
            "state_budget_bytes": int(drone["state_budget_bytes"]),
            "declared_reuses": list(drone["declared_reuses"]),
            "invalidation_rules": list(drone["invalidation_rules"]),
        }
    validate_document("experiment_plan", plan, root)
    path = research_dir(root) / "plans" / f"{experiment_id}.json"
    atomic_write_json(path, plan)
    digest = register_plan(plan, path, root)
    print(path)
    print(f"plan_sha256={digest}")
    return 0


def command_plan_invalidate(args: argparse.Namespace) -> int:
    root = project_root()
    supplied_path = args.plan.resolve()
    plan = load_json(supplied_path)
    validate_document("experiment_plan", plan, root)
    experiment_id = str(plan["experiment_id"])
    canonical_path = (research_dir(root) / "plans" / f"{experiment_id}.json").resolve()
    if supplied_path != canonical_path:
        raise ValueError(f"Plan must be invalidated at its canonical path: {canonical_path}")
    if (research_dir(root) / "results" / f"{experiment_id}.json").exists():
        raise ValueError("A plan with a recorded result cannot be invalidated")
    registered = next(
        (
            event
            for event in reversed(
                read_jsonl(research_dir(root) / "plan_registry.jsonl")
            )
            if event.get("experiment_id") == experiment_id
        ),
        None,
    )
    if registered is None or registered.get("plan_sha256") != sha256_json(plan):
        raise ValueError("Plan is unregistered or changed after preregistration")
    append_plan_status(experiment_id, "invalidated", args.reason, root)
    print(f"{experiment_id} invalidated (append-only)")
    return 0


def command_run(args: argparse.Namespace) -> int:
    path = run_experiment(args.plan)
    print(path)
    return 0


def command_report(args: argparse.Namespace) -> int:
    path = write_report()
    print(path)
    return 0


def command_hypothesis_list(args: argparse.Namespace) -> int:
    for hypothesis_id, value in sorted(latest_hypotheses().items()):
        print(
            f"{hypothesis_id}\t{value['status']}\t{value['confidence']:.2f}\t"
            f"{value['title']}"
        )
    return 0


def command_hypothesis_update(args: argparse.Namespace) -> int:
    root = project_root()
    gates = stop_gate_problems(root)
    if gates:
        raise RuntimeError("hypothesis update blocked: " + "; ".join(gates))
    hypotheses = latest_hypotheses(root)
    if args.id not in hypotheses:
        raise ValueError(f"Unknown hypothesis: {args.id}")
    previous = hypotheses[args.id]
    requested_status = args.status or str(previous["status"])
    enforce_hypothesis_transition(
        previous,
        requested_status,
        args.evidence,
        args.candidate,
        root,
    )
    updated: dict[str, Any] = dict(previous)
    updated["revision"] = int(previous["revision"]) + 1
    updated["updated_at"] = utc_now()
    updated["status"] = requested_status
    updated["confidence"] = (
        args.confidence if args.confidence is not None else previous["confidence"]
    )
    updated["change_note"] = args.note
    invalid_ids = invalid_experiment_ids(root)
    updated["evidence_experiment_ids"] = [
        value
        for value in dict.fromkeys(
            [*previous.get("evidence_experiment_ids", []), *args.evidence]
        )
        if value not in invalid_ids
    ]
    if args.next_experiment:
        updated["next_experiment"] = args.next_experiment
    validate_document("hypothesis", updated, root)
    append_jsonl(research_dir(root) / "hypothesis_events.jsonl", updated)
    print(f"{args.id} revision {updated['revision']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nextai")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init = subcommands.add_parser("init")
    init.set_defaults(func=command_init)

    doctor = subcommands.add_parser("doctor")
    doctor.set_defaults(func=command_doctor)

    integrity = subcommands.add_parser("integrity")
    integrity_sub = integrity.add_subparsers(dest="integrity_command", required=True)
    freeze = integrity_sub.add_parser("freeze")
    freeze.add_argument("--overwrite", action="store_true")
    freeze.set_defaults(func=command_integrity_freeze)
    verify = integrity_sub.add_parser("verify")
    verify.set_defaults(func=command_integrity_verify)

    plan = subcommands.add_parser("plan")
    plan_sub = plan.add_subparsers(dest="plan_command", required=True)
    new = plan_sub.add_parser("new")
    new.add_argument("--hypothesis", required=True)
    new.add_argument("--parent")
    new.add_argument("--title", required=True)
    new.add_argument("--question", required=True)
    new.add_argument("--family", required=True)
    new.add_argument("--candidates", nargs="+", required=True)
    new.add_argument("--budget", choices=["quick", "screen", "deep"], default="quick")
    new.add_argument("--primary-metric", action="append", default=[])
    new.add_argument("--prediction", required=True)
    new.add_argument("--kill-criterion", action="append", required=True)
    new.add_argument("--promotion-criterion", action="append", required=True)
    new.add_argument("--alternative", action="append", required=True)
    new.add_argument("--confound", action="append", required=True)
    new.add_argument("--positive-conclusion", required=True)
    new.add_argument("--null-conclusion", required=True)
    new.add_argument("--negative-conclusion", required=True)
    new.set_defaults(func=command_plan_new)
    invalidate = plan_sub.add_parser("invalidate")
    invalidate.add_argument("--plan", type=Path, required=True)
    invalidate.add_argument("--reason", required=True)
    invalidate.set_defaults(func=command_plan_invalidate)

    run = subcommands.add_parser("run")
    run.add_argument("--plan", type=Path, required=True)
    run.set_defaults(func=command_run)

    report = subcommands.add_parser("report")
    report.set_defaults(func=command_report)

    hypothesis = subcommands.add_parser("hypothesis")
    hypothesis_sub = hypothesis.add_subparsers(dest="hypothesis_command", required=True)
    hypothesis_list = hypothesis_sub.add_parser("list")
    hypothesis_list.set_defaults(func=command_hypothesis_list)
    hypothesis_update = hypothesis_sub.add_parser("update")
    hypothesis_update.add_argument("--id", required=True)
    hypothesis_update.add_argument(
        "--status",
        choices=[
            "proposed",
            "testing",
            "promising",
            "uncertain",
            "falsified",
            "dormant",
            "promoted",
        ],
    )
    hypothesis_update.add_argument("--confidence", type=float)
    hypothesis_update.add_argument("--evidence", action="append", default=[])
    hypothesis_update.add_argument("--candidate")
    hypothesis_update.add_argument("--next-experiment")
    hypothesis_update.add_argument("--note", required=True)
    hypothesis_update.set_defaults(func=command_hypothesis_update)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, FileExistsError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
