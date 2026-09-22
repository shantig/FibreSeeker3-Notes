# Evidence-Safe Query Layer

## Purpose

Phase 2B adds a deterministic local adapter over the Phase 2A canonical JSONL.
It makes technical evidence queryable without creating a second authoritative
fact store. The canonical JSONL, identity graph, delta JSONL, registries, and
source manifest remain authoritative; SQLite is disposable.

The architecture is:

```text
canonical JSONL + registries + source metadata
                    ↓
       deterministic SQLite adapter
                    ↓
       evidence-safe Python query API
                    ↓
       CLI human view / stable JSON
                    ↓
         future agent/RAG adapters
```

No vendor executable, hardware, web service, vector database, embedding
pipeline, MCP server, or application-state database is used.

## Files

- `tools/query_engine.py` — index builder and Python query API.
- `tools/query_kb.py` — documented CLI.
- `tools/validate_query_layer.py` — provenance, safety, canonical-reference,
  conflict, compact-output, and deterministic-rebuild validation.
- `tools/tests/test_query_engine.py` — 10 golden queries plus invariants.
- `schemas/query-contract.schema.json` — stable query response contract.
- `schemas/engineering-answer.schema.json` — structured answer contract.
- `query/question_registry.json` — unresolved-question metadata and evidence
  needed for resolution; it contains no promoted answers.

The default index is `.cache/fibreseeker-query.sqlite3`. It is ignored by Git
because it is a generated 109 MB adapter, rebuilds in about 7.5 seconds on the
Phase 2B development machine, and must never be treated as authoritative.

## Build and validation

From the repository root:

```sh
python3 tools/query_kb.py --format json index rebuild
python3 tools/validate_query_layer.py --check-determinism
python3 -m unittest discover -s tools/tests -v
```

`index build` and every normal query compare the stored input digest with the
current canonical inputs. A missing or stale index is regenerated. Rebuilding
starts with a new database file, inserts records in canonical sort order, uses
fixed SQLite settings, and produces byte-identical output for identical inputs.

The index stores canonical paths and SHA-256 hashes for entity, identity,
relationship, and delta records. Query results therefore resolve back to exact
canonical JSONL records. All 162 manifest source IDs are resolvable. Source
records intentionally omit NAS `local_path`; only safe acquisition and
provenance metadata enters the adapter. Source
responses cap the expanded reverse-reference list at 200 entries and report
`reference_count` plus `references_truncated` to avoid dumping a large fraction
of the corpus into an agent context.

## View modes

Every evidence query accepts `--view-mode`.

| Mode | Included evidence | Safety behavior |
|---|---|---|
| `FIBRESEEK_CONFIRMED` | Direct Rocket/FibreSeek observations and explicitly unresolved FibreSeek boundaries | Excludes Aura records and inference assertions. Nested inferred unit/alias semantics are filtered rather than relabeled. |
| `LINEAGE_AWARE` | FibreSeek observations plus labeled Aura ancestors, exact-UUID links, and lineage inferences | Every assertion retains classification and provenance; Aura is historical support, never FibreSeek guidance. |
| `HISTORICAL` | Legacy Aura/Anisoprint observations and semantics | Labels every result `HISTORICAL_ANISOPRINT`. |
| `ALL_EVIDENCE` | All observations, inferences, conflicts, and open questions | Does not raise confidence or select a preferred conflicting value. |

There is deliberately no `truth` or `authoritative` mode.

Each result has machine-readable `classification` and `evidence_scope`:

- `FACT` + `FIBRESEEK_FIRST_PARTY`
- `FACT` + `HISTORICAL_ANISOPRINT`
- `INFERENCE` + `LINEAGE_INFERENCE`
- `OPEN_QUESTION` + `UNRESOLVED`
- `EXPERIMENTAL` + `EXPERIMENTAL` when future separately authorized evidence exists

The labels are not prose. Agents must branch on them directly.

## Query contract

Normal queries return:

