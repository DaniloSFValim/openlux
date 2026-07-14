# Georeferenced public-lighting asset management with first-order installation photometric indices: the case of Niterói, Brazil

**Danilo Valim**
Independent researcher
`danilosfvalim@gmail.com`

> **Status:** working draft for submission. Park figures queried in production on
> 2026-07-11. Code and data: see *Availability* at the end.

---

## Abstract

Modernizing public lighting to LED and controlling light pollution require, beyond
an inventory of *what* is installed, a record of *how* and *where* each luminaire
operates. This paper presents a georeferenced web system for managing the public
lighting park in an urban environment in Brazil (**42,765 points, 52 neighborhoods,
39% already LED, ~5.8 MW installed**) and proposes a **first-order installation
photometric index method** combining two low-cost field attributes — the **aiming
angle** of the beam and the **ground material** (reflectance) — collected through
pre-classified options. From these, three comparable indicators are derived per
point and per area: **floor utilization** (η), **light pollution** (P) and
**relative luminance** (L). The system also provides **polygon-based spatial
analysis** on PostGIS, aggregating count, density, LED rate and the indices for any
arbitrary region. We discuss the model's explicit assumptions, its limits, and the
path toward radiometric calibration (.IES photometry and atmospheric scattering).
All source code, the database schema, and the model documentation are open and
versioned, with reproduction data provided.

**Keywords:** public lighting; LED retrofit; light pollution; photometry; pavement
reflectance; GIS; PostGIS; smart cities.

---

## 1. Introduction

Public lighting is among the largest municipal electricity loads and a direct driver
of safety, mobility and nighttime environmental quality. Replacing discharge lamps
(high-pressure sodium, metal halide) with LED promises efficiency but introduces
**glare** and **light-pollution** risks when installation is inadequate. Park
management has historically relied on inventories that record the *equipment* (power,
lamp type) but rarely the *installation condition* — angle, surroundings, illuminated
surface — precisely the variables that determine how much flux is useful and how much
escapes to the sky.

This paper reports the development and operation of a georeferenced system deployed
in an urban public lighting context and proposes a lightweight method to capture and
quantify installation condition at scale. The **contributions** are:

1. An **open, reproducible park-management system** (map, field data entry, auditing,
   indicators) on a build-free stack (SPA + PostGIS + continuous deployment),
   documented and versioned.
2. A **first-order installation photometric index method** from two pre-classified
   attributes (aiming angle and ground material), with explicit assumptions and
   normative framing.
3. A **polygon-based spatial analysis** layer restricting statistics and export to
   any drawn area, enabling per-region diagnostics.

## 2. Background and related work

Road lighting design in Brazil follows **ABNT NBR 5101** (illuminance/luminance and
uniformity), which incorporates **pavement reflectance** via surface classes (the
basis of CIE 144 R-tables). Obtrusive-light limitation is guided by **CIE 150**, which
defines ratios such as the *Upward Light Ratio* (ULR). The **BUG** classification
(*Backlight–Uplight–Glare*, IESNA TM-15) summarizes, per luminaire, backward, upward
and glare flux. These instruments are precise but require the full photometric curve
(.IES) and point-by-point calculation — impractical to apply directly to tens of
thousands of legacy installations without individual photometric surveys.

The gap addressed here is **operational**: how to capture, at scale and low cost,
enough installation information to *rank* and *prioritize* the park regarding
utilization and pollution — before and independently of a full radiometric
simulation.

## 3. Materials and Methods

### 3.1 System architecture

The application is a self-contained single-page application (framework-free HTML/JS,
Leaflet for the map), served statically (Netlify) and backed by **Supabase**
(PostgreSQL + PostGIS, role-based auth and storage). All authorization logic lives in
the database (RLS + `SECURITY DEFINER` functions), and the schema is versioned via
migrations. There is no build step, reducing maintenance surface and favoring
reproducibility.

### 3.2 Data model and park characterization

Each point (`pontos_luminaria`) stores geometry (`geom`, SRID 4326), asset type, lamp
type and power, modernization status and data provenance. The case-study park analyzed
contains **42,765 luminaires** across **52 neighborhoods**, of which **16,667 (39.0%)**
are already LED, totaling **~5,825 kW** installed. Figure 1 shows the composition by
lamp type and Figure 4 the power distribution.

![Figure 1](figures/fig1_tipo_lampada.svg)
**Figure 1.** Park composition by lamp type (n=42,765). High-pressure sodium still
dominates (49.6%), followed by LED (39.0%).

### 3.3 Installation photometric indices

Two attributes are collected via **pre-classified options** (no free text, ensuring
integrity and comparability):

- **Aiming angle** θ, measured from the **downward vertical (nadir)**: 0° = beam
  straight down (full-cutoff, ideal); 90° = horizontal; 120° = uplight. Options:
  {0, 15, 30, 45, 60, 75, 90, 120}°.
- **Ground material**, mapped to a tabulated **mean diffuse reflectance** ρ (Table 1).

**Table 1.** Mean diffuse reflectance by material (sources: CIE 144, CIE 30.2, IESNA,
ABNT NBR 5101).

| Material | ρ | Material | ρ |
|---|:--:|---|:--:|
| New asphalt (dark) | 0.07 | Bare soil | 0.20 |
| Worn asphalt | 0.12 | Vegetation/grass | 0.08 |
| Concrete/cement | 0.30 | Sand | 0.25 |
| Cobblestone/stone | 0.18 | Water | 0.06 |

