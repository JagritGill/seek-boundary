# Architecture and tradeoffs

`model.py` validates exact fields, bounds, homogeneous column types, scalar text
and unique complete keys, then freezes the input. `core.py` sorts records with
stable passes from the least significant column and indexes exclusive ends of
equal-prefix runs. Because a cursor retains a leading prefix, each equal-prefix
class is contiguous under the complete ordering, including mixed directions.

For a page starting at zero-based rank s with limit L, let t = min(s+L, n).
The next query excludes the prefix of rank t-1; therefore its first eligible rank
is the exclusive end e of that prefix class. Ranks [t,e) are lost; [s,t) returned.
Then s becomes e. Every iteration advances, and returned+skipped equals n. Loss
evidence includes one-based source record numbers and sorted ranks; no key values.
All totals are computed even after the evidence cap. Complete-key uniqueness
means the control's prefix groups are singletons and it returns all rows.

The bound-index implementation is independently tested against repeated
eligibility scans and actual SQLite queries using expanded lexicographic
predicates. The latter is limited to tested, non-null integer/text comparisons;
it does not establish equivalence to all database types or collations.

Time is O(k*n*log(n) + m*n) for k columns, n rows and m sizes; memory holds the
validated snapshot, sort/index arrays and bounded evidence. These are algorithmic
bounds, not benchmarks. Hard limits: 10,000 rows, eight columns, 32 page sizes,
2 MiB input, 128 Unicode scalars per string, signed 64-bit integers, fifty loss
boundaries per size with eight source-record witnesses each. Empty rows and
page sizes larger than the dataset are supported.

`io.py` reads one bounded stable local regular file and strictly decodes JSON.
It checks file type before and after opening; this is not a filesystem sandbox
against malicious concurrent path changes. The CLI validates fully before output
and emits deterministic text or JSON. It never executes or prints input values.
Record counts/positions still disclose structural information. Error messages
do not echo invalid supplied values.

Choosing a strict prefix makes the model explainable and avoids pretending to
parse a real SQL dialect. It deliberately excludes arbitrary omitted key fields,
NULL rules, changing snapshots, reverse traversal, inclusive predicates and
cursor serialization. Passing a supplied fixture is not general pagination
safety. A structurally nonunique prefix can pass selected aligned page sizes.

Return to [README](../README.md); see [research](related-work.md) and
[agent guidance](../AGENTS.md) before changing these invariants.
