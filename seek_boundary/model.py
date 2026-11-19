"""Validate and freeze the deliberately small input model."""

from dataclasses import dataclass

MAX_ROWS = 10_000
MAX_COLUMNS = 8
MAX_SIZES = 32
MAX_TEXT = 128
MAX_EVIDENCE = 50


class InputError(ValueError):
    """Rejected input, with a diagnostic that does not echo supplied values."""


@dataclass(frozen=True)
class Model:
    directions: tuple[str, ...]
    cursor_width: int
    page_sizes: tuple[int, ...]
    rows: tuple[tuple[int | str, ...], ...]


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise InputError(f"{label} must be an integer in [{low}, {high}]")
    return value


def validate(document):
    fields = {"directions", "cursor_width", "page_sizes", "rows"}
    if type(document) is not dict or set(document) != fields:
        raise InputError("expected exactly directions, cursor_width, page_sizes, rows")
    directions = document["directions"]
    if (type(directions) is not list or not 1 <= len(directions) <= MAX_COLUMNS
            or any(type(d) is not str or d not in ("asc", "desc") for d in directions)):
        raise InputError("directions must contain 1..8 asc/desc strings")
    width = integer(document["cursor_width"], 1, len(directions), "cursor_width")
    sizes = document["page_sizes"]
    if type(sizes) is not list or not 1 <= len(sizes) <= MAX_SIZES:
        raise InputError("page_sizes must contain 1..32 distinct sizes")
    for size in sizes:
        integer(size, 1, MAX_ROWS, "page size")
    if len(set(sizes)) != len(sizes):
        raise InputError("page_sizes must be distinct")
    rows = document["rows"]
    if type(rows) is not list or len(rows) > MAX_ROWS:
        raise InputError("rows must be a list of at most 10000 keys")
    types = [None] * len(directions)
    frozen = []
    seen = set()
    for number, row in enumerate(rows, 1):
        if type(row) is not list or len(row) != len(directions):
            raise InputError(f"record {number}: key width must match directions")
        for column, value in enumerate(row):
            label = f"record {number}, column {column + 1}"
            if type(value) is int:
                integer(value, -(2**63), 2**63 - 1, label)
            elif type(value) is str:
                if len(value) > MAX_TEXT or any(0xD800 <= ord(c) <= 0xDFFF for c in value):
                    raise InputError(f"{label}: string exceeds 128 scalars or has a surrogate")
            else:
                raise InputError(f"{label}: only integers or strings are supported")
            if types[column] is None:
                types[column] = type(value)
            elif types[column] is not type(value):
                raise InputError(f"column {column + 1}: mixed types are unsupported")
        key = tuple(row)
        if key in seen:
            raise InputError(f"record {number}: complete sort key is not unique")
        seen.add(key)
        frozen.append(key)
    return Model(tuple(directions), width, tuple(sorted(sizes)), tuple(frozen))
