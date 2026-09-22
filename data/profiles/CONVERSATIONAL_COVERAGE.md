# Phase 2E — Deterministic Conversational Coverage

## Purpose and status

Phase 2E adds structured conversational reference resolution and bounded
multi-intent composition above the accepted Phase 2D pipeline. It does not add
knowledge. Conversation may influence planning; it is never evidence.

Phase 2E is **ACCEPTED / COMPLETE**. The first same-model live comparison
validated the adapter/safety experiment but exposed a bounded decomposition
defect in `compare-01-supported`. The defect was corrected and regression-tested;
the corrected two-adapter live comparison completed successfully. The research
lead accepted Phase 2E on 2026-08-19.

## Architecture and trust boundary

```text
current user question + validated planning-only state
    -> deterministic mode/reference resolution
    -> deterministic bounded intent decomposition
    -> isolated branch N:
         Phase 2C plan -> Phase 2B retrieval -> Phase 2C packet
         -> Phase 2D model proposal/materialization/evaluator/repair
         -> deterministic branch render -> exact branch validation
    -> compose only branch renders that passed their existing gates
    -> exact composite-render validation
    -> next planning-only state from validated branches
```

`tools/conversation_composition.py` does not query technical evidence itself.
Each technical branch calls the existing `run_conversation()` path, which
freshly builds the Phase 2C plan and packet and applies the unchanged Phase 2C
evaluator and Phase 2D render gate. A branch cannot access another branch's
packet, candidate, conflicts, or open questions.

The following are never evidence:

- prior user, assistant, model, or rendered prose;
- conversation-state metadata or digests;
- provider conversation state;
- an LLM proposal or repair message;
- a generated summary of a prior turn.

Only Phase 2A canonical evidence retrieved through Phase 2B/2C can support a
technical assertion. The layer uses neither `previous_response_id` nor a
provider conversation object. OpenAI requests continue to set `store=false`
and include no tools.

## Versioned conversation state

`schemas/conversation-state.schema.json` defines state version `1.0.0`. State
contains only:

- a deterministic state ID;
- the current explicit evidence mode;
- validated-turn IDs and digests;
- normalized intent metadata (`family`, `fields`, `identities`, `versions`);
- plan, packet, and accepted-candidate digests/IDs;
- the active bounded referents;
- the literal boundary `PLANNING_METADATA_ONLY_NOT_EVIDENCE`.

It contains no question/answer prose, values, units, source IDs, provenance, or
canonical evidence references. Failed, rejected, and planner-`SAFE_FAILURE`
turns do not update referential authority. Mode-only turns update mode while
retaining the last validated referent.

A subjectless follow-up resolves only when exactly one active normalized intent
family exists. For example, `LinearDensity` followed by “What about Rocket?”
resolves to `linear_density` and performs a fresh retrieval. If the prior turn
established both `LinearDensity` and cutter semantics, “What about that?” is
rejected as `AMBIGUOUS` with no branch. “No, I meant CutDistance” is an explicit
correction to planning state; it does not revise canonical evidence.

Explicit modes are deliberately narrow:

- “Only show FibreSeek-confirmed evidence” selects `FIBRESEEK_CONFIRMED`;
- “Include historical evidence too” selects `ALL_EVIDENCE`;
- “show only historical evidence” selects `HISTORICAL`;
- “Go back to lineage-aware” selects `LINEAGE_AWARE`.

Vague wording such as “show stronger evidence” does not change mode.

## Multi-intent composition

The Phase 2E decomposer uses a bounded registry of the existing Phase 2C
families. It applies explicit field/entity/version patterns and deterministic
occurrence ordering; it uses no fuzzy, semantic, vector, or LLM matching.

Attribute-only conjunction fragments (`value`, `unit`, `evidence`, `history`,
and other bounded field-description terms) remain within an already recognized
intent. A fragment is still unsupported when it contains any substantive term
outside that closed attribute/filler vocabulary. Thus “value and unit evidence
for LinearDensity” is one branch, `LinearDensity and CutDistance` is two, and
`LinearDensity and mystery flux parameter` remains supported-plus-unknown.

Each branch independently retains:

- its normalized intent and evidence mode;
- its Phase 2C plan and packet IDs;
- its complete Phase 2D attempts, evaluator violations, and repair status;
- branch-local candidate assertions, conflicts, and open questions;
- its exact deterministic render and post-render validation.

Branch outcomes are `APPROVED`, `SAFE_FAILURE`, or `FAIL_CLOSED`. Composition
coverage is reported separately as `FULLY_COVERED`, `PARTIALLY_COVERED`,
`SAFE_FAILURE`, or `FAIL_CLOSED`. A failed branch cannot change another branch.
Partial success is rendered explicitly; rejected model content is never used.

