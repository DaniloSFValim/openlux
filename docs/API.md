# API Reference — OpenLux RPC Functions

**Base URL:** `https://[project-id].supabase.co/rest/v1/rpc/`  
**Auth:** All requests require `Authorization: Bearer [ANON_KEY]` header  
**Format:** JSON (POST requests with JSON body)

---

## 📍 Read Functions (Public)

### `ip_pontos_bbox`
Fetch points within a geographic bounding box.

**Parameters:**
- `p_bbox_south` (float): Latitude min
- `p_bbox_west` (float): Longitude min
- `p_bbox_north` (float): Latitude max
- `p_bbox_east` (float): Longitude max
- `p_zoom` (integer): Zoom level (determines detail level)

**Returns:** Array of point objects with geometry, asset type, lamp type, modernization status.

**Examples:**

```javascript
// JavaScript
const { data, error } = await sb.rpc('ip_pontos_bbox', {
  p_bbox_south: -23.05,
  p_bbox_west: -43.20,
  p_bbox_north: -22.80,
  p_bbox_east: -42.90,
  p_zoom: 14
});
if (error) console.error(error);
else console.log(`Fetched ${data.length} points`);
```

```bash
# cURL
curl -X POST "https://lrnmydrwzxxajylsmoih.supabase.co/rest/v1/rpc/ip_pontos_bbox" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "p_bbox_south": -23.05,
    "p_bbox_west": -43.20,
    "p_bbox_north": -22.80,
    "p_bbox_east": -42.90,
    "p_zoom": 14
  }'
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "codigo_seconser": "LM-12345",
    "latitude": -22.905,
    "longitude": -43.055,
    "tipo_ativo": "luminaria",
    "tipo_luminaria": "viaria",
    "tipo_lampada": "led",
    "potencia": 150,
    "modernizado_led": true,
    "bairro_nome": "Icaraí",
    "status": "ok",
    ...
  },
  ...
]
```

---

### `ip_clusters_grid`
Fetch aggregated cluster statistics for viewport (used at low zoom levels).

**Parameters:**
- `p_bbox_south`, `p_bbox_west`, `p_bbox_north`, `p_bbox_east` (float): Bounding box
- `p_zoom` (integer): Zoom level
- `p_grid_size` (integer): Cell size in pixels (default 256)

**Returns:** Grid of clusters with count, LED rate, average power per cell.

**Example:**
```javascript
const { data } = await sb.rpc('ip_clusters_grid', {
  p_bbox_south: -23.05,
  p_bbox_west: -43.20,
  p_bbox_north: -22.80,
  p_bbox_east: -42.90,
  p_zoom: 12,
  p_grid_size: 256
});
// Returns: [{lat, lng, count, led_count, avg_power}, ...]
```

---

### `ip_pontos_poligono`
Fetch points inside a drawn polygon (GeoJSON).

**Parameters:**
- `p_geojson` (object): GeoJSON Feature Collection with Polygon geometry
- `p_limite` (integer): Max points to return (default 5000)

**Returns:** Array of points within polygon.

**Example:**
```javascript
const polygon = {
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-43.20, -23.05],
      [-42.90, -23.05],
      [-42.90, -22.80],
      [-43.20, -22.80],
      [-43.20, -23.05]
    ]]
  }
};
const { data } = await sb.rpc('ip_pontos_poligono', {
  p_geojson: polygon,
  p_limite: 5000
});
```

---

### `ip_stats_poligono`
Get aggregated statistics for a polygon region.

**Parameters:**
- `p_geojson` (object): GeoJSON Polygon

**Returns:** Statistics object: total count, LED %, average power, area (km²), density (points/km²), photometric indices.

**Example:**
```javascript
const { data } = await sb.rpc('ip_stats_poligono', {
  p_geojson: polygon
});
// Returns: {
//   total: 150,
//   led_count: 60,
//   led_percent: 40,
//   avg_power: 175,
//   area_km2: 0.85,
//   density: 176.5,
//   avg_eta: 0.82,
//   avg_pollution: 0.28,
//   avg_luminance: 0.25
// }
```

---

### `ip_estadisticas`
Global park statistics.

