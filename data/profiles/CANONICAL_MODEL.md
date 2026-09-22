# Canonical Normalized Model

## Evidence boundary

The model stores observations, not operating recommendations. Aura observations remain `ANISOPRINT_OFFICIAL`; Rocket observations remain `FIBRESEEK_OFFICIAL`. Cross-version meaning, units, aliases, and effective values are independently classified as `FACT`, `INFERENCE`, or `OPEN_QUESTION`.

## Source chain

| ID | Software/version | Branch | Provenance | Source record |
|---|---|---|---|---|
| `aura-2.5.8` | Aura 2.5.8 | stable | `ANISOPRINT_OFFICIAL` | `AP-103` |
| `aura-2.6.2` | Aura 2.6.2 | Seeker main | `ANISOPRINT_OFFICIAL` | `AP-104` |
| `aura-2.6.1-sk3` | Aura 2.6.1 | Sk3 preview | `ANISOPRINT_OFFICIAL` | `AP-105` |
| `rocket-v13` | Rocket preset v13 | bundled | `FIBRESEEK_OFFICIAL` | `FS-121`, `FS-122` |
| `rocket-v15` | Rocket preset v15 | public | `FIBRESEEK_OFFICIAL` | `FS-125` |

`config/source_versions.json` is the authoritative input map. `generated/sources.json` adds acquisition timestamps, provenance, and an input-content hash.

## Entity observation

Each line in `generated/versions/*/entities.jsonl` is one source-native entity occurrence. The normative shape is `schemas/canonical-entity.schema.json`.

- `entity_record_id` identifies that observation and is a stable hash of source/version/location identity.
- `canonical_entity_id` uses a normalized UUID only when one is present. Non-UUID entities receive a source-scoped identity and are not cross-version matched.
- `original_entity_uuid`, `application_key`, `source_entity_type`, and `source_row_index` preserve native identity and location.
- `source_ids`, `provenance_class`, acquisition time, input path, and input hash retain provenance.
- `duplicate_in_source` preserves repeated UUID occurrences rather than merging them.
- `fields` retain original names and representations alongside cautious normalization.

## Field observation

Every field retains `original_field_name`, source-native `raw_value`, `base_value`, and `override_value`. `normalized_value` changes only representations justified by deterministic rules, currently UUID formatting. Aliases require entries in `registries/field_aliases.json`.

Units are independent assertions from `registries/unit_registry.json`:

- `known` + `FACT`: directly supported for that software.
- `inferred` + `INFERENCE`: supported only by lineage, never manufacturer-confirmed FibreSeek guidance.
- `unknown` + `OPEN_QUESTION`: no unit is populated.

## Base and override semantics

Base and override values are always preserved separately. A null override is distinguishable from no override field.

- A field without an override is `effective_value_status: known`.
- Aura override precedence has first-party documentation, but selecting a static record's effective value remains labeled `INFERENCE`.
- Rocket precedence was not recovered. Every override-capable Rocket field therefore has a null `effective_value` and `effective_value_status: unknown`, even when an override is non-null.

Example: profile UUID `d294a2dc-9d7f-460a-acf4-dc50b656d44a` stores `MacroLayerHeight` as Aura base/override `0.24/0.24`; Rocket v13 stores base/override `0.2/0.24`. The delta is both `value_changed` and `structurally_changed`; the engine does not claim Rocket's runtime value.

## Identity strategy

The generated identity graph follows the required evidence order:

1. `exact_uuid` links are generated across configured comparison pairs.
2. Native UUID-valued fields generate `explicit_foreign_key` relationships within a version.
3. No migration links were added without independent first-party support.
4. Names are never identity keys and never create links.

This makes the Seeker printer (`83bf1039-8c9e-49fc-928f-2f94a2008d40`), CFC extruder (`f3904c6f-c24e-4aff-ad9a-70405cc4df84`), and X-CCF composite (`2af8ac62-4968-4364-88e3-1045ef47feba`) directly traceable without conflating their manufacturer provenance.

## Delta semantics

`generated/deltas/*.jsonl` is derived from normalized observations. The engine supports `unchanged`, `value_changed`, `renamed`, `structurally_changed`, `added`, `removed`, `source_branch_changed`, and `unknown_correspondence`.

Field aliases are classified `INFERENCE` unless first-party evidence directly establishes them. Presence and raw value changes are `FACT` about the preserved stores, not facts about runtime behavior. The branch report records whether Rocket's exact UUID came from Aura 2.6.2, Sk3 preview, or both.

## Limitations

- Rocket runtime override precedence is unknown.
- `FiberSpoolLength` units remain unknown.
- Rocket `LinearDensity` and fiber extrusion-speed units are lineage inferences.
- Tetragrid, profile status/type, postprocessor, universal-slot, and edition numeric semantics remain unresolved.
- Non-UUID records are not name-matched, so some correspondence intentionally remains absent.
- Generated data excludes personal/application-state identifiers and Rocket navigation arrays; raw sources remain immutable on NAS.
