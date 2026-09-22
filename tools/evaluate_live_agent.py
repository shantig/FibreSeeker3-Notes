#!/usr/bin/env python3
"""Run the Phase 2C benchmark through a live Phase 2D model adapter."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from agent_consumption import build_context_packet, load_benchmark_cases, plan_question
from conversational_kb import candidate_fidelity, latency_summary, run_conversation
from llm_adapter import CodexExecAdapter, ModelAdapter, OpenAIResponsesAdapter
from query_engine import QueryEngine, ensure_index, pretty_json


def make_adapter(name: str, model: str, timeout: int) -> ModelAdapter:
    if name == "codex-cli":
        return CodexExecAdapter(model, timeout_seconds=timeout)
    if name == "openai-responses":
        return OpenAIResponsesAdapter(model, timeout_seconds=timeout)
    raise ValueError(name)


def _sanitized_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
    result = attempt["model_result"]
    return {
        "attempt": attempt["attempt"],
        "purpose": attempt["purpose"],
        "request_id": attempt["request_id"],
        "raw_provider_status": result["raw_provider_status"],
        "parse_status": result["parse_status"],
        "validation_status": result["validation_status"],
        "tool_use_detected": result["tool_use_detected"],
        "latency_ms": result["latency_ms"],
        "usage": result["usage"],
        "proposal_digest": attempt["proposal_digest"],
        "candidate_digest": attempt["candidate_digest"],
        "evaluator_passed": bool(attempt["evaluation"] and attempt["evaluation"]["passed"]),
        "violation_codes": sorted({item["code"] for item in attempt["violations"]}),
    }


def run_benchmark(
    engine: QueryEngine,
    repo_root: Path,
    adapter: ModelAdapter,
    *,
    repair_attempts: int = 1,
    case_id: str | None = None,
) -> dict[str, Any]:
    cases = load_benchmark_cases(repo_root)
    if case_id:
        cases = [item for item in cases if item["case_id"] == case_id]
        if not cases:
            raise ValueError(f"unknown benchmark case: {case_id}")
    results = []
    violation_counts: Counter[str] = Counter()
    model_latencies: list[float] = []
    end_to_end_latencies: list[float] = []
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    for case in cases:
        run = run_conversation(
            engine, adapter, case["question"], case["requested_mode"],
            max_repair_attempts=repair_attempts,
        )
        packet = build_context_packet(
            engine, plan_question(case["question"], case["requested_mode"])
        )
        fidelity = candidate_fidelity(packet, run["final_candidate"], case)
        for attempt in run["attempts"]:
            violation_counts.update(item["code"] for item in attempt["violations"])
            model_latencies.append(attempt["model_result"]["latency_ms"])
        end_to_end_latencies.append(run["metrics"]["end_to_end_latency_ms"])
        for key in total_usage:
            total_usage[key] += run["metrics"]["usage"][key]
        results.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "adversarial": case["adversarial"],
                "plan_id": run["plan_id"],
                "planner_status": run["planner_status"],
                "packet_id": run["packet_id"],
                "packet_bytes": run["packet_bytes"],
                "attempts": [_sanitized_attempt(item) for item in run["attempts"]],
                "repair_status": run["repair_status"],
                "final_status": run["final_status"],
                "candidate_answer_status": (
                    run["final_candidate"]["answer_status"]
                    if run["final_candidate"] else None
                ),
                "candidate_assertion_count": (
                    len(run["final_candidate"]["assertions"])
                    if run["final_candidate"] else 0
                ),
                "fidelity": fidelity,
                "render_status": run["rendered_answer"]["answer_status"],
                "post_render_passed": run["post_render_validation"]["passed"],
                "end_to_end_latency_ms": run["metrics"]["end_to_end_latency_ms"],
                "benchmark_passed": run["final_status"] == "APPROVED" and fidelity["passed"],
            }
        )

    count = len(results)
    first_schema_valid = sum(
        item["attempts"][0]["parse_status"] == "PARSED"
        and item["attempts"][0]["validation_status"] == "VALID"
        for item in results
    )
    first_safety_pass = sum(item["attempts"][0]["evaluator_passed"] for item in results)
    repair_attempted = sum(len(item["attempts"]) > 1 for item in results)
    repaired_success = sum(
        len(item["attempts"]) > 1 and item["final_status"] == "APPROVED"
        for item in results
    )
    final_validated = sum(item["final_status"] == "APPROVED" for item in results)
    fail_closed = count - final_validated
    post_render_pass = sum(item["post_render_passed"] for item in results)
    fidelity_pass = sum(item["fidelity"]["passed"] for item in results)
    safe_failures = sum(item["planner_status"] == "SAFE_FAILURE" for item in results)

    def rate(numerator: int, denominator: int = count) -> float | None:
        return round(numerator / denominator, 6) if denominator else None

    return {
        "live_evaluation_version": "1.0.0",
        "artifact_classification": "EVALUATION_ARTIFACT_NOT_EVIDENCE",
        "provider_id": adapter.info.provider_id,
        "adapter_id": adapter.info.adapter_id,
        "model_id": adapter.info.model_id,
        "prompt_version": "1.0.0",
        "response_format_version": "evidence-selection-1.0.0",
        "case_count": count,
        "adversarial_case_count": sum(item["adversarial"] for item in results),
        "repair_limit": repair_attempts,
        "reliability": {
            "first_pass_schema_valid_count": first_schema_valid,
            "first_pass_schema_valid_rate": rate(first_schema_valid),
            "first_pass_safety_pass_count": first_safety_pass,
            "first_pass_safety_pass_rate": rate(first_safety_pass),
            "repair_attempted_count": repair_attempted,
            "repaired_success_count": repaired_success,
            "repair_success_rate_when_attempted": rate(repaired_success, repair_attempted),
            "final_validated_answer_count": final_validated,
            "final_validated_answer_rate": rate(final_validated),
            "final_fail_closed_count": fail_closed,
            "final_fail_closed_rate": rate(fail_closed),
            "benchmark_fidelity_pass_count": fidelity_pass,
            "benchmark_fidelity_pass_rate": rate(fidelity_pass),
            "benchmark_pass_count": sum(item["benchmark_passed"] for item in results),
        },
        "safety": {
            "violation_counts_across_attempts": dict(sorted(violation_counts.items())),
            "post_render_pass_count": post_render_pass,
            "post_render_violation_count": sum(not item["post_render_passed"] for item in results),
        },
        "fidelity": {
            "accepted_candidates_are_phase2c_evaluator_validated": True,
            "technical_values_materialized_from_packet_only": True,
            "provenance_source_ids_and_canonical_refs_are_copied_not_generated": True,
            "case_expectation_pass_count": fidelity_pass,
        },
        "planner": {
            "safe_failure_count": safe_failures,
            "safe_failure_rate": rate(safe_failures),
        },
        "efficiency": {
            "model_latency": latency_summary(model_latencies),
            "end_to_end_latency": latency_summary(end_to_end_latencies),
            "usage": total_usage,
            "approximate_cost": None,
            "cost_note": "Adapter/provider metadata did not expose a billable cost.",
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 2D live LLM benchmark.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    parser.add_argument("--adapter", choices=("codex-cli", "openai-responses"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--repair-attempts", type=int, default=1)
    parser.add_argument("--case-id")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    db_path = (args.db or repo_root / ".cache/fibreseeker-query.sqlite3").resolve()
    ensure_index(repo_root, db_path)
    engine = QueryEngine(repo_root, db_path)
    try:
        result = run_benchmark(
            engine, repo_root, make_adapter(args.adapter, args.model, args.timeout),
            repair_attempts=args.repair_attempts, case_id=args.case_id,
        )
    finally:
        engine.close()
    output = pretty_json(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
