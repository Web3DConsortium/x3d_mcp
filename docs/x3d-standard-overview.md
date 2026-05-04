# X3D Standard Overview

## What is X3D?

X3D (Extensible 3D) is an **ISO-ratified, royalty-free open standard** file format and runtime architecture for representing and communicating 3D scenes and objects. It is the successor to VRML (Virtual Reality Modeling Language, 1997) and is maintained by the [Web3D Consortium](https://www.web3d.org).

## Current Version

**X3D 4.0** — released December 2023, ISO/IEC certified International Standard.
**X3D 4.1** — under development (draft).

## ISO Standards

| Standard | Title | Current Version |
|----------|-------|-----------------|
| **ISO/IEC 19775-1** | X3D Abstract Architecture & Base Components | V4.0 |
| **ISO/IEC 19775-2** | Scene Access Interface (SAI) | V3.3 |
| **ISO/IEC 19776-1** | XML Encoding | V3.3 |
| **ISO/IEC 19776-2** | Classic VRML Encoding | V3.3 |
| **ISO/IEC 19776-3** | Compressed Binary Encoding | V3.3 |
| **ISO/IEC 19776-5** | JSON Encoding | V3.3 (draft) |
| **ISO/IEC 19777-1** | ECMAScript/JavaScript Binding | V3.3 |
| **ISO/IEC 19777-2** | Java Binding | V3.0 |
| **ISO/IEC 19774** | HAnim (Humanoid Animation) | V2.0 |

## File Formats / Extensions

| Extension | Encoding | Description |
|-----------|----------|-------------|
| `.x3d` | XML | Primary encoding, XML-based |
| `.x3dv` | Classic VRML | Text-based VRML-style syntax |
| `.x3db` | Compressed Binary | Optimized for file size/performance |
| `.x3dj` / `.json` | JSON | JavaScript Object Notation encoding |

## Scene Graph Architecture

X3D uses a **directed acyclic graph (DAG)** scene graph with two primary axes:

1. **Transformation Hierarchy** — spatial relationships of rendering objects
2. **Behavior Graph** — connections between fields and event flow (ROUTE)

### Core Concepts

- **Nodes**: Fundamental building blocks (e.g., Shape, Transform, Material)
- **Fields**: Typed data values within nodes (SFFloat, MFVec3f, SFNode, etc.)
- **Routes**: Declarative connections between node fields for event propagation
- **DEF/USE**: Named node references (USE references the same node, not a copy)
- **Prototypes (PROTO)**: Author-defined reusable node types
- **EXTERNPROTO**: References to external prototype definitions

### Field Access Types

| Access Type | Description |
|-------------|-------------|
| `initializeOnly` | Set once at load time, no runtime changes |
| `inputOnly` | Receives events only (prefixed `set_`) |
| `outputOnly` | Sends events only (suffixed `_changed`) |
| `inputOutput` | Full read/write access |

### Field Type Naming Convention

- **SF** prefix = Single-value field (SFFloat, SFVec3f, SFColor, SFNode, SFBool, SFString, SFRotation, etc.)
- **MF** prefix = Multi-value/array field (MFFloat, MFVec3f, MFColor, MFNode, etc.)

## Profiles

Profiles define feature subsets for different use cases:

| Profile | Use Case |
|---------|----------|
| **Core** | Minimal baseline |
| **Interchange** | Asset sharing / 3D model distribution |
| **Interactive** | Real-time user interaction |
| **MPEG-4 Interactive** | Streaming multimedia |
| **Immersive** | Complex interactions, physics, advanced rendering |
| **Full** | Complete X3D functionality |
| **CADInterchange** | Engineering / product design |
| **MedicalInterchange** | Medical imaging data |

## Components (X3D v4.0)

X3D functionality is organized into 37 components (clauses 7–43 of the spec):

| Component | Description |
|-----------|-------------|
| Core | Metadata, WorldInfo |
| Time | TimeSensor |
| Networking | Anchor, Inline, LoadSensor |
| Grouping | Group, Transform, Switch, StaticGroup |
| Rendering | Coordinate, Color, Normal, IndexedLineSet, TriangleSet, etc. |
| Shape | Shape, Appearance, Material, PhysicalMaterial, UnlitMaterial, FillProperties, LineProperties |
| Geometry3D | Box, Cone, Cylinder, Sphere, ElevationGrid, Extrusion, IndexedFaceSet |
| Geometry2D | Arc2D, Circle2D, Disk2D, Rectangle2D, etc. |
| Text | Text, FontStyle |
| Sound | Sound, SpatialSound, AudioClip, Web Audio API nodes |
| Lighting | DirectionalLight, PointLight, SpotLight, EnvironmentLight |
| Texturing | ImageTexture, MovieTexture, PixelTexture, MultiTexture, TextureTransform |
| Interpolation | ColorInterpolator, PositionInterpolator, OrientationInterpolator, ScalarInterpolator, etc. |
| PointingDeviceSensor | TouchSensor, PlaneSensor, CylinderSensor, SphereSensor |
| KeyDeviceSensor | KeySensor, StringSensor |
| EnvironmentalSensor | ProximitySensor, TransformSensor, VisibilitySensor |
| Navigation | Viewpoint, OrthoViewpoint, NavigationInfo, Billboard, Collision, LOD |
| EnvironmentalEffects | Background, Fog, TextureBackground |
| Geospatial | GeoViewpoint, GeoLocation, GeoCoordinate, GeoElevationGrid |
| HAnim | HAnimHumanoid, HAnimJoint, HAnimSegment, HAnimMotion |
| NURBS | NurbsCurve, NurbsPatchSurface, NurbsTrimmedSurface |
| DIS | Distributed Interactive Simulation nodes |
| Scripting | Script node |
| EventUtilities | BooleanFilter, BooleanToggle, IntegerSequencer, TimeTrigger |
| Shaders | ComposedShader, ShaderPart |
| CADGeometry | CADAssembly, CADFace, CADPart, IndexedQuadSet |
| Texturing3D | ComposedTexture3D, ImageTexture3D, PixelTexture3D |
| CubeMapTexturing | ComposedCubeMapTexture, GeneratedCubeMapTexture, ImageCubeMapTexture |
| Layering | Layer, LayerSet, Viewport |
| Layout | Layout, LayoutGroup, ScreenFontStyle |
| RigidBodyPhysics | RigidBody, CollisionSensor, various joint types |
| Picking | LinePickSensor, PointPickSensor, VolumePickSensor |
| Followers | Chasers and Dampers for smooth animation |
| ParticleSystems | ParticleSystem, emitters, physics models |
| VolumeRendering | VolumeData, various volume styles |
| TextureProjection | TextureProjector, TextureProjectorParallel |
| Annotation | Annotation nodes |

## X3D v4.0 Highlights (vs 3.3)

- **Physically Based Rendering (PBR)**: New `PhysicalMaterial` and `UnlitMaterial` nodes
- **HTML5 Integration**: X3D Unified Object Model (X3DUOM) for web authoring
- **glTF 2.0 Composition**: Compose scenes with glTF assets
- **W3C Web Audio API**: Full spatial audio support
- **HAnim v2**: Motion animation support
- **Multiple Language Bindings**: JavaScript, Java, C#, C++, Python

## Coordinate System & Units

| Property | Default |
|----------|---------|
| Coordinate system | Right-handed Cartesian |
| Length | Metres |
| Angle | Radians |
| Time | Seconds |
| Color | RGB [0.0, 1.0] per component |
| Viewer orientation | On Z-axis, looking toward origin |

## Execution Model (per frame)

1. Update camera from bound Viewpoint
2. Evaluate sensor inputs
3. Evaluate and propagate routes
4. Repeat 2-3 if new events generated
5. Evaluate particle systems
6. Evaluate physics models
7. Render frame
