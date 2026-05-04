# X3D Node Reference (v4.0)

Complete list of X3D nodes organized by component. ~260 nodes total.

## Core
- `MetadataBoolean` — boolean metadata values
- `MetadataDouble` — double-precision float metadata
- `MetadataFloat` — float metadata values
- `MetadataInteger` — integer metadata values
- `MetadataSet` — set of metadata nodes
- `MetadataString` — string metadata values
- `WorldInfo` — scene-level information (title, info strings)

## Time
- `TimeSensor` — generates time-based events for animation

## Networking
- `Anchor` — grouping node; loads content on user selection
- `Inline` — includes external X3D scene
- `LoadSensor` — tracks loading status of Inline/url nodes

## Grouping
- `Group` — basic grouping, no spatial transform
- `StaticGroup` — optimized group (no runtime changes)
- `Switch` — selects one child to render (whichChoice)
- `Transform` — spatial positioning: translation, rotation, scale

## Rendering
- `ClipPlane` — clips geometry by a half-space
- `Color` — per-vertex RGB colors
- `ColorRGBA` — per-vertex RGBA colors
- `Coordinate` — 3D vertex positions
- `CoordinateDouble` — double-precision vertex positions
- `IndexedLineSet` — polylines defined by indexed vertices
- `IndexedTriangleFanSet` — indexed triangle fans
- `IndexedTriangleSet` — indexed triangles
- `IndexedTriangleStripSet` — indexed triangle strips
- `LineSet` — polylines defined by vertex lists
- `Normal` — per-vertex normal vectors
- `PointSet` — rendered point cloud
- `Tangent` — per-vertex tangent vectors (for normal mapping)
- `TriangleFanSet` — triangle fans
- `TriangleSet` — triangle list
- `TriangleStripSet` — triangle strips

## Shape
- `AcousticProperties` — sound interaction with geometry surfaces
- `Appearance` — visual properties container (material, texture, shader)
- `FillProperties` — filled/hatched rendering style
- `LineProperties` — line width/style
- `Material` — Phong lighting model (diffuseColor, specularColor, emissiveColor, shininess, transparency)
- `PhysicalMaterial` — PBR metallic-roughness model (baseColor, metallic, roughness) **[NEW in 4.0]**
- `PointProperties` — point size/attenuation
- `Shape` — pairs geometry with appearance
- `TwoSidedMaterial` — different materials for front/back faces
- `UnlitMaterial` — emissive-only, no lighting calculations **[NEW in 4.0]**

## Geometry3D
- `Box` — axis-aligned box (size)
- `Cone` — cone with optional bottom cap (bottomRadius, height)
- `Cylinder` — cylinder with optional caps (radius, height)
- `ElevationGrid` — height-field terrain (xDimension, zDimension, height[])
- `Extrusion` — 2D cross-section swept along a spine
- `IndexedFaceSet` — arbitrary polygon mesh (coordIndex, coord)
- `Sphere` — sphere (radius)

## Geometry2D
- `Arc2D` — circular arc line
- `ArcClose2D` — filled circular arc (PIE or CHORD)
- `Circle2D` — circle outline
- `Disk2D` — filled circle/annulus
- `Polyline2D` — 2D polyline
- `Polypoint2D` — 2D point set
- `Rectangle2D` — 2D rectangle
- `TriangleSet2D` — 2D triangles

## Text
- `FontStyle` — font family, size, style, justification
- `Text` — 3D text string(s)

## Sound
- `Analyser` — real-time frequency/time-domain analysis
- `AudioClip` — audio file source (.wav, .mp3, etc.)
- `AudioDestination` — audio output endpoint
- `BiquadFilter` — parametric audio filter
- `BufferAudioSource` — audio buffer playback
- `ChannelMerger` — merge audio channels
- `ChannelSelector` — select audio channel
- `ChannelSplitter` — split audio channels
- `Convolver` — convolution reverb
- `Delay` — audio delay
- `DynamicsCompressor` — audio dynamics compression
- `Gain` — audio volume control
- `ListenerPointSource` — listener position for spatial audio
- `MicrophoneSource` — live microphone input
- `OscillatorSource` — synthesized audio waveform
- `PeriodicWave` — custom waveform definition
- `Sound` — basic positional audio
- `SpatialSound` — advanced spatial audio (Web Audio API)
- `WaveShaper` — nonlinear audio distortion

## Lighting
- `DirectionalLight` — parallel rays (sun-like)
- `EnvironmentLight` — image-based lighting **[NEW in 4.0]**
- `PointLight` — omnidirectional point source
- `SpotLight` — cone-shaped light source

## Texturing
- `ImageTexture` — image file texture (.png, .jpg, etc.)
- `MovieTexture` — video texture
- `MultiTexture` — layer multiple textures
- `MultiTextureCoordinate` — multiple texture coordinate sets
- `MultiTextureTransform` — multiple texture transforms
- `PixelTexture` — inline pixel data texture
- `TextureCoordinate` — UV coordinates
- `TextureCoordinateGenerator` — auto-generated tex coords
- `TextureProperties` — minification/magnification filters, anisotropy
- `TextureTransform` — 2D texture coordinate transform

## Interpolation
- `ColorInterpolator` — animate colors
- `CoordinateInterpolator` — animate vertex positions
- `CoordinateInterpolator2D` — animate 2D positions
- `EaseInEaseOut` — easing function modifier
- `NormalInterpolator` — animate normal vectors
- `OrientationInterpolator` — animate rotations (SLERP)
- `PositionInterpolator` — animate 3D positions
- `PositionInterpolator2D` — animate 2D positions
- `ScalarInterpolator` — animate single float values
- `SplinePositionInterpolator` — spline-based position animation
- `SplinePositionInterpolator2D` — spline-based 2D animation
- `SplineScalarInterpolator` — spline-based scalar animation
- `SquadOrientationInterpolator` — spherical spline rotation

