"""Cross-validate X3D Ontology containment answers against the XSD.

For each ontology-predicted (parent, field, child) triple, generate a
minimal X3D document placing the child under the parent (with the
admitting field as containerField when it is not the child's default)
and validate it against the bundled X3D 4.1 XSD. Also run negative
controls: (parent, child) pairs the ontology does NOT predict, to see
whether the XSD rejects them.

This measures how the two spec artifacts agree, and quantifies the
"ontology answers are advisory" caveat in both directions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lxml import etree

from validation.validate import validate_xml
from x3d_utils.ontology import get_ontology
from x3d_utils.x3duom import get_x3duom


# Wrapper context needed to legally place a parent node under Scene,
# keyed by the parent's own default containerField. Without this, a
# geometry-node parent (say IndexedFaceSet) is itself rejected under
# Scene and the child placement is never exercised.
_WRAP = {
    "geometry": ("<Shape>", "</Shape>"),
    "appearance": ("<Shape>", "</Shape>"),
    "material": ("<Shape><Appearance>", "</Appearance></Shape>"),
    "texture": ("<Shape><Appearance>", "</Appearance></Shape>"),
    "coord": ("<Shape><IndexedFaceSet>", "</IndexedFaceSet></Shape>"),
    "color": ("<Shape><IndexedFaceSet>", "</IndexedFaceSet></Shape>"),
    "normal": ("<Shape><IndexedFaceSet>", "</IndexedFaceSet></Shape>"),
    "texCoord": ("<Shape><IndexedFaceSet>", "</IndexedFaceSet></Shape>"),
    "layers": ("<LayerSet>", "</LayerSet>"),
    "emitter": ("<ParticleSystem>", "</ParticleSystem>"),
    "physics": ("<ParticleSystem>", "</ParticleSystem>"),
    "joints": ("<HAnimHumanoid>", "</HAnimHumanoid>"),
    "segments": ("<HAnimHumanoid>", "</HAnimHumanoid>"),
    "trimmingContour": ("<Shape><NurbsTrimmedSurface>",
                        "</NurbsTrimmedSurface></Shape>"),
}


def minimal_doc(parent: str, child: str, container_field: str | None,
                parent_cf: str | None) -> str:
    cf = f" containerField='{container_field}'" if container_field else ""
    pre, post = _WRAP.get(parent_cf or "children", ("", ""))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<X3D profile='Full' version='4.1'>
  <Scene>
    {pre}<{parent}>
      <{child}{cf}/>
    </{parent}>{post}
  </Scene>
</X3D>"""


def main(child_types: list[str]):
    onto = get_ontology()
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()

    for child in child_types:
        default_cf = nodes.get(child, {}).get("containerField")
        rows = onto.node_parents(child)
        predicted = [(r["parent"], r["field"]) for r in rows
                     if r["parent"] in nodes]  # concrete parents only

        agree, disagree, results, inconclusive = 0, 0, [], []
        for parent, field in predicted:
            # containerField attribute: the ontology's admitting field name,
            # stripping the has* accessor prefix used by some properties
            cf = field
            if cf.startswith("has"):
                cf = cf[3:4].lower() + cf[4:]
            cf_attr = None if cf == default_cf else cf
            parent_cf = nodes.get(parent, {}).get("containerField")
            doc = minimal_doc(parent, child, cf_attr, parent_cf)
            v = validate_xml(doc)
            ok = v["valid"]
            if not ok and "Line 5" not in v["errors"][0] \
                    and f"<{child}" not in v["errors"][0]:
                # the child element line moved; detect by message target
                pass
            if not ok and f"'{child}'" not in v["errors"][0]:
                inconclusive.append((parent, field, v["errors"][0][:80]))
                continue
            agree += ok
            disagree += not ok
            if not ok:
                results.append((parent, field, v["errors"][0][:90]))

        print(f"\n=== child: {child} (default containerField: {default_cf}) ===")
        print(f"ontology-predicted concrete parents: {len(predicted)}")
        print(f"  XSD agrees (validates):   {agree}")
        print(f"  XSD disagrees (rejects):  {disagree}")
        print(f"  harness-inconclusive:     {len(inconclusive)}")
        seen = set()
        for parent, field, err in results:
            if parent in seen: continue
            seen.add(parent)
            print(f"    REJECTED {parent} via {field}")

        # Negative controls: parents the ontology did not predict
        controls = ["Material", "Appearance", "Box", "TimeSensor",
                    "Viewpoint", "Color"]
        controls = [c for c in controls
                    if c in nodes and c not in {p for p, _ in predicted}]
        false_accepts = []
        for parent in controls:
            parent_cf = nodes.get(parent, {}).get("containerField")
            doc = minimal_doc(parent, child, None, parent_cf)
            if validate_xml(doc)["valid"]:
                false_accepts.append(parent)
        print(f"  negative controls tested: {len(controls)}; "
              f"XSD wrongly-ish accepts: {false_accepts or 'none'}")


if __name__ == "__main__":
    types = sys.argv[1:] or ["Sphere", "Material", "Appearance",
                             "PointLight", "TimeSensor", "Coordinate"]
    main(types)
