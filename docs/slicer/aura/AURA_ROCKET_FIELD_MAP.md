# Aura to Rocket Field Map

## Scope and method

This table compares the official Aura 2.6.1 Sk3 preview (AP-105), Rocket
installer preset v13 (FS-121), and public preset v15 (FS-125). Aura 2.6.2
(AP-104) is used where it supplies the earlier Seeker branch.

`Aura value` and `Rocket value` show base values unless an override materially
changes the migration story. A non-null `Over` value may be the effective value,
but runtime precedence was not tested. Stable UUID continuity is required before
same-named fields are treated as lineage rather than coincidence.

Classification vocabulary: **unchanged**, **value changed**, **renamed**,
**structurally changed**, **Aura-only**, **Rocket-only**, or **unknown correspondence**.

## Machine, extruder, and slot fields

| Aura field/value | Rocket v13 | Rocket v15 | Classification | Evidence and caution |
|---|---|---|---|---|
| `GUID=83bf...08d40` | `Id=83bf...08d40`, `Key=8896` | same | renamed + structurally changed | Same 128-bit printer ID; Rocket adds numeric key |
| `Name=SEEKER 3` | `Name=FibreSeeker 3`, `NameOver=SEEKER 3` | same | renamed | Legacy label retained as override |
| `AreaSizeX=305` | 305 | 305 | unchanged | Same printer ID |
| AP-104 `AreaSizeY=300`; AP-105 `305` | 305 | 305 | value changed then unchanged | Aura branches differ |
| `AreaSizeZ=245` | 245 | 245 | unchanged | Same printer ID |
| `TravelSpeedXY=500`, `TravelSpeedZ=10` | 500 / 10 | same | unchanged values | Units documented in Aura; Rocket UI independently labels travel speed |
| `HasHeatedChamber=0`, `Over=0` | base `true`, `Over=false` | same | structurally changed | Stored base conflicts with override; current behavior not inferred |
| `DefaultAccelerationX/Y/Z=5000/5000/100` | same | same | unchanged | Same printer ID |
| `PostprocessorType=3` | 3 | 3 | unchanged value | Enum label unresolved |
| `IsAnisoprintApproved` | same property name | same | unchanged legacy name | Deprecated organizational vocabulary retained |
| CFC `GUID=f390...df84` | same `Id`, hyphenated | same | renamed representation | Direct identity |
| `CutDistance=60` | 58 | 58 | value changed | Aura documents mm; no operating recommendation |
| `FiberRestartLength=56` | 55 | 55 | value changed | Aura documents mm; runtime not tested |
| `CutCode` comment `55` | comment `54.8` | same | value changed | Separate from structured cut field |
| `HeatupSpeed=3.2` | 3.2 | 3.2 | unchanged | Same CFC ID; unit not independently established here |
| `NozzleContactRadius=1.7` | 1.2 | 1.2 | value changed | Same CFC ID |
| `NozzleContactRadiusExtended=2.6` | 1.8 | 1.8 | value changed | Same CFC ID |
| FFF `GUID=9fb4...eb90`, nozzle 0.4 | same ID and diameter | same | unchanged | Direct identity |
| `Slots.SlotIndex` / `SlotType` | `Index` / `Type` | same | renamed | AP-106 plus rows support 0 plastic, 1 composite |
| Relational `SlotExtruderMaterial` | JSON `SlotExtruderMaterials` with UUID and numeric-key foreign keys | same | structurally changed | Entity relation survives serialization change |

## Composite fields

All rows below use the same composite UUID `2af8ac62-4968-4364-88e3-1045ef47feba`.

| Aura AP-105 | Rocket v13 | Rocket v15 | Classification | Evidence and caution |
|---|---|---|---|---|
| `Name=SK3_X-CCF1K+CFC PETG` | `CFC PETG + X-CCF` | same | renamed | Same UUID |
| `FiberName=X-CCF 1K` | `X-CCF` | same | renamed | Does not establish tow construction beyond source labels |
| `FiberManufacturer=fibreseek` | same | same | unchanged | Case retained |
| `FiberDiameter=0.25` | 0.25 | 0.25 | unchanged value | Same UUID |
| `LinearDensity=102` | 102 | 102 | unchanged value | Aura unit is tex; Rocket unit is a high-confidence inference, not explicit UI fact |
| `FiberSpoolLength=0.5` | 0.5 | 0.5 | unchanged value | Unit remains open |
| `ExtrusionSpeedF=25` | 25 | 25 | unchanged value | Aura calls fiber extrusion speed mm/s; Rocket continuity is inferred |
| `TemperaturePrint=255` | 270 | 270 | value changed | Historical value is not FibreSeek guidance |
| `BedTemperature=75` | 75 | 75 | unchanged value | Historical continuity only |
| `Version=3`, approved false | version 1, approved true | same | value changed | Version domains may differ |
| One relational `Composite` row | JSON entity plus numeric `Key` and organization/user IDs | same | structurally changed | Rocket adds service-layer identity fields |
| No CCF PLA/X-CCF entity | absent | added; duplicated UUID under keys 1676/1677 | Rocket-only | Duplicate visible record is an archive finding, not a recommendation |

## Profile and path fields

Rows use profile UUID `d294a2dc-9d7f-460a-acf4-dc50b656d44a` unless noted.

