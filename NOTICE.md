# Attribution and dependencies

Original source, synthetic fixtures and tests were written with AI assistance
for this portfolio project. The [MIT license](LICENSE) applies to these original
files; it does not relicense other projects or claim sole human authorship.

Runtime has no third-party packages. It uses Python's standard library, provided
under the [Python licensing terms](https://docs.python.org/3/license.html).
Tests additionally use the standard-library sqlite3 binding; SQLite is
[public domain](https://www.sqlite.org/copyright.html). Neither is vendored.

Established keyset/tie-breaking concepts and the closest tools are credited in
[related work](docs/related-work.md). No comparator source or fixtures are reused.
Routine portfolio release conventions and previously verified GitHub Action pins
are reused; substantive model, core, fixtures and oracles were written anew.

CI uses [actions/checkout](https://github.com/actions/checkout) and
[actions/setup-python](https://github.com/actions/setup-python), both MIT-licensed,
as pinned external workflow dependencies. Their source is not bundled or
relicensed. CI configuration alone is not evidence of a successful run; see the
actual commit's checks. No packages, services or external reviewers are required.
