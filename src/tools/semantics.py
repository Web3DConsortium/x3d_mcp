"""Semantic-web query tools backed by the X3D Ontology.

Exposes the bundled X3D Ontology (Turtle encoding) for SPARQL queries
and canned relationship lookups. These tools answer questions about the
X3D type system that the X3DUOM index cannot, such as the closed set of
node types whose fields may legally contain a given node.

Ontology answers are advisory: the ontology's property ranges are in
places broader than the XSD content models, so XSD validation (level 3)
and semantic checks (level 4) remain the ground truth for validity.
"""

import json

from mcp.server.fastmcp import FastMCP

from x3d_utils.ontology import get_ontology


def register(mcp: FastMCP):

    @mcp.tool()
    def query_ontology(sparql: str) -> str:
        """Run a SPARQL SELECT or ASK query against the X3D Ontology.

        Standard prefixes are pre-declared: x3d, owl, rdf, rdfs, dcterms.
        The x3d prefix is the X3D Ontology namespace; classes are node
        type names (x3d:Sphere) and the containment lattice uses
        x3d:hasChild / x3d:hasParent with per-field subproperties
        carrying rdfs:domain and rdfs:range.

        Args:
            sparql: The SPARQL query text (SELECT or ASK).
        """
        onto = get_ontology()
        try:
            rows = onto.query(sparql)
        except Exception as e:
            return json.dumps({"error": f"SPARQL error: {e}"})
        return json.dumps({"rows": rows, "count": len(rows)}, indent=2)

    @mcp.tool()
    def node_parents(node_type: str) -> str:
        """List node types whose fields may contain the given node type.

        Answers "which node types may legally parent this node" from the
        X3D Ontology's containment property lattice. Each result names
        the candidate parent class and the field property that admits the
        child. Results are advisory; validate composed scenes with
        validate_x3d for ground truth.

        Args:
            node_type: The X3D node type name (e.g. "Sphere", "Material").
        """
        onto = get_ontology()
        rows = onto.node_parents(node_type)
        if not rows:
            return json.dumps({
                "error": f"No parents found; is '{node_type}' an X3D node type?"
            })
        return json.dumps({"nodeType": node_type, "parents": rows}, indent=2)

    @mcp.tool()
    def describe_ontology_term(term: str) -> str:
        """Describe an X3D Ontology class or property.

        Returns labels, rdf types, super/sub classes and properties,
        domains, ranges, and inverse properties for the named term.

        Args:
            term: Ontology term name (e.g. "Sphere", "hasChild", "geometry").
        """
        onto = get_ontology()
        return json.dumps(onto.describe_term(term), indent=2)
