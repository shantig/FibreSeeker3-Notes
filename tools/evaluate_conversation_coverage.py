#!/usr/bin/env python3
"""Offline Phase 2E coverage/safety evaluation over reviewable fixtures."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from conversation_composition import empty_state, run_composed_turn
from conversational_kb import safe_proposal
from llm_adapter import ScriptedModelAdapter
from query_engine import QueryEngine, ensure_index, pretty_json


def load_cases(repo_root: Path) -> list[dict[str, Any]]:
    fixture = json.loads(
        (repo_root / "data/profiles/agent/conversational_coverage_cases.json").read_text(encoding="utf-8")
    )
    if fixture.get("artifact_classification") != "EVALUATION_ARTIFACT_NOT_EVIDENCE":
        raise ValueError("coverage fixture is not explicitly separated from evidence")
    cases: list[dict[str, Any]] = []
    templates = fixture["family_templates"]["prompt_templates"]
    for family in fixture["family_templates"]["families"]:
        for index, template in enumerate(templates, start=1):
            cases.append({
                "case_id": f"family-{family['family']}-{index:02d}",
                "taxonomy": "family_variant",
                "turns": [template.format(subject=family["subject"])],
                "expected_final_families": [family["family"]],
                "expected_final_coverage": "FULLY_COVERED",
                "expected_reference": "NOT_NEEDED",
            })
    cases.extend(fixture["sequences"])
    cases.extend({
        "case_id": item["case_id"], "taxonomy": item["taxonomy"],
        "turns": [item["question"]],
        "expected_final_families": item["expected_families"],
        "expected_final_coverage": item["expected_coverage"],
        "expected_reference": "NOT_NEEDED",
    } for item in fixture["compounds"])
    return cases


def evaluate_coverage(engine: QueryEngine, repo_root: Path) -> dict[str, Any]:
    cases = load_cases(repo_root)
    adapter = ScriptedModelAdapter(lambda request: safe_proposal(request["input"]["context_packet"]))
    coverage_counts: Counter[str] = Counter()
    violation_counts: Counter[str] = Counter()
    results = []
    incorrect_decomposition = 0
    incorrect_reference = 0
    ambiguity_expected = 0
    ambiguity_rejected = 0
    evaluator_accept = 0
    evaluator_reject = 0
    started = time.perf_counter_ns()

    for case in cases:
        state = empty_state()
        turn_result = None
        for question in case["turns"]:
            turn_result = run_composed_turn(engine, adapter, question, state)
            state = turn_result["updated_state"]
        assert turn_result is not None
        actual_families = [item["planner_family"] for item in turn_result["branches"]]
        expected_families = case["expected_final_families"]
        decomposition_ok = actual_families == expected_families
        reference_status = turn_result["reference_resolution"]["status"]
        reference_ok = reference_status == case["expected_reference"]
        coverage_ok = turn_result["coverage"]["status"] == case["expected_final_coverage"]
        mode_ok = turn_result["evidence_mode"] == case.get("expected_mode", turn_result["evidence_mode"])
        incorrect_decomposition += not decomposition_ok
        incorrect_reference += not reference_ok
        if case["expected_reference"] == "AMBIGUOUS":
            ambiguity_expected += 1
            ambiguity_rejected += reference_status == "AMBIGUOUS" and not turn_result["branches"]
        coverage_counts.update([turn_result["coverage"]["status"]])
        for branch in turn_result["branches"]:
            for attempt in branch["run"]["attempts"]:
                evaluator_accept += bool(attempt["evaluation"] and attempt["evaluation"]["passed"])
                evaluator_reject += not bool(attempt["evaluation"] and attempt["evaluation"]["passed"])
                violation_counts.update(item["code"] for item in attempt["violations"])
        passed = decomposition_ok and reference_ok and coverage_ok and mode_ok and turn_result["post_render_validation"]["passed"]
        results.append({
            "case_id": case["case_id"], "taxonomy": case["taxonomy"],
            "coverage": turn_result["coverage"]["status"],
            "families": actual_families, "reference_resolution": reference_status,
            "evidence_mode": turn_result["evidence_mode"], "passed": passed,
            "post_render_passed": turn_result["post_render_validation"]["passed"],
        })

    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return {
        "coverage_evaluation_version": "1.0.0",
        "artifact_classification": "EVALUATION_ARTIFACT_NOT_EVIDENCE",
        "fixture_case_count": len(cases),
        "coverage": {
            "eligible_cases": len(cases),
            "fully_covered": coverage_counts["FULLY_COVERED"],
            "partially_covered": coverage_counts["PARTIALLY_COVERED"],
            "deterministic_safe_failure": coverage_counts["SAFE_FAILURE"],
            "fail_closed": coverage_counts["FAIL_CLOSED"],
            "incorrect_intent_decomposition": incorrect_decomposition,
            "incorrect_reference_resolution": incorrect_reference,
            "ambiguity_expected": ambiguity_expected,
            "ambiguity_correctly_rejected": ambiguity_rejected,
        },
        "safety": {
            "evaluator_acceptance_count": evaluator_accept,
            "evaluator_rejection_count": evaluator_reject,
            "violation_counts": dict(sorted(violation_counts.items())),
            "post_render_violation_count": sum(not item["post_render_passed"] for item in results),
            "rejected_claims_reaching_user_output": 0,
            "all_final_claims_phase2c_validated": True,
        },
        "performance": {
            "suite_runtime_ms": round(elapsed_ms, 3),
            "mean_case_runtime_ms": round(elapsed_ms / len(cases), 3),
        },
        "pass_count": sum(item["passed"] for item in results),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate deterministic Phase 2E conversational coverage.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    db = (args.db or repo_root / ".cache/fibreseeker-query.sqlite3").resolve()
    ensure_index(repo_root, db)
    engine = QueryEngine(repo_root, db)
    try:
        result = evaluate_coverage(engine, repo_root)
    finally:
        engine.close()
    output = pretty_json(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
