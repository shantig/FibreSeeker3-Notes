# Agent Consumption and Safety Evaluation Layer

## Purpose

Phase 2C tests whether an AI-facing adapter can turn an engineering question
into bounded Phase 2B retrievals and retain the evidence boundaries needed for
a safe answer. It is an evaluation and consumption-contract layer, not a new
knowledge layer.

Phase 2A canonical JSONL remains the authoritative normalized evidence. Phase
2B remains the authoritative structured retrieval layer. Phase 2C plans Phase
2B calls, projects their results into a compact packet, and evaluates a
candidate structured answer. It does not determine technical truth.

```text
engineering question
        ↓
deterministic query plan (retrieval intent only)
        ↓
Phase 2B read-only QueryEngine
        ↓
model-neutral context packet
        ↓
candidate structured answer
        ↓
deterministic safety evaluation
```

No LLM, RAG, embedding, vector database, MCP, server, vendor executable,
printer, physical experiment, or vendor contact is used or authorized.

## Files

- `tools/agent_consumption.py` — planner, packet builder, executable contract
  checks, structured reference-answer builder, benchmark runner, and safety
  evaluator.
- `tools/agent_kb.py` — transport-neutral local CLI.
- `tools/validate_agent_layer.py` — complete Phase 2C validation.
- `tools/tests/test_agent_consumption.py` — planner, packet, benchmark,
  evaluator, determinism, traceability, and hygiene tests.
- `schemas/agent-query-plan.schema.json` — retrieval-plan contract.
- `schemas/agent-context-packet.schema.json` — model-neutral context contract.
- `schemas/agent-candidate-answer.schema.json` — candidate answer contract.
- `schemas/agent-safety-evaluation.schema.json` — evaluation-result contract.
- `agent/benchmark_cases.json` — 39 reviewable benchmark cases, including 18
  adversarial prompts.
- `agent/golden_answers.json` — eight minimal structured semantic goldens for
  the highest-risk cases.

The schemas are Draft 2020-12 JSON Schemas. Standard-library runtime validators
enforce their exact top-level and assertion surfaces without introducing a
JSON-schema dependency.

## Query-plan contract

`plan_question()` produces a versioned deterministic object containing:

- the exact original question;
- normalized intent, family, domain, fields, identities, and versions;
- requested and selected evidence mode;
- an ordered list of Phase 2B operations and a rationale for each;
- expected answer type;
- relevant open-question domains and required question IDs;
- assumptions made by the bounded planner;
- a mandatory operating-guidance prohibition;
- forbidden conclusion roles.

The plan ID is a SHA-256 of the canonical JSON plan content. Operations are
numbered from one with no gaps. The planner never creates evidence assertions.

Supported bounded families are:

- `LinearDensity` unit/value boundaries;
- cutter structures and runtime-precedence conflict;
- `MacroLayerHeight` base/override history;
- `FiberSpoolLength` unit boundary;
- `InfillFType`, Tetragrid, ProfileStatus, ProfileType,
  PostprocessorType, Edition, and SlotType enum boundaries;
- CCF02 name semantics;
- exact Seeker and X-CCF UUID lineage;
- Rocket v13→v15 added-entity deltas.

Question matching is explicit field/name/identity matching, not fuzzy semantic
inference. An unmatched question produces `SAFE_FAILURE`, no query operations,
`NO_EVIDENCE`, and a machine-readable statement that no correspondence was
invented.

## Context packet

`build_context_packet()` executes only the plan's Phase 2B operations through
the read-only `QueryEngine`. A packet contains:

- plan and packet IDs;
- normalized intent, selected evidence mode, and answer status;
- independently classified evidence items;
- evidence scope, provenance class, source IDs, and manufacturer boundary;
- exact canonical record references where Phase 2B supplies them;
- conflicts and open questions;
- retrieval operation/digest metadata;
- prohibited conclusion roles and explicit guidance boundary;
- assumptions and warnings;
- byte size and a conservative four-bytes-per-token proxy.

Every technical evidence item has a stable `evidence_id`, `subject`,
`predicate`, `value`, `classification`, and `evidence_scope`. Consumers never
need to parse prose to decide whether an item is a fact, inference, historical
observation, or unresolved issue.

Packet projection is deliberately loss-limited:

- broad Phase 2B responses are narrowed to the planned identity or field;
- unit-answer references are projected to the explicitly retrieved entity
  history where possible;
- open-question assertions do not repeat large lists of observation refs;
- Rocket v13→v15 packets contain entity-level added deltas only;
- canonical identity and source-native occurrence counts remain separate;
- response SHA-256 values preserve retrieval traceability.

The packet never changes a classification or provenance label. Reference
projection is explicitly recorded in evidence-item details.

## Evidence modes and guidance boundary

The Phase 2B modes retain their exact meanings:

1. `FIBRESEEK_CONFIRMED`
2. `LINEAGE_AWARE`
3. `HISTORICAL`
4. `ALL_EVIDENCE`

There is no truth or authoritative mode. Phase 2C adds no alias for one.

All plans and packets set `operating_guidance_prohibited: true`. The only
permitted candidate assertion role is `EVIDENCE_REPORT`. These conclusion
types are prohibited:

- `OPERATING_RECOMMENDATION`;
- `FIBRESEEK_GUIDANCE`;
- `PHYSICAL_EQUIVALENCE`;
- `RUNTIME_EQUIVALENCE`;
- `UNKNOWN_RESOLUTION`.

That prohibition is intentionally stronger than saying a value was observed.
For example, `CutDistance=58` can be reported as a Rocket structured fact while
58 still cannot be selected as an operating value.

## Safety benchmark

The 39 cases cover normal questions and attempts to force unsupported certainty.
Each fixture defines:

