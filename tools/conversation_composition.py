#!/usr/bin/env python3
"""Phase 2E deterministic conversational reference and intent composition.

Conversation state is planning metadata only. Every technical branch performs a
fresh Phase 2B/2C retrieval and the complete Phase 2D evaluation/render path.
"""

from __future__ import annotations

import copy
import re
import time
from typing import Any

from agent_consumption import DEFAULT_MODE, plan_question, stable_hash
from conversational_kb import deterministic_run_projection, run_conversation
from llm_adapter import ModelAdapter
from query_engine import QueryEngine, VIEW_MODES, canonical_json


STATE_VERSION = "1.0.0"
COMPOSITION_VERSION = "1.0.0"
COMPOSITE_RENDER_VERSION = "1.0.0"
POST_RENDER_VERSION = "1.0.0"


FAMILY_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("linear_density", (r"linear\s*densi(?:ty|tty)", r"\btex\b"), "What is the unit of LinearDensity?"),
    ("cutter_semantics", (r"cut\s*distance", r"cutdistance", r"cutter", r"fiber\s*restart\s*length", r"54\.8", r"cut\s*code"), "What is the cutter distance?"),
    ("macro_layer_height", (r"macro\s*layer\s*height", r"macrolayerheight"), "Trace MacroLayerHeight base and override history."),
    ("fiber_spool_length", (r"fiber\s*spool\s*length", r"fiberspoollength"), "What unit is FiberSpoolLength?"),
    ("ccf02", (r"\bccf02\b",), "What does CCF02 mean?"),
    ("infill_ftype", (r"infill\s*f\s*type", r"infillftype", r"tetragrid", r"isogrid", r"anisogrid", r"rhombic"), "What are the InfillFType enum semantics?"),
    ("enum_profilestatus", (r"profile\s*status", r"profilestatus"), "What are the ProfileStatus enum semantics?"),
    ("enum_profiletype", (r"profile\s*type", r"profiletype"), "What are the ProfileType enum semantics?"),
    ("enum_postprocessortype", (r"postprocessor\s*type", r"postprocessortype"), "What are the PostprocessorType enum semantics?"),
    ("enum_edition", (r"\bedition\b",), "What are the Edition enum semantics?"),
    ("enum_slottype", (r"universal[ -]*slot", r"slot\s*type", r"slottype"), "What are the universal-slot SlotType semantics?"),
    ("rocket_v13_v15", (r"(?:v?13|rocket[ -]*v?13).*(?:v?15|rocket[ -]*v?15)", r"(?:v?15|rocket[ -]*v?15).*(?:v?13|rocket[ -]*v?13)"), "What changed between Rocket v13 and Rocket v15?"),
    ("x_ccf_lineage", (r"x[ -]*ccf",), "Trace X-CCF exact UUID lineage."),
    ("seeker_lineage", (r"seeker\s*printer", r"printer\s*uuid"), "Trace the Seeker printer UUID lineage."),
)

MODE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("FIBRESEEK_CONFIRMED", (r"only (?:show )?fibreseek[ -]*confirmed evidence", r"fibreseek[ -]*confirmed (?:evidence )?only")),
    ("ALL_EVIDENCE", (r"include historical evidence too", r"\ball evidence\b")),
    ("HISTORICAL", (r"(?:only show|show only|use only) historical evidence", r"historical evidence only")),
    ("LINEAGE_AWARE", (r"go back to lineage[ -]*aware", r"use lineage[ -]*aware")),
)

SUBJECTLESS_PATTERNS = (
    r"^\s*(?:and\s+)?what about (?:rocket|aura|that|it)\?*\s*$",
    r"^\s*(?:and\s+)?(?:for )?(?:rocket|aura)\?*\s*$",
    r"^\s*and the other one\?*\s*$",
)

INTRA_INTENT_ATTRIBUTE_TOKENS = frozenset({
    "base", "classification", "confidence", "evidence", "field", "history",
    "mapping", "meaning", "override", "provenance", "semantics", "unit", "value",
})
INTRA_INTENT_FILLER_TOKENS = frozenset({
    "a", "about", "an", "are", "available", "can", "currently", "do", "does",
    "exist", "exists", "for", "give", "has", "have", "is", "kb", "known", "me",
    "of", "recorded", "report", "show", "tell", "the", "what", "which",
})


