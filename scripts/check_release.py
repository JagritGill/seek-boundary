"""Exact release inventory, links, syntax and heuristic public-source scan."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import stat

FILES = frozenset("""
.github/workflows/ci.yml .gitignore AGENTS.md LICENSE NOTICE.md README.md
docs/architecture.md docs/related-work.md
examples/ties.json examples/aligned.json examples/complete.json examples/ties.txt
seek_boundary/__init__.py seek_boundary/__main__.py seek_boundary/model.py
seek_boundary/core.py seek_boundary/io.py
scripts/check_examples.py scripts/check_release.py
tests/test_core.py tests/test_cli_io.py tests/test_release.py
""".split())

PATTERNS = [r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{30,}",
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"/(?:Users|home)/[A-Za-z0-9_.-]+/"]


def check(root):
    root = Path(root).resolve()
    actual = set()
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if rel.parts[0] == ".git":
            continue
        if p.is_symlink():
            raise ValueError("symlink in release")
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError("non-regular release entry")
        actual.add(rel.as_posix())
    if actual != FILES:
        raise ValueError("release inventory mismatch")
    hashes = {}
    links = syntax = 0
    for name in sorted(FILES):
        p = root/name
        if stat.S_IMODE(p.stat().st_mode) != 0o644:
            raise ValueError("unexpected file permissions")
        raw = p.read_bytes()
        data = raw.decode("utf-8")
        if any(byte < 32 and byte not in (9, 10) for byte in raw):
            raise ValueError("raw control byte in release")
        if any(re.search(pattern, data) for pattern in PATTERNS):
            raise ValueError("credential-like or private-path pattern")
        if p.suffix == ".py":
            ast.parse(data, filename=name)
            syntax += 1
        if p.suffix == ".md":
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", data):
                if target.startswith(("https://", "http://", "#")):
                    continue
                path = (p.parent/target.split("#", 1)[0]).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    raise ValueError("broken or external local Markdown link")
                links += 1
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return {"files": len(hashes), "local_links": links,
            "python_syntax_files": syntax, "sha256": hashes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = check(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, SyntaxError) as exc:
        parser.exit(1, f"release check failed: {exc}\n")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"release checks passed: {result['files']} files, {result['local_links']} local links, "
              f"{result['python_syntax_files']} Python syntax files; heuristic scan only")


if __name__ == "__main__":
    main()