| Aura AP-105 | Rocket v13 | Rocket v15 | Classification | Evidence and caution |
|---|---|---|---|---|
| `Name=SK3_CCF 1K+PETG_PETG` | `Name=Speedy`; `NameOver=PETG + X-CCF / PETG` | same | renamed + structurally changed | Rocket separates profile group from speed variant |
| `MacroLayerHeight=0.24`, `Over=0.24` | base 0.2, `Over=0.24` | same | structurally changed | Legacy value migrated to override |
| No direct `FiberFLThicknessMM` field | 0.2 | 0.2 | Rocket-only | Do not equate automatically with Aura macrolayer height |
| `FiberMinRadiusF=12` | `FiberMinRadius=12` | 12 | renamed + unchanged | Aura `F` suffix removed; Rocket UI labels mm |
| `FiberMaxArcSegmentLengthF=2` | `FiberMaxArcSegmentLength=3` | 3 | renamed + value changed | Unit continuity not independently proven |
| `FiberStartLengthF=6` | `FiberStartLength=15` | 15 | renamed + value changed | Same profile ID |
| `FiberSlowLengthF=10` | `FiberSlowLength=5` | 5 | renamed + value changed | Same profile ID |
| `FiberTensionLengthF=0.15` | `FiberTensionLength=0` | 0 | renamed + value changed | Tension behavior appears disabled in this profile |
| `FiberTensionFFeedrate=100` | `FiberTensionFeedrate=0` | 0 | renamed + value changed | Aura duplicate `F` removed |
| `FiberTensionReleaseFraction=100` | 0 | 0 | value changed | Same field name |
| `FiberAfterCutExtrusionMultP=0.6` | 0.58 | 0.58 | value changed | Multiplier semantics retained by name only |
| `FiberStartMaxSpeedF=5` | `FiberStartMaxSpeed=5` | 5 | renamed + unchanged | Aura suffix removed |
| `FiberStartMinSpeedF=3` | `FiberStartMinSpeed=3` | 3 | renamed + unchanged | Same profile ID |
| `FiberNormalMaxSpeedF=30` | `FiberNormalMaxSpeed=30` | 30 | renamed + unchanged | Same profile ID |
| `FiberNormalMinSpeedF=2` | `FiberNormalMinSpeed=5` | 5 | renamed + value changed | Unit continuity not assumed |
| `FiberFinishMaxSpeedF=7` | `FiberFinishMaxSpeed=15` | 15 | renamed + value changed | Unit continuity not assumed |
| `FiberFinishMinSpeedF=2` | `FiberFinishMinSpeed=5` | 5 | renamed + value changed | Unit continuity not assumed |
| `InfillFType=2` | 2 | 2 | unchanged | Aura official enum maps 2 to isogrid; Rocket mapping is supported by direct profile continuity |
| `InfillFType` enum 0–3 | Rocket profiles use 0 and 2 | same | partially unchanged | 0=solid, 1=rhombic, 2=isogrid, 3=anisogrid in Aura; Rocket 1/3 unused in preserved presets |
| Tetragrid parameter family | same-named family | same | unchanged schema family | Numeric `InfillFType` value for Tetragrid remains unknown |
| `InfillFSolidAngleList="0"` | `"0"` | `"0"` | unchanged | Stored string syntax preserved |
| Isogrid angle/density 0/25 | 0/25 | 0/25 | unchanged values | No layup recommendation implied |
| `AllowGenerateFiber=1` | base false, `Over=true` | base true, `Over=true` | structurally/value changed | v15 aligns base and override |
| `ProfileMaterial` join table | `ProfileGroups` + `ProfileMaterials` JSON arrays and keys | same structure | structurally changed | Compatibility associations survive in service-oriented form |
| `GUID` primary keys | UUID `Id` plus numeric `Key`/`ProfileGroupKey` | same | structurally changed | Stable UUIDs coexist with backend keys |
| No `CCF02` label | absent | two CCF02 profile groups | Rocket-only | Meaning unresolved |

## Projects, masks, and settings

| Aura | Rocket | Classification | Status |
|---|---|---|---|
| `.auprojx` SQLite project with embedded printer/material/profile/session and model/mask rows | Rocket associates `.auprojx` files | unknown correspondence | File association proves recognition, not compatibility |
| `MaskRule` and `LayupRule` tables carry infill/perimeter fields and embedded STEP text | Rocket schemas/UI retain masks and reinforced infill fields | structurally changed | Conceptual lineage is clear; project migration path is untested |
| `.aus.json` exported session contains printer, materials, and profile settings | No public Rocket session sample recovered | Aura-only / unknown | Do not claim Rocket import compatibility |
| `Anisoprint.ausettings` SQLite library | JSON preset arrays plus Aura-named SQLite/backend stores | structurally changed | Rocket moved distribution presets to JSON while retaining Aura backend lineage |

## Units and enum confidence

| Item | Aura first-party evidence | Rocket conclusion |
|---|---|---|
| `CutDistance`, `FiberRestartLength` | AP-107 explicitly says mm | **INFERENCE:** likely inherited; Rocket UI independently describes cut distance but conflicting stored values remain |
| `LinearDensity` | AP-107 explicitly says tex = g/km | **INFERENCE, high confidence:** exact UUID/field/value continuity; no Rocket unit label recovered |
| `ExtrusionSpeedF` | AP-107 explicitly says mm/s | **INFERENCE, high confidence:** exact UUID/field/value continuity; no Rocket unit label recovered |
| Reinforced fiber feedrate | AP-107 explicitly says percent | **FACT for Rocket UI:** Phase 1A independently recovered percent wording |
| `FiberSpoolLength` | No unit recovered | **OPEN QUESTION** |
| `InfillFType=0` | AP-110: solid | **INFERENCE, high confidence** through stable field/schema continuity |
| `InfillFType=2` | AP-110: cellular isogrid | **INFERENCE, high confidence** through stable profile UUID and value |
| Tetragrid numeric ID | Not assigned in AP-110/schema | **OPEN QUESTION** |
| Slot `0` / `1` | Aura rows plus AP-106 roles | **FACT for inherited schema:** plastic / composite |
