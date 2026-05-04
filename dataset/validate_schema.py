"""Validate a JSONL dataset file for schema consistency without modifying it.

Usage:
    python -m dataset.validate_schema input.jsonl
"""

import json
import sys
import argparse
from pathlib import Path

from dataset.schema import validate_example


def validate_file(input_path: str) -> dict:
    """Check a JSONL file for schema issues. Returns report dict."""
    input_p = Path(input_path)

    report = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "issues": [],
    }

    with open(input_p, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            report["total"] += 1

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                report["invalid"] += 1
                report["issues"].append({"line": line_num, "errors": [f"invalid JSON: {e}"]})
                continue

            errors = validate_example(raw)
            if errors:
                report["invalid"] += 1
                report["issues"].append({"line": line_num, "errors": errors})
            else:
                report["valid"] += 1

    return report


def main():
    parser = argparse.ArgumentParser(description="Validate X3D training data JSONL schema")
    parser.add_argument("input", help="Input JSONL file path")
    args = parser.parse_args()

    report = validate_file(args.input)

    print(f"Total rows: {report['total']}")
    print(f"Valid: {report['valid']}")
    print(f"Invalid: {report['invalid']}")

    if report["issues"]:
        print("\nIssues found:")
        for issue in report["issues"]:
            print(f"  Line {issue['line']}:")
            for err in issue["errors"]:
                print(f"    - {err}")
        sys.exit(1)
    else:
        print("\nAll rows valid.")


if __name__ == "__main__":
    main()