`schemas/conversation-composition.schema.json` defines the composition envelope.
`validate_composite_render()` reconstructs the only permitted composite text
and branch-render manifest. Any changed text produces
`COMPOSITE_RENDER_TAMPERING`; manifest changes produce
`COMPOSITE_RENDER_MANIFEST_MISMATCH`.

## Coverage fixtures and offline results

`agent/conversational_coverage_cases.json` is explicitly classified
`EVALUATION_ARTIFACT_NOT_EVIDENCE`. It deterministically expands to 122 cases:

- 84 single-family paraphrase, terse, casing, forced-certainty, and
  classification-bypass variants;
- 20 explicit multi-turn sequences covering unique/ambiguous follow-ups,
  corrections, mode changes, spelling, incorrect premises, execution requests,
  recommendations, guesses, and equivalence traps;
- 18 two-/three-intent compounds, including mixed supported/unsupported cases.

Measured warm-index offline results:

| Coverage metric | Result |
| --- | ---: |
| Eligible cases | 122 |
| Fully covered | 116 |
| Partially covered | 2 |
| Deterministic `SAFE_FAILURE` | 4 |
| Incorrect decompositions | 0 |
| Incorrect reference resolutions | 0 |
| Expected ambiguities correctly rejected | 3/3 |

Safety remained independent of coverage:

- 141 branch attempts passed the unchanged Phase 2C evaluator;
- 0 post-render violations;
- 0 rejected claims reached user output;
- all 122 fixture expectations passed;
- all ten registered engineering questions remained unresolved.

The safe scripted fixture deliberately returns the deterministic complete packet
selection, so it produced no rejected attempts. Separate direct tests inject
unsupported/malformed/transport/tampered behavior and verify bounded repair or
failure closure.

## Determinism, size, and performance

Fixed state and model proposals produce byte-identical semantic projections,
state, branch order, and renders. Live timing and token metadata are excluded
from the deterministic projection.

On the implementation host with a warm disposable index:

- 122-case offline coverage evaluation: 1,228.700 ms, 10.071 ms/case mean;
- bounded decomposition: 0.276 ms median over 50 runs;
- representative two-branch end-to-end safe offline turn: 15.958 ms median;
- representative packets: 11,339 and 14,900 bytes;
- resulting planning-only state: 1,626 bytes;
- resulting deterministic composite render: 5,636 bytes.

These numbers measure local deterministic/scripted work, not live-model latency.

## Provider usage contract and comparison

The committed Phase 2D `llm-model-result.schema.json` remains version `1.0.0`
and historical `agent/live_evaluation_results.json` remains unchanged and valid.
Phase 2E adds `llm-model-result-v2.schema.json`. Its usage object adds nullable:

- `cached_input_tokens` from `input_tokens_details.cached_tokens`;
- `reasoning_tokens` from `output_tokens_details.reasoning_tokens`.

Absent detail stays `null`; it is not inferred. The existing input, output, and
total fields are preserved. This follows the official Responses usage shape:
<https://developers.openai.com/api/reference/java/resources/responses/methods/compact>.

`agent/adapter_comparison_cases.json` defines eight representative cases with
the fixed `gpt-5.4` model, same semantic branch requests, one repair attempt,
no tools, and `store=false`. `tools/compare_live_adapters.py` records input,
cached input, output, reasoning, and total tokens; model/end-to-end/local
latency; schema and safety pass rates; repair rate; final validation; and exact
violation counts. It calculates no cost.

### First live run and retained defect finding

The first live comparison used both adapters with `gpt-5.4`. Both produced 8/8
final evaluator-approved, post-render-valid answers and preserved identical
semantic plan/packet requests. It also honestly reported 7 fully covered cases
and one partially covered case per adapter. `compare-01-supported` incorrectly
split “What value and unit evidence exists for LinearDensity?” into
`linear_density` plus `unknown`.

| First run | Codex Exec | Responses |
| --- | ---: | ---: |
| First-pass schema valid | 8/8 | 8/8 |
| First-pass Phase 2C safe | 6/8 | 5/8 |
| Repairs | 2/8 | 3/8 |
| Final validated | 8/8 | 8/8 |
| Post-render valid | 8/8 | 8/8 |
| Fully / partially covered | 7 / 1 | 7 / 1 |
| Input tokens | 193,186 | 54,238 |
| Cached input tokens | 96,256 | 19,200 |
| Output tokens | 10,085 | 8,422 |
| Total tokens | 203,271 | 62,660 |
| Median model latency | 18,447.638 ms | 4,906.604 ms |
| Median end-to-end latency | 19,814.842 ms | 6,407.481 ms |

