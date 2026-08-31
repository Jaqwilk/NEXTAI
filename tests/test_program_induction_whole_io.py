from nextai_autoresearch.benchmarks.program_induction_from_whole_io_v2 import (
    make_tasks,
    meta_programs,
    run_trial,
    support_scores,
)
from nextai_autoresearch.whole_io_vm_core import PROGRAMS, active_bits, run_program


def test_scored_query_exposes_no_program_or_trace() -> None:
    task = make_tasks(8, 6, 1103, 1)[0]
    assert not hasattr(task.query, "program")
    assert not hasattr(task.query, "trace")
    assert task.program not in meta_programs(8, 1103)


def test_support_has_one_corruption_and_unique_true_mdl_program() -> None:
    task = make_tasks(8, 4, 1103, 1)[0]
    errors = sum(
        run_program(task.program, active_bits(item.tape)[0])[0] != item.target
        for item in task.query.support
    )
    winner, margin = support_scores(task.query.support)
    assert errors == 1
    assert PROGRAMS[winner] == task.program
    assert margin >= 1
    assert active_bits(task.query.tape)[0] not in {
        active_bits(item.tape)[0] for item in task.query.support
    }


def test_mdl_and_oracle_recover_heldout_length_six_programs() -> None:
    mdl = run_trial("enumerative_mdl_vm", 8, 6, 2, 1103, 6)
    oracle = run_trial("oracle_latent_vm", 8, 6, 2, 1103, 6)
    assert mdl["accuracy"] == mdl["program_induction_accuracy"] == 1.0
    assert oracle["accuracy"] == oracle["program_induction_accuracy"] == 1.0
    assert mdl["trace_supervision_rate"] == mdl["supplied_program_rate"] == 0.0


def test_compiled_mdl_warm_path_keeps_raw_support_routing_cost() -> None:
    result = run_trial("enumerative_mdl_vm", 8, 4, 2, 1103, 6)
    assert result["mean_warm_query_ops"] < result["mean_query_ops"]
    assert result["mean_warm_memory_reads"] > 4


def test_dense_control_reads_padding_while_oracle_stops_at_sentinel() -> None:
    dense = run_trial("dense_whole_io", 32, 4, 2, 1103, 6)
    oracle = run_trial("oracle_latent_vm", 32, 4, 2, 1103, 6)
    assert dense["mean_memory_reads"] > 32
    assert oracle["mean_memory_reads"] == 5
