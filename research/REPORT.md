# Research report

Generated: 2026-08-31T16:45:04Z

Only results from the same benchmark version and budget tier are compared.
The implementable Pareto frontier excludes privileged support controls and is capability-gated.
Pareto axes come from the frozen benchmark contract; incomplete rows cannot remove an axis or enter the frontier.
Append-only scientific-validity corrections exclude 3 result(s) from every frontier and evidential comparison.

## action_conditioned_predictive_equivalence_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0030.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0030 | random_history_policy | implementable | complete | 0.02083 | 1 | 27.67 | 23 | - | 810.7 | 0.6701 (2; screening) | 0 |  |
| EXP-20260830-0030 | context_tree_state | implementable | complete | 1 | 1 | 485 | 23 | - | 1.147e+04 | 0.0357 (2; screening) | 896 |  |
| EXP-20260830-0030 | cssr_state_reconstructor | implementable | complete | 1 | 1 | 485 | 23 | - | 1.147e+04 | 0.0357 (2; screening) | 576 |  |
| EXP-20260830-0030 | spectral_psr_state | implementable | complete | 1 | 1 | 485 | 23 | - | 1.224e+04 | 0.0357 (2; screening) | 832 |  |
| EXP-20260830-0030 | empirical_bisimulation_state | implementable | complete | 1 | 1 | 485 | 23 | - | 1.147e+04 | 0.0357 (2; screening) | 576 |  |
| EXP-20260830-0030 | recurrent_history_encoder | implementable | complete | 0.5208 | 1 | 2.567e+06 | 23 | - | 4.295e+07 | 0.6653 (2; screening) | 9280 |  |
| EXP-20260830-0030 | contrastive_predictive_state | implementable | complete | 1 | 1 | 485 | 23 | - | 1.378e+04 | 0.0357 (2; screening) | 832 |  |
| EXP-20260830-0030 | information_bottleneck_state | implementable | complete | 1 | 1 | 485 | 23 | - | 1.301e+04 | 0.0357 (2; screening) | 576 |  |
| EXP-20260830-0030 | oracle_predictive_state | privileged support control | complete | 1 | 1 | 177.7 | 23 | - | 2851 | 0.09759 (2; screening) | 384 |  |

## active_information_acquisition_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0029.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0029 | no_probe_guess | implementable | complete | 0.04167 | 1 | 3.667 | 0 | - | 63.33 | 0 (2; screening) | 64 |  |
| EXP-20260830-0029 | passive_observe_all | implementable | complete | 1 | 1 | 2673 | 190.7 | - | 4.549e+04 | 1.67 (2; screening) | 1312 |  |
| EXP-20260830-0029 | random_probe_policy | implementable | complete | 1 | 1 | 620.8 | 84.67 | - | 1.104e+04 | 1.386 (2; screening) | 1312 |  |
| EXP-20260830-0029 | fixed_probe_order | implementable | complete | 1 | 1 | 581.4 | 80.17 | - | 1.282e+04 | 1.484 (2; screening) | 1312 |  |
| EXP-20260830-0029 | entropy_greedy_probe | implementable | complete | 1 | 1 | 5230 | 29.33 | - | 8.897e+04 | 1.756 (2; screening) | 1312 |  |
| EXP-20260830-0029 | certified_decision_tree | implementable | complete | 1 | 1 | 183.3 | 29.33 | - | 4521 | 0.8716 (2; screening) | 1624 |  |
| EXP-20260830-0029 | learned_value_probe_policy | implementable | complete | 1 | 1 | 198 | 29.33 | - | 5615 | 0.8286 (2; screening) | 1936 |  |
| EXP-20260830-0029 | oracle_target_reader | privileged support control | complete | 1 | 1 | 3.667 | 0 | - | 63.33 | 0 (2; screening) | 64 |  |

## adaptive_depth_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0004, EXP-20260830-0005, EXP-20260830-0006.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0004 | random_guess | implementable | complete | 0.01042 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0004 | fixed_short_indexed | implementable | complete | 0.6667 | 1 | 4 | - | - | - | 0 (2; screening) | 18568 |  |
| EXP-20260830-0004 | fixed_max_indexed | implementable | complete | 1 | 1 | 16 | - | - | - | 0 (2; screening) | 18568 |  |
| EXP-20260830-0004 | adaptive_linear_scan | implementable | complete | 1 | 1 | 594.3 | - | - | - | 1.27 (2; screening) | 29136 |  |
| EXP-20260830-0004 | adaptive_indexed | implementable | complete | 1 | 1 | 7 | - | - | - | 0 (2; screening) | 18856 |  |
| EXP-20260830-0005 | random_guess | implementable | complete | 0.01042 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0005 | fixed_short_indexed | implementable | complete | 0.6667 | 1 | 4 | - | - | - | 0 (2; screening) | 18568 |  |
| EXP-20260830-0005 | fixed_max_indexed | implementable | complete | 1 | 1 | 16 | - | - | - | 0 (2; screening) | 18568 |  |
| EXP-20260830-0005 | adaptive_indexed | implementable | complete | 1 | 1 | 7 | - | - | - | 0 (2; screening) | 18856 |  |
| EXP-20260830-0005 | learned_local_halt | implementable | complete | 1 | 1 | 40 | - | - | - | 0 (2; screening) | 23240 |  |
| EXP-20260830-0006 | random_guess | implementable | complete | 0.01042 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0006 | adaptive_linear_scan | implementable | complete | 1 | 1 | 594.3 | - | - | - | 1.27 (2; screening) | 29136 |  |
| EXP-20260830-0006 | adaptive_indexed | implementable | complete | 1 | 1 | 7 | - | - | - | 0 (2; screening) | 18856 |  |
| EXP-20260830-0006 | oracle_modular_router | privileged support control | complete | 1 | 1 | 14 | - | - | - | 0 (2; screening) | 38448 |  |

## ambiguous_cross_task_energy_transfer_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0033.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0033 | random_parity_guess | implementable | complete | 0 | 1 | 63 | 63 | - | - | 0 (2; screening) | 128 |  |
| EXP-20260830-0033 | nearest_code_memory | implementable | complete | 0 | 1 | 2520 | 63 | - | - | 1 (2; screening) | 520 |  |
| EXP-20260830-0033 | classical_hopfield_parity | implementable | complete | 0 | 1 | 8064 | 63 | - | - | 0 (2; screening) | 31752 |  |
| EXP-20260830-0033 | exact_affine_span_decoder | implementable | complete | 1 | 1 | 4160 | 63 | - | - | 0 (2; screening) | 824 |  |
| EXP-20260830-0033 | sequential_factor_energy | implementable | complete | 1 | 1 | 1.121e+04 | 63 | - | - | 8.577e-05 (2; screening) | 10924 |  |
| EXP-20260830-0033 | learned_parallel_parity_energy | implementable | complete | 1 | 1 | 3133 | 63 | - | - | 0.000307 (2; screening) | 10924 |  |
| EXP-20260830-0033 | oracle_parallel_parity_energy | privileged support control | complete | 1 | 1 | 3133 | 63 | - | - | 0.000307 (2; screening) | 10924 |  |

## associative_relational_relaxation_adversarial_v2 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0018.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0018 | random_attractor_guess | implementable | complete | 0 | 3 | 36 | - | - | - | 5.131e-32 (3) | 2832 |  |
| EXP-20260830-0018 | bit_majority_attractor | implementable | complete | 0 | 3 | 36 | - | - | - | 5.131e-32 (3) | 44264 |  |
| EXP-20260830-0018 | nearest_stored_attractor | implementable | complete | 0 | 3 | 4032 | - | - | - | 1 (3) | 43968 |  |
| EXP-20260830-0018 | classical_hopfield_attractor | implementable | complete | 0.2245 | 3 | 2664 | - | - | - | -1.026e-31 (3) | 62120 |  |
| EXP-20260830-0018 | learned_parallel_energy | implementable | complete | 0.1852 | 3 | 244 | - | - | - | 0 (3) | 48480 |  |
| EXP-20260830-0018 | incremental_sequential_energy | implementable | complete | 1 | 3 | 185.5 | - | - | - | 0 (3) | 50280 |  |
| EXP-20260830-0018 | robust_parallel_energy | implementable | complete | 1 | 3 | 212 | - | - | - | 0 (3) | 50280 |  |
| EXP-20260830-0018 | oracle_relational_energy | privileged support control | complete | 1 | 3 | 212 | - | - | - | 0 (3) | 3352 |  |

## associative_relational_relaxation_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0017.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0017 | random_attractor_guess | implementable | complete | 0 | 1 | 30 | - | - | - | 0 (2; screening) | 2832 |  |
| EXP-20260830-0017 | bit_majority_attractor | implementable | complete | 0 | 1 | 30 | - | - | - | 0 (2; screening) | 10408 |  |
| EXP-20260830-0017 | nearest_stored_attractor | implementable | complete | 0 | 1 | 1200 | - | - | - | 1 (2; screening) | 10288 |  |
| EXP-20260830-0017 | classical_hopfield_attractor | implementable | complete | 1 | 1 | 1860 | - | - | - | 0 (2; screening) | 19016 |  |
| EXP-20260830-0017 | sequential_energy_repair | implementable | complete | 1 | 1 | 8212 | - | - | - | 0 (2; screening) | 14016 |  |
| EXP-20260830-0017 | learned_parallel_energy | implementable | complete | 1 | 1 | 174 | - | - | - | 0 (2; screening) | 14016 |  |
| EXP-20260830-0017 | oracle_relational_energy | privileged support control | complete | 1 | 1 | 174 | - | - | - | 0 (2; screening) | 2504 |  |

## asynchronous_temporal_binding_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0028.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0028 | random_event_guess | implementable | complete | 0 | 1 | 227.3 | 223.7 | - | 3866 | 0.9571 (2; screening) | 64 |  |
| EXP-20260830-0028 | rate_code_classifier | implementable | complete | 0.25 | 1 | 451 | 223.7 | - | 7668 | 0.9675 (2; screening) | 80 |  |
| EXP-20260830-0028 | nearest_timed_trace | implementable | complete | 0.08333 | 1 | 255.3 | 223.7 | - | 3931 | 0.8255 (2; screening) | 112 |  |
| EXP-20260830-0028 | clocked_spike_reservoir | implementable | complete | 0.0625 | 1 | 6.975e+04 | 3.476e+04 | - | 1.141e+06 | 0.5706 (2; screening) | 7440 |  |
| EXP-20260830-0028 | heap_event_transducer | implementable | complete | 1 | 1 | 2121 | 223.7 | - | 3.612e+04 | 1.114 (2; screening) | 272 |  |
| EXP-20260830-0028 | timed_automaton_matcher | implementable | complete | 1 | 1 | 256.7 | 223.7 | - | 4424 | 0.8202 (2; screening) | 272 |  |
| EXP-20260830-0028 | calendar_event_transducer | implementable | complete | 1 | 1 | 492 | 223.7 | - | 8414 | 0.8648 (2; screening) | 336 |  |
| EXP-20260830-0028 | learned_polychronous_binder | implementable | complete | 1 | 1 | 294 | 223.7 | - | 5083 | 0.6974 (2; screening) | 368 |  |
| EXP-20260830-0028 | oracle_temporal_binder | privileged support control | complete | 1 | 1 | 256.7 | 223.7 | - | 4364 | 0.8202 (2; screening) | 80 |  |

