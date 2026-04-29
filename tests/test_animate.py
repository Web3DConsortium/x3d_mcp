"""Tests for X3D animation tools.

Mirrors the 25-test inventory in
https://github.com/niknarra/x3d-mcp/blob/main/tests/test_animation.py
(Nikhil Narra, Nicholas Polys -- Virginia Tech / Web3D Consortium).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools.animate import _animate, _add_route, _animation_info


ANIM_SCENE = '''<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Immersive" version="4.1">
  <Scene>
    <Viewpoint DEF="MainView" description="Default View" position="0 0 10"/>
    <DirectionalLight direction="0 -1 -1" intensity="0.8"/>
    <Transform DEF="Spinner" translation="0 0 0">
      <Shape>
        <Appearance>
          <Material DEF="ColorMat" diffuseColor="1 0 0"/>
        </Appearance>
        <Box size="2 2 2"/>
      </Shape>
    </Transform>
  </Scene>
</X3D>'''

ROUTE_SCENE = '''<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Immersive" version="4.1">
  <Scene>
    <Viewpoint position="0 0 10"/>
    <TimeSensor DEF="Clock" cycleInterval="3" loop="true"/>
    <PositionInterpolator DEF="Mover" key="0 1" keyValue="0 0 0, 5 0 0"/>
    <Transform DEF="Target" translation="0 0 0">
      <Shape><Appearance><Material/></Appearance><Box/></Shape>
    </Transform>
  </Scene>
</X3D>'''


# ---- animate ----

def test_rotation_animation():
    result = _animate(
        ANIM_SCENE, "Spinner", "rotation",
        "0 1 0 0", "0 1 0 6.28318", duration=4.0,
    )
    assert "OrientationInterpolator" in result
    assert "TimeSensor" in result
    assert "ROUTE" in result


def test_translation_animation():
    result = _animate(
        ANIM_SCENE, "Spinner", "translation",
        "0 0 0", "5 0 0", duration=3.0,
    )
    assert "PositionInterpolator" in result
    assert "TimeSensor" in result


def test_color_animation():
    result = _animate(
        ANIM_SCENE, "ColorMat", "diffuseColor",
        "1 0 0", "0 0 1", duration=2.0,
    )
    assert "ColorInterpolator" in result


def test_scalar_animation():
    result = _animate(
        ANIM_SCENE, "ColorMat", "transparency",
        "0", "1", duration=3.0,
    )
    assert "ScalarInterpolator" in result


def test_animation_creates_timer_and_routes():
    result = _animate(
        ANIM_SCENE, "Spinner", "rotation",
        "0 1 0 0", "0 1 0 6.28318",
    )
    assert result.count("ROUTE") >= 2
    assert "TimeSensor" in result
    assert "fraction_changed" in result
    assert "value_changed" in result


def test_animation_loop_true():
    result = _animate(
        ANIM_SCENE, "Spinner", "rotation",
        "0 1 0 0", "0 1 0 6.28318", loop=True,
    )
    assert 'loop="true"' in result


def test_animation_loop_false():
    result = _animate(
        ANIM_SCENE, "Spinner", "rotation",
        "0 1 0 0", "0 1 0 6.28318", loop=False,
    )
    assert 'loop="false"' in result


def test_animation_custom_duration():
    result = _animate(
        ANIM_SCENE, "Spinner", "rotation",
        "0 1 0 0", "0 1 0 6.28318", duration=10.0,
    )
    assert 'cycleInterval="10.0"' in result


def test_animate_nonexistent_def():
    result = _animate(
        ANIM_SCENE, "FakeNode", "rotation",
        "0 1 0 0", "0 1 0 6.28318",
    )
    assert "FakeNode" in result
    assert "Available DEF names" in result or "not found" in result.lower()


def test_animate_invalid_field():
    result = _animate(
        ANIM_SCENE, "Spinner", "nonexistent_field",
        "0", "1",
    )
    assert "not found" in result.lower() or "nonexistent_field" in result


def test_animate_no_target_def():
    result = _animate(ANIM_SCENE, "", "rotation", "0 0 0 0", "0 1 0 3.14")
    assert "target_def is required" in result


def test_animate_no_field():
    result = _animate(ANIM_SCENE, "Spinner", "", "0", "1")
    assert "field_name is required" in result


def test_animate_no_values():
    result = _animate(ANIM_SCENE, "Spinner", "rotation", "", "0 1 0 3.14")
    assert "from_value" in result.lower() or "required" in result.lower()


# ---- add_route ----

def test_valid_route_inserted():
    result = _add_route(
        ROUTE_SCENE, "Clock", "fraction_changed", "Mover", "set_fraction",
    )
    assert "<ROUTE" in result
    assert 'fromNode="Clock"' in result
    assert 'toNode="Mover"' in result


def test_route_nonexistent_from_def():
    result = _add_route(
        ROUTE_SCENE, "Ghost", "fraction_changed", "Mover", "set_fraction",
    )
    assert "Ghost" in result
    assert "not found" in result.lower()


def test_route_nonexistent_to_def():
    result = _add_route(
        ROUTE_SCENE, "Clock", "fraction_changed", "Ghost", "set_fraction",
    )
    assert "Ghost" in result


def test_route_invalid_from_field():
    result = _add_route(
        ROUTE_SCENE, "Clock", "fake_field", "Mover", "set_fraction",
    )
    assert "fake_field" in result


def test_route_invalid_to_field():
    result = _add_route(
        ROUTE_SCENE, "Clock", "fraction_changed", "Mover", "fake_field",
    )
    assert "fake_field" in result


def test_route_missing_params():
    result = _add_route(ROUTE_SCENE, "", "fraction_changed", "Mover", "set_fraction")
    assert "required" in result.lower()


# ---- animation_info ----

def test_general_overview():
    result = _animation_info()
    assert "TimeSensor" in result
    assert "Interpolator" in result
    assert "ROUTE" in result


def test_interpolators_topic():
    result = _animation_info("interpolators")
    assert "OrientationInterpolator" in result
    assert "PositionInterpolator" in result
    assert "ColorInterpolator" in result
    assert "ScalarInterpolator" in result


def test_timesensor_topic():
    result = _animation_info("timesensor")
    assert "cycleInterval" in result
    assert "fraction_changed" in result


def test_routes_topic():
    result = _animation_info("routes")
    assert "fromNode" in result
    assert "outputOnly" in result
    assert "inputOnly" in result


def test_examples_topic():
    result = _animation_info("examples")
    assert "Continuous Rotation" in result
    assert "Color Pulse" in result


def test_unknown_topic_returns_overview():
    result = _animation_info("some_unknown_thing")
    assert "Animation System Overview" in result
