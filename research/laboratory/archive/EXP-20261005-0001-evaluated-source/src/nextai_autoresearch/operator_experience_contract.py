from __future__ import annotations

from dataclasses import dataclass
import random


Table = tuple[int, ...]


@dataclass(frozen=True)
class Term:
    node_id: int
    table: Table | None = None
    left: "Term | None" = None
    right: "Term | None" = None


@dataclass(frozen=True)
class LabeledPair:
    left: Term
    right: Term
    equivalent: bool


@dataclass(frozen=True)
class Training:
    pairs: tuple[LabeledPair, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class Query:
    term: Term
    state: int


@dataclass(frozen=True)
class Observation:
    query: Query
    target: int


@dataclass(frozen=True)
class Mutation:
    old: Term
    new: Term


def identity(size: int) -> Table:
    return tuple(range(size))


def compose(first: Table, second: Table) -> Table:
    return tuple(second[first[state]] for state in range(len(first)))


def flatten(term: Term, *, strip_identity: bool = True) -> tuple[Table, ...]:
    if term.table is not None:
        if strip_identity and term.table == identity(len(term.table)):
            return ()
        return (term.table,)
    if term.left is None or term.right is None:
        raise ValueError("malformed operator term")
    return flatten(term.left, strip_identity=strip_identity) + flatten(
        term.right, strip_identity=strip_identity
    )


def input_ops(term: Term) -> int:
    if term.table is not None:
        return len(term.table) + 1
    if term.left is None or term.right is None:
        raise ValueError("malformed operator term")
    return 1 + input_ops(term.left) + input_ops(term.right)


def apply(term: Term, state: int) -> tuple[int, int]:
    if term.table is not None:
        return term.table[state], 1
    if term.left is None or term.right is None:
        raise ValueError("malformed operator term")
    middle, left_ops = apply(term.left, state)
    result, right_ops = apply(term.right, middle)
    return result, left_ops + right_ops


def canonical_table(term: Term) -> tuple[Table, int]:
    tables = flatten(term)
    size = len(tables[0]) if tables else len(flatten(term, strip_identity=False)[0])
    result = identity(size)
    for table in tables:
        result = compose(result, table)
    return result, size * len(tables)


def encode(tables: tuple[Table, ...], seed: int, *, fuse: bool = False) -> Term:
    if not tables:
        raise ValueError("operator term needs a leaf")
    work = list(tables)
    if fuse and len(work) > 1:
        work[:2] = [compose(work[0], work[1])]
    work.insert(random.Random(seed ^ 0x1D).randrange(len(work) + 1), identity(len(work[0])))
    rng = random.Random(seed)
    nodes = [Term(rng.randrange(1_000_000, 2_000_000), table=table) for table in work]

    def build(values: list[Term]) -> Term:
        if len(values) == 1:
            return values[0]
        split = 1 + rng.randrange(len(values) - 1)
        return Term(
            rng.randrange(2_000_000, 3_000_000),
            left=build(values[:split]), right=build(values[split:]),
        )

    return build(nodes)


Pattern = tuple[Table | None, ...]


def anti_unify(left: Term, right: Term) -> Pattern | None:
    first, second = flatten(left), flatten(right)
    if len(first) != len(second):
        return None
    return tuple(a if a == b else None for a, b in zip(first, second))


def matches(pattern: Pattern, term: Term) -> bool:
    values = flatten(term)
    return len(values) == len(pattern) and all(
        expected is None or expected == value
        for expected, value in zip(pattern, values)
    )
