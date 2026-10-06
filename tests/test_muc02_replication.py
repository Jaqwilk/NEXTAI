"""Freshness and paired-sampler conformance; fixture TAG only, no optimizer fit."""
import hashlib
from types import SimpleNamespace

import pytest

from nextai_autoresearch import muc03_task
from nextai_autoresearch.benchmarks import mutable_contact_ledger_hard_negatives_v1 as prior
from nextai_autoresearch.benchmarks import mutable_contact_ledger_negatives_replication_v1 as replication
from nextai_autoresearch.candidates.muc02_core import SymbolicSystem, training_pairs
from nextai_autoresearch.muc02_negatives_analysis import evaluate_gates, paired_interval
from nextai_autoresearch.muc02_negatives_stage import ROLES
from nextai_autoresearch.muc02_negatives_task import TAG as PRIOR_TAG
from nextai_autoresearch.muc_contract import parse_statement
from nextai_autoresearch.utils import load_json, project_root, sha256_file

FIXTURE_TAG = "MUC02-REPLICATION-PUBLIC-FIXTURE-V1"
PLAN_PATH = "research/plans/MUC02-NEGATIVES-REPLICATION-20261006-V1.json"


def _fixture_worlds(seed, split, k, d, count):
    return muc03_task.fresh_worlds(FIXTURE_TAG, seed, split, k, d, count)


def _valid_plan():
    frozen = load_json(project_root() / PLAN_PATH)
    return {"candidates": list(ROLES),
            "matrix": {"seeds": [1000001, 1000002, 1000003, 1000004, 1000005],
                       "knowledge_sizes": [32, 128, 512], "reasoning_depths": [1, 2, 4],
                       "queries_per_cell": 16},
            "muc02_negatives_protocol": {"data_tag": replication.DATA_TAG,
                "historical_seeds": [901, 902, 903, 904, 905], "roles": frozen["roles"],
                "recipe": frozen["recipe"], "fit_steps_cap": 192, "fit_seconds_cap": 350}}


def test_world_seed_derivation_is_fresh_and_split_disjoint():
    seeds = {muc03_task.world_seed(FIXTURE_TAG, seed, split, k, d, i)
             for seed in (901, 902, 903, 904, 905) for split in ("T", "D")
             for k in (32, 128, 512) for d in (1, 2, 4)
             for i in range(45 if split == "T" else 15)}
    old = {muc03_task.world_seed(PRIOR_TAG, seed, split, k, d, i)
           for seed in (901, 902, 903, 904, 905) for split in ("T", "D")
           for k in (32, 128, 512) for d in (1, 2, 4)
           for i in range(45 if split == "T" else 15)}
    assert len(seeds) == 2700 and min(seeds) >= 2**128 and seeds.isdisjoint(old)
    raw = f"{FIXTURE_TAG}|901|T|32|1|0".encode()
    assert muc03_task.world_seed(FIXTURE_TAG, 901, "T", 32, 1, 0) == (
        2**128 + int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))
    assert replication.DATA_TAG != PRIOR_TAG != FIXTURE_TAG
    with pytest.raises(ValueError, match="train/dev"):
        _fixture_worlds(901, "F", 32, 1, 15)


def test_provider_binds_new_tag_counts_and_diagnostic_strata(monkeypatch):
    calls = []
    sentinel = object()
    monkeypatch.setattr(muc03_task, "fresh_worlds", lambda *args: calls.append(args) or sentinel)
    assert replication.fresh_worlds(901, "T", 32, 1, calls.append) is sentinel
    assert replication.fresh_worlds(901, "D", 32, 1, calls.append) is sentinel
    assert [(row[0], row[2], row[5]) for row in calls] == [
        (replication.DATA_TAG, "T", 45), (replication.DATA_TAG, "D", 15)]


def test_fixture_train_dev_and_diagnostics_are_separate():
    train = _fixture_worlds(902, "T", 32, 1, 45)
    dev = _fixture_worlds(902, "D", 32, 1, 15)
    assert len(train) == 45 and len(dev) == 15
    assert {w.statements for w in train}.isdisjoint(w.statements for w in dev)
    assert all(parse_statement(s)[1].startswith("ET") for w in train for s in w.statements)
    assert all(parse_statement(s)[1].startswith("ED") for w in dev for s in w.statements)
    queries = muc03_task.diagnostic_queries(FIXTURE_TAG, dev[0], 902, 32, 1, 0)
    keys = {(parse_statement(s)[1], parse_statement(s)[2]) for s in dev[0].statements}
    assert len(queries) == 4 and queries[0] != queries[1]
    assert all(query in keys for query in queries[:2])
    assert all(query not in keys for query in queries[2:])
    assert queries[2][0] == "ED999" and queries[3][1] == "violet"