## behavioral_conjugacy_library_transfer_v1 / quick

Pareto axes: maximize `accuracy, near_equivalent_accuracy`; minimize `mean_query_ops, workload_ops_r16, state_bytes`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0038 | random_conjugacy_program | implementable | complete | 0.2083 | 1 | 1 | 24 | 29.33 | 882.7 | 0 (2; screening) | 992 |  |
| EXP-20260830-0038 | primitive_trace_enumerator | implementable | complete | 1 | 1 | 8.929e+04 | 24 | 6.029e+05 | 2.293e+07 | 0 (2; screening) | 992 | yes |
| EXP-20260830-0038 | exact_trace_memo | implementable | complete | 1 | 1 | 8.929e+04 | 24 | 6.029e+05 | 2.293e+07 | 0 (2; screening) | 3552 |  |
| EXP-20260830-0038 | syntactic_mdl_library | implementable | complete | 1 | 1 | 8.929e+04 | 24 | 6.029e+05 | 2.293e+07 | 0 (2; screening) | 992 | yes |
| EXP-20260830-0038 | unary_semantic_library | implementable | complete | 1 | 1 | 1.129e+05 | 24 | 7.21e+05 | 2.896e+07 | 0 (2; screening) | 1008 |  |
| EXP-20260830-0038 | relational_graph_mdl_library | implementable | complete | 1 | 1 | 856.2 | 24 | 3403 | 2.213e+05 | 0 (2; screening) | 1008 | yes |
| EXP-20260830-0038 | bayesian_relational_library | implementable | complete | 1 | 1 | 856.2 | 24 | 3403 | 2.369e+05 | 0 (2; screening) | 1008 |  |
| EXP-20260830-0038 | learned_relational_library | implementable | complete | 1 | 1 | 856.2 | 24 | 3403 | 2.214e+05 | 0 (2; screening) | 1296 |  |
| EXP-20260830-0038 | oracle_conjugacy_library | privileged support control | complete | 1 | 1 | 1 | 24 | 29.33 | 276.7 | 0 (2; screening) | 1008 |  |

## causal_intervention_adversarial_v2 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0012.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0012 | random_causal_guess | implementable | complete | 0.4514 | 3 | 1 | - | - | - | 0 (3) | 64 |  |
| EXP-20260830-0012 | adversarial_observational | implementable | complete | 0.5972 | 3 | 256 | - | - | - | 0 (3) | 38960 |  |
| EXP-20260830-0012 | nearest_intervention | implementable | complete | 0.4861 | 3 | 2408 | - | - | - | 0 (3) | 222000 |  |
| EXP-20260830-0012 | robust_dense_causal | implementable | complete | 1 | 3 | 543.4 | - | - | - | 0.7917 (3) | 48532 |  |
| EXP-20260830-0012 | robust_local_causal | implementable | complete | 1 | 3 | 25.5 | - | - | - | 0 (3) | 48532 |  |
| EXP-20260830-0012 | noninvariant_local_causal | implementable | complete | 0.08333 | 3 | 1.833 | - | - | - | 0 (3) | 47972 |  |
| EXP-20260830-0012 | oracle_adversarial_causal | privileged support control | complete | 1 | 3 | 25.5 | - | - | - | 0 (3) | 11248 |  |

## causal_intervention_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0011.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0011 | random_causal_guess | implementable | complete | 0.5417 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0011 | observational_conditioning | implementable | complete | 0.6667 | 1 | 7 | - | - | - | 0 (2; screening) | 576 |  |
| EXP-20260830-0011 | intervention_memorizer | implementable | complete | 0.6667 | 1 | 2 | - | - | - | 0 (2; screening) | 37776 |  |
| EXP-20260830-0011 | learned_dense_causal | implementable | complete | 1 | 1 | 78.92 | - | - | - | 1.019 (2; screening) | 39456 |  |
| EXP-20260830-0011 | learned_local_causal | implementable | complete | 1 | 1 | 27.58 | - | - | - | 0 (2; screening) | 39456 |  |
| EXP-20260830-0011 | oracle_local_causal | privileged support control | complete | 1 | 1 | 27.58 | - | - | - | 0 (2; screening) | 896 |  |

## cellular_propagation_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0010.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0010 | random_cellular_guess | implementable | complete | 0.625 | 1 | 1 | - | - | - | 0 (2; screening) | 8256 |  |
| EXP-20260830-0010 | learned_synchronous_ca | implementable | complete | 1 | 1 | 2236 | - | - | - | 1.543 (2; screening) | 8664 |  |
| EXP-20260830-0010 | learned_event_queue_ca | implementable | complete | 1 | 1 | 143 | - | - | - | 0 (2; screening) | 8488 |  |
| EXP-20260830-0010 | oracle_event_queue_ca | privileged support control | complete | 1 | 1 | 117.7 | - | - | - | 0 (2; screening) | 8464 |  |
| EXP-20260830-0010 | sparse_grid_bfs | implementable | complete | 1 | 1 | 117.7 | - | - | - | 0 (2; screening) | 8464 |  |

## context_specific_probabilistic_circuit_v1 / quick

Pareto axes: maximize `accuracy, near_equivalent_accuracy, continual_retention`; minimize `conditional_probability_mae, conditional_log_loss, calibration_error, mean_query_ops, fit_ops, state_bytes, circuit_nodes, update_ops, workload_ops_r16`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0040 | uniform_conditional | implementable | complete | 0 | 1 | 1 | 4.167 | 41.33 | 4.541e+04 | 0 (2; screening) | 8 |  |
| EXP-20260830-0040 | empirical_joint_table | implementable | complete | 0.8125 | 1 | 5652 | 4.167 | 41.33 | 1.554e+06 | 1.93 (2; screening) | 104919 |  |
| EXP-20260830-0040 | empirical_autoregressive_table | implementable | complete | 0.2708 | 1 | 662.9 | 4.167 | 41.33 | 2.362e+05 | 0.8784 (2; screening) | 84480 |  |
| EXP-20260830-0040 | chow_liu_tree | implementable | timeout | - | 1 | - | - | - | - | - (2; screening) | - |  |
| EXP-20260830-0040 | pairwise_factor_elimination | implementable | complete | 0.1042 | 1 | 1091 | 4.167 | 41.33 | 1.807e+06 | 2.034 (2; screening) | 776 |  |
| EXP-20260830-0040 | contextual_chow_liu | implementable | complete | 1 | 1 | 44 | 4.167 | 41.33 | 6.959e+07 | 0.8828 (2; screening) | 1048 | yes |
| EXP-20260830-0040 | fixed_region_spn | implementable | complete | 0.0625 | 1 | 44 | 4.167 | 41.33 | 9.269e+04 | 0.8828 (2; screening) | 1048 |  |
| EXP-20260830-0040 | learned_decomposable_spn | implementable | complete | 1 | 1 | 44 | 4.167 | 41.33 | 6.963e+07 | 0.8828 (2; screening) | 1048 |  |
| EXP-20260830-0040 | oracle_context_spn | privileged support control | complete | 1 | 1 | 44 | 4.167 | 41.33 | 2.17e+04 | 0.8828 (2; screening) | 1048 |  |

## continuous_event_predictive_state_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0027.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0027 | random_continuous_guess | implementable | complete | 0 | 1 | 3.667 | 0 | - | 63.33 | 0 (2; screening) | 64 |  |
| EXP-20260830-0027 | last_value_forecaster | implementable | complete | 0 | 1 | 4.667 | 1 | - | 115.3 | 0 (2; screening) | 72 |  |
| EXP-20260830-0027 | dense_linear_state_space | implementable | complete | 0 | 1 | 220 | 73.33 | - | 3.996e+04 | 1 (2; screening) | 336 |  |
| EXP-20260830-0027 | echo_state_forecaster | implementable | complete | 0 | 1 | 1525 | 73.33 | - | 4.667e+04 | 0.5688 (2; screening) | 4424 |  |
| EXP-20260830-0027 | exhaustive_switching_ar | implementable | complete | 1 | 1 | 25.67 | 4.667 | - | 823 | 0 (2; screening) | 216 |  |
| EXP-20260830-0027 | screened_switching_ar | implementable | complete | 1 | 1 | 25.67 | 4.667 | - | 823 | 0 (2; screening) | 216 |  |
| EXP-20260830-0027 | variance_triggered_kalman | implementable | complete | 1 | 1 | 27.67 | 4.667 | - | 1289 | 0 (2; screening) | 312 |  |
| EXP-20260830-0027 | event_predictive_state | implementable | complete | 1 | 1 | 30.67 | 4.667 | - | 932 | 0 (2; screening) | 280 |  |
| EXP-20260830-0027 | oracle_sparse_dynamics | privileged support control | complete | 1 | 1 | 25.67 | 4.667 | - | 393 | 0 (2; screening) | 96 |  |

## cross_family_relation_fragment_transfer_v4 / quick

Pareto axes: maximize `transfer_accuracy, minimum_family_accuracy, near_equivalent_accuracy`; minimize `data_acquisition_ops, fit_ops, meta_fit_ops, mean_query_ops, update_ops, state_bytes, peak_state_bytes, mean_bytes_touched, workload_ops_r16`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0051 | shared_relation_fragment_graph | implementable | crash | - | 1 | - | - | - | - | - (2; screening) | - |  |
| EXP-20260830-0051 | independent_relation_fragment_graph | implementable | complete | 0.2083 | 1 | 1620 | 96.71 | 4868 | 2.49e+06 | 0.598 (2; screening) | 346896 |  |
| EXP-20260830-0051 | specialist_contextual_chow_liu_suite_v2 | implementable | complete | 1 | 1 | 401.7 | 96.71 | 2244 | 7.038e+07 | 0.09712 (2; screening) | 5800 | yes |
| EXP-20260830-0051 | specialist_empirical_joint_suite_v2 | implementable | complete | 0.9323 | 1 | 1732 | 96.71 | 2244 | 2.211e+06 | 1.224 (2; screening) | 88679 |  |
| EXP-20260830-0051 | specialist_autoregressive_suite_v2 | implementable | complete | 0.8385 | 1 | 553.4 | 96.71 | 2244 | 9.964e+05 | 0.3023 (2; screening) | 72336 |  |
| EXP-20260830-0051 | oracle_cross_family_suite_v2 | privileged support control | complete | 1 | 1 | 104 | 96.71 | 751.8 | 4.91e+05 | 0.3833 (2; screening) | 2472 |  |
| EXP-20260830-0052 | shared_relation_fragment_graph | implementable | complete | 0.224 | 1 | 8261 | 96.71 | 1.879e+04 | 9.266e+06 | 0.5354 (2; screening) | 141104 |  |
| EXP-20260830-0052 | independent_relation_fragment_graph | implementable | complete | 0.1979 | 1 | 1620 | 96.71 | 4868 | 2.49e+06 | 0.6024 (2; screening) | 346896 |  |
| EXP-20260830-0052 | specialist_contextual_chow_liu_suite_v2 | implementable | complete | 0.9896 | 1 | 393 | 96.71 | 2201 | 7.037e+07 | 0.09927 (2; screening) | 5800 | yes |
| EXP-20260830-0052 | specialist_empirical_joint_suite_v2 | implementable | complete | 0.9219 | 1 | 1724 | 96.71 | 2201 | 2.202e+06 | 1.235 (2; screening) | 88720 |  |
| EXP-20260830-0052 | specialist_autoregressive_suite_v2 | implementable | complete | 0.8385 | 1 | 551 | 96.71 | 2201 | 9.939e+05 | 0.3164 (2; screening) | 72336 |  |
| EXP-20260830-0052 | oracle_cross_family_suite_v2 | privileged support control | complete | 1 | 1 | 104 | 96.71 | 751.8 | 4.91e+05 | 0.3833 (2; screening) | 2472 |  |

