# Rocket Static Analysis

## Scope and method

This report covers the official Rocket packages retrieved on 2026-08-14. The
packages were hashed, signature metadata was inspected, and their containers
were extracted statically. Rocket and bundled executables were never launched.
No authentication, licensing, encryption, DRM, or protected remote service was
bypassed.

Labels used below:

- **FACT:** directly observed in first-party packages or first-party endpoints.
- **INFERENCE:** interpretation of observed data that is not manufacturer documentation.
- **OPEN QUESTION:** evidence is absent, ambiguous, or internally inconsistent.

## Package record

| Platform | Manifest ID | Package | Size | SHA-256 | Container |
|---|---|---|---:|---|---|
| Windows x64 | FS-121 | `RocketSlicer-win-x64-Setup.exe` | 322,744,816 B | `2d849eeb788faaee9dd4dcc127ff787e89ade862d94f077502301ba7f96ba642` | PE32 NSIS 3 Unicode installer containing `app-64.zip` |
| macOS Apple Silicon | FS-122 | `RocketSlicer-mac-arm64.dmg` | 315,784,558 B | `ee76209d5f54e2c5d5f6be06ee2408e0bfae46ba56a4dfd17242e7b9e0de352c` | Read-only compressed UDIF/APFS disk image |

**FACT:** both distributions identify Rocket as version `1.3.2`. The frontend
build is `1868`; the backend identifies itself as `1.3.1.480`. The macOS bundle
build is `637` and requires macOS 12 or later.

## Signing and notarization

### Windows

- **FACT:** the installer and embedded main executable each contain an
  Authenticode `WIN_CERTIFICATE` PKCS#7 signature block of 11,384 bytes.
- **FACT:** the leaf certificate subject is `Shenzhen Fibreseek Technology
  Limited Company`, chained through `GlobalSign GCC R45 EV CodeSigning CA 2020`.
- **FACT:** the leaf certificate is valid from 2025-09-09 through 2026-09-10 and
  uses SHA-256 with RSA.
- **OPEN QUESTION:** Windows-native chain and revocation validation was not
  performed on this macOS host. Certificate presence is not reported as a
  complete Windows trust verdict.

### macOS

- **FACT:** Gatekeeper accepted both the DMG and application as notarized
  Developer ID software.
- **FACT:** the origin is `Developer ID Application: Anisoprint 3D Printing
  Technology (Suzhou) Limited Company (RX954Z99LP)`.
- **FACT:** the application is thin `arm64`, team ID `RX954Z99LP`, bundle ID
  `com.rocketslicer.rocketslicer`, signed 2026-07-15 22:35:08, and associates
  `.auprojx` project files.
- **INFERENCE:** the signing identity is strong corporate/technical-continuity
  evidence. It does not establish that legacy Anisoprint parameters apply to
  FibreSeeker hardware.

## Application architecture

- **FACT:** both packages contain an Electron application with `resources/app.asar`.
- **FACT:** the package metadata names Shenzhen Fibreseek Technology Limited
  Company and declares application version `1.3.2`.
- **FACT:** the frontend communicates with a self-contained .NET backend that
  includes `Aura.*` assemblies, `Aura2SlicingEngine.dll`, SQLite libraries, and
  JSON-based template stores.
- **FACT:** the backend structured stores are semantically equivalent across the
  Windows and macOS packages; raw hashes differ where formatting or line endings differ.
- **FACT:** Windows extraction produced 591 files totaling 675,721,570 bytes.
- **INFERENCE:** Rocket is a FibreSeek-branded continuation of an Aura-derived
  application architecture.

## Update and preset endpoints

- **FACT:** static frontend resources expose `https://ota.fibreseek3d.com/update.json`
  (FS-123). It reports Rocket `1.3.2`, template version `8`, and regional service
  roots `https://app.fibreseek3d.com` and `https://app-us.fibreseek3d.com`.
- **FACT:** no protected application service was accessed.
- **FACT:** `https://ota.fibreseek3d.com/rocketslicer/manifest.json` (FS-124)
  currently reports public preset version `15`.
- **FACT:** the associated `Templates.zip` (FS-125) contains the current template store.
- **FACT:** both installers bundle preset version `13`; public preset version
  `15` is newer and therefore the preferred current profile evidence.

## Structured stores

### JSON templates

The main store is `resources/backend/resources/Templates/Presets/` and contains:

- `PrinterProperties.json`: printer geometry, extruders, limits, and cutter code.
- `Plastics.json`: plastic definitions and process temperatures.
- `Composites.json`: reinforcing-fiber and CFC matrix definitions.
- `ProfileGroups.json`: named printer/material/nozzle pairings.
- `Profiles.json`: process and reinforcement settings.
- `ProfileMaterials.json`: profile-to-material associations.
- extruder, slot, and settings-set stores.

