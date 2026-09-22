# FibreSeek Materials and Compatibility

## Feedstock construction

- **FACT (FS-120):** X-CCF is continuous carbon-fiber filament impregnated with
  thermoset resin at approximately 60% fiber volume.
- **OPEN QUESTION:** FibreSeek does not state the thermoset chemistry, tow count,
  sizing, or whether the store label “1K” is a complete construction specification.
- **FACT (FS-120):** X-CGF is listed as a supported continuous reinforcement.
- **FACT (FS-125):** current software represents X-CCF with fiber diameter 0.25
  mm and linear density 102, and X-CGF with diameter 0.35 mm and linear density 170.
- **OPEN QUESTION (FibreSeek-only evidence):** FibreSeek material does not label
  the linear-density unit. Phase 1B found high-confidence historical lineage to
  Aura's `LinearDensity` field, which Aura defines as tex, but this remains
  `ANISOPRINT_OFFICIAL` comparative evidence rather than FibreSeek guidance.

## Current software definitions

These are **FACTS from current FibreSeek preset v15 (FS-125)**. They establish
available first-party profile definitions, not blanket approval for arbitrary
brands or substitutions.

| CFC definition | Matrix | Reinforcement | CFC nozzle | Bed | Stored fiber speed |
|---|---|---|---:|---:|---:|
| CFC PLA + X-CCF | PLA | X-CCF | 230°C | 55°C | 25 |
| CFC PETG + X-CCF | PETG | X-CCF | 270°C | 75°C | 25 |
| CFC PETG + X-CGF | PETG | X-CGF | 270°C | 75°C | 20 |
| CFC PA + X-CCF | PA | X-CCF | 270°C | 80°C | 15 |

| FFF definition | Nozzle | Bed | Stored extrusion speed |
|---|---:|---:|---:|
| PLA | 220°C | 55°C | 15 |
| PETG | 250°C | 75°C | 15 |
| PET GF | 300°C | 75°C | 15 |
| PA CF / PACF | 270°C | 80°C | 15 |
| PPS CF | 330°C | 120°C | 10 |

- **OPEN QUESTION (FibreSeek-only evidence):** speed units are not labeled by
  the Rocket preset schema. Aura's exact ancestor composite defines its stored
  fiber extrusion speed in mm/s; continuity is documented separately as an
  inference in `docs/slicer/aura/AURA_ROCKET_LINEAGE.md`.
- **OPEN QUESTION:** the store contains duplicate/variant records and one
  `PPS CF`/`PPS GF20` naming inconsistency that requires vendor clarification.
- **FACT (FS-113, FS-114):** the public store currently exposes X-CCF 1K (500 m)
  and a two-piece CFC hotend kit. No X-CGF store product was exposed.

## Compatibility boundary

- **FACT (FS-120):** the manual gives PLA, PETG, and PA as CFC plastic examples.
- **FACT (FS-125):** the four matrix/reinforcement combinations above have
  current first-party profile groups.
- **OPEN QUESTION:** no separate first-party compatibility matrix, approved
  brand list, SDS, or material data sheet was found.
- **PARTIAL RESOLUTION (Phase 2F-B):** profile availability plus manual examples
  directly support the four named matrix/reinforcement definitions as current
  first-party software scope, but not as a blanket material-brand qualification.
- **FACT (FS-120):** long-term materials are to be removed and sealed. The
  manual names PETG, PC, and PACF as highly hygroscopic and calls for drying
  before each print plus sealed storage during printing.
- **OPEN QUESTION:** no material-specific drying temperature/duration/moisture
  limit or X-CCF heated-drying permission was recovered.
- **BOUNDARY:** Anisoprint CCF/CFC material guidance is not incorporated here and
  must not be presented as FibreSeek-specific guidance without explicit evidence.