## cross_family_shared_representation_v1 / quick

Pareto axes: maximize `transfer_accuracy, minimum_family_accuracy`; minimize `workload_ops_r16, state_bytes, meta_fit_ops, data_acquisition_ops`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0041 | frozen_cross_family_encoder | implementable | complete | 0.005208 | 1 | 3977 | 2048 | 1216 | 4.991e+06 | 0.01306 (2; screening) | 17728 |  |
| EXP-20260830-0041 | shared_empirical_joint | implementable | complete | 0.1562 | 1 | 4449 | 2048 | 1216 | 5.476e+06 | 0.01167 (2; screening) | 17728 |  |
| EXP-20260830-0041 | shared_autoregressive | implementable | complete | 0.05208 | 1 | 4473 | 2048 | 1216 | 5.501e+06 | 0.01161 (2; screening) | 17728 |  |
| EXP-20260830-0041 | independent_cross_family_learner | implementable | complete | 0.02083 | 1 | 2761 | 2048 | 1216 | 3.721e+06 | 0.01881 (2; screening) | 26240 |  |
| EXP-20260830-0041 | shared_cross_family_learner | implementable | complete | 0.01562 | 1 | 3977 | 2048 | 1216 | 4.991e+06 | 0.01306 (2; screening) | 17728 |  |
| EXP-20260830-0041 | specialist_empirical_joint_suite | implementable | complete | 0.8958 | 1 | 1737 | 2048 | 2243 | 2.026e+06 | 1.21 (2; screening) | 89063 |  |
| EXP-20260830-0041 | specialist_autoregressive_suite | implementable | complete | 0.8281 | 1 | 561.4 | 2048 | 2243 | 8.146e+05 | 0.3135 (2; screening) | 72720 |  |
| EXP-20260830-0041 | specialist_contextual_chow_liu_suite | implementable | complete | 0.974 | 1 | 401 | 2048 | 2243 | 7.019e+07 | 0.09728 (2; screening) | 6184 |  |
| EXP-20260830-0041 | oracle_cross_family_suite | privileged support control | complete | 1 | 1 | 104 | 2048 | 751.8 | 3.01e+05 | 0.3833 (2; screening) | 2856 |  |
| EXP-20260830-0042 | shared_cross_family_learner | implementable | complete | 0.1771 | 1 | 6209 | 2048 | 1.651e+04 | 7.825e+06 | 0.01673 (2; screening) | 20448 |  |
| EXP-20260830-0042 | independent_pointer_cross_family_learner | implementable | complete | 0.1667 | 1 | 4881 | 2048 | 5888 | 6.441e+06 | 0.02128 (2; screening) | 27488 |  |
| EXP-20260830-0042 | exp0041_shared_cross_family_learner | implementable | complete | 0.01562 | 1 | 3977 | 2048 | 1216 | 4.991e+06 | 0.01306 (2; screening) | 17728 |  |
| EXP-20260830-0042 | shared_empirical_joint | implementable | complete | 0.1823 | 1 | 4449 | 2048 | 1216 | 5.476e+06 | 0.01167 (2; screening) | 17728 |  |
| EXP-20260830-0042 | shared_autoregressive | implementable | complete | 0.04688 | 1 | 4473 | 2048 | 1216 | 5.501e+06 | 0.01161 (2; screening) | 17728 |  |
| EXP-20260830-0042 | specialist_empirical_joint_suite | implementable | complete | 0.9219 | 1 | 1736 | 2048 | 2207 | 2.024e+06 | 1.204 (2; screening) | 89104 |  |
| EXP-20260830-0042 | specialist_autoregressive_suite | implementable | complete | 0.8385 | 1 | 546.3 | 2048 | 2207 | 7.992e+05 | 0.3101 (2; screening) | 72720 |  |
| EXP-20260830-0042 | specialist_contextual_chow_liu_suite | implementable | complete | 0.9792 | 1 | 393.4 | 2048 | 2207 | 7.018e+07 | 0.09918 (2; screening) | 6184 | yes |
| EXP-20260830-0042 | oracle_cross_family_suite | privileged support control | complete | 1 | 1 | 104 | 2048 | 751.8 | 3.01e+05 | 0.3833 (2; screening) | 2856 |  |

## cross_family_shared_representation_v2 / quick

Pareto axes unavailable: no scientifically valid immutable result.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0046 | shared_multiverse_local_learner | scientifically invalid | scientifically_invalid | 0.2292 | 1 | 3943 | 96.71 | 3.123e+04 | 5.718e+06 | 0.04049 (2; screening) | 37472 |  |
| EXP-20260830-0046 | independent_multiverse_local_learner | scientifically invalid | scientifically_invalid | 0.2396 | 1 | 3511 | 96.71 | 2.778e+04 | 5.274e+06 | 0.04548 (2; screening) | 117344 |  |
| EXP-20260830-0046 | shared_contextual_chow_liu_v2 | scientifically invalid | scientifically_invalid | 0.1198 | 1 | 3943 | 96.71 | 3.123e+04 | 8.863e+06 | 0.04049 (2; screening) | 37472 |  |
| EXP-20260830-0046 | shared_empirical_joint_v2 | scientifically invalid | scientifically_invalid | 0.25 | 1 | 7.812e+04 | 96.71 | 6.246e+05 | 8.497e+07 | 0.002043 (2; screening) | 630880 |  |
| EXP-20260830-0046 | shared_autoregressive_v2 | scientifically invalid | scientifically_invalid | 0.2396 | 1 | 7.812e+04 | 96.71 | 6.246e+05 | 8.497e+07 | 0.002043 (2; screening) | 630880 |  |
| EXP-20260830-0046 | specialist_contextual_chow_liu_suite_v2 | scientifically invalid | scientifically_invalid | 0.9844 | 1 | 400.2 | 96.71 | 2236 | 7.037e+07 | 0.09749 (2; screening) | 5800 |  |
| EXP-20260830-0046 | specialist_empirical_joint_suite_v2 | scientifically invalid | scientifically_invalid | 0.9271 | 1 | 1743 | 96.71 | 2236 | 2.222e+06 | 1.195 (2; screening) | 88720 |  |
| EXP-20260830-0046 | specialist_autoregressive_suite_v2 | scientifically invalid | scientifically_invalid | 0.8438 | 1 | 556.5 | 96.71 | 2236 | 9.994e+05 | 0.2883 (2; screening) | 72336 |  |
| EXP-20260830-0046 | oracle_cross_family_suite_v2 | scientifically invalid | scientifically_invalid | 1 | 1 | 104 | 96.71 | 751.8 | 4.91e+05 | 0.3833 (2; screening) | 2472 |  |

## cross_family_shared_representation_v3 / quick

Pareto axes unavailable: inconsistent immutable pareto_metrics across experiments.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0048 | shared_recurrent_predictive_state | implementable | complete | 0.01562 | 1 | 2023 | 96.71 | 1.018e+04 | 5.949e+06 | 0.2089 (2; screening) | 16064 |  |
| EXP-20260830-0048 | independent_recurrent_predictive_state | implementable | complete | 0.07292 | 1 | 994.9 | 96.71 | 1954 | 5.291e+06 | 0.4921 (2; screening) | 17280 |  |
| EXP-20260830-0048 | specialist_contextual_chow_liu_suite_v2 | implementable | complete | 1 | 1 | 401 | 96.71 | 2239 | 7.038e+07 | 0.09727 (2; screening) | 5800 |  |
| EXP-20260830-0048 | specialist_empirical_joint_suite_v2 | implementable | complete | 0.9219 | 1 | 1737 | 96.71 | 2239 | 2.215e+06 | 1.211 (2; screening) | 88679 |  |
| EXP-20260830-0048 | specialist_autoregressive_suite_v2 | implementable | complete | 0.8177 | 1 | 537.9 | 96.71 | 2239 | 9.802e+05 | 0.257 (2; screening) | 72336 |  |
| EXP-20260830-0048 | oracle_cross_family_suite_v2 | privileged support control | complete | 1 | 1 | 104 | 96.71 | 751.8 | 4.91e+05 | 0.3833 (2; screening) | 2472 |  |
| EXP-20260830-0050 | shared_recurrent_predictive_state | implementable | complete | 0.04688 | 1 | 5525 | 96.71 | 1.332e+04 | 9.462e+06 | 0.08554 (2; screening) | 17488 |  |
| EXP-20260830-0050 | independent_recurrent_predictive_state | implementable | complete | 0.0625 | 1 | 1300 | 96.71 | 2054 | 5.123e+06 | 0.3672 (2; screening) | 17488 |  |
| EXP-20260830-0050 | specialist_contextual_chow_liu_suite_v2 | implementable | complete | 0.9948 | 1 | 405.7 | 96.71 | 2267 | 7.038e+07 | 0.09615 (2; screening) | 5800 |  |
| EXP-20260830-0050 | specialist_empirical_joint_suite_v2 | implementable | complete | 0.9271 | 1 | 1747 | 96.71 | 2267 | 2.225e+06 | 1.194 (2; screening) | 88720 |  |
| EXP-20260830-0050 | specialist_autoregressive_suite_v2 | implementable | complete | 0.8177 | 1 | 546.2 | 96.71 | 2267 | 9.889e+05 | 0.2755 (2; screening) | 72336 |  |
| EXP-20260830-0050 | oracle_cross_family_suite_v2 | privileged support control | complete | 1 | 1 | 104 | 96.71 | 751.8 | 4.91e+05 | 0.3833 (2; screening) | 2472 |  |