| Store version | Plastics | Composites | Profile groups | Profiles |
|---|---:|---:|---:|---:|
| Bundled v13 | 4 | 3 | 14 | 42 |
| Public v15 | 7 | 5 | 16 | 48 |

**FACT:** v15 adds PLA definitions, CFC PLA + X-CCF definitions, and the profile
groups `PLA 0.2mm --- PLA+CCF02` and `PLA 0.25mm --- PLA+CCF02`.

### SQLite stores

- **FACT:** `Monolith.db` is SQLite user version 27 with 33 tables. It combines
  application state with printer/material/profile records.
- **FACT:** `aura3/data/settings.db` is SQLite user version 100 with a legacy
  schema containing 25 composites, 14 plastics, 4 printers, 39 profiles, 6 CFC
  extruders, 8 FFF extruders, 12 slots, and 68 profile-material links.
- **FACT:** potentially personal or sample application-state rows were not
  normalized or published.
- **OPEN QUESTION:** which legacy rows remain reachable in current Rocket UI and
  which exist only for migration compatibility.

## FibreSeeker machine definition

**FACT — current structured values:**

| Property | Value |
|---|---:|
| Machine name/key | `FibreSeeker 3` / `8896` |
| Build area | 305 × 305 × 245 mm |
| Heated bed/chamber | true / true |
| XY / Z travel speed | 500 / 10 mm/s |
| Default XY / Z acceleration | 5000 / 100 mm/s² |
| FFF nozzle diameter | 0.4 mm |
| CFC nozzle diameter | 0.7 mm |
| CFC `CutDistance` | 58 mm |
| CFC `FiberRestartLength` | 55 mm |

The CFC cut code is:

```gcode
M2800
M400
;CUT DISTANCE 54.8
```

- **FACT:** the structured cut distance (`58`) conflicts with the embedded code
  comment (`54.8`).
- **FACT:** UI text defines cut distance as the distance from the cut point to
  the nozzle outlet and marks it manufacturer-only. Restart length is extrusion
  during restart and is described as generally equal to cut distance.
- **OPEN QUESTION:** which distance the runtime uses and why restart length is 55 mm.
- **FACT:** no cutter timing value was found beyond `M400` synchronization.

## Current material definitions

### FFF plastics

| FibreSeek definition | Nozzle | Bed | Stored extrusion speed |
|---|---:|---:|---:|
| PLA | 220°C | 55°C | 15 |
| PETG | 250°C | 75°C | 15 |
| PET GF | 300°C | 75°C | 15 |
| PA CF / PACF | 270°C | 80°C | 15 |
| PPS CF | 330°C | 120°C | 10 |

### CFC composites

| Definition | Fiber diameter | Linear density | CFC nozzle | Bed | Stored fiber speed |
|---|---:|---:|---:|---:|---:|
| CFC PLA + X-CCF | 0.25 | 102 | 230°C | 55°C | 25 |
| CFC PETG + X-CCF | 0.25 | 102 | 270°C | 75°C | 25 |
| CFC PETG + X-CGF | 0.35 | 170 | 270°C | 75°C | 20 |
| CFC PA + X-CCF | 0.25 | 102 | 270°C | 80°C | 15 |

- **FACT:** the UI identifies fiber diameter in millimetres.
- **OPEN QUESTION (Rocket-only evidence):** the recovered Rocket schema does not
  label units for `LinearDensity`, stored fiber speed, or `FiberSpoolLength`.
- **INFERENCE (Phase 1B lineage):** official Aura documentation defines the
  same `LinearDensity` field as tex and fiber extrusion speed as mm/s; the exact
  composite UUID, fields, and values survive into Rocket. Unit continuity is
  high-confidence historical evidence, not FibreSeek manufacturer guidance.
  `FiberSpoolLength` remains unanswered. See
  `docs/slicer/aura/AURA_ROCKET_FIELD_MAP.md`.
- **OPEN QUESTION:** the preset name `CCF02` is not defined in first-party documentation.

## Profile and reinforcement parameters

**FACT:** v15 provides 16 material/nozzle profile groups, each with `Speedy`,
`ReinForced`, and `Fortified` profiles. Recovered ranges include:

| Parameter | Values observed |
|---|---|
| `MacroLayerHeight` | 0.10, 0.20, 0.22, 0.24, 0.25, 0.30 mm |
| `FLThickness` | 0.15, 0.20 mm |
| `FiberMinRadius` | 10, 12 mm |
| `FiberMaxArcSegmentLength` | 1, 3, 4 mm |
| `FiberNormalMinSpeed` | 2, 5 |
| `FiberNormalMaxSpeed` | 15, 20, 25, 30, 40 |
| `FiberStartLength` | 5, 10, 15 mm |
| `FiberSlowLength` | 5, 8, 10 mm |
| `FiberTensionLength` | 0, 2 mm |
| `FiberTensionFeedrate` | 0, 50% |
| `FiberAfterCutExtrusionMultP` | 0.58–0.72 |

