import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OPS = REPO / "data/operational/records/operational_knowledge.jsonl"
VIDEOS = REPO / "data/operational/training/video_inventory.jsonl"
QUESTIONS = REPO / "data/operational/questions/fibreseek_validation_questions.jsonl"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class OperationalKnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ops = load_jsonl(OPS)
        cls.videos = load_jsonl(VIDEOS)
        cls.questions = load_jsonl(QUESTIONS)
        cls.manifest = load_jsonl(REPO / "sources/manifest.jsonl")

    def test_validator_passes(self):
        result = subprocess.run(
            ["python3", str(REPO / "tools/validate_operational_knowledge.py")],
            cwd=REPO, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_phase2fa_schemas_are_valid_json(self):
        for path in (REPO / "data/operational/schemas").glob("*.json"):
            self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)

    def test_every_domain_and_provenance_resolve(self):
        self.assertEqual(
            set(Counter(r["domain"] for r in self.ops)),
            {"calibration", "manufacturability", "composite_layer_architecture", "fiber_path_generation", "design_rules", "materials_process", "cutter_feed_mechanics", "diagnostics", "maintenance"},
        )
        source_ids = {r["record_id"] for r in self.manifest}
        for record in self.ops:
            self.assertTrue(set(record["source_ids"]) <= source_ids)
            self.assertTrue(all(ref["location"].strip() for ref in record["source_references"]))

    def test_anisoprint_cannot_be_fibreseek_confirmed(self):
        self.assertTrue(self.ops)
        for record in self.ops:
            self.assertEqual(record["manufacturer_scope"], "ANISOPRINT")
            self.assertNotEqual(record["fibreseek_applicability"], "CONFIRMED_EQUIVALENT")

    def test_unsupported_analog_promotion_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [
                "sources/manifest.jsonl",
                "data/profiles/generated/summary.json",
                "data/operational/records/operational_knowledge.jsonl",
                "data/operational/training/video_inventory.jsonl",
                "data/operational/questions/fibreseek_validation_questions.jsonl",
                "data/operational/fixtures/regression_cases.json",
                "data/operational/corpus/github_index.json",
            ]
            for rel in paths:
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO / rel, destination)
            records = load_jsonl(root / "data/operational/records/operational_knowledge.jsonl")
            records[0]["fibreseek_applicability"] = "CONFIRMED_EQUIVALENT"
            (root / "data/operational/records/operational_knowledge.jsonl").write_text(
                "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in records),
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(REPO / "tools/validate_operational_knowledge.py"), "--repo", str(root)],
                cwd=REPO, text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("promoted to CONFIRMED_EQUIVALENT", result.stdout + result.stderr)

    def test_firmware_code_is_not_guidance(self):
        firmware_records = [r for r in self.ops if r["assertion_kind"].startswith("CODE_") or r["assertion_kind"] == "COMMENT"]
        self.assertTrue(firmware_records)
        self.assertTrue(all(r["guidance_status"] == "NOT_GUIDANCE" for r in firmware_records))
        constant = next(r for r in self.ops if r["concept"] == "firmware hotend-offset constants")
        self.assertEqual(constant["fibreseek_applicability"], "NO_KNOWN_EQUIVALENT")

    def test_45_and_12_conflicts_remain_explicit(self):
        perimeter = next(r for r in self.ops if r["concept"] == "minimum reinforced perimeter field")
        radius = next(r for r in self.ops if r["concept"] == "fiber minimum-radius profile field")
        self.assertEqual(perimeter["value"], 45.0)
        self.assertIn("not evidence of a universal", perimeter["normalized_interpretation"])
        self.assertIn("not clearance around holes", radius["normalized_interpretation"])
        self.assertIsNone(perimeter["unit"])
        self.assertIsNone(radius["unit"])

    def test_video_records_are_distinct_and_annotation_ready(self):
        self.assertEqual(len(self.videos), 7)
        for video in self.videos:
            self.assertEqual(video["transcript_status"], "NOT_PUBLICLY_EXPOSED")
            self.assertEqual(video["annotation_status"], "READY_FOR_HUMAN_NOTES")
            self.assertIsNone(video["transcript_source_id"])

    def test_failure_state_is_preserved(self):
        record = next(r for r in self.manifest if r["record_id"] == "AP-120")
        self.assertEqual(record["acquisition_status"], "failed")
        self.assertEqual(record["http_status"], 404)
        self.assertIsNone(record["sha256"])

    def test_question_backlog_is_analog_linked(self):
        op_ids = {r["record_id"] for r in self.ops}
        self.assertGreaterEqual(len(self.questions), 20)
        self.assertTrue(all(q["status"] == "OPEN" for q in self.questions))
        self.assertTrue(all(set(q["motivating_analog_record_ids"]) <= op_ids for q in self.questions))

    def test_acquisition_existing_bytes_are_idempotent_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive"
            record_dir = archive / "originals/ANISOPRINT_OFFICIAL/AP-999"
            record_dir.mkdir(parents=True)
            payload = record_dir / "fixture.txt"
            payload.write_bytes(b"immutable fixture\n")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            (record_dir / "retrieval.txt").write_text(
                "source_url=https://example.invalid/fixture\nfilename=fixture.txt\nsha256=" + digest + "\n",
                encoding="utf-8",
            )
            before = payload.read_bytes()
            env = dict(os.environ, FIBRESEEK_ARCHIVE_ROOT=str(archive))
            command = [str(REPO / "tools/acquire_source.sh"), "AP-999", "https://example.invalid/fixture", "fixture.txt", "ANISOPRINT_OFFICIAL"]
            for _ in range(2):
                result = subprocess.run(command, cwd=REPO, env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("byte-identical", result.stdout)
            self.assertEqual(payload.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
