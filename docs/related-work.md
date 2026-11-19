# Related work and provenance

Research date: November 19, 2026, before implementation. Searches included
`keyset pagination duplicate sort key audit skipped records tool github`,
`cursor pagination tie unique column skipped rows validator tool`,
`pagination simulator keyset github`, `pagination audit page size ties`,
`site:github.com pagination page sizes audit keyset`,
`offline keyset pagination checker simulator duplicate keys`, and the proposed
names `cursor-tie` and `seek-boundary`. Local catalog and public personal repository
names were checked. Searches do not prove global uniqueness or name availability.

## Closest comparisons

- [PaginationProbe](https://github.com/6t9xstar/pagination-probe) is the closest
  audit tool. Its public README describes live HTTP pagination walks, missing or
  duplicated records, ordering and repeated-cursor checks, plus comparisons across
  page sizes. **There is substantial overlap in purpose and page-size testing.**
  This project instead takes a finite local key snapshot and a declared strict
  prefix cursor; it explains individual boundary losses and compares the complete
  key control without calling an endpoint. It cannot verify an actual API.
- [sqlakeyset](https://github.com/djrobstep/sqlakeyset) supplies SQLAlchemy keyset
  pagination. Its README warns that keys must uniquely identify rows and describes
  omitted NULL rows. This project audits a deliberately incomplete cursor model;
  it does not replace a pagination library or connect to a database.
- [kysely-cursor](https://github.com/lukewpc/kysely-cursor) provides multi-dialect
  query pagination, cursor serialization and documented unique-final-sort-key
  requirements. Here ordering is supplied explicitly, types are restricted and
  cursor token construction/query integration are out of scope.
- [QASkills boundary-testing guide](https://qaskills.sh/blog/testing-cursor-pagination-api-boundaries)
  recommends tied fixtures and complete traversal assertions. Our synthetic
  page-size-sensitive fixture demonstrates that established testing principle.
- [Prisma reading documentation](https://www.prisma.io/docs/orm/fundamentals/reading-data)
  describes including all ordered fields in a cursor and a unique tie-breaker.
- [SQLite row-value documentation](https://www.sqlite.org/rowvalue.html)
  explains lexicographic comparisons and scrolling-window queries. SQLite is
  used only as an independent test oracle, not the runtime implementation.

These are comparisons of published primary documentation, not exhaustive product
evaluations. We make no claim that other tools lack any particular feature or that
the idea is globally new. Keyset pagination, tie-breaking and boundary tests are
established concepts. The modest useful artifact here is an offline counterexample
report: exact skipped source record numbers at each defective boundary, repeated
for selected page sizes, with a complete-key control. One passing size is not a
uniqueness proof. A static snapshot cannot establish safety under concurrent writes.

## Independent implementation

Design, source, fixtures and tests are independently written with AI assistance.
No comparator implementation, fixture or documentation wording is copied or
translated; README usage examples were read only to understand documented scope.
No existing application was cloned, and no private/customer/employer source or
data is used. Runtime uses Python's standard library only. See [NOTICE](../NOTICE.md)
for dependency licensing and reuse of routine portfolio CI/release conventions.
The demo uses six synthetic tuples: a three-row prefix tie, a singleton, and a
two-row tie. Page size two skips two rows; page size three skips none. The full-key
control returns every row for both. This is a supplied model, not an API prediction.