```json
{
  "contract_version": "1.0.0",
  "query": {"operation": "field"},
  "view_mode": "LINEAGE_AWARE",
  "result_count": 4,
  "results": [
    {
      "kind": "field_observation",
      "classification": "FACT",
      "evidence_scope": "FIBRESEEK_FIRST_PARTY",
      "provenance_class": "FIBRESEEK_OFFICIAL",
      "source_ids": ["FS-125"],
      "manufacturer_guidance": "not_operating_recommendation",
      "canonical_ref": {
        "path": "data/profiles/generated/versions/rocket-v15/entities.jsonl",
        "record_id": "entity:…#CutDistance",
        "record_sha256": "…"
      },
      "payload": {}
    }
  ],
  "warnings": [],
  "index": {"schema_version": "1.0.0", "input_digest": "…"}
}
```

Entity and field payloads expose canonical identity, source-native identity,
entity type, software/version/branch, raw/base/override/effective-value
structure, unit status and classification, source IDs, acquisition/input
metadata, and canonical reference.
Delta, source, enum, relationship, and question payloads expose their native
structured semantics without requiring prose parsing.

Use `--format compact` for deterministic single-line JSON and `--format json`
for indented JSON. `--format text` is only a human convenience view.

## Engineering answer object

`answer unit`, `answer cutter-distance`, and `answer field` return the separate
engineering-answer contract. It contains:

- `answer_status`: `SUPPORTED`, `CONFLICTING`, `UNRESOLVED`, or `NO_EVIDENCE`;
- independently classified `assertions`;
- visible `conflicts` rather than one selected scalar;
- relevant `open_questions` and resolution requirements;
- `operating_recommendation: null` for this evidence-only phase.

For `LinearDensity`, `LINEAGE_AWARE` returns the historical Aura `tex` fact,
the absence of a recovered Rocket unit label, the Rocket `tex` lineage
inference, and the unresolved FibreSeek-confirmed unit as separate assertions.
`FIBRESEEK_CONFIRMED` omits the Aura fact and lineage inference.

For cutter distance, the answer preserves Rocket `CutDistance=58`,
`FiberRestartLength=55`, and the `CutCode` comment `54.8` separately. Runtime
precedence remains an open question and no operating value is emitted.

## CLI reference

Global options precede the command:

```sh
python3 tools/query_kb.py \
  --view-mode LINEAGE_AWARE \
  --format compact \
  COMMAND
```

### Entity and lineage

```sh
# One entity across versions
python3 tools/query_kb.py --format json entity \
  83bf1039-8c9e-49fc-928f-2f94a2008d40

# Exact UUID lineage
python3 tools/query_kb.py --format json lineage \
  2af8ac62-4968-4364-88e3-1045ef47feba

# Entity plus native foreign-key graph
python3 tools/query_kb.py --format json entity \
  2af8ac62-4968-4364-88e3-1045ef47feba --graph
```

### Fields

```sh
# CutDistance history
python3 tools/query_kb.py --format json field CutDistance \
  --identity f3904c6f-c24e-4aff-ad9a-70405cc4df84

# LinearDensity value and unit boundary
python3 tools/query_kb.py --format json answer unit LinearDensity

# MacroLayerHeight base/override history
python3 tools/query_kb.py --format json field MacroLayerHeight \
  --identity d294a2dc-9d7f-460a-acf4-dc50b656d44a
```

### Deltas

```sh
# Rocket v13 → v15
python3 tools/query_kb.py --format compact delta rocket-v13 rocket-v15

# Only entity/profile additions
python3 tools/query_kb.py --format json delta rocket-v13 rocket-v15 \
  --classification added --entity-type profile

# One field delta
python3 tools/query_kb.py --format json delta aura-2.6.1-sk3 rocket-v13 \
  --identity d294a2dc-9d7f-460a-acf4-dc50b656d44a \
  --field MacroLayerHeight
```

### Sources, enums, and open questions

