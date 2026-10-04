"""Legal raw-text grammar only: no generator, splits or answer oracle."""
from __future__ import annotations

import re

_STATEMENT = re.compile(r"At step (\d{4}), (E[TDF]\d{3})'s ([a-z]+) contact became (E[TDF]\d{3})\.")
_QUESTION = re.compile(r"Starting at (E[TDF]\d{3}), follow ([a-z]+(?:, then [a-z]+)*). Which contact is reached now\?")


def parse_statement(text: str):
    match = _STATEMENT.fullmatch(text)
    if match is None:
        return None
    step, subject, relation, target = match.groups()
    return int(step), subject, relation, target


def parse_question(text: str):
    match = _QUESTION.fullmatch(text)
    return (match[1], tuple(match[2].split(", then "))) if match else None
