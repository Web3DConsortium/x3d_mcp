"""Scene state manager for granular X3D scene construction.

Wraps x3d.py objects to provide node-by-node scene building with
UUID-based node tracking, DEF/USE management, and ROUTE support.
"""

import uuid
import x3d.x3d as x3d_mod
from x3d.x3d import X3D, Scene, head, meta, ROUTE

from .x3duom import get_x3duom


class SceneError(Exception):
    """Raised for invalid scene operations."""


class SceneManager:
    """Manages in-memory X3D scene state for granular tool operations."""

    def __init__(self):
        self._nodes: dict[str, object] = {}
        self._def_to_id: dict[str, str] = {}
        self._id_to_def: dict[str, str] = {}
        self._children: dict[str, list[str]] = {}
        self._parent: dict[str, str] = {}
        self._routes: list[dict] = []
        self._metas: list[dict] = []
        self._profile = "Interchange"
        self._uom = get_x3duom()

    def create_node(self, node_type: str, **fields) -> str:
        """Create an X3D node and return its tracking ID."""
        concrete = self._uom.get_concrete_nodes()
        if node_type not in concrete:
            raise SceneError(f"Unknown node type: {node_type}")

        cls = getattr(x3d_mod, node_type, None)
        if cls is None:
            raise SceneError(f"x3d.py has no class for: {node_type}")

        node = cls(**fields)
        node_id = str(uuid.uuid4())
        self._nodes[node_id] = node
        self._children[node_id] = []
        return node_id

    def set_field(self, node_id: str, field_name: str, value) -> None:
        """Set a field value on an existing node."""
        node = self._get_node(node_id)
        node_type = type(node).__name__
        node_fields = self._uom.get_node_fields(node_type)
        field_names = {f["name"] for f in node_fields}

        if field_name not in field_names:
            raise SceneError(f"{node_type} has no field '{field_name}'")

        setattr(node, field_name, value)

    def add_child(self, parent_id: str, child_id: str) -> None:
        """Add a child node to a parent node."""
        parent = self._get_node(parent_id)
        child = self._get_node(child_id)

        if child_id in self._parent:
            old_parent = self._parent[child_id]
            self._children[old_parent].remove(child_id)

        self._children[parent_id].append(child_id)
        self._parent[child_id] = parent_id

        child_type = type(child).__name__
        container_field = self._uom.get_container_field(child_type)

        if container_field and container_field == "children":
            if hasattr(parent, "children"):
                parent.children = [
                    self._nodes[cid] for cid in self._children[parent_id]
                    if self._uom.get_container_field(type(self._nodes[cid]).__name__) == "children"
                ]
        elif container_field:
            setattr(parent, container_field, child)

    def def_node(self, node_id: str, def_name: str) -> None:
        """Assign a DEF name to a node."""
        node = self._get_node(node_id)

        if def_name in self._def_to_id:
            raise SceneError(f"DEF name already in use: {def_name}")

        if node_id in self._id_to_def:
            old_def = self._id_to_def[node_id]
            del self._def_to_id[old_def]

        node.DEF = def_name
        # Workaround: x3d.py DEF setter sets USE=None, but XML() checks
        # USE=="" to decide whether to output attributes. Reset to "".
        node.USE = ""
        self._def_to_id[def_name] = node_id
        self._id_to_def[node_id] = def_name

    def use_node(self, def_name: str) -> str:
        """Create a USE reference to a DEF'd node. Returns new node ID."""
        if def_name not in self._def_to_id:
            raise SceneError(f"No node with DEF name: {def_name}")

        original_id = self._def_to_id[def_name]
        original = self._nodes[original_id]
        node_type = type(original).__name__

        cls = getattr(x3d_mod, node_type)
        use_node = cls(USE=def_name)

        node_id = str(uuid.uuid4())
        self._nodes[node_id] = use_node
        self._children[node_id] = []
        return node_id

    def add_route(self, from_node: str, from_field: str,
                  to_node: str, to_field: str) -> None:
        """Add a ROUTE between two node fields."""
        if from_node not in self._id_to_def:
            raise SceneError(f"Source node has no DEF name (node_id={from_node})")
        if to_node not in self._id_to_def:
            raise SceneError(f"Target node has no DEF name (node_id={to_node})")

        self._routes.append({
            "fromNode": self._id_to_def[from_node],
            "fromField": from_field,
            "toNode": self._id_to_def[to_node],
            "toField": to_field,
        })

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the scene."""
        self._get_node(node_id)

        if node_id in self._parent:
            parent_id = self._parent[node_id]
            self._children[parent_id].remove(node_id)
            del self._parent[node_id]

        for child_id in list(self._children.get(node_id, [])):
            self.remove_node(child_id)

        if node_id in self._id_to_def:
            def_name = self._id_to_def[node_id]
            del self._def_to_id[def_name]
            del self._id_to_def[node_id]

        del self._nodes[node_id]
        del self._children[node_id]

    def add_meta(self, name: str, content: str) -> None:
        """Add a meta tag to the scene head."""
        self._metas.append({"name": name, "content": content})

    def set_profile(self, profile: str) -> None:
        """Set the X3D profile."""
        profiles = self._uom.get_profiles()
        if profile not in profiles:
            raise SceneError(f"Unknown profile: {profile}")
        self._profile = profile

    def get_model(self) -> X3D:
        """Build and return the complete X3D model."""
        head_children = [meta(name=m["name"], content=m["content"])
                         for m in self._metas]
        h = head(children=head_children) if head_children else None

        scene_children = []
        root_ids = [nid for nid in self._nodes if nid not in self._parent]
        for nid in root_ids:
            self._collect_tree(nid, scene_children)

        for r in self._routes:
            scene_children.append(ROUTE(
                fromNode=r["fromNode"], fromField=r["fromField"],
                toNode=r["toNode"], toField=r["toField"],
            ))

        return X3D(
            profile=self._profile,
            version="4.1",
            head=h,
            Scene=Scene(children=scene_children),
        )

    def _collect_tree(self, node_id: str, out: list) -> None:
        """Recursively collect a node and its children for scene assembly."""
        node = self._nodes[node_id]
        node_type = type(node).__name__
        child_ids = self._children.get(node_id, [])

        if child_ids:
            children_list = []
            non_children = []
            for cid in child_ids:
                child = self._nodes[cid]
                child_type = type(child).__name__
                cf = self._uom.get_container_field(child_type)
                if cf == "children":
                    sub = []
                    self._collect_tree(cid, sub)
                    children_list.extend(sub)
                else:
                    non_children.append((cid, cf))

            if hasattr(node, "children") and children_list:
                node.children = children_list
            for cid, cf in non_children:
                if cf:
                    child_sub = []
                    self._collect_tree(cid, child_sub)
                    if child_sub:
                        setattr(node, cf, child_sub[0])

        out.append(node)

    def to_xml(self) -> str:
        """Serialize scene to X3D XML encoding."""
        return self.get_model().XML()

    def to_json(self) -> str:
        """Serialize scene to X3D JSON encoding."""
        return self.get_model().JSON()

    def to_vrml(self) -> str:
        """Serialize scene to ClassicVRML encoding."""
        return self.get_model().VRML()

    def reset(self) -> None:
        """Clear all scene state."""
        self.__init__()

    def _get_node(self, node_id: str) -> object:
        """Get a node by ID, raising SceneError if not found."""
        if node_id not in self._nodes:
            raise SceneError(f"No node with ID: {node_id}")
        return self._nodes[node_id]
