# Example 3: Doha, Qatar from Google APIs

Building a real-world 3D city scene by combining the x3d-mcp server with Google Maps APIs. This example was created for the Web3D 2026 Conference in Doha.

## Data Sources

1. **Google Elevation API** -- 12x12 grid of real terrain heights across Doha (144 points, ~6.6km x 6.6km)
2. **Google Places API** -- landmark locations and West Bay skyscraper positions with names
3. **Google 3D Tiles API** -- confirmed available for Doha at `https://tile.googleapis.com/v1/3dtiles/root.json` (GLB format tiles)

## Chat

**User:** Create a 3D scene of Doha, Qatar using real data from Google APIs.

**Model:** I'll fetch elevation data and building locations, then generate the X3D scene.

### Step 1: Fetch terrain

**Model runs:** Google Elevation API for 144 points centered on 25.2854, 51.5310
```
GET https://maps.googleapis.com/maps/api/elevation/json
  ?locations=25.2554,51.5010|25.2554,51.5065|...(144 points)
  &key=GOOGLE_API_KEY
```
**Response:** 144 elevation values, range -3.45m to 18.97m (Doha is flat coastal terrain)

### Step 2: Fetch landmarks and buildings

**Model runs:** Google Places API text search
```
POST https://places.googleapis.com/v1/places:searchText
Body: {"textQuery": "landmarks in Doha Qatar", "maxResultCount": 10, ...}

POST https://places.googleapis.com/v1/places:searchText
Body: {"textQuery": "skyscrapers towers buildings West Bay Doha Qatar", ...}
```
**Response:**
- Landmarks: Pearl Monument, Souq Waqif, Sword Gate Monument, Corniche Viewpoint
- West Bay towers: Doha Tower (238m), Forty Four Tower (170m), Excellence Tower (150m), The Residence (140m), Laffan Tower (130m), Darwish Tower (120m), City Tower (110m), Beverly Hills Tower (100m)

### Step 3: Generate X3D

**Model calls** `validate_x3d` on the generated scene:
```json
{"valid": true, "errors": []}
```

The scene uses:
- `ElevationGrid` with real heights from the Elevation API for terrain
- `Box` geometry for West Bay skyscrapers, positioned at real lat/lon converted to X3D coordinates, heights proportional to actual building heights
- `Cylinder` geometry for landmarks
- `Box` with transparency for Doha Bay water
- 3 viewpoints: aerial, West Bay skyline, Corniche waterfront
- Directional sun + fill lighting

### Coordinate mapping

Lat/lon to X3D:
```
x = (lon - 51.5310) * 111000 * cos(25.2854 deg) / 100
z = -(lat - 25.2854) * 111000 / 100
y = elevation / 100
```

## What this demonstrates

- MCP tools generate valid X3D from real geospatial data
- Google Elevation API provides terrain for ElevationGrid
- Google Places API provides building positions and names for DEF'd geometry
- Google 3D Tiles API root tileset is accessible for Doha (GLB mesh tiles)
- The pipeline: API data -> coordinate transform -> X3D scene graph -> XSD validation

## Available Google APIs for 3D city generation

| API | Data | X3D Use |
|-----|------|---------|
| Elevation API | Terrain heights at any lat/lon | ElevationGrid, IndexedFaceSet terrain |
| Places API | Building names, locations, types | Positioned geometry with DEF names |
| 3D Tiles API | Photorealistic mesh tiles (GLB) | Source for detailed building geometry |
| Geocoding API | Address to lat/lon | Scene positioning |
| Street View API | Panoramic imagery | ImageTexture on geometry |

## Scene file

[scenes/doha_qatar.x3d](scenes/doha_qatar.x3d)
