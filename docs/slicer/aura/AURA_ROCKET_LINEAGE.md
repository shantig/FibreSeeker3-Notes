# Aura to Rocket Lineage

> Legacy Anisoprint/Aura evidence is historical/comparative evidence and is not
> FibreSeek manufacturer guidance.

## Conclusion

**FACT:** Rocket is not merely similar to Aura. Stable UUIDs for the Seeker
printer, both extruders, the X-CCF composite, and an X-CCF profile survive from
official Aura packages into Rocket preset v13 and v15. Field names, base/override
pairs, relational concepts, and the `IsAnisoprintApproved` property also survive.

**INFERENCE:** this constitutes a direct schema/data genealogy. It does not show
that every inherited field is active, correctly labeled, expressed in the same
unit, or safe to use on current hardware.

## Evidence chain

| Stage | Evidence | Scope |
|---|---|---|
| Aura 2.5.8 Stable | AP-103, SQLite schema v14 | Mature pre-Seeker Aura model and public project samples |
| Aura 2.6.2 | AP-104, SQLite schema v17 | First bounded package containing `Seeker-3` plus stable printer/extruder IDs |
| Aura 2.6.1 Sk3 preview | AP-105, SQLite schema v19 | Focused Seeker/X-CCF material and profile records |
| Rocket 1.3.2 installer | FS-121/FS-122, preset v13 | FibreSeek distribution with JSON entities and Aura-derived backend |
| Rocket public templates | FS-125, preset v15 | Current first-party preset snapshot at Phase 1A cutoff |

Version numbers do not establish package build order. AP-104 and AP-105 are
treated as parallel official evidence unless a build date independently proves
otherwise.

## Stable identity chain

| Entity | Aura ID | Rocket ID | Result |
|---|---|---|---|
| Seeker printer | `83bf10398c9e49fc928f2f94a2008d40` | `83bf1039-8c9e-49fc-928f-2f94a2008d40` | Same 128-bit ID, hyphenated in Rocket |
| CFC extruder | `f3904c6fc24e4affad9a70405cc4df84` | `f3904c6f-c24e-4aff-ad9a-70405cc4df84` | Same ID |
| FFF extruder | `9fb4b169bf0f4436833e6afdfaeeeb90` | `9fb4b169-bf0f-4436-833e-6afdfaeeeb90` | Same ID |
| X-CCF/CFC PETG composite | `2af8ac624968436488e31045ef47feba` | `2af8ac62-4968-4364-88e3-1045ef47feba` | Same ID |
| X-CCF profile | `d294a2dc9d7f460aacf4dc50b656d44a` | `d294a2dc-9d7f-460a-acf4-dc50b656d44a` | Same ID |
| CFC slot | `e24c808eaa324b0fb1eecf377d5a3428` | `e24c808e-aa32-4b0f-b1ee-cf377d5a3428` | Same ID from both Seeker Aura packages |
| FFF slot | AP-104 `55a7c2ac...`; AP-105 `ea6f4e24...` | `55a7c2ac-da0f-4af3-a493-56c59cc2f1df` | Rocket selects the AP-104 branch |

**FACT:** Rocket combines the AP-104 FFF slot identity with the AP-105 X-CCF
composite/profile identities. This is stronger evidence of deliberate migration
than a simple package rename.

## Material changes across the chain

The same X-CCF composite ID contains:

| Field | Aura Sk3 preview | Rocket v13 | Rocket v15 | Classification |
|---|---:|---:|---:|---|
| Name | `SK3_X-CCF1K+CFC PETG` | `CFC PETG + X-CCF` | same as v13 | renamed |
| Fiber diameter | 0.25 | 0.25 | 0.25 | unchanged |
| Linear density | 102 | 102 | 102 | unchanged value |
| Fiber spool length | 0.5 | 0.5 | 0.5 | unchanged value; unit open |
| Stored fiber extrusion speed | 25 | 25 | 25 | unchanged value |
| Print temperature | 255 | 270 | 270 | value changed |
| Bed temperature | 75 | 75 | 75 | unchanged |

**FACT:** AP-107 defines the Aura `LinearDensity` unit as tex and fiber
extrusion speed as mm/s. The exact composite UUID, field names, and numeric
values persist into Rocket.

