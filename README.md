# seek-boundary

Find rows a strict cursor can skip when it carries only part of the sort key.
Run against a small local snapshot before choosing pagination regression fixtures.
The report compares selected page sizes and identifies each loss boundary using
source record numbers, without printing key values or calling an API/database.

**A test can pass at size three and lose rows at size two.** The example sorts six
keys by `(group, sequence)` but continues using only `group`. The first group has
three rows and the last has two. Size two leaves a tied row behind at two page
boundaries; size three happens to align. The complete-key control loses none.
This is a finite model of a declared strict seek, not a test of a deployed API.

## Quickstart

Use installed Python 3.13+ from this folder; no installation or dependencies:

```sh
python3 -B -m seek_boundary examples/ties.json
python3 -B -m seek_boundary examples/ties.json --format json
python3 -B -m seek_boundary examples/complete.json
```

The first two commands intentionally exit **1** because they find skipped rows.
The complete cursor exits **0**. Exact first-command output:

```text
rows=6 key_width=2 cursor_width=1
cursor_unique=false tied_groups=2
size=2 pages=2 returned=4 skipped=2 full_key_skipped=0
  page=1 boundary_record=2 skipped_records=[3] omitted_records=0
  page=2 boundary_record=5 skipped_records=[6] omitted_records=0
size=3 pages=2 returned=6 skipped=0 full_key_skipped=0
gate=FAIL (selected sizes skip rows)
```

`examples/aligned.json` selects only size three and exits 0, while still reporting
`cursor_unique=false`. A green gate covers the selected sizes and supplied rows
only. `--evidence 0` suppresses witnesses without changing counts or exit status.
Default evidence is ten loss boundaries per size, maximum fifty; each boundary
lists at most eight skipped source records and explicitly counts omissions.

## Input and semantics

[The input fixture](examples/ties.json) contains exactly four fields:

| Field | Meaning |
| --- | --- |
| `directions` | 1..8 `asc`/`desc` entries, one per key column |
| `rows` | Up to 10,000 key arrays; each has that exact width |
| `cursor_width` | Number of leading key fields retained in the strict cursor |
| `page_sizes` | 1..32 distinct sizes, each 1..10,000; results sorted by size |

Each column has one type across all rows: signed 64-bit integers or strings of at
most 128 Unicode scalars. No null, Boolean, float, date parsing or coercion. Text
uses exact code-point order, without locale, normalization or case folding.
Complete keys must be unique; duplicate full keys are rejected instead of using
input position as an implicit tie-breaker. Empty snapshots are valid.

Rows are sorted by the complete key and its per-field directions. The first page
starts at the beginning. Later pages select keys strictly after the previous last
row's **prefix**, using the same directions, then take up to the page size.
Remaining rows equal to that prefix are skipped permanently. The complete-key
control retains all supplied fields with the same ordering. All page counts are
nonempty pages; no terminal empty fetch is counted. Input order supplies record
numbers only and is never an extra ordering column.

Exit **0**: no modeled skips at selected sizes. Exit **1**: modeled skips.
Exit **2**: invalid input/usage; no partial stdout report. Input is bounded to
2 MiB UTF-8 JSON in a stable local regular file; symlinks and special files are
rejected. Duplicate object keys and non-finite JSON numbers are rejected.

## API and checks

```python
from seek_boundary import audit

report = audit({
    "directions": ["asc", "asc"], "cursor_width": 1,
    "page_sizes": [1], "rows": [[7, 1], [7, 2]],
})
assert report["runs"][0]["skipped"] == 1
```

`audit` validates first, does not mutate input and returns a JSON-compatible dict.
Invalid input raises `InputError`. Reports omit key values, but counts and record
references may still be sensitive; this is not an anonymization guarantee.

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_examples.py
python3 -B scripts/check_release.py
git diff --check
```

Tests use a direct repeated-query definition and in-memory SQLite as independent
oracles, plus real CLI/error cases. Local targets are Python 3.13.5 and 3.15.0;
the CI matrix is 3.13/3.15. No static type checker/full linter is configured;
syntax parsing in the release check is neither. The scanner checks exact scope,
local links and selected credential/private-path patterns, not comprehensive
security or provenance. Verification records belong outside the public release.

## Boundaries and design

This does not inspect SQL, decode tokens, measure performance, repair queries,
contact services or prove production correctness. It models only a fixed dataset
and a strict leading-prefix cursor. No inserts/deletes, late commits, nullable
keys, inclusive comparisons, arbitrary omitted columns, backwards traversal,
collations or server-specific types. A complete key here is not proof that the
same key stays unique or immutable in production. Supply appropriate synthetic
data and test the real API separately.

See [architecture/tradeoffs](docs/architecture.md),
[related tools and research](docs/related-work.md), [agent guidance](AGENTS.md),
[attribution](NOTICE.md) and [MIT license](LICENSE). PaginationProbe already
checks live APIs and page-size consistency; this tool's narrower value is an
offline boundary explanation with a complete-key control. No global novelty claim.