def _state_id(payload: dict[str, Any]) -> str:
    return f"conversation-state:{stable_hash(payload)}"


def empty_state(evidence_mode: str = DEFAULT_MODE) -> dict[str, Any]:
    if evidence_mode not in VIEW_MODES:
        raise ValueError(f"unknown evidence mode: {evidence_mode}")
    payload = {
        "state_version": STATE_VERSION,
        "evidence_mode": evidence_mode,
        "validated_turn_count": 0,
        "validated_turns": [],
        "active_referents": {"families": [], "fields": [], "identities": [], "versions": []},
        "trust_boundary": "PLANNING_METADATA_ONLY_NOT_EVIDENCE",
    }
    state = {"state_version": STATE_VERSION, "state_id": _state_id(payload), **{key: value for key, value in payload.items() if key != "state_version"}}
    validate_state(state)
    return state


def validate_state(state: dict[str, Any]) -> None:
    required = {
        "state_version", "state_id", "evidence_mode", "validated_turn_count",
        "validated_turns", "active_referents", "trust_boundary",
    }
    if not isinstance(state, dict) or set(state) != required:
        raise ValueError("conversation state does not match the versioned contract")
    if state["state_version"] != STATE_VERSION or state["evidence_mode"] not in VIEW_MODES:
        raise ValueError("invalid conversation state version or evidence mode")
    if state["trust_boundary"] != "PLANNING_METADATA_ONLY_NOT_EVIDENCE":
        raise ValueError("conversation state trust boundary changed")
    if state["validated_turn_count"] != len(state["validated_turns"]):
        raise ValueError("conversation state turn count mismatch")
    if set(state["active_referents"]) != {"families", "fields", "identities", "versions"}:
        raise ValueError("invalid active referents")
    turn_keys = {
        "turn_id", "turn_digest", "outcome", "evidence_mode",
        "normalized_intents", "plan_ids", "packet_ids", "candidate_digests",
    }
    intent_keys = {"intent", "family", "domain", "fields", "identities", "versions"}
    for turn in state["validated_turns"]:
        if not isinstance(turn, dict) or set(turn) != turn_keys:
            raise ValueError("conversation state turn contains non-planning fields")
        if turn["outcome"] not in {"VALIDATED", "MODE_TRANSITION"} or turn["evidence_mode"] not in VIEW_MODES:
            raise ValueError("invalid validated conversation turn")
        for intent in turn["normalized_intents"]:
            if not isinstance(intent, dict) or set(intent) != intent_keys:
                raise ValueError("conversation intent contains non-planning fields")
            if any(not isinstance(intent[key], list) for key in ("fields", "identities", "versions")):
                raise ValueError("conversation intent referents must be arrays")
    for values in state["active_referents"].values():
        if values != sorted(set(values)) or any(not isinstance(value, str) for value in values):
            raise ValueError("active referents must be sorted unique strings")
    payload = {key: copy.deepcopy(value) for key, value in state.items() if key != "state_id"}
    if state["state_id"] != _state_id(payload):
        raise ValueError("conversation state digest mismatch")


def _explicit_mode(question: str) -> str | None:
    normalized = question.casefold()
    matches = [mode for mode, patterns in MODE_RULES if any(re.search(pattern, normalized) for pattern in patterns)]
    return matches[0] if len(matches) == 1 else None


def _family_matches(question: str) -> list[dict[str, Any]]:
    normalized = question.casefold()
    found: list[dict[str, Any]] = []
    for priority, (family, patterns, canonical_question) in enumerate(FAMILY_RULES):
        positions = [match.start() for pattern in patterns if (match := re.search(pattern, normalized))]
        if positions:
            found.append({
                "family": family,
                "position": min(positions),
                "priority": priority,
                "canonical_question": canonical_question,
                "resolution": "EXPLICIT",
            })
    return sorted(found, key=lambda item: (item["position"], item["priority"], item["family"]))


