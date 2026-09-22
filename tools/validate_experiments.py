#!/usr/bin/env python3
"""Validate physical-experiment evidence, classifications, and provenance."""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import resolve_recorded_path


CLASS_BASIS = {
    "CONFIRMED": {"REPOSITORY_ARTIFACT", "CROSS_SESSION_ARTIFACT", "NAS_PRIMARY_ARTIFACT"},
    "USER-OBSERVED": {"OWNER_RETROSPECTIVE"},
    "STRONGLY INFERRED": {"DERIVED_INTERPRETATION"},
    "UNKNOWN / EVIDENCE MISSING": {"MISSING_PRIMARY_ARTIFACT"},
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args()


def load_jsonl(path):
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append((line_number, json.loads(line)))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error
    return records


def validate_source_artifacts(repo, manifest):
    experiment_root = (repo / "sources/loom/experiments").resolve()
    for source_id in ("LX-001", "LX-002", "LX-003", "LX-004"):
        if source_id not in manifest:
            raise ValueError(f"missing experiment source {source_id}")
        source = manifest[source_id]
        if source["provenance_class"] != "EXPERIMENTAL":
            raise ValueError(f"{source_id}: source must be EXPERIMENTAL")
        path = resolve_recorded_path(source["local_path"], repo).resolve()
        if experiment_root not in path.parents:
            raise ValueError(f"{source_id}: source path escapes experiment source tree")
        if not path.is_file():
            raise ValueError(f"{source_id}: missing source artifact")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != source["sha256"]:
            raise ValueError(f"{source_id}: SHA-256 mismatch")
        if len(content) != source["byte_size"]:
            raise ValueError(f"{source_id}: byte-size mismatch")


def validate_record(line_number, record, schema, manifest_ids):
    prefix = f"record line {line_number} ({record.get('record_id', 'unknown')})"
    required = set(schema["required"])
    properties = set(schema["properties"])
    missing = required - record.keys()
    extra = record.keys() - properties
    if missing:
        raise ValueError(f"{prefix}: missing fields {sorted(missing)}")
    if extra:
        raise ValueError(f"{prefix}: unexpected fields {sorted(extra)}")

    if not re.fullmatch(r"LXE-[0-9]{4}", record["record_id"]):
        raise ValueError(f"{prefix}: invalid record_id")
    if record["experiment_id"] != "LOOM-2026-09-07":
        raise ValueError(f"{prefix}: incorrect experiment_id")
    if record["experiment_date"] != "2026-09-07" or record["machine"] != "Loom":
        raise ValueError(f"{prefix}: incorrect experiment scope")

    for name in ("domain", "classification", "evidence_basis", "chronology_precision", "confidence", "status"):
        allowed = set(schema["properties"][name]["enum"])
        if record[name] not in allowed:
            raise ValueError(f"{prefix}: invalid {name}")
    if record["evidence_basis"] not in CLASS_BASIS[record["classification"]]:
        raise ValueError(f"{prefix}: classification and evidence_basis conflict")
    expected_status = "EVIDENCE_GAP" if record["classification"] == "UNKNOWN / EVIDENCE MISSING" else "PRESERVED"
    if record["status"] != expected_status:
        raise ValueError(f"{prefix}: classification and status conflict")

    if not isinstance(record["sequence"], int) or isinstance(record["sequence"], bool) or record["sequence"] < 1:
        raise ValueError(f"{prefix}: invalid sequence")
    for name in ("claim", "limitations"):
        if not isinstance(record[name], str) or not record[name].strip():
            raise ValueError(f"{prefix}: empty {name}")
    if record["reported_value_text"] is not None:
        if record["classification"] != "USER-OBSERVED":
            raise ValueError(f"{prefix}: reported values are permitted only for USER-OBSERVED records")
        if not isinstance(record["reported_value_text"], str) or not record["reported_value_text"].strip():
            raise ValueError(f"{prefix}: invalid reported_value_text")

    source_ids = record["source_ids"]
    if not isinstance(source_ids, list) or not source_ids or len(source_ids) != len(set(source_ids)):
        raise ValueError(f"{prefix}: invalid source_ids")
    unknown_sources = set(source_ids) - manifest_ids
    if unknown_sources:
        raise ValueError(f"{prefix}: unknown source IDs {sorted(unknown_sources)}")
    references = record["source_references"]
    if not isinstance(references, list) or not references:
        raise ValueError(f"{prefix}: source_references must not be empty")
    reference_ids = []
    for reference in references:
        if set(reference) != {"source_id", "locator"} or not reference["locator"].strip():
            raise ValueError(f"{prefix}: invalid source reference")
        reference_ids.append(reference["source_id"])
    if set(reference_ids) != set(source_ids):
        raise ValueError(f"{prefix}: source references do not match source_ids")

    if record["classification"] == "USER-OBSERVED" and "LX-001" not in source_ids:
        raise ValueError(f"{prefix}: USER-OBSERVED record lacks owner retrospective")
    if any(source_id.startswith("LM-") for source_id in source_ids) and record["domain"] != "session_boundary":
        raise ValueError(f"{prefix}: Sep 8 live evidence leaked outside session boundary")


def main():
    args = parse_args()
    repo = args.repo.resolve()
    schema_path = repo / "experiments/schemas/physical-experiment-record.schema.json"
    records_path = repo / "experiments/Loom/2026-09-07/experiment_records.jsonl"
    gaps_path = repo / "experiments/Loom/2026-09-07/EVIDENCE_GAPS.md"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest_rows = load_jsonl(repo / "sources/manifest.jsonl")
    manifest = {record["record_id"]: record for _, record in manifest_rows}
    validate_source_artifacts(repo, manifest)

    rows = load_jsonl(records_path)
    if not rows:
        raise ValueError("no physical experiment records")
    record_ids = [record["record_id"] for _, record in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("duplicate experiment record_id")
    sequences = [record["sequence"] for _, record in rows]
    if sequences != list(range(1, len(rows) + 1)):
        raise ValueError("experiment sequences are not contiguous in file order")
    for line_number, record in rows:
        validate_record(line_number, record, schema, set(manifest))

    classifications = Counter(record["classification"] for _, record in rows)
    missing_classes = set(CLASS_BASIS) - classifications.keys()
    if missing_classes:
        raise ValueError(f"missing evidence classifications: {sorted(missing_classes)}")
    if not gaps_path.is_file() or "# Evidence gaps" not in gaps_path.read_text(encoding="utf-8"):
        raise ValueError("missing EVIDENCE_GAPS.md")

    print(f"Validated {len(rows)} Loom physical-experiment records: {dict(sorted(classifications.items()))}.")


if __name__ == "__main__":
    main()
