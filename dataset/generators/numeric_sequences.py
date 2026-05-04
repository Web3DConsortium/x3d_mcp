"""Generate X3D training examples with long numeric sequences.

Targets: IndexedFaceSet, Extrusion, Interpolators -- the node types
where fine-tuned models struggle with long number arrays.
"""

import math
import random
from typing import Optional

from dataset.schema import TrainingExample


def _fmt(v: float) -> str:
    """Format float, strip trailing zeros."""
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s


def _grid_mesh(rows: int, cols: int, rng: random.Random) -> dict:
    """Generate a grid mesh with coordinates and indices."""
    coords = []
    for r in range(rows):
        for c in range(cols):
            x = c / max(cols - 1, 1) * 2.0 - 1.0
            z = r / max(rows - 1, 1) * 2.0 - 1.0
            y = rng.uniform(-0.3, 0.3)
            coords.append((x, y, z))

    indices = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            tl = r * cols + c
            tr = tl + 1
            bl = (r + 1) * cols + c
            br = bl + 1
            indices.extend([tl, tr, br, -1])
            indices.extend([tl, br, bl, -1])

    tex_coords = []
    for r in range(rows):
        for c in range(cols):
            u = c / max(cols - 1, 1)
            v = r / max(rows - 1, 1)
            tex_coords.append((u, v))

    return {"coords": coords, "indices": indices, "tex_coords": tex_coords}


def _sphere_mesh(slices: int, stacks: int, radius: float = 1.0) -> dict:
    """Generate a UV sphere mesh."""
    coords = []
    coords.append((0.0, radius, 0.0))
    for i in range(1, stacks):
        phi = math.pi * i / stacks
        for j in range(slices):
            theta = 2.0 * math.pi * j / slices
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            coords.append((x, y, z))
    coords.append((0.0, -radius, 0.0))

    indices = []
    for j in range(slices):
        next_j = (j + 1) % slices
        indices.extend([0, 1 + j, 1 + next_j, -1])

    for i in range(stacks - 2):
        row_start = 1 + i * slices
        next_row = 1 + (i + 1) * slices
        for j in range(slices):
            next_j = (j + 1) % slices
            a = row_start + j
            b = row_start + next_j
            c = next_row + next_j
            d = next_row + j
            indices.extend([a, b, c, -1])
            indices.extend([a, c, d, -1])

    bottom = len(coords) - 1
    last_row = 1 + (stacks - 2) * slices
    for j in range(slices):
        next_j = (j + 1) % slices
        indices.extend([bottom, last_row + next_j, last_row + j, -1])

    return {"coords": coords, "indices": indices}


def _torus_mesh(major_r: float, minor_r: float,
                major_seg: int, minor_seg: int) -> dict:
    """Generate a torus mesh."""
    coords = []
    for i in range(major_seg):
        theta = 2.0 * math.pi * i / major_seg
        for j in range(minor_seg):
            phi = 2.0 * math.pi * j / minor_seg
            x = (major_r + minor_r * math.cos(phi)) * math.cos(theta)
            y = minor_r * math.sin(phi)
            z = (major_r + minor_r * math.cos(phi)) * math.sin(theta)
            coords.append((x, y, z))

    indices = []
    for i in range(major_seg):
        next_i = (i + 1) % major_seg
        for j in range(minor_seg):
            next_j = (j + 1) % minor_seg
            a = i * minor_seg + j
            b = i * minor_seg + next_j
            c = next_i * minor_seg + next_j
            d = next_i * minor_seg + j
            indices.extend([a, b, c, -1])
            indices.extend([a, c, d, -1])

    return {"coords": coords, "indices": indices}


