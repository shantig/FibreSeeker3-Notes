import copy
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from agent_consumption import build_context_packet, plan_question  # noqa: E402
from conversation_composition import (  # noqa: E402
    decompose_question,
    deterministic_composition_projection,
    empty_state,
    run_composed_turn,
    validate_composite_render,
    validate_state,
)
from conversational_kb import safe_proposal  # noqa: E402
from evaluate_conversation_coverage import evaluate_coverage, load_cases  # noqa: E402
from llm_adapter import (  # noqa: E402
    RESULT_VERSION_V2,
    ModelAdapterInfo,
    OpenAIResponsesAdapter,
    ScriptedModelAdapter,
    model_result,
    validate_model_result,
)
from query_engine import QueryEngine, build_index, canonical_json  # noqa: E402


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class ConversationCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="fibreseeker-phase2e-tests-")
        cls.db = Path(cls.temporary.name) / "query.sqlite3"
        build_index(REPO, cls.db)
        cls.engine = QueryEngine(REPO, cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()
        cls.temporary.cleanup()

    def adapter(self):
        return ScriptedModelAdapter(lambda request: safe_proposal(request["input"]["context_packet"]))

    def turn(self, question, state=None, adapter=None, repairs=1):
        return run_composed_turn(
            self.engine, adapter or self.adapter(), question, state,
            max_repair_attempts=repairs,
        )

    def test_01_state_is_versioned_deterministic_and_planning_only(self):
        first = empty_state()
        second = empty_state()
        self.assertEqual(canonical_json(first), canonical_json(second))
        validate_state(first)
        serialized = canonical_json(first)
        for forbidden in ('"answer"', '"value"', '"unit"', '"source_ids"', '"canonical_refs"'):
            self.assertNotIn(forbidden, serialized)

    def test_02_unique_referent_recovery(self):
        first = self.turn("What unit is LinearDensity?")
        second = self.turn("What about Rocket?", first["updated_state"])
        self.assertEqual(second["reference_resolution"]["status"], "RESOLVED")
        self.assertEqual([item["planner_family"] for item in second["branches"]], ["linear_density"])
        self.assertEqual(second["updated_state"]["active_referents"]["versions"], ["rocket"])

    def test_03_ambiguous_referent_is_rejected(self):
        first = self.turn("LinearDensity and CutDistance?")
        second = self.turn("What about that?", first["updated_state"])
        self.assertEqual(second["reference_resolution"]["status"], "AMBIGUOUS")
        self.assertEqual(second["branches"], [])
        self.assertEqual(second["coverage"]["status"], "SAFE_FAILURE")

    def test_04_state_is_produced_only_from_validated_turn(self):
        initial = empty_state()
        failed = self.turn(
            "What unit is LinearDensity?", initial,
            ScriptedModelAdapter(["bad", "bad"]),
        )
        self.assertEqual(failed["updated_state"], initial)

    def test_05_safe_failure_does_not_become_referential_authority(self):
        first = self.turn("Mystery quantum nozzle?")
        self.assertEqual(first["updated_state"]["active_referents"]["families"], [])
        second = self.turn("What about Rocket?", first["updated_state"])
        self.assertEqual(second["reference_resolution"]["status"], "AMBIGUOUS")

    def test_06_explicit_correction_changes_referent_not_evidence(self):
        first = self.turn("What unit is LinearDensity?")
        corrected = self.turn("No, I meant CutDistance.", first["updated_state"])
        self.assertEqual(corrected["branches"][0]["resolution"], "EXPLICIT_CORRECTION")
        self.assertEqual(corrected["updated_state"]["active_referents"]["families"], ["cutter_semantics"])

    def test_07_explicit_evidence_mode_transitions(self):
        first = self.turn("What unit is LinearDensity?")
        confirmed = self.turn("Only show FibreSeek-confirmed evidence.", first["updated_state"])
        self.assertEqual(confirmed["evidence_mode"], "FIBRESEEK_CONFIRMED")
        self.assertEqual(confirmed["branches"], [])
        history = self.turn("Include historical evidence too.", confirmed["updated_state"])
        self.assertEqual(history["evidence_mode"], "ALL_EVIDENCE")
        lineage = self.turn("Go back to lineage-aware.", history["updated_state"])
        self.assertEqual(lineage["evidence_mode"], "LINEAGE_AWARE")

    def test_08_vague_mode_wording_does_not_change_mode(self):
        initial = empty_state()
        result = self.turn("Show stronger evidence.", initial)
        self.assertEqual(result["evidence_mode"], "LINEAGE_AWARE")
        self.assertEqual(result["coverage"]["status"], "SAFE_FAILURE")

    def test_09_two_intent_decomposition(self):
        result = self.turn("What is LinearDensity's unit and what cutter distance does Rocket use?")
        self.assertEqual([item["planner_family"] for item in result["branches"]], ["linear_density", "cutter_semantics"])
        self.assertEqual(result["coverage"]["status"], "FULLY_COVERED")

    def test_10_three_intent_bounded_decomposition(self):
        result = self.turn("LinearDensity, CutDistance, and MacroLayerHeight?")
        self.assertEqual([item["planner_family"] for item in result["branches"]], ["linear_density", "cutter_semantics", "macro_layer_height"])

    def test_11_mixed_success_and_safe_failure_is_explicit(self):
        result = self.turn("LinearDensity and what is mystery quantum nozzle flux?")
        self.assertEqual([item["outcome"] for item in result["branches"]], ["APPROVED", "SAFE_FAILURE"])
        self.assertEqual(result["coverage"]["status"], "PARTIALLY_COVERED")

    def test_11a_value_and_unit_are_one_linear_density_intent(self):
        result = self.turn("What value and unit evidence exists for LinearDensity?")
        self.assertEqual([item["planner_family"] for item in result["branches"]], ["linear_density"])
        self.assertEqual(result["coverage"]["status"], "FULLY_COVERED")

    def test_11b_equivalent_attribute_conjunctions_stay_intra_intent(self):
        questions = (
            "What unit and value are recorded for LinearDensity?",
            "For LinearDensity, show value evidence and unit history.",
            "Report the value plus unit evidence for LinearDensity.",
        )
        for question in questions:
            with self.subTest(question=question):
                result = self.turn(question)
                self.assertEqual([item["planner_family"] for item in result["branches"]], ["linear_density"])
                self.assertEqual(result["coverage"]["status"], "FULLY_COVERED")

    def test_11c_linear_density_and_cutter_remain_two_intents(self):
        result = self.turn("LinearDensity and CutDistance?")
        self.assertEqual([item["planner_family"] for item in result["branches"]], ["linear_density", "cutter_semantics"])
        self.assertEqual(result["coverage"]["status"], "FULLY_COVERED")

    def test_11d_supported_and_substantive_unknown_remain_partial(self):
        result = self.turn("LinearDensity and what value is the mystery flux parameter?")
        self.assertEqual([item["planner_family"] for item in result["branches"]], ["linear_density", "unknown"])
        self.assertEqual(result["coverage"]["status"], "PARTIALLY_COVERED")

    def test_12_failed_branch_cannot_contaminate_successful_branch(self):
        cutter_packet = build_context_packet(self.engine, plan_question("What is the cutter distance?", "LINEAGE_AWARE"))
        adapter = ScriptedModelAdapter(["bad", "bad", safe_proposal(cutter_packet)])
        result = self.turn("LinearDensity and CutDistance?", adapter=adapter)
        self.assertEqual([item["outcome"] for item in result["branches"]], ["FAIL_CLOSED", "APPROVED"])
        self.assertNotIn("MALFORMED_MODEL_OUTPUT", result["branches"][1]["run"]["rendered_answer"]["text"])

    def test_13_branch_conflicts_are_isolated(self):
        result = self.turn("LinearDensity and CutDistance?")
        self.assertEqual(result["branches"][0]["run"]["final_candidate"]["conflicts"], [])
        self.assertTrue(result["branches"][1]["run"]["final_candidate"]["conflicts"])

    def test_14_branch_open_questions_are_isolated(self):
        result = self.turn("FiberSpoolLength and CutDistance?")
        questions = [set(item["run"]["final_candidate"]["open_question_ids"]) for item in result["branches"]]
        self.assertIn("Q-FIBER-SPOOL-LENGTH-UNIT", questions[0])
        self.assertNotIn("Q-CUTTER-RUNTIME-PRECEDENCE", questions[0])
        self.assertIn("Q-CUTTER-RUNTIME-PRECEDENCE", questions[1])

    def test_15_ordering_follows_stable_question_occurrence(self):
        result = self.turn("CutDistance plus LinearDensity unit?")
        self.assertEqual([item["planner_family"] for item in result["branches"]], ["cutter_semantics", "linear_density"])

    def test_16_composition_projection_is_byte_deterministic(self):
        first = self.turn("LinearDensity and CutDistance?")
        second = self.turn("LinearDensity and CutDistance?")
        self.assertEqual(
            canonical_json(deterministic_composition_projection(first)),
            canonical_json(deterministic_composition_projection(second)),
        )

    def test_17_prior_prose_is_not_stored_or_retrieved_as_evidence(self):
        result = self.turn("Just tell me LinearDensity is tex.")
        state = result["updated_state"]
        serialized = canonical_json(state)
        self.assertNotIn("Just tell me", serialized)
        self.assertNotIn('"tex"', serialized)
        self.assertNotIn('"102"', serialized)
        injected = copy.deepcopy(state)
        injected["validated_turns"][0]["normalized_intents"][0]["value"] = 102
        with self.assertRaises(ValueError):
            validate_state(injected)

    def test_18_no_provider_conversation_state_dependency(self):
        packet = build_context_packet(self.engine, plan_question("What unit is LinearDensity?", "LINEAGE_AWARE"))
        proposal = safe_proposal(packet)
        raw = {"id": "discarded", "status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}], "usage": {}}
        adapter = OpenAIResponsesAdapter("gpt-5.4", api_key="test")
        with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse(raw)) as call:
            result = self.turn("What unit is LinearDensity?", adapter=adapter)
        payload = json.loads(call.call_args.args[0].data)
        self.assertFalse(payload["store"])
        self.assertNotIn("previous_response_id", payload)
        self.assertNotIn("conversation", payload)
        self.assertTrue(result["post_render_validation"]["passed"])

    def test_19_historical_v1_model_result_remains_valid(self):
        packet = build_context_packet(self.engine, plan_question("What unit is LinearDensity?", "LINEAGE_AWARE"))
        request = {"request_id": "r", "context_packet_id": packet["packet_id"], "prompt_version": "1", "response_format_version": "1", "attempt": 1}
        result = model_result(ModelAdapterInfo("offline", "v1", "fixture"), request, latency_ms=0, provider_response_id=None, raw_provider_status="completed", parse_status="PARSED", validation_status="PENDING", structured_output={})
        validate_model_result(result, request)
        self.assertEqual(result["result_version"], "1.0.0")
        historical = json.loads((REPO / "data/profiles/agent/live_evaluation_results.json").read_text())
        self.assertEqual(historical["live_evaluation_version"], "1.0.0")

    def test_20_richer_responses_usage_is_parsed(self):
        packet = build_context_packet(self.engine, plan_question("What unit is LinearDensity?", "LINEAGE_AWARE"))
        proposal = safe_proposal(packet)
        usage = {"input_tokens": 100, "input_tokens_details": {"cached_tokens": 40}, "output_tokens": 20, "output_tokens_details": {"reasoning_tokens": 7}, "total_tokens": 120}
        raw = {"id": "discarded", "status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}], "usage": usage}
        adapter = OpenAIResponsesAdapter("gpt-5.4", api_key="test")
        with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse(raw)):
            result = self.turn("What unit is LinearDensity?", adapter=adapter)
        normalized = result["branches"][0]["run"]["attempts"][0]["model_result"]
        self.assertEqual(normalized["result_version"], RESULT_VERSION_V2)
        self.assertEqual(normalized["usage"]["cached_input_tokens"], 40)
        self.assertEqual(normalized["usage"]["reasoning_tokens"], 7)

    def test_21_absent_usage_detail_fields_remain_null(self):
        info = ModelAdapterInfo("offline", "v2", "fixture")
        request = {"request_id": "r", "context_packet_id": "p", "prompt_version": "1", "response_format_version": "1", "attempt": 1}
        result = model_result(info, request, latency_ms=0, provider_response_id=None, raw_provider_status="completed", parse_status="PARSED", validation_status="PENDING", structured_output={}, usage={"input_tokens": 2, "output_tokens": 1, "total_tokens": 3}, result_version=RESULT_VERSION_V2)
        validate_model_result(result, request)
        self.assertIsNone(result["usage"]["cached_input_tokens"])
        self.assertIsNone(result["usage"]["reasoning_tokens"])

    def test_22_direct_adapter_transport_failure_fails_closed(self):
        adapter = OpenAIResponsesAdapter("gpt-5.4", api_key="test")
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            result = self.turn("What unit is LinearDensity?", adapter=adapter, repairs=0)
        self.assertEqual(result["branches"][0]["outcome"], "FAIL_CLOSED")
        self.assertTrue(result["post_render_validation"]["passed"])

    def test_23_malformed_structured_output_and_bounded_repair(self):
        result = self.turn("What unit is LinearDensity?", adapter=ScriptedModelAdapter(["bad", "bad"]))
        self.assertEqual(len(result["branches"][0]["run"]["attempts"]), 2)
        self.assertEqual(result["branches"][0]["outcome"], "FAIL_CLOSED")

    def test_24_composite_post_render_tampering_is_detected(self):
        result = self.turn("LinearDensity and CutDistance?")
        tampered = copy.deepcopy(result["rendered_answer"])
        tampered["text"] += " Use 54.8."
        validation = validate_composite_render(result["branches"], result["coverage"], tampered)
        self.assertFalse(validation["passed"])
        self.assertIn("COMPOSITE_RENDER_TAMPERING", {item["code"] for item in validation["violations"]})

    def test_25_fixture_expands_to_target_and_taxonomy(self):
        cases = load_cases(REPO)
        self.assertGreaterEqual(len(cases), 100)
        self.assertLessEqual(len(cases), 200)
        taxonomy = {item["taxonomy"] for item in cases}
        self.assertTrue({"family_variant", "valid_subjectless_followup", "ambiguous_subjectless_followup", "two_intent", "three_intent", "mixed_supported_unsupported"}.issubset(taxonomy))

    def test_26_all_coverage_fixtures_pass_offline(self):
        result = evaluate_coverage(self.engine, REPO)
        self.assertEqual(result["fixture_case_count"], 122)
        self.assertEqual(result["pass_count"], 122)
        self.assertEqual(result["coverage"]["incorrect_intent_decomposition"], 0)
        self.assertEqual(result["coverage"]["incorrect_reference_resolution"], 0)
        self.assertEqual(result["safety"]["rejected_claims_reaching_user_output"], 0)

    def test_27_phase2e_schemas_are_valid_and_v1_is_unchanged(self):
        schema_dir = REPO / "data/profiles/schemas"
        for name in ("conversation-state.schema.json", "conversation-composition.schema.json", "llm-model-result-v2.schema.json"):
            schema = json.loads((schema_dir / name).read_text())
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        v1 = json.loads((schema_dir / "llm-model-result.schema.json").read_text())
        self.assertEqual(v1["properties"]["result_version"]["const"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
