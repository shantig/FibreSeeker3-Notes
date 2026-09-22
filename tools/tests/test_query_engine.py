import hashlib
import json
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from query_engine import QueryEngine, build_index, canonical_json, input_paths  # noqa: E402


CFC = "f3904c6f-c24e-4aff-ad9a-70405cc4df84"
X_CCF = "2af8ac62-4968-4364-88e3-1045ef47feba"
MIGRATED_PROFILE = "d294a2dc-9d7f-460a-acf4-dc50b656d44a"
SEEKER = "83bf1039-8c9e-49fc-928f-2f94a2008d40"


class QueryEngineGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="fibreseeker-query-tests-")
        cls.db = Path(cls.temporary.name) / "query.sqlite3"
        cls.build = build_index(REPO, cls.db)
        cls.engine = QueryEngine(REPO, cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()
        cls.temporary.cleanup()

    def test_01_cut_distance_lineage(self):
        result = self.engine.field_history("CutDistance", identity=CFC, compact=True)
        values = [(item["payload"]["version"], item["payload"]["base_value"]) for item in result["results"]]
        self.assertEqual(
            values,
            [
                ("aura-2.6.1-sk3", 60.0),
                ("aura-2.6.2", 60.0),
                ("rocket-v13", 58),
                ("rocket-v15", 58),
            ],
        )
        self.assertTrue(all(item["payload"]["unit"] == "mm" for item in result["results"]))

    def test_02_cut_code_55_to_54_8_lineage(self):
        result = self.engine.field_history("CutCode", identity=CFC, compact=True)
        values = []
        for item in result["results"]:
            match = re.search(r";CUT(?: DISTANCE)?\s+([0-9.]+)", item["payload"]["base_value"])
            values.append((item["payload"]["version"], float(match.group(1))))
        self.assertEqual(
            values,
            [
                ("aura-2.6.1-sk3", 55.0),
                ("aura-2.6.2", 55.0),
                ("rocket-v13", 54.8),
                ("rocket-v15", 54.8),
            ],
        )

    def test_03_linear_density_102_and_tex_boundary(self):
        history = self.engine.field_history("LinearDensity", identity=X_CCF, compact=True)
        self.assertEqual([item["payload"]["base_value"] for item in history["results"]], [102.0, 102, 102])
        answer = self.engine.answer_unit("LinearDensity", "LINEAGE_AWARE")
        assertions = {(item["subject"], item["predicate"], item["classification"], item["value"]) for item in answer["assertions"]}
        self.assertIn(("Aura.LinearDensity", "unit", "FACT", "tex"), assertions)
        self.assertIn(("Rocket.LinearDensity", "lineage_unit", "INFERENCE", "tex"), assertions)
        self.assertIn(("FibreSeek.LinearDensity", "manufacturer_confirmed_unit", "OPEN_QUESTION", None), assertions)

    def test_04_macro_layer_base_override_migration(self):
        result = self.engine.deltas(
            "aura-2.6.1-sk3", "rocket-v13", identity=MIGRATED_PROFILE,
            field_name="MacroLayerHeight",
        )
        self.assertEqual(result["result_count"], 1)
        payload = result["results"][0]["payload"]
        self.assertEqual(payload["classifications"], ["value_changed", "structurally_changed"])
        self.assertEqual(payload["from"][0]["base_value"], 0.24)
        self.assertEqual(payload["to"][0]["base_value"], 0.2)
        self.assertEqual(payload["to"][0]["override_value"], 0.24)
        self.assertEqual(payload["to"][0]["effective_value_status"], "unknown")

    def test_05_infill_type_aura_rocket_distinction(self):
        result = self.engine.enum("InfillFType", "LINEAGE_AWARE")
        mapping = {
            (item["payload"]["software"], item["payload"]["value"]): item["classification"]
            for item in result["results"]
            if item["payload"]["value"] in (0, 2)
        }
        self.assertEqual(mapping[("Aura", 0)], "FACT")
        self.assertEqual(mapping[("Aura", 2)], "FACT")
        self.assertEqual(mapping[("Rocket", 0)], "INFERENCE")
        self.assertEqual(mapping[("Rocket", 2)], "INFERENCE")

    def test_06_fiber_spool_length_remains_unresolved(self):
        answer = self.engine.answer_unit("FiberSpoolLength", "ALL_EVIDENCE")
        self.assertEqual(answer["answer_status"], "UNRESOLVED")
        self.assertTrue(answer["assertions"])
        self.assertTrue(all(item["classification"] == "OPEN_QUESTION" for item in answer["assertions"]))
        self.assertTrue(all(item["value"] is None for item in answer["assertions"]))
        self.assertIn("Q-FIBER-SPOOL-LENGTH-UNIT", {q["question_id"] for q in answer["open_questions"]})

    def test_07_rocket_v13_v15_entity_additions(self):
        result = self.engine.deltas(
            "rocket-v13", "rocket-v15", classification="added", limit=2000
        )
        entity_additions = [item for item in result["results"] if item["payload"]["field_name"] is None]
        self.assertEqual(len(entity_additions), 14)
        summary = json.loads((REPO / "data/profiles/generated/summary.json").read_text())
        self.assertEqual(summary["entity_counts"]["rocket-v15"] - summary["entity_counts"]["rocket-v13"], 15)

    def test_08_direct_seeker_printer_uuid_lineage(self):
        result = self.engine.lineage(SEEKER)
        entities = [item for item in result["results"] if item["kind"] == "entity"]
        versions = [item["payload"]["version"] for item in entities]
        self.assertEqual(versions, ["aura-2.6.1-sk3", "aura-2.6.2", "rocket-v13", "rocket-v15"])
        links = [item for item in result["results"] if item["kind"] == "identity_link"]
        self.assertTrue(any(item["payload"]["from_source_version"].startswith("aura-") and item["payload"]["to_source_version"] == "rocket-v13" for item in links))

    def test_09_x_ccf_composite_lineage(self):
        result = self.engine.lineage(X_CCF)
        entities = [item for item in result["results"] if item["kind"] == "entity"]
        self.assertEqual(
            [(item["payload"]["version"], item["payload"]["entity_type"]) for item in entities],
            [("aura-2.6.1-sk3", "composite"), ("rocket-v13", "composite"), ("rocket-v15", "composite")],
        )

    def test_10_confirmed_view_never_promotes_aura_inference(self):
        answer = self.engine.answer_unit("LinearDensity", "FIBRESEEK_CONFIRMED")
        self.assertFalse(any(item["classification"] == "INFERENCE" for item in answer["assertions"]))
        self.assertFalse(any(item["evidence_scope"] == "HISTORICAL_ANISOPRINT" for item in answer["assertions"]))
        self.assertTrue(all(not source.startswith("AP-") for item in answer["assertions"] for source in item["source_ids"]))
        self.assertTrue(
            all(
                not source.startswith("AP-")
                for question in answer["open_questions"]
                for source in question["source_ids"]
            )
        )


class QueryEngineInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="fibreseeker-query-invariants-")
        cls.db = Path(cls.temporary.name) / "query.sqlite3"
        cls.build = build_index(REPO, cls.db)
        cls.engine = QueryEngine(REPO, cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()
        cls.temporary.cleanup()

    def test_index_counts_match_canonical_summary(self):
        summary = json.loads((REPO / "data/profiles/generated/summary.json").read_text())
        self.assertEqual(self.build["entity_count"], summary["total_entities"])
        self.assertEqual(self.build["field_count"], summary["total_fields"])
        self.assertEqual(self.build["identity_link_count"], summary["identity_link_count"])
        self.assertEqual(self.build["delta_count"], sum(summary["delta_counts"].values()))

    def test_index_regeneration_is_byte_deterministic(self):
        second = Path(self.temporary.name) / "query-second.sqlite3"
        rebuilt = build_index(REPO, second)
        self.assertEqual(self.build["input_digest"], rebuilt["input_digest"])
        self.assertEqual(self.build["database_sha256"], rebuilt["database_sha256"])
        self.assertEqual(self.db.read_bytes(), second.read_bytes())

    def test_compact_response_is_deterministic(self):
        first = self.engine.field_history("MacroLayerHeight", identity=MIGRATED_PROFILE, compact=True)
        second = self.engine.field_history("MacroLayerHeight", identity=MIGRATED_PROFILE, compact=True)
        self.assertEqual(canonical_json(first), canonical_json(second))

    def test_canonical_reference_resolves_to_exact_record(self):
        result = self.engine.field_history("CutDistance", identity=CFC, compact=True)["results"][0]
        reference = result["canonical_ref"]
        with (REPO / reference["path"]).open(encoding="utf-8") as source:
            hashes = {
                hashlib.sha256(line.rstrip("\n").encode()).hexdigest()
                for line in source
                if line.strip()
            }
        self.assertIn(reference["record_sha256"], hashes)

    def test_source_ids_and_acquisition_metadata_are_preserved(self):
        source = self.engine.source("FS-125", "ALL_EVIDENCE")["results"][0]
        self.assertEqual(source["payload"]["publisher"], "FibreSeek")
        self.assertEqual(source["payload"]["acquisition_status"], "acquired")
        self.assertEqual(source["source_ids"], ["FS-125"])
        self.assertNotIn("local_path", source["payload"])

    def test_every_manifest_source_id_is_resolvable(self):
        manifest_ids = {
            json.loads(line)["record_id"]
            for line in (REPO / "sources/manifest.jsonl").read_text().splitlines()
            if line
        }
        indexed_ids = {
            row[0] for row in self.engine.connection.execute("SELECT source_id FROM sources")
        }
        self.assertEqual(indexed_ids, manifest_ids)

    def test_field_result_preserves_source_native_and_input_metadata(self):
        result = self.engine.field_history(
            "CutDistance", identity=CFC, compact=True
        )["results"][0]["payload"]
        native = result["source_native_identity"]
        self.assertTrue(native["original_uuid"])
        self.assertTrue(native["source_entity_type"])
        self.assertIsInstance(native["source_row_index"], int)
        self.assertTrue(result["source_metadata"]["acquired_utc"])
        self.assertTrue(result["source_metadata"]["input_path"])
        self.assertRegex(result["source_metadata"]["input_sha256"], r"^[0-9a-f]{64}$")

    def test_open_questions_are_first_class(self):
        result = self.engine.questions("ALL_EVIDENCE")
        self.assertEqual(result["result_count"], 10)
        self.assertTrue(all(item["classification"] == "OPEN_QUESTION" for item in result["results"]))
        self.assertEqual(
            {item["payload"]["resolution_requirement"] for item in result["results"]},
            {"STATIC_FIRST_PARTY", "VENDOR_CONFIRMATION", "OFFLINE_RUNTIME_TEST"},
        )

    def test_override_question_is_associated_with_override_fields(self):
        result = self.engine.questions(
            "ALL_EVIDENCE", field_name="MacroLayerHeight"
        )
        self.assertIn(
            "Q-ROCKET-OVERRIDE-PRECEDENCE",
            {item["payload"]["question_id"] for item in result["results"]},
        )

    def test_material_and_profile_graphs_follow_two_explicit_fk_hops(self):
        material = self.engine.graph(X_CCF, domain="materials")
        material_types = {
            item["payload"]["entity_type"]
            for item in material["results"]
            if item["kind"] == "entity"
        }
        self.assertIn("profile", material_types)
        profile = self.engine.graph(MIGRATED_PROFILE, domain="profiles")
        profile_types = {
            item["payload"]["entity_type"]
            for item in profile["results"]
            if item["kind"] == "entity"
        }
        self.assertTrue({"plastic", "composite"} & profile_types)

    def test_branch_origin_delta_expression_is_queryable(self):
        result = self.engine.deltas(
            "aura-2.6.2+aura-2.6.1-sk3", "rocket-v13", limit=2000
        )
        self.assertTrue(result["results"])
        self.assertTrue(
            all(
                item["payload"]["comparison_id"]
                == "aura-seeker-branches__rocket-v13"
                for item in result["results"]
            )
        )

    def test_cutter_conflict_keeps_all_values_visible(self):
        answer = self.engine.answer_cutter("LINEAGE_AWARE")
        rocket = {
            (item["predicate"], item["value"])
            for item in answer["assertions"]
            if item["subject"].startswith("rocket-")
        }
        self.assertEqual(
            rocket,
            {("CutDistance", 58), ("FiberRestartLength", 55), ("CutCode_comment_distance", 54.8)},
        )
        self.assertIsNone(answer["operating_recommendation"])

    def test_index_contains_no_forbidden_personal_application_fields(self):
        connection = sqlite3.connect(self.db)
        forbidden = ("CompanyId", "UserId", "ProjectId", "SourceProjectId")
        count = connection.execute(
            f"SELECT count(*) FROM fields WHERE field_name IN ({','.join('?' for _ in forbidden)})",
            forbidden,
        ).fetchone()[0]
        connection.close()
        self.assertEqual(count, 0)

    def test_querying_does_not_modify_canonical_inputs(self):
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths(REPO)}
        self.engine.entity(SEEKER, compact=True)
        self.engine.deltas("rocket-v13", "rocket-v15", entity_type="profile")
        self.engine.questions()
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths(REPO)}
        self.assertEqual(before, after)

    def test_view_modes_preserve_labels(self):
        confirmed = self.engine.entity(X_CCF, "FIBRESEEK_CONFIRMED", field_name="LinearDensity", compact=True)
        historical = self.engine.entity(X_CCF, "HISTORICAL", field_name="LinearDensity", compact=True)
        self.assertTrue(all(item["evidence_scope"] == "FIBRESEEK_FIRST_PARTY" for item in confirmed["results"]))
        self.assertTrue(all(item["evidence_scope"] == "HISTORICAL_ANISOPRINT" for item in historical["results"]))
        self.assertTrue(
            all(
                "unit" not in field
                and field["filtered_assertions"][0]["classification"] == "INFERENCE"
                for item in confirmed["results"]
                for field in item["payload"]["fields"]
            )
        )

    def test_confirmed_structured_answers_tolerate_filtered_units_and_sources(self):
        cutter = self.engine.answer_cutter("FIBRESEEK_CONFIRMED")
        macro = self.engine.answer_field(
            "MacroLayerHeight", MIGRATED_PROFILE, "FIBRESEEK_CONFIRMED"
        )
        self.assertEqual(cutter["answer_status"], "CONFLICTING")
        self.assertEqual(macro["answer_status"], "UNRESOLVED")
        self.assertTrue(
            all(
                not source_id.startswith("AP-")
                for answer in (cutter, macro)
                for assertion in answer["assertions"]
                for source_id in assertion["source_ids"]
            )
        )


if __name__ == "__main__":
    unittest.main()
