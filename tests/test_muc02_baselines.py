"""Algorithm conformance, not scored learning or a claim of model competence."""
import math

import pytest
import torch

from nextai_autoresearch.candidates.muc02_core import (
    BM25Index, Reader, SymbolicSystem, encoded_pair, training_pairs,
)
from nextai_autoresearch.muc_contract import parse_statement
from nextai_autoresearch.utils import load_json, project_root


def test_reader_semantics_masks_and_bm25():
    recipe = dict(pair_bytes_cap=96,width=24,encoder_layers=1,feedforward_width=48,heads=3,dropout=0.)
    torch.manual_seed(117)
    model = Reader(recipe).eval()
    ids = torch.tensor([encoded_pair("ET000 amber","ET000 amber"),encoded_pair("ET001 amber","ET000 amber")])
    with torch.inference_mode():
        first = model(ids)
        assert first.shape == (2,) and torch.isfinite(first).all()
        model.position.weight[50:].add_(37.)
        second = model(ids)
    assert torch.allclose(first,second,atol=1e-5)  # Masked positions cannot affect CLS.
    with pytest.raises(ValueError,match="truncate"):
        encoded_pair("x"*96,"document")
    index = BM25Index()
    index.add("amber amber")
    index.add("amber " + "jade "*8)
    index.add("copper")
    scores = dict(index.rank(("amber",),top_k=3))
    average = (2+9+1)/3
    idf = math.log(1+(3-2+.5)/(2+.5))
    expected = idf*2*2.2/(2+1.2*(1-.75+.75*2/average))
    assert scores[0] == pytest.approx(expected)
    assert scores[0] > scores[1] > 0 and index.search_ops > 0
    assert [row[0] for row in index.rank(("absent",))] == []
    # Actual candidate architecture, not only a parser fixture.
    from nextai_autoresearch.candidates.frozen_bm25_pair_transformer_v2 import Candidate
    protocol = load_json(project_root()/"research/plans/EXP-20261002-0001.json")["muc02_protocol"]
    system = Candidate(991,protocol)
    assert len(system.model.encoder.layers) == 6 and system.model.width == 384
    system.model.eval()
    outputs = system.scores("ET000 amber",["ET000 amber","ET001 amber"])
    assert len(outputs) == 2 and all(0 <= score <= 1 for score in outputs)
    assert system.learn is False


def test_sampling_covers_all_cells_worlds_and_has_no_contradictory_negatives():
    worlds=[]
    for k in (32,128,512):
        for d in (1,2,4):
            for i in range(2):
                statements=tuple(f"At step {j:04d}, ET{j:03d}'s amber contact became ET001." for j in range(4))
                statements += ("At step 0005, ET000's amber contact became ET003.",)
                worlds.append({"statements":statements,"knowledge_size":k,"reasoning_depth":d})
    pairs, report = training_pairs(tuple(worlds),512,197)
    assert report["worlds_covered"] == report["worlds_available"] == 18
    assert report["cells_covered"] == 9 and report["subjects_covered"] == 4
    labels={}
    for query,doc,label in pairs:
        assert bool(label) == (query == doc)
        assert labels.setdefault((query,doc),label) == label
    assert len(pairs) == 512 and sum(p[2] for p in pairs) == 256


def test_symbolic_semantics_and_costs():
    system = SymbolicSystem(17,{})
    first = system.new_session()
    first.ingest("At step 0001, EF000's amber contact became EF001.")
    first.ingest("At step 0003, EF000's amber contact became EF002.")
    first.ingest("At step 0002, EF000's amber contact became EF003.")
    first.ingest("At step 0004, EF002's jade contact became EF004.")
    answer = first.answer_batch(("Starting at EF000, follow amber, then jade. Which contact is reached now?",))
    assert answer == ("EF004",)
    before = first.cost_report()
    assert before["key_lookups"] == 2 and before["query_count"] == 1
    first.answer_batch(("Starting at EF999, follow amber. Which contact is reached now?",))
    after = first.cost_report()
    assert after["query_count"] == 2 and after["input_ops"] == before["input_ops"]
    second = system.new_session()
    assert second.cost_report()["query_count"] == 0
    assert system.current_session is second and not hasattr(system,"sessions")
    # World accounting and precision in the actual scorer, using a fixed fixture seed.
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_v2 import run_trial
    system.record_fit_resources(0,0)
    trial = run_trial(system,32,1,16,911,{})
    assert trial["accuracy"] == 1 and trial["query_count"] == 240
    assert len(trial["latency_samples_us"]) == 240 and len(trial["world_costs"]) == 15
    expected=sum(c["query_ops"] for c in trial["world_costs"])/240
    assert trial["mean_query_ops"] == pytest.approx(expected)
    repeat=run_trial(system,32,1,16,911,{})
    for name in ("mean_query_ops","mean_input_ops","workload_ops_r1","workload_ops_r16"):
        assert repeat[name] == trial[name]


def test_learned_world_state_and_counters_are_scoped_to_one_session():
    from nextai_autoresearch.candidates.frozen_bm25_pair_transformer_v2 import Candidate
    protocol=load_json(project_root()/"research/plans/EXP-20261002-0001.json")["muc02_protocol"]
    system=Candidate(881,protocol)
    system.model.eval()
    first=system.new_session()
    first.ingest("At step 0001, ET000's amber contact became ET001.")
    first.ingest("At step 0002, ET000's amber contact became ET002.")
    first.answer_batch(("Starting at ET000, follow amber. Which contact is reached now?",))
    one=first.cost_report()
    assert one["query_count"] == 1 and one["query_ops"] >= system.model.estimated_forward_flops(2)
    first.answer_batch(("Starting at ET000, follow amber. Which contact is reached now?",))
    two=first.cost_report()
    assert two["query_count"] == 2 and two["input_ops"] == one["input_ops"]
    assert two["state_bytes"] > system.parameter_bytes
    second=system.new_session()
    assert not second.rows and second.cost_report()["query_ops"] == 0 and not hasattr(system,"sessions")
