"""Exercise documented commands and intentional CLI exit statuses."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args, code):
    result = subprocess.run([sys.executable, "-B", "-m", "seek_boundary", *args],
                            cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == code, (args, result.returncode, result.stderr)
    assert not result.stderr
    return result.stdout


def main():
    assert run("examples/ties.json", code=1) == (ROOT/"examples/ties.txt").read_text()
    data = json.loads(run("examples/ties.json", "--format", "json", code=1))
    assert [r["skipped"] for r in data["runs"]] == [2, 0]
    capped = json.loads(run("examples/ties.json", "--format", "json", "--evidence", "0", code=1))
    assert capped["runs"][0]["omitted_boundaries"] == 2
    assert capped["runs"][0]["evidence"] == []
    assert "not a general safety proof" in run("examples/aligned.json", code=0)
    aligned = json.loads(run("examples/aligned.json", "--format", "json", code=0))
    assert not aligned["cursor_unique"] and not aligned["gate_failed"]
    assert "skipped=0" in run("examples/complete.json", code=0)
    complete = json.loads(run("examples/complete.json", "--format", "json", code=0))
    assert complete["cursor_unique"] and not complete["gate_failed"]
    assert "--evidence" in run("--help", code=0)
    print("8 CLI examples passed, including expected finding exits")


if __name__ == "__main__":
    main()
