"""Normalize training data JSONL to consistent schema.

Usage:
    python -m dataset.normalize input.jsonl output.jsonl [--report]
"""

import json
import sys
import argparse
from pathlib import Path

from dataset.schema import TrainingExample, validate_example, normalize_metadata


def normalize_file(input_path: str, output_path: str, report: bool = False) -> dict:
    """Read a JSONL file, normalize all rows, write output. Returns stats."""
    input_p = Path(input_path)
    output_p = Path(output_path)

    stats = {
        "total": 0,
        "normalized": 0,
        "string_metadata_fixed": 0,
        "missing_metadata_fixed": 0,
        "errors": [],
    }

    rows = []
    with open(input_p, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            stats["total"] += 1

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                stats["errors"].append(f"line {line_num}: invalid JSON: {e}")
                continue

            validation_errors = validate_example(raw)

            raw_meta = raw.get("metadata")
            if isinstance(raw_meta, str):
                stats["string_metadata_fixed"] += 1
            elif raw_meta is None:
                stats["missing_metadata_fixed"] += 1

            if any("instruction" in e or "output" in e for e in validation_errors):
                stats["errors"].append(f"line {line_num}: {'; '.join(validation_errors)}")
                continue

            example = TrainingExample.from_dict(raw)
            rows.append(example)
            stats["normalized"] += 1

    output_p.parent.mkdir(parents=True, exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        for example in rows:
            f.write(example.to_json() + "\n")

    if report:
        print(f"Total rows read: {stats['total']}")
        print(f"Normalized: {stats['normalized']}")
        print(f"String metadata fixed: {stats['string_metadata_fixed']}")
        print(f"Missing metadata fixed: {stats['missing_metadata_fixed']}")
        print(f"Errors: {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"  {err}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Normalize X3D training data JSONL")
    parser.add_argument("input", help="Input JSONL file path")
    parser.add_argument("output", help="Output JSONL file path")
    parser.add_argument("--report", action="store_true", help="Print normalization report")
    args = parser.parse_args()

    stats = normalize_file(args.input, args.output, report=args.report)
    if stats["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
