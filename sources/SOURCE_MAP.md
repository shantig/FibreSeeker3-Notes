# Source Map

## Phase 1A preserved FibreSeek corpus

The raw originals for the following groups are preserved under
`<archive>/FibreSeeker-KB-Archive/originals/FIBRESEEK_OFFICIAL/`. Exact URLs,
hashes, sizes, timestamps, filenames, and archive paths are in
`sources/manifest.jsonl`.

| IDs | Preserved group | Why it matters |
|---|---|---|
| FS-101–FS-110 | English and Chinese official web pages | Dated first-party product, material, software, and support claims. |
| FS-111–FS-115 | Store pages, products JSON, and sitemap | Machine-readable evidence for X-CCF and CFC hotend availability. |
| FS-120 | FibreSeeker 3 User Manual R1 | Primary architecture, X-CCF construction, operation, storage, calibration, and maintenance evidence. |
| FS-121–FS-122 | Rocket 1.3.2 Windows/macOS packages | Signed static-forensics sources for machine, material, profile, and parameter stores. |
| FS-123–FS-125 | Rocket update manifest, preset manifest, and preset v15 | Current version endpoints and usable first-party settings/profile definitions. |
| FS-130–FS-147, FS-149 | Quick Start, unboxing, service, and troubleshooting corpus | First-party calibration, replacement, unclogging, offset, layer-shift, and first-layer procedures. |
| FS-116–FS-119, FS-148 | Diagnostic fallback captures | Evidence that expected sitemap/robots/English first-layer endpoints returned homepage HTML rather than requested resources. |

## Phase 1B preserved Aura corpus

Raw originals are under
`<archive>/FibreSeeker-KB-Archive/originals/ANISOPRINT_OFFICIAL/`; bounded
static extracts and indexes are under the matching NAS `derived/` trees.

| IDs | Preserved group | Why it matters |
|---|---|---|
| AP-101–AP-102 | Aura download-index retrieval records | Preserves the current official package/version list and the expired-TLS acquisition condition. |
| AP-103 | Aura 2.5.8 Stable installer | Pre-Seeker schema baseline, public projects, settings DB v14, and CLI schema. |
| AP-104 | Aura 2.6.2 installer | Seeker-3 printer/extruder IDs, settings DB v17, modern .NET package, and Fibreseek signing metadata. |
| AP-105 | Aura 2.6.1 Sk3 template preview | Focused X-CCF composite/profile records and settings DB v19 that directly bridge to Rocket. |
| AP-106 | Archived Aura changelog | Versioned evidence for formats, migration, masks, Tetragrid, tension, and settings evolution. |
| AP-107 | Aura settings review | First-party legacy units and semantics for cutter distance, restart, fiber speed, linear density, and feedrate. |
| AP-108–AP-109 | Aura guide and GUI docs | Official project, session, settings, and export behavior. |
| AP-110 | Aura CLI documentation | `.aus.json` role, model-input schema, and fiber-infill enum mapping. |
| AP-111–AP-113 | Macrolayer, entity, and mask docs | Historical semantics for composite layers and localized reinforcement. |

## Phase 2F-A preserved Anisoprint operational corpus

All originals remain under the same immutable Anisoprint NAS tree. Derived
operational records and coverage details are in `data/operational/`.

| IDs | Preserved group | Why it matters |
|---|---|---|
| AP-114–AP-115 | `aura-docs` and `MKA-firmware` Git bundles | Immutable official documentation and static firmware/code semantics at recorded commits. |
| AP-116–AP-120 | Composer manuals, guide, XY calibration, failed service G-code | Calibration triggers/procedures/verification and visible `NozzleOffsetTest.gcode` 404 state. |
| AP-121–AP-142 | Firmware inventory, design/material/support/Aura operational pages | Bounded operation, design, materials, layers, supports, layup, diagnostics, and maintenance corpus. |
| AP-143–AP-148 plus AP-124 | Official training video lesson pages | Canonical Anisoprint provenance, Vimeo IDs, durations, relevance, and annotation-ready transcript status. |

