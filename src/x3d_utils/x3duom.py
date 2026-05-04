"""Parser for X3D Unified Object Model (X3DUOM) 4.1.

Loads X3dUnifiedObjectModel-4.1.xml and provides lookup tables for
node types, fields, components, profiles, and field types.
"""

from pathlib import Path
from lxml import etree


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "validation" / "schemas"
X3DUOM_PATH = SCHEMAS_DIR / "X3dUnifiedObjectModel-4.1.xml"


class X3DUOM:
    """Parsed representation of the X3D Unified Object Model."""

    def __init__(self, path: Path = X3DUOM_PATH):
        self._tree = etree.parse(str(path))
        self._root = self._tree.getroot()
        self._concrete_nodes = None
        self._abstract_types = None
        self._field_types = None
        self._components = None

    def get_field_types(self) -> dict:
        """Return dict of type_name -> {isArray, tupleSize, defaultValue, regex}."""
        if self._field_types is not None:
            return self._field_types
        result = {}
        for ft in self._root.iter("FieldType"):
            name = ft.get("type")
            result[name] = {
                "isArray": ft.get("isArray") == "true",
                "tupleSize": int(ft.get("tupleSize", "1")),
                "defaultValue": ft.get("defaultValue", ""),
                "regex": ft.get("regex", ""),
            }
        self._field_types = result
        return result

    def get_abstract_types(self) -> dict:
        """Return dict of abstract_type_name -> {baseType, component, level, fields}."""
        if self._abstract_types is not None:
            return self._abstract_types
        result = {}
        for section_tag in ("AbstractObjectTypes", "AbstractNodeTypes"):
            for atype in self._root.iter(section_tag):
                for node in atype:
                    if node.tag in ("AbstractObjectType", "AbstractNodeType"):
                        name = node.get("name")
                        idef = node.find("InterfaceDefinition")
                        base_type = None
                        component = None
                        level = None
                        fields = []
                        if idef is not None:
                            inh = idef.find("Inheritance")
                            if inh is not None:
                                base_type = inh.get("baseType")
                            comp = idef.find("componentInfo")
                            if comp is not None:
                                component = comp.get("name")
                                level = int(comp.get("level", "0"))
                            fields = self._parse_fields(idef)
                        result[name] = {
                            "baseType": base_type,
                            "component": component,
                            "level": level,
                            "fields": fields,
                        }
        self._abstract_types = result
        return result

    def get_concrete_nodes(self) -> dict:
        """Return dict of node_name -> {component, level, baseType, fields, containerField}."""
        if self._concrete_nodes is not None:
            return self._concrete_nodes
        result = {}
        for cnode in self._root.iter("ConcreteNode"):
            name = cnode.get("name")
            idef = cnode.find("InterfaceDefinition")
            base_type = None
            component = None
            level = None
            container_field = None
            fields = []
            if idef is not None:
                inh = idef.find("Inheritance")
                if inh is not None:
                    base_type = inh.get("baseType")
                comp = idef.find("componentInfo")
                if comp is not None:
                    component = comp.get("name")
                    level = int(comp.get("level", "0"))
                cf = idef.find("containerField")
                if cf is not None:
                    container_field = cf.get("default")
                fields = self._parse_fields(idef)
            result[name] = {
                "component": component,
                "level": level,
                "baseType": base_type,
                "fields": fields,
                "containerField": container_field,
            }
        self._concrete_nodes = result
        return result

    def get_node_fields(self, node_name: str) -> list[dict]:
        """Return list of field dicts for a concrete node, including inherited fields."""
        nodes = self.get_concrete_nodes()
        node = nodes.get(node_name)
        if node is None:
            return []
        return node["fields"]

    def get_components(self) -> dict:
        """Return dict of component_name -> list of concrete node names."""
        nodes = self.get_concrete_nodes()
        result = {}
        for name, info in nodes.items():
            comp = info["component"]
            if comp:
                result.setdefault(comp, []).append(name)
        for comp in result:
            result[comp].sort()
        return result

    def get_profiles(self) -> dict:
        """Return dict of profile_name -> {appinfo, documentation}."""
        result = {}
        for st in self._root.iter("SimpleType"):
            if st.get("name") == "profileNameChoices":
                for enum in st.iter("enumeration"):
                    result[enum.get("value")] = {
                        "appinfo": enum.get("appinfo", ""),
                        "documentation": enum.get("documentation", ""),
                    }
                break
        return result

    def get_container_field(self, node_name: str) -> str | None:
        """Return the default containerField for a concrete node."""
        nodes = self.get_concrete_nodes()
        node = nodes.get(node_name)
        if node is None:
            return None
        return node["containerField"]

    def get_enriched_node(self, node_name: str) -> dict | None:
        """Return node info with tooltip data merged into fields."""
        from x3d_utils.tooltips import get_tooltips

        nodes = self.get_concrete_nodes()
        node = nodes.get(node_name)
        if node is None:
            return None

        tips = get_tooltips()
        node_tip = tips.get_node_tooltip(node_name)

        result = dict(node)
        if node_tip:
            result["tooltip"] = node_tip["description"]
            result["hints"] = node_tip["hints"]
            result["warnings"] = node_tip["warnings"]
            result["specUrls"] = node_tip["specUrls"]
        else:
            result["tooltip"] = ""
            result["hints"] = []
            result["warnings"] = []
            result["specUrls"] = []

        enriched_fields = []
        for f in node["fields"]:
            ef = dict(f)
            if node_tip:
                field_tip = node_tip["fields"].get(f["name"])
                if field_tip:
                    ef["tooltip"] = field_tip["description"]
                    ef["hints"] = field_tip["hints"]
                    ef["warnings"] = field_tip["warnings"]
                    ef["specUrls"] = field_tip["specUrls"]
                else:
                    ef["tooltip"] = ""
                    ef["hints"] = []
                    ef["warnings"] = []
                    ef["specUrls"] = []
            else:
                ef["tooltip"] = ""
                ef["hints"] = []
                ef["warnings"] = []
                ef["specUrls"] = []
            enriched_fields.append(ef)
        result["fields"] = enriched_fields
        return result

    def get_coverage_report(self) -> dict:
        """Compare X3DUOM nodes/fields with tooltips. Returns drift report."""
        from x3d_utils.tooltips import get_tooltips

        tips = get_tooltips()
        tip_nodes = tips.get_nodes()
        uom_nodes = self.get_concrete_nodes()

        uom_only = sorted(set(uom_nodes.keys()) - set(tip_nodes.keys()))
        tips_only = sorted(set(tip_nodes.keys()) - set(uom_nodes.keys()))
        common = sorted(set(uom_nodes.keys()) & set(tip_nodes.keys()))

        field_drift = {}
        for node_name in common:
            uom_fields = {f["name"] for f in uom_nodes[node_name]["fields"]}
            tip_fields = set(tip_nodes[node_name]["fields"].keys())
            uom_only_fields = sorted(uom_fields - tip_fields)
            tip_only_fields = sorted(tip_fields - uom_fields)
            if uom_only_fields or tip_only_fields:
                field_drift[node_name] = {
                    "uom_only": uom_only_fields,
                    "tips_only": tip_only_fields,
                }

        return {
            "uom_node_count": len(uom_nodes),
            "tips_node_count": len(tip_nodes),
            "common_nodes": len(common),
            "uom_only_nodes": uom_only,
            "tips_only_nodes": tips_only,
            "field_drift": field_drift,
        }

    def _parse_fields(self, idef: etree._Element) -> list[dict]:
        """Extract field definitions from an InterfaceDefinition element."""
        fields = []
        for field in idef.iterchildren("field"):
            f = {
                "name": field.get("name"),
                "type": field.get("type"),
                "accessType": field.get("accessType"),
                "default": field.get("default"),
                "description": field.get("description", ""),
            }
            if field.get("inheritedFrom"):
                f["inheritedFrom"] = field.get("inheritedFrom")
            if field.get("acceptableNodeTypes"):
                f["acceptableNodeTypes"] = field.get("acceptableNodeTypes")
            if field.get("minInclusive"):
                f["minInclusive"] = field.get("minInclusive")
            if field.get("maxInclusive"):
                f["maxInclusive"] = field.get("maxInclusive")
            fields.append(f)
        return fields


# Module-level singleton
_instance = None


def get_x3duom() -> X3DUOM:
    """Return the cached X3DUOM singleton."""
    global _instance
    if _instance is None:
        _instance = X3DUOM()
    return _instance