The deterministic gates rejected one unsupported assertion and two unsupported
conflict IDs on Codex Exec, and two unsupported assertions and two unsupported
conflict IDs on Responses. Every rejected proposal was repaired; none reached
rendering. Reasoning-token metadata was reported as zero on both adapters. No
cost was inferred.

The finding is not overwritten: it motivated the closed-vocabulary
attribute-fragment correction and four direct regression tests. The fixed
eight-case offline comparison is now 8/8 `FULLY_COVERED` for both deterministic
adapter instances, with identical semantic requests.

### Corrected live comparison — accepted result

The corrected run is a sanitized aggregate classified
`EVALUATION_ARTIFACT_NOT_EVIDENCE`. It used the same eight semantic requests,
explicit `gpt-5.4`, one repair attempt, `store=false`, no tools, and no provider
conversation state. `same_semantic_requests_verified` was `true`.

The planner correction behaved as intended:

- `compare-01-supported` produced exactly one `linear_density` branch and was
  `FULLY_COVERED` on both adapters;
- genuine multi-intent `compare-08-multi` remained two isolated branches;
- all eight cases were fully covered by the deterministic planner.

| Corrected run | Codex Exec | Direct Responses |
| --- | ---: | ---: |
| Case count | 8 | 8 |
| First-pass schema valid | 8/8 | 8/8 |
| First-pass Phase 2C safe | 6/8 | 5/8 |
| Repairs attempted | 2/8 | 3/8 |
| Final approved/validated answers | 8/8 | 6/8 |
| Safe `FAIL_CLOSED` | 0/8 | 2/8 |
| Post-render valid | 8/8 | 8/8 |
| Input tokens | 180,304 | 49,319 |
| Cached input tokens | 94,336 | 37,376 |
| Output tokens | 10,088 | 7,678 |
| Total tokens | 190,392 | 56,997 |
| Median model latency | 19,538.424 ms | 4,543.825 ms |
| Median end-to-end latency | 19,011.357 ms | 6,250.266 ms |

Codex Exec proposals produced two `UNSUPPORTED_CONFLICT` violations. Both were
contained and repaired. Direct Responses proposals produced five
`UNSUPPORTED_ASSERTION` and one `UNSUPPORTED_CONFLICT` violations.
`compare-03-override` and `compare-05-best-guess` remained safely
`FAIL_CLOSED` after the single bounded repair. No rejected claim from either
adapter reached user-facing output.

The two Responses fail-closed cases are availability/reliability failures, not
safety failures: the deterministic architecture withheld unvalidated answers
and emitted post-render-valid safe results. No additional retry or architectural
change was introduced to manufacture an 8/8 availability result.

Structured schema validity was 100% for both adapters, while evidence/domain
validity still required the Phase 2C evaluator. Relative to Codex Exec, direct
Responses reduced input tokens by approximately 72.6% and total tokens by
approximately 70.1%. Its median model latency was approximately 4.30 times
faster and median end-to-end latency approximately 3.04 times faster. These
same-model results support the bounded inference that Phase 2D's very large
token use was primarily Codex runtime/envelope overhead rather than intrinsic
KB packet size.

This eight-case run does not establish provider-independent model reliability.
The original defect-bearing live run above remains historical evaluation
evidence and is not overwritten by the corrected result.

## Validation commands

```sh
PYTHONPYCACHEPREFIX=/private/tmp/fibreseeker-pycache python3 -m unittest discover -s tools/tests -p 'test_*.py'
PYTHONPYCACHEPREFIX=/private/tmp/fibreseeker-pycache python3 tools/validate_normalized.py
PYTHONPYCACHEPREFIX=/private/tmp/fibreseeker-pycache python3 tools/validate_query_layer.py --check-determinism
PYTHONPYCACHEPREFIX=/private/tmp/fibreseeker-pycache python3 tools/validate_agent_layer.py
PYTHONPYCACHEPREFIX=/private/tmp/fibreseeker-pycache python3 tools/validate_llm_layer.py
PYTHONPYCACHEPREFIX=/private/tmp/fibreseeker-pycache python3 tools/validate_conversation_layer.py
```

## Limitations

- The planner covers a bounded registry, not open-domain language.
- `Rocket`/`Aura` subjectless follow-ups select a uniquely known subject family;
  version-specific filtering remains whatever the existing Phase 2C family
  contract retrieves. Conversation never supplies missing evidence.
- Coverage failures are reported, not repaired with fuzzy matching.
- Live reliability conclusions are limited to this eight-case, same-model run.
- This phase validates no provider-independent performance, RAG need, runtime
  behavior, hardware behavior, or manufacturer recommendation.
- Canonical evidence did not change, and no unresolved engineering question was
  resolved.
