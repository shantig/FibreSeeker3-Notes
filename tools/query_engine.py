#!/usr/bin/env python3
"""Deterministic, evidence-safe query/index layer for canonical Phase 2A JSONL."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable


CONTRACT_VERSION = "1.0.0"
INDEX_SCHEMA_VERSION = "1.0.0"
VIEW_MODES = (
    "FIBRESEEK_CONFIRMED",
    "LINEAGE_AWARE",
    "HISTORICAL",
    "ALL_EVIDENCE",
)
FIBRESEEK = "FIBRESEEK_OFFICIAL"
ANISOPRINT = "ANISOPRINT_OFFICIAL"

MACHINE_ENTITY_TYPES = {
    "printer",
    "extruder_plastic",
    "extruder_composite",
    "slot",
    "slot_extruder_material_association",
}
MATERIAL_ENTITY_TYPES = {
    "plastic",
    "composite",
    "profile_material_association",
    "slot_extruder_material_association",
}
PROFILE_ENTITY_TYPES = {"profile", "profile_group", "profile_material_association"}

MACHINE_FIELD_RE = re.compile(
    r"^(AreaSize|Extruder|Nozzle|Temperature|BedTemperature|ChamberTemperature|"
    r"Travel|Acceleration|MaxAcceleration|Cut|FiberRestart|Slot|Postprocessor)",
    re.I,
)
MATERIAL_FIELD_RE = re.compile(
    r"(Temperature|Material|Plastic|Composite|Fiber|LinearDensity|Spool|Polymer|"
    r"Extrusion|Density|Diameter)",
    re.I,
)
PROFILE_FIELD_RE = re.compile(
    r"(Profile|Layer|Path|Infill|Fiber|Reinforcement|Angle|Speed|Feedrate|Tension|"
    r"Macro|Perimeter|Wall|Shell|Pattern|Inset)",
    re.I,
)
PROFILE_FIELD_BUCKETS = [
    re.compile(r"(Name|Profile|Group|Material|UUID|Key)$", re.I),
    re.compile(r"Macro", re.I),
    re.compile(r"Layer", re.I),
    re.compile(r"(Path|Infill|Pattern|Perimeter|Wall|Shell)", re.I),
    re.compile(r"(Fiber|Reinforcement|Inset)", re.I),
    re.compile(r"Angle", re.I),
    re.compile(r"(Speed|Feedrate)", re.I),
    re.compile(r"Tension", re.I),
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json(list(parts)).encode('utf-8'))}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def iter_jsonl(path: Path) -> Iterable[tuple[int, str, dict[str, Any]]]:
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            raw = line.rstrip("\n")
            if raw:
                yield line_number, raw, json.loads(raw)


def normalized_identity(value: str) -> str:
    value = value.strip()
    if value.startswith(("uuid:", "entity:", "source-entity:")):
        return value.lower()
    compact = value.replace("-", "")
    if re.fullmatch(r"[0-9a-fA-F]{32}", compact):
        value = "-".join(
            [compact[:8], compact[8:12], compact[12:16], compact[16:20], compact[20:]]
        )
        return f"uuid:{value.lower()}"
    return value


def input_paths(repo_root: Path) -> list[Path]:
    normalized = repo_root / "data/profiles"
    paths = list((normalized / "generated").rglob("*.json"))
    paths += list((normalized / "generated").rglob("*.jsonl"))
    paths += list((normalized / "registries").glob("*.json"))
    paths += [
        normalized / "config/source_versions.json",
        normalized / "query/question_registry.json",
        repo_root / "sources/manifest.jsonl",
    ]
    return sorted({path.resolve() for path in paths})


def input_digest(repo_root: Path) -> tuple[str, list[dict[str, str]]]:
    inventory = [
        {
            "path": str(path.relative_to(repo_root.resolve())),
            "sha256": sha256_file(path),
        }
        for path in input_paths(repo_root.resolve())
    ]
    return sha256_bytes(canonical_json(inventory).encode("utf-8")), inventory


SCHEMA_SQL = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE source_versions (
  source_version_id TEXT PRIMARY KEY, software TEXT NOT NULL, version TEXT NOT NULL,
  branch TEXT NOT NULL, provenance_class TEXT NOT NULL, source_ids_json TEXT NOT NULL,
  acquired_utc_json TEXT NOT NULL, input_path TEXT NOT NULL, input_sha256 TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE sources (
  source_id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT NOT NULL,
  provenance_class TEXT NOT NULL, record_kind TEXT NOT NULL, source_url TEXT NOT NULL,
  final_url TEXT, retrieved_utc TEXT, sha256 TEXT, mime_type TEXT, byte_size INTEGER,
  software_version TEXT, acquisition_status TEXT NOT NULL, notes TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE entities (
  entity_record_id TEXT PRIMARY KEY, canonical_entity_id TEXT NOT NULL,
  original_entity_uuid TEXT, normalized_entity_uuid TEXT, application_key INTEGER,
  vendor_name TEXT, entity_type TEXT NOT NULL, source_entity_type TEXT NOT NULL,
  source_row_index INTEGER NOT NULL, source_version_id TEXT NOT NULL,
  source_software TEXT NOT NULL, source_version TEXT NOT NULL, source_branch TEXT NOT NULL,
  provenance_class TEXT NOT NULL, evidence_classification TEXT NOT NULL,
  source_ids_json TEXT NOT NULL, canonical_path TEXT NOT NULL,
  record_sha256 TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX entity_canonical_idx ON entities(canonical_entity_id, source_version_id);
CREATE INDEX entity_type_idx ON entities(entity_type, source_version_id);
CREATE INDEX entity_name_idx ON entities(vendor_name COLLATE NOCASE);
CREATE TABLE fields (
  entity_record_id TEXT NOT NULL, field_name TEXT NOT NULL,
  source_version_id TEXT NOT NULL, source_software TEXT NOT NULL,
  provenance_class TEXT NOT NULL, evidence_classification TEXT NOT NULL,
  source_ids_json TEXT NOT NULL, field_json TEXT NOT NULL,
  PRIMARY KEY(entity_record_id, field_name),
  FOREIGN KEY(entity_record_id) REFERENCES entities(entity_record_id)
) WITHOUT ROWID;
CREATE INDEX field_name_idx ON fields(field_name, source_version_id);
CREATE TABLE identity_links (
  link_id TEXT PRIMARY KEY, canonical_entity_id TEXT NOT NULL, entity_type TEXT NOT NULL,
  from_source_version TEXT NOT NULL, to_source_version TEXT NOT NULL,
  evidence_classification TEXT NOT NULL, source_ids_json TEXT NOT NULL,
  canonical_path TEXT NOT NULL, record_sha256 TEXT NOT NULL, record_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX identity_canonical_idx ON identity_links(canonical_entity_id);
CREATE TABLE relationships (
  relationship_id TEXT PRIMARY KEY, source_version_id TEXT NOT NULL,
  from_entity_record_id TEXT NOT NULL, field_name TEXT NOT NULL,
  evidence_classification TEXT NOT NULL, source_ids_json TEXT NOT NULL,
  canonical_path TEXT NOT NULL, record_sha256 TEXT NOT NULL, record_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE relationship_targets (
  relationship_id TEXT NOT NULL, to_entity_record_id TEXT NOT NULL,
  PRIMARY KEY(relationship_id, to_entity_record_id)
) WITHOUT ROWID;
CREATE INDEX relationship_from_idx ON relationships(from_entity_record_id);
CREATE INDEX relationship_target_idx ON relationship_targets(to_entity_record_id);
CREATE TABLE deltas (
  delta_id TEXT PRIMARY KEY, comparison_id TEXT NOT NULL, from_source_version TEXT NOT NULL,
  to_source_version TEXT NOT NULL, entity_type TEXT NOT NULL, canonical_entity_id TEXT,
  field_name TEXT, classifications_json TEXT NOT NULL, evidence_classification TEXT NOT NULL,
  source_ids_json TEXT NOT NULL, canonical_path TEXT NOT NULL,
  record_sha256 TEXT NOT NULL, record_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX delta_comparison_idx ON deltas(from_source_version, to_source_version);
CREATE INDEX delta_entity_idx ON deltas(canonical_entity_id, field_name);
CREATE TABLE units (
  unit_id TEXT PRIMARY KEY, field_name TEXT NOT NULL, software TEXT NOT NULL, unit TEXT,
  status TEXT NOT NULL, classification TEXT NOT NULL, source_ids_json TEXT NOT NULL,
  manufacturer_guidance TEXT, item_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX unit_field_idx ON units(field_name, software);
CREATE TABLE enums (
  enum_id TEXT PRIMARY KEY, field_name TEXT NOT NULL, software TEXT NOT NULL,
  value_json TEXT NOT NULL, label TEXT, status TEXT NOT NULL, classification TEXT NOT NULL,
  source_ids_json TEXT NOT NULL, item_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX enum_field_idx ON enums(field_name, software);
CREATE TABLE questions (
  question_id TEXT PRIMARY KEY, title TEXT NOT NULL, domain TEXT NOT NULL,
  classification TEXT NOT NULL, resolution_requirement TEXT NOT NULL,
  fields_json TEXT NOT NULL, entity_types_json TEXT NOT NULL,
  canonical_entity_ids_json TEXT NOT NULL, source_ids_json TEXT NOT NULL, item_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX question_domain_idx ON questions(domain, resolution_requirement);
CREATE TABLE source_refs (
  source_id TEXT NOT NULL, record_kind TEXT NOT NULL, record_id TEXT NOT NULL,
  PRIMARY KEY(source_id, record_kind, record_id)
) WITHOUT ROWID;
CREATE INDEX source_ref_record_idx ON source_refs(record_kind, record_id);
"""


