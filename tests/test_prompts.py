"""Tests for the MCP guided-workflow prompts.

Verifies registration and that each prompt body references the tool names
the LLM is meant to call. Adapted from server.py prompt registrations in
https://github.com/niknarra/x3d-mcp by Nikhil Narra and Nicholas Polys
(Virginia Tech / Web3D Consortium).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp.server.fastmcp import FastMCP

from tools.prompts import register


def _build_mcp():
    mcp = FastMCP("test")
    register(mcp)
    return mcp


def _prompt_body(mcp: FastMCP, name: str, **kwargs) -> str:
    prompt = mcp._prompt_manager._prompts[name]
    return prompt.fn(**kwargs)


def test_all_prompts_registered():
    mcp = _build_mcp()
    names = set(mcp._prompt_manager._prompts.keys())
    assert names == {"build_scene", "audit_scene", "animate_scene", "convert_to_x3dom"}


def test_build_scene_registered():
    mcp = _build_mcp()
    body = _prompt_body(mcp, "build_scene", description="a red sphere")
    assert "a red sphere" in body
    assert "validate_x3d" in body
    assert "x3dom_page" in body
    assert "create_scene" in body or "compose_scene" in body


def test_audit_scene_registered():
    mcp = _build_mcp()
    body = _prompt_body(mcp, "audit_scene")
    assert "validate_x3d" in body
    assert "validate_semantic" in body
    assert "describe_node" in body


def test_animate_scene_registered():
    mcp = _build_mcp()
    body = _prompt_body(mcp, "animate_scene", target_description="a spinning cube")
    assert "a spinning cube" in body
    assert "animate_x3d_node" in body
    assert "x3d_animation_info" in body
    assert "validate_x3d" in body


def test_convert_to_x3dom_registered():
    mcp = _build_mcp()
    body = _prompt_body(mcp, "convert_to_x3dom")
    assert "validate_x3d" in body
    assert "x3dom_page" in body
