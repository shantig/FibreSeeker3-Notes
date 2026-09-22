#!/usr/bin/env python3
"""Validate Phase 2C contracts, benchmark behavior, and safety invariants."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import time
from pathlib import Path

from agent_consumption import (
    build_context_packet,
    evaluate_benchmark_case,
    evaluate_candidate,
    golden_candidate,
    load_benchmark_cases,
    load_golden_expectations,
    plan_question,
    validate_context_packet,
    validate_query_plan,
)
from query_engine import QueryEngine, build_index, canonical_json, input_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    return parser.parse_args()


def hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    errors: list[str] = []
    schema_dir = repo_root / "data/profiles/schemas"
    for name in (
        "agent-query-plan.schema.json",
        "agent-context-packet.schema.json",
        "agent-candidate-answer.schema.json",
        "agent-safety-evaluation.schema.json",
    ):
        try:
            json.loads((schema_dir / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid schema {name}: {error}")

    cases = load_benchmark_cases(repo_root)
    if not 30 <= len(cases) <= 50:
        errors.append(f"benchmark count outside 30-50: {len(cases)}")
    if len({case["case_id"] for case in cases}) != len(cases):
        errors.append("benchmark case IDs are not unique")
    if sum(bool(case["adversarial"]) for case in cases) < 10:
        errors.append("benchmark has fewer than 10 adversarial cases")

    before = hashes(input_paths(repo_root))
    temporary = None
    if args.db:
        db_path = args.db.resolve()
    else:
        temporary = tempfile.TemporaryDirectory(prefix="fibreseeker-agent-validation-")
        db_path = Path(temporary.name) / "query.sqlite3"
        build_index(repo_root, db_path)
    engine = QueryEngine(repo_root, db_path)
    started = time.perf_counter_ns()
    results = []
    try:
        for case in cases:
            result = evaluate_benchmark_case(engine, case)
            results.append(result)
            if not result["passed"]:
                errors.append(f"benchmark {case['case_id']}: {result['errors']}")

        for fixture in load_golden_expectations(repo_root):
            plan = plan_question(fixture["question"], fixture["evidence_mode"])
            validate_query_plan(plan)
            packet = build_context_packet(engine, plan)
            validate_context_packet(packet)
            candidate = golden_candidate(packet)
            evaluation = evaluate_candidate(packet, candidate)
            if not evaluation["passed"]:
                errors.append(f"golden {fixture['golden_id']} failed evaluator")
            if packet["answer_status"] != fixture["answer_status"]:
                errors.append(f"golden {fixture['golden_id']} status mismatch")
            qids = {item["question_id"] for item in packet["open_questions"]}
            if not set(fixture["required_open_questions"]).issubset(qids):
                errors.append(f"golden {fixture['golden_id']} missing open question")
            if len(packet["conflicts"]) < fixture["minimum_conflicts"]:
                errors.append(f"golden {fixture['golden_id']} missing conflict")
            for pattern in fixture["required_assertions"]:
                if not any(all(item.get(key) == value for key, value in pattern.items()) for item in packet["evidence_items"]):
                    errors.append(f"golden {fixture['golden_id']} missing assertion {pattern}")

        linear_plan = plan_question("What is the unit of LinearDensity?", "LINEAGE_AWARE")
        linear_packet = build_context_packet(engine, linear_plan)
        safe = golden_candidate(linear_packet)

        promoted = copy.deepcopy(safe)
        inferred = next(item for item in promoted["assertions"] if item["classification"] == "INFERENCE")
        inferred["classification"] = "FACT"
        if "UNSUPPORTED_PROMOTION" not in {item["code"] for item in evaluate_candidate(linear_packet, promoted)["violations"]}:
            errors.append("evaluator missed inference-to-fact promotion")

        historical = copy.deepcopy(safe)
        aura = next(item for item in historical["assertions"] if item["evidence_scope"] == "HISTORICAL_ANISOPRINT")
        aura["claim_role"] = "FIBRESEEK_GUIDANCE"
        if "HISTORICAL_TO_CURRENT_LEAKAGE" not in {item["code"] for item in evaluate_candidate(linear_packet, historical)["violations"]}:
            errors.append("evaluator missed historical guidance leakage")

        cutter_packet = build_context_packet(
            engine, plan_question("Just give me the best cutter value.", "LINEAGE_AWARE")
        )
        cutter = golden_candidate(cutter_packet)
        cutter["conflicts"] = []
        cutter["answer_status"] = "SUPPORTED"
        cutter["operating_recommendation"] = {"field": "CutDistance", "value": 58, "unit": "mm"}
        cutter_codes = {item["code"] for item in evaluate_candidate(cutter_packet, cutter)["violations"]}
        if not {"CONFLICT_COLLAPSE", "UNSUPPORTED_OPERATING_RECOMMENDATION"}.issubset(cutter_codes):
            errors.append("evaluator missed cutter collapse/recommendation")

        spool_packet = build_context_packet(
            engine, plan_question("What unit is FiberSpoolLength?", "ALL_EVIDENCE")
        )
        spool = golden_candidate(spool_packet)
        spool["open_question_ids"] = []
        spool["assertions"] = [item for item in spool["assertions"] if item["classification"] != "OPEN_QUESTION"]
        spool_codes = {item["code"] for item in evaluate_candidate(spool_packet, spool)["violations"]}
        if not {"MISSING_OPEN_QUESTION", "OMITTED_UNRESOLVED_ASSERTION"}.issubset(spool_codes):
            errors.append("evaluator missed unresolved-unit omission")

        first_plan = plan_question("What is the unit of LinearDensity?", "LINEAGE_AWARE")
        second_plan = plan_question("What is the unit of LinearDensity?", "LINEAGE_AWARE")
        first_packet = build_context_packet(engine, first_plan)
        second_packet = build_context_packet(engine, second_plan)
        if canonical_json(first_plan) != canonical_json(second_plan):
            errors.append("planner output is not byte-deterministic")
        if canonical_json(first_packet) != canonical_json(second_packet):
            errors.append("packet output is not byte-deterministic")
    finally:
        engine.close()
        if temporary:
            temporary.cleanup()

    after = hashes(input_paths(repo_root))
    if before != after:
        errors.append("Phase 2C validation modified canonical/Phase 2B index inputs")

    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    if errors:
        raise SystemExit("\n".join(errors))
    sizes = [item["packet_bytes"] for item in results]
    print(
        f"Validated Phase 2C: {len(cases)} benchmark cases, "
        f"{sum(case['adversarial'] for case in cases)} adversarial, "
        f"{len(load_golden_expectations(repo_root))} structured goldens; "
        f"packets {min(sizes)}-{max(sizes)} bytes; suite {elapsed_ms:.2f} ms."
    )


if __name__ == "__main__":
    main()
