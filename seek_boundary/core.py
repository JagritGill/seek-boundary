"""Audit strict seeks on a prefix of an explicit, unique complete sort key."""

from .model import MAX_EVIDENCE, integer, validate

WITNESSES = 8


def _ordered(model):
    # Stable passes from least to most significant field support mixed directions
    # without negating strings, coercing types, or depending on input tie order.
    records = list(enumerate(model.rows, 1))
    for column in reversed(range(len(model.directions))):
        records.sort(key=lambda r: r[1][column], reverse=model.directions[column] == "desc")
    return records


def _prefix_ends(records, width):
    ends = [0] * len(records)
    tied_groups = tied_rows = 0
    start = 0
    while start < len(records):
        end = start + 1
        prefix = records[start][1][:width]
        while end < len(records) and records[end][1][:width] == prefix:
            end += 1
        for position in range(start, end):
            ends[position] = end
        if end - start > 1:
            tied_groups += 1
            tied_rows += end - start
        start = end
    return ends, tied_groups, tied_rows


def _walk(records, ends, size, evidence):
    start = pages = returned = skipped = boundaries = 0
    witnesses = []
    while start < len(records):
        stop = min(start + size, len(records))
        pages += 1
        returned += stop - start
        next_start = ends[stop - 1]
        lost = next_start - stop
        if lost:
            skipped += lost
            boundaries += 1
            if len(witnesses) < evidence:
                sample = [r[0] for r in records[stop:min(next_start, stop + WITNESSES)]]
                witnesses.append({
                    "page": pages,
                    "boundary_record": records[stop - 1][0],
                    "boundary_rank": stop,
                    "skipped_count": lost,
                    "first_skipped_rank": stop + 1,
                    "last_skipped_rank": next_start,
                    "skipped_records": sample,
                    "omitted_records": lost - len(sample),
                })
        start = next_start
    return {"page_size": size, "pages": pages, "returned": returned,
            "skipped": skipped, "loss_boundaries": boundaries,
            "evidence": witnesses, "omitted_boundaries": boundaries - len(witnesses)}


def audit(document, *, evidence=10):
    """Return a JSON-compatible report; validate before work, never mutate input.

    Source record numbers are one-based positions in document['rows']. Sorted
    ranks are also one-based. No input key values are included in the report.
    """
    integer(evidence, 0, MAX_EVIDENCE, "evidence")
    model = validate(document)
    records = _ordered(model)
    ends, groups, tied_rows = _prefix_ends(records, model.cursor_width)
    complete_ends = list(range(1, len(records) + 1))
    runs = []
    for size in model.page_sizes:
        result = _walk(records, ends, size, evidence)
        control = _walk(records, complete_ends, size, 0)
        result["full_key_control"] = {k: control[k] for k in ("pages", "returned", "skipped")}
        runs.append(result)
    return {"schema_version": 1, "rows": len(records),
            "key_width": len(model.directions), "directions": list(model.directions),
            "cursor_width": model.cursor_width, "cursor_unique": groups == 0,
            "tied_prefix_groups": groups, "rows_in_tied_prefix_groups": tied_rows,
            "evidence_limit": evidence, "runs": runs,
            "gate_failed": any(r["skipped"] for r in runs)}