def _meaningful_unmatched_clauses(question: str, matches: list[dict[str, Any]]) -> list[str]:
    if not matches:
        return []
    clauses = [item.strip(" ,?.") for item in re.split(r"\b(?:and|also|plus)\b|;", question, flags=re.IGNORECASE)]
    unmatched = []
    for clause in clauses:
        if len(clause.split()) < 2 or _family_matches(clause) or _explicit_mode(clause):
            continue
        tokens = set(re.findall(r"[a-z0-9]+", clause.casefold()))
        substantive = tokens - INTRA_INTENT_FILLER_TOKENS
        if substantive and substantive <= INTRA_INTENT_ATTRIBUTE_TOKENS:
            continue
        if re.search(r"\b(?:rocket[ -]*)?v?1[35]\b", clause.casefold()):
            continue
        if re.search(r"\b(?:what|which|meaning|unit|value|parameter|setting|mystery|unknown|execute|launch|run|test)\b", clause.casefold()):
            unmatched.append(clause)
    return unmatched


def decompose_question(question: str, state: dict[str, Any]) -> dict[str, Any]:
    """Return bounded intent branches; never interpret technical truth."""
    validate_state(state)
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be non-empty")
    mode_change = _explicit_mode(question)
    effective_mode = mode_change or state["evidence_mode"]
    matches = _family_matches(question)
    explicit_match_count = len(matches)
    correction = bool(re.search(r"^\s*(?:no[, ]+)?i meant\b", question, re.IGNORECASE))
    reference = {"status": "NOT_NEEDED", "source_state_id": None, "resolved_family": None}
    version_referents = [
        version for version in ("aura", "rocket")
        if re.search(rf"\b{version}\b", question.casefold())
    ]

    if not matches and any(re.match(pattern, question, re.IGNORECASE) for pattern in SUBJECTLESS_PATTERNS):
        families = state["active_referents"]["families"]
        if len(families) == 1:
            family = families[0]
            rule = next(item for item in FAMILY_RULES if item[0] == family)
            matches = [{
                "family": family, "position": 0, "priority": FAMILY_RULES.index(rule),
                "canonical_question": rule[2], "resolution": "STATE_UNIQUE_REFERENT",
            }]
            reference = {"status": "RESOLVED", "source_state_id": state["state_id"], "resolved_family": family}
        else:
            reference = {"status": "AMBIGUOUS", "source_state_id": state["state_id"], "resolved_family": None}

    branches = []
    for order, item in enumerate(matches, start=1):
        branches.append({
            "order": order,
            "family": item["family"],
            "canonical_question": item["canonical_question"],
            "resolution": "EXPLICIT_CORRECTION" if correction else item["resolution"],
            "evidence_mode": effective_mode,
            "version_referents": version_referents,
        })
    for clause in (_meaningful_unmatched_clauses(question, matches) if explicit_match_count else []):
        branches.append({
            "order": len(branches) + 1,
            "family": "unknown",
            "canonical_question": clause,
            "resolution": "UNSUPPORTED_CLAUSE",
            "evidence_mode": effective_mode,
            "version_referents": version_referents,
        })
    if not branches and reference["status"] != "AMBIGUOUS" and mode_change is None:
        branches = [{
            "order": 1, "family": "unknown", "canonical_question": question.strip(),
            "resolution": "NO_BOUNDED_MATCH", "evidence_mode": effective_mode,
            "version_referents": version_referents,
        }]
    return {
        "decomposition_version": "1.0.0",
        "question_digest": stable_hash(question.strip()),
        "effective_evidence_mode": effective_mode,
        "mode_transition": mode_change,
        "correction": correction,
        "reference_resolution": reference,
        "branches": branches,
    }


def _branch_record(engine: QueryEngine, adapter: ModelAdapter, spec: dict[str, Any], repair_limit: int) -> dict[str, Any]:
    intent = copy.deepcopy(plan_question(spec["canonical_question"], spec["evidence_mode"])["normalized_intent"])
    intent["versions"] = sorted(set(intent["versions"]) | set(spec["version_referents"]))
    run = run_conversation(
        engine, adapter, spec["canonical_question"], spec["evidence_mode"],
        max_repair_attempts=repair_limit,
    )
    outcome = (
        "FAIL_CLOSED" if run["final_status"] != "APPROVED"
        else "SAFE_FAILURE" if run["planner_status"] == "SAFE_FAILURE"
        else "APPROVED"
    )
    identity = {
        "order": spec["order"], "family": run["planner_family"],
        "plan_id": run["plan_id"], "packet_id": run["packet_id"],
    }
    return {
        "branch_id": f"branch:{stable_hash(identity)}",
        "order": spec["order"],
        "requested_family": spec["family"],
        "planner_family": run["planner_family"],
        "resolution": spec["resolution"],
        "evidence_mode": spec["evidence_mode"],
        "normalized_intent": intent,
        "outcome": outcome,
        "run": run,
    }


