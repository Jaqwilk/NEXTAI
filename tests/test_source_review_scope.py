import copy
from pathlib import Path

from jsonschema.exceptions import ValidationError
import pytest

from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.schemas import validate_document

ROOT = Path(__file__).resolve().parents[1]


def record():
    return copy.deepcopy(read_jsonl(ROOT / "research/sources.jsonl")[-1])


def test_source_scope_preserves_old_and_new_ledger_record_validity():
    source = record()
    validate_document("source", source, ROOT)
    del source["checked_scope"]
    validate_document("source", source, ROOT)


@pytest.mark.parametrize("value", ["", " ", "\n", "x" * 1025, 42, {}, None])
def test_source_scope_rejects_empty_overlong_or_untyped_review_scope(value):
    source = record()
    source["checked_scope"] = value
    with pytest.raises(ValidationError):
        validate_document("source", source, ROOT)


def test_source_scope_does_not_accept_other_undeclared_fields():
    source = record()
    source["unreviewed_hidden_context"] = "must not be silently accepted"
    with pytest.raises(ValidationError, match="Additional properties"):
        validate_document("source", source, ROOT)
