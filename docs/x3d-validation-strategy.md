# X3D Validation Strategy for MCP

## Goal

The X3D MCP must generate **valid X3D** output. This document captures the validation approach.

## Validation Layers

### Layer 1: Structural Correctness (built into generator)

- Correct XML declaration and encoding
- Proper DOCTYPE declaration
- Required root attributes (profile, version)
- Valid head/meta/Scene structure
- Nodes only contain valid child nodes per spec
- Fields have correct types and access semantics

### Layer 2: Schema Conformance

- XML Schema (XSD) validation against `x3d-4.0.xsd`
- Ensures:
  - All element names are valid X3D nodes
  - All attributes are valid fields for their parent node
  - Attribute value types match field definitions
  - Required attributes are present
  - Enumerated values are from valid sets

### Layer 3: DTD Validation

- DOCTYPE validation against `x3d-4.0.dtd`
- Validates parent-child element relationships
- Validates attribute declarations

### Layer 4: Semantic Validation (Schematron-level)

- DEF must be declared before USE reference
- Interpolator `key` array length must match `keyValue` divisions
- `coordIndex` values must be within `Coordinate.point` bounds
- ROUTE `fromNode`/`toNode` must reference valid DEF names
- ROUTE field names must exist on referenced nodes
- `url` fields should have fallback values
- No circular prototype definitions

## Implementation Options

### Option A: Offline XSD Validation (Recommended)

Download and bundle `x3d-4.0.xsd` for local validation using:
- Python: `lxml` library (XSD + Schematron support)
- Node.js: `libxmljs2` or `xmllint` via subprocess

### Option B: Schematron XSLT Pipeline

1. Apply `X3dSchematronValidityChecks.xslt` to generated X3D
2. Parse SVRL (Schematron Validation Report Language) output
3. Apply `SvrlReportText.xslt` for human-readable diagnostics

### Option C: X3D Validator API

- Use https://savage.nps.edu/X3dValidator if available
- Fallback: local validation

### Option D: Generative Correctness by Construction

- Build node/field constraints directly from X3DUOM
- Parse `X3dUnifiedObjectModel-4.0.xml` to extract:
  - Valid node names
  - Valid fields per node (name, type, default, accessType)
  - Valid child nodes per containerField
  - Valid profiles and their component sets
- Validate at generation time, not post-hoc
- Still run XSD as a safety net

## Recommended Approach: D + A

1. **Parse X3DUOM** at build time to generate validation tables
2. **Validate at generation** — reject invalid node/field combinations during scene construction
3. **Post-validate with XSD** — run `lxml` XSD validation as final check
4. **Optional Schematron** — for advanced semantic checks

## Key Constraints from Spec

### containerField Mapping

Each node has a default `containerField` that determines where it sits in parent:
- `Shape` → `children` (of Group/Transform)
- `Material` → `material` (of Appearance)
- `Sphere`/`Box`/etc. → `geometry` (of Shape)
- `ImageTexture` → `texture` (of Appearance)
- `Coordinate` → `coord` (of IndexedFaceSet)
- `Normal` → `normal` (of IndexedFaceSet)
- `TextureCoordinate` → `texCoord` (of IndexedFaceSet)

### Profile → Component Mapping

The declared `profile` determines which components/nodes are available:
- `Interchange`: Shape, Geometry3D, Texturing, Lighting, Navigation, Grouping, Rendering, Core, EnvironmentalEffects
- `Immersive`: All of Interchange + Sound, Sensors, Interpolation, EventUtilities, Scripting, etc.
- `Full`: Everything

### Value Formatting (XML encoding)

- Colors: `'R G B'` (space-separated floats 0–1)
- Vectors: `'X Y Z'` (space-separated)
- Rotations: `'X Y Z angle'` (axis + radians)
- Boolean: `'true'` / `'false'`
- coordIndex: integers with `-1` as face terminator
- url: `'"primary.x3d" "fallback.x3d"'` (MFString in quotes)

### Value Formatting (JSON encoding)

- Colors: `[R, G, B]` (JSON array)
- Vectors: `[X, Y, Z]` (JSON array)
- Boolean: `true`/`false` (JSON native)
- coordIndex: `[0, 1, 2, -1, ...]` (JSON array)
- url: `["primary.x3d", "fallback.x3d"]` (JSON string array)
