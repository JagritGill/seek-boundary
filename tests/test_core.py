import copy
from contextlib import closing
import itertools
import random
import sqlite3
import unittest

from seek_boundary import InputError, audit


def model(rows, directions=None, width=1, sizes=None):
    return {"directions": directions or ["asc", "asc"], "cursor_width": width,
            "page_sizes": sizes or [1, 2, 3, 4], "rows": rows}


def direct_walk(rows, directions, width, size):
    # Definition by repeated eligibility scans; no prefix runs or index jumping.
    def later(a, b, count):
        for i in range(count):
            if a[i] != b[i]:
                return a[i] > b[i] if directions[i] == "asc" else a[i] < b[i]
        return False
    remaining = list(enumerate(rows, 1))
    ordered = []
    while remaining:
        first = next(a for a in remaining
                     if not any(later(a[1], b[1], len(directions)) for b in remaining))
        ordered.append(first)
        remaining.remove(first)
    returned, losses = [], []
    cursor = None
    pages = 0
    while True:
        eligible = [r for r in ordered if cursor is None or later(r[1], cursor, width)]
        page = eligible[:size]
        if not page:
            break
        pages += 1
        returned.extend(r[0] for r in page)
        cursor = page[-1][1]
        lost = [r[0] for r in eligible[size:] if r[1][:width] == cursor[:width]]
        if lost:
            rank = next(i for i, r in enumerate(ordered, 1) if r[0] == page[-1][0])
            losses.append({"page": pages, "boundary_record": page[-1][0],
                           "boundary_rank": rank, "skipped_count": len(lost),
                           "first_skipped_rank": rank + 1, "last_skipped_rank": rank + len(lost),
                           "skipped_records": lost[:8], "omitted_records": max(0, len(lost) - 8)})
    return returned, losses, pages


