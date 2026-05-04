# X3D Examples & Patterns

## Common Scene Patterns

### Hello World — Red Sphere

**XML (.x3d):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 4.0//EN"
  "http://www.web3d.org/specifications/x3d-4.0.dtd">
<X3D profile='Interchange' version='4.0'
     xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance'
     xsd:noNamespaceSchemaLocation='http://www.web3d.org/specifications/x3d-4.0.xsd'>
  <head>
    <meta name='title' content='HelloWorld.x3d'/>
    <meta name='description' content='A red sphere'/>
    <meta name='generator' content='X3D MCP Server'/>
  </head>
  <Scene>
    <Shape>
      <Appearance>
        <Material diffuseColor='1.0 0.0 0.0'/>
      </Appearance>
      <Sphere radius='1.0'/>
    </Shape>
  </Scene>
</X3D>
```

**JSON (.x3dj):**
```json
{
  "X3D": {
    "@profile": "Interchange",
    "@version": "4.0",
    "encoding": "UTF-8",
    "head": {
      "meta": [
        { "@name": "title", "@content": "HelloWorld.x3dj" },
        { "@name": "description", "@content": "A red sphere" },
        { "@name": "generator", "@content": "X3D MCP Server" }
      ]
    },
    "Scene": {
      "-children": [
        {
          "Shape": {
            "-appearance": [
              {
                "Appearance": {
                  "-material": [
                    {
                      "Material": {
                        "@diffuseColor": [1.0, 0.0, 0.0]
                      }
                    }
                  ]
                }
              }
            ],
            "-geometry": [
              {
                "Sphere": {
                  "@radius": 1.0
                }
              }
            ]
          }
        }
      ]
    }
  }
}
```

### Positioned Geometry with Transform

```xml
<Scene>
  <Transform translation='2.0 0.0 0.0' rotation='0 1 0 0.785'>
    <Shape>
      <Appearance>
        <Material diffuseColor='0.0 0.5 1.0' transparency='0.2'/>
      </Appearance>
      <Box size='1.0 2.0 0.5'/>
    </Shape>
  </Transform>
</Scene>
```

### Multiple Objects with DEF/USE

```xml
<Scene>
  <Shape DEF='SharedShape'>
    <Appearance>
      <Material DEF='BlueMat' diffuseColor='0.0 0.0 1.0'/>
    </Appearance>
    <Sphere radius='0.5'/>
  </Shape>

  <Transform translation='3.0 0.0 0.0'>
    <Shape USE='SharedShape'/>
  </Transform>
</Scene>
```

### Viewpoint and Lighting

```xml
<Scene>
  <NavigationInfo type='"EXAMINE" "ANY"' headlight='false'/>
  <Viewpoint DEF='DefaultView'
             position='0 2 10'
             orientation='1 0 0 -0.2'
             description='Default View'/>

  <DirectionalLight direction='0 -1 -1' intensity='0.8' color='1 1 1'/>
  <PointLight location='3 5 3' intensity='0.5' radius='20'/>

  <Transform translation='0 0 0'>
    <Shape>
      <Appearance>
        <Material diffuseColor='0.8 0.8 0.8' specularColor='1 1 1' shininess='0.9'/>
      </Appearance>
      <IndexedFaceSet coordIndex='0 1 2 3 -1'>
        <Coordinate point='
          -2 0 2,
           2 0 2,
           2 0 -2,
          -2 0 -2'/>
      </IndexedFaceSet>
    </Shape>
  </Transform>
</Scene>
```

### Background and Fog

```xml
<Scene>
  <Background skyColor='0.0 0.2 0.7' groundColor='0.1 0.1 0.0'/>
  <Fog color='0.8 0.8 0.8' visibilityRange='50' fogType='"LINEAR"'/>
  <!-- scene content -->
</Scene>
```

### Textured Geometry

```xml
<Shape>
  <Appearance>
    <ImageTexture url='"texture.png" "texture.jpg"'/>
    <TextureTransform scale='2 2'/>
  </Appearance>
  <Box size='2 2 2'/>
</Shape>
```

### Simple Animation with Interpolator + ROUTE

```xml
<Scene>
  <TimeSensor DEF='Clock' cycleInterval='4.0' loop='true'/>

  <OrientationInterpolator DEF='Spinner'
    key='0.0 0.5 1.0'
    keyValue='0 1 0 0, 0 1 0 3.14159, 0 1 0 6.28318'/>

  <Transform DEF='SpinTransform'>
    <Shape>
      <Appearance><Material diffuseColor='1 0.5 0'/></Appearance>
      <Box size='1 1 1'/>
    </Shape>
  </Transform>

  <ROUTE fromNode='Clock' fromField='fraction_changed'
         toNode='Spinner' toField='set_fraction'/>
  <ROUTE fromNode='Spinner' fromField='value_changed'
         toNode='SpinTransform' toField='set_rotation'/>