## heldout_dronepropa_factor_recombination_v5 / quick

Pareto axes: maximize `none`; minimize `none`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0059 | shared_operator_subspace_arx | implementable | complete | 0.5913 | 1 | 4504 | 320 | 2608 | 2.11e+10 | 0 (2; screening) | 216112 |  |
| EXP-20260830-0059 | persistence_state_v1 | implementable | complete | 0.476 | 1 | 6 | 320 | 2608 | 8.992e+09 | 0 (2; screening) | 32 |  |
| EXP-20260830-0059 | ridge_arx_v1 | implementable | complete | 0.6041 | 1 | 4504 | 320 | 2608 | 2.058e+10 | 0 (2; screening) | 31168 |  |
| EXP-20260830-0059 | rls_arx_v1 | implementable | complete | 0.6071 | 1 | 4504 | 320 | 2608 | 2.628e+10 | 0 (2; screening) | 1.67979e+06 |  |
| EXP-20260830-0059 | nearest_operator_template_v1 | implementable | complete | 0.2713 | 1 | 4504 | 320 | 2608 | 2.318e+10 | 0 (2; screening) | 508672 |  |
| EXP-20260830-0059 | source_identical_independent_arx_v1 | implementable | complete | 0.5319 | 1 | 4504 | 320 | 2608 | 2.263e+10 | 0 (2; screening) | 15600 |  |
| EXP-20260830-0059 | no_sharing_pooled_arx_v1 | implementable | complete | 0.6071 | 1 | 4504 | 320 | 2608 | 2.316e+10 | 0 (2; screening) | 1.07136e+07 |  |
| EXP-20260830-0059 | empirical_gaussian_joint_v1 | implementable | timeout | - | 1 | - | - | - | - | - (2; screening) | - |  |
| EXP-20260830-0059 | contextual_gaussian_chow_liu_v1 | implementable | complete | 0.6041 | 1 | 4504 | 320 | 2608 | 2.058e+10 | 0 (2; screening) | 32288 |  |
| EXP-20260830-0059 | oracle_charged_condition_specialist_arx_v2 | privileged support control | complete | 0.008127 | 1 | 4504 | 320 | 2608 | 2.075e+10 | 0 (2; screening) | 171360 |  |
| EXP-20260830-0059 | privileged_same_condition_oracle_arx_v2 | privileged support control | complete | 0.008127 | 1 | 4504 | 320 | 2608 | 2.021e+10 | 0 (2; screening) | 62496 |  |

## heldout_mechanism_recombination_v2 / quick

Pareto axes: maximize `none`; minimize `none`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0056 | shared_latent_mechanism_library | implementable | complete | 0.125 | 1 | 7.333 | 1 | 117.3 | 3774 | 0 (2; screening) | 16432 |  |
| EXP-20260830-0056 | independent_latent_mechanism_library | implementable | complete | 0 | 1 | 121 | 1 | 1936 | 1.855e+04 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0056 | no_cross_mechanism_factorizer | implementable | complete | 0 | 1 | 7.333 | 1 | 117.3 | 3774 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0056 | unigram_recombination | implementable | complete | 0 | 1 | 7.333 | 1 | 117.3 | 3774 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0056 | markov5_recombination | implementable | complete | 0.02083 | 1 | 121 | 1 | 1936 | 1.855e+04 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0056 | nearest_template_recombination | implementable | complete | 0 | 1 | 121 | 1 | 1936 | 1.855e+04 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0056 | exact_mdl_module_library | implementable | complete | 0.125 | 1 | 7.333 | 1 | 117.3 | 3774 | 0 (2; screening) | 16432 |  |
| EXP-20260830-0056 | oracle_composition_graph | privileged support control | complete | 1 | 1 | 1 | 1 | 8 | 2026 | 0 (2; screening) | 0 |  |

## heldout_mechanism_recombination_v3 / quick

Pareto axes: maximize `none`; minimize `none`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0057 | operator_algebra_completion | implementable | complete | 0.625 | 1 | 7.333 | 1 | 58.67 | 3774 | 0 (2; screening) | 26064 |  |
| EXP-20260830-0057 | operator_algebra_independent | implementable | complete | 0 | 1 | 3601 | 1 | 2.881e+04 | 4.709e+05 | -4.468 (2; screening) | 24256 |  |
| EXP-20260830-0057 | operator_algebra_no_relations | implementable | complete | 0.04167 | 1 | 231 | 1 | 1848 | 3.285e+04 | -2.977 (2; screening) | 16416 |  |
| EXP-20260830-0057 | unigram_recombination | implementable | complete | 0 | 1 | 7.333 | 1 | 117.3 | 3774 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0057 | markov5_recombination | implementable | complete | 0 | 1 | 121 | 1 | 1936 | 1.855e+04 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0057 | nearest_template_recombination | implementable | complete | 0.02083 | 1 | 121 | 1 | 1936 | 1.855e+04 | 0 (2; screening) | 21632 |  |
| EXP-20260830-0057 | exact_mdl_module_library | implementable | complete | 0.04167 | 1 | 7.333 | 1 | 117.3 | 3774 | 0 (2; screening) | 16400 |  |
| EXP-20260830-0057 | oracle_composition_graph | privileged support control | complete | 1 | 1 | 1 | 1 | 8 | 2026 | 0 (2; screening) | 0 |  |

## heldout_parallel_masked_infilling_v1 / quick

Pareto axes unavailable: no scientifically valid immutable result.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0047 | iterative_masked_learner | scientifically invalid | scientifically_invalid | 0.1249 | 1 | 3817 | 674.7 | 1.324e+06 | 8.276e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | one_pass_masked_learner | scientifically invalid | scientifically_invalid | 0.1274 | 1 | 1798 | 184 | 5.734e+05 | 3.935e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | uniform_masked_byte | scientifically invalid | scientifically_invalid | 0 | 1 | 863.3 | 674.7 | 129.3 | 1.92e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | empirical_unigram_masked_byte | scientifically invalid | scientifically_invalid | 0.1037 | 1 | 1452 | 674.7 | 2.649e+05 | 3.19e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | left_to_right_ppm_masked_byte | scientifically invalid | scientifically_invalid | 0.1081 | 1 | 2043 | 674.7 | 5.297e+05 | 4.462e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | context_tree_weighting_masked_byte | scientifically invalid | scientifically_invalid | 0.1372 | 1 | 2635 | 674.7 | 7.946e+05 | 5.733e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | dense_autoregressive_masked_byte | scientifically invalid | scientifically_invalid | 0.1076 | 1 | 1.15e+04 | 674.7 | 4.768e+06 | 2.481e+08 | 0 (2; screening) | 1.83757e+06 |  |
| EXP-20260830-0047 | bidirectional_markov_masked_byte | scientifically invalid | scientifically_invalid | 0.1097 | 1 | 3.036e+05 | 674.7 | 1.356e+08 | 6.529e+09 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0047 | parallel_markov_bp_masked_byte | scientifically invalid | scientifically_invalid | 0.1097 | 1 | 8.943e+05 | 674.7 | 2.001e+08 | 1.935e+10 | -0.003461 (2; screening) | 2.624e+06 |  |
| EXP-20260830-0047 | oracle_conditional_masked_byte | scientifically invalid | scientifically_invalid | 1 | 1 | 863.3 | 674.7 | 129.3 | 1.92e+07 | 0 (2; screening) | 526848 |  |

## heldout_parallel_masked_infilling_v2 / quick

Pareto axes: maximize `exact_span_accuracy`; minimize `bits_per_byte, worst_span_bits_per_byte, critical_path_steps, data_acquisition_ops, fit_ops, mean_query_ops, update_ops, workload_ops, workload_ops_r16, state_bytes, peak_state_bytes, mean_bytes_touched`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0053 | iterative_masked_learner | implementable | complete | 0.1867 | 1 | 3817 | 674.7 | 1.324e+06 | 8.276e+07 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0053 | one_pass_masked_learner | implementable | complete | 0.193 | 1 | 1798 | 184 | 5.734e+05 | 3.935e+07 | 0 (2; screening) | 526848 | yes |
| EXP-20260830-0053 | uniform_masked_byte | implementable | complete | 0.002604 | 1 | 863.3 | 674.7 | 129.3 | 1.92e+07 | 0 (2; screening) | 526848 | yes |
| EXP-20260830-0053 | empirical_unigram_masked_byte | implementable | complete | 0.1315 | 1 | 1452 | 674.7 | 2.649e+05 | 3.19e+07 | 0 (2; screening) | 526848 | yes |
| EXP-20260830-0053 | left_to_right_ppm_masked_byte | implementable | complete | 0.203 | 1 | 1.15e+04 | 674.7 | 4.768e+06 | 2.481e+08 | 0 (2; screening) | 1.43851e+06 | yes |
| EXP-20260830-0053 | context_tree_weighting_masked_byte | implementable | complete | 0.1715 | 1 | 1.15e+04 | 674.7 | 4.768e+06 | 2.481e+08 | 0 (2; screening) | 652328 |  |
| EXP-20260830-0053 | dense_autoregressive_masked_byte | implementable | complete | 0.1455 | 1 | 1.15e+04 | 674.7 | 4.768e+06 | 2.481e+08 | 0 (2; screening) | 1.83757e+06 |  |
| EXP-20260830-0053 | bidirectional_markov_masked_byte | implementable | complete | 0.1634 | 1 | 3.036e+05 | 674.7 | 1.356e+08 | 6.529e+09 | 0 (2; screening) | 526848 |  |
| EXP-20260830-0053 | parallel_markov_bp_masked_byte | implementable | complete | 0.1634 | 1 | 8.959e+05 | 674.7 | 2.005e+08 | 1.938e+10 | -0.002931 (2; screening) | 2.624e+06 |  |
| EXP-20260830-0053 | oracle_conditional_masked_byte | privileged support control | complete | 1 | 1 | 863.3 | 674.7 | 129.3 | 1.92e+07 | 0 (2; screening) | 526848 |  |

## heldout_repository_sequence_compression_v1 / quick

