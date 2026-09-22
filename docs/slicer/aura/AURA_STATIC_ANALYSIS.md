# Aura Static Analysis

## Evidence boundary

Legacy Aura material in this report is `ANISOPRINT_OFFICIAL` historical and
comparative evidence. It is not FibreSeek operating guidance. No installer or
bundled executable was launched. All findings came from package metadata,
archive extraction, read-only SQLite queries, JSON/XML inspection, and strings
already present in public first-party artifacts.

## Corpus

| Record | Package | Bytes | SHA-256 | Container | Static result |
|---|---|---:|---|---|---|
| AP-103 | Aura 2.5.8 Stable x64 | 117,751,117 | `8d1670b20a9a07287f11f8dab7b793796a793632b9f1333dbcf0185e89bf2828` | PE32 Inno Setup 6.3.0 | 101 files; package integrity test passed |
| AP-104 | Aura 2.6.2 x64 | 139,036,800 | `7534d390e6456b78d1538c2ac184c12293a80e7e69f9d3e9d6cd7f5441b900f8` | PE32 Inno Setup 6.4.3 | 213 files; package integrity test passed |
| AP-105 | Aura 2.6.1 Sk3 template preview x64 | 143,686,752 | `ec0d16cfa98be38c3ac748bf4452aa7965ba2ac6e851f49fa189d0a2ead4888f` | PE32 Inno Setup 6.3.0 | 190 files; package integrity test passed |

**FACT:** AP-102 is the official Anisoprint downloads page. It labels 2.5.8
“Stable,” lists 2.6.1 Beta and the 2.6.1 Sk3 preview separately, and presents
2.6.2 as the current download. The AP-104 response names its payload
`AuraSetup_2.6.2_beta.exe`, so the page label and server filename are both
retained rather than reconciled by assumption.

**FACT:** the Anisoprint support/docs hosts served an expired TLS certificate at
retrieval. AP-101 records the failed verified-TLS attempt. AP-102–AP-113 were
then acquired with verification explicitly disabled and this condition recorded
in every retrieval note. No credentials or protected endpoint were used.

## Signing metadata

| Package | Embedded Authenticode data |
|---|---|
| Aura 2.5.8 | No PE certificate table in the outer installer |
| Aura 2.6.2 | PKCS#7 signer subject `Shenzhen Fibreseek Technology Limited Company`; GlobalSign EV CodeSigning chain; signer certificate valid 2025-09-09 through 2026-09-10 |
| Aura 2.6.1 Sk3 preview | Same Fibreseek signer subject and certificate validity as AP-104 |

**FACT:** the signer names above are embedded certificate metadata. This phase
did not establish Windows trust-chain status or execute Windows signature APIs.

**INFERENCE:** FibreSeek signing two packages distributed from Anisoprint's
official Aura portal is strong organizational and build-lineage evidence. It
does not make their parameter values current FibreSeek guidance.

## Application architecture

- **FACT:** all three packages are x64 Windows desktop applications with Aura
  GUI and CLI entry points, slicing/settings libraries, SQLite support, and
  first-party templates.
- **FACT:** 2.5.8 and the 2.6.1 Sk3 preview target .NET Framework 4.7.2. Aura
  2.6.2 is a .NET 8 Windows Desktop application.
- **FACT:** each package contains `Aura.CLI`, `SettingsDB`, `SettingsJson`,
  slicing-engine libraries, `cli-inputfile.schema.json`, the settings library
  `Anisoprint.ausettings`, and 18 public `.auprojx` sample projects.
- **FACT:** 2.6.2 adds a larger modern dependency set, including IFC/PDF/image
  libraries and .NET runtime/dependency manifests.

No executable code was decompiled or run. The bounded extraction retained only
the settings database, CLI schema, public sample projects, file inventories,
SQLite inventories, package-signature metadata, and hashes on the NAS.

## Settings stores

`Anisoprint.ausettings` is an ordinary SQLite database in every package.

| Package | SQLite `user_version` | Rows: printer / plastic / composite / profile | Principal tables |
|---|---:|---:|---|
| 2.5.8 | 14 | 4 / 14 / 25 / 39 | `Printer`, `ExtruderP`, `ExtruderC`, `Plastic`, `Composite`, `Profile`, `ProfileMaterial`, `Slots`, `SlotExtruderMaterial`, `Session`, `RecentProject` |
| 2.6.2 | 17 | 5 / 15 / 26 / 40 | Same 11-table entity model |
| 2.6.1 Sk3 preview | 19 | 1 / 1 / 1 / 2 | Same 11-table entity model, reduced to Sk3 preview records |