**FACT — Phase 2F-B static contract:** all 48 v15 profiles store 10 mm for
solid- and cellular-fiber minimum line length. Rocket's UI defines these as the
shortest printable infill line, potentially with prolonging or polygon
connection. A separate minimum reinforced-perimeter field stores 20 mm in
Speedy profiles and 55 mm in ReinForced/Fortified profiles; the UI states that
shorter reinforced perimeters are not printed.

**BOUNDARY:** these are entity- and profile-specific Rocket thresholds. They do
not establish one universal FibreSeeker physical minimum segment length.

- **FACT:** UI text labels `FiberMinRadius` “Min. arc radius (mm)” and describes
  it as the radius corresponding to minimum printing speed.
- **INFERENCE:** this is a speed-model parameter, not proof of an absolute
  hardware turning-radius limit.
- **FACT:** UI text defines 100% fiber feedrate as the presumed path length and
  says lowering the percentage increases tension. No absolute linear fiber feed
  speed was recovered.
- **FACT:** reinforced pattern labels available in the UI are Solid, Rhombic
  grid, Isogrid, Anisogrid, and Tetragrid.
- **FACT:** observed angle lists include `0`, `0/90/0`, rhombic `0/90`, and
  isogrid guide angles `0/45`.
- **INFERENCE (Phase 1B lineage):** Aura's official CLI documentation maps
  `InfillFType` 0 to solid and 2 to isogrid. The field, value, associated
  parameter family, and one profile UUID survive into Rocket, supporting this
  enum mapping with high confidence. Tetragrid's numeric value remains open.

## Macrolayers and entity scheduling

- **FACT (FS-122):** Rocket defines a macrolayer as a package containing
  microlayers; each microlayer contains one or more print entities at the same
  height. Fiber layer height always equals macrolayer height.
- **FACT (FS-122, FS-125):** shell, plastic-perimeter, infill, and thick-support
  heights are exposed as ratio-derived values relative to macrolayer height.
  Current v15 profiles use ratios 1 or 2.
- **FACT (FS-122):** Rocket output parsers separately recognize `; LAYER:` and
  `; MACROLAYER:` and retain micro/macro layer mappings.
- **FACT (FS-122):** reinforced entity order is configurable as first in layer,
  last in layer, or before external shell after all other plastic/support
  entities. Enum values are 0, 1, and 2 respectively.
- **OPEN QUESTION:** invalid non-divisible input behavior and detailed complex
  support event scheduling require a contained offline output test.

## Masks and localized reinforcement

- **FACT (FS-122):** Rocket provides full/internal masks and support
  blocker/enforcer masks. Full/internal masks can locally modify fiber
  perimeters, fiber infill, and reinforcement patterns.
- **FACT (FS-122):** overlapping height-band layups use higher priority, with
  priority 1 highest.
- **OPEN QUESTION:** mask records carry priority and engine metadata includes
  trimming by other masks, but exact geometric mask-to-mask and mask-to-layup
  precedence has not been observed in generated output.

## Calibration and project formats

- **FACT:** Rocket associates `.auprojx` projects.
- **FACT:** the package contains parameters for nozzle offsets, fiber extrusion,
  cutting/restart, tension, path curvature, macrolayers, masks, and reinforced infill.
- **FACT:** static frontend bundles link to some legacy `aura.anisoprint.com`
  documentation pages.
- **OPEN QUESTION:** which calibration workflows are considered supported for
  end users versus service technicians in Rocket 1.3.2.

## Platform differences

- **FACT:** the project/proposals/frontend/backend content and current printer/preset semantics are
  effectively the same.
- **FACT:** Windows is x86-64 in an NSIS wrapper; macOS is arm64 in a notarized DMG.
- **FACT:** platform-specific Electron/runtime binaries and raw ASAR hashes differ.
- **FACT:** backend build timestamps differ by seconds while version/commit data match.

## Recommended next forensic steps

1. Diff preset v13 against v15 at field level and retain versioned normalized exports.
2. Map profile enums only from first-party UI code or an official schema.
3. Determine runtime precedence for `CutDistance` versus cut-code comments without executing hardware actions.
4. Ask FibreSeek to define `CCF02`, linear-density/spool units, and approved profile scope.
5. In Phase 1B only, compare Aura distributions against the legacy stores without promoting matches to FibreSeek guidance.