Pareto axes: maximize `none`; minimize `none`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0044 | hierarchical_motif_compressor | implementable | complete | 0.2843 | 1 | 2389 | 3.667 | 9573 | 1.995e+08 | 0 (2; screening) | 3.56995e+06 |  |
| EXP-20260830-0044 | uniform_byte | implementable | complete | 0 | 1 | 1 | 3.667 | 0.5 | 4.49e+05 | 0 (2; screening) | 256 |  |
| EXP-20260830-0044 | empirical_unigram_byte | implementable | complete | 0.2069 | 1 | 2389 | 3.667 | 9565 | 1.961e+08 | 0 (2; screening) | 32488 |  |
| EXP-20260830-0044 | ppm_byte | implementable | complete | 0.3715 | 1 | 2389 | 3.667 | 9573 | 1.964e+08 | 0 (2; screening) | 3.56995e+06 |  |
| EXP-20260830-0044 | context_tree_weighting_byte | implementable | complete | 0.2802 | 1 | 2389 | 3.667 | 9573 | 1.964e+08 | 0 (2; screening) | 3.56995e+06 |  |
| EXP-20260830-0044 | lz_dictionary_byte | implementable | complete | 0.3078 | 1 | 259.7 | 3.667 | 1070 | 2.173e+07 | 0 (2; screening) | 2.30834e+06 |  |
| EXP-20260830-0044 | dense_autoregressive_byte | implementable | complete | 0.2165 | 1 | 5035 | 3.667 | 2.015e+04 | 4.129e+08 | 0 (2; screening) | 1.59528e+06 |  |
| EXP-20260830-0044 | oracle_test_table_byte | privileged support control | complete | 0.2069 | 1 | 256 | 3.667 | 128 | 2.134e+07 | 0 (2; screening) | 256 |  |

## heldout_three_family_continuous_transfer_v1 / quick

Pareto axes: maximize `transfer_accuracy, minimum_family_accuracy, stable_rollout_rate, shared_vs_independent_gain, cross_family_transfer_gain`; minimize `normalized_rmse, data_acquisition_ops, preprocessing_ops, fit_ops, adaptation_ops, mean_query_ops, state_bytes, peak_state_bytes, mean_bytes_touched, workload_ops_r1, workload_ops_r4, workload_ops_r16`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260831-0001 | shared_tensor_dynamics_v1 | implementable | complete | 0.3751 | 1 | 6083 | 4096 | 2.427e+04 | 1.079e+10 | 0 (2; screening) | 42240 |  |
| EXP-20260831-0001 | independent_tensor_dynamics_v1 | implementable | complete | 0.1413 | 1 | 6083 | 4096 | 2.427e+04 | 1.079e+10 | 0 (2; screening) | 126720 |  |
| EXP-20260831-0001 | cross_family_only_tensor_dynamics_v1 | implementable | complete | 0.1886 | 1 | 6083 | 4096 | 2.427e+04 | 1.08e+10 | 0 (2; screening) | 126720 |  |
| EXP-20260831-0001 | support_only_tensor_dynamics_v1 | implementable | complete | 0.3012 | 1 | 6083 | 4096 | 2.427e+04 | 1.074e+10 | 0 (2; screening) | 0 |  |
| EXP-20260831-0001 | tensor_persistence_v1 | implementable | complete | 0.5247 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0001 | tensor_ridge_arx_v1 | implementable | complete | 0.2652 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0001 | tensor_rls_arx_v1 | implementable | complete | 0.2652 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0001 | tensor_empirical_gaussian_joint_v1 | implementable | complete | 0.2636 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0001 | tensor_contextual_gaussian_chow_liu_v1 | implementable | complete | 0.41 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0001 | tensor_autoregressive_v1 | implementable | complete | 0.2652 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0001 | privileged_tensor_support_v1 | privileged support control | complete | 0.3274 | 1 | 6083 | 4096 | 2.33e+04 | 9.695e+09 | 0 (2; screening) | 1.13633e+07 |  |

## heldout_three_family_continuous_transfer_v2 / quick

Pareto axes: maximize `transfer_accuracy, minimum_family_accuracy, stable_rollout_rate`; minimize `normalized_rmse, data_acquisition_ops, preprocessing_ops, fit_ops, adaptation_ops, mean_query_ops, state_bytes, peak_state_bytes, mean_bytes_touched, workload_ops_r1, workload_ops_r4, workload_ops_r16`.

Promotion-only gates (not Pareto axes): `shared_vs_independent_gain, cross_family_transfer_gain`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260831-0002 | shared_tensor_dynamics_v1 | implementable | complete | 0.6199 | 1 | 3500 | 4096 | 2.338e+04 | 9.71e+09 | 0 (2; screening) | 24 |  |
| EXP-20260831-0002 | independent_tensor_dynamics_v1 | implementable | complete | 0.2847 | 1 | 3500 | 4096 | 2.338e+04 | 9.71e+09 | 0 (2; screening) | 72 |  |
| EXP-20260831-0002 | cross_family_only_tensor_dynamics_v1 | implementable | complete | 0.3515 | 1 | 3500 | 4096 | 2.338e+04 | 9.71e+09 | 0 (2; screening) | 72 |  |
| EXP-20260831-0002 | support_only_tensor_dynamics_v1 | implementable | complete | 0.3225 | 1 | 3500 | 4096 | 2.338e+04 | 9.71e+09 | 0 (2; screening) | 0 |  |
| EXP-20260831-0002 | tensor_persistence_v1 | implementable | complete | 0.5253 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0002 | tensor_ridge_arx_v1 | implementable | complete | 0.2663 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0002 | tensor_rls_arx_v1 | implementable | complete | 0.2663 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0002 | tensor_empirical_gaussian_joint_v1 | implementable | complete | 0.2644 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0002 | tensor_contextual_gaussian_chow_liu_v1 | implementable | complete | 0.4112 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0002 | tensor_autoregressive_v1 | implementable | complete | 0.2663 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0002 | privileged_tensor_support_v1 | privileged support control | complete | 0.3294 | 1 | 6083 | 4096 | 2.33e+04 | 9.695e+09 | 0 (2; screening) | 1.13633e+07 |  |
| EXP-20260831-0003 | shared_tensor_dynamics_v1 | implementable | complete | 0.3729 | 1 | 2.785e+04 | 4096 | 1.211e+05 | 9.906e+09 | 0 (2; screening) | 25368 |  |
| EXP-20260831-0003 | independent_tensor_dynamics_v1 | implementable | complete | 0.1377 | 1 | 2.785e+04 | 4096 | 1.211e+05 | 9.906e+09 | 0 (2; screening) | 76104 |  |
| EXP-20260831-0003 | cross_family_only_tensor_dynamics_v1 | implementable | complete | 0.1675 | 1 | 2.785e+04 | 4096 | 1.211e+05 | 9.907e+09 | 0 (2; screening) | 76104 |  |
| EXP-20260831-0003 | support_only_tensor_dynamics_v1 | implementable | complete | 0.3266 | 1 | 2.785e+04 | 4096 | 1.211e+05 | 9.906e+09 | 0 (2; screening) | 76032 |  |
| EXP-20260831-0003 | tensor_persistence_v1 | implementable | complete | 0.5264 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0003 | tensor_ridge_arx_v1 | implementable | complete | 0.2661 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0003 | tensor_rls_arx_v1 | implementable | complete | 0.2661 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0003 | tensor_empirical_gaussian_joint_v1 | implementable | complete | 0.2641 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0003 | tensor_contextual_gaussian_chow_liu_v1 | implementable | complete | 0.4112 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0003 | tensor_autoregressive_v1 | implementable | complete | 0.2661 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (2; screening) | 746496 |  |
| EXP-20260831-0003 | privileged_tensor_support_v1 | privileged support control | complete | 0.328 | 1 | 6083 | 4096 | 2.33e+04 | 9.695e+09 | 0 (2; screening) | 1.13633e+07 |  |

## heldout_three_family_continuous_transfer_v3 / quick

Pareto axes unavailable: no scientifically valid immutable result.

Promotion-only gates (not Pareto axes): `shared_vs_independent_gain, cross_family_transfer_gain`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260831-0004 | shared_predictive_index_v1 | scientifically invalid | scientifically_invalid | - | 1 | - | - | - | - | - (3) | - |  |
| EXP-20260831-0004 | independent_predictive_index_v1 | scientifically invalid | scientifically_invalid | - | 1 | - | - | - | - | - (3) | - |  |
| EXP-20260831-0004 | cross_family_only_predictive_index_v1 | scientifically invalid | scientifically_invalid | - | 1 | - | - | - | - | - (3) | - |  |
| EXP-20260831-0004 | support_only_predictive_index_v1 | scientifically invalid | scientifically_invalid | 0.3532 | 1 | 4.54e+04 | 4096 | 5.524e+05 | 9.958e+09 | 0 (3) | 818808 |  |
| EXP-20260831-0004 | tensor_persistence_v1 | scientifically invalid | scientifically_invalid | 0.5261 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0004 | tensor_ridge_arx_v1 | scientifically invalid | scientifically_invalid | 0.2855 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0004 | tensor_rls_arx_v1 | scientifically invalid | scientifically_invalid | 0.2855 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0004 | tensor_empirical_gaussian_joint_v1 | scientifically invalid | scientifically_invalid | 0.282 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0004 | tensor_contextual_gaussian_chow_liu_v1 | scientifically invalid | scientifically_invalid | 0.3851 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0004 | tensor_autoregressive_v1 | scientifically invalid | scientifically_invalid | 0.2855 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0004 | tensor_raw_window_local_linear_v1 | scientifically invalid | scientifically_invalid | 0.3765 | 1 | 1.652e+05 | 4096 | 8.32e+05 | 1.028e+10 | 0 (3) | 427712 |  |
| EXP-20260831-0004 | tensor_random_projection_hash_v1 | scientifically invalid | scientifically_invalid | - | 1 | - | - | - | - | - (3) | - |  |
| EXP-20260831-0004 | privileged_tensor_support_v1 | scientifically invalid | scientifically_invalid | 0.3268 | 1 | 6083 | 4096 | 2.33e+04 | 9.695e+09 | 0 (3) | 1.13633e+07 |  |

## heldout_three_family_continuous_transfer_v4 / quick

Pareto axes: maximize `transfer_accuracy, minimum_family_accuracy, stable_rollout_rate`; minimize `normalized_rmse, data_acquisition_ops, preprocessing_ops, fit_ops, adaptation_ops, mean_query_ops, state_bytes, peak_state_bytes, mean_bytes_touched, workload_ops_r1, workload_ops_r4, workload_ops_r16`.

