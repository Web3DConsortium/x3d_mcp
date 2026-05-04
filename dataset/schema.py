"""Canonical schema for X3D training dataset examples."""

import json
from dataclasses import dataclass, field, asdict
from typing import Optional


METADATA_FIELDS = {
    "complexity": str,
    "viewpoints": list,
    "node_types": list,
    "components": list,
    "source": str,
    "augmentation_params": dict,
    "numeric_complexity": str,
    "sequence_lengths": dict,
    "raw": str,
}

METADATA_DEFAULTS = {
    "complexity": "",
    "viewpoints": [],
    "node_types": [],
    "components": [],
    "source": "original",
    "augmentation_params": {},
    "numeric_complexity": "",
    "sequence_lengths": {},
    "raw": "",
}


@dataclass
class TrainingExample:
    instruction: str
    output: str
    metadata: dict = field(default_factory=lambda: dict(METADATA_DEFAULTS))

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "TrainingExample":
        instruction = d.get("instruction", "")
        output = d.get("output", "")
        raw_meta = d.get("metadata", {})
        metadata = normalize_metadata(raw_meta)
        return cls(instruction=instruction, output=output, metadata=metadata)


def normalize_metadata(raw) -> dict:
    """Normalize metadata to a consistent dict with all expected fields."""
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return _fill_defaults(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        result = dict(METADATA_DEFAULTS)
        result["raw"] = raw
        return result

    if isinstance(raw, dict):
        return _fill_defaults(raw)

    result = dict(METADATA_DEFAULTS)
    result["raw"] = str(raw) if raw is not None else ""
    return result


def _fill_defaults(d: dict) -> dict:
    """Fill missing metadata fields with defaults, coerce types."""
    result = {}
    for key, expected_type in METADATA_FIELDS.items():
        val = d.get(key, METADATA_DEFAULTS[key])
        if not isinstance(val, expected_type):
            val = METADATA_DEFAULTS[key]
        result[key] = val
    for key, val in d.items():
        if key not in METADATA_FIELDS:
            result[key] = val
    return result


def validate_example(d: dict) -> list[str]:
    """Validate a raw dict against the training example schema. Returns list of errors."""
    errors = []
    if "instruction" not in d or not isinstance(d.get("instruction"), str):
        errors.append("missing or non-string 'instruction' field")
    if "output" not in d or not isinstance(d.get("output"), str):
        errors.append("missing or non-string 'output' field")
    if "instruction" in d and not d["instruction"].strip():
        errors.append("empty 'instruction' field")
    if "output" in d and not d["output"].strip():
        errors.append("empty 'output' field")

    raw_meta = d.get("metadata")
    if raw_meta is not None:
        if isinstance(raw_meta, str):
            errors.append("metadata is a plain string (should be a dict)")
        elif not isinstance(raw_meta, dict):
            errors.append(f"metadata is {type(raw_meta).__name__} (should be a dict)")

    return errors
