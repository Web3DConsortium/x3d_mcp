export const SAMPLE_SCENE = `<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Full" version="4.1">
  <head>
    <meta name="title" content="x3d_mcp Studio — Observatory"/>
    <meta name="description" content="Competition preview scene"/>
  </head>
  <Scene>
    <WorldInfo title="x3d_mcp Studio Observatory"/>
    <NavigationInfo type='"EXAMINE" "ANY"' headlight="false"/>
    <Background skyColor="0.018 0.027 0.055, 0.045 0.071 0.12" skyAngle="1.35"/>
    <Viewpoint DEF="HeroView" description="Studio overview" position="6 4.3 10.5" orientation="-0.39 0.9 0.19 0.59" centerOfRotation="0 0.7 0" fieldOfView="0.62"/>
    <DirectionalLight direction="-0.5 -1 -0.7" color="0.82 0.92 1" intensity="0.9"/>
    <PointLight location="-4 4 4" color="0.2 0.85 1" intensity="0.7" radius="15"/>
    <PointLight location="4 2 -1" color="0.62 0.36 1" intensity="0.55" radius="12"/>

    <Transform translation="0 -1.18 0">
      <Shape>
        <Appearance><Material diffuseColor="0.035 0.055 0.085" specularColor="0.18 0.26 0.4" shininess="0.45"/></Appearance>
        <Box size="10 0.12 7"/>
      </Shape>
    </Transform>

    <Transform translation="0 0.65 0">
      <Shape DEF="CoreShape">
        <Appearance><Material diffuseColor="0.08 0.72 0.9" emissiveColor="0.01 0.12 0.18" specularColor="0.8 0.96 1" shininess="0.78"/></Appearance>
        <Sphere radius="1.42"/>
      </Shape>
    </Transform>
    <Transform translation="0 0.65 0" rotation="1 0 0 0.28">
      <Shape>
        <Appearance><Material diffuseColor="0.43 0.25 0.92" emissiveColor="0.05 0.015 0.12" specularColor="0.9 0.82 1" shininess="0.9" transparency="0.67"/></Appearance>
        <Cylinder radius="1.9" height="0.05"/>
      </Shape>
    </Transform>

    <Transform translation="-3 -0.15 0.35" rotation="0 1 0 0.45">
      <Shape>
        <Appearance><Material diffuseColor="0.26 0.92 0.67" specularColor="0.8 1 0.9" shininess="0.65"/></Appearance>
        <Box size="1.45 1.45 1.45"/>
      </Shape>
    </Transform>
    <Transform translation="3 -0.15 0.35" rotation="0 0 1 -0.12">
      <Shape>
        <Appearance><Material diffuseColor="1 0.55 0.2" specularColor="1 0.86 0.58" shininess="0.72"/></Appearance>
        <Cone bottomRadius="0.95" height="2.1"/>
      </Shape>
    </Transform>

    <Transform translation="0 -1.02 0">
      <Shape>
        <Appearance><Material diffuseColor="0.11 0.15 0.22" emissiveColor="0.02 0.03 0.05" transparency="0.08"/></Appearance>
        <Cylinder radius="2.65" height="0.24"/>
      </Shape>
    </Transform>
  </Scene>
</X3D>`;
