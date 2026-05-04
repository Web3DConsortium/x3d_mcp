"""Filter and split training data by source and token budget.

Usage:
    python -m dataset.filter input.jsonl output.jsonl \
        --source original \
        --max-tokens 8192
"""

import json
import argparse
import sys
from pathlib import Path

from dataset.schema import TrainingExample


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (chars / 4)."""
    return len(text) // 4


def filter_file(
    input_path: str,
    output_path: str,
    source: str = "all",
    max_tokens: int = 0,
) -> dict:
    """Filter a JSONL file by source and token budget. Returns stats."""
    input_p = Path(input_path)
    output_p = Path(output_path)

    stats = {
        "total": 0,
        "kept": 0,
        "filtered_by_source": 0,
        "filtered_by_tokens": 0,
    }

    rows = []
    with open(input_p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats["total"] += 1

            raw = json.loads(line)
            example = TrainingExample.from_dict(raw)

            if source != "all":
                example_source = example.metadata.get("source", "original")
                if example_source != source:
                    stats["filtered_by_source"] += 1
                    continue

            if max_tokens > 0:
                total = estimate_tokens(example.instruction) + estimate_tokens(example.output)
                if total > max_tokens:
                    stats["filtered_by_tokens"] += 1
                    continue

            rows.append(example)
            stats["kept"] += 1

    output_p.parent.mkdir(parents=True, exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(row.to_json() + "\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Filter X3D training data")
    parser.add_argument("input", help="Input JSONL file")
    parser.add_argument("output", help="Output JSONL file")
    parser.add_argument("--source", choices=["original", "augmented", "all"],
                        default="all", help="Filter by source (default: all)")
    parser.add_argument("--max-tokens", type=int, default=0,
                        help="Filter examples exceeding token estimate (0 = no filter)")
    args = parser.parse_args()

    stats = filter_file(args.input, args.output, source=args.source, max_tokens=args.max_tokens)

    print(f"Total: {stats['total']}")
    print(f"Kept: {stats['kept']}")
    print(f"Filtered by source: {stats['filtered_by_source']}")
    print(f"Filtered by tokens: {stats['filtered_by_tokens']}")


if __name__ == "__main__":
    main()