Promotion-only gates (not Pareto axes): `shared_vs_independent_gain, cross_family_transfer_gain`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260831-0005 | shared_predictive_index_v1 | implementable | complete | 0.3853 | 1 | 4.54e+04 | 4096 | 5.524e+05 | 1e+10 | 0 (3) | 303464 |  |
| EXP-20260831-0005 | independent_predictive_index_v1 | implementable | complete | 0.3255 | 1 | 4.54e+04 | 4096 | 5.524e+05 | 1.006e+10 | 0 (3) | 889080 |  |
| EXP-20260831-0005 | cross_family_only_predictive_index_v1 | implementable | complete | 0.2097 | 1 | 4.54e+04 | 4096 | 5.524e+05 | 9.999e+09 | 0 (3) | 910392 |  |
| EXP-20260831-0005 | support_only_predictive_index_v1 | implementable | complete | 0.3556 | 1 | 4.54e+04 | 4096 | 5.524e+05 | 9.958e+09 | 0 (3) | 818808 |  |
| EXP-20260831-0005 | tensor_persistence_v1 | implementable | complete | 0.5254 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0005 | tensor_ridge_arx_v1 | implementable | complete | 0.2855 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0005 | tensor_rls_arx_v1 | implementable | complete | 0.2855 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0005 | tensor_empirical_gaussian_joint_v1 | implementable | complete | 0.2817 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0005 | tensor_contextual_gaussian_chow_liu_v1 | implementable | complete | 0.3858 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0005 | tensor_autoregressive_v1 | implementable | complete | 0.2855 | 1 | 6083 | 4096 | 2.33e+04 | 9.692e+09 | 0 (3) | 746496 |  |
| EXP-20260831-0005 | tensor_raw_window_local_linear_v1 | implementable | complete | 0.38 | 1 | 1.652e+05 | 4096 | 8.32e+05 | 1.028e+10 | 0 (3) | 427712 |  |
| EXP-20260831-0005 | tensor_random_projection_hash_v1 | implementable | complete | 0.3627 | 1 | 2.755e+04 | 4096 | 4.864e+05 | 9.791e+09 | 0 (3) | 296960 |  |
| EXP-20260831-0005 | privileged_tensor_support_v1 | privileged support control | complete | 0.3269 | 1 | 6083 | 4096 | 2.33e+04 | 9.695e+09 | 0 (3) | 1.13633e+07 |  |

## heldout_wt_changepoints_prequential_v1 / quick

Pareto axes: maximize `stable_rollout_rate`; minimize `normalized_rmse, worst_file_normalized_rmse, worst_transition_normalized_rmse, rollout_16_nrmse, rollout_32_nrmse, rollout_96_nrmse, data_acquisition_ops, preprocessing_ops, fit_ops, adaptation_ops, mean_query_ops, update_ops, state_bytes, peak_state_bytes, mean_bytes_touched, workload_ops_r1, workload_ops_r4, workload_ops_r16`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260831-0006 | wt_candidate_under_test | implementable | complete | 0.5979 | 1 | 2.256e+04 | 321 | 2.406e+04 | 1.668e+07 | 0 (3) | 16896 | yes |
| EXP-20260831-0006 | wt_persistence_v1 | implementable | complete | 0.4816 | 1 | 960 | 321 | 1.024e+04 | 7.599e+06 | 0 (3) | 0 | yes |
| EXP-20260831-0006 | wt_pooled_mean_v1 | implementable | complete | 0.4882 | 1 | 960 | 321 | 1.024e+04 | 7.61e+06 | 0 (3) | 2560 | yes |
| EXP-20260831-0006 | wt_control_level_bank_v1 | implementable | complete | 0.4988 | 1 | 1920 | 321 | 1.024e+04 | 7.887e+06 | 0 (3) | 10240 | yes |
| EXP-20260831-0006 | wt_lms_v1 | implementable | complete | 0.4237 | 1 | 6.144e+04 | 321 | 9.216e+04 | 2.573e+07 | 0 (3) | 253952 |  |
| EXP-20260831-0006 | wt_rls_v1 | implementable | complete | 0.4251 | 1 | 6.144e+04 | 321 | 1.004e+05 | 2.58e+07 | 0 (3) | 270336 |  |
| EXP-20260831-0006 | wt_transition_bank_v1 | implementable | complete | 0.49 | 1 | 2040 | 321 | 1.237e+04 | 7.944e+06 | -6.39e-31 (3) | 105168 |  |
| EXP-20260831-0006 | wt_bounded_replay_v1 | implementable | complete | 0.4482 | 1 | 7072 | 321 | 1.664e+04 | 9.378e+06 | 0 (3) | 264448 |  |
| EXP-20260831-0006 | wt_ridge_fir_v1 | implementable | complete | 0.4139 | 1 | 6.144e+04 | 321 | 1.024e+04 | 2.542e+07 | 0 (3) | 90112 |  |

## heterogeneous_module_composition_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0021.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0021 | random_module_router | implementable | complete | 0 | 1 | 75.17 | - | - | - | -0.005598 (2; screening) | 11936 |  |
| EXP-20260830-0021 | primitive_demo_memorizer | implementable | complete | 0 | 1 | 63.33 | - | - | - | 0 (2; screening) | 17472 |  |
| EXP-20260830-0021 | dense_shared_transform | implementable | complete | 0 | 1 | 3.013e+04 | - | - | - | 0 (2; screening) | 33792 |  |
| EXP-20260830-0021 | dense_expert_sweep | implementable | complete | 1 | 1 | 2570 | - | - | - | 0.9684 (2; screening) | 1024 |  |
| EXP-20260830-0021 | direct_program_index | implementable | complete | 1 | 1 | 70.96 | - | - | - | 0 (2; screening) | 11360 |  |
| EXP-20260830-0021 | learned_sparse_modules | implementable | complete | 1 | 1 | 74.62 | - | - | - | 0 (2; screening) | 11936 |  |
| EXP-20260830-0021 | oracle_sparse_modules | privileged support control | complete | 1 | 1 | 74.62 | - | - | - | 0 (2; screening) | 11936 |  |

## latent_causal_transfer_adversarial_v2 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0015.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0015 | random_latent_independent | implementable | complete | 0.4583 | 1 | 1 | - | - | - | 0 (2; screening) | 2832 |  |
| EXP-20260830-0015 | latent_majority_guess | implementable | complete | 0.5 | 1 | 1 | - | - | - | 0 (2; screening) | 2832 |  |
| EXP-20260830-0015 | latent_parity_shortcut | implementable | complete | 0.5417 | 1 | 5 | - | - | - | 0 (2; screening) | 2832 |  |
| EXP-20260830-0015 | raw_episode_predictor | implementable | complete | 0.4792 | 1 | 7.116e+04 | - | - | - | 0.9895 (2; screening) | 1.03002e+06 |  |
| EXP-20260830-0015 | latent_factorized_mixed | implementable | complete | 1 | 1 | 73.67 | - | - | - | 0.4878 (2; screening) | 2.03774e+06 |  |
| EXP-20260830-0015 | oracle_representation_mixed | privileged support control | complete | 1 | 1 | 73.67 | - | - | - | 0.4878 (2; screening) | 2.04219e+06 |  |
| EXP-20260830-0015 | oracle_latent_mixed | privileged support control | complete | 1 | 1 | 73.67 | - | - | - | 0.4878 (2; screening) | 8576 |  |

## latent_causal_transfer_adversarial_v2 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0016.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0016 | random_latent_independent | implementable | complete | 0.3056 | 3 | 1 | - | - | - | 0 (3) | 2880 |  |
| EXP-20260830-0016 | latent_majority_guess | implementable | complete | 0.5 | 3 | 1 | - | - | - | 0 (3) | 2880 |  |
| EXP-20260830-0016 | latent_parity_shortcut | implementable | complete | 0.3333 | 3 | 5 | - | - | - | 0 (3) | 2880 |  |
| EXP-20260830-0016 | raw_episode_predictor | implementable | complete | 0.5278 | 3 | 6.234e+05 | - | - | - | 1.182 (3) | 1.35316e+07 |  |
| EXP-20260830-0016 | latent_factorized_mixed | implementable | complete | 1 | 3 | 149.1 | - | - | - | 0.6161 (3) | 1.79323e+07 |  |
| EXP-20260830-0016 | oracle_representation_mixed | privileged support control | complete | 1 | 3 | 149.1 | - | - | - | 0.6161 (3) | 1.79416e+07 |  |
| EXP-20260830-0016 | oracle_latent_mixed | privileged support control | complete | 1 | 3 | 149.1 | - | - | - | 0.6161 (3) | 17504 |  |

## latent_causal_transfer_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0014.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0014 | random_latent_guess | implementable | complete | 0.6667 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0014 | raw_episode_predictor | implementable | complete | 0 | 1 | 7.111e+04 | - | - | - | 0.9904 (2; screening) | 1.02945e+06 |  |
| EXP-20260830-0014 | latent_factorized_causal | implementable | complete | 1 | 1 | 88.33 | - | - | - | 0.4021 (2; screening) | 2.03784e+06 |  |
| EXP-20260830-0014 | oracle_representation_causal | privileged support control | complete | 1 | 1 | 88.33 | - | - | - | 0.4021 (2; screening) | 2.04224e+06 |  |
| EXP-20260830-0014 | oracle_latent_causal | privileged support control | complete | 1 | 1 | 88.33 | - | - | - | 0.4021 (2; screening) | 8576 |  |

## latent_entity_binding_retrieval_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0035.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0035 | random_view_binding | implementable | complete | 0 | 1 | 12 | 12 | 96 | - | 0 (2; screening) | 392 |  |
| EXP-20260830-0035 | raw_view_nearest | implementable | complete | 0.1458 | 1 | 3532 | 12 | 7136 | - | 0.9954 (2; screening) | 13288 |  |
| EXP-20260830-0035 | raw_sign_lsh | implementable | complete | 0.02083 | 1 | 19.33 | 12 | 184 | - | 0 (2; screening) | 1408 |  |
| EXP-20260830-0035 | probabilistic_linkage_scan | implementable | complete | 1 | 1 | 3532 | 12 | 7136 | - | 0.9954 (2; screening) | 13288 |  |
| EXP-20260830-0035 | paired_stability_index | implementable | complete | 1 | 1 | 19.33 | 12 | 184 | - | 0 (2; screening) | 1360 |  |
| EXP-20260830-0035 | contrastive_hash_index | implementable | complete | 0.5417 | 1 | 19.33 | 12 | 184 | - | 0 (2; screening) | 1360 |  |
| EXP-20260830-0035 | oracle_identity_index | privileged support control | complete | 1 | 1 | 15.67 | 12 | 154.7 | - | 0 (2; screening) | 984 |  |

## noisy_nonexhaustive_causal_transfer_v3 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0020.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0020 | random_latent_independent | implementable | complete | 0.4583 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0020 | latent_majority_guess | implementable | complete | 0.5 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0020 | dense_random_feature_causal | implementable | complete | 0.5625 | 1 | 2.334e+04 | - | - | - | 0.3904 (2; screening) | 121664 |  |
| EXP-20260830-0020 | noisy_factorized_dense | implementable | complete | 0.04167 | 1 | 58.85 | - | - | - | 0.7275 (2; screening) | 1072 |  |
| EXP-20260830-0020 | noisy_factorized_local | implementable | complete | 0.04167 | 1 | 54.79 | - | - | - | 0.701 (2; screening) | 1072 |  |
| EXP-20260830-0020 | oracle_representation_noisy | privileged support control | crash | - | 1 | - | - | - | - | - (2; screening) | - |  |
| EXP-20260830-0020 | oracle_noisy_causal | privileged support control | complete | 1 | 1 | 79.67 | - | - | - | 0.4485 (2; screening) | 3440 |  |