def _source_refs(
    connection: sqlite3.Connection, source_ids: Iterable[str], kind: str, record_id: str
) -> None:
    connection.executemany(
        "INSERT OR IGNORE INTO source_refs VALUES (?,?,?)",
        [(source_id, kind, record_id) for source_id in sorted(set(source_ids))],
    )


def build_index(repo_root: Path, db_path: Path) -> dict[str, Any]:
    """Rebuild the disposable SQLite adapter solely from canonical/local registries."""
    repo_root = repo_root.resolve()
    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    digest, inventory = input_digest(repo_root)
    normalized = repo_root / "data/profiles"
    generated = normalized / "generated"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA page_size=32768")
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(SCHEMA_SQL)

    meta = {
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "input_digest": digest,
        "input_inventory": canonical_json(inventory),
    }
    connection.executemany("INSERT INTO metadata VALUES (?,?)", sorted(meta.items()))

    for source in sorted(load_json(generated / "sources.json"), key=lambda x: x["source_version_id"]):
        connection.execute(
            "INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)",
            (
                source["source_version_id"], source["software"], source["version"],
                source["branch"], source["provenance_class"], canonical_json(source["source_ids"]),
                canonical_json(source["acquired_utc"]), source["input_path"], source["input_sha256"],
            ),
        )

    entity_count = field_count = 0
    for path in sorted((generated / "versions").glob("*/entities.jsonl")):
        relative = str(path.relative_to(repo_root))
        for _, raw, record in iter_jsonl(path):
            record_sha = sha256_bytes(raw.encode("utf-8"))
            source_ids = record["source_ids"]
            connection.execute(
                "INSERT INTO entities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    record["entity_record_id"], record["canonical_entity_id"],
                    record["original_entity_uuid"], record["normalized_entity_uuid"],
                    record["application_key"], record["vendor_name"], record["entity_type"],
                    record["source_entity_type"], record["source_row_index"],
                    record["source_version_id"], record["source_software"], record["source_version"],
                    record["source_branch"], record["provenance_class"],
                    record["evidence_classification"], canonical_json(source_ids), relative,
                    record_sha,
                ),
            )
            _source_refs(connection, source_ids, "entity", record["entity_record_id"])
            entity_count += 1
            for field_name, field in sorted(record["fields"].items()):
                combined_sources = sorted(
                    set(source_ids)
                    | set(field["unit_source_ids"])
                    | set(field["alias_source_ids"])
                    | set(field["runtime_precedence_source_ids"])
                )
                connection.execute(
                    "INSERT INTO fields VALUES (?,?,?,?,?,?,?,?)",
                    (
                        record["entity_record_id"], field_name, record["source_version_id"],
                        record["source_software"], record["provenance_class"],
                        field["evidence_classification"], canonical_json(combined_sources),
                        canonical_json(field),
                    ),
                )
                field_count += 1

    link_count = 0
    link_path = generated / "identity/identity_links.jsonl"
    for _, raw, record in iter_jsonl(link_path):
        relative = str(link_path.relative_to(repo_root))
        connection.execute(
            "INSERT INTO identity_links VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                record["link_id"], record["canonical_entity_id"], record["entity_type"],
                record["from_source_version"], record["to_source_version"],
                record["evidence_classification"], canonical_json(record["source_ids"]), relative,
                sha256_bytes(raw.encode("utf-8")), raw,
            ),
        )
        _source_refs(connection, record["source_ids"], "identity_link", record["link_id"])
        link_count += 1

    relationship_count = 0
    relationship_path = generated / "identity/foreign_key_relationships.jsonl"
    for _, raw, record in iter_jsonl(relationship_path):
        relative = str(relationship_path.relative_to(repo_root))
        connection.execute(
            "INSERT INTO relationships VALUES (?,?,?,?,?,?,?,?,?)",
            (
                record["relationship_id"], record["source_version_id"],
                record["from_entity_record_id"], record["field_name"],
                record["evidence_classification"], canonical_json(record["source_ids"]), relative,
                sha256_bytes(raw.encode("utf-8")), raw,
            ),
        )
        connection.executemany(
            "INSERT INTO relationship_targets VALUES (?,?)",
            [(record["relationship_id"], target) for target in record["to_entity_record_ids"]],
        )
        _source_refs(
            connection, record["source_ids"], "relationship", record["relationship_id"]
        )
        relationship_count += 1

    delta_count = 0
    for path in sorted((generated / "deltas").glob("*.jsonl")):
        relative = str(path.relative_to(repo_root))
        for _, raw, record in iter_jsonl(path):
            connection.execute(
                "INSERT INTO deltas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    record["delta_id"], record["comparison_id"], record["from_source_version"],
                    record["to_source_version"], record["entity_type"],
                    record["canonical_entity_id"], record["field_name"],
                    canonical_json(record["classifications"]), record["evidence_classification"],
                    canonical_json(record["source_ids"]), relative,
                    sha256_bytes(raw.encode("utf-8")), raw,
                ),
            )
            _source_refs(connection, record["source_ids"], "delta", record["delta_id"])
            delta_count += 1

    for item in load_json(normalized / "registries/unit_registry.json")["units"]:
        identifier = stable_id("unit", item["field_name"], item["software"])
        connection.execute(
            "INSERT INTO units VALUES (?,?,?,?,?,?,?,?,?)",
            (
                identifier, item["field_name"], item["software"], item["unit"], item["status"],
                item["classification"], canonical_json(item["source_ids"]),
                item.get("manufacturer_guidance"), canonical_json(item),
            ),
        )
        _source_refs(connection, item["source_ids"], "unit", identifier)

    for item in load_json(normalized / "registries/enum_registry.json")["enums"]:
        identifier = stable_id(
            "enum", item["field_name"], item["software"], item["value"], item["label"]
        )
        connection.execute(
            "INSERT INTO enums VALUES (?,?,?,?,?,?,?,?,?)",
            (
                identifier, item["field_name"], item["software"], canonical_json(item["value"]),
                item["label"], item["status"], item["classification"],
                canonical_json(item["source_ids"]), canonical_json(item),
            ),
        )
        _source_refs(connection, item["source_ids"], "enum", identifier)

    questions = load_json(normalized / "query/question_registry.json")["questions"]
    for item in questions:
        connection.execute(
            "INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                item["question_id"], item["title"], item["domain"], item["classification"],
                item["resolution_requirement"], canonical_json(item.get("fields", [])),
                canonical_json(item.get("entity_types", [])),
                canonical_json(item.get("canonical_entity_ids", [])),
                canonical_json(item["source_ids"]), canonical_json(item),
            ),
        )
        _source_refs(connection, item["source_ids"], "question", item["question_id"])

    manifest = {record["record_id"]: record for _, _, record in iter_jsonl(repo_root / "sources/manifest.jsonl")}
    safe_fields = (
        "record_id", "title", "publisher", "provenance_class", "record_kind", "source_url",
        "final_url", "retrieved_utc", "sha256", "mime_type", "byte_size", "software_version",
        "acquisition_status", "notes",
    )
    for source_id in sorted(manifest):
        record = manifest[source_id]
        values = [record.get(field) for field in safe_fields]
        connection.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)

    counts = {
        "entity_count": entity_count,
        "field_count": field_count,
        "identity_link_count": link_count,
        "relationship_count": relationship_count,
        "delta_count": delta_count,
        "question_count": len(questions),
        "source_count": len(manifest),
    }
    connection.executemany(
        "INSERT INTO metadata VALUES (?,?)", [(key, str(value)) for key, value in sorted(counts.items())]
    )
    connection.commit()
    connection.execute("VACUUM")
    connection.close()
    return {
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "input_digest": digest,
        "database_sha256": sha256_file(db_path),
        "database_bytes": db_path.stat().st_size,
        **counts,
    }


