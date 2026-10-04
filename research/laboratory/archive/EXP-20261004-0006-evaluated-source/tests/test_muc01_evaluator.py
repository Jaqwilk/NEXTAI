from nextai_autoresearch.muc01_task import HELDOUT_TUPLES, TRAIN_TUPLES, make_world, split_worlds


def test_generator_is_deterministic_and_exactly_stratified() -> None:
    first = make_world(128, 4, 12345, "F")
    assert first == make_world(128, 4, 12345, "F")
    assert len(first.statements) == 160
    assert len(first.questions) == 16
    assert sum(q.replacement_affected for q in first.questions) >= 6
    assert sum(q.unknown for q in first.questions) == 2
    assert sum(q.unseen_composition for q in first.questions) == 8


def test_split_sizes_and_entity_inventories_are_disjoint() -> None:
    train, dev, final = split_worlds(32, 2, 1234567)
    assert (len(train), len(dev), len(final)) == (45, 15, 15)
    joined = lambda worlds: " ".join(worlds[0].statements)
    assert "ET" in joined(train) and "ED" in joined(dev) and "EF" in joined(final)
    assert "EF" not in joined(train) and "ET" not in joined(final)


def test_final_compositions_are_absent_from_training() -> None:
    assert set(TRAIN_TUPLES[2]).isdisjoint(HELDOUT_TUPLES[2])
    assert set(TRAIN_TUPLES[4]).isdisjoint(HELDOUT_TUPLES[4])