## nonlinear_local_state_transfer_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0034.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0034 | random_local_state | implementable | complete | 0 | 1 | 123 | 120 | - | - | 0.9675 (2; screening) | 1664 |  |
| EXP-20260830-0034 | stateless_graph_bfs | implementable | complete | 0.2917 | 1 | 175 | 120 | - | - | 0.6309 (2; screening) | 2132 |  |
| EXP-20260830-0034 | exact_finite_state_propagation | implementable | complete | 1 | 1 | 186 | 120 | - | - | 0.5892 (2; screening) | 4888 |  |
| EXP-20260830-0034 | learned_dense_nca | implementable | complete | 1 | 1 | 1.692e+05 | 120 | - | - | 1 (2; screening) | 12112 |  |
| EXP-20260830-0034 | learned_sparse_event_nca | implementable | complete | 1 | 1 | 8597 | 120 | - | - | 0.01208 (2; screening) | 12112 |  |
| EXP-20260830-0034 | oracle_local_state_rule | privileged support control | complete | 1 | 1 | 193.3 | 120 | - | - | 0.5644 (2; screening) | 1728 |  |

## nonstationary_online_update_battery_v1 / quick

Pareto axes: maximize `none`; minimize `none`.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0043 | no_update_online | implementable | complete | 0.00394 | 1 | 1 | 20 | 4 | 2.136e+04 | 0 (2; screening) | 16 |  |
| EXP-20260830-0043 | delta_lms_online | implementable | complete | 0.1548 | 1 | 42 | 20 | 336 | 1.98e+05 | 0.9372 (2; screening) | 856 |  |
| EXP-20260830-0043 | rls_kalman_online | implementable | complete | 0.1035 | 1 | 42 | 20 | 4848 | 7.182e+05 | 0.9372 (2; screening) | 26992 |  |
| EXP-20260830-0043 | polynomial_rls_online | implementable | complete | 0.08265 | 1 | 606 | 20 | 4848 | 2.979e+06 | 1.82 (2; screening) | 26992 |  |
| EXP-20260830-0043 | kernel_dictionary_online | implementable | complete | 0.05429 | 1 | 1577 | 20 | 4177 | 6.008e+06 | 0.9219 (2; screening) | 25408 |  |
| EXP-20260830-0043 | changepoint_bank_rls_online | implementable | complete | 0.1131 | 1 | 42 | 20 | 1.351e+04 | 7.454e+05 | 0.9372 (2; screening) | 80880 |  |
| EXP-20260830-0043 | bounded_replay_online | implementable | complete | 0.05118 | 1 | 1577 | 20 | 4177 | 6.008e+06 | 0.9219 (2; screening) | 25408 |  |
| EXP-20260830-0043 | additive_fast_weights_online | implementable | complete | 0.037 | 1 | 606 | 20 | 4848 | 2.626e+06 | 1.82 (2; screening) | 13528 |  |
| EXP-20260830-0043 | delta_fast_weights_online | implementable | complete | 0.06725 | 1 | 606 | 20 | 4848 | 2.626e+06 | 1.82 (2; screening) | 13528 |  |
| EXP-20260830-0043 | independent_meta_update | implementable | complete | 0.06601 | 1 | 606 | 20 | 4384 | 2.173e+07 | 1.82 (2; screening) | 31544 |  |
| EXP-20260830-0043 | shared_meta_update | implementable | complete | 0.05455 | 1 | 606 | 20 | 4392 | 2.173e+07 | 1.82 (2; screening) | 31544 |  |
| EXP-20260830-0043 | oracle_segmented_online | privileged support control | complete | 1 | 1 | 42 | 20 | 160 | 1.731e+05 | 0.9372 (2; screening) | 64 |  |

## opaque_alias_acquisition_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0025.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0025 | random_alias_guess | implementable | complete | 0 | 1 | 173.7 | 172.7 | - | 3021 | 0.8979 (2; screening) | 64 |  |
| EXP-20260830-0025 | opaque_full_evaluator | implementable | complete | 1 | 1 | 268.7 | 172.7 | - | 5292 | 0.5393 (2; screening) | 64 |  |
| EXP-20260830-0025 | opaque_exact_key_cache | implementable | complete | 1 | 1 | 268.7 | 172.7 | - | 3314 | 0.5393 (2; screening) | 44480 |  |
| EXP-20260830-0025 | independent_frequency_cache | implementable | complete | 1 | 1 | 1497 | 172.7 | - | 2.88e+04 | 1.443 (2; screening) | 104 |  |
| EXP-20260830-0025 | soft_unification_result_cache | implementable | complete | 1 | 1 | 1.873e+04 | 172.7 | - | 3.542e+05 | 2.602 (2; screening) | 2144 |  |
| EXP-20260830-0025 | soft_unification_dependency_trace | implementable | complete | 1 | 1 | 1.873e+04 | 172.7 | - | 3.542e+05 | 2.594 (2; screening) | 9816 |  |
| EXP-20260830-0025 | exact_constraint_result_cache | implementable | complete | 1 | 1 | 3173 | 172.7 | - | 5.87e+04 | 1.623 (2; screening) | 1856 |  |
| EXP-20260830-0025 | exact_constraint_dependency_trace | implementable | complete | 1 | 1 | 3183 | 172.7 | - | 5.866e+04 | 1.611 (2; screening) | 9720 |  |
| EXP-20260830-0025 | mapping_oracle_dependency_trace | privileged support control | complete | 1 | 1 | 342.7 | 172.7 | - | 4702 | 0.4092 (2; screening) | 9720 |  |

## pointer_machine_composition_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0013.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0013 | random_pointer_guess | implementable | complete | 0.04167 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0013 | pointer_trace_memorizer | implementable | complete | 0 | 1 | 24.67 | - | - | - | 0.7667 (2; screening) | 5056 |  |
| EXP-20260830-0013 | dense_pointer_controller | implementable | complete | 1 | 1 | 82.5 | - | - | - | 0.8581 (2; screening) | 960 |  |
| EXP-20260830-0013 | learned_hard_pointer | implementable | complete | 1 | 1 | 12.83 | - | - | - | 0 (2; screening) | 808 |  |
| EXP-20260830-0013 | oracle_pointer_machine | privileged support control | complete | 1 | 1 | 9.167 | - | - | - | 0 (2; screening) | 272 |  |

## program_induction_from_whole_io_v2 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0022.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0022 | random_whole_io | implementable | complete | 0.5417 | 1 | 5.667 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0022 | nearest_whole_io | implementable | complete | 0.6667 | 1 | 306.3 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0022 | dense_whole_io | implementable | complete | 0.5417 | 1 | 5373 | - | - | - | 0.4126 (2; screening) | 24192 |  |
| EXP-20260830-0022 | enumerative_mdl_vm | implementable | complete | 1 | 1 | 1.284e+05 | - | - | - | 0 (2; screening) | 1448 |  |
| EXP-20260830-0022 | learned_latent_vm | implementable | complete | 0.9375 | 1 | 6.1e+05 | - | - | - | -0.0007844 (2; screening) | 1576 |  |
| EXP-20260830-0022 | oracle_latent_vm | privileged support control | complete | 1 | 1 | 23 | - | - | - | 0 (2; screening) | 72 |  |

## program_library_adversarial_v2 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0008.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0008 | random_program_guess | implementable | complete | 0.01389 | 3 | 1 | - | - | - | 0 (3) | 1504 |  |
| EXP-20260830-0008 | primitive_program_search | implementable | complete | 0.9931 | 3 | 8.212e+04 | - | - | - | 0 (3) | 1504 |  |
| EXP-20260830-0008 | exact_program_memo | implementable | complete | 0.9931 | 3 | 8.212e+04 | - | - | - | 0 (3) | 2336 |  |
| EXP-20260830-0008 | mismatched_library_search | implementable | complete | 0.9861 | 3 | 1.695e+05 | - | - | - | -2.052e-31 (3) | 1504 |  |
| EXP-20260830-0008 | oracle_library_search | privileged support control | complete | 0.9931 | 3 | 3.35e+04 | - | - | - | 0 (3) | 1504 |  |
| EXP-20260830-0008 | learned_library_search | implementable | complete | 0.9931 | 3 | 3.35e+04 | - | - | - | 0 (3) | 25624 |  |

## program_library_identifiable_v3 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0009.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0009 | random_program_guess | implementable | complete | 0.03472 | 3 | 1 | - | - | - | 0 (3) | 1504 |  |
| EXP-20260830-0009 | primitive_program_search | implementable | complete | 1 | 3 | 8.272e+04 | - | - | - | 2.052e-31 (3) | 1504 |  |
| EXP-20260830-0009 | exact_program_memo | implementable | complete | 1 | 3 | 8.272e+04 | - | - | - | 2.052e-31 (3) | 2336 |  |
| EXP-20260830-0009 | mismatched_library_search | implementable | complete | 1 | 3 | 1.764e+05 | - | - | - | 0 (3) | 1504 |  |
| EXP-20260830-0009 | oracle_library_search | privileged support control | complete | 1 | 3 | 3.406e+04 | - | - | - | 0 (3) | 1504 |  |
| EXP-20260830-0009 | learned_library_search | implementable | complete | 1 | 3 | 3.406e+04 | - | - | - | 0 (3) | 25624 |  |

## program_library_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0007.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0007 | random_program_guess | implementable | complete | 0.04167 | 1 | 1 | - | - | - | 0 (2; screening) | 800 |  |
| EXP-20260830-0007 | primitive_program_search | implementable | complete | 1 | 1 | 4718 | - | - | - | 0 (2; screening) | 800 |  |
| EXP-20260830-0007 | exact_program_memo | implementable | complete | 1 | 1 | 4718 | - | - | - | 0 (2; screening) | 1696 |  |
| EXP-20260830-0007 | mismatched_library_search | implementable | complete | 1 | 1 | 9134 | - | - | - | 0 (2; screening) | 800 |  |
| EXP-20260830-0007 | oracle_library_search | privileged support control | complete | 1 | 1 | 198.6 | - | - | - | 0 (2; screening) | 800 |  |
| EXP-20260830-0007 | learned_library_search | implementable | complete | 1 | 1 | 198.6 | - | - | - | 0 (2; screening) | 6780 |  |