**INFERENCE:** Rocket probably retains those two units. This is high-confidence
lineage evidence, but no Rocket/FibreSeek UI label was recovered for either
field; therefore it is not elevated to FibreSeek manufacturer guidance.

**OPEN QUESTION:** `FiberSpoolLength = 0.5` remains unitless in both recovered
first-party schemas.

## Cutter-distance genealogy

| Source | Structured `CutDistance` | Structured restart | Cut-code comment |
|---|---:|---:|---:|
| Aura 2.6.2, same CFC ID | 60 | 56 | `;CUT 55` |
| Aura 2.6.1 Sk3 preview, same CFC ID | 60 | 56 | `;CUT 55` |
| Rocket preset v13, same CFC ID | 58 | 55 | `;CUT DISTANCE 54.8` |
| Rocket preset v15, same CFC ID | 58 | 55 | `;CUT DISTANCE 54.8` |

**FACT:** the 58 mm versus 54.8 mm discrepancy is inherited from an Aura design
that already stored a structured cutter distance separately from a different
value in the G-code comment. Rocket changed both values and retained the split.

**OPEN QUESTION:** static data does not establish whether 54.8 is calibration,
effective cut-to-outlet distance, stale commentary, or another physical
quantity. It also does not establish runtime precedence. No operating value is
recommended.

## Profile migration

The AP-105 profile UUID becomes Rocket's `Speedy` profile. Selected base/override
changes are listed in the field map; key changes include:

- **FACT:** Aura suffixes many path fields with `F`; Rocket removes that suffix
  while preserving the profile ID and concepts.
- **FACT:** minimum radius stays 12, while maximum arc segment changes 2→3,
  start length 6→15, slow length 10→5, tension length 0.15→0, tension feedrate
  100→0, and after-cut multiplier 0.6→0.58.
- **FACT:** the Aura macrolayer value 0.24 appears in Rocket as the override,
  while Rocket's base value is 0.2. This demonstrates migration of defaults and
  overrides rather than a simple scalar replacement.
- **FACT:** `InfillFType = 2` survives in the same profile. AP-110 maps Aura enum
  2 to cellular isogrid.
- **INFERENCE:** Rocket enum 2 is isogrid because the same profile ID, field, and
  value survive and Rocket retains the associated isogrid parameter fields.
  Enum 0 is correspondingly solid under the same documented mapping. This is
  schema interpretation, not a structural-use recommendation.
- **FACT:** v15 changes the same profile's `AllowGenerateFiber` base from false
  to true while leaving its other highlighted values unchanged from v13.

## v13 to v15

- **FACT:** printer, CFC/FFF extruder, slot, and highlighted X-CCF composite
  records are unchanged between v13 and v15.
- **FACT:** v15 expands plastics, composites, profile groups, and profiles and
  introduces six profiles in two `CCF02`-named PLA groups.
- **FACT:** v15 duplicates the CFC PLA + X-CCF composite UUID under keys 1676
  and 1677 with identical visible values.
- **OPEN QUESTION:** no bounded first-party source defines `CCF02`; it must not
  be expanded or interpreted from its name alone.

## Five high-value lineage discoveries

1. Stable entity UUIDs prove direct Aura→Rocket migration.
2. Rocket combines identities from two official Aura Seeker package branches.
3. Aura explains the origin of the structured/comment cutter-distance split.
4. Aura first-party docs resolve infill enum 0–3 and historical units for
   linear density, fiber extrusion speed, cutter distance, and restart length.
5. Rocket retains legacy names such as `IsAnisoprintApproved`, base/override
   pairs, macrolayers, masks, Tetragrid fields, and Aura project association.

## Remaining uncertainties

- Whether current Rocket consumes every inherited field or merely serializes it.
- Whether Rocket interprets all inherited values with unchanged units.
- Runtime precedence for base versus override fields and cutter-code comments.
- Numeric Tetragrid and profile-status mappings.
- `CCF02` meaning and `FiberSpoolLength` unit.
- Whether Rocket can safely open every Aura 2 `.auprojx`; file association is
  not proof of migration compatibility.
