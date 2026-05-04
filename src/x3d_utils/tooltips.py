"""Parser for X3D tooltips profile XML.

Extracts per-node and per-field tooltip descriptions, authoring hints,
warnings, spec references, and type annotations.
Uses x3d-4.0.profile.xml (4.1 profile not yet published by Web3D Consortium).
"""

import re
from pathlib import Path
from lxml import etree


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "validation" / "schemas"
TOOLTIPS_PATH = SCHEMAS_DIR / "x3d-4.0.profile.xml"


def _split_tooltip(raw: str) -> dict:
    """Parse a tooltip string into structured parts."""
    lines = raw.replace("&#10;", "\n").split("\n")
    lines = [l.strip() for l in lines if l.strip()]

    description_parts = []
    hints = []
    warnings = []
    spec_urls = []

    url_re = re.compile(r'https?://\S+')

    for line in lines:
        if line.startswith("Hint:"):
            text = line[5:].strip()
            hints.append(text)
            for url in url_re.findall(text):
                spec_urls.append(url)
        elif line.startswith("Warning:"):
            text = line[8:].strip()
            warnings.append(text)
            for url in url_re.findall(text):
                spec_urls.append(url)
        else:
            description_parts.append(line)
            for url in url_re.findall(line):
                spec_urls.append(url)

    description = " ".join(description_parts)

    base_type = ""
    bt_match = re.match(r'^\[([^\]]+)\]', description)
    if bt_match:
        base_type = bt_match.group(1)
        description = description[bt_match.end():].strip()

    return {
        "description": description,
        "baseType": base_type,
        "hints": hints,
        "warnings": warnings,
        "specUrls": spec_urls,
    }


class X3DTooltips:
    """Parsed representation of the X3D tooltips profile."""

    def __init__(self, path: Path = TOOLTIPS_PATH):
        parser = etree.XMLParser(recover=True, resolve_entities=False)
        self._tree = etree.parse(str(path), parser)
        self._root = self._tree.getroot()
        self._nodes = None

    def get_nodes(self) -> dict:
        """Return dict of node_name -> {tooltip, baseType, hints, warnings, specUrls, fields}."""
        if self._nodes is not None:
            return self._nodes

        result = {}
        for elem in self._root.iter("element"):
            name = elem.get("name")
            if not name:
                continue

            raw_tooltip = elem.get("tooltip", "")
            node_info = _split_tooltip(raw_tooltip)

            fields = {}
            for attr in elem.iterchildren("attribute"):
                attr_name = attr.get("name")
                if not attr_name:
                    continue
                attr_tooltip = attr.get("tooltip", "")
                field_info = _split_tooltip(attr_tooltip)
                fields[attr_name] = field_info

            node_info["fields"] = fields
            result[name] = node_info

        self._nodes = result
        return result

    def get_node_tooltip(self, node_name: str) -> dict | None:
        """Return tooltip info for a specific node."""
        nodes = self.get_nodes()
        return nodes.get(node_name)

    def get_field_tooltip(self, node_name: str, field_name: str) -> dict | None:
        """Return tooltip info for a specific field on a node."""
        node = self.get_node_tooltip(node_name)
        if node is None:
            return None
        return node["fields"].get(field_name)

    def get_node_names(self) -> list[str]:
        """Return sorted list of all node names in tooltips."""
        return sorted(self.get_nodes().keys())


_instance = None


def get_tooltips() -> X3DTooltips:
    """Return the cached X3DTooltips singleton."""
    global _instance
    if _instance is None:
        _instance = X3DTooltips()
    return _instance