def generate_indexed_face_set(
    complexity: str = "medium",
    rng: Optional[random.Random] = None,
) -> TrainingExample:
    """Generate an IndexedFaceSet training example."""
    if rng is None:
        rng = random.Random()

    sizes = {"short": (4, 4), "medium": (8, 8), "long": (16, 16)}
    mesh_type = rng.choice(["grid", "sphere", "torus"])

    if mesh_type == "grid":
        rows, cols = sizes.get(complexity, (8, 8))
        mesh = _grid_mesh(rows, cols, rng)
        desc = f"a {rows}x{cols} terrain grid"
    elif mesh_type == "sphere":
        slices_map = {"short": 8, "medium": 16, "long": 32}
        n = slices_map.get(complexity, 16)
        mesh = _sphere_mesh(n, n, radius=rng.uniform(0.5, 2.0))
        desc = f"a sphere with {n} slices and stacks"
    else:
        seg_map = {"short": 8, "medium": 16, "long": 24}
        n = seg_map.get(complexity, 16)
        mesh = _torus_mesh(
            major_r=rng.uniform(1.0, 3.0),
            minor_r=rng.uniform(0.2, 0.8),
            major_seg=n, minor_seg=n,
        )
        desc = f"a torus with {n} segments"

    coord_str = ", ".join(f"{_fmt(c[0])} {_fmt(c[1])} {_fmt(c[2])}" for c in mesh["coords"])
    index_str = " ".join(str(i) for i in mesh["indices"])

    color = (rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0))
    color_str = f"{_fmt(color[0])} {_fmt(color[1])} {_fmt(color[2])}"

    has_tex = "tex_coords" in mesh
    tex_coord_block = ""
    tex_index_attr = ""
    if has_tex:
        tex_str = ", ".join(f"{_fmt(t[0])} {_fmt(t[1])}" for t in mesh["tex_coords"])
        tex_coord_block = f"""
            <TextureCoordinate point='{tex_str}'/>"""
        tex_index_attr = f' texCoordIndex="{index_str}"'

    x3d_output = f"""<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <head>
    <meta name="title" content="IndexedFaceSet {mesh_type}"/>
  </head>
  <Scene>
    <Shape>
      <Appearance>
        <Material diffuseColor='{color_str}'/>
      </Appearance>
      <IndexedFaceSet coordIndex='{index_str}'{tex_index_attr} solid='false'>
        <Coordinate point='{coord_str}'/>{tex_coord_block}
      </IndexedFaceSet>
    </Shape>
  </Scene>
</X3D>"""

    instruction = f"Create an X3D scene containing {desc} using IndexedFaceSet"

    return TrainingExample(
        instruction=instruction,
        output=x3d_output.strip(),
        metadata={
            "complexity": complexity,
            "viewpoints": [],
            "node_types": ["IndexedFaceSet", "Coordinate", "Shape", "Material"],
            "components": ["Geometry3D", "Shape", "Rendering"],
            "source": "generated",
            "augmentation_params": {},
            "numeric_complexity": complexity,
            "sequence_lengths": {
                "coord_count": len(mesh["coords"]),
                "index_count": len(mesh["indices"]),
            },
            "raw": "",
        },
    )


def _circle_cross_section(n: int) -> list[tuple[float, float]]:
    """Generate a circle cross-section with n points (closed)."""
    points = []
    for i in range(n + 1):
        angle = 2.0 * math.pi * i / n
        points.append((math.cos(angle), math.sin(angle)))
    return points


def _star_cross_section(points_count: int, outer_r: float = 1.0,
                        inner_r: float = 0.4) -> list[tuple[float, float]]:
    """Generate a star cross-section."""
    points = []
    for i in range(points_count * 2 + 1):
        angle = math.pi * i / points_count
        r = outer_r if i % 2 == 0 else inner_r
        points.append((r * math.cos(angle), r * math.sin(angle)))
    return points


def _polygon_cross_section(sides: int, radius: float = 1.0) -> list[tuple[float, float]]:
    """Generate a regular polygon cross-section."""
    points = []
    for i in range(sides + 1):
        angle = 2.0 * math.pi * i / sides
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return points


