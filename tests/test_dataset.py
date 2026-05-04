"""Tests for dataset schema normalization (Issue #2)."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataset.schema import (
    TrainingExample,
    normalize_metadata,
    validate_example,
    METADATA_DEFAULTS,
)
from dataset.normalize import normalize_file
from dataset.validate_schema import validate_file


class TestNormalizeMetadata:
    def test_dict_passthrough(self):
        meta = {"complexity": "simple", "source": "original"}
        result = normalize_metadata(meta)
        assert result["complexity"] == "simple"
        assert result["source"] == "original"
        assert result["viewpoints"] == []

    def test_string_parsed_as_json(self):
        meta = '{"complexity": "complex", "source": "original"}'
        result = normalize_metadata(meta)
        assert result["complexity"] == "complex"
        assert result["source"] == "original"

    def test_plain_string_wrapped(self):
        meta = "just a description"
        result = normalize_metadata(meta)
        assert result["raw"] == "just a description"
        assert result["source"] == "original"

    def test_none_handled(self):
        result = normalize_metadata(None)
        assert result["raw"] == ""
        assert result["source"] == "original"

    def test_wrong_type_coerced(self):
        meta = {"complexity": 42, "viewpoints": "not a list"}
        result = normalize_metadata(meta)
        assert result["complexity"] == ""
        assert result["viewpoints"] == []

    def test_extra_fields_preserved(self):
        meta = {"complexity": "simple", "custom_field": "custom_value"}
        result = normalize_metadata(meta)
        assert result["custom_field"] == "custom_value"

    def test_all_defaults_filled(self):
        result = normalize_metadata({})
        for key, default in METADATA_DEFAULTS.items():
            assert result[key] == default


class TestValidateExample:
    def test_valid_example(self):
        d = {
            "instruction": "Create a box",
            "output": "<X3D>...</X3D>",
            "metadata": {"complexity": "simple"},
        }
        errors = validate_example(d)
        assert errors == []

    def test_missing_instruction(self):
        d = {"output": "<X3D>...</X3D>"}
        errors = validate_example(d)
        assert any("instruction" in e for e in errors)

    def test_empty_instruction(self):
        d = {"instruction": "  ", "output": "<X3D>...</X3D>"}
        errors = validate_example(d)
        assert any("empty" in e and "instruction" in e for e in errors)

    def test_missing_output(self):
        d = {"instruction": "Create a box"}
        errors = validate_example(d)
        assert any("output" in e for e in errors)

    def test_string_metadata_flagged(self):
        d = {
            "instruction": "Create a box",
            "output": "<X3D>...</X3D>",
            "metadata": "plain string",
        }
        errors = validate_example(d)
        assert any("string" in e for e in errors)

    def test_no_metadata_is_ok(self):
        d = {"instruction": "Create a box", "output": "<X3D>...</X3D>"}
        errors = validate_example(d)
        assert errors == []


class TestTrainingExample:
    def test_from_dict_with_struct_metadata(self):
        d = {
            "instruction": "Make a sphere",
            "output": "<X3D/>",
            "metadata": {"complexity": "simple", "source": "original"},
        }
        ex = TrainingExample.from_dict(d)
        assert ex.instruction == "Make a sphere"
        assert ex.metadata["complexity"] == "simple"

    def test_from_dict_with_string_metadata(self):
        d = {
            "instruction": "Make a sphere",
            "output": "<X3D/>",
            "metadata": "some description",
        }
        ex = TrainingExample.from_dict(d)
        assert ex.metadata["raw"] == "some description"
        assert ex.metadata["source"] == "original"

    def test_round_trip(self):
        d = {
            "instruction": "Make a sphere",
            "output": "<X3D/>",
            "metadata": {"complexity": "simple"},
        }
        ex = TrainingExample.from_dict(d)
        as_json = ex.to_json()
        restored = json.loads(as_json)
        assert restored["instruction"] == "Make a sphere"
        assert isinstance(restored["metadata"], dict)
        assert restored["metadata"]["complexity"] == "simple"


class TestNormalizeFile:
    def test_normalizes_mixed_metadata(self):
        rows = [
            {"instruction": "Box", "output": "<X3D/>", "metadata": {"complexity": "simple"}},
            {"instruction": "Sphere", "output": "<X3D/>", "metadata": "a string"},
            {"instruction": "Cone", "output": "<X3D/>"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            input_path = f.name

        output_path = input_path + ".out"
        stats = normalize_file(input_path, output_path)

        assert stats["total"] == 3
        assert stats["normalized"] == 3
        assert stats["string_metadata_fixed"] == 1
        assert stats["missing_metadata_fixed"] == 1

        with open(output_path) as f:
            output_rows = [json.loads(line) for line in f if line.strip()]
        assert len(output_rows) == 3
        for row in output_rows:
            assert isinstance(row["metadata"], dict)
            assert "source" in row["metadata"]

    def test_skips_invalid_rows(self):
        rows = [
            {"output": "<X3D/>"},
            {"instruction": "Box", "output": "<X3D/>"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            input_path = f.name

        output_path = input_path + ".out"
        stats = normalize_file(input_path, output_path)

        assert stats["total"] == 2
        assert stats["normalized"] == 1
        assert len(stats["errors"]) == 1


class TestValidateFile:
    def test_all_valid(self):
        rows = [
            {"instruction": "Box", "output": "<X3D/>", "metadata": {"complexity": "simple"}},
            {"instruction": "Sphere", "output": "<X3D/>", "metadata": {"source": "original"}},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            input_path = f.name

        report = validate_file(input_path)
        assert report["total"] == 2
        assert report["valid"] == 2
        assert report["invalid"] == 0

    def test_detects_string_metadata(self):
        rows = [
            {"instruction": "Box", "output": "<X3D/>", "metadata": "not a dict"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            input_path = f.name

        report = validate_file(input_path)
        assert report["invalid"] == 1
        assert any("string" in e for issue in report["issues"] for e in issue["errors"])
