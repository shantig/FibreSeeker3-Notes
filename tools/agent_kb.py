#!/usr/bin/env python3
"""CLI for Phase 2C deterministic planning, packets, and safety evaluation."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from agent_consumption import (
    build_context_packet,
    evaluate_benchmark_case,
    evaluate_candidate,
    golden_candidate,
    load_benchmark_cases,
    plan_question,
)
from query_engine import VIEW_MODES, QueryEngine, canonical_json, ensure_index, pretty_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build evidence-safe model-neutral agent inputs from Phase 2B queries."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    parser.add_argument("--view-mode", choices=VIEW_MODES)
    parser.add_argument("--format", choices=("json", "compact"), default="json")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("plan", "Create a deterministic Phase 2B query plan."),
        ("packet", "Execute a plan and build a compact context packet."),
        ("golden", "Build the safe structured reference answer for a packet."),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("question")

    evaluate = sub.add_parser("evaluate", help="Evaluate a candidate structured answer JSON file.")
    evaluate.add_argument("question")
    evaluate.add_argument("candidate", type=Path)

    benchmark = sub.add_parser("benchmark", help="Run benchmark cases and measure local overhead.")
    benchmark.add_argument("--iterations", type=int, default=3)
    benchmark.add_argument("--case-id")
    return parser.parse_args()


def _timed(callback: Any, iterations: int) -> dict[str, float | int]:
    samples = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        callback()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    ordered = sorted(samples)
    return {
        "iterations": iterations,
        "min_ms": round(ordered[0], 3),
        "median_ms": round(statistics.median(ordered), 3),
        "max_ms": round(ordered[-1], 3),
    }


def benchmark(engine: QueryEngine, repo_root: Path, iterations: int, case_id: str | None) -> dict[str, Any]:
    if iterations < 1:
        raise SystemExit("--iterations must be positive")
    cases = load_benchmark_cases(repo_root)
    if case_id:
        cases = [case for case in cases if case["case_id"] == case_id]
        if not cases:
            raise SystemExit(f"unknown benchmark case: {case_id}")
    results = [evaluate_benchmark_case(engine, case) for case in cases]
    representative = cases[0]
    mode = representative["requested_mode"]
    question = representative["question"]
    plan = plan_question(question, mode)
    packet = build_context_packet(engine, plan)
    timings = {
        "planner": _timed(lambda: plan_question(question, mode), iterations),
        "packet": _timed(lambda: build_context_packet(engine, plan), iterations),
        "direct_phase2b": _timed(
            lambda: engine.answer_unit("LinearDensity", mode)
            if plan["normalized_intent"]["family"] == "linear_density"
            else build_context_packet(engine, plan),
            iterations,
        ),
    }
    suite_started = time.perf_counter_ns()
    for case in cases:
        evaluate_benchmark_case(engine, case)
    suite_ms = (time.perf_counter_ns() - suite_started) / 1_000_000
    sizes = [item["packet_bytes"] for item in results]
    return {
        "benchmark_version": "1.0.0",
        "case_count": len(cases),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "suite_runtime_ms": round(suite_ms, 3),
        "timings": timings,
        "packet_sizes": {
            "min_bytes": min(sizes),
            "median_bytes": round(statistics.median(sizes)),
            "max_bytes": max(sizes),
            "representative_bytes": packet["metrics"]["payload_bytes_excluding_metrics"],
            "representative_token_proxy": packet["metrics"]["token_proxy_excluding_metrics"],
        },
        "results": results,
    }


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    db_path = (args.db or repo_root / ".cache/fibreseeker-query.sqlite3").resolve()

    if args.command == "plan":
        value = plan_question(args.question, args.view_mode)
    else:
        ensure_index(repo_root, db_path)
        engine = QueryEngine(repo_root, db_path)
        try:
            if args.command == "benchmark":
                value = benchmark(engine, repo_root, args.iterations, args.case_id)
            else:
                plan = plan_question(args.question, args.view_mode)
                packet = build_context_packet(engine, plan)
                if args.command == "packet":
                    value = packet
                elif args.command == "golden":
                    value = golden_candidate(packet)
                elif args.command == "evaluate":
                    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
                    value = evaluate_candidate(packet, candidate)
                else:
                    raise AssertionError(args.command)
        finally:
            engine.close()

    if args.format == "compact":
        print(canonical_json(value))
    else:
        print(pretty_json(value), end="")


if __name__ == "__main__":
    main()