def test_frozen_4096_pairing_changes_only_negative_key_distribution():
    worlds = tuple({"statements": w.statements, "knowledge_size": k, "reasoning_depth": d}
                   for k in (32, 128, 512) for d in (1, 2, 4)
                   for w in _fixture_worlds(903, "T", k, d, 2))
    random_pairs, random_report = training_pairs(worlds, 4096, 903, "random")
    hard_pairs, hard_report = training_pairs(worlds, 4096, 903, "hard")
    assert len(random_pairs) == len(hard_pairs) == 4096
    assert sum(y for _, _, y in random_pairs) == sum(y for _, _, y in hard_pairs) == 2048
    assert [(document, label) for _, document, label in random_pairs] == [
        (document, label) for _, document, label in hard_pairs]
    assert [(q, doc) for q, doc, y in random_pairs if y] == [(q, doc) for q, doc, y in hard_pairs if y]
    assert all(bool(y) == (q == doc) for q, doc, y in random_pairs + hard_pairs)
    assert all(sum(a != b for a, b in zip(q.split(), doc.split(), strict=True)) == 1
               for q, doc, y in hard_pairs if not y)
    assert hard_report["mismatch_types"] == {"same_subject": 1024, "same_relation": 1024}
    assert random_report["mismatch_types"]["both_different"] > 0
    for field in ("positive_sequence_sha256", "document_and_label_sequence_sha256"):
        assert random_report[field] == hard_report[field]
    assert random_report["pairs_sha256"] != hard_report["pairs_sha256"]
    assert hard_report["worlds_covered"] == hard_report["worlds_available"] == 18
    assert hard_report["cells_covered"] == 9
    assert hard_pairs == training_pairs(worlds, 4096, 903, "hard")[0]


@pytest.mark.parametrize("fault", ["collision", "duplicate", "missing_history", "history_order", "history_type",
                                   "old_tag", "wrong_role", "wrong_steps", "wrong_pairs", "unknown_role"],
                         ids=["collision", "duplicate", "missing-history", "history-order", "history-type",
                              "old-tag", "wrong-role", "wrong-steps", "wrong-pairs", "unknown-role"])
def test_freshness_failure_precedes_candidate_import_or_data(monkeypatch, fault):
    plan = _valid_plan()
    candidate = ROLES[0]
    if fault == "collision":
        plan["muc02_negatives_protocol"]["historical_seeds"].append(1000001)
    elif fault == "duplicate":
        plan["matrix"]["seeds"][-1] = plan["matrix"]["seeds"][0]
    elif fault == "missing_history":
        del plan["muc02_negatives_protocol"]["historical_seeds"]
    elif fault == "history_order":
        plan["muc02_negatives_protocol"]["historical_seeds"].reverse()
    elif fault == "history_type":
        plan["muc02_negatives_protocol"]["historical_seeds"][0] = True
    elif fault == "old_tag":
        plan["muc02_negatives_protocol"]["data_tag"] = PRIOR_TAG
    elif fault == "wrong_role":
        plan["muc02_negatives_protocol"]["roles"][candidate]["seed_index"] = 1
    elif fault == "wrong_steps":
        plan["muc02_negatives_protocol"]["fit_steps_cap"] = 193
    elif fault == "wrong_pairs":
        plan["muc02_negatives_protocol"]["recipe"]["training_pairs"] = 4098
    else:
        candidate = "muc02_unregistered"
    def forbidden(*args, **kwargs):
        raise AssertionError("Candidate import/data/fit occurred before freshness failure")
    monkeypatch.setattr(replication.importlib, "import_module", forbidden)
    monkeypatch.setattr(replication, "fresh_worlds", forbidden)
    with pytest.raises(ValueError):
        replication.run_suite(candidate, plan)


