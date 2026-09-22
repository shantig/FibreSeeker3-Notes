#!/usr/bin/env python3
"""Deterministic Phase 2C planning, context packets, and safety evaluation.

This module consumes Phase 2B responses. It does not add technical facts,
choose runtime values, or mutate canonical/index inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from query_engine import VIEW_MODES, QueryEngine, canonical_json


PLAN_VERSION = "1.0.0"
PACKET_VERSION = "1.0.0"
CANDIDATE_VERSION = "1.0.0"
EVALUATION_VERSION = "1.0.0"
DEFAULT_MODE = "LINEAGE_AWARE"

SEEKER_UUID = "83bf1039-8c9e-49fc-928f-2f94a2008d40"
X_CCF_UUID = "2af8ac62-4968-4364-88e3-1045ef47feba"
CFC_UUID = "f3904c6f-c24e-4aff-ad9a-70405cc4df84"
MIGRATED_PROFILE_UUID = "d294a2dc-9d7f-460a-acf4-dc50b656d44a"
CCF02_GROUP_UUIDS = (
    "4d816c47-4b74-4420-af0c-054ac6867278",
    "9599e88f-afd9-4109-9b18-3ba338003cba",
)

FORBIDDEN_CONCLUSIONS = [
    "OPERATING_RECOMMENDATION",
    "FIBRESEEK_GUIDANCE",
    "PHYSICAL_EQUIVALENCE",
    "RUNTIME_EQUIVALENCE",
    "UNKNOWN_RESOLUTION",
]

CLASS_SCOPE = {
    "FACT": {"FIBRESEEK_FIRST_PARTY", "HISTORICAL_ANISOPRINT"},
    "INFERENCE": {"LINEAGE_INFERENCE"},
    "OPEN_QUESTION": {"UNRESOLVED"},
    "EXPERIMENTAL": {"EXPERIMENTAL"},
}

ENUM_RULES = (
    ("tetragrid", "InfillFType", "Q-TETRAGRID-ENUM"),
    ("profile status", "ProfileStatus", "Q-PROFILE-STATUS-ENUM"),
    ("profilestatus", "ProfileStatus", "Q-PROFILE-STATUS-ENUM"),
    ("profile type", "ProfileType", "Q-PROFILE-TYPE-ENUM"),
    ("profiletype", "ProfileType", "Q-PROFILE-TYPE-ENUM"),
    ("postprocessor", "PostprocessorType", "Q-POSTPROCESSOR-ENUM"),
    ("edition", "Edition", "Q-EDITION-ENUM"),
    ("universal slot", "SlotType", "Q-UNIVERSAL-SLOT-ENUM"),
    ("universal-slot", "SlotType", "Q-UNIVERSAL-SLOT-ENUM"),
    ("slot type", "SlotType", "Q-UNIVERSAL-SLOT-ENUM"),
)


class ContractError(ValueError):
    """Raised when a Phase 2C structured object violates its contract."""


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_question(question: str) -> str:
    return " ".join(question.strip().casefold().split())


def _op(order: int, operation: str, arguments: dict[str, Any], rationale: str) -> dict[str, Any]:
    return {
        "order": order,
        "operation": operation,
        "arguments": arguments,
        "rationale": rationale,
    }


def _intent(
    intent: str,
    family: str,
    domain: str,
    fields: Iterable[str] = (),
    identities: Iterable[str] = (),
    versions: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "intent": intent,
        "family": family,
        "domain": domain,
        "fields": list(fields),
        "identities": list(identities),
        "versions": list(versions),
    }


def plan_question(question: str, requested_mode: str | None = None) -> dict[str, Any]:
    """Map a bounded benchmark question to Phase 2B operations without truth finding."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    if requested_mode is not None and requested_mode not in VIEW_MODES:
        raise ValueError(f"unknown evidence mode: {requested_mode}")

    normalized = normalize_question(question)
    mode = requested_mode or DEFAULT_MODE
    status = "MATCHED"
    assumptions: list[str] = []
    question_ids: list[str] = []
    domains: list[str] = []
    operations: list[dict[str, Any]] = []

    if (
        "lineardensity" in normalized.replace(" ", "")
        or "linear density" in normalized
        or "aura used tex" in normalized
        or "rocket must" in normalized and "tex" in normalized
    ):
        intent = _intent("unit_and_value_boundary", "linear_density", "materials", ["LinearDensity"], [X_CCF_UUID])
        operations = [
            _op(1, "answer_unit", {"field_name": "LinearDensity"}, "Retrieve independently classified unit assertions."),
            _op(2, "field", {"field_name": "LinearDensity", "identity": X_CCF_UUID, "compact": True}, "Retrieve the source-version value history without inferring a unit."),
        ]
        answer_type = "UNIT_BOUNDARY"
        domains = ["materials"]
    elif any(token in normalized for token in ("cutter", "cutdistance", "cut distance", "fiberrestartlength", "restart length", "54.8", "cutcode", "cut code")):
        intent = _intent(
            "conflicting_cutter_observations", "cutter_semantics", "machine",
            ["CutDistance", "FiberRestartLength", "CutCode"], [CFC_UUID],
        )
        operations = [_op(1, "answer_cutter", {}, "Retrieve the preserved cutter structures, conflict, and runtime-precedence question together.")]
        answer_type = "CONFLICT_SET"
        question_ids = ["Q-CUTTER-RUNTIME-PRECEDENCE"]
        domains = ["machine"]
    elif "macrolayerheight" in normalized.replace(" ", "") or "macro layer height" in normalized or "macrolayer height" in normalized:
        intent = _intent("base_override_history", "macro_layer_height", "profiles", ["MacroLayerHeight"], [MIGRATED_PROFILE_UUID])
        operations = [_op(1, "answer_field", {"field_name": "MacroLayerHeight", "identity": MIGRATED_PROFILE_UUID}, "Retrieve base/override structures and unresolved Rocket precedence.")]
        answer_type = "FIELD_STRUCTURE_HISTORY"
        question_ids = ["Q-ROCKET-OVERRIDE-PRECEDENCE"]
        domains = ["profiles"]
    elif "fiberspoollength" in normalized.replace(" ", "") or "fiber spool length" in normalized:
        intent = _intent("unit_boundary", "fiber_spool_length", "materials", ["FiberSpoolLength"])
        operations = [_op(1, "answer_unit", {"field_name": "FiberSpoolLength"}, "Retrieve explicit unknown-unit assertions and the registered resolution boundary.")]
        answer_type = "UNIT_BOUNDARY"
        question_ids = ["Q-FIBER-SPOOL-LENGTH-UNIT"]
        domains = ["materials"]
    elif "ccf02" in normalized:
        intent = _intent("name_semantics", "ccf02", "materials", identities=CCF02_GROUP_UUIDS)
        operations = [
            _op(1, "entity", {"identity": CCF02_GROUP_UUIDS[0], "compact": True}, "Retrieve the first exact CCF02-named profile-group occurrence without assigning a meaning."),
            _op(2, "entity", {"identity": CCF02_GROUP_UUIDS[1], "compact": True}, "Retrieve the second exact CCF02-named profile-group occurrence without assigning a meaning."),
            _op(3, "questions", {"domain": "materials"}, "Retrieve the registered CCF02 meaning boundary."),
        ]
        answer_type = "UNRESOLVED_SEMANTICS"
        question_ids = ["Q-CCF02-MEANING"]
        domains = ["materials"]
    elif any(token in normalized for token in ("infillftype", "infill ftype", "infill type", "isogrid", "anisogrid", "rhombic")):
        intent = _intent("version_aware_enum", "infill_ftype", "profiles", ["InfillFType"])
        operations = [
            _op(1, "enum", {"field_name": "InfillFType"}, "Retrieve Aura facts and Rocket mappings with their independent classifications."),
            _op(2, "questions", {"field_name": "InfillFType"}, "Retrieve unresolved Tetragrid semantics."),
        ]
        answer_type = "ENUM_BOUNDARY"
        question_ids = ["Q-TETRAGRID-ENUM"]
        domains = ["profiles"]
    else:
        enum_match = next((item for item in ENUM_RULES if item[0] in normalized), None)
        if enum_match:
            _, field_name, question_id = enum_match
            domain = "machine" if field_name in {"PostprocessorType", "SlotType"} else "profiles"
            intent = _intent("version_aware_enum", f"enum_{field_name.casefold()}", domain, [field_name])
            operations = [
                _op(1, "enum", {"field_name": field_name}, "Retrieve only registered mappings and confidence labels."),
                _op(2, "questions", {"field_name": field_name}, "Retrieve the registered unresolved semantic boundary."),
            ]
            answer_type = "ENUM_BOUNDARY"
            question_ids = [question_id]
            domains = [domain]
        elif (
            "v13" in normalized and "v15" in normalized
        ) or (
            "rocket 13" in normalized and "rocket 15" in normalized
        ) or "rocket-v13" in normalized and "rocket-v15" in normalized:
            intent = _intent("version_delta", "rocket_v13_v15", "versions", versions=["rocket-v13", "rocket-v15"])
            operations = [_op(1, "delta", {"from_version": "rocket-v13", "to_version": "rocket-v15", "classification": "added", "entity_level_only": True, "limit": 2000}, "Retrieve added canonical entity delta records; preserve source-native occurrence counts separately.")]
            answer_type = "VERSION_DELTA"
        elif X_CCF_UUID in normalized or "x-ccf" in normalized or "x ccf" in normalized:
            intent = _intent("exact_uuid_lineage", "x_ccf_lineage", "identity", identities=[X_CCF_UUID])
            operations = [_op(1, "lineage", {"identity": X_CCF_UUID}, "Retrieve exact data-identity occurrences and links only.")]
            answer_type = "IDENTITY_LINEAGE"
        elif SEEKER_UUID in normalized or "seeker printer" in normalized or "printer uuid" in normalized:
            intent = _intent("exact_uuid_lineage", "seeker_lineage", "identity", identities=[SEEKER_UUID])
            operations = [_op(1, "lineage", {"identity": SEEKER_UUID}, "Retrieve exact data-identity occurrences and links only.")]
            answer_type = "IDENTITY_LINEAGE"
        else:
            status = "SAFE_FAILURE"
            intent = _intent("unsupported_question", "unknown", "unknown")
            operations = []
            answer_type = "NO_EVIDENCE"
            assumptions = ["No bounded Phase 2C planner rule matched the question; no technical identity or field correspondence was invented."]

    plan_without_id = {
        "plan_version": PLAN_VERSION,
        "original_question": question.strip(),
        "normalized_intent": intent,
        "requested_evidence_mode": requested_mode,
        "evidence_mode": mode,
        "mode_selection": "EXPLICIT" if requested_mode is not None else "DEFAULT",
        "planner_status": status,
        "query_operations": operations,
        "expected_answer_type": answer_type,
        "relevant_open_question_domains": sorted(domains),
        "required_open_question_ids": sorted(question_ids),
        "operating_guidance_prohibited": True,
        "assumptions": assumptions,
        "forbidden_conclusion_types": FORBIDDEN_CONCLUSIONS,
    }
    plan = {"plan_version": PLAN_VERSION, "plan_id": f"plan:{stable_hash(plan_without_id)}", **{key: value for key, value in plan_without_id.items() if key != "plan_version"}}
    validate_query_plan(plan)
    return plan


