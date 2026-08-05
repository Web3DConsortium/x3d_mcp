"""Tests for the X3D Ontology loader and semantics tools."""

import json

import pytest

from x3d_utils.ontology import get_ontology


@pytest.fixture(scope="module")
def onto():
    return get_ontology()


def test_ontology_loads(onto):
    assert len(onto.graph) > 15000


def test_singleton():
    assert get_ontology() is get_ontology()


def test_sphere_is_geometry_node(onto):
    rows = onto.query("""
ASK { x3d:Sphere rdfs:subClassOf x3d:X3DGeometryNode }
""")
    assert rows == [{"ask": True}]


def test_select_returns_rows(onto):
    rows = onto.query("""
SELECT ?cls WHERE { ?cls rdfs:subClassOf x3d:X3DGeometryNode } LIMIT 5
""")
    assert len(rows) == 5
    assert all("cls" in r for r in rows)


def test_node_parents_sphere(onto):
    rows = onto.node_parents("Sphere")
    parents = {r["parent"] for r in rows}
    # Canonical geometry parents from the specification
    assert "Shape" in parents
    assert "ParticleSystem" in parents
    assert "RigidBody" in parents
    # The admitting field is reported alongside each parent
    shape_fields = {r["field"] for r in rows if r["parent"] == "Shape"}
    assert "geometry" in shape_fields


def test_node_parents_material(onto):
    rows = onto.node_parents("Material")
    parents = {r["parent"] for r in rows}
    assert "Appearance" in parents


def test_describe_term_class(onto):
    info = onto.describe_term("Sphere")
    assert info["term"] == "Sphere"
    assert "X3DGeometryNode" in info["superClasses"]


def test_describe_term_property(onto):
    info = onto.describe_term("geometry")
    assert "hasChild" in info["superProperties"]
    assert "X3DGeometryNode" in info["ranges"]
    assert "Shape" in info["domains"]


def test_describe_term_unknown(onto):
    info = onto.describe_term("NotARealTerm")
    assert "error" in info


def test_mcp_tools_registered():
    from mcp.server.fastmcp import FastMCP
    from tools import semantics

    mcp = FastMCP("test")
    semantics.register(mcp)
    import asyncio
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert {"query_ontology", "node_parents", "describe_ontology_term"} <= names


def test_query_ontology_tool_output():
    from mcp.server.fastmcp import FastMCP
    from tools import semantics

    mcp = FastMCP("test")
    semantics.register(mcp)
    # Invoke the underlying function through the tool manager
    import asyncio
    result = asyncio.run(
        mcp.call_tool("node_parents", {"node_type": "Sphere"})
    )
    content = result[0] if not isinstance(result, tuple) else result[0]
    if isinstance(content, list):
        content = content[0]
    payload = json.loads(content.text)
    assert payload["nodeType"] == "Sphere"
    assert any(p["parent"] == "Shape" for p in payload["parents"])


def test_query_ontology_bad_sparql():
    from mcp.server.fastmcp import FastMCP
    from tools import semantics

    mcp = FastMCP("test")
    semantics.register(mcp)
    import asyncio
    result = asyncio.run(
        mcp.call_tool("query_ontology", {"sparql": "SELECT WHERE nonsense"})
    )
    content = result[0] if not isinstance(result, tuple) else result[0]
    if isinstance(content, list):
        content = content[0]
    payload = json.loads(content.text)
    assert "error" in payload
