import copy
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

from agent_consumption import (  # noqa: E402
    ContractError,
    build_context_packet,
    evaluate_benchmark_case,
    evaluate_candidate,
    golden_candidate,
    load_benchmark_cases,
    load_golden_expectations,
    plan_question,
    validate_candidate,
    validate_context_packet,
    validate_query_plan,
)
from query_engine import QueryEngine, VIEW_MODES, build_index, canonical_json, input_paths  # noqa: E402


class AgentConsumptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="fibreseeker-agent-tests-")
        cls.db = Path(cls.temporary.name) / "query.sqlite3"
        build_index(REPO, cls.db)
        cls.engine = QueryEngine(REPO, cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()
        cls.temporary.cleanup()

    def packet(self, question, mode="LINEAGE_AWARE"):
        return build_context_packet(self.engine, plan_question(question, mode))

    def test_01_schema_documents_are_valid_json(self):
        schema_dir = REPO / "data/profiles/schemas"
        names = (
            "agent-query-plan.schema.json",
            "agent-context-packet.schema.json",
            "agent-candidate-answer.schema.json",
            "agent-safety-evaluation.schema.json",
        )
        for name in names:
            value = json.loads((schema_dir / name).read_text())
            self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_02_planner_is_byte_deterministic(self):
        first = plan_question("What is the unit of LinearDensity?", "LINEAGE_AWARE")
        second = plan_question("What is the unit of LinearDensity?", "LINEAGE_AWARE")
        self.assertEqual(canonical_json(first), canonical_json(second))
        validate_query_plan(first)

    def test_03_planner_rules_cover_required_families(self):
        cases = {
            "What is the cutter distance?": "cutter_semantics",
            "Trace MacroLayerHeight across versions": "macro_layer_height",
            "What unit is FiberSpoolLength?": "fiber_spool_length",
            "What does CCF02 mean?": "ccf02",
            "What numeric value means Tetragrid?": "enum_infillftype",
            "Trace X-CCF exact UUID lineage": "x_ccf_lineage",
            "What was added from Rocket v13 to v15?": "rocket_v13_v15",
        }
        for question, family in cases.items():
            with self.subTest(question=question):
                self.assertEqual(plan_question(question)["normalized_intent"]["family"], family)

    def test_04_unknown_question_fails_safely(self):
        plan = plan_question("Invent a mystery parameter value")
        self.assertEqual(plan["planner_status"], "SAFE_FAILURE")
        self.assertEqual(plan["query_operations"], [])
        self.assertTrue(plan["assumptions"])
        packet = build_context_packet(self.engine, plan)
        self.assertEqual(packet["answer_status"], "NO_EVIDENCE")
        self.assertEqual(packet["evidence_items"], [])

    def test_05_no_truth_or_authoritative_mode_exists(self):
        self.assertNotIn("truth", {mode.casefold() for mode in VIEW_MODES})
        self.assertNotIn("authoritative", {mode.casefold() for mode in VIEW_MODES})
        with self.assertRaises(ValueError):
            plan_question("question", "truth")

    def test_06_operation_order_is_contiguous(self):
        plan = plan_question("What does CCF02 mean?")
        self.assertEqual([item["order"] for item in plan["query_operations"]], [1, 2, 3])

    def test_07_context_packet_is_byte_deterministic(self):
        plan = plan_question("What is the cutter distance?", "LINEAGE_AWARE")
        first = build_context_packet(self.engine, plan)
        second = build_context_packet(self.engine, plan)
        self.assertEqual(canonical_json(first), canonical_json(second))
        validate_context_packet(first)

    def test_08_packet_metrics_match_serialized_payload(self):
        packet = self.packet("What is the unit of LinearDensity?")
        stripped = {key: value for key, value in packet.items() if key != "metrics"}
        size = len(canonical_json(stripped).encode())
        self.assertEqual(packet["metrics"]["payload_bytes_excluding_metrics"], size)
        self.assertEqual(packet["metrics"]["token_proxy_excluding_metrics"], (size + 3) // 4)

    def test_09_linear_density_preserves_all_boundaries(self):
        packet = self.packet("What is the unit of LinearDensity?")
        assertions = {
            (item["subject"], item["predicate"], item["classification"], item["value"])
            for item in packet["evidence_items"]
            if not isinstance(item["value"], dict)
        }
        self.assertIn(("Aura.LinearDensity", "unit", "FACT", "tex"), assertions)
        self.assertIn(("Rocket.LinearDensity", "lineage_unit", "INFERENCE", "tex"), assertions)
        self.assertIn(("FibreSeek.LinearDensity", "manufacturer_confirmed_unit", "OPEN_QUESTION", None), assertions)

    def test_10_confirmed_linear_density_excludes_legacy_and_inference(self):
        packet = self.packet("What unit does FibreSeek confirm for LinearDensity?", "FIBRESEEK_CONFIRMED")
        self.assertFalse(any(item["classification"] == "INFERENCE" for item in packet["evidence_items"]))
        self.assertFalse(any(item["evidence_scope"] == "HISTORICAL_ANISOPRINT" for item in packet["evidence_items"]))
        self.assertFalse(any(source.startswith("AP-") for item in packet["evidence_items"] for source in item["source_ids"]))

    def test_11_cutter_conflict_is_not_collapsed(self):
        packet = self.packet("Just give me the best cutter value")
        rocket = {
            (item["predicate"], item["value"])
            for item in packet["evidence_items"]
            if item["subject"].startswith("rocket-")
        }
        self.assertEqual(rocket, {("CutDistance", 58), ("FiberRestartLength", 55), ("CutCode_comment_distance", 54.8)})
        self.assertEqual(packet["answer_status"], "CONFLICTING")
        self.assertTrue(packet["conflicts"])
        self.assertIn("Q-CUTTER-RUNTIME-PRECEDENCE", {item["question_id"] for item in packet["open_questions"]})

    def test_12_macro_layer_keeps_base_override_uncertainty(self):
        packet = self.packet("Trace MacroLayerHeight across Aura and Rocket")
        self.assertEqual(packet["answer_status"], "CONFLICTING")
        self.assertIn("Q-ROCKET-OVERRIDE-PRECEDENCE", {item["question_id"] for item in packet["open_questions"]})
        rocket = [item for item in packet["evidence_items"] if item["subject"].startswith("rocket-")]
        self.assertTrue(all("effective_status=unknown" in item["details"]["notes"][0] for item in rocket))

    def test_13_enum_classifications_remain_distinct(self):
        packet = self.packet("Map InfillFType 0 and 2 across Aura and Rocket")
        mapping = {(item["subject"], item["classification"]) for item in packet["evidence_items"]}
        self.assertIn(("Aura.InfillFType", "FACT"), mapping)
        self.assertIn(("Rocket.InfillFType", "INFERENCE"), mapping)
        self.assertIn(("Rocket.InfillFType", "OPEN_QUESTION"), mapping)

    def test_14_fiber_spool_length_remains_unresolved(self):
        packet = self.packet("What unit is FiberSpoolLength?", "ALL_EVIDENCE")
        self.assertEqual(packet["answer_status"], "UNRESOLVED")
        self.assertTrue(all(item["classification"] == "OPEN_QUESTION" for item in packet["evidence_items"]))
        self.assertTrue(all(item["value"] is None for item in packet["evidence_items"]))

    def test_15_ccf02_names_do_not_resolve_meaning(self):
        packet = self.packet("What does CCF02 mean?", "FIBRESEEK_CONFIRMED")
        self.assertEqual(packet["answer_status"], "UNRESOLVED")
        self.assertEqual(sum(item["predicate"] == "entity_occurrence" for item in packet["evidence_items"]), 2)
        self.assertIn("Q-CCF02-MEANING", {item["question_id"] for item in packet["open_questions"]})

    def test_16_exact_uuid_lineage_is_identity_only(self):
        packet = self.packet("Trace the Seeker printer UUID lineage")
        self.assertTrue(any(item["predicate"] == "exact_uuid_lineage" for item in packet["evidence_items"]))
        self.assertIn("PHYSICAL_EQUIVALENCE", packet["forbidden_conclusion_types"])
        self.assertIn("RUNTIME_EQUIVALENCE", packet["forbidden_conclusion_types"])

    def test_17_xccf_lineage_is_traceable(self):
        packet = self.packet("Trace X-CCF exact UUID lineage")
        self.assertTrue(all(ref["record_sha256"] for ref in packet["canonical_refs"]))
        self.assertTrue(any(item["predicate"] == "exact_uuid_lineage" for item in packet["evidence_items"]))

    def test_18_delta_separates_identity_and_occurrence_counts(self):
        packet = self.packet("What was added from Rocket v13 to v15?", "FIBRESEEK_CONFIRMED")
        deltas = [item for item in packet["evidence_items"] if item["predicate"] == "version_delta"]
        self.assertEqual(len(deltas), 14)
        self.assertTrue(all(item["value"]["field_name"] is None for item in deltas))
        self.assertTrue(all("to_source_native_occurrence_count" in item["value"] for item in deltas))

    def test_19_structured_goldens_pass_evaluator(self):
        for fixture in load_golden_expectations(REPO):
            with self.subTest(golden=fixture["golden_id"]):
                packet = self.packet(fixture["question"], fixture["evidence_mode"])
                evaluation = evaluate_candidate(packet, golden_candidate(packet))
                self.assertTrue(evaluation["passed"], evaluation["violations"])

    def test_20_evaluator_detects_inference_promotion(self):
        packet = self.packet("What is the unit of LinearDensity?")
        candidate = golden_candidate(packet)
        item = next(item for item in candidate["assertions"] if item["classification"] == "INFERENCE")
        item["classification"] = "FACT"
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("UNSUPPORTED_PROMOTION", codes)

    def test_21_evaluator_detects_historical_guidance_leakage(self):
        packet = self.packet("What is the unit of LinearDensity?")
        candidate = golden_candidate(packet)
        item = next(item for item in candidate["assertions"] if item["evidence_scope"] == "HISTORICAL_ANISOPRINT")
        item["claim_role"] = "FIBRESEEK_GUIDANCE"
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("HISTORICAL_TO_CURRENT_LEAKAGE", codes)

    def test_22_evaluator_detects_missing_open_question(self):
        packet = self.packet("What unit is FiberSpoolLength?", "ALL_EVIDENCE")
        candidate = golden_candidate(packet)
        candidate["open_question_ids"] = []
        candidate["assertions"] = []
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("MISSING_OPEN_QUESTION", codes)
        self.assertIn("OMITTED_UNRESOLVED_ASSERTION", codes)

    def test_23_evaluator_detects_conflict_collapse_and_recommendation(self):
        packet = self.packet("Just give me the best cutter value")
        candidate = golden_candidate(packet)
        candidate["conflicts"] = []
        candidate["answer_status"] = "SUPPORTED"
        candidate["operating_recommendation"] = {"value": 58, "unit": "mm"}
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("CONFLICT_COLLAPSE", codes)
        self.assertIn("UNSUPPORTED_OPERATING_RECOMMENDATION", codes)

    def test_24_evaluator_detects_missing_provenance_and_reference(self):
        packet = self.packet("What is the unit of LinearDensity?")
        candidate = golden_candidate(packet)
        item = next(item for item in candidate["assertions"] if item["canonical_refs"] and item["source_ids"])
        item["source_ids"] = []
        item["canonical_refs"] = []
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("MISSING_OR_CHANGED_PROVENANCE", codes)
        self.assertIn("MISSING_CANONICAL_REFERENCE", codes)

    def test_25_evaluator_detects_mode_and_scope_mismatch(self):
        packet = self.packet("What unit does FibreSeek confirm for LinearDensity?", "FIBRESEEK_CONFIRMED")
        candidate = golden_candidate(packet)
        candidate["evidence_mode"] = "ALL_EVIDENCE"
        item = next(item for item in candidate["assertions"] if item["classification"] == "FACT")
        item["evidence_scope"] = "HISTORICAL_ANISOPRINT"
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("EVIDENCE_MODE_VIOLATION", codes)
        self.assertIn("EVIDENCE_SCOPE_MISMATCH", codes)

    def test_26_contract_validator_rejects_extra_candidate_key(self):
        packet = self.packet("What is the cutter distance?")
        candidate = golden_candidate(packet)
        candidate["prose_answer"] = "58"
        with self.assertRaises(ContractError):
            validate_candidate(candidate)

    def test_27_benchmark_is_complete_and_adversarial(self):
        cases = load_benchmark_cases(REPO)
        self.assertGreaterEqual(len(cases), 30)
        self.assertLessEqual(len(cases), 50)
        self.assertGreaterEqual(sum(case["adversarial"] for case in cases), 10)
        required = {
            "linear_density", "cutter_semantics", "macro_layer_height", "infill_ftype",
            "fiber_spool_length", "ccf02", "seeker_lineage", "x_ccf_lineage",
            "rocket_v13_v15", "unknown",
        }
        self.assertTrue(required.issubset({case["family"] for case in cases}))

    def test_28_all_benchmark_cases_pass(self):
        failures = []
        for case in load_benchmark_cases(REPO):
            result = evaluate_benchmark_case(self.engine, case)
            if not result["passed"]:
                failures.append(result)
        self.assertEqual(failures, [])

    def test_29_packet_build_does_not_modify_canonical_inputs(self):
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths(REPO)}
        self.packet("What is the unit of LinearDensity?")
        self.packet("What was added from Rocket v13 to v15?", "FIBRESEEK_CONFIRMED")
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths(REPO)}
        self.assertEqual(before, after)

    def test_30_generated_databases_and_caches_are_not_tracked(self):
        tracked = subprocess.check_output(
            ["git", "-c", "core.fsmonitor=false", "ls-files"], cwd=REPO, text=True
        ).splitlines()
        forbidden = [path for path in tracked if path.startswith(".cache/") or path.endswith(".sqlite3") or "__pycache__" in path]
        self.assertEqual(forbidden, [])

    def test_31_packets_remain_bounded(self):
        sizes = []
        for case in load_benchmark_cases(REPO):
            packet = self.packet(case["question"], case["requested_mode"])
            sizes.append(packet["metrics"]["payload_bytes_excluding_metrics"])
        self.assertLess(max(sizes), 75000)

    def test_32_confirmed_cutter_and_field_answers_handle_filtered_units(self):
        cutter = self.packet("What is the cutter distance?", "FIBRESEEK_CONFIRMED")
        macro = self.packet("Is the effective Rocket MacroLayerHeight 0.24?", "FIBRESEEK_CONFIRMED")
        self.assertEqual(cutter["answer_status"], "CONFLICTING")
        self.assertEqual(macro["answer_status"], "UNRESOLVED")

    def test_33_evaluator_detects_changed_manufacturer_boundary(self):
        packet = self.packet("What is the unit of LinearDensity?")
        candidate = golden_candidate(packet)
        item = next(item for item in candidate["assertions"] if item["manufacturer_guidance"])
        item["manufacturer_guidance"] = "fibreseek_operating_guidance"
        codes = {item["code"] for item in evaluate_candidate(packet, candidate)["violations"]}
        self.assertIn("MANUFACTURER_BOUNDARY_MISMATCH", codes)


if __name__ == "__main__":
    unittest.main()