def _execute_operation(engine: QueryEngine, operation: dict[str, Any], mode: str) -> dict[str, Any]:
    name = operation["operation"]
    args = operation["arguments"]
    if name == "answer_unit":
        return engine.answer_unit(args["field_name"], mode)
    if name == "answer_cutter":
        return engine.answer_cutter(mode)
    if name == "answer_field":
        return engine.answer_field(args["field_name"], args.get("identity"), mode)
    if name == "field":
        return engine.field_history(
            args["field_name"], mode, identity=args.get("identity"),
            version=args.get("version"), entity_type=args.get("entity_type"),
            compact=args.get("compact", True), limit=args.get("limit", 100),
        )
    if name == "enum":
        return engine.enum(args["field_name"], mode, args.get("software"), args.get("value"))
    if name == "questions":
        return engine.questions(
            mode, field_name=args.get("field_name"), entity_type=args.get("entity_type"),
            domain=args.get("domain"), requirement=args.get("requirement"),
        )
    if name == "lineage":
        return engine.lineage(args["identity"], mode)
    if name == "delta":
        return engine.deltas(
            args["from_version"], args["to_version"], mode,
            identity=args.get("identity"), entity_type=args.get("entity_type"),
            field_name=args.get("field_name"), classification=args.get("classification"),
            limit=args.get("limit", 1000),
        )
    if name == "entity":
        return engine.entity(
            args["identity"], mode, version=args.get("version"),
            field_name=args.get("field_name"), compact=args.get("compact", True),
        )
    raise ValueError(f"unsupported planned operation: {name}")