def generate_extrusion(
    complexity: str = "medium",
    rng: Optional[random.Random] = None,
) -> TrainingExample:
    """Generate an Extrusion training example."""
    if rng is None:
        rng = random.Random()

    cross_type = rng.choice(["circle", "star", "polygon"])
    seg_map = {"short": 6, "medium": 12, "long": 24}
    n = seg_map.get(complexity, 12)

    if cross_type == "circle":
        cross = _circle_cross_section(n)
        desc = f"a circular cross-section with {n} segments"
    elif cross_type == "star":
        star_points = max(4, n // 2)
        cross = _star_cross_section(star_points, rng.uniform(0.8, 1.5), rng.uniform(0.2, 0.6))
        desc = f"a {star_points}-pointed star cross-section"
    else:
        sides = max(3, n // 2)
        cross = _polygon_cross_section(sides, rng.uniform(0.5, 1.5))
        desc = f"a {sides}-sided polygon cross-section"

    spine_len_map = {"short": 4, "medium": 8, "long": 16}
    spine_len = spine_len_map.get(complexity, 8)

    spine_type = rng.choice(["straight", "curved", "helix"])
    spine = []
    if spine_type == "straight":
        for i in range(spine_len):
            y = i / max(spine_len - 1, 1) * 4.0
            spine.append((0.0, y, 0.0))
    elif spine_type == "curved":
        for i in range(spine_len):
            t = i / max(spine_len - 1, 1)
            x = math.sin(t * math.pi) * 2.0
            y = t * 4.0
            z = math.cos(t * math.pi * 0.5) * rng.uniform(0.0, 1.0)
            spine.append((x, y, z))
    else:
        for i in range(spine_len):
            t = i / max(spine_len - 1, 1)
            angle = t * math.pi * 2.0
            x = math.cos(angle) * 1.5
            y = t * 4.0
            z = math.sin(angle) * 1.5
            spine.append((x, y, z))

    scale = []
    for i in range(spine_len):
        t = i / max(spine_len - 1, 1)
        s = 1.0 - t * rng.uniform(0.0, 0.8)
        scale.append((s, s))

    cross_str = ", ".join(f"{_fmt(p[0])} {_fmt(p[1])}" for p in cross)
    spine_str = ", ".join(f"{_fmt(p[0])} {_fmt(p[1])} {_fmt(p[2])}" for p in spine)
    scale_str = ", ".join(f"{_fmt(s[0])} {_fmt(s[1])}" for s in scale)

    color = (rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0))
    color_str = f"{_fmt(color[0])} {_fmt(color[1])} {_fmt(color[2])}"

    x3d_output = f"""<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <head>
    <meta name="title" content="Extrusion {spine_type} {cross_type}"/>
  </head>
  <Scene>
    <Shape>
      <Appearance>
        <Material diffuseColor='{color_str}'/>
      </Appearance>
      <Extrusion crossSection='{cross_str}' spine='{spine_str}' scale='{scale_str}' solid='false' creaseAngle='1.57'/>
    </Shape>
  </Scene>
</X3D>"""

    instruction = f"Create an X3D extrusion with {desc} along a {spine_type} spine path"

    return TrainingExample(
        instruction=instruction,
        output=x3d_output.strip(),
        metadata={
            "complexity": complexity,
            "viewpoints": [],
            "node_types": ["Extrusion", "Shape", "Material"],
            "components": ["Geometry3D", "Shape", "Rendering"],
            "source": "generated",
            "augmentation_params": {},
            "numeric_complexity": complexity,
            "sequence_lengths": {
                "cross_section_points": len(cross),
                "spine_points": len(spine),
                "scale_points": len(scale),
            },
            "raw": "",
        },
    )


def generate_interpolator(
    complexity: str = "medium",
    rng: Optional[random.Random] = None,
) -> TrainingExample:
    """Generate an Interpolator training example with animation."""
    if rng is None:
        rng = random.Random()

    interp_type = rng.choice(["color", "coordinate", "orientation", "position", "scalar"])
    key_count_map = {"short": 4, "medium": 8, "long": 20}
    key_count = key_count_map.get(complexity, 8)

    keys = [i / (key_count - 1) for i in range(key_count)]
    key_str = " ".join(_fmt(k) for k in keys)

    if interp_type == "color":
        node_name = "ColorInterpolator"
        values = []
        for _ in range(key_count):
            values.extend([rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 1)])
        value_str = " ".join(_fmt(v) for v in values)
        desc = f"a color animation with {key_count} keyframes"
        target_field = "diffuseColor"
        target_node = "Material"

    elif interp_type == "coordinate":
        node_name = "CoordinateInterpolator"
        points_per_key = rng.choice([3, 4, 6])
        values = []
        for k in range(key_count):
            t = k / max(key_count - 1, 1)
            for p in range(points_per_key):
                angle = 2.0 * math.pi * p / points_per_key
                r = 1.0 + 0.5 * math.sin(t * math.pi * 2)
                values.extend([r * math.cos(angle), math.sin(t * math.pi), r * math.sin(angle)])
        value_str = " ".join(_fmt(v) for v in values)
        desc = f"a coordinate animation with {key_count} keyframes and {points_per_key} points each"
        target_field = "point"
        target_node = "Coordinate"

    elif interp_type == "orientation":
        node_name = "OrientationInterpolator"
        values = []
        axis = [rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)]
        mag = math.sqrt(sum(a * a for a in axis))
        axis = [a / mag for a in axis]
        for k in range(key_count):
            angle = 2.0 * math.pi * k / max(key_count - 1, 1)
            values.extend(axis + [angle])
        value_str = " ".join(_fmt(v) for v in values)
        desc = f"an orientation animation with {key_count} keyframes"
        target_field = "rotation"
        target_node = "Transform"

    elif interp_type == "position":
        node_name = "PositionInterpolator"
        values = []
        for k in range(key_count):
            t = k / max(key_count - 1, 1)
            x = math.sin(t * math.pi * 2) * rng.uniform(1, 5)
            y = math.cos(t * math.pi) * rng.uniform(0.5, 3)
            z = rng.uniform(-2, 2)
            values.extend([x, y, z])
        value_str = " ".join(_fmt(v) for v in values)
        desc = f"a position animation with {key_count} keyframes"
        target_field = "translation"
        target_node = "Transform"

    else:
        node_name = "ScalarInterpolator"
        values = []
        for k in range(key_count):
            t = k / max(key_count - 1, 1)
            values.append(abs(math.sin(t * math.pi * 2)))
        value_str = " ".join(_fmt(v) for v in values)
        desc = f"a scalar animation with {key_count} keyframes"
        target_field = "transparency"
        target_node = "Material"

    color = (rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0))
    color_str = f"{_fmt(color[0])} {_fmt(color[1])} {_fmt(color[2])}"
    cycle = _fmt(rng.uniform(2.0, 10.0))

    x3d_output = f"""<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Immersive" version="4.1">
  <head>
    <meta name="title" content="{node_name} animation"/>
  </head>
  <Scene>
    <TimeSensor DEF='Clock' cycleInterval='{cycle}' loop='true'/>
    <{node_name} DEF='Interp' key='{key_str}' keyValue='{value_str}'/>
    <Transform DEF='AnimatedTransform'>
      <Shape>
        <Appearance>
          <Material DEF='AnimatedMaterial' diffuseColor='{color_str}'/>
        </Appearance>
        <Sphere radius='1.0'/>
      </Shape>
    </Transform>
    <ROUTE fromNode='Clock' fromField='fraction_changed' toNode='Interp' toField='set_fraction'/>
    <ROUTE fromNode='Interp' fromField='value_changed' toNode='{("Animated" + target_node)}' toField='{target_field}'/>
  </Scene>
</X3D>"""

    instruction = f"Create an X3D scene with {desc} applied to a sphere"

    return TrainingExample(
        instruction=instruction,
        output=x3d_output.strip(),
        metadata={
            "complexity": complexity,
            "viewpoints": [],
            "node_types": [node_name, "TimeSensor", "Shape", "Material", "Transform", "Sphere"],
            "components": ["Interpolation", "Time", "Shape", "Geometry3D"],
            "source": "generated",
            "augmentation_params": {},
            "numeric_complexity": complexity,
            "sequence_lengths": {
                "key_count": key_count,
                "value_count": len(values),
            },
            "raw": "",
        },
    )
