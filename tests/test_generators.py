"""Tests for numeric sequence generators (Issue #4)."""

import json
import re
import sys
import random
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataset.generators.numeric_sequences import (
    generate_indexed_face_set,
    generate_extrusion,
    generate_interpolator,
)
from dataset.generate import generate_examples
from validation.validate import validate_xml


class TestIndexedFaceSet:
    def test_generates_valid_example(self):
        rng = random.Random(42)
        ex = generate_indexed_face_set(complexity="medium", rng=rng)
        assert ex.instruction
        assert "<IndexedFaceSet" in ex.output
        assert "<Coordinate" in ex.output

    def test_coord_index_has_terminators(self):
        rng = random.Random(42)
        ex = generate_indexed_face_set(complexity="medium", rng=rng)
        match = re.search(r"coordIndex='([^']+)'", ex.output)
        assert match
        indices = [int(x) for x in match.group(1).split()]
        assert -1 in indices
        assert indices[-1] == -1

    def test_coord_index_no_out_of_bounds(self):
        rng = random.Random(42)
        ex = generate_indexed_face_set(complexity="long", rng=rng)
        coord_match = re.search(r"point='([^']+)'", ex.output)
        index_match = re.search(r"coordIndex='([^']+)'", ex.output)
        assert coord_match and index_match

        coords = coord_match.group(1).split(",")
        num_coords = len(coords)
        indices = [int(x) for x in index_match.group(1).split()]
        for idx in indices:
            if idx != -1:
                assert 0 <= idx < num_coords, f"Index {idx} out of bounds (max {num_coords - 1})"

    def test_short_complexity_smaller_than_long(self):
        rng = random.Random(42)
        short = generate_indexed_face_set(complexity="short", rng=rng)
        rng2 = random.Random(42)
        long_ex = generate_indexed_face_set(complexity="long", rng=rng2)

        short_meta = short.metadata["sequence_lengths"]
        long_meta = long_ex.metadata["sequence_lengths"]
        assert short_meta["coord_count"] <= long_meta["coord_count"]

    def test_passes_xsd_validation(self):
        rng = random.Random(42)
        for complexity in ["short", "medium", "long"]:
            ex = generate_indexed_face_set(complexity=complexity, rng=rng)
            result = validate_xml(ex.output)
            assert result["valid"], f"{complexity}: {result['errors']}"

    def test_metadata_populated(self):
        rng = random.Random(42)
        ex = generate_indexed_face_set(complexity="medium", rng=rng)
        assert ex.metadata["source"] == "generated"
        assert ex.metadata["numeric_complexity"] == "medium"
        assert "coord_count" in ex.metadata["sequence_lengths"]
        assert "index_count" in ex.metadata["sequence_lengths"]
        assert "IndexedFaceSet" in ex.metadata["node_types"]


class TestExtrusion:
    def test_generates_valid_example(self):
        rng = random.Random(42)
        ex = generate_extrusion(complexity="medium", rng=rng)
        assert ex.instruction
        assert "<Extrusion" in ex.output

    def test_cross_section_is_closed(self):
        rng = random.Random(42)
        for _ in range(10):
            ex = generate_extrusion(complexity="medium", rng=rng)
            match = re.search(r"crossSection='([^']+)'", ex.output)
            assert match
            points = match.group(1).strip().split(",")
            first = points[0].strip()
            last = points[-1].strip()
            first_vals = [float(x) for x in first.split()]
            last_vals = [float(x) for x in last.split()]
            for a, b in zip(first_vals, last_vals):
                assert abs(a - b) < 0.001, f"Cross-section not closed: first={first}, last={last}"

    def test_passes_xsd_validation(self):
        rng = random.Random(42)
        for complexity in ["short", "medium", "long"]:
            ex = generate_extrusion(complexity=complexity, rng=rng)
            result = validate_xml(ex.output)
            assert result["valid"], f"{complexity}: {result['errors']}"

    def test_metadata_has_sequence_lengths(self):
        rng = random.Random(42)
        ex = generate_extrusion(complexity="long", rng=rng)
        sl = ex.metadata["sequence_lengths"]
        assert "cross_section_points" in sl
        assert "spine_points" in sl
        assert "scale_points" in sl


class TestInterpolator:
    def test_generates_valid_example(self):
        rng = random.Random(42)
        ex = generate_interpolator(complexity="medium", rng=rng)
        assert ex.instruction
        assert "Interpolator" in ex.output or "TimeSensor" in ex.output

    def test_key_value_counts_match(self):
        rng = random.Random(42)
        for _ in range(20):
            ex = generate_interpolator(complexity="medium", rng=rng)
            key_match = re.search(r"key='([^']+)'", ex.output)
            value_match = re.search(r"keyValue='([^']+)'", ex.output)
            assert key_match and value_match

            keys = key_match.group(1).strip().split()
            values = value_match.group(1).strip().split()
            key_count = len(keys)

            if "ColorInterpolator" in ex.output:
                assert len(values) == key_count * 3
            elif "CoordinateInterpolator" in ex.output:
                assert len(values) % key_count == 0
            elif "OrientationInterpolator" in ex.output:
                assert len(values) == key_count * 4
            elif "PositionInterpolator" in ex.output:
                assert len(values) == key_count * 3
            elif "ScalarInterpolator" in ex.output:
                assert len(values) == key_count

    def test_passes_xsd_validation(self):
        rng = random.Random(42)
        for complexity in ["short", "medium", "long"]:
            for _ in range(5):
                ex = generate_interpolator(complexity=complexity, rng=rng)
                result = validate_xml(ex.output)
                assert result["valid"], f"{complexity}: {result['errors']}"

    def test_has_routes(self):
        rng = random.Random(42)
        ex = generate_interpolator(complexity="medium", rng=rng)
        assert "<ROUTE" in ex.output
        assert "fromNode='Clock'" in ex.output
        assert "fromNode='Interp'" in ex.output

    def test_long_has_more_values_than_short(self):
        rng = random.Random(42)
        short = generate_interpolator(complexity="short", rng=rng)
        rng2 = random.Random(42)
        long_ex = generate_interpolator(complexity="long", rng=rng2)

        assert short.metadata["sequence_lengths"]["key_count"] < \
               long_ex.metadata["sequence_lengths"]["key_count"]


class TestGenerateExamples:
    def test_generates_all_types(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            output_path = f.name

        stats = generate_examples(
            output_path,
            types=["indexed-face-set", "extrusion", "interpolator"],
            count=3,
            complexity="medium",
            validate=True,
            seed=42,
        )

        assert stats["generated"] == 9
        assert stats["invalid"] == 0

        with open(output_path) as f:
            rows = [json.loads(line) for line in f if line.strip()]
        assert len(rows) == 9

    def test_mixed_complexity(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            output_path = f.name

        stats = generate_examples(
            output_path,
            types=["indexed-face-set"],
            count=10,
            complexity="mixed",
            validate=True,
            seed=42,
        )

        with open(output_path) as f:
            rows = [json.loads(line) for line in f if line.strip()]

        complexities = set(r["metadata"]["numeric_complexity"] for r in rows)
        assert len(complexities) > 1

    def test_all_pass_validation(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            output_path = f.name

        stats = generate_examples(
            output_path,
            types=["indexed-face-set", "extrusion", "interpolator"],
            count=5,
            complexity="mixed",
            validate=True,
            seed=42,
        )

        assert stats["invalid"] == 0
        assert stats["valid"] == stats["generated"]