def _question_payload(item: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "question_id", "title", "domain", "entity_types", "fields",
        "canonical_entity_ids", "classification", "source_ids",
        "evidence_available", "resolution_requirement", "resolution_evidence",
        "manufacturer_guidance",
    )
    return {key: item.get(key) for key in keys if key in item}


def _normal_result_evidence(item: dict[str, Any]) -> dict[str, Any] | None:
    payload = item["payload"]
    kind = item["kind"]
    if kind == "open_question":
        return None
    if kind == "field_observation":
        subject = f"{payload['version']}.{payload['canonical_entity_id']}"
        predicate = payload["field"]
        value = {
            "raw_value": payload.get("raw_value"),
            "base_value": payload.get("base_value"),
            "override_value": payload.get("override_value"),
            "effective_value": payload.get("effective_value"),
            "effective_value_status": payload.get("effective_value_status"),
        }
        unit = payload.get("unit")
        details = {
            key: payload.get(key)
            for key in (
                "entity_record_id", "entity_type", "name", "software", "version",
                "branch", "source_native_identity", "unit_status", "unit_classification",
                "lineage_relationship", "filtered_assertions",
            )
            if key in payload
        }
    elif kind == "enum_assertion":
        subject = f"{payload['software']}.{payload['field_name']}"
        predicate = "enum_mapping"
        value = {"numeric_value": payload.get("value"), "label": payload.get("label"), "status": payload.get("status")}
        unit = None
        details = {"field_name": payload["field_name"], "software": payload["software"], "notes": payload.get("notes")}
    elif kind == "entity":
        subject = payload["canonical_entity_id"]
        predicate = "entity_occurrence"
        value = {"version": payload["version"], "entity_type": payload["entity_type"], "name": payload.get("name")}
        unit = None
        details = {key: payload.get(key) for key in ("software", "branch", "source_native_identity")}
    elif kind == "identity_link":
        subject = payload["canonical_entity_id"]
        predicate = "exact_uuid_lineage"
        value = {key: payload.get(key) for key in ("from_source_version", "to_source_version", "relationship")}
        unit = None
        details = {key: payload.get(key) for key in ("entity_type", "from_entity_record_ids", "to_entity_record_ids")}
    elif kind == "delta":
        subject = payload.get("canonical_entity_id") or payload["entity_type"]
        predicate = "version_delta"
        from_occurrences = payload.get("from") or []
        to_occurrences = payload.get("to") or []
        value = {
            "from_source_version": payload.get("from_source_version"),
            "to_source_version": payload.get("to_source_version"),
            "entity_type": payload.get("entity_type"),
            "field_name": payload.get("field_name"),
            "classifications": payload.get("classifications"),
            "from_source_native_occurrence_count": len(from_occurrences),
            "to_source_native_occurrence_count": len(to_occurrences),
        }
        unit = None
        details = {
            "comparison_id": payload.get("comparison_id"),
            "source_native_occurrences": {
                "from": [
                    (
                        {key: occurrence.get(key) for key in ("entity_record_id", "application_key")}
                        if isinstance(occurrence, dict)
                        else {"entity_record_id": occurrence, "application_key": None}
                    )
                    for occurrence in from_occurrences
                ],
                "to": [
                    (
                        {key: occurrence.get(key) for key in ("entity_record_id", "application_key")}
                        if isinstance(occurrence, dict)
                        else {"entity_record_id": occurrence, "application_key": None}
                    )
                    for occurrence in to_occurrences
                ],
            },
            "notes": payload.get("notes"),
        }
    else:
        subject = str(payload.get("canonical_entity_id") or payload.get("source_id") or kind)
        predicate = kind
        value = payload
        unit = None
        details = {}

    refs = [item["canonical_ref"]] if item.get("canonical_ref") else []
    identity = [kind, subject, predicate, value, item["classification"], item["evidence_scope"], refs]
    return {
        "evidence_id": f"evidence:{stable_hash(identity)}",
        "kind": kind,
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "unit": unit,
        "classification": item["classification"],
        "evidence_scope": item["evidence_scope"],
        "provenance_class": item.get("provenance_class"),
        "source_ids": sorted(item.get("source_ids", [])),
        "manufacturer_guidance": item.get("manufacturer_guidance"),
        "canonical_refs": refs,
        "canonical_reference_required": bool(refs),
        "details": details,
    }