def test_valid_freshness_validation_preserves_the_unchanged_core():
    plan = _valid_plan()
    assert replication._validate_plan(ROLES[0], plan) == (plan["matrix"], plan["muc02_negatives_protocol"])
    frozen = load_json(project_root() / PLAN_PATH)
    for path, expected in frozen["unchanged_implementation_files"].items():
        assert sha256_file(project_root() / path) == expected
    assert frozen["recipe"]["updates"] == 192 and frozen["recipe"]["training_pairs"] == 4096
    assert frozen["model_identity"].startswith("unchanged Reader")
    assert replication.run_trial is prior.run_trial
    assert replication.selection_diagnostics is prior.selection_diagnostics
    assert replication.diagnostic_metrics is prior.diagnostic_metrics


def test_explicit_fixture_providers_do_not_fall_back_to_prior_worlds(monkeypatch):
    worlds = _fixture_worlds(904, "D", 32, 1, 15)
    system = SymbolicSystem(904, {})
    system.model = SimpleNamespace(length=96, estimated_forward_flops=lambda n: n * 100)
    system.scores = lambda query, keys: [float(query == key) for key in keys]
    seen = []
    def forbidden(*args, **kwargs):
        raise AssertionError("Prior cohort default provider used")
    def diagnostic_provider(system, world, seed, k, d, index):
        seen.append(index)
        return prior.selection_diagnostics(system, world, seed, k, d, index,
            queries_override=muc03_task.diagnostic_queries(FIXTURE_TAG, world, seed, k, d, index))
    monkeypatch.setattr(prior, "fresh_worlds", forbidden)
    monkeypatch.setattr(prior, "diagnostic_queries", forbidden)
    trial = replication.run_trial(system, 32, 1, 904, {}, learned=True,
        worlds_provider=lambda: worlds, diagnostic_provider=diagnostic_provider)
    assert seen == list(range(15))
    assert trial["fit_seconds"] == 0 and trial["query_count"] == 240
    assert trial["accuracy"] == trial["fact_top1_accuracy"] == trial["dense_unknown_rejection"] == 1
    assert trial["known_false_abstention"] == 0
    assert trial["calibration"]["parser_failures"] == 0


def test_fresh_diagnostic_adapter_passes_explicit_new_tag_queries(monkeypatch):
    marker_queries = (("ED000", "amber"), ("ED001", "blue"), ("ED999", "amber"), ("ED001", "violet"))
    calls = []
    monkeypatch.setattr(muc03_task, "diagnostic_queries", lambda *args: calls.append(args) or marker_queries)
    monkeypatch.setattr(replication, "selection_diagnostics", lambda *args, **kwargs: kwargs)
    system, world = object(), object()
    assert replication.fresh_diagnostics(system, world, 905, 32, 1, 0) == {"queries_override": marker_queries}
    assert calls == [(replication.DATA_TAG, world, 905, 32, 1, 0)]


@pytest.mark.parametrize("fault", ["primary_interval", "top1_gain", "unknown_gain", "accepted", "known", "abstention", "symbolic"],
                         ids=["primary-interval", "top1-gain", "unknown-gain", "accepted", "known", "abstention", "symbolic"])
def test_unchanged_scientific_gates_reject_each_failed_requirement(fault):
    thresholds = load_json(project_root() / PLAN_PATH)["decision_gates"]
    contrast = {"fact_top1_accuracy": paired_interval([.1] * 5, .975),
                "dense_unknown_rejection": paired_interval([.2] * 5, .975),
                "accepted_fact_accuracy": paired_interval([0.] * 5),
                "e2e_known_accuracy": paired_interval([0.] * 5),
                "known_false_abstention": paired_interval([0.] * 5)}
    symbolic = 1.
    assert evaluate_gates(contrast, symbolic, thresholds)["decision"] == "keep_dev_recipe"
    if fault == "primary_interval":
        contrast["fact_top1_accuracy"]["lower"] = 0.
    elif fault == "top1_gain":
        contrast["fact_top1_accuracy"] = paired_interval([.049] * 5, .975)
    elif fault == "unknown_gain":
        contrast["dense_unknown_rejection"] = paired_interval([.099] * 5, .975)
    elif fault == "accepted":
        contrast["accepted_fact_accuracy"] = paired_interval([-.021] * 5)
    elif fault == "known":
        contrast["e2e_known_accuracy"] = paired_interval([-.021] * 5)
    elif fault == "abstention":
        contrast["known_false_abstention"] = paired_interval([.021] * 5)
    else:
        symbolic = .994
    result = evaluate_gates(contrast, symbolic, thresholds)
    assert result["decision"] == "discard_proposed_recipe" and not result["architecture_promotion"]