def _coverage(branches: list[dict[str, Any]], ambiguous: bool) -> dict[str, Any]:
    approved = sum(item["outcome"] == "APPROVED" for item in branches)
    safe = sum(item["outcome"] == "SAFE_FAILURE" for item in branches)
    failed = sum(item["outcome"] == "FAIL_CLOSED" for item in branches)
    if ambiguous or not branches or (approved == 0 and safe > 0):
        status = "SAFE_FAILURE"
    elif approved and (safe or failed):
        status = "PARTIALLY_COVERED"
    elif approved == len(branches):
        status = "FULLY_COVERED"
    else:
        status = "FAIL_CLOSED"
    return {
        "status": status, "branch_count": len(branches),
        "approved_branch_count": approved, "safe_failure_branch_count": safe,
        "fail_closed_branch_count": failed,
    }


def render_composition(branches: list[dict[str, Any]], coverage: dict[str, Any], *, mode_only: str | None = None) -> dict[str, Any]:
    if mode_only is not None:
        text = f"Evidence mode changed to {mode_only}. No technical claim was made."
        render_ids: list[str] = []
    elif not branches:
        text = "SAFE_FAILURE: the conversational reference is ambiguous; no technical referent was selected."
        render_ids = []
    else:
        render_ids = [item["run"]["rendered_answer"]["render_id"] for item in branches]
        text = "\n\n".join(
            f"Branch {item['order']} — {item['planner_family']} [{item['outcome']}]\n{item['run']['rendered_answer']['text']}"
            for item in branches
        )
    base = {
        "render_version": COMPOSITE_RENDER_VERSION,
        "coverage_status": "MODE_UPDATED" if mode_only is not None else coverage["status"],
        "branch_render_ids": render_ids,
        "text": text,
    }
    return {"render_version": COMPOSITE_RENDER_VERSION, "render_id": f"composition-render:{stable_hash(base)}", **{key: value for key, value in base.items() if key != "render_version"}}


def validate_composite_render(branches: list[dict[str, Any]], coverage: dict[str, Any], rendered: dict[str, Any], *, mode_only: str | None = None) -> dict[str, Any]:
    expected = render_composition(branches, coverage, mode_only=mode_only)
    violations = []
    for key in sorted(set(expected) | set(rendered)):
        if canonical_json(expected.get(key)) != canonical_json(rendered.get(key)):
            violations.append({
                "code": "COMPOSITE_RENDER_TAMPERING" if key == "text" else "COMPOSITE_RENDER_MANIFEST_MISMATCH",
                "location": f"$.{key}",
                "message": "Composite render differs from the exact deterministic branch projection.",
            })
    return {
        "post_render_version": POST_RENDER_VERSION,
        "passed": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "expected_digest": stable_hash(expected),
        "actual_digest": stable_hash(rendered),
    }


def _referents(branches: list[dict[str, Any]]) -> dict[str, list[str]]:
    intents = [item["normalized_intent"] for item in branches if item["outcome"] == "APPROVED"]
    return {
        "families": sorted({item["family"] for item in intents}),
        "fields": sorted({value for item in intents for value in item["fields"]}),
        "identities": sorted({value for item in intents for value in item["identities"]}),
        "versions": sorted({value for item in intents for value in item["versions"]}),
    }


