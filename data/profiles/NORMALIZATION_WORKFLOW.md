# Normalization Workflow

## Layout

- `config/source_versions.json`: version inputs, entity stores, comparisons, and branch comparison.
- `registries/field_aliases.json`: evidence-backed field-name mappings.
- `registries/unit_registry.json`: software-specific unit knowledge and manufacturer-guidance boundary.
- `registries/enum_registry.json`: version-aware enum meanings and explicit open questions.
- `schemas/`: canonical entity, identity-link, and field-delta contracts.
- `generated/versions/`: source observations.
- `generated/identity/`: exact-UUID continuity and native foreign keys.
- `generated/deltas/`: reproducible pair and branch comparisons.
- `generated/summary.json`: record counts and SHA-256 for every generated dependency file.

## Generate and validate

Run from the repository root with the NAS mounted:

```sh
python3 tools/generate_normalized.py
python3 tools/validate_normalized.py
python3 tools/generate_normalized.py --check
python3 -m unittest discover -s tools/tests -v
```

Generation reads immutable NAS inputs and replaces only `data/profiles/generated/`. Output ordering, identifiers, JSON serialization, and hashes are deterministic. `--check` generates into a temporary directory and byte-compares every output file.

## Query examples

The examples below are the Phase 2A direct-JSONL utility. New consumers should
use the Phase 2B evidence-safe CLI documented in `QUERY_LAYER.md`; the original
utility remains available for low-level inspection and regression comparison.

Trace X-CCF linear density:

```sh
python3 tools/query_normalized.py \
  --uuid 2af8ac62-4968-4364-88e3-1045ef47feba \
  --field LinearDensity
```

Trace CFC extruder cutter distance:

```sh
python3 tools/query_normalized.py \
  --uuid f3904c6f-c24e-4aff-ad9a-70405cc4df84 \
  --field CutDistance
```

Trace migrated profile base/override structure:

```sh
python3 tools/query_normalized.py \
  --uuid d294a2dc-9d7f-460a-acf4-dc50b656d44a \
  --field MacroLayerHeight
```

Trace the Seeker printer identity:

```sh
python3 tools/query_normalized.py \
  --uuid 83bf1039-8c9e-49fc-928f-2f94a2008d40
```

## Change procedure

1. Add or correct source metadata in the manifest before adding a source version.
2. Add the immutable NAS-relative input to `source_versions.json`.
3. Add aliases, units, or enums only with source IDs and evidence classification.
4. Regenerate, validate, run tests, and run `--check`.
5. Review generated deltas; never manually edit generated output.

No generator path executes vendor software or writes to the NAS.

## Phase 2B adapter

Build and validate the disposable query index without the NAS:

```sh
python3 tools/query_kb.py --format json index rebuild
python3 tools/validate_query_layer.py --check-determinism
python3 -m unittest discover -s tools/tests -v
```

The query index reads only committed canonical/registry/manifest inputs, is
ignored by Git, and never modifies `generated/`.
