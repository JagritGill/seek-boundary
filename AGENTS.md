# Working on seek-boundary

Purpose: explain losses from a strict cursor retaining only a leading prefix of
a unique complete ordering, over one fixed finite snapshot. Read [README](README.md),
[architecture](docs/architecture.md) and [related work](docs/related-work.md).

Map: `seek_boundary/model.py` validates/freezes; `core.py` sorts/indexes/walks;
`io.py` handles bounded local JSON; `__main__.py` prints reports. `examples/` are
synthetic. `tests/` contain direct-query and SQLite oracles plus actual CLI and
release-check regressions; `scripts/` verify examples and release inventory.

Commands from repo root, using installed Python (no setup/install step):

```sh
python3 -B -m unittest discover -s tests -v
python3.13 -B -m unittest discover -s tests -v
python3 -B scripts/check_examples.py
python3 -B scripts/check_release.py
python3 -B scripts/check_release.py --json
python3 -B -m seek_boundary examples/ties.json
git diff --check
```

The ties example intentionally exits 1; complete/aligned examples exit 0. Invalid
input exits 2 without partial stdout. Local runtime targets are 3.13.5 and 3.15.0.
No static checker/full linter is configured; syntax parsing is not either check.
Do not infer pass status from this command list; record actual results per commit.

Invariants: full key must be unique; prefix fields and directions are explicit.
No implicit input-index tie-breaker. Equal prefixes are contiguous in full order.
Returned+skipped=n for every size; full-key control skips zero. Source records and
sorted ranks are distinct one-based coordinates. Evidence caps never affect totals
or the gate. A passing selected size is not prefix uniqueness or live-API safety.
No NULL/coercion/collation assumptions. Preserve no-key-value output and bounds.

Use independent definitions and real CLI regressions for semantic changes; test
mixed directions, tied boundaries, aligned false reassurance, limits and malformed
inputs. Keep exact inventory and local documentation links updated. Do not expand
into API access, database writes, private data, paid services, credentials, hardware
or CodeRabbit/external reviews. Preserve owner work and unrelated repositories.
Publication needs applicable task authorization; never bypass CI or permissions.

Handoff with exact commit, dirty files, verified commands/exits, unrun checks,
observed CI and scope limits. Store machine-specific evidence outside the release.
See [NOTICE](NOTICE.md) and [LICENSE](LICENSE) before adding third-party material.
