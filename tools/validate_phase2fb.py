#!/usr/bin/env python3
"""Validate Phase 2F-B direct evidence, FSQ overlays, and inherited boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


BASELINE = "d49899368227979c9ea743ed09fff9b4bba06c88"
ANALOG_HASHES = {
    "data/operational/records/operational_knowledge.jsonl": "ecf44a5e41cdcad8e4304b53d974f35ed5fb23929507e4f37037b0a5a9b1f9fd",
    "data/operational/questions/fibreseek_validation_questions.jsonl": "b55978184d76fb90a3450c6118ba28816cdf25d4770270c33d0f2e68e840f141",
    "data/operational/fixtures/regression_cases.json": "8ae62bddb44920fc7ab7d6cee2a8f83f6b4f9db2f8d47afa5ca461f369861a87",
}
DIRECT_FIELDS = {
    "evidence_id", "domain", "fsq_ids", "evidence_class", "source_ids",
    "source_locations", "observation", "interpretation", "scope",
    "guidance_status", "status_effect", "confidence", "limitations", "baseline_commit",
}
STATUS_FIELDS = {
    "question_id", "phase2fa_status", "phase2fb_status", "direct_evidence_ids",
    "determination", "residual_unknowns", "next_resolution_class", "offline_runtime_performed",
}
EVIDENCE_CLASSES = {
    "FIBRESEEK_FIRST_PARTY", "ROCKET_STATIC_OBSERVATION", "ROCKET_OFFLINE_RUNTIME",
    "OWNER_EXPERIMENT", "VENDOR_CONFIRMATION",
}


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    errors: list[str] = []

    manifest_rows = jsonl(root / "sources/manifest.jsonl")
    manifest = {row["record_id"]: row for row in manifest_rows}
    phase2fa_questions = jsonl(root / "data/operational/questions/fibreseek_validation_questions.jsonl")
    direct = jsonl(root / "data/operational/fibreseek/records/direct_evidence.jsonl")
    statuses = jsonl(root / "data/operational/fibreseek/questions/fsq_status.jsonl")
    fixtures = json.loads((root / "data/operational/fibreseek/fixtures/regression_cases.json").read_text(encoding="utf-8"))["cases"]
    static_index = json.loads((root / "data/operational/fibreseek/static/rocket_static_index.json").read_text(encoding="utf-8"))

    fsq_ids = {row["question_id"] for row in phase2fa_questions}
    expected_fsq_ids = {f"FSQ-{index:03d}" for index in range(1, 23)}
    if fsq_ids != expected_fsq_ids:
        errors.append("inherited FSQ-001..FSQ-022 set changed")
    if len({row["evidence_id"] for row in direct}) != len(direct):
        errors.append("duplicate direct evidence ID")
    if len({row["question_id"] for row in statuses}) != len(statuses):
        errors.append("duplicate FSQ status overlay")
    if {row["question_id"] for row in statuses} != expected_fsq_ids:
        errors.append("not every FSQ has exactly one Phase 2F-B status")

    direct_by_id = {row["evidence_id"]: row for row in direct}
    for row in direct:
        eid = row.get("evidence_id", "unknown")
        if set(row) != DIRECT_FIELDS:
            errors.append(f"{eid}: direct-evidence fields differ from contract")
            continue
        if row["baseline_commit"] != BASELINE:
            errors.append(f"{eid}: baseline commit changed")
        if row["evidence_class"] not in EVIDENCE_CLASSES:
            errors.append(f"{eid}: invalid evidence class")
        if not row["fsq_ids"] or not set(row["fsq_ids"]) <= fsq_ids:
            errors.append(f"{eid}: invalid FSQ linkage")
        if not row["source_ids"] or any(sid.startswith("AP-") for sid in row["source_ids"]):
            errors.append(f"{eid}: analog source leaked into direct evidence")
        for sid in row["source_ids"]:
            if sid not in manifest or manifest[sid]["provenance_class"] != "FIBRESEEK_OFFICIAL":
                errors.append(f"{eid}: source {sid} is not valid FibreSeek first-party provenance")
        if not row["source_locations"]:
            errors.append(f"{eid}: no precise source location")
        for source_location in row["source_locations"]:
            if source_location.get("source_id") not in row["source_ids"]:
                errors.append(f"{eid}: source location does not resolve to source_ids")
            if not source_location.get("artifact", "").strip() or not source_location.get("locator", "").strip():
                errors.append(f"{eid}: empty artifact or locator")
        if row["evidence_class"] == "ROCKET_STATIC_OBSERVATION" and row["guidance_status"] == "MANUFACTURER_GUIDANCE":
            errors.append(f"{eid}: Rocket static observation promoted to guidance")
        if row["guidance_status"] in {"STATIC_CODE_INDICATOR", "BOUNDED_SEARCH_ABSENCE"} and row["status_effect"] == "RESOLVES":
            errors.append(f"{eid}: weak static/search evidence resolved a question")
        if not all(row[field].strip() for field in ("observation", "interpretation", "scope", "limitations")):
            errors.append(f"{eid}: empty evidence narrative")

    for row in statuses:
        qid = row.get("question_id", "unknown")
        if set(row) != STATUS_FIELDS:
            errors.append(f"{qid}: status fields differ from contract")
            continue
        if row["phase2fa_status"] != "OPEN":
            errors.append(f"{qid}: historical Phase 2F-A status rewritten")
        if row["offline_runtime_performed"] is not False:
            errors.append(f"{qid}: unexpected runtime flag")
        if not set(row["direct_evidence_ids"]) <= set(direct_by_id):
            errors.append(f"{qid}: unknown direct evidence linkage")
        for eid in row["direct_evidence_ids"]:
            if qid not in direct_by_id[eid]["fsq_ids"]:
                errors.append(f"{qid}: evidence {eid} does not link back")
        if row["phase2fb_status"] == "RESOLVED":
            supporting = [direct_by_id[eid] for eid in row["direct_evidence_ids"]]
            if not any(item["status_effect"] == "RESOLVES" and item["confidence"] == "HIGH" for item in supporting):
                errors.append(f"{qid}: resolved without high-confidence resolving evidence")
            if row["next_resolution_class"] != "NONE":
                errors.append(f"{qid}: resolved question still has next resolution class")
        elif row["next_resolution_class"] == "NONE":
            errors.append(f"{qid}: unresolved question lacks next resolution class")

    for fixture in fixtures:
        qid = fixture["fsq_id"]
        status = next((row for row in statuses if row["question_id"] == qid), None)
        if status is None or status["phase2fb_status"] != fixture["expected_status"]:
            errors.append(f"{fixture['case_id']}: status regression failed")
        elif fixture["must_include_evidence"] not in status["direct_evidence_ids"]:
            errors.append(f"{fixture['case_id']}: evidence regression failed")

    expected_status_counts = {"OPEN": 4, "PARTIALLY_RESOLVED": 15, "RESOLVED": 3}
    if dict(Counter(row["phase2fb_status"] for row in statuses)) != expected_status_counts:
        errors.append("Phase 2F-B status counts changed unexpectedly")
    if any(row["evidence_class"] in {"ROCKET_OFFLINE_RUNTIME", "OWNER_EXPERIMENT", "VENDOR_CONFIRMATION"} for row in direct):
        errors.append("unauthorized/unperformed evidence class present")
    if static_index["execution_performed"] is not False or not static_index["not_executed"]:
        errors.append("static index execution boundary changed")
    if static_index["baseline_commit"] != BASELINE:
        errors.append("static index baseline changed")

    for relative, expected in ANALOG_HASHES.items():
        if sha(root / relative) != expected:
            errors.append(f"accepted Phase 2F-A artifact mutated: {relative}")
    summary_path = root / "data/profiles/generated/summary.json"
    if sha(summary_path) != "691a25af27e00694ece361c32e94d9d9726f14e8a4e53ad56d19caeb17d2987d":
        errors.append("accepted canonical generated summary bytes changed")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    counts = (summary["total_entities"], summary["total_fields"], summary["identity_link_count"], sum(summary["delta_counts"].values()))
    if counts != (620, 45721, 298, 23022):
        errors.append("accepted Phase 2A canonical counts changed")

    if args.verify_archive:
        for source_id in ("FS-120", "FS-122", "FS-125", "FS-133", "FS-135", "FS-137", "FS-139", "FS-142", "FS-144", "FS-147", "FS-149"):
            record = manifest[source_id]
            path = Path(record["local_path"])
            if not path.is_file():
                errors.append(f"{source_id}: archived original missing")
            elif sha(path) != record["sha256"]:
                errors.append(f"{source_id}: archived original hash mismatch")

    if errors:
        raise SystemExit("\n".join(errors))
    print(
        "Validated Phase 2F-B: "
        f"{len(direct)} direct records; {dict(sorted(expected_status_counts.items()))}; "
        f"{len(fixtures)} fixtures; canonical counts {counts}; no offline runtime evidence."
    )


if __name__ == "__main__":
    main()