## raw_byte_motif_composition_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0026.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0026 | random_byte_guess | implementable | complete | 0 | 1 | 30.62 | 26.96 | - | 613.7 | 0 (2; screening) | 64 |  |
| EXP-20260830-0026 | raw_support_rescan | implementable | complete | 1 | 1 | 9005 | 26.96 | - | 1.532e+05 | 0.3529 (2; screening) | 1684 |  |
| EXP-20260830-0026 | fixed_trigram_composer | implementable | complete | 1 | 1 | 221.4 | 26.96 | - | 6439 | 0 (2; screening) | 236 |  |
| EXP-20260830-0026 | lz_phrase_composer | implementable | complete | 1 | 1 | 210.6 | 26.96 | - | 4.71e+05 | 0 (2; screening) | 246 |  |
| EXP-20260830-0026 | sequitur_grammar_composer | implementable | complete | 0.6458 | 1 | 205.5 | 26.96 | - | 1.695e+05 | -0.03569 (2; screening) | 246 |  |
| EXP-20260830-0026 | dense_recurrent_composer | implementable | complete | 0.04167 | 1 | 4665 | 26.96 | - | 1.61e+05 | 0 (2; screening) | 31408 |  |
| EXP-20260830-0026 | contrastive_motif_composer | implementable | complete | 1 | 1 | 210.6 | 26.96 | - | 3.59e+04 | 0 (2; screening) | 246 |  |
| EXP-20260830-0026 | exact_suffix_composer | implementable | complete | 1 | 1 | 59.62 | 26.96 | - | 1.01e+04 | 0 (2; screening) | 608 |  |
| EXP-20260830-0026 | oracle_motif_composer | privileged support control | complete | 1 | 1 | 59.62 | 26.96 | - | 1219 | 0 (2; screening) | 608 |  |

## routed_vsa_capacity_scaling_v2 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0032.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0032 | random_vsa_capacity | implementable | complete | 0.05787 | 3 | 2 | 1 | 8 | - | 0 (3) | 128 |  |
| EXP-20260830-0032 | exact_tuple_store_vsa | implementable | complete | 1 | 3 | 4.75 | 1 | 76 | - | 2.565e-32 (3) | 2304 |  |
| EXP-20260830-0032 | global_vsa_r8 | implementable | complete | 0.2801 | 3 | 4.469e+05 | 1 | 2.32e+05 | - | 1.96 (3) | 137728 |  |
| EXP-20260830-0032 | global_vsa_r32 | implementable | complete | 0.9907 | 3 | 1.788e+06 | 1 | 9.278e+05 | - | 1.96 (3) | 543232 |  |
| EXP-20260830-0032 | bucketed_vsa_r32 | implementable | complete | 0.4815 | 3 | 3.528e+05 | 1 | 4.768e+05 | - | 1.452 (3) | 740864 |  |
| EXP-20260830-0032 | learned_routed_vsa_r32 | implementable | complete | 1 | 3 | 3.526e+05 | 1 | 4.767e+05 | - | 1.452 (3) | 740864 |  |
| EXP-20260830-0032 | dense_associative_vsa_r32 | implementable | complete | 1 | 3 | 1.779e+06 | 1 | 8.938e+05 | - | 1.98 (3) | 1.05114e+06 |  |
| EXP-20260830-0032 | oracle_routed_vsa_r32 | privileged support control | complete | 1 | 3 | 1.751e+05 | 1 | 1.216e+05 | - | 1.409 (3) | 544256 |  |

## semantic_reaction_composition_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0019.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0019 | random_reaction_guess | implementable | complete | 0 | 1 | 40 | - | - | - | 1 (2; screening) | 2920 |  |
| EXP-20260830-0019 | reaction_trajectory_memorizer | implementable | complete | 0 | 1 | 60 | - | - | - | 1 (2; screening) | 25184 |  |
| EXP-20260830-0019 | learned_reaction_sweep | implementable | complete | 1 | 1 | 106.3 | - | - | - | 0.635 (2; screening) | 2464 |  |
| EXP-20260830-0019 | learned_reaction_recurrent | implementable | complete | 1 | 1 | 133.3 | - | - | - | 0.08057 (2; screening) | 2464 |  |
| EXP-20260830-0019 | rete_reaction_engine | implementable | complete | 1 | 1 | 53 | - | - | - | 0.3324 (2; screening) | 2464 |  |
| EXP-20260830-0019 | learned_semantic_reactor | implementable | complete | 1 | 1 | 53 | - | - | - | 0.3324 (2; screening) | 2464 |  |
| EXP-20260830-0019 | oracle_reaction_engine | privileged support control | complete | 1 | 1 | 53 | - | - | - | 0.3324 (2; screening) | 2464 |  |

## semantic_trace_compilation_adversarial_v2 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0024.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0024 | random_trace_guess | implementable | complete | 0.002315 | 3 | 129.5 | 128.5 | - | 2279 | 0.7573 (3) | 64 |  |
| EXP-20260830-0024 | exact_key_trace_cache | implementable | complete | 1 | 3 | 256.5 | 128.5 | - | 2716 | 0.3298 (3) | 5008 |  |
| EXP-20260830-0024 | indexed_dag_planner | implementable | complete | 1 | 3 | 256.5 | 128.5 | - | 5130 | 0.3298 (3) | 64 |  |
| EXP-20260830-0024 | canonical_result_cache | implementable | complete | 1 | 3 | 289.5 | 128.5 | - | 3494 | 0.2909 (3) | 12736 |  |
| EXP-20260830-0024 | dependency_trace_compiler | implementable | complete | 1 | 3 | 289.5 | 128.5 | - | 3430 | 0.2909 (3) | 44800 |  |
| EXP-20260830-0024 | rewrite_normal_form_result_cache | implementable | complete | 1 | 3 | 333.2 | 128.5 | - | 4154 | 0.2521 (3) | 3520 |  |
| EXP-20260830-0024 | rewrite_normal_form_dependency_trace | implementable | complete | 1 | 3 | 341.2 | 128.5 | - | 4098 | 0.2461 (3) | 20128 |  |
| EXP-20260830-0024 | oracle_equivalence_trace | privileged support control | complete | 1 | 3 | 1 | 0 | - | 18 | 0 (3) | 64 |  |

## semantic_trace_compilation_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0023.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0023 | random_trace_guess | implementable | complete | 0 | 1 | 41 | 40 | - | - | 0.9675 (2; screening) | 64 |  |
| EXP-20260830-0023 | exact_key_trace_cache | implementable | complete | 1 | 1 | 157.3 | 40 | - | - | 0.2218 (2; screening) | 1328 |  |
| EXP-20260830-0023 | indexed_dag_planner | implementable | complete | 1 | 1 | 157.3 | 40 | - | - | 0.2218 (2; screening) | 64 |  |
| EXP-20260830-0023 | canonical_result_cache | implementable | complete | 1 | 1 | 180 | 40 | - | - | 0.1935 (2; screening) | 2240 |  |
| EXP-20260830-0023 | dependency_trace_compiler | implementable | complete | 1 | 1 | 180 | 40 | - | - | 0.1935 (2; screening) | 6400 |  |
| EXP-20260830-0023 | oracle_trace_compiler | privileged support control | complete | 1 | 1 | 1 | 0 | - | - | 0 (2; screening) | 64 |  |

## shared_transition_adaptive_compute_v2 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0031.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0031 | random_shared_halt | implementable | complete | 0.4583 | 1 | 1967 | 20 | - | 3.794e+04 | 1.148 (2; screening) | 4160 |  |
| EXP-20260830-0031 | fixed_short_shared_transition | implementable | complete | 0.6667 | 1 | 2692 | 20 | - | 4.579e+04 | 0.984 (2; screening) | 4160 |  |
| EXP-20260830-0031 | fixed_max_shared_transition | implementable | complete | 1 | 1 | 4028 | 20 | - | 6.717e+04 | 0.984 (2; screening) | 4160 |  |
| EXP-20260830-0031 | residual_shared_transition | implementable | complete | 1 | 1 | 3324 | 20 | - | 5.59e+04 | 0.9849 (2; screening) | 4160 |  |
| EXP-20260830-0031 | transition_gate_halt | implementable | complete | 1 | 1 | 2794 | 20 | - | 4.742e+04 | 0.9837 (2; screening) | 4160 |  |
| EXP-20260830-0031 | learned_adaptive_halt | implementable | complete | 1 | 1 | 2873 | 20 | - | 4.869e+04 | 0.9478 (2; screening) | 4232 |  |
| EXP-20260830-0031 | act_ponder_halt | implementable | complete | 1 | 1 | 2901 | 20 | - | 4.914e+04 | 0.9358 (2; screening) | 4232 |  |
| EXP-20260830-0031 | oracle_shared_halt | privileged support control | complete | 1 | 1 | 2469 | 20 | - | 4.223e+04 | 0.984 (2; screening) | 4160 |  |

## successor_graph_v1 / quick

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0001, EXP-20260830-0003.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0001 | random_guess | implementable | complete | 0.01042 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0001 | linear_scan | implementable | complete | 1 | 1 | 577.4 | - | - | - | 0.9938 (2; screening) | 28840 |  |
| EXP-20260830-0001 | indexed_graph | implementable | complete | 1 | 1 | 7 | - | - | - | 0 (2; screening) | 18568 |  |
| EXP-20260830-0001 | memoized_graph | implementable | complete | 1 | 1 | 6.625 | - | - | - | 0.08175 (2; screening) | 19640 |  |
| EXP-20260830-0001 | compiled_jump | implementable | complete | 1 | 1 | 1 | - | - | - | 0 (2; screening) | 92584 |  |
| EXP-20260830-0001 | dense_recurrent | implementable | complete | 1 | 1 | 4.874e+05 | - | - | - | 2 (2; screening) | 264196 |  |
| EXP-20260830-0003 | random_guess | implementable | complete | 0.01042 | 1 | 1 | - | - | - | 0 (2; screening) | 64 |  |
| EXP-20260830-0003 | linear_scan | implementable | complete | 1 | 1 | 577.4 | - | - | - | 0.9938 (2; screening) | 28840 |  |
| EXP-20260830-0003 | indexed_graph | implementable | complete | 1 | 1 | 7 | - | - | - | 0 (2; screening) | 18568 |  |
| EXP-20260830-0003 | dense_recurrent | implementable | complete | 1 | 1 | 4.874e+05 | - | - | - | 2 (2; screening) | 264196 |  |
| EXP-20260830-0003 | vsa_superposition | implementable | complete | 0.5625 | 1 | 4.616e+06 | - | - | - | 0.9916 (2; screening) | 2.11382e+06 |  |

## successor_graph_v1 / screen

Pareto axes unavailable: immutable result lacks pareto_metrics: EXP-20260830-0002.

| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| EXP-20260830-0002 | random_guess | implementable | complete | 0.006076 | 3 | 1 | - | - | - | 0 (3) | 64 |  |
| EXP-20260830-0002 | linear_scan | implementable | complete | 1 | 3 | 4755 | - | - | - | 0.9938 (3) | 114856 |  |
| EXP-20260830-0002 | indexed_graph | implementable | complete | 1 | 3 | 21.25 | - | - | - | 0 (3) | 73864 |  |
| EXP-20260830-0002 | memoized_graph | implementable | complete | 1 | 3 | 18.01 | - | - | - | 0.1434 (3) | 74936 |  |
| EXP-20260830-0002 | compiled_jump | implementable | complete | 1 | 3 | 1 | - | - | - | 0 (3) | 516664 |  |