```sh
python3 tools/query_kb.py --format json source FS-125
python3 tools/query_kb.py --format json enum InfillFType
python3 tools/query_kb.py --format json questions
python3 tools/query_kb.py --format json questions --domain materials
python3 tools/query_kb.py --format json questions \
  --requirement VENDOR_CONFIRMATION
```

The question registry currently exposes 10 unresolved issues, including
`FiberSpoolLength`, Rocket override precedence, Tetragrid, profile status/type,
postprocessor, edition, universal-slot semantics, CCF02, and cutter runtime
precedence. Resolution requirements are limited to evidence-supported
`STATIC_FIRST_PARTY`, `VENDOR_CONFIRMATION`, or `OFFLINE_RUNTIME_TEST`. None of
the current questions invents a hardware experiment as the resolution path.
When a field filter names a Rocket base/override field with unknown effective
status, the override-precedence question is associated dynamically even though
the registry correctly applies it to a field family rather than one copied list.

### High-value engineering views

```sh
python3 tools/query_kb.py --format compact view machine --version rocket-v15
python3 tools/query_kb.py --format compact view materials --version rocket-v15
python3 tools/query_kb.py --format compact view profiles --version rocket-v15
python3 tools/query_kb.py --format compact view lineage \
  --identity 2af8ac62-4968-4364-88e3-1045ef47feba
python3 tools/query_kb.py --format compact material \
  2af8ac62-4968-4364-88e3-1045ef47feba
python3 tools/query_kb.py --format compact profile \
  d294a2dc-9d7f-460a-acf4-dc50b656d44a
```

The machine view selects geometry, extruders, nozzle/temperature, travel,
acceleration, slot, and cutter fields. Materials selects plastics, composites,
temperature, extrusion, density, spool, and compatibility relationships.
Profiles selects groups, associations, base/override fields, layer/path,
reinforcement, angle, speed, tension, pattern, and macrolayer fields. These are
query projections; no parallel fact tables are maintained. Bulk engineering
views default to 25 entities. Profile projections sample each required field
family and report `matching_field_count`, `selected_field_count`, and
`fields_truncated`; agents should narrow by identity/name before requesting more.
Relationship graphs similarly cap root/related field payloads while retaining
all graph edges and explicit truncation metadata. The `material` and `profile`
commands follow at most two explicit foreign-key hops so an association can
reach its related profile or material; names never create those edges.

### Structured answers and performance

```sh
python3 tools/query_kb.py --format compact answer cutter-distance
python3 tools/query_kb.py --format compact answer field MacroLayerHeight \
  --identity d294a2dc-9d7f-460a-acf4-dc50b656d44a
python3 tools/query_kb.py --format json benchmark --iterations 20
```

## Safe agent consumption

Future agents should:

1. choose an explicit view mode;
2. request only the entity, field, delta, material/profile graph, or questions
   needed for the current answer;
3. branch on `classification`, `evidence_scope`, unit classification, and
   effective-value status;
4. cite `source_ids` and retain `canonical_ref` for audit;
5. keep every conflict and open question visible;
6. never convert `LINEAGE_INFERENCE` into FibreSeek guidance;
7. never choose an effective Rocket override or cutter value when status is
   unresolved;
8. never emit an operating recommendation from this layer.

The compact responses are intended to prevent a downstream agent from loading
the entire 45,721-field corpus into context.

## Limitations

- SQLite is a generated adapter, not an evidence source.
- Exact UUID continuity proves data identity, not runtime consumption or
  physical behavior.
- Rocket base/override precedence is still unknown.
- The index cannot resolve unsupported units or enums.
- Name lookup is a convenience filter and never creates identity links.
- High-value views use explicit field-name projections; absence from a view is
  not evidence that a canonical field does not exist.
- Phase 2B itself contains no agent planner/evaluator, vector, embedding,
  server, or execution layer. The separately authorized deterministic Phase 2C
  consumption/evaluation adapter is documented in `AGENT_CONSUMPTION.md`.
