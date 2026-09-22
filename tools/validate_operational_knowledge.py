#!/usr/bin/env python3
"""Validate Phase 2F-A structure, evidence boundaries, and optional raw hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


DOMAINS = {"calibration", "manufacturability", "composite_layer_architecture", "fiber_path_generation", "design_rules", "materials_process", "cutter_feed_mechanics", "diagnostics", "maintenance"}
OP_REQUIRED = {"record_id", "domain", "concept", "manufacturer_scope", "system_scope", "machine_scope", "software_scope", "material_scope", "source_ids", "source_references", "source_claim", "normalized_interpretation", "value", "unit", "qualifier", "evidence_classification", "assertion_kind", "guidance_status", "historical_context", "fibreseek_applicability", "confidence", "relationships", "unresolved_fibreseek_question", "notes"}
VIDEO_REQUIRED = {"video_id", "title", "course", "canonical_page", "page_source_id", "host", "host_video_id", "host_url", "publication_date", "duration", "description", "relevance", "related_written_source_ids", "transcript_status", "transcript_source_id", "annotation_status", "notes"}
QUESTION_REQUIRED = {"question_id", "domain", "question", "why_it_matters", "motivating_analog_record_ids", "evidence_needed", "resolution_class", "status", "notes"}


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unique(records: list[dict], field: str, errors: list[str]) -> None:
    vals = [r[field] for r in records]
    if len(vals) != len(set(vals)):
        errors.append(f"duplicate {field}")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-archive", action="store_true")
    args = parser.parse_args()
    root = args.repo.resolve()
    manifest_records = jsonl(root / "sources/manifest.jsonl")
    manifest = {r["record_id"]: r for r in manifest_records}
    ops = jsonl(root / "data/operational/records/operational_knowledge.jsonl")
    videos = jsonl(root / "data/operational/training/video_inventory.jsonl")
    questions = jsonl(root / "data/operational/questions/fibreseek_validation_questions.jsonl")
    fixtures = json.loads((root / "data/operational/fixtures/regression_cases.json").read_text(encoding="utf-8"))["cases"]
    errors: list[str] = []
    unique(manifest_records, "record_id", errors)
    unique(ops, "record_id", errors)
    unique(videos, "video_id", errors)
    unique(questions, "question_id", errors)
    for rec in ops:
        if set(rec) != OP_REQUIRED:
            errors.append(f"{rec.get('record_id')}: operational fields differ from contract")
        if rec["domain"] not in DOMAINS:
            errors.append(f"{rec['record_id']}: invalid domain")
        if rec["manufacturer_scope"] != "ANISOPRINT" or rec["evidence_classification"] not in {"ANISOPRINT_OFFICIAL", "INFERENCE"}:
            errors.append(f"{rec['record_id']}: evidence boundary violated")
        if rec["fibreseek_applicability"] == "CONFIRMED_EQUIVALENT":
            errors.append(f"{rec['record_id']}: Anisoprint evidence promoted to CONFIRMED_EQUIVALENT")
        if not rec["source_ids"] or not rec["source_references"] or not rec["source_claim"].strip():
            errors.append(f"{rec['record_id']}: missing provenance")
        for sid in rec["source_ids"]:
            if sid not in manifest:
                errors.append(f"{rec['record_id']}: unknown source {sid}")
        for ref in rec["source_references"]:
            if ref["source_id"] not in rec["source_ids"] or not ref["location"].strip():
                errors.append(f"{rec['record_id']}: invalid source reference")
        if rec["assertion_kind"].startswith("CODE_") or rec["assertion_kind"] == "COMMENT":
            if rec["guidance_status"] != "NOT_GUIDANCE":
                errors.append(f"{rec['record_id']}: static code became guidance")
        if rec["value"] is not None and rec["unit"] is None and not (rec["qualifier"] and "unit" in rec["qualifier"].lower()):
            errors.append(f"{rec['record_id']}: unqualified unitless value")
    if set(r["domain"] for r in ops) != DOMAINS:
        errors.append("not every operational domain is represented")
    for video in videos:
        if set(video) != VIDEO_REQUIRED:
            errors.append(f"{video.get('video_id')}: video fields differ from contract")
        if video["page_source_id"] not in manifest or video["host"] != "VIMEO":
            errors.append(f"{video['video_id']}: invalid official page linkage")
        if video["transcript_status"] == "NOT_PUBLICLY_EXPOSED" and video["transcript_source_id"] is not None:
            errors.append(f"{video['video_id']}: unavailable transcript has a source")
    op_ids = {r["record_id"] for r in ops}
    for q in questions:
        if set(q) != QUESTION_REQUIRED or not set(q["motivating_analog_record_ids"]) <= op_ids:
            errors.append(f"{q.get('question_id')}: invalid question linkage")
    expected_topics = {"macrolayer semantics", "nozzle XY calibration", "composite Z-offset calibration", "minimum fiber length", "hole-adjacent fiber constraint", "cutter/restart behavior", "diagnostic/failure-mode chain", "training-video-derived claim", "firmware code constant", "analog value promotion"}
    if {f["topic"] for f in fixtures} != expected_topics:
        errors.append("regression fixture coverage mismatch")
    for fixture in fixtures:
        if "record_ids" in fixture and not set(fixture["record_ids"]) <= op_ids:
            errors.append(f"{fixture['fixture_id']}: unknown operational record")
    synthetic = next(f for f in fixtures if f["topic"] == "training-video-derived claim")["synthetic_record"]
    if synthetic != {"assertion_kind": "HUMAN_TIMESTAMP_NOTE", "guidance_status": "UNVERIFIED_NOTE", "fibreseek_applicability": "UNRESOLVED", "source_reference": "VID-AP-124 @ 12:43"}:
        errors.append("training-note safety fixture changed")
    firmware = next(r for r in ops if r["concept"] == "firmware hotend-offset constants")
    if firmware["guidance_status"] != "NOT_GUIDANCE" or firmware["fibreseek_applicability"] != "NO_KNOWN_EQUIVALENT":
        errors.append("firmware constant promotion guard failed")
    failed = [r for r in manifest_records if r["acquisition_status"] in {"failed", "blocked"}]
    if not any(r["record_id"] == "AP-120" and r["http_status"] == 404 for r in failed):
        errors.append("NozzleOffsetTest failure state was dropped")
    summary = json.loads((root / "data/profiles/generated/summary.json").read_text(encoding="utf-8"))
    if (summary["total_entities"], summary["total_fields"], summary["identity_link_count"], sum(summary["delta_counts"].values())) != (620, 45721, 298, 23022):
        errors.append("accepted Phase 2A canonical counts mutated")
    git_index = json.loads((root / "data/operational/corpus/github_index.json").read_text(encoding="utf-8"))
    expected_commits = {"aura-docs": "3fa58f9590b581a3df3da6cd4f1c4ba919599bc0", "MKA-firmware": "6e02973b1b8f325040cc3dbf66ac545ffc5c06b3"}
    for corpus in git_index["corpora"]:
        if corpus["commit_sha"] != expected_commits.get(corpus["name"]) or corpus["inspection_mode"] != "STATIC_ONLY":
            errors.append(f"{corpus['name']}: immutable Git index mismatch")
    if args.verify_archive:
        for rec in manifest_records:
            if not ("AP-114" <= rec["record_id"] <= "AP-148") or rec["acquisition_status"] != "acquired" or rec["local_path"] is None:
                continue
            path = Path(rec["local_path"])
            if not path.is_file():
                errors.append(f"{rec['record_id']}: archived original missing")
            elif sha(path) != rec["sha256"]:
                errors.append(f"{rec['record_id']}: archived original hash mismatch")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Validated Phase 2F-A: {len(ops)} records {dict(sorted(Counter(r['domain'] for r in ops).items()))}; {len(videos)} videos; {len(questions)} open questions; {len(fixtures)} fixtures; {len(failed)} preserved failed/blocked acquisitions.")


if __name__ == "__main__":
    main()