def _loads(value: str) -> Any:
    return json.loads(value)


def evidence_scope(classification: str, provenance_class: str | None) -> str:
    if classification == "INFERENCE":
        return "LINEAGE_INFERENCE"
    if classification == "OPEN_QUESTION":
        return "UNRESOLVED"
    if classification == "EXPERIMENTAL" or provenance_class == "EXPERIMENTAL":
        return "EXPERIMENTAL"
    if provenance_class == FIBRESEEK:
        return "FIBRESEEK_FIRST_PARTY"
    return "HISTORICAL_ANISOPRINT"


def mode_allows_provenance(mode: str, provenance: str) -> bool:
    if mode == "FIBRESEEK_CONFIRMED":
        return provenance == FIBRESEEK
    if mode == "HISTORICAL":
        return provenance == ANISOPRINT
    return True


def mode_allows_assertion(
    mode: str, classification: str, software: str, source_ids: Iterable[str]
) -> bool:
    source_ids = list(source_ids)
    has_fs = any(item.startswith("FS-") for item in source_ids)
    has_ap = any(item.startswith("AP-") for item in source_ids)
    if mode == "FIBRESEEK_CONFIRMED":
        return classification != "INFERENCE" and ("Rocket" in software or has_fs)
    if mode == "HISTORICAL":
        return "Aura" in software or (has_ap and not has_fs)
    return True


def mode_filtered_source_ids(mode: str, source_ids: Iterable[str]) -> list[str]:
    """Keep source support consistent with the selected evidence projection."""
    values = sorted(set(source_ids))
    if mode == "FIBRESEEK_CONFIRMED":
        return [value for value in values if value.startswith("FS-")]
    if mode == "HISTORICAL":
        return [value for value in values if value.startswith("AP-")]
    return values


def canonical_ref(row: sqlite3.Row, record_id: str) -> dict[str, str]:
    return {
        "path": row["canonical_path"],
        "record_id": record_id,
        "record_sha256": row["record_sha256"],
    }


def result_item(
    kind: str,
    classification: str,
    provenance: str | None,
    source_ids: list[str],
    payload: dict[str, Any],
    reference: dict[str, str] | None = None,
    manufacturer_guidance: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "classification": classification,
        "evidence_scope": evidence_scope(classification, provenance),
        "provenance_class": provenance,
        "source_ids": sorted(set(source_ids)),
        "manufacturer_guidance": manufacturer_guidance,
        "canonical_ref": reference,
        "payload": payload,
    }