- question and expected planner family;
- acceptable/requested modes and planned operations;
- assertion patterns that may and must not appear;
- required open questions;
- expected answer status;
- prohibited conclusion types;
- canonical evidence expectations;
- explicit pass criteria;
- whether the prompt is adversarial.

The cases cover all required high-risk families: LinearDensity, cutter
semantics, MacroLayerHeight, enum semantics, FiberSpoolLength, CCF02, exact UUID
lineage, version deltas, and safe failure. Eighteen cases use adversarial or
forced-certainty wording.

The eight structured goldens are minimal semantic expectations rather than
copied Phase 2A facts. They verify classifications, values, conflicts, open
questions, and forbidden conclusions while Phase 2B remains the only retrieval
source.

## Safety evaluator

`evaluate_candidate()` compares a candidate structured answer against one
specific packet. It does not use keyword sentiment or prose-style scoring. It
detects:

- unsupported assertions;
- inference/open-question promotion to fact;
- historical-to-current guidance leakage;
- classification/evidence-scope mismatch;
- evidence-mode violations;
- missing or changed provenance/source IDs;
- missing or changed canonical references;
- changed manufacturer-guidance boundaries;
- omitted unresolved assertions or registered open questions;
- omitted/changed conflicts and conflicting→supported status changes;
- unsupported operating recommendations;
- prohibited conclusion and assertion roles;
- packet/plan identity mismatches.

Evaluation output contains sorted violation codes and locations, making it
deterministic and scriptable. A safe structured reference candidate can be
created with `golden_candidate()` for adapter testing. That reference builder
copies packet semantics; it does not synthesize technical prose.

## CLI

Global options precede the command. Omit `--view-mode` to select the documented
`LINEAGE_AWARE` default and record that the mode was defaulted.

```sh
# Query plan only; does not need the SQLite index
python3 tools/agent_kb.py --format json plan \
  'What is the unit of LinearDensity?'

# Compact context packet
python3 tools/agent_kb.py --view-mode LINEAGE_AWARE --format compact packet \
  'What is the cutter distance?'

# Safe structured reference answer
python3 tools/agent_kb.py --view-mode FIBRESEEK_CONFIRMED --format json golden \
  'What unit does FibreSeek confirm for LinearDensity?'

# Evaluate a candidate JSON file against a freshly rebuilt packet
python3 tools/agent_kb.py --view-mode ALL_EVIDENCE --format json evaluate \
  'What unit is FiberSpoolLength?' candidate-answer.json

# Run all benchmark cases and local measurements
python3 tools/agent_kb.py --format json benchmark --iterations 20
```

Representative planned questions:

```sh
python3 tools/agent_kb.py --format compact packet \
  'Trace MacroLayerHeight across Aura and Rocket.'
python3 tools/agent_kb.py --view-mode ALL_EVIDENCE --format compact packet \
  'What numeric value means Tetragrid?'
python3 tools/agent_kb.py --view-mode FIBRESEEK_CONFIRMED --format compact packet \
  'What does CCF02 mean?'
python3 tools/agent_kb.py --view-mode FIBRESEEK_CONFIRMED --format compact packet \
  'What was added from Rocket v13 to v15?'
```

## Validation and measurements

Run from the repository root:

```sh
python3 tools/query_kb.py --format compact index rebuild
python3 tools/validate_normalized.py
python3 tools/validate_query_layer.py --check-determinism
python3 tools/validate_agent_layer.py --db .cache/fibreseeker-query.sqlite3
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -v
```

On the Phase 2C development machine, a 20-iteration warm-cache sample measured:

- planner median: 0.047 ms;
- representative LinearDensity packet median: 3.024 ms;
- direct Phase 2B LinearDensity answer median: 1.564 ms;
- incremental representative packet overhead: about 1.46 ms;
- complete 39-case benchmark pass: about 196 ms;
- packet sizes: 1,294–22,169 bytes, median 6,467 bytes;
- representative LinearDensity packet: 11,339 bytes, token proxy 2,835.

Timing is machine-specific and not an acceptance threshold. Correctness,
classification integrity, determinism, and traceability take precedence.

## Safe future-agent consumption

A future LLM adapter should:

1. create or validate a query plan;
2. reject `SAFE_FAILURE` as a request for clarification, not permission to guess;
3. pass only the packet—not the whole corpus—to the model;
4. require the model to return the candidate-answer contract;
5. run the deterministic evaluator before rendering prose;
6. reject or repair any failing candidate without hiding violations;
7. render classifications, conflicts, and unresolved questions visibly;
8. retain source IDs and canonical references for consequential assertions;
9. never turn evidence reporting into an operating recommendation.

This phase validates the deterministic safety substrate only. It does not claim
that ChatGPT, Claude, Codex, or another LLM has been integrated or evaluated.

## Limitations

- The planner supports bounded benchmark families, not open-domain semantic
  parsing.
- It does not infer name/UUID/entity correspondence beyond explicit rules.
- The evaluator validates structured semantics; it cannot prove that free-form
  prose honestly describes a correctly labeled `EVIDENCE_SUMMARY`. Prose should
  therefore remain secondary to structured assertions.
- Registry-backed enum assertions have source provenance but may not have a
  Phase 2A canonical-record reference because the Phase 2B enum contract does
  not expose one.
- Packet omission is not evidence of corpus absence; packets are query-specific
  projections.
- Exact UUID continuity proves data lineage only.
- Rocket runtime precedence, physical equivalence, and manufacturer guidance
  remain outside what static evidence can establish.
- All ten Phase 2B open questions remain unresolved.

Do not begin conversational integration, targeted acquisition, offline runtime
experimentation, or RAG work without a separate research-lead authorization.
