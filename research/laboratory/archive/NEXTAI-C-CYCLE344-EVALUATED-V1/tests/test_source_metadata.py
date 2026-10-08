"""Dataset attribution is explicit without opening the source schema to arbitrary fields."""
import pytest
from jsonschema import ValidationError

from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


@pytest.mark.parametrize("source_id", ["SRC-0458", "SRC-0459"])
def test_official_dataset_metadata_accepts_doi_and_license(source_id):
    root = project_root()
    source = next(row for row in read_jsonl(root / "research/sources.jsonl")
                  if row["source_id"] == source_id)
    assert source["primary_source"] and source["source_type"] == "dataset"
    validate_document("source", source, root)


@pytest.mark.parametrize("field,value", [("doi", "unverified"), ("license", " "),
                                        ("license", 4), ("arbitrary_metadata", True)])
def test_source_metadata_stays_typed_and_closed(field, value):
    root = project_root()
    source = next(row for row in read_jsonl(root / "research/sources.jsonl")
                  if row["source_id"] == "SRC-0458")
    with pytest.raises(ValidationError):
        validate_document("source", {**source, field: value}, root)
