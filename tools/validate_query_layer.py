#!/usr/bin/env python3
"""Validate Phase 2B query/index evidence, determinism, and safety invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from query_engine import QueryEngine, build_index, canonical_json, input_digest


FORBIDDEN_FIELDS = {"CompanyId", "UserId", "ProjectId", "SourceProjectId"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    parser.add_argument("--check-determinism", action="store_true")
    return parser.parse_args()


def record_hashes(path: Path) -> set[str]:
    with path.open(encoding="utf-8") as source:
        return {
            hashlib.sha256(line.rstrip("\n").encode("utf-8")).hexdigest()
            for line in source
            if line.strip()
        }


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    default_db = repo_root / ".cache/fibreseeker-query.sqlite3"
    db_path = (args.db or default_db).resolve()
    errors: list[str] = []
    if not db_path.exists():
        errors.append(f"missing query index: {db_path}")
    if errors:
        raise SystemExit("\n".join(errors))

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        errors.append(f"SQLite integrity check failed: {integrity}")
    metadata = {row["key"]: row["value"] for row in connection.execute("SELECT * FROM metadata")}
    current_digest, _ = input_digest(repo_root)
    if metadata.get("input_digest") != current_digest:
        errors.append("query index input digest is stale")

    summary = json.loads(
        (repo_root / "data/profiles/generated/summary.json").read_text(encoding="utf-8")
    )
    expected = {
        "entity_count": summary["total_entities"],
        "field_count": summary["total_fields"],
        "identity_link_count": summary["identity_link_count"],
        "relationship_count": summary["foreign_key_relationship_count"],
        "delta_count": sum(summary["delta_counts"].values()),
    }
    for key, value in expected.items():
        if int(metadata.get(key, -1)) != value:
            errors.append(f"{key} mismatch: {metadata.get(key)} != {value}")
    manifest_count = sum(
        bool(line.strip())
        for line in (repo_root / "sources/manifest.jsonl").read_text(encoding="utf-8").splitlines()
    )
    if int(metadata.get("source_count", -1)) != manifest_count:
        errors.append(
            f"source_count mismatch: {metadata.get('source_count')} != {manifest_count}"
        )

    placeholders = ",".join("?" for _ in FORBIDDEN_FIELDS)
    forbidden_count = connection.execute(
        f"SELECT count(*) FROM fields WHERE field_name IN ({placeholders})",
        sorted(FORBIDDEN_FIELDS),
    ).fetchone()[0]
    if forbidden_count:
        errors.append(f"forbidden personal/application fields indexed: {forbidden_count}")
    source_columns = {row[1] for row in connection.execute("PRAGMA table_info(sources)")}
    if "local_path" in source_columns:
        errors.append("source local_path must not enter query index")

    canonical_cache: dict[str, set[str]] = {}
    for table, id_column in (
        ("entities", "entity_record_id"),
        ("identity_links", "link_id"),
        ("relationships", "relationship_id"),
        ("deltas", "delta_id"),
    ):
        for row in connection.execute(
            f"SELECT {id_column},canonical_path,record_sha256 FROM {table}"
        ):
            path = row["canonical_path"]
            if path not in canonical_cache:
                canonical_cache[path] = record_hashes(repo_root / path)
            if row["record_sha256"] not in canonical_cache[path]:
                errors.append(f"unresolvable canonical record: {table} {row[id_column]}")
                break
    connection.close()

    engine = QueryEngine(repo_root, db_path)
    confirmed = engine.answer_unit("LinearDensity", "FIBRESEEK_CONFIRMED")
    if any(item["classification"] == "INFERENCE" for item in confirmed["assertions"]):
        errors.append("FIBRESEEK_CONFIRMED emitted an inference")
    if any(
        source_id.startswith("AP-")
        for item in confirmed["assertions"]
        for source_id in item["source_ids"]
    ):
        errors.append("FIBRESEEK_CONFIRMED emitted Aura evidence")
    if any(
        source_id.startswith("AP-")
        for item in confirmed["open_questions"]
        for source_id in item["source_ids"]
    ):
        errors.append("FIBRESEEK_CONFIRMED open-question view emitted Aura evidence")
    questions = engine.questions("ALL_EVIDENCE")
    if questions["result_count"] != int(metadata["question_count"]):
        errors.append("open-question count mismatch")
    cutter = engine.answer_cutter("LINEAGE_AWARE")
    if cutter["answer_status"] != "CONFLICTING" or cutter["operating_recommendation"] is not None:
        errors.append("cutter conflict was collapsed or promoted to a recommendation")
    compact_one = engine.field_history(
        "MacroLayerHeight", identity="d294a2dc-9d7f-460a-acf4-dc50b656d44a", compact=True
    )
    compact_two = engine.field_history(
        "MacroLayerHeight", identity="d294a2dc-9d7f-460a-acf4-dc50b656d44a", compact=True
    )
    if canonical_json(compact_one) != canonical_json(compact_two):
        errors.append("compact JSON response is non-deterministic")
    query_required = {
        "contract_version", "query", "view_mode", "result_count", "results", "warnings", "index"
    }
    result_required = {
        "kind", "classification", "evidence_scope", "provenance_class", "source_ids",
        "manufacturer_guidance", "canonical_ref", "payload",
    }
    for response in (compact_one, questions, engine.enum("InfillFType")):
        if set(response) != query_required:
            errors.append("query response does not match contract top-level keys")
        if any(set(item) != result_required for item in response["results"]):
            errors.append("query result does not match contract result keys")
    answer_required = {
        "answer_version", "question", "view_mode", "answer_status", "assertions", "conflicts",
        "open_questions", "operating_recommendation", "warnings",
    }
    if set(confirmed) != answer_required or set(cutter) != answer_required:
        errors.append("engineering answer does not match contract top-level keys")
    engine.close()

    determinism = None
    if args.check_determinism:
        with tempfile.TemporaryDirectory(prefix="fibreseeker-index-validation-") as temporary:
            first = build_index(repo_root, Path(temporary) / "first.sqlite3")
            second = build_index(repo_root, Path(temporary) / "second.sqlite3")
            determinism = first["database_sha256"]
            if first["database_sha256"] != second["database_sha256"]:
                errors.append("index rebuild is not byte-deterministic")

    if errors:
        raise SystemExit("\n".join(errors))
    suffix = f", deterministic SHA-256 {determinism}" if determinism else ""
    print(
        f"Validated Phase 2B index: {expected['entity_count']} entities, "
        f"{expected['field_count']} fields, {expected['delta_count']} deltas, "
        f"{metadata['question_count']} open questions{suffix}."
    )


if __name__ == "__main__":
    main()
