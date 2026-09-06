from nextai_autoresearch.muc01_baseline_core import SymbolicSystem, parse_question, parse_statement
from nextai_autoresearch.muc01_task import make_world


def test_public_parsers_reject_non_grammar_and_parse_legal_text() -> None:
    world = make_world(32, 2, 991, "F")
    assert parse_statement(world.statements[0]) is not None
    assert parse_question(world.questions[0].text) is not None
    assert parse_statement("private graph edge") is None


def test_symbolic_control_is_exact_on_replacement_retention_composition_and_unknown() -> None:
    world = make_world(128, 4, 992, "F")
    system = SymbolicSystem(992, {})
    session = system.new_session()
    for statement in world.statements:
        session.ingest(statement)
    answers = session.answer_batch(tuple(q.text for q in world.questions))
    assert answers == tuple(q.answer for q in world.questions)
    assert system.parser_failures == 0


def test_symbolic_update_is_last_write_wins_and_local() -> None:
    system = SymbolicSystem(1, {})
    session = system.new_session()
    session.ingest("At step 0001, EF000's amber contact became EF001.")
    session.ingest("At step 0002, EF000's amber contact became EF002.")
    assert session.last_replaced is True
    assert session.answer_batch(("Starting at EF000, follow amber. Which contact is reached now?",)) == ("EF002",)