def _answer_assertion_evidence(assertion: dict[str, Any]) -> dict[str, Any]:
    refs = assertion.get("canonical_refs", [])
    return {
        "evidence_id": assertion["assertion_id"],
        "kind": "engineering_assertion",
        "subject": assertion["subject"],
        "predicate": assertion["predicate"],
        "value": assertion["value"],
        "unit": assertion.get("unit"),
        "classification": assertion["classification"],
        "evidence_scope": assertion["evidence_scope"],
        "provenance_class": assertion.get("provenance_class"),
        "source_ids": sorted(assertion.get("source_ids", [])),
        "manufacturer_guidance": assertion.get("manufacturer_guidance"),
        "canonical_refs": refs,
        "canonical_reference_required": bool(refs) and assertion["classification"] != "OPEN_QUESTION",
        "details": {"notes": assertion.get("notes", [])},
    }


def build_context_packet(engine: QueryEngine, plan: dict[str, Any]) -> dict[str, Any]:
    """Execute a valid plan and retain only structured answer-critical evidence."""
    validate_query_plan(plan)
    evidence: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    questions: dict[str, dict[str, Any]] = {}
    retrievals: list[dict[str, Any]] = []
    warnings: set[str] = set()
    answer_statuses: list[str] = []

    for operation in plan["query_operations"]:
        response = _execute_operation(engine, operation, plan["evidence_mode"])
        response_digest = stable_hash(response)
        if "answer_version" in response:
            answer_statuses.append(response["answer_status"])
            evidence.extend(_answer_assertion_evidence(item) for item in response["assertions"])
            conflicts.extend(copy.deepcopy(response["conflicts"]))
            for item in response["open_questions"]:
                if item.get("question_id"):
                    questions[item["question_id"]] = _question_payload(item)
            warnings.update(response.get("warnings", []))
            result_count = len(response["assertions"])
        else:
            for item in response["results"]:
                if (
                    operation["operation"] == "delta"
                    and operation["arguments"].get("entity_level_only")
                    and item["payload"].get("field_name") is not None
                ):
                    continue
                if item["kind"] == "open_question":
                    payload = item["payload"]
                    questions[payload["question_id"]] = _question_payload(payload)
                else:
                    converted = _normal_result_evidence(item)
                    if converted is not None:
                        evidence.append(converted)
            warnings.update(response.get("warnings", []))
            result_count = response["result_count"]
        retrievals.append(
            {
                "order": operation["order"],
                "operation": operation["operation"],
                "arguments": operation["arguments"],
                "result_count": result_count,
                "response_sha256": response_digest,
            }
        )

    unique_evidence = {item["evidence_id"]: item for item in evidence}
    evidence = [unique_evidence[key] for key in sorted(unique_evidence)]
    targeted_field_refs: dict[tuple[str, str], list[dict[str, str]]] = {}
    for item in evidence:
        if item["kind"] != "field_observation":
            continue
        software = "Aura" if item["subject"].startswith("aura-") else "Rocket"
        targeted_field_refs.setdefault((item["predicate"], software), []).extend(item["canonical_refs"])
    for item in evidence:
        if item["kind"] != "engineering_assertion":
            continue
        original_refs = item["canonical_refs"]
        if item["classification"] == "OPEN_QUESTION":
            item["canonical_refs"] = []
        elif "." in item["subject"]:
            software, field_name = item["subject"].split(".", 1)
            software = "Rocket" if software == "FibreSeek" else software
            targeted = targeted_field_refs.get((field_name, software), [])
            if targeted:
                unique_targeted = {canonical_json(ref): ref for ref in targeted}
                item["canonical_refs"] = [unique_targeted[key] for key in sorted(unique_targeted)]
            elif len(original_refs) > 4:
                item["canonical_refs"] = original_refs[:4]
        if len(item["canonical_refs"]) != len(original_refs):
            item["details"]["canonical_ref_count_before_projection"] = len(original_refs)
            item["details"]["canonical_refs_projected"] = True
    unique_conflicts = {stable_hash(item): item for item in conflicts}
    conflicts = [unique_conflicts[key] for key in sorted(unique_conflicts)]
    if plan["required_open_question_ids"]:
        required_ids = set(plan["required_open_question_ids"])
        questions = {key: value for key, value in questions.items() if key in required_ids}

    if conflicts or "CONFLICTING" in answer_statuses:
        answer_status = "CONFLICTING"
    elif questions or any(item["classification"] == "OPEN_QUESTION" for item in evidence) or "UNRESOLVED" in answer_statuses:
        answer_status = "UNRESOLVED"
    elif evidence:
        answer_status = "SUPPORTED"
    else:
        answer_status = "NO_EVIDENCE"

    refs = {
        canonical_json(ref): ref
        for item in evidence
        for ref in item["canonical_refs"]
    }
    base = {
        "packet_version": PACKET_VERSION,
        "plan_id": plan["plan_id"],
        "question": plan["original_question"],
        "normalized_intent": plan["normalized_intent"],
        "evidence_mode": plan["evidence_mode"],
        "planner_status": plan["planner_status"],
        "expected_answer_type": plan["expected_answer_type"],
        "answer_status": answer_status,
        "evidence_items": evidence,
        "conflicts": conflicts,
        "open_questions": [questions[key] for key in sorted(questions)],
        "retrievals": retrievals,
        "canonical_refs": [refs[key] for key in sorted(refs)],
        "manufacturer_guidance_boundary": {
            "allowed_claim_role": "EVIDENCE_REPORT",
            "fibreseek_guidance_requires": ["FACT", "FIBRESEEK_FIRST_PARTY", "explicit manufacturer guidance"],
            "lineage_is_not": ["manufacturer recommendation", "physical equivalence", "runtime equivalence"],
            "historical_is_not": "current FibreSeek guidance",
            "unresolved_is_not": "permission to choose a value",
        },
        "operating_guidance_prohibited": True,
        "forbidden_conclusion_types": plan["forbidden_conclusion_types"],
        "assumptions": plan["assumptions"],
        "warnings": sorted(warnings),
    }
    packet_id = f"packet:{stable_hash(base)}"
    packet_without_metrics = {"packet_version": PACKET_VERSION, "packet_id": packet_id, **{key: value for key, value in base.items() if key != "packet_version"}}
    byte_count = len(canonical_json(packet_without_metrics).encode("utf-8"))
    packet = {
        **packet_without_metrics,
        "metrics": {
            "payload_bytes_excluding_metrics": byte_count,
            "token_proxy_excluding_metrics": (byte_count + 3) // 4,
        },
    }
    validate_context_packet(packet)
    return packet


