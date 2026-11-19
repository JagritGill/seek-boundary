import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from seek_boundary import InputError
from seek_boundary.io import MAX_BYTES, load

ROOT = Path(__file__).resolve().parents[1]


def cli(*args):
    return subprocess.run([sys.executable, "-B", "-m", "seek_boundary", *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=10)


class CliTests(unittest.TestCase):
    def bad_bytes(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/"input.json"
            p.write_bytes(raw)
            result = cli(p)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        self.assertTrue(result.stderr.startswith("seek-boundary:"))

    def test_exact_example_text(self):
        result = cli("examples/ties.json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, (ROOT/"examples/ties.txt").read_text())
        self.assertEqual(result.stderr, "")

    def test_json_and_zero_evidence(self):
        result = cli("examples/ties.json", "--format", "json", "--evidence", "0")
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data["runs"][0]["skipped"], 2)
        self.assertEqual(data["runs"][0]["evidence"], [])
        self.assertEqual(data["runs"][0]["omitted_boundaries"], 2)

    def test_passing_sizes_do_not_imply_unique_cursor(self):
        result = cli("examples/aligned.json", "--format", "json")
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(data["cursor_unique"])
        self.assertEqual(cli("examples/complete.json").returncode, 0)

    def test_invalid_json_and_integer_limit(self):
        for raw in (b"{", b"[]", b"\xff", b"1" * 5000, b"[" * 1500 + b"]" * 1500,
                    b'{"x":1,"x":2}', b'{"x":NaN}', b'{} trailing'):
            self.bad_bytes(raw)

    def test_size_limit(self):
        self.bad_bytes(b" " * (MAX_BYTES + 1))

    def test_regular_file_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root/"input.json"
            target.write_text("{}")
            link = root/"link.json"
            link.symlink_to(target)
            for path in (root, root/"absent", link):
                with self.assertRaises(InputError):
                    load(path)

    def test_values_not_disclosed(self):
        doc = {"directions": ["asc", "asc"], "cursor_width": 1,
               "page_sizes": [1], "rows": [["private\u001b[2J", 1], ["private\u001b[2J", 2]]}
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/"input.json"
            p.write_text(json.dumps(doc))
            for output in ("text", "json"):
                result = cli(p, "--format", output)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("private", result.stdout)
                self.assertNotIn("\x1b", result.stdout)

    def test_usage_and_error_are_not_findings(self):
        for args in ((), ("examples/ties.json", "--evidence", "-1"),
                     ("examples/ties.json", "--format", "xml")):
            result = cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
        self.assertEqual(cli("--help").returncode, 0)