Under explicit first-order assumptions — beam represented by its optical axis,
Lambertian floor reflection with a fraction f_up = 0.5 returning to the upper
hemisphere, horizontal work plane — we define:

- **Geometric floor utilization:** η = max(0, cos θ)
- **Relative surface luminance:** L = η · ρ
- **Light-pollution index (proxy 0–1):** P = min(1, (1 − η) + ρ · η · f_up)

The first term of P is the fraction of flux **not** reaching the floor (lost
laterally/upward as glare and direct skyglow); the second is the **reflected** share
returning to the sky — so brighter surfaces (concrete, sand) raise reflected
pollution while improving perception (L). Figure 3 shows the monotonic behavior of η
and P with θ.

![Figure 3](figures/fig3_modelo_fotometrico.svg)
**Figure 3.** Indices vs. angle (concrete floor, ρ=0.30). η decreases from 1 (nadir)
to 0 (horizontal); P rises complementarily, crossing near 57°.

### 3.4 Polygon-based spatial analysis

Two PostGIS functions (`ip_pontos_poligono`, `ip_stats_poligono`) take a GeoJSON
polygon and, via a bounding-box prefilter (GIST index) followed by `ST_Contains`,
return the points and statistics **restricted to the area**: total, area (km²),
density (points/km²), LED rate, installed power, composition by type, and the mean
photometric indices. This enables diagnostics and export for any arbitrary region,
not only per neighborhood or map viewport.

### 3.5 Reproducibility

The schema is versioned via migrations mirrored in the repository; CI pipelines run
API tests (Newman), E2E (Playwright), performance auditing (Lighthouse) and security
scanning. The figures in this paper are listed in
`paper/data/parque_stats_2026-07-11.csv` and generated by a deterministic script
(`paper/figures/gen_figures.py`).

## 4. Results

### 4.1 Characterization and heterogeneity

The park mixes a still discharge-dominated base (sodium 49.6%, metal halide 10.4%)
with 39.0% LED (Figure 1). The power distribution (Figure 4) concentrates in the
70–99 W (14,819) and 150–249 W (10,723) bands, reflecting the coexistence of modern
LED road lighting and higher-load sodium fixtures.

![Figure 4](figures/fig4_potencia_dist.svg)
**Figure 4.** Installed power distribution per luminaire.

Modernization is **spatially heterogeneous** (Figure 2): among the fifteen largest
neighborhoods, the LED rate ranges from 0.2% (Engenho do Mato) and 0.8% (Serra
Grande) to 70.9% (Centro) and 63.8% (Cantagalo), against the 39% park average — a
signature of concentrated retrofit fronts and still-pending peripheral areas.

![Figure 2](figures/fig2_pct_led_bairro.svg)
**Figure 2.** LED rate in the 15 largest neighborhoods; dashed line = park average
(39%).

### 4.2 Model behavior

The model (Figure 3) reproduces the expected qualitative physics: utilization is
maximal at nadir aiming and zero at horizontal; pollution grows monotonically with
tilt and is amplified by higher-reflectance materials. For concrete (ρ=0.30), P ranges
from 0.15 (nadir) to 1.0 (horizontal/uplight); for new asphalt (ρ=0.07), P at nadir
drops to 0.035 — highlighting the trade-off between perception (bright materials help
L) and reflected pollution.

### 4.3 Area analysis example

A polygon selection over the Centro/Icaraí region (~10.2 km²) returned 6,497
luminaires, a density of 635 points/km², 57.5% LED and 1,209 kW installed — within
seconds, over the spatial index. The same feature restricts export (CSV/GeoJSON) to
the area, supporting localized studies.

## 5. Discussion

The method is deliberately a **first-order geometric proxy**: it assumes a narrow
beam, purely diffuse reflection and a transparent atmosphere. It replaces neither
radiometric simulation nor NBR 5101 for design. Its value lies in **ranking and
prioritizing** a large park with cheap, comparable data — e.g., flagging
high-aiming-angle installations (high P) for inspection, or estimating the effect of
changing surroundings/geometry before a full photometric survey. The assumptions are
stated so the indices are read as *relative indicators*, not absolute quantities (lux,
cd/m²).

A notable limitation is **water**, whose specular reflection at grazing angles is
underestimated by the diffuse model. Another is dependence on field-classification
quality; hence collection uses closed options validated by database constraints
(`CHECK` on angle, foreign key on material).

## 6. Conclusion and future work

We presented an open management system for the Niterói lighting park and a lightweight
method to quantify installation condition, integrating inventory data, first-order
photometric indicators and polygon-based spatial analysis. Next steps (Phase 3) are:
(i) integrate the **.IES photometric curve** already stored in the model catalog; (ii)
model **specular** reflection for water bodies; (iii) incorporate **atmospheric
scattering by particulates (PM2.5)** from air-quality series, correcting useful
efficacy and skyglow; and (iv) **calibrate** the indices to absolute quantities (lux,
ULR) per CIE 150.

## Availability of data and code

Source code, migrations and model documentation:
<https://github.com/DaniloSFValim/openlux> (MIT license). Reproduction
data in `paper/data/`. Once archived, cite via the Zenodo DOI (see
`docs/INTELLECTUAL_PROPERTY.md`).

## References

See `paper/references.bib`.
