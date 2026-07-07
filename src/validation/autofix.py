"""Auto-fix for containerField mistakes -- returns a corrected X3D document.

The companion to the containerField semantic check: rather than only telling the
author the right containerField, this rewrites it. It only touches containerField
attributes (it never moves, adds, or deletes nodes), so the fix is conservative.

Some placements are ambiguous (an ImageTexture under a PhysicalMaterial could be
baseTexture, normalTexture, ...). For those it picks the conventional slot and
flags the change `ambiguous` with the alternatives, so the caller can override.
USE-before-DEF ordering is *not* auto-fixed -- reordering the scene graph is
structural and intent-dependent; the validator reports it for a human decision.
"""

from lxml import etree

from x3d_utils.x3duom import get_x3duom
from validation.semantic import (
    _local_tag, _type_ancestry, _node_field_map, _field_accepts, _NODE_FIELD_TYPES,
)

# Conventional "primary" slots, chosen first when several fields accept the node.
_PREFERRED = [
    "skeleton", "geometry", "appearance", "material", "coord", "color", "normal",
    "fogCoord", "texCoord", "baseTexture", "emissiveTexture", "skin", "children",
]


def _pick(candidates: list[str], child: etree._Element, pfields: dict) -> str:
    """Choose the best containerField among the fields that accept this node."""
    if child.get("USE") is not None:
        # USE references belong in list (MFNode) fields -- joints/segments/sites/...
        mfnode = [c for c in candidates if pfields[c].get("type") == "MFNode"]
        if mfnode:
            return mfnode[0]
        return candidates[0]
    pref = [c for c in _PREFERRED if c in candidates]
    return pref[0] if pref else candidates[0]


def autofix_containerfields(xml_string: str) -> dict:
    """Return {fixed, changes, unfixable} -- fixed is the corrected X3D document."""
    try:
        root = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        return {"error": f"Parse error: {exc}", "fixed": "", "changes": [], "unfixable": []}

    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    abstracts = uom.get_abstract_types()

    changes: list[dict] = []
    unfixable: list[dict] = []

    for parent in root.iter():
        ptag = _local_tag(parent)
        if ptag not in nodes:
            continue
        pfields = _node_field_map(ptag, nodes)
        for child in parent:
            ctag = _local_tag(child)
            if ctag not in nodes:
                continue
            explicit = child.get("containerField")
            cf = explicit or nodes[ctag]["containerField"]
            if not cf:
                continue
            anc = _type_ancestry(ctag, nodes, abstracts)
            field = pfields.get(cf)
            if field is not None and _field_accepts(field, anc):
                continue                                   # already correct
            label = child.get("DEF") or child.get("USE") or ""
            candidates = [n for n, f in pfields.items() if _field_accepts(f, anc)]
            if not candidates:
                unfixable.append({
                    "node": ctag, "parent": ptag, "ref": label,
                    "reason": f"{ptag} has no field that accepts a {ctag}; "
                              f"the node is in the wrong place, not just mis-labelled.",
                })
                continue
            chosen = _pick(candidates, child, pfields)
            child.set("containerField", chosen)
            changes.append({
                "node": ctag, "parent": ptag, "ref": label,
                "from": explicit, "to": chosen,
                "ambiguous": len(candidates) > 1,
                "alternatives": [c for c in candidates if c != chosen],
            })

    decl = '<?xml version="1.0" encoding="UTF-8"?>\n'
    fixed = decl + etree.tostring(root, pretty_print=True, encoding="unicode")
    return {"fixed": fixed, "changes": changes, "unfixable": unfixable}
