"""Loader for the X3D Ontology for Semantic Web (Turtle encoding).

Parses the bundled X3dOntology4.0.ttl into an rdflib Graph and provides
SPARQL query access. The ontology complements the X3DUOM: the X3DUOM
records each node's own metadata (fields, types, containerField), while
the ontology's property lattice (hasChild/hasParent with domains and
ranges) supports relationship queries such as "which node types may
parent a given node" that the X3DUOM index cannot answer directly.

Ontology answers are advisory; XSD and semantic validation remain the
ground truth for document validity.
"""

from pathlib import Path

import rdflib


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "validation" / "schemas"
ONTOLOGY_PATH = SCHEMAS_DIR / "X3dOntology4.0.ttl"

X3D_NS = "https://www.web3d.org/specifications/X3dOntology4.0#"

PREFIXES = f"""\
PREFIX x3d: <{X3D_NS}>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
"""


class X3DOntology:
    """Parsed representation of the X3D Ontology."""

    def __init__(self, path: Path = ONTOLOGY_PATH):
        self._graph = rdflib.Graph()
        self._graph.parse(str(path), format="turtle")
        self._ns = rdflib.Namespace(X3D_NS)

    @property
    def graph(self) -> rdflib.Graph:
        return self._graph

    def query(self, sparql: str) -> list[dict]:
        """Run a SPARQL SELECT/ASK query, prepending standard prefixes.

        Returns a list of {variable: value} dicts for SELECT, or a single
        {"ask": bool} dict for ASK.
        """
        result = self._graph.query(PREFIXES + sparql)
        if result.type == "ASK":
            return [{"ask": bool(result.askAnswer)}]
        rows = []
        for binding in result:
            row = {}
            for var in result.vars:
                value = binding[var]
                row[str(var)] = self._render(value)
            rows.append(row)
        return rows

    def node_parents(self, node_type: str) -> list[dict]:
        """Return node types whose fields may contain the given node type.

        Walks properties that are subproperties of x3d:hasChild whose
        rdfs:range subsumes the node type, reporting each property's
        rdfs:domain as a candidate parent.
        """
        sparql = """
SELECT DISTINCT ?parent ?field WHERE {
  ?field rdfs:subPropertyOf+ x3d:hasChild ;
         rdfs:range ?range ;
         rdfs:domain ?parent .
  x3d:%s rdfs:subClassOf* ?range .
}
ORDER BY ?parent
""" % node_type
        return self.query(sparql)

    def describe_term(self, term: str) -> dict:
        """Return labels, types, and super/sub relations for an ontology term."""
        uri = self._ns[term]
        g = self._graph
        if (uri, None, None) not in g:
            return {"error": f"Term not found in ontology: {term}"}

        def q(items):
            return sorted({self._render(x) for x in items})

        return {
            "term": term,
            "types": q(g.objects(uri, rdflib.RDF.type)),
            "labels": q(g.objects(uri, rdflib.RDFS.label)),
            "superClasses": q(g.objects(uri, rdflib.RDFS.subClassOf)),
            "subClasses": q(g.subjects(rdflib.RDFS.subClassOf, uri)),
            "superProperties": q(g.objects(uri, rdflib.RDFS.subPropertyOf)),
            "subProperties": q(g.subjects(rdflib.RDFS.subPropertyOf, uri)),
            "domains": q(g.objects(uri, rdflib.RDFS.domain)),
            "ranges": q(g.objects(uri, rdflib.RDFS.range)),
            "inverseOf": q(
                list(g.objects(uri, rdflib.OWL.inverseOf))
                + list(g.subjects(rdflib.OWL.inverseOf, uri))
            ),
        }

    def _render(self, value) -> str:
        """Render an rdflib term compactly (strip the x3d namespace)."""
        if isinstance(value, rdflib.URIRef):
            text = str(value)
            if text.startswith(X3D_NS):
                return text[len(X3D_NS):]
            return text
        if value is None:
            return ""
        return str(value)


# Module-level singleton
_instance = None


def get_ontology() -> X3DOntology:
    """Return the cached X3DOntology singleton."""
    global _instance
    if _instance is None:
        _instance = X3DOntology()
    return _instance