def golden_candidate(packet: dict[str, Any]) -> dict[str, Any]:
    """Create a lossless structured reference answer; no prose synthesis is needed."""
    validate_context_packet(packet)
    assertions = []
    for item in packet["evidence_items"]:
        assertions.append(
            {
                "assertion_id": f"candidate:{stable_hash([packet['packet_id'], item['evidence_id']])}",
                "evidence_id": item["evidence_id"],
                "subject": item["subject"],
                "predicate": item["predicate"],
                "value": item["value"],
                "unit": item["unit"],
                "classification": item["classification"],
                "evidence_scope": item["evidence_scope"],
                "provenance_class": item["provenance_class"],
                "source_ids": item["source_ids"],
                "canonical_refs": item["canonical_refs"],
                "manufacturer_guidance": item["manufacturer_guidance"],
                "claim_role": "EVIDENCE_REPORT",
            }
        )
    candidate = {
        "candidate_version": CANDIDATE_VERSION,
        "plan_id": packet["plan_id"],
        "packet_id": packet["packet_id"],
        "evidence_mode": packet["evidence_mode"],
        "answer_status": packet["answer_status"],
        "assertions": assertions,
        "conflicts": copy.deepcopy(packet["conflicts"]),
        "open_question_ids": [item["question_id"] for item in packet["open_questions"]],
        "conclusions": [],
        "operating_recommendation": None,
    }
    validate_candidate(candidate)
    return candidate


