#!/usr/bin/env python3
"""Controlled Phase 2E gpt-5.4 Codex Exec vs Responses comparison."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from conversation_composition import run_composed_turn
from conversational_kb import latency_summary
from llm_adapter import CodexExecAdapter, ModelAdapter, OpenAIResponsesAdapter
from query_engine import QueryEngine, ensure_index, pretty_json


PRIMARY_MODEL = "gpt-5.4"


def _adapter(name: str, model: str, timeout: int) -> ModelAdapter:
    if name == "codex-cli":
        return CodexExecAdapter(model, timeout_seconds=timeout)
    if name == "openai-responses":
        return OpenAIResponsesAdapter(model, timeout_seconds=timeout)
    raise ValueError(name)


def _evaluate_adapter(engine: QueryEngine, adapter: ModelAdapter, cases: list[dict[str, Any]], repair_limit: int) -> dict[str, Any]:
    results = []
    usage = {key: 0 for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")}
    model_latencies: list[float] = []
    end_to_end: list[float] = []
    local_overhead: list[float] = []
    violations: Counter[str] = Counter()
    semantic_requests = []
    for case in cases:
        result = run_composed_turn(
            engine, adapter, case["question"], max_repair_attempts=repair_limit
        )
        attempts = [attempt for branch in result["branches"] for attempt in branch["run"]["attempts"]]
        case_usage = {key: 0 for key in usage}
        for attempt in attempts:
            item_usage = attempt["model_result"]["usage"]
            for key in usage:
                usage[key] += item_usage.get(key) or 0
                case_usage[key] += item_usage.get(key) or 0
            model_latencies.append(attempt["model_result"]["latency_ms"])
            violations.update(item["code"] for item in attempt["violations"])
        end_to_end.append(result["metrics"]["end_to_end_latency_ms"])
        local_overhead.append(result["metrics"]["local_deterministic_overhead_ms"])
        first_attempts = [branch["run"]["attempts"][0] for branch in result["branches"]]
        final_valid = all(branch["outcome"] in {"APPROVED", "SAFE_FAILURE"} for branch in result["branches"])
        repair_attempted = any(len(branch["run"]["attempts"]) > 1 for branch in result["branches"])
        semantic = [{
            "family": branch["planner_family"], "plan_id": branch["run"]["plan_id"],
            "packet_id": branch["run"]["packet_id"], "evidence_mode": branch["evidence_mode"],
        } for branch in result["branches"]]
        semantic_requests.append({"case_id": case["case_id"], "branches": semantic})
        results.append({
            "case_id": case["case_id"], "category": case["category"],
            "branch_count": len(result["branches"]),
            "first_pass_schema_valid": bool(first_attempts) and all(
                item["model_result"]["parse_status"] == "PARSED" and item["model_result"]["validation_status"] == "VALID"
                for item in first_attempts
            ),
            "first_pass_phase2c_safe": bool(first_attempts) and all(item["passed"] for item in first_attempts),
            "repair_attempted": repair_attempted,
            "final_validated": final_valid and result["post_render_validation"]["passed"],
            "coverage": result["coverage"]["status"],
            "post_render_passed": result["post_render_validation"]["passed"],
            "model_latency_ms": round(sum(item["model_result"]["latency_ms"] for item in attempts), 3),
            "end_to_end_latency_ms": result["metrics"]["end_to_end_latency_ms"],
            "local_deterministic_overhead_ms": result["metrics"]["local_deterministic_overhead_ms"],
            "usage": case_usage,
            "violation_codes": sorted({item["code"] for attempt in attempts for item in attempt["violations"]}),
        })
    count = len(results)
    rate = lambda number: round(number / count, 6) if count else None  # noqa: E731
    return {
        "provider_id": adapter.info.provider_id,
        "adapter_id": adapter.info.adapter_id,
        "model_id": adapter.info.model_id,
        "case_count": count,
        "semantic_requests": semantic_requests,
        "reliability": {
            "first_pass_schema_valid_rate": rate(sum(item["first_pass_schema_valid"] for item in results)),
            "first_pass_phase2c_safety_rate": rate(sum(item["first_pass_phase2c_safe"] for item in results)),
            "repair_rate": rate(sum(item["repair_attempted"] for item in results)),
            "final_validated_answer_rate": rate(sum(item["final_validated"] for item in results)),
        },
        "safety_violation_counts": dict(sorted(violations.items())),
        "efficiency": {
            "model_latency": latency_summary(model_latencies),
            "end_to_end_latency": latency_summary(end_to_end),
            "local_deterministic_overhead": latency_summary(local_overhead),
            "usage": usage,
            "cost": None,
            "cost_note": "No billable cost is inferred from token metadata.",
        },
        "results": results,
    }


def run_comparison(engine: QueryEngine, repo_root: Path, adapters: list[ModelAdapter]) -> dict[str, Any]:
    fixture = json.loads((repo_root / "data/profiles/agent/adapter_comparison_cases.json").read_text(encoding="utf-8"))
    cases = fixture["cases"]
    results = [_evaluate_adapter(engine, adapter, cases, fixture["repair_limit"]) for adapter in adapters]
    request_sets_equal = len(results) < 2 or all(
        item["semantic_requests"] == results[0]["semantic_requests"] for item in results[1:]
    )
    return {
        "adapter_comparison_version": "1.0.0",
        "artifact_classification": "EVALUATION_ARTIFACT_NOT_EVIDENCE",
        "model_id": PRIMARY_MODEL,
        "store": False,
        "tools_enabled": False,
        "provider_conversation_state_used": False,
        "repair_limit": fixture["repair_limit"],
        "case_count": len(cases),
        "same_semantic_requests_verified": request_sets_equal,
        "adapters": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Phase 2E live adapters on the same gpt-5.4 requests.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    parser.add_argument("--adapter", choices=("codex-cli", "openai-responses", "both"), default="both")
    parser.add_argument("--model", default=PRIMARY_MODEL)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.model != PRIMARY_MODEL:
        raise SystemExit(f"Primary Phase 2E comparison requires exactly {PRIMARY_MODEL}.")
    names = ["codex-cli", "openai-responses"] if args.adapter == "both" else [args.adapter]
    repo_root = args.repo_root.resolve()
    db = (args.db or repo_root / ".cache/fibreseeker-query.sqlite3").resolve()
    ensure_index(repo_root, db)
    engine = QueryEngine(repo_root, db)
    try:
        result = run_comparison(engine, repo_root, [_adapter(name, args.model, args.timeout) for name in names])
    finally:
        engine.close()
    output = pretty_json(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
