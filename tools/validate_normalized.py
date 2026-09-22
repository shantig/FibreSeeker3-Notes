#!/usr/bin/env python3
"""Validate provenance, identity, evidence, and safety invariants."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from normalized_model import (
    DELTA_CLASSES,
    EFFECTIVE_STATUSES,
    EVIDENCE_CLASSES,
    load_json,
    load_jsonl,
    load_manifest,
    normalize_uuid,
    sha256_file,
)


FORBIDDEN_FIELDS = {"CompanyId", "UserId", "ProjectId", "SourceProjectId"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    normalized_root = repo_root / "data/profiles"
    generated_root = normalized_root / "generated"
    manifest = load_manifest(repo_root / "sources/manifest.jsonl")
    source_registry = {item["source_version_id"]: item for item in load_json(generated_root / "sources.json")}
    units = load_json(normalized_root / "registries/unit_registry.json")["units"]
    enums = load_json(normalized_root / "registries/enum_registry.json")["enums"]
    aliases = load_json(normalized_root / "registries/field_aliases.json")["aliases"]
    summary = load_json(generated_root / "summary.json")
    errors: list[str] = []
    entity_records = []

    for path in sorted((generated_root / "versions").glob("*/entities.jsonl")):
        for record in load_jsonl(path):
            entity_records.append(record)
            version = record["source_version_id"]
            require(version in source_registry, f"unknown source version: {version}", errors)
            require(record["source_ids"], f"missing source IDs: {record['entity_record_id']}", errors)
            for source_id in record["source_ids"]:
                require(source_id in manifest, f"unknown source ID: {source_id}", errors)
                if source_id in manifest:
                    require(
                        manifest[source_id]["provenance_class"] == record["provenance_class"],
                        f"provenance mismatch: {record['entity_record_id']} {source_id}",
                        errors,
                    )
            if record["source_software"] == "Aura":
                require(
                    record["provenance_class"] == "ANISOPRINT_OFFICIAL",
                    f"Aura mislabeled: {record['entity_record_id']}",
                    errors,
                )
            require(
                not Path(record["source_input_path"]).is_absolute(),
                f"absolute source path leaked: {record['entity_record_id']}",
                errors,
            )
            if record["normalized_entity_uuid"]:
                require(
                    normalize_uuid(record["original_entity_uuid"])
                    == record["normalized_entity_uuid"],
                    f"UUID normalization mismatch: {record['entity_record_id']}",
                    errors,
                )
                require(
                    record["canonical_entity_id"]
                    == f"uuid:{record['normalized_entity_uuid']}",
                    f"canonical UUID mismatch: {record['entity_record_id']}",
                    errors,
                )
            for field_name, field in record["fields"].items():
                require(field_name == field["field_name"], f"field key mismatch: {field_name}", errors)
                require(
                    field["evidence_classification"] in EVIDENCE_CLASSES,
                    f"invalid evidence class: {record['entity_record_id']} {field_name}",
                    errors,
                )
                require(
                    field["effective_value_status"] in EFFECTIVE_STATUSES,
                    f"invalid effective status: {record['entity_record_id']} {field_name}",
                    errors,
                )
                require(
                    field["original_field_name"] not in FORBIDDEN_FIELDS,
                    f"forbidden personal/application field: {field['original_field_name']}",
                    errors,
                )
                if field["effective_value_status"] == "unknown":
                    require(
                        field["effective_value"] is None,
                        f"unknown effective value populated: {record['entity_record_id']} {field_name}",
                        errors,
                    )
                if field["unit_status"] == "inferred":
                    require(
                        field["unit_evidence_classification"] == "INFERENCE",
                        f"inferred unit labeled non-inference: {record['entity_record_id']} {field_name}",
                        errors,
                    )
                for source_id in (
                    field["unit_source_ids"]
                    + field["alias_source_ids"]
                    + field["runtime_precedence_source_ids"]
                ):
                    require(source_id in manifest, f"unknown field evidence: {source_id}", errors)

    canonical_types: dict[str, set[str]] = defaultdict(set)
    source_duplicates: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    entity_record_ids = set()
    for record in entity_records:
        require(
            record["entity_record_id"] not in entity_record_ids,
            f"duplicate entity record ID: {record['entity_record_id']}",
            errors,
        )
        entity_record_ids.add(record["entity_record_id"])
        canonical_types[record["canonical_entity_id"]].add(record["entity_type"])
        source_duplicates[
            (record["source_version_id"], record["entity_type"], record["canonical_entity_id"])
        ].append(record)
    for canonical_id, types in canonical_types.items():
        require(len(types) == 1, f"canonical identity crosses entity types: {canonical_id}", errors)
    for key, records in source_duplicates.items():
        expected_duplicate = len(records) > 1
        require(
            all(record["duplicate_in_source"] == expected_duplicate for record in records),
            f"duplicate marker mismatch: {key}",
            errors,
        )

    for registry_name, items in (("unit", units), ("enum", enums), ("alias", aliases)):
        for item in items:
            require(
                item["classification"] in EVIDENCE_CLASSES,
                f"invalid {registry_name} classification: {item}",
                errors,
            )
            require(item["source_ids"], f"missing {registry_name} evidence: {item}", errors)
            for source_id in item["source_ids"]:
                require(source_id in manifest, f"unknown {registry_name} source: {source_id}", errors)
    for item in units:
        if item["status"] == "inferred":
            require(
                item["classification"] == "INFERENCE",
                f"inferred unit labeled FACT: {item['software']} {item['field_name']}",
                errors,
            )
        if item["status"] == "unknown":
            require(item["unit"] is None, f"unknown unit populated: {item}", errors)

    link_ids = set()
    for path in [
        generated_root / "identity/identity_links.jsonl",
        generated_root / "identity/foreign_key_relationships.jsonl",
    ]:
        for record in load_jsonl(path):
            identifier = record.get("link_id") or record.get("relationship_id")
            require(identifier not in link_ids, f"duplicate graph record: {identifier}", errors)
            link_ids.add(identifier)
            for source_id in record["source_ids"]:
                require(source_id in manifest, f"unknown graph source: {source_id}", errors)

    delta_ids = set()
    for path in sorted((generated_root / "deltas").glob("*.jsonl")):
        for record in load_jsonl(path):
            require(record["delta_id"] not in delta_ids, f"duplicate delta: {record['delta_id']}", errors)
            delta_ids.add(record["delta_id"])
            require(
                set(record["classifications"]) <= DELTA_CLASSES,
                f"invalid delta classification: {record['delta_id']}",
                errors,
            )
            require(
                record["evidence_classification"] in EVIDENCE_CLASSES,
                f"invalid delta evidence: {record['delta_id']}",
                errors,
            )
            for source_id in record["source_ids"]:
                require(source_id in manifest, f"unknown delta source: {source_id}", errors)

    for relative_path, expected_hash in summary["file_sha256"].items():
        path = generated_root / relative_path
        require(path.exists(), f"missing hashed generated file: {relative_path}", errors)
        if path.exists():
            require(
                sha256_file(path) == expected_hash,
                f"generated file hash mismatch: {relative_path}",
                errors,
            )
    require(summary["total_entities"] == len(entity_records), "entity summary mismatch", errors)
    require(
        summary["total_fields"] == sum(len(record["fields"]) for record in entity_records),
        "field summary mismatch",
        errors,
    )

    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"Validated {len(entity_records)} entities, {summary['total_fields']} fields, "
        f"{summary['identity_link_count']} identity links, and {len(delta_ids)} deltas."
    )


if __name__ == "__main__":
    main()
