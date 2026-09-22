# Phase 2D conversational integration and live LLM evaluation

## Purpose and measured scope

Phase 2D tests whether a real language model can participate in a bounded
FibreSeeker-KB conversation without an unsupported engineering claim reaching
the user. The model is an untrusted selector, not evidence and not a fact store.
Phase 2A remains the canonical evidence layer, Phase 2B remains the retrieval
layer, and Phase 2C remains the planning, packet, candidate, and evaluation
authority.

The committed live evaluation used the isolated `codex-exec-v1` adapter with
the explicit OpenAI model identifier `gpt-5.4`. It evaluated all 39 Phase 2C
cases, including all 18 adversarial cases. These results describe this pipeline,
model, prompt, fixture set, and run only. They are not a general claim of model
reliability or “safe AI.”

## Pipeline and trust boundaries

```text
question
  -> deterministic Phase 2C plan
  -> deterministic Phase 2B retrieval
  -> deterministic Phase 2C packet
  -> untrusted structured model proposal
  -> deterministic packet-backed Phase 2C candidate materialization
  -> mandatory Phase 2C evaluator
  -> at most one repair by default
  -> deterministic renderer
  -> exact post-render validation
  -> approved answer or deterministic fail-closed result
```

The LLM receives one question, its selected evidence mode, one Phase 2C packet,
the response contract, and the evidence rules. It does not receive the corpus,
the SQLite index, repository paths, prior free-form conversation, tools, or an
alternate retrieval path. The Codex CLI live adapter runs in an ephemeral empty
directory under a read-only command sandbox. Any observed tool event is a
deterministic failure.

No provider output becomes canonical evidence. The committed live result is
explicitly labeled `EVALUATION_ARTIFACT_NOT_EVIDENCE`.

## Provider-neutral adapter

`tools/llm_adapter.py` defines the replaceable interface:

```python
class ModelAdapter:
    @property
    def info(self) -> ModelAdapterInfo: ...

    def complete_structured(self, request: dict) -> dict: ...
```

The normalized result records provider, adapter and model identifiers; request
and packet IDs; prompt/format versions; attempt; latency; token usage when
available; provider status; parse/schema status; sanitized error state; and
whether a tool event occurred. It deliberately has no raw-response or prompt-log
field.

Implemented adapters are:

- `ScriptedModelAdapter`: deterministic offline fixtures; never a live-result
  substitute.
- `OpenAIResponsesAdapter`: standard-library HTTPS adapter using Responses API
  Structured Outputs and `store=false`; requires `OPENAI_API_KEY`.
- `CodexExecAdapter`: isolated live adapter for an existing local Codex login;
  requires an explicit model ID and rejects tool use.

The OpenAI SDK is not a core dependency. The Responses adapter follows the
official structured-output form, `text.format.type=json_schema`.

## Request and candidate contracts

The Phase 2D schemas are:

- `schemas/llm-request.schema.json`
- `schemas/llm-candidate-proposal.schema.json`
- `schemas/llm-model-result.schema.json`
- `schemas/llm-run.schema.json`

The model response is a compact reference-form proposal. It selects packet
evidence IDs and repeats their classification, evidence scope, and claim role;
it also selects conflict IDs and open-question IDs, preserves answer status,
and exposes any attempted conclusion or operating recommendation. This is the
model's only generative decision surface.

The deterministic materializer copies the selected subject, predicate, value,
unit, provenance, source IDs, canonical references, and manufacturer boundary
from the packet into the unchanged Phase 2C candidate-answer contract. The
model therefore cannot generate a new technical value or provenance record for
an accepted candidate. Unknown IDs are rejected. This reference-form step is a
compact transport extension; the object sent to the authoritative evaluator is
the exact Phase 2C `1.0.0` candidate contract.

Request IDs, repair requests, candidate materialization, evaluator input,
rendering, post-render validation, and scoring are deterministic for fixed
structured inputs. Live latency, usage, provider IDs, and model selections are
kept outside the deterministic semantic projection.

## Mandatory evaluator and bounded repair

There is no evaluation bypass. The materialized candidate is always passed to
Phase 2C `evaluate_candidate()` before rendering. That gate continues to detect:

- inference-to-fact promotion;
- historical-to-current guidance leakage;
- unsupported evidence IDs or altered values;
- unresolved-assertion and open-question omission;
- conflict collapse;
- unsupported operating recommendations;
- evidence-mode, classification, and scope mismatches;
- provenance, source-ID, canonical-reference, and manufacturer-boundary loss;
- physical/runtime equivalence and unknown-resolution roles.

The default repair limit is one. A repair request contains the unchanged packet,
the rejected structured candidate when one could be materialized, the exact
sorted deterministic violations, and an instruction to correct those violations
only. The repair cannot add evidence. If repair is unavailable or fails, the
pipeline returns `FAIL_CLOSED`; rejected model text is never rendered.

## Rendering and post-render safety

Rendering is not delegated to an LLM. The renderer groups accepted assertions
by evidence scope and mechanically emits their classification, subject,
predicate, value, unit, source IDs, canonical-reference count, and manufacturer
boundary. Conflicts and open questions have separate sections. The final
boundary explicitly says that historical evidence and lineage inference are not
FibreSeek guidance, UUID continuity is not physical/runtime equivalence, and
unknowns remain unresolved.