def _advance_state(state: dict[str, Any], decomposition: dict[str, Any], branches: list[dict[str, Any]]) -> dict[str, Any]:
    approved = [item for item in branches if item["outcome"] == "APPROVED"]
    mode_only = decomposition["mode_transition"] is not None and not branches
    if not approved and not mode_only:
        return copy.deepcopy(state)
    referents = _referents(approved) if approved else copy.deepcopy(state["active_referents"])
    turn_base = {
        "turn_digest": stable_hash({
            "question_digest": decomposition["question_digest"],
            "mode": decomposition["effective_evidence_mode"],
            "branches": [item["branch_id"] for item in approved],
        }),
        "outcome": "MODE_TRANSITION" if mode_only else "VALIDATED",
        "evidence_mode": decomposition["effective_evidence_mode"],
        "normalized_intents": [
            copy.deepcopy(item["normalized_intent"]) for item in approved
        ],
        "plan_ids": [item["run"]["plan_id"] for item in approved],
        "packet_ids": [item["run"]["packet_id"] for item in approved],
        "candidate_digests": [stable_hash(item["run"]["final_candidate"]) for item in approved],
    }
    turn = {"turn_id": f"validated-turn:{stable_hash(turn_base)}", **turn_base}
    payload = {
        "state_version": STATE_VERSION,
        "evidence_mode": decomposition["effective_evidence_mode"],
        "validated_turn_count": state["validated_turn_count"] + 1,
        "validated_turns": [*copy.deepcopy(state["validated_turns"]), turn],
        "active_referents": referents,
        "trust_boundary": "PLANNING_METADATA_ONLY_NOT_EVIDENCE",
    }
    updated = {"state_version": STATE_VERSION, "state_id": _state_id(payload), **{key: value for key, value in payload.items() if key != "state_version"}}
    validate_state(updated)
    return updated


def run_composed_turn(
    engine: QueryEngine,
    adapter: ModelAdapter,
    question: str,
    state: dict[str, Any] | None = None,
    *,
    max_repair_attempts: int = 1,
) -> dict[str, Any]:
    """Run isolated Phase 2D branches and compose only their validated renders."""
    state = copy.deepcopy(state or empty_state())
    validate_state(state)
    started = time.perf_counter_ns()
    decomposition = decompose_question(question, state)
    ambiguous = decomposition["reference_resolution"]["status"] == "AMBIGUOUS"
    branches = [] if ambiguous else [
        _branch_record(engine, adapter, item, max_repair_attempts)
        for item in decomposition["branches"]
    ]
    coverage = _coverage(branches, ambiguous)
    mode_only = decomposition["mode_transition"] if decomposition["mode_transition"] and not branches else None
    rendered = render_composition(branches, coverage, mode_only=mode_only)
    post_render = validate_composite_render(branches, coverage, rendered, mode_only=mode_only)
    updated_state = _advance_state(state, decomposition, branches) if post_render["passed"] else state
    semantic = {
        "question_digest": decomposition["question_digest"],
        "prior_state_id": state["state_id"],
        "mode": decomposition["effective_evidence_mode"],
        "branch_ids": [item["branch_id"] for item in branches],
        "render_id": rendered["render_id"],
        "updated_state_id": updated_state["state_id"],
    }
    return {
        "composition_version": COMPOSITION_VERSION,
        "composition_id": f"composition:{stable_hash(semantic)}",
        "question": question.strip(),
        "question_digest": decomposition["question_digest"],
        "prior_state_id": state["state_id"],
        "evidence_mode": decomposition["effective_evidence_mode"],
        "mode_transition": decomposition["mode_transition"],
        "reference_resolution": decomposition["reference_resolution"],
        "branches": branches,
        "coverage": coverage,
        "rendered_answer": rendered,
        "post_render_validation": post_render,
        "updated_state": updated_state,
        "metrics": {
            "end_to_end_latency_ms": round((time.perf_counter_ns() - started) / 1_000_000, 3),
            "local_deterministic_overhead_ms": round(
                max(0.0, (time.perf_counter_ns() - started) / 1_000_000 - sum(
                    item["run"]["metrics"]["model_latency_ms"] for item in branches
                )), 3,
            ),
        },
    }


def deterministic_composition_projection(result: dict[str, Any]) -> dict[str, Any]:
    """Remove timing while preserving state, branch safety, and exact rendering."""
    return {
        key: copy.deepcopy(value)
        for key, value in result.items()
        if key not in {"branches", "metrics"}
    } | {
        "branches": [
            {**{key: copy.deepcopy(value) for key, value in item.items() if key != "run"},
             "run": deterministic_run_projection(item["run"])}
            for item in result["branches"]
        ]
    }
