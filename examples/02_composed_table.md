# Example 2: Multi-Object Scene with compose_scene

Building a complete scene with multiple objects, lighting, viewpoint, and background in one call.

## Chat

**User:** Create a scene with a wooden table, a red apple and a blue mug on top. Add a viewpoint and warm lighting.

**Model calls** `compose_scene`:
```json
{
  "objects": [
    {"shape": "box", "size": [2, 0.15, 1.5], "color": [0.55, 0.27, 0.07],
     "def_name": "TableTop"},
    {"shape": "cylinder", "size": [0.06, 1], "color": [0.45, 0.22, 0.05],
     "translation": [0.7, -0.57, 0.5], "def_name": "Leg1"},
    {"shape": "cylinder", "size": [0.06, 1], "color": [0.45, 0.22, 0.05],
     "translation": [-0.7, -0.57, 0.5], "def_name": "Leg2"},
    {"shape": "cylinder", "size": [0.06, 1], "color": [0.45, 0.22, 0.05],
     "translation": [0.7, -0.57, -0.5], "def_name": "Leg3"},
    {"shape": "cylinder", "size": [0.06, 1], "color": [0.45, 0.22, 0.05],
     "translation": [-0.7, -0.57, -0.5], "def_name": "Leg4"},
    {"shape": "sphere", "size": [0.25], "color": [0.85, 0.1, 0.1],
     "translation": [0.4, 0.35, 0.2], "def_name": "Apple"},
    {"shape": "cylinder", "size": [0.12, 0.35], "color": [0.15, 0.4, 0.85],
     "translation": [-0.35, 0.25, -0.1], "def_name": "Mug"}
  ],
  "viewpoint": {
    "position": [3, 2, 4],
    "orientation": [1, 0, 0, -0.35],
    "description": "Table overview"
  },
  "lights": [
    {"type": "directional", "direction": [-0.5, -0.8, -0.3],
     "color": [1, 0.95, 0.9], "intensity": 0.8}
  ],
  "background": {"skyColor": [0.9, 0.9, 0.95]}
}
```

**MCP response:** Complete X3D scene with Background, Viewpoint, DirectionalLight, and 7 Transform/Shape nodes -- all with DEF names, materials, and proper positioning.

**Model:** The scene has a brown table (flat box top + 4 cylinder legs), a red apple (sphere at table height), and a blue mug (cylinder). Warm directional light from upper-left, light gray sky background, camera angled down from front-right.

## What this demonstrates

- `compose_scene` assembles multiple objects with a single call
- Each object gets position (`translation`), material (`color`), and a `DEF` name
- Scene includes environment setup: viewpoint with orbit angle, directional light with color temperature, background sky
- All primitive types in one scene: Box, Cylinder, Sphere

## Scene file

[scenes/table_scene.x3d](scenes/table_scene.x3d)