Each rendered claim has a manifest entry tied to its accepted assertion and a
sentence hash. Post-render validation reconstructs the only permitted output
from the candidate and requires an exact structured match. A changed sentence,
claim manifest, conflict set, question set, status, or boundary fails. A
fail-closed rendering has no technical claim manifest and never includes the
rejected response.

## Live benchmark results

Sanitized case-level results are in
`agent/live_evaluation_results.json`. No raw model text, provider response ID,
prompt log, secret, or account identifier is retained.

| Metric | Result |
|---|---:|
| Cases | 39 |
| Adversarial cases | 18 |
| First-pass JSON-schema-valid | 39/39 (100%) |
| First-pass Phase 2C safety pass | 33/39 (84.6154%) |
| Repairs attempted | 6 |
| Repairs successful | 6/6 (100%) |
| Final validated answers | 39/39 (100%) |
| Final fail-closed | 0/39 (0%) |
| Benchmark fidelity pass | 39/39 (100%) |
| Post-render validation pass | 39/39 (100%) |
| Planner `SAFE_FAILURE` | 4/39 (10.2564%) |

The six rejected first passes were five `UNSUPPORTED_CONFLICT` identifiers in
the cutter family and one `UNSUPPORTED_ASSERTION` identifier in an adversarial
MacroLayerHeight case. All were structurally valid JSON, but they did not
resolve to packet IDs. The deterministic gate rejected them, the single repair
attempt corrected them, and none reached the renderer. No inference promotion,
historical-guidance leak, recommendation, uncertainty omission, conflict
collapse, equivalence claim, evidence-mode violation, or post-render violation
survived into an approved answer.

The live run made 45 model calls and reported 711,083 input tokens, 34,670
output tokens, and 745,753 total tokens. Provider metadata did not expose a
billable cost, so approximate cost is recorded as `null` rather than inferred.

Model-call latency was 7,904–32,417 ms, with a 17,849 ms median and 28,013 ms
p95. End-to-end case latency was 7,908–58,290 ms, with a 17,814 ms median and
57,895 ms p95; repaired cases include two calls. Deterministic local overhead
computed per case after subtracting model-call latency was 3.126–72.693 ms,
with a 9.474 ms median.

Packets were 1,294–22,169 bytes (median 6,467), approximately 324–5,543 tokens
by the Phase 2C four-bytes-per-token proxy (median 1,617). Provider input usage
is much larger because it also includes the provider's agent/runtime instruction
envelope; that overhead is a measured limitation of the evaluated CLI adapter,
not packet growth.

## Conversational coverage

Phase 2E supersedes the limited behavior described in this Phase 2D section.
See `CONVERSATIONAL_COVERAGE.md` for validated planning-only state, unique
subjectless resolution, isolated multi-intent composition, and the expanded
122-case evaluation. The Phase 2D artifact and behavior below remain historical
baseline documentation.

`agent/conversational_cases.json` adds 16 small offline variants covering
paraphrase, terse wording, spelling variation, explicit and implicit follow-up,
forced certainty, incorrect premises, ignored classifications, best guesses,
lineage-as-equivalence, prohibited execution, and a two-family question.

Technical claims are always replanned and freshly retrieved. A prior turn may
contribute only the digest of a validated structured candidate; prior prose is
not evidence. An explicit follow-up such as “what does Rocket say about
LinearDensity?” replans successfully. An implicit “what about Rocket?” safely
fails because Phase 2D does not invent the omitted subject. A combined
LinearDensity/cutter question currently follows the planner's first bounded
match and is marked as partial coverage in the fixture; multi-intent planning
is not silently inferred.

## Commands

Offline validation, with no live credentials or cost:

```sh
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/validate_normalized.py
python3 tools/validate_query_layer.py --check-determinism
python3 tools/validate_agent_layer.py
python3 tools/validate_llm_layer.py
```

One live question through an existing local Codex login:

```sh
python3 tools/chat_kb.py \
  --adapter codex-cli --model gpt-5.4 \
  --view-mode LINEAGE_AWARE \
  "What is the unit of LinearDensity?"
```

OpenAI Responses API use requires a local environment variable; never write it
to the repository:

```sh
export OPENAI_API_KEY='...'
python3 tools/chat_kb.py \
  --adapter openai-responses --model YOUR_EXPLICIT_MODEL_ID \
  --view-mode FIBRESEEK_CONFIRMED \
  "What unit does FibreSeek confirm for LinearDensity?"
```

The full live benchmark is intentionally explicit so ordinary tests cannot
incur API usage:

```sh
python3 tools/evaluate_live_agent.py \
  --adapter codex-cli --model gpt-5.4 \
  --output /private/tmp/fibreseeker-live-eval.json
```

## Limitations and implications

- Only one provider path and one exact model identifier were tested. Provider-
  independent performance is not claimed.
- The live adapter's surrounding runtime instruction overhead is substantial.
- The bounded planner has expected `SAFE_FAILURE` behavior and only partial
  multi-intent/follow-up coverage. This does not establish a need for RAG;
  targeted planner coverage can be evaluated first.
- Deterministic materialization intentionally limits model freedom. It proves
  evidence-safe participation, not open-domain conversational competence.
- Ten registered engineering questions remain unresolved. The LLM run resolved
  none of them.
- The benchmark cannot prove absence of every possible failure; it proves that
  the specified violations are mechanically excluded in this evaluated path.

Phase 2D added no RAG, embeddings, vector database, MCP, server, Rocket/Aura
execution, hardware access, physical experiment, vendor contact, or autonomous
operating recommendation. It does not authorize a next phase.
