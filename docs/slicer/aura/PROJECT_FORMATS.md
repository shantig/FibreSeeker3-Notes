# Aura and Rocket Project Formats

## Safety boundary

All project/session findings are from public first-party documentation and
static file inspection. No project was imported, sliced, or sent to hardware.

## `.auprojx`

**FACT:** the 18 public sample projects bundled with each analyzed Aura package
are SQLite 3 databases, not ZIP archives. All 18 sample files are byte-identical
across Aura 2.5.8, Aura 2.6.2, and the Aura 2.6.1 Sk3 preview.

The representative `Plate with Masks.auprojx` has SQLite `user_version = 11`
and 14 tables:

`Composite`, `EntityWithLayupData`, `ExtruderC`, `ExtruderP`, `LayupRule`,
`MaskRule`, `Plastic`, `Printer`, `Profile`, `ProfileMaterial`, `ProjectInfo`,
`Session`, `SlotExtruderMaterial`, and `Slots`.

### Embedded content

- **FACT:** printer, extruder, plastic, composite, profile, compatibility, slot,
  and session rows are embedded in the project rather than referenced only by
  an external settings library.
- **FACT:** `ProjectInfo` contains project name, description, three base64 JPEG
  thumbnails, approval/update flags, and a project GUID.
- **FACT:** `Session` points to the selected printer/profile and slot-material
  combinations by GUID.
- **FACT:** `EntityWithLayupData` embeds model text and flags for layup/mask data.
  In the inspected sample the main model is embedded STEP text.
- **FACT:** two `MaskRule` rows embed separate STEP mask bodies and carry layer,
  priority, mask type, perimeter, infill, angle, and density settings.
- **FACT:** nearly all configurable project settings retain Aura's base plus
  `Over` override-column convention.

### Version and migration evidence

- **FACT (AP-106):** Aura 2 introduced `.auprojx`; old `.auproj` projects could
  be opened but only saved in the new format, subject to the documented license.
- **FACT (AP-106):** Aura 2.1 changed migration to use temporary files so the
  original project was not modified when opened by a newer version.
- **FACT (AP-106):** Aura 2.3.2 added an “update AP settings” path that updated
  base settings while preserving user overrides.
- **FACT:** `ProjectInfo.UpdateSettingFromNewAP=1` is present in the public sample.
- **OPEN QUESTION:** SQLite `user_version=11` is a database schema marker; no
  bounded first-party source maps it to an Aura release or guarantees future
  compatibility.

## `.aus.json`

**FACT (AP-109/AP-110):** Aura's “Export session” operation writes all slicing
settings, including printer, materials, and profile settings. Aura CLI consumes
this JSON session with `--session settings.aus.json`.

**FACT:** no public `.aus.json` sample was present in the three installers and
none was acquired from the bounded official corpus. Therefore its complete
property schema, version marker, and migration rules remain unknown.

Do not confuse `.aus.json` with `Anisoprint.ausettings`. The latter is the
SQLite settings library distributed with Aura; the former is a user-exported
JSON session described by official CLI documentation.

## CLI model-input JSON

The separate `cli-inputfile.schema.json` is not an `.aus.json` schema. It
describes the optional `--input` model list, transforms, layup rules, and masks.

- **FACT:** the schema requires a root `Models` array.
- **FACT:** each model may carry transforms and either layup rules or masks;
  official documentation says masks take precedence when both are supplied.
- **FACT:** the 2.5.8 schema uses one combined bottom/top solid-layer count.
  The 2.6.2 and Sk3 schemas split it into top and bottom counts.
- **FACT:** the 2.6.2 and Sk3 CLI schemas are byte-identical.
- **FACT:** all recovered CLI schemas constrain `InfillFType` to 0–3.

## Rocket relationship

- **FACT:** Rocket 1.3.2 registers an `.auprojx` file association.
- **FACT:** Rocket retains Aura-derived project/settings libraries and fields
  for masks, layups, macrolayers, materials, slots, and reinforced infill.
- **INFERENCE:** Rocket is intended to recognize an Aura-family project
  container. File association and schema lineage do not prove that all Aura
  projects migrate correctly or that their embedded printer/material values are
  safe for FibreSeeker.
- **OPEN QUESTION:** whether Rocket opens Aura `user_version=11` directly,
  migrates it, or accepts only a Rocket-specific descendant format.
- **OPEN QUESTION:** whether Rocket can import Aura `.aus.json` sessions. No
  public first-party evidence in this phase supports that claim.

## Preserved evidence

The public sample projects, CLI schemas, SQLite inventories, and per-file hashes
are stored under:

- `<archive>/FibreSeeker-KB-Archive/derived/extracted/AP-103`
- `<archive>/FibreSeeker-KB-Archive/derived/extracted/AP-104`
- `<archive>/FibreSeeker-KB-Archive/derived/extracted/AP-105`