**FACT:** settings entities use 32-hex-character GUID primary keys and store a
base column plus an `Over` override column for nearly every configurable value.
Profiles are related to plastics/composites through `ProfileMaterial`; printer
slots are related to extruders/materials through `SlotExtruderMaterial`.

**FACT:** profile schema width grows from 322 columns in 2.5.8 to 324 in 2.6.2
and 338 in the Sk3 preview. Aura 2.6.x splits the earlier combined top/bottom
solid-layer field. The Sk3 preview also carries tree-support and wipe-tower
fields. This is schema evolution, not evidence that all fields are active for
FibreSeeker.

## Seeker records in Aura

Aura 2.5.8 has no Seeker printer. Both later official packages contain Seeker
data with IDs that survive into Rocket.

| Entity | Stable legacy ID | Aura 2.6.2 | Aura 2.6.1 Sk3 preview |
|---|---|---|---|
| Printer | `83bf10398c9e49fc928f2f94a2008d40` | `Seeker-3`, 305×300×245 | `SEEKER 3`, 305×305×245 |
| CFC extruder | `f3904c6fc24e4affad9a70405cc4df84` | cut 60; restart 56; code comment 55 | cut 60; restart 56; code comment 55 |
| FFF extruder | `9fb4b169bf0f4436833e6afdfaeeeb90` | 0.4 mm | 0.4 mm |
| X-CCF composite | `2af8ac624968436488e31045ef47feba` | absent; placeholder Sk3 composite has a different ID and CBF data | `SK3_X-CCF1K+CFC PETG` |
| X-CCF profile | `d294a2dc9d7f460aacf4dc50b656d44a` | absent | `SK3_CCF 1K+PETG_PETG` |

**FACT:** the 2.6.2 record named `SK3-CCF1K +PLA` contains CBF/Basalt and
Anisoprint values. Its label and content conflict. It is excluded from any
FibreSeek material recommendation.

## Official semantics recovered

From AP-107 and AP-110:

- **FACT:** Aura documents `CutDistance` in mm as the distance from cutter to
  nozzle outlet, and `FiberRestartLength` in mm as the fiber fed during restart.
- **FACT:** Aura documents fiber extrusion speed in mm/s and linear density in
  tex (g/km).
- **FACT:** Aura documents reinforced-perimeter fiber feedrate as percent of
  presumed path length.
- **FACT:** Aura maps fiber infill enum `0` to solid, `1` to cellular rhombic,
  `2` to cellular isogrid, and `3` to cellular anisogrid.
- **FACT:** the archived changelog says Tetragrid was added in 2.3.2, but neither
  the CLI page nor recovered CLI schema assigns it a numeric enum value.
- **FACT:** the changelog defines slot roles as plastic, composite, or universal.
  Stored Composer/Seeker rows support numeric `0 = plastic` and `1 = composite`.
  A numeric universal-slot mapping was not established.

These are Aura meanings. Their relevance to Rocket is classified in
`AURA_ROCKET_FIELD_MAP.md` and never promoted automatically.

## Archive locations

- Originals: `<archive>/FibreSeeker-KB-Archive/originals/ANISOPRINT_OFFICIAL/AP-102` through `AP-113`
- Static extracts: `<archive>/FibreSeeker-KB-Archive/derived/extracted/AP-103` through `AP-105`
- Derived web text: `<archive>/FibreSeeker-KB-Archive/derived/text/AP-102` and `AP-106` through `AP-113`

## Open questions

- **OPEN QUESTION:** whether Aura 2.6.2 or the numerically older Sk3 preview is
  the direct template source used to build Rocket; Rocket appears to combine
  records from both branches.
- **OPEN QUESTION:** runtime precedence among structured cut values and the
  human-readable cut-code comment.
- **OPEN QUESTION:** the unit of `FiberSpoolLength`; no first-party label was
  recovered.
- **OPEN QUESTION:** numeric Tetragrid, profile-status, and any universal-slot
  enum values not directly documented by the bounded corpus.
