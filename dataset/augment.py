"""Tunable augmentation pipeline for X3D training data.

Usage:
    python -m dataset.augment base.jsonl augmented.jsonl \
        --ratio 5 --seed 42 \
        --instruction-diversity 0.5 \
        --x3d-mutation 0.3 \
        --max-tokens 8192
"""

import json
import re
import copy
import random
import argparse
import sys
import math
from pathlib import Path

from dataset.schema import TrainingExample


SYNONYM_MAP = {
    "create": ["generate", "build", "make", "construct", "produce"],
    "scene": ["environment", "world", "setting", "space"],
    "red": ["crimson", "scarlet", "ruby"],
    "blue": ["azure", "cobalt", "navy", "sapphire"],
    "green": ["emerald", "lime", "jade"],
    "white": ["ivory", "pearl", "snow"],
    "black": ["ebony", "onyx", "jet"],
    "small": ["tiny", "compact", "little", "miniature"],
    "large": ["big", "huge", "massive", "enormous"],
    "sphere": ["ball", "globe", "orb"],
    "box": ["cube", "block", "rectangular solid"],
    "cylinder": ["tube", "column", "pillar"],
    "cone": ["pointed shape", "conical form", "tapered cylinder"],
    "rotate": ["spin", "turn", "revolve"],
    "move": ["translate", "shift", "displace"],
    "color": ["hue", "shade", "tint"],
    "bright": ["vivid", "brilliant", "luminous"],
    "dark": ["dim", "shadowy", "muted"],
    "above": ["over", "on top of", "higher than"],
    "below": ["under", "beneath", "lower than"],
    "next to": ["beside", "adjacent to", "alongside"],
    "animation": ["motion", "movement", "animated behavior"],
    "3D": ["three-dimensional", "3-dimensional"],
    "simple": ["basic", "minimal", "straightforward"],
    "complex": ["detailed", "intricate", "elaborate"],
}

INSTRUCTION_TEMPLATES = [
    "Create {description}",
    "Generate {description}",
    "Build {description}",
    "Make {description}",
    "Produce {description}",
    "Design {description}",
    "Construct {description}",
    "Model {description}",
]

GEOMETRY_SWAPS = {
    "Box": "Cylinder",
    "Cylinder": "Box",
    "Sphere": "Cone",
    "Cone": "Sphere",
}

COLOR_PATTERN = re.compile(
    r'(diffuseColor|emissiveColor|specularColor|color)\s*=\s*["\']'
    r'([\d.\-\s]+)["\']'
)

FLOAT_ATTR_PATTERN = re.compile(
    r'(translation|scale|size|radius|height)\s*=\s*["\']'
    r'([\d.\-\s]+)["\']'
)

ROTATION_PATTERN = re.compile(
    r'(rotation)\s*=\s*["\']'
    r'([\d.\-\s]+)["\']'
)


def augment_instruction(instruction: str, diversity: float, rng: random.Random) -> str:
    """Augment instruction text with synonym replacement and restructuring."""
    result = instruction

    if rng.random() < diversity * 0.5:
        lower = result.lower()
        for original, synonyms in SYNONYM_MAP.items():
            if original in lower and rng.random() < diversity:
                replacement = rng.choice(synonyms)
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                result = pattern.sub(replacement, result, count=1)

    if rng.random() < diversity * 0.3:
        template = rng.choice(INSTRUCTION_TEMPLATES)
        sentences = result.split(".")
        core = sentences[0].strip()
        for prefix in ["Create ", "Generate ", "Build ", "Make ", "Produce ",
                       "Design ", "Construct ", "Model "]:
            if core.startswith(prefix):
                core = core[len(prefix):]
                break
        core = core.strip().lstrip("aA ").strip()
        if core:
            result = template.format(description=core)
            if len(sentences) > 1:
                result += ". " + ". ".join(s.strip() for s in sentences[1:] if s.strip())

    return result


def mutate_x3d_colors(x3d: str, mutation: float, rng: random.Random) -> str:
    """Mutate color values in X3D output within valid [0,1] range."""
    def replace_color(match):
        attr = match.group(1)
        values = match.group(2).strip().split()
        mutated = []
        for v in values:
            try:
                f = float(v)
                delta = rng.gauss(0, mutation * 0.3)
                f = max(0.0, min(1.0, f + delta))
                mutated.append(f"{f:.4f}")
            except ValueError:
                mutated.append(v)
        return f'{attr}="{" ".join(mutated)}"'

    if rng.random() < mutation:
        x3d = COLOR_PATTERN.sub(replace_color, x3d)
    return x3d


def mutate_x3d_transforms(x3d: str, mutation: float, rng: random.Random) -> str:
    """Mutate translation, scale, size values in X3D output."""
    def replace_float_attr(match):
        attr = match.group(1)
        values = match.group(2).strip().split()
        mutated = []
        for v in values:
            try:
                f = float(v)
                if attr == "scale":
                    delta = rng.gauss(0, mutation * 0.5)
                    f = max(0.1, f + delta)
                elif attr == "radius" or attr == "height":
                    delta = rng.gauss(0, mutation * f * 0.3)
                    f = max(0.01, f + delta)
                else:
                    delta = rng.gauss(0, mutation * 2.0)
                    f = f + delta
                mutated.append(f"{f:.4f}")
            except ValueError:
                mutated.append(v)
        return f'{attr}="{" ".join(mutated)}"'

    if rng.random() < mutation:
        x3d = FLOAT_ATTR_PATTERN.sub(replace_float_attr, x3d)
    return x3d


