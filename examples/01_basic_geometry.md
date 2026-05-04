# Example 1: Basic Geometry with create_geometry

Single MCP tool call to generate a shape with material.

## Chat

**User:** Make me a red sphere.

**Model calls** `create_geometry`:
```json
{
  "shape": "sphere",
  "color": [0.9, 0.1, 0.1],
  "size": [1.5]
}
```

**MCP response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 4.0//EN"
  "https://www.web3d.org/specifications/x3d-4.0.dtd">
<X3D profile='Interchange' version='4.0'>
  <Scene>
    <Shape>
      <Appearance>
        <Material diffuseColor='0.9 0.1 0.1'/>
      </Appearance>
      <Sphere radius='1.5'/>
    </Shape>
  </Scene>
</X3D>
```

**Model calls** `validate_x3d` on the output:
```json
{"valid": true, "errors": []}
```

**Model:** Red sphere, radius 1.5, valid X3D 4.0 Interchange profile.

## What this demonstrates

- `create_geometry` produces a complete, valid X3D document from a single call
- The model specifies shape type, RGB color, and size parameters
- Output includes proper DOCTYPE, profile, and version headers
- Validation confirms XSD compliance

## Scene file

[scenes/red_sphere.x3d](scenes/red_sphere.x3d)