**Parameters:** None

**Returns:** Totals: point count, LED count, power, by neighborhood, by lamp type.

**Example:**
```javascript
const { data } = await sb.rpc('ip_estadisticas');
// Returns: {
//   total_pontos: 42765,
//   led_instalado: 16667,
//   potencia_total_kw: 5825,
//   bairros: [{nome, count, led}, ...],
//   tipos_lampada: [{tipo, count}, ...]
// }
```

---

### `ip_bairro_geojson`
Fetch neighborhood boundaries as GeoJSON (for choropleth maps).

**Parameters:** None

**Returns:** GeoJSON FeatureCollection with neighborhood polygons + properties (LED %, density).

---

### `ip_historico_ponto`
Fetch edit history for a point (audit trail).

**Parameters:**
- `p_id` (uuid): Point ID

**Returns:** Array of historical records: who, when, what changed.

**Example:**
```javascript
const { data } = await sb.rpc('ip_historico_ponto', {
  p_id: '550e8400-e29b-41d4-a716-446655440000'
});
// Returns: [
//   {criado_em: '2026-07-10T14:30:00Z', editor: 'user@example.com', mudanca: 'Potência: 150W → 200W'},
//   ...
// ]
```

---

### `ip_listar_modelos`
Fetch equipment model catalog.

**Parameters:** None

**Returns:** Array of models: manufacturer, model name, power, Tier 2 specs (lumens, efficiency, etc).

---

### `ip_listar_campanhas`
Fetch census campaigns (field survey campaigns).

**Parameters:** None

**Returns:** Array of campaigns: name, date, status (active/closed), verified points count.

---

## ✏️ Write Functions (Requires Authentication)

### `ip_inserir_ponto`
Create a new point.

**Parameters:**
- `p_lat` (float): Latitude
- `p_lng` (float): Longitude
- `p_tipo_ativo` (enum): "luminaria" | "poste" | "caixa" | "braço"
- `p_tipo_luminaria` (enum, if luminaria): "viaria" | "globo" | etc
- `p_tipo_lampada` (enum): "led" | "vapor_sodio" | "metalico" | ...
- `p_potencia` (integer): Power in watts
- `p_status` (enum): "ok" | "pendente" | "sem_lampada"
- `p_fonte` (enum): "levantamento_campo" | "ponto_original_kml" | "estimado" | "censo_enel"
- `p_requer_aprovacao` (boolean): If true, goes to approval queue
- `p_angulo_inclinacao_graus` (integer, optional): Tier 3 aiming angle (0-120°)
- `p_material_piso` (enum, optional): Tier 3 ground material

**Returns:** Created point object with new ID.

**Example:**
```javascript
const { data, error } = await sb.rpc('ip_inserir_ponto', {
  p_lat: -22.905,
  p_lng: -43.055,
  p_tipo_ativo: 'luminaria',
  p_tipo_luminaria: 'viaria',
  p_tipo_lampada: 'led',
  p_potencia: 150,
  p_status: 'ok',
  p_fonte: 'levantamento_campo',
  p_requer_aprovacao: false,
  p_angulo_inclinacao_graus: 30,
  p_material_piso: 'concreto'
});
if (error) console.error('Failed to create point:', error.message);
else console.log('Point created:', data.id);
```

**Permissions:** Requires `editor` or `admin` role.

---

### `ip_atualizar_ponto`
Update an existing point.

**Parameters:**
- `p_id` (uuid): Point ID to update
- `p_lat`, `p_lng`, `p_tipo_*`, `p_potencia`, `p_status`, `p_angulo_inclinacao_graus`, `p_material_piso`: Same as insert (only pass fields to update)

**Returns:** Updated point object.

**Example:**
```javascript
const { data, error } = await sb.rpc('ip_atualizar_ponto', {
  p_id: '550e8400-e29b-41d4-a716-446655440000',
  p_potencia: 200,
  p_status: 'ok',
  p_angulo_inclinacao_graus: 45
});
```

**Permissions:** Requires `editor` or `admin` role (for own edits or if admin).

---

### `ip_remover_ponto`
Delete a point.

