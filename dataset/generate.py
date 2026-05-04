"""Generate targeted X3D training examples with long numeric sequences.

Usage:
    python -m dataset.generate output.jsonl \
        --type all --count 10 --complexity mixed \
        --validate --seed 42
"""

import json
import sys
import random
import argparse
from pathlib import Path

from dataset.generators.numeric_sequences import (
    generate_indexed_face_set,
    generate_extrusion,
    generate_interpolator,
)


GENERATORS = {
    "indexed-face-set": generate_indexed_face_set,
    "extrusion": generate_extrusion,
    "interpolator": generate_interpolator,
}


def generate_examples(
    output_path: str,
    types: list[str],
    count: int = 10,
    complexity: str = "mixed",
    validate: bool = False,
    seed: int = 42,
) -> dict:
    """Generate training examples and write to JSONL. Returns stats."""
    rng = random.Random(seed)

    stats = {
        "generated": 0,
        "valid": 0,
        "invalid": 0,
        "by_type": {},
    }

    validate_fn = None
    if validate:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from validation.validate import validate_xml
        validate_fn = validate_xml

    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for gen_type in types:
        gen_fn = GENERATORS[gen_type]
        stats["by_type"][gen_type] = {"generated": 0, "valid": 0, "invalid": 0}

        for _ in range(count):
            if complexity == "mixed":
                c = rng.choice(["short", "medium", "long"])
            else:
                c = complexity

            example = gen_fn(complexity=c, rng=rng)
            stats["generated"] += 1
            stats["by_type"][gen_type]["generated"] += 1

            if validate_fn:
                result = validate_fn(example.output)
                if result["valid"]:
                    stats["valid"] += 1
                    stats["by_type"][gen_type]["valid"] += 1
                    rows.append(example)
                else:
                    stats["invalid"] += 1
                    stats["by_type"][gen_type]["invalid"] += 1
                    print(f"INVALID {gen_type}: {result['errors']}", file=sys.stderr)
            else:
                rows.append(example)

    with open(output_p, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(row.to_json() + "\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Generate X3D training examples")
    parser.add_argument("output", help="Output JSONL file path")
    parser.add_argument("--type", dest="types", default="all",
                        help="Generator types (comma-separated): indexed-face-set,extrusion,interpolator,all")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of examples per type (default: 10)")
    parser.add_argument("--complexity", choices=["short", "medium", "long", "mixed"],
                        default="mixed", help="Numeric complexity level (default: mixed)")
    parser.add_argument("--validate", action="store_true",
                        help="XSD-validate each generated example")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    args = parser.parse_args()

    if args.types == "all":
        types = list(GENERATORS.keys())
    else:
        types = [t.strip() for t in args.types.split(",")]
        for t in types:
            if t not in GENERATORS:
                print(f"Unknown type: {t}. Available: {list(GENERATORS.keys())}")
                sys.exit(1)

    stats = generate_examples(
        args.output, types,
        count=args.count,
        complexity=args.complexity,
        validate=args.validate,
        seed=args.seed,
    )

    print(f"Generated: {stats['generated']}")
    if args.validate:
        print(f"Valid: {stats['valid']}")
        print(f"Invalid: {stats['invalid']}")
    for gen_type, type_stats in stats["by_type"].items():
        print(f"  {gen_type}: {type_stats}")


if __name__ == "__main__":
    main()