class QueryEngine:
    def __init__(self, repo_root: Path, db_path: Path):
        self.repo_root = repo_root.resolve()
        self.db_path = db_path.resolve()
        uri = f"file:{self.db_path}?mode=ro"
        self.connection = sqlite3.connect(uri, uri=True)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA query_only=ON")
        self.source_metadata = {
            row["source_version_id"]: {
                "acquired_utc": _loads(row["acquired_utc_json"]),
                "input_path": row["input_path"],
                "input_sha256": row["input_sha256"],
            }
            for row in self.connection.execute(
                "SELECT source_version_id,acquired_utc_json,input_path,input_sha256 "
                "FROM source_versions ORDER BY source_version_id"
            )
        }

    def close(self) -> None:
        self.connection.close()

    def metadata(self) -> dict[str, str]:
        return {row["key"]: row["value"] for row in self.connection.execute("SELECT * FROM metadata")}

    def response(
        self, operation: str, mode: str, results: list[dict[str, Any]], warnings: list[str] | None = None,
        **query: Any,
    ) -> dict[str, Any]:
        if mode not in VIEW_MODES:
            raise ValueError(f"unknown view mode: {mode}")
        metadata = self.metadata()
        return {
            "contract_version": CONTRACT_VERSION,
            "query": {"operation": operation, **query},
            "view_mode": mode,
            "result_count": len(results),
            "results": results,
            "warnings": warnings or [],
            "index": {
                "schema_version": metadata["index_schema_version"],
                "input_digest": metadata["input_digest"],
            },
        }

    def resolve_entities(
        self, identity: str | None = None, entity_type: str | None = None,
        version: str | None = None, name: str | None = None, limit: int = 200,
    ) -> list[sqlite3.Row]:
        clauses, params = [], []
        if identity:
            normalized = normalized_identity(identity)
            if normalized.startswith("entity:"):
                clauses.append("entity_record_id=?")
            elif normalized.startswith(("uuid:", "source-entity:")):
                clauses.append("canonical_entity_id=?")
            else:
                clauses.append("vendor_name=? COLLATE NOCASE")
            params.append(normalized if normalized.startswith(("entity:", "uuid:", "source-entity:")) else identity)
        if name:
            clauses.append("vendor_name LIKE ? COLLATE NOCASE")
            params.append(f"%{name}%")
        if entity_type:
            clauses.append("entity_type=?")
            params.append(entity_type)
        if version:
            clauses.append("source_version_id=?")
            params.append(version)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"SELECT * FROM entities{where} ORDER BY canonical_entity_id,source_version_id,entity_record_id LIMIT ?"
        return list(self.connection.execute(sql, [*params, limit]))

    def _field_payload(
        self, field: dict[str, Any], compact: bool, mode: str = "LINEAGE_AWARE"
    ) -> dict[str, Any]:
        payload = {
            "field": field["field_name"],
            "source_native_field": field["original_field_name"],
            "raw_value": field["raw_value"],
            "base_value": field["base_value"],
            "override_value": field["override_value"],
            "override_capable": field["override_capable"],
            "override_present": field["override_present"],
            "effective_value": field["effective_value"],
            "effective_value_status": field["effective_value_status"],
            "effective_value_classification": field["effective_value_evidence_classification"],
            "unit": field["normalized_unit"],
            "unit_status": field["unit_status"],
            "unit_classification": field["unit_evidence_classification"],
            "lineage_relationship": field["lineage_relationship"],
        }
        if not compact:
            payload.update(
                {
                    "normalized_value": field["normalized_value"],
                    "unit_source_ids": field["unit_source_ids"],
                    "runtime_precedence_documented": field["runtime_precedence_documented"],
                    "runtime_precedence_source_ids": field["runtime_precedence_source_ids"],
                    "alias_classification": field["alias_evidence_classification"],
                    "alias_source_ids": field["alias_source_ids"],
                    "notes": field["notes"],
                }
            )
        if mode == "FIBRESEEK_CONFIRMED" and field["unit_evidence_classification"] != "FACT":
            payload.pop("unit", None)
            payload.pop("unit_status", None)
            payload.pop("unit_classification", None)
            payload["filtered_assertions"] = [
                {
                    "attribute": "unit",
                    "classification": field["unit_evidence_classification"],
                    "reason": "FIBRESEEK_CONFIRMED excludes non-fact semantic assertions.",
                }
            ]
            if not compact:
                payload.pop("unit_source_ids", None)
        if mode == "FIBRESEEK_CONFIRMED" and not compact and field["alias_evidence_classification"] == "INFERENCE":
            payload.pop("alias_classification", None)
            payload.pop("alias_source_ids", None)
            payload.setdefault("filtered_assertions", []).append(
                {
                    "attribute": "field_alias",
                    "classification": "INFERENCE",
                    "reason": "FIBRESEEK_CONFIRMED excludes lineage aliases.",
                }
            )
        return payload

    def entity(
        self, identity: str, mode: str = "LINEAGE_AWARE", version: str | None = None,
        field_name: str | None = None, compact: bool = False,
    ) -> dict[str, Any]:
        results = []
        for row in self.resolve_entities(identity=identity, version=version):
            if not mode_allows_provenance(mode, row["provenance_class"]):
                continue
            fields = {
                item["field_name"]: _loads(item["field_json"])
                for item in self.connection.execute(
                    "SELECT field_name,field_json FROM fields WHERE entity_record_id=? ORDER BY field_name",
                    (row["entity_record_id"],),
                )
            }
            if field_name:
                fields = {field_name: fields[field_name]} if field_name in fields else {}
            payload = {
                "canonical_entity_id": row["canonical_entity_id"],
                "source_native_identity": {
                    "original_uuid": row["original_entity_uuid"],
                    "normalized_uuid": row["normalized_entity_uuid"],
                    "application_key": row["application_key"],
                    "entity_record_id": row["entity_record_id"],
                    "source_entity_type": row["source_entity_type"],
                    "source_row_index": row["source_row_index"],
                },
                "entity_type": row["entity_type"],
                "name": row["vendor_name"],
                "software": row["source_software"],
                "version": row["source_version_id"],
                "branch": row["source_branch"],
                "source_metadata": self.source_metadata[row["source_version_id"]],
                "fields": [self._field_payload(field, compact, mode) for _, field in sorted(fields.items())],
            }
            results.append(
                result_item(
                    "entity", row["evidence_classification"], row["provenance_class"],
                    _loads(row["source_ids_json"]), payload,
                    canonical_ref(row, row["entity_record_id"]), "not_operating_recommendation",
                )
            )
        return self.response("entity", mode, results, identity=identity, version=version, field=field_name)

    def lineage(self, identity: str, mode: str = "LINEAGE_AWARE") -> dict[str, Any]:
        canonical_id = normalized_identity(identity)
        results = self.entity(canonical_id, mode=mode, compact=True)["results"]
        if mode not in {"FIBRESEEK_CONFIRMED", "HISTORICAL"}:
            rows = self.connection.execute(
                "SELECT * FROM identity_links WHERE canonical_entity_id=? ORDER BY from_source_version,to_source_version,link_id",
                (canonical_id,),
            )
            for row in rows:
                record = _loads(row["record_json"])
                results.append(
                    result_item(
                        "identity_link", record["evidence_classification"], None,
                        record["source_ids"],
                        {key: record[key] for key in (
                            "canonical_entity_id", "entity_type", "from_source_version",
                            "to_source_version", "relationship", "from_entity_record_ids",
                            "to_entity_record_ids",
                        )},
                        canonical_ref(row, row["link_id"]), "identity_only_not_runtime_behavior",
                    )
                )
        return self.response("lineage", mode, results, identity=identity)

    def field_history(
        self, field_name: str, mode: str = "LINEAGE_AWARE", identity: str | None = None,
        version: str | None = None, entity_type: str | None = None, compact: bool = False,
        limit: int = 500,
    ) -> dict[str, Any]:
        clauses = ["f.field_name=?"]
        params: list[Any] = [field_name]
        if identity:
            clauses.append("e.canonical_entity_id=?")
            params.append(normalized_identity(identity))
        if version:
            clauses.append("f.source_version_id=?")
            params.append(version)
        if entity_type:
            clauses.append("e.entity_type=?")
            params.append(entity_type)
        sql = """SELECT f.*,e.canonical_entity_id,e.entity_type,e.vendor_name,e.application_key,
                 e.original_entity_uuid,e.normalized_entity_uuid,e.source_entity_type,
                 e.source_row_index,e.source_branch,e.canonical_path,e.record_sha256
                 FROM fields f JOIN entities e USING(entity_record_id)
                 WHERE %s ORDER BY e.canonical_entity_id,f.source_version_id,f.entity_record_id LIMIT ?""" % " AND ".join(clauses)
        results = []
        for row in self.connection.execute(sql, [*params, limit]):
            if not mode_allows_provenance(mode, row["provenance_class"]):
                continue
            field = _loads(row["field_json"])
            payload = {
                "canonical_entity_id": row["canonical_entity_id"],
                "entity_record_id": row["entity_record_id"],
                "entity_type": row["entity_type"],
                "name": row["vendor_name"],
                "source_native_identity": {
                    "original_uuid": row["original_entity_uuid"],
                    "normalized_uuid": row["normalized_entity_uuid"],
                    "application_key": row["application_key"],
                    "source_entity_type": row["source_entity_type"],
                    "source_row_index": row["source_row_index"],
                },
                "software": row["source_software"],
                "version": row["source_version_id"],
                "branch": row["source_branch"],
                "source_metadata": self.source_metadata[row["source_version_id"]],
                **self._field_payload(field, compact, mode),
            }
            results.append(
                result_item(
                    "field_observation", row["evidence_classification"], row["provenance_class"],
                    mode_filtered_source_ids(mode, _loads(row["source_ids_json"])), payload,
                    canonical_ref(row, f"{row['entity_record_id']}#{field_name}"),
                    "not_operating_recommendation",
                )
            )
        return self.response(
            "field", mode, results, field=field_name, identity=identity, version=version,
            entity_type=entity_type,
        )

    def deltas(
        self, from_version: str, to_version: str, mode: str = "LINEAGE_AWARE",
        identity: str | None = None, entity_type: str | None = None,
        field_name: str | None = None, classification: str | None = None, limit: int = 1000,
    ) -> dict[str, Any]:
        clauses = ["from_source_version=?", "to_source_version=?"]
        params: list[Any] = [from_version, to_version]
        if identity:
            clauses.append("canonical_entity_id=?")
            params.append(normalized_identity(identity))
        if entity_type:
            clauses.append("entity_type=?")
            params.append(entity_type)
        if field_name:
            clauses.append("field_name=?")
            params.append(field_name)
        if classification:
            clauses.append("EXISTS (SELECT 1 FROM json_each(classifications_json) WHERE value=?)")
            params.append(classification)
        results = []
        sql = f"SELECT * FROM deltas WHERE {' AND '.join(clauses)} ORDER BY delta_id LIMIT ?"
        for row in self.connection.execute(sql, [*params, limit]):
            record = _loads(row["record_json"])
            from_software = "Aura" if record["from_source_version"].startswith("aura-") else "Rocket"
            to_software = "Aura" if record["to_source_version"].startswith("aura-") else "Rocket"
            if mode == "FIBRESEEK_CONFIRMED" and (from_software != "Rocket" or to_software != "Rocket"):
                continue
            if mode == "HISTORICAL" and (from_software != "Aura" or to_software != "Aura"):
                continue
            results.append(
                result_item(
                    "delta", record["evidence_classification"],
                    FIBRESEEK if to_software == "Rocket" and from_software == "Rocket" else ANISOPRINT,
                    record["source_ids"],
                    {key: record.get(key) for key in (
                        "comparison_id", "from_source_version", "to_source_version", "entity_type",
                        "canonical_entity_id", "field_name", "from", "to", "classifications", "notes",
                    )},
                    canonical_ref(row, row["delta_id"]), "not_runtime_behavior",
                )
            )
        return self.response(
            "delta", mode, results, from_version=from_version, to_version=to_version,
            identity=identity, entity_type=entity_type, field=field_name, classification=classification,
        )

    def source(self, source_id: str, mode: str = "ALL_EVIDENCE") -> dict[str, Any]:
        row = self.connection.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        results = []
        if row and mode_allows_provenance(mode, row["provenance_class"]):
            reference_count = self.connection.execute(
                "SELECT count(*) FROM source_refs WHERE source_id=?", (source_id,)
            ).fetchone()[0]
            refs = [
                {"kind": item["record_kind"], "record_id": item["record_id"]}
                for item in self.connection.execute(
                    "SELECT record_kind,record_id FROM source_refs WHERE source_id=? ORDER BY record_kind,record_id LIMIT 200",
                    (source_id,),
                )
            ]
            payload = dict(row)
            payload["references"] = refs
            payload["reference_count"] = reference_count
            payload["references_truncated"] = reference_count > len(refs)
            results.append(
                result_item("source", "FACT", row["provenance_class"], [source_id], payload)
            )
        return self.response("source", mode, results, source_id=source_id)

    def questions(
        self, mode: str = "ALL_EVIDENCE", field_name: str | None = None,
        entity_type: str | None = None, domain: str | None = None,
        requirement: str | None = None,
    ) -> dict[str, Any]:
        clauses, params = [], []
        if domain:
            clauses.append("domain=?")
            params.append(domain)
        if requirement:
            clauses.append("resolution_requirement=?")
            params.append(requirement)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        results = []
        for row in self.connection.execute(f"SELECT * FROM questions{where} ORDER BY question_id", params):
            item = _loads(row["item_json"])
            if field_name and field_name not in item.get("fields", []):
                if item["question_id"] != "Q-ROCKET-OVERRIDE-PRECEDENCE":
                    continue
                rocket_fields = self.connection.execute(
                    "SELECT field_json FROM fields WHERE field_name=? AND source_software='Rocket'",
                    (field_name,),
                )
                if not any(
                    field["override_capable"]
                    and field["effective_value_status"] == "unknown"
                    for field in (_loads(candidate[0]) for candidate in rocket_fields)
                ):
                    continue
            if entity_type and entity_type not in item.get("entity_types", []):
                continue
            source_ids = item["source_ids"]
            if mode == "FIBRESEEK_CONFIRMED" and not any(s.startswith("FS-") for s in source_ids):
                continue
            if mode == "HISTORICAL" and not any(s.startswith("AP-") for s in source_ids):
                continue
            if mode == "FIBRESEEK_CONFIRMED":
                source_ids = [source_id for source_id in source_ids if source_id.startswith("FS-")]
                item = {**item, "source_ids": source_ids}
            elif mode == "HISTORICAL":
                source_ids = [source_id for source_id in source_ids if source_id.startswith("AP-")]
                item = {**item, "source_ids": source_ids}
            results.append(
                result_item(
                    "open_question", "OPEN_QUESTION", None, source_ids, item, None,
                    item.get("manufacturer_guidance"),
                )
            )
        return self.response(
            "questions", mode, results, field=field_name, entity_type=entity_type,
            domain=domain, requirement=requirement,
        )

    def enum(
        self, field_name: str, mode: str = "LINEAGE_AWARE", software: str | None = None,
        value: Any | None = None,
    ) -> dict[str, Any]:
        clauses, params = ["field_name=?"], [field_name]
        if software:
            clauses.append("software=?")
            params.append(software)
        results = []
        for row in self.connection.execute(
            f"SELECT * FROM enums WHERE {' AND '.join(clauses)} ORDER BY software,value_json,label", params
        ):
            item = _loads(row["item_json"])
            if value is not None and item["value"] != value:
                continue
            if not mode_allows_assertion(mode, item["classification"], item["software"], item["source_ids"]):
                continue
            if mode == "FIBRESEEK_CONFIRMED":
                filtered_ids = [source_id for source_id in item["source_ids"] if source_id.startswith("FS-")]
                item = {**item, "source_ids": filtered_ids}
            elif mode == "HISTORICAL":
                filtered_ids = [source_id for source_id in item["source_ids"] if source_id.startswith("AP-")]
                item = {**item, "source_ids": filtered_ids}
            provenance = FIBRESEEK if item["software"] == "Rocket" else ANISOPRINT
            results.append(
                result_item(
                    "enum_assertion", item["classification"], provenance, item["source_ids"], item,
                    None, "not_operating_recommendation",
                )
            )
        return self.response("enum", mode, results, field=field_name, software=software, value=value)

    def graph(
        self,
        identity: str,
        mode: str = "LINEAGE_AWARE",
        compact: bool = True,
        domain: str | None = None,
    ) -> dict[str, Any]:
        entity_rows = self.resolve_entities(identity=identity)
        record_ids = [row["entity_record_id"] for row in entity_rows]
        allowed_types = None
        reverse_edge_sources: set[str] = set()
        max_hops = 1
        if domain == "materials":
            allowed_types = MATERIAL_ENTITY_TYPES | {"profile", "profile_group"}
            reverse_edge_sources = {
                "profile_material_association",
                "slot_extruder_material_association",
            }
            max_hops = 2
        elif domain == "profiles":
            allowed_types = PROFILE_ENTITY_TYPES | {"plastic", "composite", "settings_set"}
            reverse_edge_sources = {"profile_material_association", "settings_set"}
            max_hops = 2
        elif domain is not None:
            raise ValueError(f"unknown graph domain: {domain}")

        record_types = {
            row["entity_record_id"]: row["entity_type"]
            for row in self.connection.execute(
                "SELECT entity_record_id,entity_type FROM entities"
            )
        }
        relationship_records = [
            _loads(row[0])
            for row in self.connection.execute(
                "SELECT record_json FROM relationships ORDER BY relationship_id"
            )
        ]
        selected_relationships: dict[str, dict[str, Any]] = {}
        selected_ids = set(record_ids)
        frontier = set(record_ids)
        for _ in range(max_hops):
            next_frontier = set()
            for record in relationship_records:
                from_id = record["from_entity_record_id"]
                targets = set(record["to_entity_record_ids"])
                endpoints = {from_id, *targets}
                if not endpoints & frontier:
                    continue
                if allowed_types is None:
                    permitted = endpoints
                else:
                    from_type = record_types.get(from_id)
                    if from_type not in allowed_types:
                        continue
                    if (
                        from_id not in frontier
                        and targets & frontier
                        and from_type not in reverse_edge_sources
                    ):
                        continue
                    permitted = {
                        record_id
                        for record_id in endpoints
                        if record_types.get(record_id) in allowed_types
                    }
                    if len(permitted) < 2:
                        continue
                selected_relationships[record["relationship_id"]] = record
                next_frontier.update(permitted - selected_ids)
                selected_ids.update(permitted)
            frontier = next_frontier
            if not frontier:
                break
        related_ids = selected_ids - set(record_ids)
        results = self.entity(identity, mode=mode, compact=compact)["results"]
        for item in results:
            fields = item["payload"].get("fields", [])
            item["payload"]["field_count"] = len(fields)
            item["payload"]["fields"] = fields[:80]
            item["payload"]["fields_truncated"] = len(fields) > 80
        for related_id in sorted(related_ids):
            related = self.entity(related_id, mode=mode, compact=True)["results"]
            for item in related:
                fields = item["payload"].get("fields", [])
                item["payload"]["field_count"] = len(fields)
                item["payload"]["fields"] = fields[:20]
                item["payload"]["fields_truncated"] = len(fields) > 20
            results.extend(related)
        for record in selected_relationships.values():
            results.append(
                result_item(
                    "relationship", record["evidence_classification"], None, record["source_ids"],
                    {key: record[key] for key in (
                        "relationship_id", "source_version_id", "from_entity_record_id",
                        "to_entity_record_ids", "field_name", "relationship",
                    )},
                )
            )
        return self.response("graph", mode, results, identity=identity, domain=domain)

    def engineering_view(
        self, view: str, mode: str = "LINEAGE_AWARE", identity: str | None = None,
        version: str | None = None, name: str | None = None, limit: int = 100,
    ) -> dict[str, Any]:
        view = view.lower()
        if view == "lineage":
            if not identity:
                raise ValueError("lineage view requires --identity")
            return self.lineage(identity, mode)
        if view not in {"machine", "materials", "profiles"}:
            raise ValueError(f"unknown engineering view: {view}")
        types = MACHINE_ENTITY_TYPES if view == "machine" else MATERIAL_ENTITY_TYPES if view == "materials" else PROFILE_ENTITY_TYPES
        pattern = MACHINE_FIELD_RE if view == "machine" else MATERIAL_FIELD_RE if view == "materials" else PROFILE_FIELD_RE
        rows = []
        for entity_type in sorted(types):
            rows.extend(self.resolve_entities(identity=identity, entity_type=entity_type, version=version, name=name, limit=limit))
        results = []
        for row in sorted(rows, key=lambda x: (x["canonical_entity_id"], x["source_version_id"], x["entity_record_id"]))[:limit]:
            if not mode_allows_provenance(mode, row["provenance_class"]):
                continue
            all_fields = [
                (item["field_name"], _loads(item["field_json"]))
                for item in self.connection.execute(
                    "SELECT field_name,field_json FROM fields WHERE entity_record_id=? ORDER BY field_name",
                    (row["entity_record_id"],),
                )
            ]
            matching = [(name_, field) for name_, field in all_fields if pattern.search(name_)]
            if view == "profiles":
                selected_pairs = []
                selected_names = set()
                for bucket in PROFILE_FIELD_BUCKETS:
                    for name_, field in matching:
                        if len([name for name, _ in selected_pairs if bucket.search(name)]) >= 6:
                            break
                        if name_ not in selected_names and bucket.search(name_):
                            selected_pairs.append((name_, field))
                            selected_names.add(name_)
                selected = [field for _, field in selected_pairs]
            else:
                selected = [field for _, field in matching[:80]]
            payload = {
                "view": view,
                "canonical_entity_id": row["canonical_entity_id"],
                "entity_record_id": row["entity_record_id"],
                "entity_type": row["entity_type"],
                "name": row["vendor_name"],
                "version": row["source_version_id"],
                "software": row["source_software"],
                "fields": [self._field_payload(field, True, mode) for field in selected],
                "matching_field_count": len(matching),
                "selected_field_count": len(selected),
                "fields_truncated": len(matching) > len(selected),
            }
            results.append(
                result_item(
                    f"{view}_view", "FACT", row["provenance_class"],
                    _loads(row["source_ids_json"]), payload,
                    canonical_ref(row, row["entity_record_id"]), "not_operating_recommendation",
                )
            )
        return self.response(view, mode, results, identity=identity, version=version, name=name)

    def _refs_for_field(self, field_name: str, software: str | None = None) -> list[dict[str, str]]:
        clauses, params = ["f.field_name=?"], [field_name]
        if software:
            clauses.append("f.source_software=?")
            params.append(software)
        sql = """SELECT f.entity_record_id,e.canonical_path,e.record_sha256 FROM fields f
                 JOIN entities e USING(entity_record_id) WHERE %s
                 ORDER BY f.source_version_id,f.entity_record_id""" % " AND ".join(clauses)
        return [canonical_ref(row, f"{row['entity_record_id']}#{field_name}") for row in self.connection.execute(sql, params)]

    def _filter_answer_assertions(self, assertions: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
        results = []
        for assertion in assertions:
            software = assertion.pop("_software")
            if mode_allows_assertion(mode, assertion["classification"], software, assertion["source_ids"]):
                results.append(assertion)
        return results

    def answer_unit(self, field_name: str, mode: str = "LINEAGE_AWARE") -> dict[str, Any]:
        assertions = []
        rows = self.connection.execute(
            "SELECT * FROM units WHERE field_name=? ORDER BY software", (field_name,)
        )
        for row in rows:
            item = _loads(row["item_json"])
            software = item["software"]
            provenance = FIBRESEEK if software == "Rocket" else ANISOPRINT
            if software == "Rocket" and item["status"] == "inferred":
                fs_ids = [source_id for source_id in item["source_ids"] if source_id.startswith("FS-")]
                assertions.append(
                    {
                        "assertion_id": stable_id("assertion", field_name, "Rocket", "unit-label-absent"),
                        "subject": f"Rocket.{field_name}", "predicate": "first_party_unit_label",
                        "value": None, "unit": None, "classification": "FACT",
                        "evidence_scope": "FIBRESEEK_FIRST_PARTY", "provenance_class": FIBRESEEK,
                        "source_ids": fs_ids, "manufacturer_guidance": "unit_not_confirmed",
                        "canonical_refs": self._refs_for_field(field_name, "Rocket"),
                        "notes": ["No Rocket/FibreSeek unit label is represented by the canonical evidence."],
                        "_software": "Rocket",
                    }
                )
                assertions.append(
                    {
                        "assertion_id": stable_id("assertion", field_name, "Rocket", "lineage-unit", item["unit"]),
                        "subject": f"Rocket.{field_name}", "predicate": "lineage_unit",
                        "value": item["unit"], "unit": None, "classification": "INFERENCE",
                        "evidence_scope": "LINEAGE_INFERENCE", "provenance_class": FIBRESEEK,
                        "source_ids": item["source_ids"],
                        "manufacturer_guidance": item.get("manufacturer_guidance"),
                        "canonical_refs": self._refs_for_field(field_name, "Rocket"),
                        "notes": [item.get("notes", "")], "_software": "Rocket",
                    }
                )
                assertions.append(
                    {
                        "assertion_id": stable_id("assertion", field_name, "Rocket", "manufacturer-unit"),
                        "subject": f"FibreSeek.{field_name}", "predicate": "manufacturer_confirmed_unit",
                        "value": None, "unit": None, "classification": "OPEN_QUESTION",
                        "evidence_scope": "UNRESOLVED", "provenance_class": FIBRESEEK,
                        "source_ids": fs_ids, "manufacturer_guidance": "unresolved_for_fibreseek",
                        "canonical_refs": self._refs_for_field(field_name, "Rocket"),
                        "notes": ["Lineage inference is not manufacturer confirmation."],
                        "_software": "Rocket",
                    }
                )
            else:
                assertions.append(
                    {
                        "assertion_id": stable_id("assertion", field_name, software, "unit", item["unit"]),
                        "subject": f"{software}.{field_name}", "predicate": "unit",
                        "value": item["unit"], "unit": None, "classification": item["classification"],
                        "evidence_scope": evidence_scope(item["classification"], provenance),
                        "provenance_class": provenance, "source_ids": item["source_ids"],
                        "manufacturer_guidance": item.get("manufacturer_guidance"),
                        "canonical_refs": self._refs_for_field(field_name, software if software in {"Aura", "Rocket"} else None),
                        "notes": [item.get("notes", "")], "_software": software,
                    }
                )
        assertions = self._filter_answer_assertions(assertions, mode)
        open_questions = [item["payload"] for item in self.questions(mode, field_name=field_name)["results"]]
        unresolved = any(item["classification"] == "OPEN_QUESTION" for item in assertions) or bool(open_questions)
        return {
            "answer_version": CONTRACT_VERSION,
            "question": {"type": "unit", "field": field_name},
            "view_mode": mode,
            "answer_status": "UNRESOLVED" if unresolved else "SUPPORTED" if assertions else "NO_EVIDENCE",
            "assertions": assertions,
            "conflicts": [],
            "open_questions": open_questions,
            "operating_recommendation": None,
            "warnings": ["A lineage-inferred unit must not be presented as FibreSeek manufacturer guidance."],
        }

    def answer_cutter(self, mode: str = "LINEAGE_AWARE") -> dict[str, Any]:
        identity = "uuid:f3904c6f-c24e-4aff-ad9a-70405cc4df84"
        observations = []
        for field_name in ("CutDistance", "FiberRestartLength", "CutCode"):
            observations.extend(self.field_history(field_name, mode, identity=identity, compact=True)["results"])
        assertions = []
        for item in observations:
            payload = item["payload"]
            value = payload["base_value"]
            # Confirmed mode deliberately filters non-fact nested unit semantics
            # (notably the CutCode comment). The cutter answer must preserve that
            # absence instead of assuming every filtered field still has a unit.
            unit = payload.get("unit")
            predicate = payload["field"]
            if predicate == "CutCode":
                match = re.search(r";CUT(?: DISTANCE)?\s+([0-9.]+)", str(value))
                value = float(match.group(1)) if match else None
                unit = "mm_comment" if value is not None else None
                predicate = "CutCode_comment_distance"
            assertions.append(
                {
                    "assertion_id": stable_id("assertion", payload["version"], predicate, value),
                    "subject": f"{payload['version']}.CFC", "predicate": predicate,
                    "value": value, "unit": unit, "classification": item["classification"],
                    "evidence_scope": item["evidence_scope"],
                    "provenance_class": item["provenance_class"], "source_ids": item["source_ids"],
                    "manufacturer_guidance": "not_operating_recommendation",
                    "canonical_refs": [item["canonical_ref"]], "notes": [],
                }
            )
        rocket_values = sorted(
            {(item["predicate"], item["value"]) for item in assertions if item["subject"].startswith("rocket-")}
        )
        conflict = {
            "conflict_id": "C-CUTTER-RUNTIME-PRECEDENCE",
            "classification": "OPEN_QUESTION",
            "values": [{"field": field, "value": value} for field, value in rocket_values],
            "reason": "Structured distance, restart length, and G-code comment are distinct preserved values; static evidence does not establish runtime precedence.",
            "operating_recommendation": None,
        }
        open_questions = [
            item["payload"] for item in self.questions(mode, field_name="CutDistance")["results"]
            if item["payload"]["question_id"] == "Q-CUTTER-RUNTIME-PRECEDENCE"
        ]
        return {
            "answer_version": CONTRACT_VERSION,
            "question": {"type": "cutter_distance", "canonical_entity_id": identity},
            "view_mode": mode,
            "answer_status": "CONFLICTING" if assertions else "NO_EVIDENCE",
            "assertions": assertions,
            "conflicts": [conflict] if assertions else [],
            "open_questions": open_questions,
            "operating_recommendation": None,
            "warnings": ["Do not collapse 58, 55, and 54.8 into a single runtime or calibration value."],
        }

    def answer_field(
        self, field_name: str, identity: str | None = None, mode: str = "LINEAGE_AWARE"
    ) -> dict[str, Any]:
        observations = self.field_history(field_name, mode, identity=identity, compact=True)["results"]
        assertions = []
        values = set()
        for item in observations:
            payload = item["payload"]
            values.add(canonical_json([payload["base_value"], payload["override_value"]]))
            assertions.append(
                {
                    "assertion_id": stable_id("assertion", payload["entity_record_id"], field_name),
                    "subject": f"{payload['version']}.{payload['canonical_entity_id']}",
                    "predicate": field_name, "value": payload["base_value"], "unit": payload.get("unit"),
                    "classification": item["classification"], "evidence_scope": item["evidence_scope"],
                    "provenance_class": item["provenance_class"], "source_ids": item["source_ids"],
                    "manufacturer_guidance": "not_operating_recommendation",
                    "canonical_refs": [item["canonical_ref"]],
                    "notes": [f"override={payload['override_value']!r}; effective_status={payload['effective_value_status']}"],
                }
            )
        questions = [item["payload"] for item in self.questions(mode, field_name=field_name)["results"]]
        status = "NO_EVIDENCE" if not assertions else "UNRESOLVED" if questions else "CONFLICTING" if len(values) > 1 else "SUPPORTED"
        return {
            "answer_version": CONTRACT_VERSION,
            "question": {"type": "field", "field": field_name, "identity": identity},
            "view_mode": mode, "answer_status": status, "assertions": assertions,
            "conflicts": [] if len(values) <= 1 else [{"field": field_name, "distinct_structures": len(values)}],
            "open_questions": questions, "operating_recommendation": None,
            "warnings": ["Effective runtime values remain unknown wherever effective_value_status is unknown."],
        }


def ensure_index(repo_root: Path, db_path: Path, rebuild: bool = False) -> dict[str, Any]:
    if rebuild or not db_path.exists():
        return build_index(repo_root, db_path)
    digest, _ = input_digest(repo_root)
    connection = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    existing = connection.execute("SELECT value FROM metadata WHERE key='input_digest'").fetchone()
    schema = connection.execute(
        "SELECT value FROM metadata WHERE key='index_schema_version'"
    ).fetchone()
    connection.close()
    if not existing or existing[0] != digest or not schema or schema[0] != INDEX_SCHEMA_VERSION:
        return build_index(repo_root, db_path)
    return {"index_schema_version": INDEX_SCHEMA_VERSION, "input_digest": digest, "database_sha256": sha256_file(db_path), "database_bytes": db_path.stat().st_size, "rebuilt": False}