The remaining tables began as the Phase 0 discovery inventory on 2026-08-13.
An item is an acquisition candidate unless a preserved group above or the
manifest marks it acquired. IDs correspond to `sources/manifest.jsonl`.

## FibreSeek official

| ID | Source | Why it matters |
|---|---|---|
| FS-001 | [FibreSeek home](https://www.fibreseek3d.com/) | Current product claims, Rocket links, examples, and corporate identity. |
| FS-002 | [FibreSeeker 3 product page](https://www.fibreseek3d.com/products.html) | 350°C hotend, 65°C chamber, application material examples, and current machine positioning. |
| FS-003 | [Filaments page](https://www.fibreseek3d.com/filaments.html) | Official material catalog shell and X-CCF navigation target. |
| FS-004 | [Rocket software page](https://www.fibreseek3d.com/software.html) | Official slicer modes, masks, visualization, and download links. |
| FS-005 | [Support page](https://www.fibreseek3d.com/support.html) | Warranty/ticket endpoints and the nominal setup, troubleshooting, software, and material guide categories. |
| FS-006 | [Chinese Rocket page](https://www.fibreseek3d.cn/software.html) | Parallel first-party page that may expose region-specific assets or versions. |
| FS-007 | [Official store collection](https://store.fibreseek3d.com/collections/all) | Current X-CCF 1K and CFC hotend product listings. |
| FS-008 | [Rocket Windows installer](https://ota.fibreseek3d.com/rocketslicer/RocketSlicer-win-x64-Setup.exe) | Primary static-forensics target for printer/material/profile definitions. |
| FS-009 | [Rocket macOS installer](https://ota.fibreseek3d.com/rocketslicer/RocketSlicer-mac-arm64.dmg) | Apple Silicon distribution and independent package comparison target. |
| FS-010 | [FibreSeeker 3 User Manual R1](https://fccid.co/api/files/s2/fccids/2BVZ6-FIBRESEEKER3/files/6a1adb68_13_FibreSeeker_3_Users_Manual_R1.pdf) | Most information-dense FibreSeek-authored source found: X-CCF construction, nozzle/cutter, materials, calibration, storage, and maintenance. |
| FS-011 | [Official Kickstarter campaign](https://www.kickstarter.com/projects/1763117873/fibreseeker-3-the-first-personal-continuous-fibre-3d-printer) | Dated launch specifications, updates, comments, and potentially vanished downloads. |
| FS-012 | [Rocket 0.10.0 update post](https://www.linkedin.com/posts/fibreseek_fibreseeker3-rocketslicer-optimizations-activity-7426682555371814912-oH4I) | Versioned Rocket change evidence and a pointer to official walkthrough video. |

## Anisoprint official

| ID | Source | Why it matters |
|---|---|---|
| AP-001 | [Anisoprint home](https://anisoprint.com/) | First-party CFC process explanation and legacy application examples. |
| AP-002 | [Support portal](https://support.anisoprint.com/) | Stable hub for Composer, Aura, design, firmware, and safety notices. |
| AP-003 | [Aura Docs](https://docs.anisoprint.com/) | Structured current documentation index. |
| AP-004 | [Aura downloads/changelog](https://support.anisoprint.com/aura/downloads/) | Aura 2.6.2, 2.5.8 stable, beta/Sk3 preview, sample-project, profile, and change history targets. |
| AP-005 | [Archived Aura changelog](https://support.anisoprint.com/aura/downloads/changelog-legacy/) | Version archaeology, formats, compatibility, settings/profile additions, and algorithm changes. |
| AP-006 | [Aura guide](https://support.anisoprint.com/aura/guide/) | Legacy modular stores for plastics, fibers, printers, profiles, and export behavior. |
| AP-007 | [Aura settings review](https://support.anisoprint.com/aura/settings-review/) | Parameter names, units, fiber feedrate semantics, layer model, and reinforced path controls. |
| AP-008 | [Aura GUI overview](https://docs.anisoprint.com/aura/gui/) | Confirms exportable settings stores and session behavior. |
| AP-009 | [Aura CLI](https://docs.anisoprint.com/aura/premium/cli/) | `.aus.json` session format, CLI schema location, layup JSON, and infill enums. |
| AP-010 | [Macrolayers](https://docs.anisoprint.com/aura/macrolayers/) | Authoritative legacy relationship between composite macrolayers and plastic microlayers. |
| AP-011 | [Part internal structure](https://docs.anisoprint.com/aura/entities/) | Official reinforced perimeter and solid/rhombic/isogrid/anisogrid taxonomy. |
| AP-012 | [Masks](https://docs.anisoprint.com/aura/premium/masks/) | Localized reinforcement and hole-adjacent path-control example. |
| AP-013 | [Aura editions](https://docs.anisoprint.com/aura/licensing/editions/) | Explains NEAT/EXT/OPEN access, exports, legacy projects, and licensing limits. |
| AP-014 | [Composer support index](https://support.anisoprint.com/composer/) | Canonical map to manuals, troubleshooting, guide, and firmware. |
| AP-015 | [Composer online manual](https://support.anisoprint.com/composer/manual/) | Operation, calibration, cutter, material storage, safety, and failure modes. |
| AP-016 | [Composer User Manual PDF](https://support.anisoprint.com/wp-content/uploads/2021/12/composer-user-manual-18.pdf) | Immutable manual acquisition target suitable for hashing and text extraction. |
| AP-017 | [Composer guide](https://support.anisoprint.com/composer/guide/) | Detailed load/unload, calibration, firmware, and maintenance procedures. |
| AP-018 | [Composer firmware downloads](https://support.anisoprint.com/composer/firmware-downloads/) | Versioned safety fixes and firmware history; archive only, never flash during research. |
| AP-019 | [Basic Rules for Design](https://support.anisoprint.com/design/design-2/) | Legacy first-party plane-load, bending, orientation, and reinforcement guidance. |
| AP-020 | [Training courses](https://anisoprint.com/trainings/) | Official curriculum and linked material/operation pages and videos. |
| AP-021 | [CFC PA training/material page](https://anisoprint.com/trainings/cfc-pa/) | Legacy temperature, speed, drying/storage, and nozzle recommendations. |
| AP-022 | [CFC PETG material page](https://anisoprint.com/cfc-petg/) | Official matrix properties, temperatures, straight-path speeds, and drying guidance. |
| AP-023 | [CFC PETG datasheet v2.1](https://anisoprint.com/wp-content/uploads/2022/03/CFC_PETG_datasheet_March_2022.pdf) | Versioned mechanical test data and material definition. |
| AP-024 | [Reinforcing fiber](https://support.anisoprint.com/2021/12/15/reinforcing-fiber/) | Official CCF tow construction and material cautions. |
| AP-025 | [Clear PETG](https://anisoprint.com/clear-petg/) | Companion FFF material and datasheet link for the approved PETG pair. |
| AP-026 | [Composer material compatibility FAQ](https://support.anisoprint.com/2018/12/16/what-materials-can-be-used-on-composer-a4/) | Legacy approved/possible material scope and explicit guarantee boundary. |
| AP-027 | [Aura.Connect quickstart](https://docs.anisoprint.com/aura-connect/quickstart/) | Confirms `.auprojx` association, G-code workflow, and historical cloud endpoint. |
| AP-028 | [Desktop Anisoprinting](https://anisoprint.com/solutions/desktop/) | Legacy machine specifications, CFC speeds, material flexibility, and documented reinforcement examples. |

## Research

| ID | Source | Why it matters |
|---|---|---|
| AC-001 | [Novel Continuous Fiber Bi-Matrix Composite 3-D Printing Technology](https://pmc.ncbi.nlm.nih.gov/articles/PMC6766289/) | Core 2019 open-access paper co-authored by Antonov/Anisoprint researchers; process and material architecture. |
| AC-002 | [Optimization of parts manufactured using continuous fiber 3D printing](https://www.sciencedirect.com/science/article/abs/pii/S1359836821007770) | Anisoprint-coauthored topology/fiber-orientation optimization and race-car pedal case. |
| AC-003 | [Development of a two-matrix composite material](https://doi.org/10.1134/S1995421217010026) | Early Antonov/Azarov paper defining the dual-matrix concept and mechanical basis. |
| AC-004 | [Compression Behavior of 3D Printed Composite Isogrid Structures](https://pmc.ncbi.nlm.nih.gov/articles/PMC11478640/) | Mechanical testing of Anisoprint CFC isogrid structures. |
| AC-005 | [Mechanical Properties and Economic Analysis of FFF Continuous Carbon Fiber Composites](https://pmc.ncbi.nlm.nih.gov/articles/PMC11435924/) | Tested Clear PETG/CFC PETG/CCF system, dimensions, parameters, and economics. |
| AC-006 | [Effect of moisture content on a continuous reinforced two-matrix composite](https://link.springer.com/article/10.1007/s00170-024-14041-5) | Directly relevant moisture/mechanical study; does not by itself establish FibreSeek storage rules. |
| AC-007 | [Component-based topology and continuous fiber layout optimization](https://link.springer.com/article/10.1007/s00158-025-04223-4) | Manufactures the optimized result on Composer A4 and discusses curvature/spacing constraints. |

## Patents

| ID | Source | Why it matters |
|---|---|---|
| PT-001 | [EP3693151A1 — Production of composite articles by 3D printing](https://patents.google.com/patent/EP3693151A1/en) | CFC process, cured thermoset-impregnated tow, thermoplastic co-extrusion, cutting, and nozzle architecture. |
| PT-002 | [US20200283591A1 — Reinforcing composite filament and production](https://patents.google.com/patent/US20200283591A1/en) | Feedstock construction, impregnation, matrices, and production methods. |
| PT-003 | [ES2998030T3 — Print head for additive manufacturing](https://patents.google.com/patent/ES2998030T3/en) | Active print-head family record covering plastic/fiber feeds and cutting mechanism. |

## Community and open source

| ID | Source | Why it matters |
|---|---|---|
| CM-001 | [Bilby3D FibreSeeker 3 page](https://b3d.com.au/fibreseek/fibreseeker3.asp) | Reseller specifications and regional product/support context; verify every value against FibreSeek. |
| CM-002 | [FullControl](https://github.com/FullControlXYZ/fullcontrol) | Open-source explicit toolpath generation useful for future experiments, not vendor guidance. |
| CM-003 | [Strecs3D](https://github.com/tomohiron907/Strecs3D) | Open-source stress-result-to-variable-infill workflow and potential Forge research input. |
| CM-004 | [FibreSeek community discussion](https://www.reddit.com/r/3Dprinting/comments/1mi7r1y/anyone_have_any_further_info_on_the_fibre_seek/) | Leads and user claims about Anisoprint continuity; useful only as questions to verify. |

## High-priority evidence status

- **FibreSeek-confirmed:** the R1 manual describes X-CCF as continuous carbon
  fiber impregnated with thermoset resin at approximately 60% fiber volume; CFC
  plastic examples are PLA/PETG/PA; the CFC nozzle is 0.7 mm, rated to 350°C,
  and has a built-in cutter; X-CGF is listed as supported.
- **Partially answered:** FibreSeek says remove materials for long storage and
  use a sealed container. Its explicit drying instruction names hygroscopic FFF
  plastics, not X-CCF. No authoritative Phase 0 source says X-CCF should be
  heated or gives a drying cycle.
- **Still open for FibreSeek:** exact resin chemistry, X-CCF storage limits,
  whether X-CCF must never be heated/dried, approved matrix combinations and
  temperatures, fiber linear feed speed, cutting geometry/timing, minimum turn
  radius, composite layer-height window, fill/volume equations, structural
  layup rules, and machine-specific failure recovery.
- **Legacy-only evidence exists:** Anisoprint documents CCF construction,
  feedrate semantics, macrolayers, reinforced perimeters/infills, masks around
  holes, plane-load/bending guidance, calibration, approved material profiles,
  and common CFC failures. These remain `ANISOPRINT_OFFICIAL` pending explicit
  FibreSeek confirmation.