def mutate_x3d_rotations(x3d: str, mutation: float, rng: random.Random) -> str:
    """Mutate rotation values in X3D output."""
    def replace_rotation(match):
        attr = match.group(1)
        values = match.group(2).strip().split()
        if len(values) == 4:
            axis = values[:3]
            try:
                angle = float(values[3])
                angle += rng.gauss(0, mutation * math.pi * 0.25)
                return f'{attr}="{" ".join(axis)} {angle:.4f}"'
            except ValueError:
                pass
        return match.group(0)

    if rng.random() < mutation:
        x3d = ROTATION_PATTERN.sub(replace_rotation, x3d)
    return x3d


def mutate_x3d_geometry(x3d: str, mutation: float, rng: random.Random) -> str:
    """Swap compatible geometry types."""
    if rng.random() < mutation * 0.3:
        for original, replacement in GEOMETRY_SWAPS.items():
            if f"<{original}" in x3d and rng.random() < 0.5:
                x3d = x3d.replace(f"<{original}", f"<{replacement}", 1)
                x3d = x3d.replace(f"</{original}>", f"</{replacement}>", 1)
                break
    return x3d


def augment_example(
    example: TrainingExample,
    instruction_diversity: float,
    x3d_mutation: float,
    rng: random.Random,
    augment_index: int,
) -> TrainingExample:
    """Produce one augmented example from an original."""
    new_instruction = augment_instruction(example.instruction, instruction_diversity, rng)

    new_output = example.output
    new_output = mutate_x3d_colors(new_output, x3d_mutation, rng)
    new_output = mutate_x3d_transforms(new_output, x3d_mutation, rng)
    new_output = mutate_x3d_rotations(new_output, x3d_mutation, rng)
    new_output = mutate_x3d_geometry(new_output, x3d_mutation, rng)

    new_metadata = copy.deepcopy(example.metadata)
    new_metadata["source"] = "augmented"
    new_metadata["augmentation_params"] = {
        "instruction_diversity": instruction_diversity,
        "x3d_mutation": x3d_mutation,
        "augment_index": augment_index,
    }

    return TrainingExample(
        instruction=new_instruction,
        output=new_output,
        metadata=new_metadata,
    )


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (chars / 4)."""
    return len(text) // 4


def augment_file(
    input_path: str,
    output_path: str,
    ratio: int = 5,
    instruction_diversity: float = 0.5,
    x3d_mutation: float = 0.3,
    max_tokens: int = 0,
    seed: int = 42,
) -> dict:
    """Augment a JSONL file. Returns stats."""
    rng = random.Random(seed)
    input_p = Path(input_path)
    output_p = Path(output_path)

    stats = {
        "originals_read": 0,
        "augmented_generated": 0,
        "filtered_by_tokens": 0,
        "written": 0,
    }

    examples = []
    with open(input_p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            examples.append(TrainingExample.from_dict(raw))
            stats["originals_read"] += 1

    output_rows = []
    for example in examples:
        for i in range(ratio):
            aug = augment_example(example, instruction_diversity, x3d_mutation, rng, i)
            stats["augmented_generated"] += 1

            if max_tokens > 0:
                total = estimate_tokens(aug.instruction) + estimate_tokens(aug.output)
                if total > max_tokens:
                    stats["filtered_by_tokens"] += 1
                    continue

            output_rows.append(aug)
            stats["written"] += 1

    output_p.parent.mkdir(parents=True, exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(row.to_json() + "\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Augment X3D training data")
    parser.add_argument("input", help="Input JSONL file (base/hand-authored examples)")
    parser.add_argument("output", help="Output JSONL file (augmented examples)")
    parser.add_argument("--ratio", type=int, default=5,
                        help="Augmented examples per original (default: 5)")
    parser.add_argument("--instruction-diversity", type=float, default=0.5,
                        help="Instruction variation level 0.0-1.0 (default: 0.5)")
    parser.add_argument("--x3d-mutation", type=float, default=0.3,
                        help="X3D output mutation level 0.0-1.0 (default: 0.3)")
    parser.add_argument("--max-tokens", type=int, default=0,
                        help="Filter examples exceeding token estimate (0 = no filter)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    stats = augment_file(
        args.input, args.output,
        ratio=args.ratio,
        instruction_diversity=args.instruction_diversity,
        x3d_mutation=args.x3d_mutation,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )

    print(f"Originals read: {stats['originals_read']}")
    print(f"Augmented generated: {stats['augmented_generated']}")
    print(f"Filtered by tokens: {stats['filtered_by_tokens']}")
    print(f"Written: {stats['written']}")


if __name__ == "__main__":
    main()
