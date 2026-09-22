#!/usr/bin/env python3
"""Deterministic normalization and delta functions for FibreSeeker-KB."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote


SCHEMA_VERSION = "1.0.0"
EVIDENCE_CLASSES = {"FACT", "INFERENCE", "OPEN_QUESTION"}
EFFECTIVE_STATUSES = {"known", "inferred", "unknown"}
DELTA_CLASSES = {
    "unchanged",
    "value_changed",
    "renamed",
    "structurally_changed",
    "added",
    "removed",
    "source_branch_changed",
    "unknown_correspondence",
}
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?"
    r"[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$"
)
ROCKET_EXCLUDED_FIELDS = {
    "CompanyId",
    "UserId",
    "ProjectId",
    "SourceProjectId",
    "Slots",
    "ExtruderPs",
    "ExtruderCs",
    "SettingSets",
    "SlotExtruderMaterialEntitys",
    "ProfileMaterials",
    "Profiles",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256(canonical_json(list(parts)).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_uuid(value: Any) -> str | None:
    if not isinstance(value, str) or not UUID_PATTERN.fullmatch(value):
        return None
    compact = value.replace("-", "").lower()
    return "-".join(
        [compact[:8], compact[8:12], compact[12:16], compact[16:20], compact[20:]]
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [canonical_json(record) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    records = load_jsonl(path)
    return {record["record_id"]: record for record in records}


def alias_index(registry: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    result = {}
    for alias in registry["aliases"]:
        result[(alias["software"], alias["entity_type"], alias["original"])] = alias
    return result


def unit_index(registry: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(item["software"], item["field_name"]): item for item in registry["units"]}


def canonical_field_name(
    software: str,
    entity_type: str,
    original_name: str,
    value: Any,
    aliases: dict[tuple[str, str, str], dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    alias = aliases.get((software, entity_type, original_name)) or aliases.get(
        (software, "*", original_name)
    )
    if alias:
        return alias["canonical"], alias
    if original_name not in {"Id", "GUID"} and normalize_uuid(value):
        if original_name.endswith("GUID") or original_name.endswith("Guid"):
            return original_name[:-4] + "UUID", None
        if original_name.endswith("Id"):
            return original_name[:-2] + "UUID", None
    return original_name, None


def field_category(field_name: str) -> str:
    if field_name.startswith(("Fiber", "InfillF", "InsetXF", "GenerateFiber")):
        return "reinforcement"
    if field_name.startswith(("Temperature", "BedTemperature", "ChamberTemperature")):
        return "temperature"
    if field_name.endswith("UUID") or field_name.endswith("Key"):
        return "identity_or_relation"
    return "general"


def normalized_scalar(field_name: str, value: Any) -> Any:
    if field_name.endswith("UUID"):
        return normalize_uuid(value) or value
    return value


def build_field(
    source: dict[str, Any],
    entity_type: str,
    original_name: str,
    base_value: Any,
    override_name: str | None,
    override_value: Any,
    aliases: dict[tuple[str, str, str], dict[str, Any]],
    units: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    field_name, alias = canonical_field_name(
        source["software"], entity_type, original_name, base_value, aliases
    )
    override_capable = override_name is not None
    override_present = override_capable and override_value is not None
    effective_value = None
    effective_status = "unknown"
    effective_classification = "OPEN_QUESTION"
    precedence_documented = False
    precedence_source_ids: list[str] = []

    if not override_capable:
        effective_value = normalized_scalar(field_name, base_value)
        effective_status = "known"
        effective_classification = "FACT"
    elif source["software"] == "Aura":
        effective_value = normalized_scalar(
            field_name, override_value if override_present else base_value
        )
        effective_status = "inferred"
        effective_classification = "INFERENCE"
        precedence_documented = True
        precedence_source_ids = ["AP-106"]

    unit = units.get((source["software"], field_name))
    normalized_unit = unit["unit"] if unit else None
    unit_status = unit["status"] if unit else "unknown"
    unit_classification = unit["classification"] if unit else "OPEN_QUESTION"
    unit_source_ids = unit["source_ids"] if unit else []

    notes = []
    if alias and alias.get("notes"):
        notes.append(alias["notes"])
    if unit and unit.get("notes"):
        notes.append(unit["notes"])
    if override_capable and source["software"] == "Rocket":
        notes.append("Rocket base/override runtime precedence is not established.")

    return {
        "field_name": field_name,
        "original_field_name": original_name,
        "original_override_field_name": override_name,
        "category": field_category(field_name),
        "raw_value": {"base": base_value, "override": override_value},
        "normalized_value": normalized_scalar(field_name, base_value),
        "raw_unit": None,
        "normalized_unit": normalized_unit,
        "unit_status": unit_status,
        "unit_evidence_classification": unit_classification,
        "unit_source_ids": unit_source_ids,
        "base_value": base_value,
        "override_value": override_value,
        "override_capable": override_capable,
        "override_present": override_present,
        "runtime_precedence_documented": precedence_documented,
        "runtime_precedence_source_ids": precedence_source_ids,
        "effective_value": effective_value,
        "effective_value_status": effective_status,
        "effective_value_evidence_classification": effective_classification,
        "evidence_classification": "FACT",
        "lineage_relationship": "source_observation",
        "alias_evidence_classification": alias["classification"] if alias else None,
        "alias_source_ids": alias["source_ids"] if alias else [],
        "notes": notes,
    }


def source_metadata(
    definition: dict[str, Any], manifest: dict[str, dict[str, Any]], input_sha256: str
) -> dict[str, Any]:
    manifest_records = [manifest[source_id] for source_id in definition["source_ids"]]
    provenances = sorted({record["provenance_class"] for record in manifest_records})
    if len(provenances) != 1:
        raise ValueError(f"mixed provenance for {definition['source_version_id']}")
    return {
        **definition,
        "provenance_class": provenances[0],
        "acquired_utc": [record["retrieved_utc"] for record in manifest_records],
        "input_sha256": input_sha256,
    }


def source_rows(
    source: dict[str, Any],
    archive_root: Path,
    config: dict[str, Any],
) -> tuple[list[tuple[str, str, int, dict[str, Any]]], str]:
    input_path = archive_root / source["input_path"]
    rows: list[tuple[str, str, int, dict[str, Any]]] = []
    if source["input_format"] == "sqlite":
        uri = f"file:{quote(str(input_path.resolve()))}?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        for table_name, entity_type in sorted(config["sqlite_entities"].items()):
            quoted_name = '"' + table_name.replace('"', '""') + '"'
            table_rows = [dict(row) for row in connection.execute(f"SELECT * FROM {quoted_name}")]
            table_rows.sort(key=lambda row: canonical_json(row))
            for row_index, row in enumerate(table_rows):
                rows.append((table_name, entity_type, row_index, row))
        connection.close()
        return rows, sha256_file(input_path)

    file_hashes = []
    for filename, entity_type in sorted(config["json_entities"].items()):
        path = input_path / filename
        file_hashes.append((filename, sha256_file(path)))
        values = load_json(path)
        if not isinstance(values, list):
            raise ValueError(f"expected array in {path}")
        indexed_values = list(enumerate(values))
        indexed_values.sort(key=lambda item: canonical_json(item[1]))
        for native_index, row in indexed_values:
            rows.append((filename, entity_type, native_index, row))
    return rows, hashlib.sha256(canonical_json(file_hashes).encode("utf-8")).hexdigest()


def normalize_source(
    definition: dict[str, Any],
    archive_root: Path,
    config: dict[str, Any],
    manifest: dict[str, dict[str, Any]],
    aliases: dict[tuple[str, str, str], dict[str, Any]],
    units: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_rows, input_sha256 = source_rows(definition, archive_root, config)
    source = source_metadata(definition, manifest, input_sha256)
    records = []
    for source_entity_type, entity_type, row_index, row in raw_rows:
        original_uuid = row.get("GUID") if source["software"] == "Aura" else row.get("Id")
        normalized_entity_uuid = normalize_uuid(original_uuid)
        application_key = row.get("Key") if source["software"] == "Rocket" else None
        canonical_entity_id = (
            f"uuid:{normalized_entity_uuid}"
            if normalized_entity_uuid
            else stable_id(
                "source-entity",
                source["source_version_id"],
                entity_type,
                source_entity_type,
                application_key,
                row_index,
            )
        )
        override_names = {
            name for name in row if name.endswith("Over") and name[:-4] in row
        }
        fields: dict[str, dict[str, Any]] = {}
        for original_name in sorted(row):
            if original_name in override_names:
                continue
            if source["software"] == "Rocket" and original_name in ROCKET_EXCLUDED_FIELDS:
                continue
            override_name = original_name + "Over" if original_name + "Over" in row else None
            field = build_field(
                source,
                entity_type,
                original_name,
                row[original_name],
                override_name,
                row.get(override_name) if override_name else None,
                aliases,
                units,
            )
            if field["field_name"] in fields:
                raise ValueError(
                    f"canonical field collision: {source['source_version_id']} "
                    f"{entity_type} {field['field_name']}"
                )
            fields[field["field_name"]] = field
        record_id = stable_id(
            "entity",
            source["source_version_id"],
            entity_type,
            source_entity_type,
            normalized_entity_uuid,
            application_key,
            row_index,
        )
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "entity_record_id": record_id,
                "source_version_id": source["source_version_id"],
                "source_software": source["software"],
                "source_version": source["version"],
                "source_branch": source["branch"],
                "source_ids": source["source_ids"],
                "provenance_class": source["provenance_class"],
                "acquired_utc": source["acquired_utc"],
                "source_input_path": source["input_path"],
                "source_input_sha256": source["input_sha256"],
                "source_format": source["input_format"],
                "source_entity_type": source_entity_type,
                "source_row_index": row_index,
                "entity_type": entity_type,
                "canonical_entity_id": canonical_entity_id,
                "original_entity_uuid": original_uuid,
                "normalized_entity_uuid": normalized_entity_uuid,
                "application_key": application_key,
                "vendor_name": row.get("Name"),
                "duplicate_in_source": False,
                "evidence_classification": "FACT",
                "fields": dict(sorted(fields.items())),
                "notes": [],
            }
        )

    duplicate_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        duplicate_groups[(record["entity_type"], record["canonical_entity_id"])].append(record)
    for group in duplicate_groups.values():
        if len(group) > 1:
            for record in group:
                record["duplicate_in_source"] = True
                record["notes"].append(
                    "Source contains multiple occurrences of this canonical identity."
                )
    records.sort(
        key=lambda record: (
            record["entity_type"],
            record["canonical_entity_id"],
            record["application_key"] if record["application_key"] is not None else -1,
            record["source_row_index"],
        )
    )
    return source, records


def entity_index(
    version_records: dict[str, list[dict[str, Any]]]
) -> dict[str, dict[tuple[str, str], list[dict[str, Any]]]]:
    result: dict[str, dict[tuple[str, str], list[dict[str, Any]]]] = {}
    for version, records in version_records.items():
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[(record["entity_type"], record["canonical_entity_id"])].append(record)
        result[version] = grouped
    return result


def generate_identity_links(
    version_records: dict[str, list[dict[str, Any]]], comparison_pairs: list[list[str]]
) -> list[dict[str, Any]]:
    indexes = entity_index(version_records)
    links = []
    for from_version, to_version in comparison_pairs:
        shared = sorted(set(indexes[from_version]) & set(indexes[to_version]))
        for entity_type, canonical_entity_id in shared:
            if not canonical_entity_id.startswith("uuid:"):
                continue
            from_records = indexes[from_version][(entity_type, canonical_entity_id)]
            to_records = indexes[to_version][(entity_type, canonical_entity_id)]
            source_ids = sorted(
                {source_id for record in from_records + to_records for source_id in record["source_ids"]}
            )
            links.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "link_id": stable_id(
                        "identity-link", from_version, to_version, entity_type, canonical_entity_id
                    ),
                    "from_source_version": from_version,
                    "to_source_version": to_version,
                    "entity_type": entity_type,
                    "canonical_entity_id": canonical_entity_id,
                    "from_entity_record_ids": [r["entity_record_id"] for r in from_records],
                    "to_entity_record_ids": [r["entity_record_id"] for r in to_records],
                    "relationship": "exact_uuid",
                    "evidence_classification": "FACT",
                    "source_ids": source_ids,
                    "notes": "Identity link is based only on exact normalized UUID continuity.",
                }
            )
    return sorted(links, key=lambda link: link["link_id"])


def generate_foreign_key_relationships(
    version_records: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    relationships = []
    for version, records in sorted(version_records.items()):
        targets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            if record["normalized_entity_uuid"]:
                targets[record["normalized_entity_uuid"]].append(record)
        for record in records:
            for field_name, field in record["fields"].items():
                if field_name == "EntityUUID" or not field_name.endswith("UUID"):
                    continue
                target_uuid = normalize_uuid(field["base_value"])
                if not target_uuid or target_uuid not in targets:
                    continue
                target_records = targets[target_uuid]
                relationships.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "relationship_id": stable_id(
                            "foreign-key",
                            version,
                            record["entity_record_id"],
                            field_name,
                            target_uuid,
                        ),
                        "source_version_id": version,
                        "from_entity_record_id": record["entity_record_id"],
                        "to_entity_record_ids": [r["entity_record_id"] for r in target_records],
                        "field_name": field_name,
                        "relationship": "explicit_foreign_key",
                        "evidence_classification": "FACT",
                        "source_ids": record["source_ids"],
                    }
                )
    return sorted(relationships, key=lambda item: item["relationship_id"])


def field_snapshots(records: list[dict[str, Any]], field_name: str) -> list[dict[str, Any]]:
    snapshots = []
    for record in records:
        field = record["fields"].get(field_name)
        if field:
            snapshots.append(
                {
                    "entity_record_id": record["entity_record_id"],
                    "application_key": record["application_key"],
                    "original_field_name": field["original_field_name"],
                    "original_override_field_name": field["original_override_field_name"],
                    "base_value": field["base_value"],
                    "override_value": field["override_value"],
                    "override_capable": field["override_capable"],
                    "effective_value": field["effective_value"],
                    "effective_value_status": field["effective_value_status"],
                    "normalized_unit": field["normalized_unit"],
                    "unit_status": field["unit_status"],
                }
            )
    return sorted(snapshots, key=canonical_json)


def compare_entity_groups(
    comparison_id: str,
    from_version: str,
    to_version: str,
    entity_type: str,
    canonical_entity_id: str,
    from_records: list[dict[str, Any]],
    to_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_ids = sorted(
        {source_id for record in from_records + to_records for source_id in record["source_ids"]}
    )
    deltas = []
    if not from_records or not to_records:
        classification = "added" if to_records else "removed"
        deltas.append(
            {
                "schema_version": SCHEMA_VERSION,
                "delta_id": stable_id(
                    "delta", comparison_id, entity_type, canonical_entity_id, None, classification
                ),
                "comparison_id": comparison_id,
                "from_source_version": from_version,
                "to_source_version": to_version,
                "entity_type": entity_type,
                "canonical_entity_id": canonical_entity_id,
                "field_name": None,
                "from": [record["entity_record_id"] for record in from_records],
                "to": [record["entity_record_id"] for record in to_records],
                "classifications": [classification],
                "evidence_classification": "FACT",
                "source_ids": source_ids,
                "notes": "Presence or absence is relative to the two preserved source stores.",
            }
        )
        return deltas

    if (
        {record["source_format"] for record in from_records}
        != {record["source_format"] for record in to_records}
        or {record["source_entity_type"] for record in from_records}
        != {record["source_entity_type"] for record in to_records}
        or len(from_records) != len(to_records)
    ):
        deltas.append(
            {
                "schema_version": SCHEMA_VERSION,
                "delta_id": stable_id(
                    "delta", comparison_id, entity_type, canonical_entity_id, "__entity_structure__"
                ),
                "comparison_id": comparison_id,
                "from_source_version": from_version,
                "to_source_version": to_version,
                "entity_type": entity_type,
                "canonical_entity_id": canonical_entity_id,
                "field_name": "__entity_structure__",
                "from": {
                    "formats": sorted({record["source_format"] for record in from_records}),
                    "source_entity_types": sorted(
                        {record["source_entity_type"] for record in from_records}
                    ),
                    "occurrences": len(from_records),
                },
                "to": {
                    "formats": sorted({record["source_format"] for record in to_records}),
                    "source_entity_types": sorted(
                        {record["source_entity_type"] for record in to_records}
                    ),
                    "occurrences": len(to_records),
                },
                "classifications": ["structurally_changed"],
                "evidence_classification": "FACT",
                "source_ids": source_ids,
                "notes": "Source representation, entity-store name, or occurrence count changed.",
            }
        )

    field_names = sorted(
        {name for record in from_records + to_records for name in record["fields"]}
    )
    for field_name in field_names:
        from_snapshot = field_snapshots(from_records, field_name)
        to_snapshot = field_snapshots(to_records, field_name)
        classifications = []
        if not from_snapshot:
            classifications.append("added")
        elif not to_snapshot:
            classifications.append("removed")
        else:
            from_originals = {
                (item["original_field_name"], item["original_override_field_name"])
                for item in from_snapshot
            }
            to_originals = {
                (item["original_field_name"], item["original_override_field_name"])
                for item in to_snapshot
            }
            from_values = [
                (item["base_value"], item["override_value"], item["normalized_unit"])
                for item in from_snapshot
            ]
            to_values = [
                (item["base_value"], item["override_value"], item["normalized_unit"])
                for item in to_snapshot
            ]
            if from_originals != to_originals:
                classifications.append("renamed")
            if canonical_json(from_values) != canonical_json(to_values):
                classifications.append("value_changed")
            from_override = {item["override_capable"] for item in from_snapshot}
            to_override = {item["override_capable"] for item in to_snapshot}
            moved_to_override = any(
                left["base_value"] == right["override_value"]
                and left["base_value"] != right["base_value"]
                for left in from_snapshot
                for right in to_snapshot
            )
            if from_override != to_override or moved_to_override:
                classifications.append("structurally_changed")
            if not classifications:
                classifications.append("unchanged")
        evidence = "INFERENCE" if "renamed" in classifications else "FACT"
        deltas.append(
            {
                "schema_version": SCHEMA_VERSION,
                "delta_id": stable_id(
                    "delta", comparison_id, entity_type, canonical_entity_id, field_name
                ),
                "comparison_id": comparison_id,
                "from_source_version": from_version,
                "to_source_version": to_version,
                "entity_type": entity_type,
                "canonical_entity_id": canonical_entity_id,
                "field_name": field_name,
                "from": from_snapshot,
                "to": to_snapshot,
                "classifications": classifications,
                "evidence_classification": evidence,
                "source_ids": source_ids,
                "notes": "Effective values are not used for comparison when precedence is unknown.",
            }
        )
    return deltas


def generate_pair_deltas(
    version_records: dict[str, list[dict[str, Any]]], from_version: str, to_version: str
) -> list[dict[str, Any]]:
    indexes = entity_index(version_records)
    comparison_id = f"{from_version}__{to_version}"
    keys = sorted(set(indexes[from_version]) | set(indexes[to_version]))
    deltas = []
    for entity_type, canonical_entity_id in keys:
        deltas.extend(
            compare_entity_groups(
                comparison_id,
                from_version,
                to_version,
                entity_type,
                canonical_entity_id,
                indexes[from_version].get((entity_type, canonical_entity_id), []),
                indexes[to_version].get((entity_type, canonical_entity_id), []),
            )
        )

    removed = [
        records[0]
        for key, records in indexes[from_version].items()
        if key not in indexes[to_version] and records[0].get("vendor_name")
    ]
    added = [
        records[0]
        for key, records in indexes[to_version].items()
        if key not in indexes[from_version] and records[0].get("vendor_name")
    ]
    for left in removed:
        for right in added:
            if (
                left["entity_type"] == right["entity_type"]
                and left["vendor_name"].casefold() == right["vendor_name"].casefold()
            ):
                deltas.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "delta_id": stable_id(
                            "delta-unknown",
                            comparison_id,
                            left["canonical_entity_id"],
                            right["canonical_entity_id"],
                        ),
                        "comparison_id": comparison_id,
                        "from_source_version": from_version,
                        "to_source_version": to_version,
                        "entity_type": left["entity_type"],
                        "canonical_entity_id": None,
                        "field_name": None,
                        "from": [left["entity_record_id"]],
                        "to": [right["entity_record_id"]],
                        "classifications": ["unknown_correspondence"],
                        "evidence_classification": "OPEN_QUESTION",
                        "source_ids": sorted(set(left["source_ids"] + right["source_ids"])),
                        "notes": "Names match, but UUIDs differ; no identity link is asserted.",
                    }
                )
    return sorted(deltas, key=lambda item: item["delta_id"])


def generate_branch_deltas(
    version_records: dict[str, list[dict[str, Any]]], branch_config: dict[str, Any]
) -> list[dict[str, Any]]:
    indexes = entity_index(version_records)
    branches = branch_config["source_versions"]
    target = branch_config["target_version"]
    comparison_id = branch_config["comparison_id"]
    deltas = []
    for key in sorted(indexes[target]):
        target_records = indexes[target][key]
        matching_branches = [branch for branch in branches if key in indexes[branch]]
        if len(matching_branches) == 1:
            branch = matching_branches[0]
            entity_type, canonical_entity_id = key
            source_records = indexes[branch][key]
            source_ids = sorted(
                {sid for record in source_records + target_records for sid in record["source_ids"]}
            )
            deltas.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "delta_id": stable_id(
                        "branch-delta", comparison_id, entity_type, canonical_entity_id
                    ),
                    "comparison_id": comparison_id,
                    "from_source_version": branch,
                    "to_source_version": target,
                    "entity_type": entity_type,
                    "canonical_entity_id": canonical_entity_id,
                    "field_name": None,
                    "from": [record["entity_record_id"] for record in source_records],
                    "to": [record["entity_record_id"] for record in target_records],
                    "classifications": ["source_branch_changed"],
                    "evidence_classification": "FACT",
                    "source_ids": source_ids,
                    "notes": f"Exact UUID occurs in {branch} and Rocket, but not the other Seeker Aura branch.",
                }
            )
        elif not matching_branches:
            entity_type, canonical_entity_id = key
            deltas.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "delta_id": stable_id(
                        "branch-added", comparison_id, entity_type, canonical_entity_id
                    ),
                    "comparison_id": comparison_id,
                    "from_source_version": "+".join(branches),
                    "to_source_version": target,
                    "entity_type": entity_type,
                    "canonical_entity_id": canonical_entity_id,
                    "field_name": None,
                    "from": [],
                    "to": [record["entity_record_id"] for record in target_records],
                    "classifications": ["added"],
                    "evidence_classification": "FACT",
                    "source_ids": sorted({sid for record in target_records for sid in record["source_ids"]}),
                    "notes": "No exact UUID ancestor occurs in either preserved Seeker Aura branch.",
                }
            )
    return sorted(deltas, key=lambda item: item["delta_id"])


def output_file_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "summary.json"
    }
