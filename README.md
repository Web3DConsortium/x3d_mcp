# x3d_mcp

MCP server for generating, validating, and converting valid X3D content. Built on the official Web3D Consortium toolchain.

## Overview

x3d_mcp exposes X3D capabilities to LLMs via the Model Context Protocol (MCP). It generates spec-compliant X3D scenes in XML, JSON, and ClassicVRML encodings, with full validation against the ISO/IEC 19775 standard.

LLMs have spatial and visual understanding of 3D space. X3D (Extensible 3D) provides a declarative, XML-based means to express that understanding as valid, interoperable 3D content. This server bridges the two.

## Design Decisions

### Language: Python

- **`x3d.py`** (PyPI `x3d` v4.0.65, BSD-3) -- official Web3D Consortium package, auto-generated from X3DUOM
- **`lxml`** -- XSD and ISO-Schematron validation, 42x faster than pure-Python alternatives
- **`FastMCP`** (PyPI `mcp`) -- official Anthropic MCP SDK, decorator-based tool registration
- All dependencies are BSD/MIT licensed. Project uses [Web3D Consortium Open-Source License](https://www.web3d.org/license).

### Two Operating Modes

**Workflow Mode** -- high-level tools for end-to-end scene generation. The LLM describes what it wants; the server handles construction, validation, and serialization. Fewer tool calls, higher reliability.

**Granular Mode** -- low-level tools for node-by-node scene construction. The LLM builds the scene graph incrementally: create nodes, set fields, add children, define routes. Full control for complex or iterative workflows.

Both modes validate output before returning it.

### JSON Conversion

JSON and ClassicVRML encoding uses `x3d.py`'s built-in `.JSON()` and `.VRML()` serialization methods. These are auto-generated from X3DUOM and produce spec-compliant output directly. The Web3D Consortium's `X3dToJson.xslt` is XSLT 2.0, which is incompatible with lxml (XSLT 1.0 only), so we use the native Python serialization instead.

### Validation Pipeline

Four layers, matching the X3D specification's own validation hierarchy:

1. **Type checking at generation time** -- `x3d.py` enforces field types, ranges, and enumerations during scene construction
2. **XSD validation** -- `lxml.etree.XMLSchema` against `x3d-4.1.xsd` (bundled with companion schemas)
3. **JSON Schema validation** -- `jsonschema.Draft202012Validator` against `x3d-4.0-JSONSchema.json` (Web3D Consortium, 364 `$defs`). Catches misspelled keys (`head`/`meta`/etc.), unknown node names inside `Scene`, missing required fields (`encoding`, `@version`, `@profile`, `Scene`), and wrong-type values. Web3D has not yet published a 4.1 JSON Schema, so the 4.0 schema is bundled in the meantime.
4. **Semantic checks** -- imperative Python checks for authoring-level bugs XSD cannot express: missing geometry/appearance on Shapes, empty grouping nodes, duplicate DEFs, USE/DEF consistency, ROUTE field/access-type/type validity, missing Viewpoints. Adapted from [niknarra/x3d-mcp](https://github.com/niknarra/x3d-mcp) (Nikhil Narra, Nicholas Polys -- Virginia Tech / Web3D Consortium).

### X3DUOM as Foundation

The `X3dUnifiedObjectModel-4.1.xml` (X3DUOM) is the single source of truth for all 265 concrete nodes (5 new in 4.1: EnvironmentLight, FontLibrary, HAnimPose, InlineGeometry, Tangent), abstract types, simple types, and statements. It is parsed at build time to generate:

- Node/field metadata lookup tables
- containerField mapping rules
- Enumeration value sets
- Default value tables
- Inheritance hierarchy

## Architecture

```
x3d_mcp/
  src/
    server.py              # FastMCP server, tool registration
    tools/
      workflow.py          # High-level scene generation tools
      granular.py          # Low-level node manipulation tools
      validate_tool.py     # Validation MCP tool wrappers
      convert.py           # Encoding conversion (XML, JSON, VRML)
      query.py             # Node/field metadata queries
      render.py            # X3DOM HTML page wrapper for browser viewing
      scene_ops.py         # Scene CRUD: modify, remove, move nodes
      animate.py           # Animation chain generation (TimeSensor + Interpolator + ROUTE)
      prompts.py           # MCP prompts for guided workflows
    x3d_utils/
      scene.py             # Scene graph state management
      x3duom.py            # X3DUOM parser, node/field metadata
    validation/
      validate.py          # XSD + JSON validation pipeline
      semantic.py          # Layer 4 semantic checks (DEF/USE, ROUTE validity, etc.)
      schemas/             # Bundled x3d-4.1.xsd, x3d-4.1.dtd, X3DUOM 4.1
  dataset/
    schema.py              # Canonical training example schema, normalization
    normalize.py           # JSONL schema normalization CLI
    validate_schema.py     # JSONL schema validation CLI
    augment.py             # Tunable augmentation pipeline CLI
    filter.py              # Dataset filter/split by source and token budget
    generate.py            # Numeric sequence example generator CLI
    generators/
      numeric_sequences.py # IndexedFaceSet, Extrusion, Interpolator generators
  tests/
  output/
    logs/                  # Container logs per issue number
  docs/                    # Research and reference documentation
  Dockerfile
  docker-compose.yml
  pyproject.toml
  README.md
```

## MCP Tools

### Workflow Tools

| Tool | Description |
|------|-------------|
| `create_scene` | Generate a complete X3D scene from a natural language description. Returns validated X3D in the requested encoding (xml, json, vrml). |
| `create_geometry` | Generate a single geometric object with material, transform, and optional animation. |
| `compose_scene` | Combine multiple objects, lights, viewpoints, and backgrounds into a complete scene. |

### Granular Tools

| Tool | Description |
|------|-------------|
| `create_node` | Create an X3D node by type name. Returns a node handle for further manipulation. |
| `set_field` | Set a field value on a node (with type validation). |
| `add_child` | Add a child node to a parent (validates containerField rules). |
| `add_route` | Create a ROUTE between two node fields (validates field existence and type compatibility). |
| `def_node` | Assign a DEF name to a node. |
| `use_node` | Reference a previously DEF'd node via USE. |
| `remove_node` | Remove a node from the scene graph. |
| `get_scene` | Serialize the current scene state to X3D (xml, json, or vrml). |
| `reset_scene` | Clear all nodes and reset the scene to empty state. |

### Validation Tools

| Tool | Description |
|------|-------------|
| `validate_x3d` | Validate an X3D document (XML or JSON) against the XSD schema. Returns pass/fail with detailed error messages. |
| `validate_current_scene` | Validate the current granular scene against the XSD schema. |
| `validate_semantic` | Run semantic checks on X3D XML beyond XSD: missing geometry/appearance on Shapes, empty grouping nodes, duplicate DEFs, USE/DEF consistency, ROUTE field/access-type/type-match validity, missing Viewpoints. Returns a markdown report. |

### Conversion Tools

| Tool | Description |
|------|-------------|
| `convert_x3d` | Convert X3D between encodings: xml, json, vrml. Uses x3d.py native serialization. |

### Query Tools

| Tool | Description |
|------|-------------|
| `list_nodes` | List available X3D nodes, optionally filtered by component. |
| `describe_node` | Get full field definitions for a node type: field names, types, defaults, ranges, access types. |
| `list_components` | List all X3D components with their support levels. |
| `list_profiles` | List available profiles and their component requirements. |

### Render Tools

| Tool | Description |
|------|-------------|
| `x3dom_page` | Wrap X3D content (full document or scene fragment) in a standalone X3DOM HTML page for browser viewing. Lowercases tag/attr names, strips namespace declarations, embeds X3DOM 1.8.2 from CDN. Adapted from [niknarra/x3d-mcp](https://github.com/niknarra/x3d-mcp). |
| `x3dom_starter` | Return a starter X3DOM HTML page with a small example scene. Useful as a known-good baseline. |

### Scene Manipulation Tools

Operate on serialized X3D content (file path or inline XML) and return the modified document. Distinct from the granular tools, which mutate the in-memory `SceneManager` state.

| Tool | Description |
|------|-------------|
| `modify_x3d_node` | Update one or more attribute values on a DEF'd node. Field changes passed as a JSON object string. Adapted from [niknarra/x3d-mcp](https://github.com/niknarra/x3d-mcp). |
| `remove_x3d_node` | Remove a node and its children. Identify by DEF name or by node type plus index. |
| `move_x3d_node` | Reparent a DEF'd node. Empty `new_parent_def` moves it to the Scene root. Rejects moves that would create a cycle. |

### Animation Tools

Generate event-driven animation in X3D content (TimeSensor + Interpolator + ROUTE chains). Adapted from [niknarra/x3d-mcp](https://github.com/niknarra/x3d-mcp).

| Tool | Description |
|------|-------------|
| `animate_x3d_node` | Insert a complete animation chain for a target field. Auto-selects the interpolator from the field's type via X3DUOM (SFRotation -> OrientationInterpolator, SFVec3f -> PositionInterpolator, SFColor -> ColorInterpolator, SFFloat -> ScalarInterpolator, etc.). |
| `add_x3d_route` | Validate and insert a single ROUTE statement, with full DEF / field / accessType / type-match checking. |
| `x3d_animation_info` | Reference documentation for X3D's animation system. Topics: `interpolators`, `timesensor`, `routes`, `examples`, or empty for overview. |

## MCP Prompts

Guided multi-step workflows. Prompts steer the LLM through the right tool sequence for tasks where ordering matters. Adapted from [niknarra/x3d-mcp](https://github.com/niknarra/x3d-mcp).

| Prompt | Argument | Description |
|--------|----------|-------------|
| `build_scene` | `description` | Step-by-step guide to build an X3D scene from scratch. Covers both workflow and granular paths, validation, and X3DOM rendering. |
| `audit_scene` | `content` | Audit existing X3D content for schema and authoring issues. Walks through `validate_x3d`, `validate_semantic`, `describe_node`, and the scene CRUD tools. |
| `animate_scene` | `target_description` | Add animation. Walks through `x3d_animation_info`, `describe_node`, `animate_x3d_node`, validation, and rendering. |
| `convert_to_x3dom` | -- | Convert X3D content to a browser-viewable X3DOM HTML page via `validate_x3d` and `x3dom_page`. |

## Dataset Pipeline

Tools for building, normalizing, augmenting, and generating X3D training data for fine-tuning.

### Schema Normalization

Normalize mixed-type metadata fields to a consistent schema:

```bash
python -m dataset.normalize input.jsonl output.jsonl --report
python -m dataset.validate_schema input.jsonl
```

### Augmentation

Tunable augmentation with configurable instruction diversity, X3D mutation, and token budget:

```bash
python -m dataset.augment base.jsonl augmented.jsonl \
    --ratio 5 --seed 42 \
    --instruction-diversity 0.5 \
    --x3d-mutation 0.3 \
    --max-tokens 8192
```

### Filtering

Filter by source (original/augmented) and token budget:

```bash
python -m dataset.filter input.jsonl output.jsonl --source original --max-tokens 8192
```

### Numeric Sequence Generation

Generate training examples targeting long numeric arrays (IndexedFaceSet, Extrusion, Interpolator):

```bash
python -m dataset.generate output.jsonl \
    --type all --count 50 --complexity mixed \
    --validate --seed 42
```

## X3D Standard Reference

This server targets **X3D version 4.1** (candidate draft, building on ISO/IEC 19775-1:2023 v4.0).

### Supported Encodings

| Encoding | Extension | Spec |
|----------|-----------|------|
| XML | `.x3d` | ISO/IEC 19776-1 |
| JSON | `.x3dj` | ISO/IEC 19776-5 |
| ClassicVRML | `.x3dv` | ISO/IEC 19776-2 |

### Profiles

Default profile is `Interchange` (static geometry, textures, lighting, navigation). Automatically upgraded to `Immersive` or `Full` when the scene uses sensors, animation, scripting, or advanced components.

| Profile | Use Case |
|---------|----------|
| Core | Minimal baseline |
| Interchange | Asset sharing, static 3D models |
| Interactive | User interaction, basic behaviors |
| Immersive | Sensors, animation, scripting, physics |
| Full | Everything |
| CADInterchange | Engineering / product design |

### Key Components (37 total)

Geometry3D, Shape, Grouping, Rendering, Lighting, Texturing, Navigation, EnvironmentalEffects, Interpolation, PointingDeviceSensor, EnvironmentalSensor, KeyDeviceSensor, EventUtilities, Sound, Text, Scripting, Shaders, NURBS, Geospatial, HAnim, CADGeometry, RigidBodyPhysics, ParticleSystems, VolumeRendering, Followers, Picking, Layering, Layout, Texturing3D, CubeMapTexturing, TextureProjection, Annotation, DIS, Core, Time, Networking, Geometry2D.

Full node reference: [docs/x3d-node-reference.md](docs/x3d-node-reference.md)

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | >=1.7 | MCP SDK (FastMCP) |
| `x3d` | >=4.0.65 | Official X3D scene construction and type validation |
| `lxml` | >=6.0 | XSD validation, Schematron validation, XSLT transforms |
| `xmlschema` | >=4.3 | Pure-Python XSD validation (fallback) |
| `jsonschema` | >=4.26 | JSON Schema validation for X3D JSON encoding |

## Docker

All code lives on the host. Docker is used for testing and validation only.

```bash
docker compose up --build
```

The container mounts `src/` and `tests/` from the host. Logs are written to `output/logs/`.

## Reference Documentation

| Document | Description |
|----------|-------------|
| [docs/x3d-standard-overview.md](docs/x3d-standard-overview.md) | ISO standards, scene graph architecture, profiles, components, field types, execution model |
| [docs/x3d-file-structure.md](docs/x3d-file-structure.md) | Minimal valid files (XML/JSON/VRML), DOCTYPE declarations, encoding rules, 4-layer validation |
| [docs/x3d-node-reference.md](docs/x3d-node-reference.md) | All ~260 nodes organized by component with descriptions |
| [docs/x3d-examples.md](docs/x3d-examples.md) | Code patterns from hello world through PBR and animation. Links to 4,142+ Web3D example scenes |
| [docs/x3d-tools-and-references.md](docs/x3d-tools-and-references.md) | URLs for schemas, DTDs, X3DUOM, validators, viewers, converters, libraries |
| [docs/x3d-validation-strategy.md](docs/x3d-validation-strategy.md) | Validation approach: X3DUOM parsing, XSD, Schematron, containerField rules |
| [docs/ecosystem-research.md](docs/ecosystem-research.md) | Survey of existing tools, Python vs TypeScript analysis, community resources |

## External References

- X3D Specification (v4.1 draft): https://www.web3d.org/specifications/X3Dv4Draft/ISO-IEC19775-1v4.1-CD/Part01/Architecture.html
- X3D Specification (v4.0): https://www.web3d.org/specifications/X3Dv4Draft/ISO-IEC19775-1v4-WD2/Part01/Architecture.html
- X3D Tooltips (HTML): https://www.web3d.org/x3d/tooltips/X3dTooltips.html
- X3D Tooltips Profile (XML): https://www.web3d.org/x3d/tooltips/x3d-4.0.profile.xml
- X3D Examples Archive: https://www.web3d.org/x3d/content/examples/X3dForAdvancedModeling/
- X3D Resources: https://www.web3d.org/x3d/content/examples/X3dResources.html
- X3D Schemas and DTDs: https://www.web3d.org/specifications/
- X3D Unified Object Model: https://www.web3d.org/specifications/X3DUOM.html
- X3D Schematron QA: https://www.web3d.org/x3d/tools/schematron/X3dSchematron.html
- X3D JSON Encoding (19776-5): https://www.web3d.org/documents/specifications/19776-5/V3.3/Part05/concepts.html
- x3d.py Python Package: https://www.web3d.org/x3d/stylesheets/python/python.html
- MCP Specification: https://modelcontextprotocol.io/specification/2025-11-25
- FastMCP Documentation: https://gofastmcp.com/servers/tools
- Web3D Consortium: https://www.web3d.org

## Acknowledgments

The following features were adopted based on guidance from **Nikhil Narra** ([@niknarra](https://github.com/niknarra)), **Nicholas Polys** ([@npolys](https://github.com/npolys)), and **Don Brutzman** ([@brutzman](https://github.com/brutzman)) of the Web3D Consortium and X3D AI Working Group:

- **Semantic validation** (Validation Tools, Layer 4 of the pipeline) -- DEF/USE consistency, ROUTE validity, Shape completeness, empty-group detection, missing-Viewpoint advisory
- **Animation tools** -- TimeSensor + Interpolator + ROUTE chain auto-generation, single ROUTE insertion with type checking, animation reference docs
- **X3DOM rendering** -- standalone HTML page wrapper for browser preview
- **Scene CRUD** -- modify/remove/move operations on serialized X3D content with cycle detection
- **MCP guided prompts** -- `build_scene`, `audit_scene`, `animate_scene`, `convert_to_x3dom`

Reference implementation: [niknarra/x3d-mcp](https://github.com/niknarra/x3d-mcp). Related published work:

- Nikhil Narra, Anuj Marisetty, Nicholas Polys, and Ben Sandbrook. **X3Test: A Headless Browser-Based Framework for Automated Performance Benchmarking of X3D/X3DOM Scenes.** *Proceedings of the 30th International Conference on 3D Web Technology (Web3D '25)*, Siena, Italy, September 9-10, 2025. ACM, ISBN 979-8-4007-2038-3. [doi:10.1145/3746237.3746315](https://doi.org/10.1145/3746237.3746315) -- 3rd place, Web3D 2025 Tools Competition. Repo: [VT-Visionarium/X3Test](https://github.com/VT-Visionarium/X3Test). VTechworks copy: [471dddd8](https://vtechworks.lib.vt.edu/items/471dddd8-7665-4e6f-a8f5-7f9276213835).
- Earlier work probing visual/spatial knowledge in LLMs: [doi:10.1145/3665318.3677159](https://doi.org/10.1145/3665318.3677159), with the [LLM-generated X3D Model Browser](https://metagrid1.sv.vt.edu/~bsandbro/x3dgen/all_models/) as an empirical artifact.

Coordination ongoing via the X3D AI Working Group ([ai@web3d.org](https://web3d.org/mailman/listinfo/ai_web3d.org)) and the Web3D Consortium.

## License

[Web3D Consortium Open-Source License](https://www.web3d.org/license) -- see [LICENSE](LICENSE).