class CoreTests(unittest.TestCase):
    def test_page_size_can_hide_incomplete_cursor(self):
        report = audit(model([[10, 1], [10, 2], [10, 3], [20, 4], [30, 5], [30, 6]], sizes=[2, 3]))
        self.assertEqual([r["skipped"] for r in report["runs"]], [2, 0])
        self.assertEqual([e["skipped_records"] for e in report["runs"][0]["evidence"]], [[3], [6]])
        self.assertTrue(report["gate_failed"])
        self.assertFalse(report["cursor_unique"])
        aligned = audit(model([[0, 1], [0, 2], [0, 3]], sizes=[3]))
        self.assertFalse(aligned["gate_failed"])
        self.assertFalse(aligned["cursor_unique"])

    def test_complete_cursor_and_short_pages(self):
        r = audit(model([[1, 0], [1, 1], [1, 2]], width=2, sizes=[2]))
        self.assertTrue(r["cursor_unique"])
        self.assertEqual((r["runs"][0]["pages"], r["runs"][0]["returned"]), (2, 3))
        self.assertEqual(r["runs"][0]["skipped"], 0)

    def test_empty_and_singleton(self):
        for rows in ([], [[0, 1]]):
            r = audit(model(rows))
            self.assertFalse(r["gate_failed"])
            self.assertTrue(r["cursor_unique"])
            for run in r["runs"]:
                self.assertEqual(run["returned"], len(rows))
                self.assertEqual(run["pages"], len(rows))

    def test_bounds_and_witness_omission(self):
        r = audit(model([[0, i] for i in range(10_000)], sizes=[1]), evidence=1)
        run = r["runs"][0]
        self.assertEqual(run["skipped"], 9999)
        self.assertEqual(run["evidence"][0]["omitted_records"], 9991)
        self.assertEqual(run["evidence"][0]["skipped_records"], list(range(2, 10)))
        zero = audit(model([[0, i] for i in range(20)], sizes=[1]), evidence=0)["runs"][0]
        self.assertEqual((zero["skipped"], zero["omitted_boundaries"], zero["evidence"]), (19, 1, []))

    def test_input_not_mutated_and_sizes_canonical(self):
        d = model([[2, 1], [1, 0]], sizes=[4, 2, 1])
        original = copy.deepcopy(d)
        report = audit(d)
        self.assertEqual(d, original)
        self.assertEqual([r["page_size"] for r in report["runs"]], [1, 2, 4])

    def test_many_loss_boundaries_cap_keeps_exact_totals(self):
        doc = model([[i // 3, i] for i in range(60)], sizes=[2])
        all_rows = audit(doc, evidence=50)["runs"][0]
        limited = audit(doc, evidence=2)["runs"][0]
        self.assertEqual(limited["evidence"], all_rows["evidence"][:2])
        self.assertEqual(limited["omitted_boundaries"], 18)
        self.assertEqual(limited["skipped"], 20)
        self.assertEqual(limited["returned"], 40)
        self.assertEqual(limited["full_key_control"], all_rows["full_key_control"])

    def test_mixed_directions_unicode_and_extreme_integers(self):
        rows = [["\U0001f600", -(2**63)], ["a\x00", 2**63 - 1], ["a\x00", 0], ["é", 2]]
        doc = model(rows, ["desc", "asc"])
        for run in audit(doc)["runs"]:
            returned, losses, pages = direct_walk(rows, doc["directions"], 1, run["page_size"])
            self.assertEqual(run["evidence"], losses)
            self.assertEqual(run["returned"], len(returned))
            self.assertEqual(run["pages"], pages)

    def test_exhaustive_direct_definition(self):
        count = 0
        for length in range(7):
            for values in itertools.product(range(3), repeat=length):
                rows = [[value, i] for i, value in enumerate(values)]
                for directions in itertools.product(("asc", "desc"), repeat=2):
                    for width in (1, 2):
                        report = audit(model(rows, list(directions), width))
                        for run in report["runs"]:
                            returned, losses, pages = direct_walk(rows, directions, width, run["page_size"])
                            self.assertEqual(run["evidence"], losses)
                            self.assertEqual(run["pages"], pages)
                            self.assertEqual(run["returned"], len(returned))
                            self.assertEqual(run["skipped"], length - len(returned))
                            self.assertEqual(run["full_key_control"]["skipped"], 0)
                        count += 1
        self.assertEqual(count, 8744)

    def test_sqlite_expanded_predicate_oracle(self):
        rng = random.Random(934)
        with closing(sqlite3.connect(":memory:")) as db:
            db.execute("CREATE TABLE records (record INTEGER, a INTEGER, b TEXT, c INTEGER)")
            for case in range(180):
                db.execute("DELETE FROM records")
                rows = [[rng.randrange(4), rng.choice(["a", "b", "é", "😀"]), i]
                        for i in range(rng.randrange(25))]
                rng.shuffle(rows)
                db.executemany("INSERT INTO records VALUES (?, ?, ?, ?)",
                               [(i, *row) for i, row in enumerate(rows, 1)])
                directions = [rng.choice(["asc", "desc"]) for _ in range(3)]
                width = 1 + case % 3
                doc = model(rows, directions, width, [1, 2, 5])
                order = ", ".join(f"{col} {direction}" for col, direction in zip("abc", directions))
                for run in audit(doc)["runs"]:
                    cursor = None
                    seen = []
                    pages = 0
                    while True:
                        terms, params = [], []
                        if cursor is not None:
                            for i in range(width):
                                term = [f"{'abc'[j]} = ?" for j in range(i)]
                                term.append(f"{'abc'[i]} {'>' if directions[i] == 'asc' else '<'} ?")
                                terms.append("(" + " AND ".join(term) + ")")
                                params.extend(cursor[:i + 1])
                        where = " WHERE " + " OR ".join(terms) if terms else ""
                        page = db.execute("SELECT record, a, b, c FROM records" + where
                                          + " ORDER BY " + order + " LIMIT ?",
                                          [*params, run["page_size"]]).fetchall()
                        if not page:
                            break
                        pages += 1
                        seen.extend(r[0] for r in page)
                        cursor = page[-1][1:]
                    self.assertEqual(run["returned"], len(seen))
                    self.assertEqual(run["pages"], pages)
                    self.assertEqual(run["skipped"], len(rows) - len(seen))
                    witnesses = {r for loss in run["evidence"] for r in loss["skipped_records"]}
                    self.assertTrue(witnesses <= set(range(1, len(rows) + 1)) - set(seen))


class ValidationTests(unittest.TestCase):
    def reject(self, doc):
        with self.assertRaises(InputError):
            audit(doc)

    def test_schema_and_directions(self):
        for value in (None, [], {}, {**model([]), "extra": 1}):
            self.reject(value)
        for value in ([], ["ASC"], [True], ["asc"] * 9, "asc"):
            self.reject({**model([]), "directions": value})

    def test_sizes_width_and_evidence(self):
        for sizes in ([], [0], [-1], [True], [1.0], [10001], [1, 1], list(range(1, 34))):
            self.reject(model([], sizes=sizes) if sizes else {**model([]), "page_sizes": []})
        for width in (0, 3, True, 1.0, "1"):
            self.reject(model([], width=width))
        for value in (-1, 51, True, "2"):
            with self.assertRaises(InputError):
                audit(model([]), evidence=value)

    def test_unsupported_values_and_mixed_types(self):
        for value in (None, True, 1.0, [], {}, 2**63, -(2**63)-1, "x" * 129, "\ud800"):
            self.reject(model([[value, 1]]))
        self.reject(model([[1, 0], ["1", 1]]))
        self.reject(model([[1]]))
        self.reject(model([[1, 2, 3]]))

    def test_duplicate_full_key_and_row_bound(self):
        self.reject(model([[1, 2], [1, 2]]))
        self.reject(model([[1, i] for i in range(10001)]))
        self.reject({**model([]), "rows": {}})


if __name__ == "__main__":
    unittest.main()
