"""Command-line report for a fixed snapshot under an explicit cursor model."""

import argparse
import json
import sys

from . import InputError, audit
from .io import load


def render(report):
    lines = [f"rows={report['rows']} key_width={report['key_width']} cursor_width={report['cursor_width']}",
             f"cursor_unique={str(report['cursor_unique']).lower()} tied_groups={report['tied_prefix_groups']}"]
    for run in report["runs"]:
        lines.append(f"size={run['page_size']} pages={run['pages']} returned={run['returned']} "
                     f"skipped={run['skipped']} full_key_skipped={run['full_key_control']['skipped']}")
        for item in run["evidence"]:
            lines.append(f"  page={item['page']} boundary_record={item['boundary_record']} "
                         f"skipped_records={item['skipped_records']} omitted_records={item['omitted_records']}")
        if run["omitted_boundaries"]:
            lines.append(f"  omitted_boundaries={run['omitted_boundaries']}")
    lines.append("gate=" + ("FAIL (selected sizes skip rows)" if report["gate_failed"]
                             else "PASS (selected sizes only; not a general safety proof)"))
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", help="stable local UTF-8 JSON file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--evidence", type=int, default=10, help="0..50 loss boundaries per size")
    args = parser.parse_args(argv)
    try:
        result = audit(load(args.snapshot), evidence=args.evidence)
    except InputError as exc:
        print(f"seek-boundary: {exc}", file=sys.stderr)
        return 2
    output = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
              if args.format == "json" else render(result))
    sys.stdout.write(output)
    return int(result["gate_failed"])


if __name__ == "__main__":
    raise SystemExit(main())
