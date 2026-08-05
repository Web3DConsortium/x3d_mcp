"""Scene-graph SPARQL tests over Example Archives Turtle fixtures.

The Web3D Consortium publishes every Example Archives scene in triple
form (converted via X3dToTurtle.xslt); the X3D Semantics page documents
canonical queries against them. These tests reproduce that query surface
locally: each fixture is loaded together with the bundled ontology into
one graph, which is the pattern a future query_scene_semantics tool will
productize (issue #20).

Triple-form conventions exercised here, per the Semantics page: DEF names
become colon-prefixed subjects, USE occurrences append -USE-n, unnamed
nodes get positional names like :Shape_2_2_1_1, and every instance is
typed `a x3do:<NodeType>`.
"""

import sys
from pathlib import Path

import pytest
import rdflib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from x3d_utils.ontology import PREFIXES, get_ontology

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "semantics"


def _scene_graph(fixture: str) -> tuple[rdflib.Graph, str]:
    """Ontology + scene triples in one graph, plus the scene's base prefix."""
    g = rdflib.Graph()
    g += get_ontology().graph
    g.parse(FIXTURES / fixture, format="turtle")
    # The scene's own prefix (":") is its catalog URL + "#"
    scene_ns = dict(g.namespaces())[""]
    return g, f"PREFIX scene: <{scene_ns}>\n" + PREFIXES.replace(
        "PREFIX x3d:", "PREFIX x3do:"
    )


@pytest.fixture(scope="module")
def helloworld():
    return _scene_graph("HelloWorld.ttl")


@pytest.fixture(scope="module")
def colorinterp():
    return _scene_graph("ColorInterpolatorExample.ttl")


@pytest.fixture(scope="module")
def joekick():
    return _scene_graph("JoeKick.ttl")


# ---- HelloWorld: the Semantics page's introductory query family ----

def test_helloworld_shape_count(helloworld):
    g, prefixes = helloworld
    rows = list(g.query(prefixes + """
        SELECT ?s WHERE { ?s a x3do:Shape }
    """))
    assert len(rows) == 2


def test_helloworld_texture_urls(helloworld):
    g, prefixes = helloworld
    rows = list(g.query(prefixes + """
        SELECT ?url WHERE { ?tex a x3do:ImageTexture ; x3do:url ?url }
    """))
    assert len(rows) == 1
    assert "earth-topo.png" in str(rows[0].url)


def test_helloworld_material_reuse_via_use(helloworld):
    g, prefixes = helloworld
    # DEF'd material plus its -USE-1 occurrence, both typed Material
    rows = list(g.query(prefixes + """
        SELECT ?m WHERE { ?m a x3do:Material }
    """))
    names = sorted(str(r.m).rsplit("#", 1)[-1] for r in rows)
    assert names == ["MaterialOffWhite", "MaterialOffWhite-USE-1"]


def test_helloworld_def_joins_ontology_inheritance(helloworld):
    g, prefixes = helloworld
    # Scene triples join ontology triples: the DEF'd Text node is an
    # X3DGeometryNode by the ontology's subclass axioms.
    rows = list(g.query(prefixes + """
        SELECT ?n WHERE {
          ?n x3do:DEF 'TextMessage' ; a ?type .
          ?type rdfs:subClassOf* x3do:X3DGeometryNode .
        }
    """))
    assert len(rows) >= 1


# ---- ColorInterpolatorExample: animation-chain traversal ----

def test_animation_chain_route_traversal(colorinterp):
    g, prefixes = colorinterp
    # Follow the event chain through ROUTE individuals by joining the
    # fromNode/toNode literals against DEF names:
    # TimeSensor --fraction_changed/set_fraction--> ColorInterpolator
    rows = list(g.query(prefixes + """
        SELECT ?clock ?interp WHERE {
          ?r a x3do:ROUTE ;
             x3do:fromNode ?clockDef ; x3do:fromField 'fraction_changed' ;
             x3do:toNode ?interpDef ; x3do:toField 'set_fraction' .
          ?clock a x3do:TimeSensor ; x3do:DEF ?clockDef .
          ?interp a x3do:ColorInterpolator ; x3do:DEF ?interpDef .
        }
    """))
    assert len(rows) == 1


def test_animation_chain_reaches_a_material(colorinterp):
    g, prefixes = colorinterp
    # Second hop: interpolator value_changed drives some node's field.
    rows = list(g.query(prefixes + """
        SELECT ?target ?field WHERE {
          ?interp a x3do:ColorInterpolator ; x3do:DEF ?interpDef .
          ?r a x3do:ROUTE ;
             x3do:fromNode ?interpDef ; x3do:fromField 'value_changed' ;
             x3do:toNode ?targetDef ; x3do:toField ?field .
          ?target x3do:DEF ?targetDef .
        }
    """))
    assert len(rows) >= 1


def test_routes_are_scoped_under_parents(colorinterp):
    g, prefixes = colorinterp
    rows = list(g.query(prefixes + """
        SELECT ?r WHERE { ?r a x3do:ROUTE ; x3do:hasParent ?p }
    """))
    assert len(rows) >= 3


# ---- JoeKick: "which scenes exercise HAnim" ----

def test_hanim_scene_detected_by_ask(joekick):
    g, prefixes = joekick
    assert bool(g.query(prefixes + """
        ASK { ?h a x3do:HAnimHumanoid }
    """).askAnswer)


def test_hanim_joint_skeleton_size(joekick):
    g, prefixes = joekick
    rows = list(g.query(prefixes + """
        SELECT (COUNT(DISTINCT ?j) AS ?n) WHERE { ?j a x3do:HAnimJoint }
    """))
    # LOA skeleton: dozens of joints, far beyond a trivial fixture
    assert int(rows[0].n) > 40


def test_non_hanim_scene_ask_is_false(helloworld):
    g, prefixes = helloworld
    assert not bool(g.query(prefixes + """
        ASK { ?h a x3do:HAnimHumanoid }
    """).askAnswer)
