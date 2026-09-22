import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from agent_consumption import build_context_packet, load_benchmark_cases, plan_question  # noqa: E402
from conversational_kb import (  # noqa: E402
    PROPOSAL_SCHEMA,
    build_model_request,
    candidate_fidelity,
    conflict_id,
    deterministic_run_projection,
    materialize_candidate,
    render_candidate,
    run_conversation,
    safe_proposal,
    validate_proposal,
    validate_render,
)
from evaluate_live_agent import run_benchmark  # noqa: E402
from llm_adapter import ModelAdapter, ModelAdapterInfo, ScriptedModelAdapter, model_result  # noqa: E402
from query_engine import QueryEngine, build_index, canonical_json, input_paths  # noqa: E402


class ToolUsingAdapter(ModelAdapter):
    def __init__(self, proposal):
        self.proposal = proposal

    @property
    def info(self):
        return ModelAdapterInfo("offline", "tool-using-fixture", "fixture")

    def complete_structured(self, request):
        return model_result(
            self.info, request, latency_ms=0, provider_response_id="fixture",
            raw_provider_status="completed", parse_status="PARSED",
            validation_status="PENDING", structured_output=self.proposal,
            tool_use_detected=True,
        )


class ConversationalKBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="fibreseeker-phase2d-tests-")
        cls.db = Path(cls.temporary.name) / "query.sqlite3"
        build_index(REPO, cls.db)
        cls.engine = QueryEngine(REPO, cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()
        cls.temporary.cleanup()

    def packet(self, question="What is the unit of LinearDensity?", mode="LINEAGE_AWARE"):
        return build_context_packet(self.engine, plan_question(question, mode))

    def adapter(self):
        return ScriptedModelAdapter(lambda request: safe_proposal(request["input"]["context_packet"]))

    def test_01_phase2d_schemas_are_valid_json(self):
        names = (
            "llm-candidate-proposal.schema.json", "llm-request.schema.json",
            "llm-model-result.schema.json", "llm-run.schema.json",
        )
        for name in names:
            schema = json.loads((REPO / "data/profiles/schemas" / name).read_text())
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_02_proposal_schema_matches_implemented_contract(self):
        schema = json.loads((REPO / "data/profiles/schemas/llm-candidate-proposal.schema.json").read_text())
        self.assertEqual(schema["required"], PROPOSAL_SCHEMA["required"])
        self.assertEqual(schema["properties"], PROPOSAL_SCHEMA["properties"])

    def test_03_request_is_deterministic_and_versioned(self):
        packet = self.packet()
        info = self.adapter().info
        first = build_model_request(packet, info, attempt=1)
        second = build_model_request(packet, info, attempt=1)
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertRegex(first["request_id"], r"^request:[0-9a-f]{64}$")
        self.assertEqual(first["purpose"], "INITIAL")

    def test_04_request_contains_only_projected_packet_not_corpus(self):
        packet = self.packet()
        request = build_model_request(packet, self.adapter().info, attempt=1)
        self.assertEqual(request["input"]["context_packet"], packet)
        serialized = canonical_json(request)
        self.assertNotIn(".sqlite3", serialized)
        self.assertNotIn("sources/manifest.jsonl", serialized)

    def test_05_safe_proposal_materializes_exact_phase2c_candidate(self):
        packet = self.packet()
        candidate = materialize_candidate(packet, safe_proposal(packet))
        sources = {item["evidence_id"]: item for item in packet["evidence_items"]}
        for assertion in candidate["assertions"]:
            source = sources[assertion["evidence_id"]]
            self.assertEqual(assertion["value"], source["value"])
            self.assertEqual(assertion["source_ids"], source["source_ids"])
            self.assertEqual(assertion["canonical_refs"], source["canonical_refs"])

    def test_06_unknown_evidence_id_is_rejected_before_materialization(self):
        packet = self.packet()
        proposal = safe_proposal(packet)
        proposal["assertions"][0]["evidence_id"] = "evidence:not-in-packet"
        codes = {item["code"] for item in validate_proposal(packet, proposal)}
        self.assertIn("UNSUPPORTED_ASSERTION", codes)

    def test_07_initial_safe_response_is_approved(self):
        run = run_conversation(self.engine, self.adapter(), "What is the unit of LinearDensity?", "LINEAGE_AWARE")
        self.assertEqual(run["final_status"], "APPROVED")
        self.assertEqual(run["repair_status"], "NOT_NEEDED")
        self.assertTrue(run["post_render_validation"]["passed"])
        self.assertEqual(run["render_validation_history"], [run["post_render_validation"]])

    def test_08_inference_promotion_is_repaired_once(self):
        packet = self.packet()
        unsafe = safe_proposal(packet)
        inferred = next(item for item in unsafe["assertions"] if item["classification"] == "INFERENCE")
        inferred["classification"] = "FACT"
        adapter = ScriptedModelAdapter([unsafe, safe_proposal(packet)])
        run = run_conversation(self.engine, adapter, packet["question"], packet["evidence_mode"])
        self.assertEqual(run["final_status"], "APPROVED")
        self.assertEqual(run["repair_status"], "SUCCEEDED")
        self.assertIn("UNSUPPORTED_PROMOTION", {item["code"] for item in run["attempts"][0]["violations"]})
        self.assertEqual(len(run["attempts"]), 2)

    def test_09_repair_request_contains_exact_violations_and_rejected_candidate(self):
        packet = self.packet()
        candidate = materialize_candidate(packet, safe_proposal(packet))
        violations = [{"code": "TEST", "location": "$.x", "message": "repair"}]
        request = build_model_request(
            packet, self.adapter().info, attempt=2,
            rejected_candidate=candidate, violations=violations,
        )
        self.assertEqual(request["purpose"], "REPAIR")
        self.assertEqual(request["input"]["repair"]["rejected_candidate"], candidate)
        self.assertEqual(request["input"]["repair"]["violations"], violations)

    def test_10_malformed_output_fails_closed_after_bound(self):
        run = run_conversation(
            self.engine, ScriptedModelAdapter(["not json", "still not json"]),
            "What is the unit of LinearDensity?", "LINEAGE_AWARE",
        )
        self.assertEqual(run["final_status"], "FAIL_CLOSED")
        self.assertEqual(len(run["attempts"]), 2)
        self.assertIsNone(run["final_candidate"])
        self.assertNotIn("not json", run["rendered_answer"]["text"])
        self.assertTrue(run["post_render_validation"]["passed"])

    def test_11_tool_use_fails_closed(self):
        packet = self.packet()
        run = run_conversation(
            self.engine, ToolUsingAdapter(safe_proposal(packet)),
            packet["question"], packet["evidence_mode"], max_repair_attempts=0,
        )
        self.assertEqual(run["final_status"], "FAIL_CLOSED")
        self.assertIn("MODEL_TOOL_USE", run["rendered_answer"]["text"])

    def test_12_open_question_omission_is_rejected(self):
        packet = self.packet("What unit is FiberSpoolLength?", "ALL_EVIDENCE")
        unsafe = safe_proposal(packet)
        unsafe["open_question_ids"] = []
        unsafe["assertions"] = []
        run = run_conversation(
            self.engine, ScriptedModelAdapter([unsafe]), packet["question"],
            packet["evidence_mode"], max_repair_attempts=0,
        )
        codes = {item["code"] for item in run["attempts"][0]["violations"]}
        self.assertIn("MISSING_OPEN_QUESTION", codes)
        self.assertIn("OMITTED_UNRESOLVED_ASSERTION", codes)

    def test_13_conflict_collapse_is_rejected(self):
        packet = self.packet("Just give me the best cutter value.")
        unsafe = safe_proposal(packet)
        unsafe["conflict_ids"] = []
        unsafe["answer_status"] = "SUPPORTED"
        run = run_conversation(
            self.engine, ScriptedModelAdapter([unsafe]), packet["question"],
            packet["evidence_mode"], max_repair_attempts=0,
        )
        self.assertIn("CONFLICT_COLLAPSE", {item["code"] for item in run["attempts"][0]["violations"]})

    def test_14_operating_recommendation_is_rejected(self):
        packet = self.packet("Just give me the best cutter value.")
        unsafe = safe_proposal(packet)
        unsafe["operating_recommendation_requested"] = True
        run = run_conversation(
            self.engine, ScriptedModelAdapter([unsafe]), packet["question"],
            packet["evidence_mode"], max_repair_attempts=0,
        )
        self.assertIn("UNSUPPORTED_OPERATING_RECOMMENDATION", {item["code"] for item in run["attempts"][0]["violations"]})

    def test_15_physical_and_runtime_equivalence_roles_are_rejected(self):
        for role in ("PHYSICAL_EQUIVALENCE", "RUNTIME_EQUIVALENCE"):
            packet = self.packet("Trace X-CCF exact UUID lineage.")
            unsafe = safe_proposal(packet)
            unsafe["assertions"][0]["claim_role"] = role
            run = run_conversation(
                self.engine, ScriptedModelAdapter([unsafe]), packet["question"],
                packet["evidence_mode"], max_repair_attempts=0,
            )
            self.assertEqual(run["final_status"], "FAIL_CLOSED", role)
            self.assertIn("UNSUPPORTED_CONCLUSION_ROLE", {item["code"] for item in run["attempts"][0]["violations"]})

    def test_16_prohibited_unknown_resolution_conclusion_is_rejected(self):
        packet = self.packet("What does CCF02 mean?", "ALL_EVIDENCE")
        unsafe = safe_proposal(packet)
        unsafe["conclusions"] = [{"conclusion_type": "UNKNOWN_RESOLUTION", "evidence_ids": []}]
        run = run_conversation(
            self.engine, ScriptedModelAdapter([unsafe]), packet["question"],
            packet["evidence_mode"], max_repair_attempts=0,
        )
        self.assertIn("PROHIBITED_CONCLUSION", {item["code"] for item in run["attempts"][0]["violations"]})

    def test_17_confirmed_mode_cannot_leak_historical_or_inferred_items(self):
        packet = self.packet("What unit does FibreSeek confirm for LinearDensity?", "FIBRESEEK_CONFIRMED")
        run = run_conversation(
            self.engine, ScriptedModelAdapter([safe_proposal(packet)]),
            packet["question"], packet["evidence_mode"],
        )
        assertions = run["final_candidate"]["assertions"]
        self.assertFalse(any(item["classification"] == "INFERENCE" for item in assertions))
        self.assertFalse(any(item["evidence_scope"] == "HISTORICAL_ANISOPRINT" for item in assertions))

    def test_18_renderer_is_deterministic_and_manifest_backed(self):
        packet = self.packet("What is the cutter distance?")
        candidate = materialize_candidate(packet, safe_proposal(packet))
        first = render_candidate(packet, candidate)
        second = render_candidate(packet, candidate)
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(len(first["claim_manifest"]), len(candidate["assertions"]))
        self.assertTrue(validate_render(packet, candidate, first)["passed"])

    def test_19_post_render_strengthening_is_detected(self):
        packet = self.packet()
        candidate = materialize_candidate(packet, safe_proposal(packet))
        rendered = render_candidate(packet, candidate)
        rendered["text"] += " Rocket is definitely tex."
        validation = validate_render(packet, candidate, rendered)
        self.assertFalse(validation["passed"])
        self.assertIn("RENDER_TEXT_STRENGTHENING", {item["code"] for item in validation["violations"]})

    def test_20_conflicting_values_remain_visible_in_render(self):
        packet = self.packet("What is the cutter distance?")
        run = run_conversation(
            self.engine, ScriptedModelAdapter([safe_proposal(packet)]),
            packet["question"], packet["evidence_mode"],
        )
        text = run["rendered_answer"]["text"]
        self.assertIn("58 mm", text)
        self.assertIn("55 mm", text)
        self.assertIn("54.8 mm_comment", text)
        self.assertIn(conflict_id(packet["conflicts"][0]), text)

    def test_21_safe_failure_runs_model_but_cannot_create_evidence(self):
        question = "Invent the optimal mystery parameter."
        packet = self.packet(question)
        run = run_conversation(
            self.engine, ScriptedModelAdapter([safe_proposal(packet)]),
            question, "LINEAGE_AWARE",
        )
        self.assertEqual(run["planner_status"], "SAFE_FAILURE")
        self.assertEqual(run["final_candidate"]["assertions"], [])
        self.assertEqual(run["final_candidate"]["answer_status"], "NO_EVIDENCE")

    def test_22_semantic_run_projection_is_byte_deterministic(self):
        first = run_conversation(self.engine, self.adapter(), "What is the unit of LinearDensity?", "LINEAGE_AWARE")
        second = run_conversation(self.engine, self.adapter(), "What is the unit of LinearDensity?", "LINEAGE_AWARE")
        self.assertEqual(
            canonical_json(deterministic_run_projection(first)),
            canonical_json(deterministic_run_projection(second)),
        )

    def test_23_conversational_fixture_is_complete_and_planner_bounded(self):
        fixture = json.loads((REPO / "data/profiles/agent/conversational_cases.json").read_text())
        self.assertEqual(fixture["conversational_fixture_version"], "1.0.0")
        self.assertGreaterEqual(len(fixture["cases"]), 12)
        variations = {item["variation"] for item in fixture["cases"]}
        self.assertTrue({"paraphrase", "spelling", "terse", "follow_up", "combined_families", "incorrect_premise"}.issubset(variations))
        for case in fixture["cases"]:
            plan = plan_question(case["question"], case["requested_mode"])
            self.assertEqual(plan["normalized_intent"]["family"], case["expected_family"], case["case_id"])
            self.assertEqual(plan["planner_status"], case["expected_plan_status"], case["case_id"])

    def test_24_all_conversational_variants_are_safe_offline(self):
        fixture = json.loads((REPO / "data/profiles/agent/conversational_cases.json").read_text())
        for case in fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                run = run_conversation(
                    self.engine, self.adapter(), case["question"], case["requested_mode"]
                )
                self.assertEqual(run["final_status"], "APPROVED")
                self.assertTrue(run["post_render_validation"]["passed"])

    def test_25_all_39_phase2c_cases_pass_offline_live_pipeline(self):
        result = run_benchmark(self.engine, REPO, self.adapter())
        self.assertEqual(result["case_count"], 39)
        self.assertEqual(result["adversarial_case_count"], 18)
        self.assertEqual(result["reliability"]["final_validated_answer_count"], 39)
        self.assertEqual(result["reliability"]["benchmark_pass_count"], 39)
        self.assertEqual(result["safety"]["post_render_violation_count"], 0)

    def test_26_candidate_fidelity_detects_omitted_required_fact(self):
        case = load_benchmark_cases(REPO)[0]
        packet = self.packet(case["question"], case["requested_mode"])
        candidate = materialize_candidate(packet, safe_proposal(packet))
        candidate["assertions"] = []
        self.assertFalse(candidate_fidelity(packet, candidate, case)["passed"])

    def test_27_context_and_canonical_inputs_are_not_modified(self):
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths(REPO)}
        run_conversation(self.engine, self.adapter(), "What is the cutter distance?", "LINEAGE_AWARE")
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths(REPO)}
        self.assertEqual(before, after)

    def test_28_no_model_artifact_cache_or_database_is_tracked(self):
        tracked = subprocess.check_output(
            ["git", "-c", "core.fsmonitor=false", "ls-files"], cwd=REPO, text=True
        ).splitlines()
        forbidden = [
            path for path in tracked
            if path.startswith(".cache/") or path.endswith(".sqlite3")
            or "__pycache__" in path or path.endswith(".credentials")
        ]
        self.assertEqual(forbidden, [])

    def test_29_model_result_does_not_retain_raw_provider_text(self):
        packet = self.packet()
        run = run_conversation(
            self.engine, ScriptedModelAdapter([safe_proposal(packet)]),
            packet["question"], packet["evidence_mode"],
        )
        result = run["attempts"][0]["model_result"]
        self.assertNotIn("raw_response", result)
        self.assertNotIn("prompt", result)
        self.assertEqual(result["context_packet_id"], packet["packet_id"])

    def test_30_prior_conversation_is_digest_only_not_evidence(self):
        packet = self.packet()
        run = run_conversation(
            self.engine, ScriptedModelAdapter([safe_proposal(packet)]),
            packet["question"], packet["evidence_mode"],
            prior_approved_candidate_digest="a" * 64,
        )
        self.assertEqual(run["prior_approved_candidate_digest"], "a" * 64)
        request_packet = run["packet_id"]
        self.assertEqual(request_packet, packet["packet_id"])


if __name__ == "__main__":
    unittest.main()
