import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from normalized_model import (  # noqa: E402
    build_field,
    canonical_field_name,
    canonical_json,
    compare_entity_groups,
    normalize_uuid,
)


class NormalizedModelTests(unittest.TestCase):
    def setUp(self):
        self.aura = {"software": "Aura"}
        self.rocket = {"software": "Rocket"}

    def test_uuid_normalization(self):
        self.assertEqual(
            normalize_uuid("2af8ac624968436488e31045ef47feba"),
            "2af8ac62-4968-4364-88e3-1045ef47feba",
        )
        self.assertIsNone(normalize_uuid("not-a-uuid"))

    def test_alias_is_explicit(self):
        aliases = {
            ("Aura", "profile", "FiberMinRadiusF"): {
                "canonical": "FiberMinRadius",
                "classification": "INFERENCE",
                "source_ids": ["AP-105", "FS-121"],
            }
        }
        name, alias = canonical_field_name(
            "Aura", "profile", "FiberMinRadiusF", 12, aliases
        )
        self.assertEqual(name, "FiberMinRadius")
        self.assertEqual(alias["classification"], "INFERENCE")

    def test_aura_override_effective_is_inferred(self):
        field = build_field(
            self.aura,
            "profile",
            "MacroLayerHeight",
            0.24,
            "MacroLayerHeightOver",
            0.24,
            {},
            {},
        )
        self.assertEqual(field["effective_value"], 0.24)
        self.assertEqual(field["effective_value_status"], "inferred")
        self.assertTrue(field["runtime_precedence_documented"])

    def test_rocket_override_effective_remains_unknown(self):
        field = build_field(
            self.rocket,
            "profile",
            "MacroLayerHeight",
            0.2,
            "MacroLayerHeightOver",
            0.24,
            {},
            {},
        )
        self.assertIsNone(field["effective_value"])
        self.assertEqual(field["effective_value_status"], "unknown")

    def test_inferred_unit_remains_inference(self):
        units = {
            ("Rocket", "LinearDensity"): {
                "unit": "tex",
                "status": "inferred",
                "classification": "INFERENCE",
                "source_ids": ["AP-107", "AP-105", "FS-121"],
                "notes": "lineage",
            }
        }
        field = build_field(
            self.rocket, "composite", "LinearDensity", 102, None, None, {}, units
        )
        self.assertEqual(field["normalized_unit"], "tex")
        self.assertEqual(field["unit_evidence_classification"], "INFERENCE")

    def test_delta_detects_base_to_override_migration(self):
        left_field = build_field(
            self.aura,
            "profile",
            "MacroLayerHeight",
            0.24,
            "MacroLayerHeightOver",
            0.24,
            {},
            {},
        )
        right_field = build_field(
            self.rocket,
            "profile",
            "MacroLayerHeight",
            0.2,
            "MacroLayerHeightOver",
            0.24,
            {},
            {},
        )
        common = {
            "entity_type": "profile",
            "canonical_entity_id": "uuid:d294a2dc-9d7f-460a-acf4-dc50b656d44a",
            "application_key": None,
            "source_ids": ["AP-105"],
            "source_format": "sqlite",
            "source_entity_type": "Profile",
        }
        left = {**common, "entity_record_id": "left", "fields": {"MacroLayerHeight": left_field}}
        right = {
            **common,
            "entity_record_id": "right",
            "application_key": 2499,
            "source_ids": ["FS-121"],
            "source_format": "json_directory",
            "source_entity_type": "Profiles.json",
            "fields": {"MacroLayerHeight": right_field},
        }
        deltas = compare_entity_groups(
            "test", "aura", "rocket", "profile", common["canonical_entity_id"], [left], [right]
        )
        macro = next(delta for delta in deltas if delta["field_name"] == "MacroLayerHeight")
        self.assertIn("value_changed", macro["classifications"])
        self.assertIn("structurally_changed", macro["classifications"])

    def test_canonical_json_is_deterministic(self):
        self.assertEqual(canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}')


if __name__ == "__main__":
    unittest.main()