def _violation(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def evaluate_candidate(packet: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Detect structured evidence laundering and missing safety boundaries."""
    validate_context_packet(packet)
    violations: list[dict[str, str]] = []
    try:
        validate_candidate(candidate)
    except ContractError as error:
        violations.append(_violation("MALFORMED_CANDIDATE", "$", str(error)))

    checks = [
        "contract_identity", "evidence_mode", "assertion_support", "classification_scope",
        "provenance", "canonical_reference", "open_questions", "conflicts",
        "operating_recommendation", "conclusion_roles", "answer_status",
    ]
    if violations:
        return _evaluation(packet, candidate, violations, checks)

    if candidate["packet_id"] != packet["packet_id"] or candidate["plan_id"] != packet["plan_id"]:
        violations.append(_violation("CONTRACT_IDENTITY_MISMATCH", "$", "Candidate does not identify the supplied plan and packet."))
    if candidate["evidence_mode"] != packet["evidence_mode"]:
        violations.append(_violation("EVIDENCE_MODE_VIOLATION", "$.evidence_mode", "Candidate evidence mode differs from the packet."))
    if candidate["answer_status"] != packet["answer_status"]:
        code = "CONFLICT_COLLAPSE" if packet["answer_status"] == "CONFLICTING" else "ANSWER_STATUS_MISMATCH"
        violations.append(_violation(code, "$.answer_status", "Candidate changed the packet answer status."))

    available = {item["evidence_id"]: item for item in packet["evidence_items"]}
    seen: set[str] = set()
    for index, assertion in enumerate(candidate["assertions"]):
        location = f"$.assertions[{index}]"
        evidence_id = assertion["evidence_id"]
        source = available.get(evidence_id)
        if source is None:
            violations.append(_violation("UNSUPPORTED_ASSERTION", location, "Assertion does not resolve to a packet evidence item."))
            continue
        seen.add(evidence_id)
        for key in ("subject", "predicate", "value", "unit"):
            if assertion[key] != source[key]:
                violations.append(_violation("UNSUPPORTED_ASSERTION", f"{location}.{key}", f"Candidate changed supported {key}."))
        if assertion["classification"] != source["classification"]:
            code = "UNSUPPORTED_PROMOTION" if source["classification"] in {"INFERENCE", "OPEN_QUESTION"} and assertion["classification"] == "FACT" else "CLASSIFICATION_MISMATCH"
            violations.append(_violation(code, f"{location}.classification", "Candidate changed the evidence classification."))
        if assertion["evidence_scope"] != source["evidence_scope"]:
            if source["evidence_scope"] == "HISTORICAL_ANISOPRINT" and assertion["evidence_scope"] == "FIBRESEEK_FIRST_PARTY":
                code = "HISTORICAL_TO_CURRENT_LEAKAGE"
            elif source["evidence_scope"] == "LINEAGE_INFERENCE" and assertion["evidence_scope"] == "FIBRESEEK_FIRST_PARTY":
                code = "UNSUPPORTED_PROMOTION"
            else:
                code = "EVIDENCE_SCOPE_MISMATCH"
            violations.append(_violation(code, f"{location}.evidence_scope", "Candidate changed the evidence scope."))
        if assertion["provenance_class"] != source["provenance_class"]:
            violations.append(_violation("MISSING_OR_CHANGED_PROVENANCE", f"{location}.provenance_class", "Candidate omitted or changed provenance."))
        if sorted(assertion["source_ids"]) != sorted(source["source_ids"]):
            violations.append(_violation("MISSING_OR_CHANGED_PROVENANCE", f"{location}.source_ids", "Candidate omitted or changed source IDs."))
        if assertion["manufacturer_guidance"] != source["manufacturer_guidance"]:
            violations.append(_violation("MANUFACTURER_BOUNDARY_MISMATCH", f"{location}.manufacturer_guidance", "Candidate changed the manufacturer-guidance boundary."))
        if source["canonical_reference_required"] and not assertion["canonical_refs"]:
            violations.append(_violation("MISSING_CANONICAL_REFERENCE", f"{location}.canonical_refs", "Consequential canonical evidence lost its reference."))
        elif canonical_json(assertion["canonical_refs"]) != canonical_json(source["canonical_refs"]):
            violations.append(_violation("CHANGED_CANONICAL_REFERENCE", f"{location}.canonical_refs", "Candidate changed canonical references."))
        if assertion["claim_role"] != "EVIDENCE_REPORT":
            if assertion["claim_role"] == "FIBRESEEK_GUIDANCE" and source["evidence_scope"] == "HISTORICAL_ANISOPRINT":
                code = "HISTORICAL_TO_CURRENT_LEAKAGE"
            elif assertion["claim_role"] == "FIBRESEEK_GUIDANCE" and source["classification"] != "FACT":
                code = "UNSUPPORTED_PROMOTION"
            else:
                code = "UNSUPPORTED_CONCLUSION_ROLE"
            violations.append(_violation(code, f"{location}.claim_role", "Packet permits evidence reporting only."))
        if packet["evidence_mode"] == "FIBRESEEK_CONFIRMED" and (
            assertion["evidence_scope"] in {"HISTORICAL_ANISOPRINT", "LINEAGE_INFERENCE"}
            or any(source_id.startswith("AP-") for source_id in assertion["source_ids"])
        ):
            violations.append(_violation("EVIDENCE_MODE_VIOLATION", location, "Confirmed mode contains historical or inferred evidence."))
        if packet["evidence_mode"] == "HISTORICAL" and assertion["evidence_scope"] == "FIBRESEEK_FIRST_PARTY":
            violations.append(_violation("EVIDENCE_MODE_VIOLATION", location, "Historical mode contains FibreSeek first-party evidence."))
        if assertion["classification"] in CLASS_SCOPE and assertion["evidence_scope"] not in CLASS_SCOPE[assertion["classification"]]:
            violations.append(_violation("CLASSIFICATION_SCOPE_MISMATCH", location, "Classification and evidence scope are incompatible."))

    for item in packet["evidence_items"]:
        if item["classification"] == "OPEN_QUESTION" and item["evidence_id"] not in seen:
            violations.append(_violation("OMITTED_UNRESOLVED_ASSERTION", "$.assertions", f"Unresolved assertion {item['evidence_id']} was omitted."))

    required_questions = {item["question_id"] for item in packet["open_questions"]}
    missing_questions = sorted(required_questions - set(candidate["open_question_ids"]))
    for question_id in missing_questions:
        violations.append(_violation("MISSING_OPEN_QUESTION", "$.open_question_ids", f"Required unresolved question {question_id} was omitted."))

    candidate_conflicts = {canonical_json(item) for item in candidate["conflicts"]}
    for conflict in packet["conflicts"]:
        if canonical_json(conflict) not in candidate_conflicts:
            violations.append(_violation("CONFLICT_COLLAPSE", "$.conflicts", "A packet conflict was omitted or changed."))

    if packet["operating_guidance_prohibited"] and candidate["operating_recommendation"] is not None:
        violations.append(_violation("UNSUPPORTED_OPERATING_RECOMMENDATION", "$.operating_recommendation", "This packet prohibits operating recommendations."))
    for index, conclusion in enumerate(candidate["conclusions"]):
        if conclusion["conclusion_type"] in packet["forbidden_conclusion_types"]:
            violations.append(_violation("PROHIBITED_CONCLUSION", f"$.conclusions[{index}]", f"Conclusion type {conclusion['conclusion_type']} is forbidden."))

    return _evaluation(packet, candidate, violations, checks)


def _evaluation(
    packet: dict[str, Any], candidate: dict[str, Any], violations: list[dict[str, str]], checks: list[str]
) -> dict[str, Any]:
    ordered = sorted(violations, key=lambda item: (item["code"], item["location"], item["message"]))
    return {
        "evaluation_version": EVALUATION_VERSION,
        "packet_id": packet["packet_id"],
        "candidate_digest": stable_hash(candidate),
        "passed": not ordered,
        "violation_count": len(ordered),
        "violations": ordered,
        "checks": checks,
    }


def _require(value: dict[str, Any], keys: set[str], name: str) -> None:
    missing = sorted(keys - set(value))
    extra = sorted(set(value) - keys)
    if missing or extra:
        raise ContractError(f"{name} keys mismatch; missing={missing}, extra={extra}")


def validate_query_plan(plan: dict[str, Any]) -> None:
    keys = {
        "plan_version", "plan_id", "original_question", "normalized_intent",
        "requested_evidence_mode", "evidence_mode", "mode_selection", "planner_status",
        "query_operations", "expected_answer_type", "relevant_open_question_domains",
        "required_open_question_ids", "operating_guidance_prohibited", "assumptions",
        "forbidden_conclusion_types",
    }
    _require(plan, keys, "query plan")
    if plan["plan_version"] != PLAN_VERSION or not re.fullmatch(r"plan:[0-9a-f]{64}", plan["plan_id"]):
        raise ContractError("invalid query plan version or ID")
    if plan["evidence_mode"] not in VIEW_MODES or plan["requested_evidence_mode"] not in (*VIEW_MODES, None):
        raise ContractError("invalid query plan evidence mode")
    if plan["planner_status"] not in {"MATCHED", "SAFE_FAILURE"}:
        raise ContractError("invalid planner status")
    if plan["operating_guidance_prohibited"] is not True:
        raise ContractError("query plans must prohibit operating guidance")
    orders = [item.get("order") for item in plan["query_operations"]]
    if orders != list(range(1, len(orders) + 1)):
        raise ContractError("query operation ordering is not deterministic and contiguous")


def validate_context_packet(packet: dict[str, Any]) -> None:
    keys = {
        "packet_version", "packet_id", "plan_id", "question", "normalized_intent",
        "evidence_mode", "planner_status", "expected_answer_type", "answer_status",
        "evidence_items", "conflicts", "open_questions", "retrievals", "canonical_refs",
        "manufacturer_guidance_boundary", "operating_guidance_prohibited",
        "forbidden_conclusion_types", "assumptions", "warnings", "metrics",
    }
    _require(packet, keys, "context packet")
    if packet["packet_version"] != PACKET_VERSION or not re.fullmatch(r"packet:[0-9a-f]{64}", packet["packet_id"]):
        raise ContractError("invalid context packet version or ID")
    if packet["evidence_mode"] not in VIEW_MODES or packet["answer_status"] not in {"SUPPORTED", "CONFLICTING", "UNRESOLVED", "NO_EVIDENCE"}:
        raise ContractError("invalid context packet mode or answer status")
    if packet["operating_guidance_prohibited"] is not True:
        raise ContractError("context packets must prohibit operating guidance")
    for index, item in enumerate(packet["evidence_items"]):
        required = {
            "evidence_id", "kind", "subject", "predicate", "value", "unit",
            "classification", "evidence_scope", "provenance_class", "source_ids",
            "manufacturer_guidance", "canonical_refs", "canonical_reference_required", "details",
        }
        _require(item, required, f"evidence item {index}")
        if item["classification"] not in CLASS_SCOPE or item["evidence_scope"] not in CLASS_SCOPE[item["classification"]]:
            raise ContractError(f"evidence item {index} classification/scope mismatch")


def validate_candidate(candidate: dict[str, Any]) -> None:
    keys = {
        "candidate_version", "plan_id", "packet_id", "evidence_mode", "answer_status",
        "assertions", "conflicts", "open_question_ids", "conclusions",
        "operating_recommendation",
    }
    _require(candidate, keys, "candidate")
    if candidate["candidate_version"] != CANDIDATE_VERSION:
        raise ContractError("invalid candidate version")
    if candidate["evidence_mode"] not in VIEW_MODES:
        raise ContractError("invalid candidate evidence mode")
    assertion_keys = {
        "assertion_id", "evidence_id", "subject", "predicate", "value", "unit",
        "classification", "evidence_scope", "provenance_class", "source_ids",
        "canonical_refs", "manufacturer_guidance", "claim_role",
    }
    for index, assertion in enumerate(candidate["assertions"]):
        _require(assertion, assertion_keys, f"candidate assertion {index}")


def load_benchmark_cases(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / "data/profiles/agent/benchmark_cases.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("benchmark_version") != "1.0.0" or not isinstance(value.get("cases"), list):
        raise ContractError("invalid benchmark fixture")
    return value["cases"]


def load_golden_expectations(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / "data/profiles/agent/golden_answers.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("golden_version") != "1.0.0" or not isinstance(value.get("answers"), list):
        raise ContractError("invalid golden fixture")
    return value["answers"]


def item_matches(item: dict[str, Any], pattern: dict[str, Any]) -> bool:
    return all(item.get(key) == value for key, value in pattern.items())


def validate_benchmark_case(case: dict[str, Any]) -> None:
    required = {
        "case_id", "family", "question", "acceptable_modes", "requested_mode",
        "expected_plan_status", "expected_operations", "may_appear", "must_not_appear",
        "required_open_questions", "expected_answer_status",
        "operating_guidance_prohibited", "prohibited_conclusion_types",
        "canonical_evidence_expectations", "adversarial", "pass_criteria",
    }
    missing = sorted(required - set(case))
    if missing:
        raise ContractError(f"benchmark case {case.get('case_id')} missing {missing}")
    if case["requested_mode"] not in case["acceptable_modes"]:
        raise ContractError(f"benchmark case {case['case_id']} requested mode is unacceptable")
    if case["operating_guidance_prohibited"] is not True:
        raise ContractError(f"benchmark case {case['case_id']} permits operating guidance")


def evaluate_benchmark_case(engine: QueryEngine, case: dict[str, Any]) -> dict[str, Any]:
    validate_benchmark_case(case)
    plan = plan_question(case["question"], case["requested_mode"])
    packet = build_context_packet(engine, plan)
    candidate = golden_candidate(packet)
    evaluation = evaluate_candidate(packet, candidate)
    errors = []
    if plan["normalized_intent"]["family"] != case["family"]:
        errors.append("planner family mismatch")
    if plan["planner_status"] != case["expected_plan_status"]:
        errors.append("planner status mismatch")
    if [item["operation"] for item in plan["query_operations"]] != case["expected_operations"]:
        errors.append("planned operations mismatch")
    if packet["evidence_mode"] not in case["acceptable_modes"]:
        errors.append("unacceptable evidence mode")
    if packet["answer_status"] != case["expected_answer_status"]:
        errors.append(f"answer status mismatch: {packet['answer_status']}")
    question_ids = {item["question_id"] for item in packet["open_questions"]}
    if not set(case["required_open_questions"]).issubset(question_ids):
        errors.append("required open question missing")
    for pattern in case["canonical_evidence_expectations"]:
        if not any(item_matches(item, pattern) for item in packet["evidence_items"]):
            errors.append(f"canonical evidence expectation missing: {canonical_json(pattern)}")
    for pattern in case["must_not_appear"]:
        if any(item_matches(item, pattern) for item in packet["evidence_items"]):
            errors.append(f"forbidden evidence appeared: {canonical_json(pattern)}")
    if not evaluation["passed"]:
        errors.append("structured golden candidate failed safety evaluation")
    return {
        "case_id": case["case_id"],
        "passed": not errors,
        "errors": errors,
        "plan_id": plan["plan_id"],
        "packet_id": packet["packet_id"],
        "packet_bytes": packet["metrics"]["payload_bytes_excluding_metrics"],
        "token_proxy": packet["metrics"]["token_proxy_excluding_metrics"],
    }
