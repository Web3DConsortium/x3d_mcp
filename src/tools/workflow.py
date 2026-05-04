"""High-level X3D scene generation tools.

Provides workflow-oriented tools that generate complete X3D scenes
from high-level descriptions.
"""

import x3d.x3d as x3d_mod
from x3d.x3d import (
    X3D, Scene, head, meta,
    Shape, Appearance, Material,
    Box, Sphere, Cone, Cylinder,
    Transform, Viewpoint, DirectionalLight, PointLight, Background,
)
from mcp.server.fastmcp import FastMCP


GEOMETRY_MAP = {
    "box": Box,
    "sphere": Sphere,
    "cone": Cone,
    "cylinder": Cylinder,
}


def _serialize(model: X3D, encoding: str) -> str:
    if encoding == "json":
        return model.JSON()
    elif encoding == "vrml":
        return model.VRML()
    return model.XML()


def register(mcp: FastMCP):

    @mcp.tool()
    def create_scene(description: str, profile: str = "Interchange",
                     encoding: str = "xml") -> str:
        """Create an empty X3D scene with metadata.

        Args:
            description: A title/description for the scene.
            profile: X3D profile - "Core", "Interchange", "Interactive",
                    "Immersive", or "Full".
            encoding: Output encoding - "xml", "json", or "vrml".
        """
        model = X3D(
            profile=profile,
            version="4.1",
            head=head(children=[
                meta(name="title", content=description),
            ]),
            Scene=Scene(),
        )
        return _serialize(model, encoding)

    @mcp.tool()
    def create_geometry(shape: str, color: list[float] | None = None,
                        size: list[float] | None = None,
                        translation: list[float] | None = None,
                        rotation: list[float] | None = None,
                        transparency: float = 0.0,
                        encoding: str = "xml") -> str:
        """Create a single X3D geometry with material and optional transform.

        Args:
            shape: Geometry type - "box", "sphere", "cone", or "cylinder".
            color: RGB color as [r, g, b], each 0.0-1.0. Default white.
            size: Size parameters as a list. For box: [x,y,z]. For sphere: [radius].
                  For cone: [bottomRadius, height]. For cylinder: [radius, height].
            translation: Position as [x, y, z].
            rotation: Axis-angle rotation as [x, y, z, angle_radians].
            transparency: Material transparency, 0.0 (opaque) to 1.0 (invisible).
            encoding: Output encoding - "xml", "json", or "vrml".
        """
        shape_lower = shape.lower()
        if shape_lower not in GEOMETRY_MAP:
            return f"Unknown shape: {shape}. Use: {list(GEOMETRY_MAP.keys())}"

        geo_cls = GEOMETRY_MAP[shape_lower]
        geo_kwargs = {}
        if size:
            if shape_lower == "box" and len(size) >= 3:
                geo_kwargs["size"] = tuple(size[:3])
            elif shape_lower == "sphere" and len(size) >= 1:
                geo_kwargs["radius"] = size[0]
            elif shape_lower == "cone" and len(size) >= 2:
                geo_kwargs["bottomRadius"] = size[0]
                geo_kwargs["height"] = size[1]
            elif shape_lower == "cylinder" and len(size) >= 2:
                geo_kwargs["radius"] = size[0]
                geo_kwargs["height"] = size[1]

        mat_kwargs = {}
        if color and len(color) >= 3:
            mat_kwargs["diffuseColor"] = tuple(color[:3])
        if transparency > 0:
            mat_kwargs["transparency"] = transparency

        shape_node = Shape(
            appearance=Appearance(material=Material(**mat_kwargs)),
            geometry=geo_cls(**geo_kwargs),
        )

        if translation or rotation:
            xform_kwargs = {}
            if translation and len(translation) >= 3:
                xform_kwargs["translation"] = tuple(translation[:3])
            if rotation and len(rotation) >= 4:
                xform_kwargs["rotation"] = tuple(rotation[:4])
            scene_child = Transform(children=[shape_node], **xform_kwargs)
        else:
            scene_child = shape_node

        model = X3D(
            profile="Interchange",
            version="4.1",
            Scene=Scene(children=[scene_child]),
        )
        return _serialize(model, encoding)

    @mcp.tool()
    def compose_scene(objects: list[dict],
                      viewpoint: dict | None = None,
                      lights: list[dict] | None = None,
                      background: dict | None = None,
                      encoding: str = "xml") -> str:
        """Compose multiple objects into a complete X3D scene.

        Args:
            objects: List of object dicts, each with:
                - shape: "box", "sphere", "cone", or "cylinder"
                - color: [r, g, b] (optional)
                - size: size params list (optional)
                - translation: [x, y, z] (optional)
                - rotation: [x, y, z, angle] (optional)
                - def_name: DEF name (optional)
            viewpoint: Optional dict with "position" [x,y,z] and
                      "orientation" [x,y,z,angle].
            lights: Optional list of light dicts with "type" ("directional"
                   or "point"), "direction" or "location", "color", "intensity".
            background: Optional dict with "skyColor" [r,g,b].
            encoding: Output encoding - "xml", "json", or "vrml".
        """
        scene_children = []

        if background:
            bg_kwargs = {}
            if "skyColor" in background:
                bg_kwargs["skyColor"] = [tuple(background["skyColor"][:3])]
            scene_children.append(Background(**bg_kwargs))

        if viewpoint:
            vp_kwargs = {}
            if "position" in viewpoint:
                vp_kwargs["position"] = tuple(viewpoint["position"][:3])
            if "orientation" in viewpoint:
                vp_kwargs["orientation"] = tuple(viewpoint["orientation"][:4])
            if "description" in viewpoint:
                vp_kwargs["description"] = viewpoint["description"]
            scene_children.append(Viewpoint(**vp_kwargs))

        if lights:
            for light in lights:
                light_type = light.get("type", "directional")
                light_kwargs = {}
                if "color" in light:
                    light_kwargs["color"] = tuple(light["color"][:3])
                if "intensity" in light:
                    light_kwargs["intensity"] = light["intensity"]
                if light_type == "directional":
                    if "direction" in light:
                        light_kwargs["direction"] = tuple(light["direction"][:3])
                    scene_children.append(DirectionalLight(**light_kwargs))
                elif light_type == "point":
                    if "location" in light:
                        light_kwargs["location"] = tuple(light["location"][:3])
                    scene_children.append(PointLight(**light_kwargs))

        for obj in objects:
            shape_name = obj.get("shape", "box").lower()
            if shape_name not in GEOMETRY_MAP:
                continue
            geo_cls = GEOMETRY_MAP[shape_name]
            geo_kwargs = {}
            obj_size = obj.get("size")
            if obj_size:
                if shape_name == "box" and len(obj_size) >= 3:
                    geo_kwargs["size"] = tuple(obj_size[:3])
                elif shape_name == "sphere" and len(obj_size) >= 1:
                    geo_kwargs["radius"] = obj_size[0]
                elif shape_name == "cone" and len(obj_size) >= 2:
                    geo_kwargs["bottomRadius"] = obj_size[0]
                    geo_kwargs["height"] = obj_size[1]
                elif shape_name == "cylinder" and len(obj_size) >= 2:
                    geo_kwargs["radius"] = obj_size[0]
                    geo_kwargs["height"] = obj_size[1]

            mat_kwargs = {}
            if "color" in obj:
                mat_kwargs["diffuseColor"] = tuple(obj["color"][:3])

            shape_kwargs = {}
            if obj.get("def_name"):
                shape_kwargs["DEF"] = obj["def_name"]

            shape_node = Shape(
                appearance=Appearance(material=Material(**mat_kwargs)),
                geometry=geo_cls(**geo_kwargs),
                **shape_kwargs,
            )

            if obj.get("translation") or obj.get("rotation"):
                xform_kwargs = {}
                if obj.get("translation"):
                    xform_kwargs["translation"] = tuple(obj["translation"][:3])
                if obj.get("rotation"):
                    xform_kwargs["rotation"] = tuple(obj["rotation"][:4])
                if obj.get("def_name"):
                    xform_kwargs["DEF"] = obj["def_name"]
                    shape_node.DEF = None
                    shape_node.USE = ""
                scene_children.append(Transform(children=[shape_node], **xform_kwargs))
            else:
                scene_children.append(shape_node)

        model = X3D(
            profile="Interchange",
            version="4.1",
            Scene=Scene(children=scene_children),
        )
        return _serialize(model, encoding)