</Scene>
```

### PBR Material (X3D 4.0)

```xml
<Shape>
  <Appearance>
    <PhysicalMaterial
      baseColor='0.8 0.1 0.1'
      metallic='0.9'
      roughness='0.3'/>
  </Appearance>
  <Sphere radius='1.0'/>
</Shape>
```

### Inline (External Scene Reference)

```xml
<Scene>
  <Inline url='"subscene.x3d"' load='true'/>
</Scene>
```

### IndexedFaceSet (Custom Mesh)

```xml
<Shape>
  <Appearance>
    <Material diffuseColor='0.6 0.6 0.6'/>
  </Appearance>
  <IndexedFaceSet coordIndex='0 1 2 -1  2 3 0 -1' solid='false'>
    <Coordinate point='
      0 0 0,
      1 0 0,
      1 1 0,
      0 1 0'/>
    <Normal vector='0 0 1, 0 0 1, 0 0 1, 0 0 1'/>
  </IndexedFaceSet>
</Shape>
```

### Grouping with Switch

```xml
<Switch DEF='LevelSelector' whichChoice='0'>
  <!-- Choice 0: Low detail -->
  <Shape>
    <Appearance><Material diffuseColor='1 0 0'/></Appearance>
    <Sphere radius='1.0'/>
  </Shape>
  <!-- Choice 1: High detail -->
  <Shape>
    <Appearance><Material diffuseColor='0 1 0'/></Appearance>
    <IndexedFaceSet coordIndex='...'>
      <Coordinate point='...'/>
    </IndexedFaceSet>
  </Shape>
</Switch>
```

### TouchSensor Interaction

```xml
<Group>
  <TouchSensor DEF='Touch' description='Click me'/>
  <Shape DEF='ClickableBox'>
    <Appearance><Material DEF='BoxMat' diffuseColor='0.5 0.5 0.5'/></Appearance>
    <Box size='1 1 1'/>
  </Shape>
</Group>

<Script DEF='ColorChanger'>
  <field name='isActive' type='SFBool' accessType='inputOnly'/>
  <field name='newColor' type='SFColor' accessType='outputOnly'/>
</Script>

<ROUTE fromNode='Touch' fromField='isActive' toNode='ColorChanger' toField='isActive'/>
<ROUTE fromNode='ColorChanger' fromField='newColor' toNode='BoxMat' toField='set_diffuseColor'/>
```

## Example Archives (4,142+ scenes)

| Collection | Scenes | URL |
|-----------|--------|-----|
| X3D for Web Authors | 271 | https://www.web3d.org/x3d/content/examples/X3dForWebAuthors |
| X3D for Advanced Modeling | 147 | https://www.web3d.org/x3d/content/examples/X3dForAdvancedModeling |
| Basic | 745 | https://www.web3d.org/x3d/content/examples/Basic |
| ConformanceNist | 761 | https://www.web3d.org/x3d/content/examples/ConformanceNist |
| HumanoidAnimation | 192 | https://www.web3d.org/x3d/content/examples/HumanoidAnimation |
| VRML 2 Sourcebook | 416 | https://www.web3d.org/x3d/content/examples/Vrml2Sourcebook |
| Savage | 1,233 | https://www.web3d.org/x3d/content/examples/Savage |

## X3D for Advanced Modeling Categories

18 directories, 147 models covering:
- **Additive Manufacturing** — 3D printing, Rocktopus, molecular structures
- **Animation** — viewpoint sequencers, Pong, origami crane
- **Audio Spatial Sound** — W3C Web Audio API, acoustic propagation
- **Buildings** — arches, cathedral vaults, BIM
- **Conversions** — Blender, Netfabb, OpenJSCad, Tinkercad imports
- **Geometric Shapes** — Platonic solids, icosahedrons, Mobius extrusion
- **glTF Sample Models** — PBR, NPR conversions from glTF 2.0
- **Hello World Scenes** — internationalization (German, Korean, Mandarin, etc.)
- **Large Language Models** — LLM-generated X3D experiments with corrections
- **Matlab** — Simulink visualization, phased array beams
- **San Carlos Cathedral** — cultural heritage archival model
- **Scanning** — 3D scanner output, mesh reconstruction
- **Security** — XML signature, encryption, model obfuscation
- **Texture Mapping** — multitexture, volumetric texturing
- **User Experience** — interactive design patterns, event monitoring
- **Visualization** — background collections, textured environments
