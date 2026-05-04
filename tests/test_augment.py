"""Tests for augmentation pipeline (Issue #3)."""

import json
import sys
import random
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataset.schema import TrainingExample
from dataset.augment import (
    augment_instruction,
    augment_example,
    augment_file,
    mutate_x3d_colors,
    mutate_x3d_transforms,
    estimate_tokens,
)
from dataset.filter import filter_file


SAMPLE_X3D = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <Scene>
    <Transform translation="1.0 2.0 3.0">
      <Shape>
        <Appearance>
          <Material diffuseColor="0.8 0.2 0.1"/>
        </Appearance>
        <Box size="2.0 2.0 2.0"/>
      </Shape>
    </Transform>
  </Scene>
</X3D>"""


class TestAugmentInstruction:
    def test_returns_string(self):
        rng = random.Random(42)
        result = augment_instruction("Create a red box", 0.5, rng)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_diversity_zero_returns_original(self):
        rng = random.Random(42)
        result = augment_instruction("Create a red box", 0.0, rng)
        assert result == "Create a red box"

    def test_high_diversity_changes_text(self):
        rng = random.Random(42)
        original = "Create a large red sphere next to a small blue box"
        changed = False
        for _ in range(20):
            result = augment_instruction(original, 1.0, rng)
            if result != original:
                changed = True
                break
        assert changed


class TestMutateX3D:
    def test_color_mutation_stays_in_range(self):
        rng = random.Random(42)
        for _ in range(50):
            result = mutate_x3d_colors(SAMPLE_X3D, 1.0, rng)
            import re
            matches = re.findall(r'diffuseColor="([\d.\s]+)"', result)
            for match in matches:
                values = [float(v) for v in match.strip().split()]
                for v in values:
                    assert 0.0 <= v <= 1.0, f"Color out of range: {v}"

    def test_transform_mutation_changes_values(self):
        rng = random.Random(42)
        changed = False
        for _ in range(20):
            result = mutate_x3d_transforms(SAMPLE_X3D, 1.0, rng)
            if result != SAMPLE_X3D:
                changed = True
                break
        assert changed


class TestAugmentExample:
    def test_produces_augmented_source(self):
        example = TrainingExample(
            instruction="Create a red box",
            output=SAMPLE_X3D,
            metadata={"source": "original", "complexity": "simple",
                       "viewpoints": [], "node_types": [], "components": [],
                       "augmentation_params": {}, "numeric_complexity": "",
                       "sequence_lengths": {}, "raw": ""},
        )
        rng = random.Random(42)
        aug = augment_example(example, 0.5, 0.3, rng, 0)
        assert aug.metadata["source"] == "augmented"
        assert "augmentation_params" in aug.metadata
        assert aug.metadata["augmentation_params"]["instruction_diversity"] == 0.5
        assert aug.metadata["augmentation_params"]["x3d_mutation"] == 0.3

    def test_preserves_original_metadata_fields(self):
        example = TrainingExample(
            instruction="Create a sphere",
            output=SAMPLE_X3D,
            metadata={"source": "original", "complexity": "medium",
                       "viewpoints": ["front"], "node_types": ["Box"],
                       "components": ["Geometry3D"], "augmentation_params": {},
                       "numeric_complexity": "", "sequence_lengths": {}, "raw": ""},
        )
        rng = random.Random(42)
        aug = augment_example(example, 0.5, 0.3, rng, 0)
        assert aug.metadata["complexity"] == "medium"
        assert aug.metadata["viewpoints"] == ["front"]


class TestAugmentFile:
    def _write_sample(self):
        rows = [
            {"instruction": "Create a red box", "output": SAMPLE_X3D,
             "metadata": {"source": "original"}},
            {"instruction": "Create a blue sphere", "output": SAMPLE_X3D,
             "metadata": {"source": "original"}},
        ]
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        for row in rows:
            f.write(json.dumps(row) + "\n")
        f.close()
        return f.name

    def test_ratio_control(self):
        input_path = self._write_sample()
        output_path = input_path + ".aug"

        stats = augment_file(input_path, output_path, ratio=3, seed=42)
        assert stats["originals_read"] == 2
        assert stats["augmented_generated"] == 6
        assert stats["written"] == 6

        with open(output_path) as f:
            output_rows = [json.loads(line) for line in f if line.strip()]
        assert len(output_rows) == 6

    def test_max_tokens_filter(self):
        input_path = self._write_sample()
        output_path = input_path + ".aug"

        stats = augment_file(input_path, output_path, ratio=3, max_tokens=50, seed=42)
        assert stats["filtered_by_tokens"] > 0
        assert stats["written"] < stats["augmented_generated"]

    def test_reproducibility_with_seed(self):
        input_path = self._write_sample()
        out1 = input_path + ".aug1"
        out2 = input_path + ".aug2"

        augment_file(input_path, out1, ratio=3, seed=123)
        augment_file(input_path, out2, ratio=3, seed=123)

        with open(out1) as f:
            rows1 = f.readlines()
        with open(out2) as f:
            rows2 = f.readlines()
        assert rows1 == rows2

    def test_all_augmented_tagged(self):
        input_path = self._write_sample()
        output_path = input_path + ".aug"

        augment_file(input_path, output_path, ratio=2, seed=42)

        with open(output_path) as f:
            for line in f:
                row = json.loads(line)
                assert row["metadata"]["source"] == "augmented"


class TestFilterFile:
    def _write_mixed(self):
        rows = [
            {"instruction": "Box", "output": "short",
             "metadata": {"source": "original"}},
            {"instruction": "Sphere", "output": "short",
             "metadata": {"source": "augmented"}},
            {"instruction": "Cone", "output": "x" * 40000,
             "metadata": {"source": "original"}},
        ]
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        for row in rows:
            f.write(json.dumps(row) + "\n")
        f.close()
        return f.name

    def test_filter_by_source_original(self):
        input_path = self._write_mixed()
        output_path = input_path + ".filtered"

        stats = filter_file(input_path, output_path, source="original")
        assert stats["kept"] == 2
        assert stats["filtered_by_source"] == 1

    def test_filter_by_source_augmented(self):
        input_path = self._write_mixed()
        output_path = input_path + ".filtered"

        stats = filter_file(input_path, output_path, source="augmented")
        assert stats["kept"] == 1
        assert stats["filtered_by_source"] == 2

    def test_filter_by_tokens(self):
        input_path = self._write_mixed()
        output_path = input_path + ".filtered"

        stats = filter_file(input_path, output_path, max_tokens=100)
        assert stats["filtered_by_tokens"] > 0
        assert stats["kept"] < stats["total"]

    def test_filter_all_no_filter(self):
        input_path = self._write_mixed()
        output_path = input_path + ".filtered"

        stats = filter_file(input_path, output_path, source="all", max_tokens=0)
        assert stats["kept"] == stats["total"]