## PointingDeviceSensor
- `CylinderSensor` — drag around Y-axis (rotation)
- `PlaneSensor` — drag in XY plane (translation)
- `SphereSensor` — drag in 3D (rotation)
- `TouchSensor` — click/hover detection

## KeyDeviceSensor
- `KeySensor` — keyboard key events
- `StringSensor` — text input

## EnvironmentalSensor
- `ProximitySensor` — detect viewer proximity
- `TransformSensor` — detect transform changes
- `VisibilitySensor` — detect when region is visible

## Navigation
- `Billboard` — auto-orient geometry toward viewer
- `Collision` — collision detection with geometry
- `LOD` — level-of-detail switching by distance
- `NavigationInfo` — navigation type, speed, avatar size
- `OrthoViewpoint` — orthographic camera
- `Viewpoint` — perspective camera (position, orientation, fieldOfView)
- `ViewpointGroup` — group viewpoints in UI

## EnvironmentalEffects
- `Background` — sky/ground colors and panorama textures
- `Fog` — distance-based fog
- `FogCoordinate` — per-vertex fog depth
- `LocalFog` — scoped fog effect
- `TextureBackground` — texture-based background

## Geospatial
- `GeoCoordinate`, `GeoElevationGrid`, `GeoLOD`, `GeoLocation`, `GeoMetadata`, `GeoOrigin`, `GeoPositionInterpolator`, `GeoProximitySensor`, `GeoTouchSensor`, `GeoTransform`, `GeoViewpoint`

## HAnim (Humanoid Animation)
- `HAnimDisplacer`, `HAnimHumanoid`, `HAnimJoint`, `HAnimMotion`, `HAnimPose`, `HAnimSegment`, `HAnimSite`

## NURBS
- `Contour2D`, `ContourPolyline2D`, `NurbsCurve`, `NurbsCurve2D`, `NurbsOrientationInterpolator`, `NurbsPatchSurface`, `NurbsPositionInterpolator`, `NurbsSet`, `NurbsSurfaceInterpolator`, `NurbsSweptSurface`, `NurbsSwungSurface`, `NurbsTextureCoordinate`, `NurbsTrimmedSurface`

## Scripting
- `Script` — embedded ECMAScript/JavaScript logic

## EventUtilities
- `BooleanFilter` — split boolean into true/false/negate
- `BooleanSequencer` — output boolean sequence by key
- `BooleanToggle` — toggle boolean state
- `BooleanTrigger` — convert event to boolean
- `IntegerSequencer` — output integer sequence by key
- `IntegerTrigger` — convert event to integer
- `TimeTrigger` — convert event to time

## Shaders
- `ComposedShader` — GLSL/HLSL shader program
- `FloatVertexAttribute` — custom float vertex data
- `Matrix3VertexAttribute` — custom matrix3 vertex data
- `Matrix4VertexAttribute` — custom matrix4 vertex data
- `ShaderPart` — vertex/fragment shader source

## CADGeometry
- `CADAssembly`, `CADFace`, `CADLayer`, `CADPart`, `IndexedQuadSet`, `QuadSet`

## Texturing3D
- `ComposedTexture3D`, `ImageTexture3D`, `PixelTexture3D`, `TextureCoordinate3D`, `TextureCoordinate4D`, `TextureTransform3D`, `TextureTransformMatrix3D`

## CubeMapTexturing
- `ComposedCubeMapTexture`, `GeneratedCubeMapTexture`, `ImageCubeMapTexture`

## Layering
- `Layer`, `LayerSet`, `Viewport`

## Layout
- `Layout`, `LayoutGroup`, `LayoutLayer`, `ScreenFontStyle`, `ScreenGroup`

## RigidBodyPhysics
- `BallJoint`, `CollidableOffset`, `CollidableShape`, `CollisionCollection`, `CollisionSensor`, `CollisionSpace`, `Contact`, `DoubleAxisHingeJoint`, `RigidBody`, `RigidBodyCollection`, `SingleAxisHingeJoint`, `SliderJoint`

## Picking
- `LinePickSensor`, `PickableGroup`, `PointPickSensor`, `PrimitivePickSensor`, `VolumePickSensor`

## Followers
- `ColorChaser`, `ColorDamper`, `CoordinateChaser`, `CoordinateDamper`, `OrientationChaser`, `OrientationDamper`, `PositionChaser`, `PositionChaser2D`, `PositionDamper`, `PositionDamper2D`, `ScalarChaser`, `ScalarDamper`, `TexCoordChaser2D`, `TexCoordDamper2D`

## ParticleSystems
- `BoundedPhysicsModel`, `ConeEmitter`, `ExplosionEmitter`, `ForcePhysicsModel`, `ParticleSystem`, `PointEmitter`, `PolylineEmitter`, `SurfaceEmitter`, `VolumeEmitter`, `WindPhysicsModel`

## VolumeRendering
- `BlendedVolumeStyle`, `BoundaryEnhancementVolumeStyle`, `CartoonVolumeStyle`, `ComposedVolumeStyle`, `EdgeEnhancementVolumeStyle`, `IsoSurfaceVolumeData`, `OpacityMapVolumeStyle`, `ProjectionVolumeStyle`, `SegmentedVolumeData`, `ShadedVolumeStyle`, `SilhouetteEnhancementVolumeStyle`, `ToneMappedVolumeStyle`, `VolumeData`

## TextureProjection
- `TextureProjector`, `TextureProjectorParallel`