**Parameters:**
- `p_id` (uuid): Point ID

**Returns:** Confirmation.

**Permissions:** Requires `admin` role only.

---

### `ip_criar_modelo`
Add equipment model to catalog.

**Parameters:**
- `p_fabricante` (text): Manufacturer name
- `p_modelo` (text): Model name
- `p_potencia` (integer): Power (W)
- `p_temperatura` (integer, optional): Color temp (K)
- `p_tensao` (text, optional): "110" | "220" | "110/220"
- `p_ip` (text, optional): IP rating
- `p_classe_nbr` (text, optional): NBR class
- `p_tipo_lampada` (enum): Lamp type
- `p_fluxo_luminoso_lm` (integer, optional): Tier 2 lumens
- `p_eficacia_lm_w` (numeric, optional): Tier 2 efficiency
- `p_fator_potencia` (numeric, optional): Power factor (0.90-1.0)
- `p_thd_percentual` (numeric, optional): THD %
- `p_grau_ik` (text, optional): IK rating
- `p_tipo_conectividade` (text, optional): Connectivity type
- `p_arquivo_ies_url` (text, optional): .IES photometry file URL

**Permissions:** Requires `editor` or `admin` role.

---

### `ip_criar_campanha`
Start a new census campaign (field survey).

**Parameters:**
- `p_nome` (text): Campaign name
- `p_descricao` (text, optional): Description

**Returns:** Campaign object with ID and status.

**Example:**
```javascript
const { data } = await sb.rpc('ip_criar_campanha', {
  p_nome: 'Recenseamento Icaraí 2026-07',
  p_descricao: 'Field survey for Icaraí neighborhood'
});
```

**Permissions:** Requires `admin` role.

---

### `ip_confirmar_ponto`
Mark a point as verified during an active campaign.

**Parameters:**
- `p_id` (uuid): Point ID
- `p_campanha_id` (uuid): Campaign ID

**Returns:** Updated point with verification timestamp.

**Permissions:** Requires `editor` or `admin` role.

---

### `ip_encerrar_campanha`
Close a campaign.

**Parameters:**
- `p_campanha_id` (uuid): Campaign ID

**Returns:** Campaign status = "closed".

**Permissions:** Requires `admin` role.

---

### `ip_registrar_intervencao`
Log a maintenance intervention on a point.

**Parameters:**
- `p_id` (uuid): Point ID
- `p_tipo_intervencao` (enum): "troca_lampada" | "limpeza" | "troca_luminaria" | etc
- `p_observacoes` (text, optional): Notes

**Returns:** Intervention record with timestamp.

---

## 🔍 Filter & Aggregation Functions

### `ip_grid_densidade`
Density heatmap grid.

**Parameters:** Same as `ip_clusters_grid` (bbox + zoom).

**Returns:** Grid cells with point density (points/km²).

---

### `ip_serie_metricas`
Time series of park metrics (historical trends).

**Parameters:**
- `p_periodo_dias` (integer): Days back (e.g., 90)

**Returns:** Array of daily snapshots: {data, total_pontos, led_count, avg_power, ...}

---

## 🔐 Security Notes

- **Public queries** (read): Use anon key; no login required.
- **Private queries** (write): Require authenticated session + appropriate role (editor/admin).
- **RLS policies** enforce row-level access:
  - `leitura`: Read-only all data
  - `editor`: Create/edit own points; read all
  - `admin`: Full access

---

## 🚨 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `42P01: relation "pontos_luminaria" does not exist` | Schema not deployed | Run `supabase db push` |
| `PGRST102: The rpc... does not exist` | Typo in RPC name | Check function exists: `supabase db list functions` |
| `42501: permission denied for function` | Insufficient role | Verify user role in `profiles.role` |
| `42P22: malformed geometry` | Invalid lat/lng | Ensure lat ∈ [-90, 90], lng ∈ [-180, 180] |

---

## 📚 See Also

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) — Setting up your own instance
- [FIELD_REFERENCE_TIER3_PHOTOMETRY.md](FIELD_REFERENCE_TIER3_PHOTOMETRY.md) — Photometry model
- [supabase/README.md](../supabase/README.md) — Local development
