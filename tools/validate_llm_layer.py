#!/usr/bin/env python3
"""Validate Phase 2D offline orchestration, repair, rendering, and hygiene."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

from agent_consumption import build_context_packet, plan_question
from conversational_kb import (
    deterministic_run_projection,
    run_conversation,
    safe_proposal,
    validate_render,
)
from evaluate_live_agent import run_benchmark
from llm_adapter import ScriptedModelAdapter
from query_engine import QueryEngine, build_index, canonical_json, input_paths


def hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    schema_dir = repo_root / "data/profiles/schemas"
    for name in (
        "llm-candidate-proposal.schema.json", "llm-request.schema.json",
        "llm-model-result.schema.json", "llm-run.schema.json",
    ):
        try:
            schema = json.loads((schema_dir / name).read_text(encoding="utf-8"))
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"unexpected schema draft: {name}")
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid schema {name}: {error}")

    fixture_path = repo_root / "data/profiles/agent/conversational_cases.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("conversational_fixture_version") != "1.0.0":
        errors.append("invalid conversational fixture version")
    if len(fixture.get("cases", [])) < 12:
        errors.append("fewer than 12 conversational variants")
    live_path = repo_root / "data/profiles/agent/live_evaluation_results.json"
    try:
        live = json.loads(live_path.read_text(encoding="utf-8"))
        if live.get("artifact_classification") != "EVALUATION_ARTIFACT_NOT_EVIDENCE":
            errors.append("live artifact is not explicitly separated from evidence")
        if live.get("case_count") != 39 or live.get("adversarial_case_count") != 18:
            errors.append("live benchmark did not record all required cases")
        if live.get("reliability", {}).get("benchmark_pass_count") != 39:
            errors.append("live benchmark contains an unsuccessful final case")
        if live.get("safety", {}).get("post_render_violation_count") != 0:
            errors.append("live benchmark contains a post-render violation")
        serialized_live = canonical_json(live)
        for forbidden_key in ("raw_response", "provider_response_id", "api_key", "bearer"):
            if forbidden_key in serialized_live.casefold():
                errors.append(f"live artifact retained forbidden data: {forbidden_key}")
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid live evaluation artifact: {error}")

    before = hashes(input_paths(repo_root))
    started = time.perf_counter_ns()
    with tempfile.TemporaryDirectory(prefix="fibreseeker-phase2d-validation-") as directory:
        db = Path(directory) / "query.sqlite3"
        build_index(repo_root, db)
        engine = QueryEngine(repo_root, db)
        adapter_factory = lambda: ScriptedModelAdapter(  # noqa: E731
            lambda request: safe_proposal(request["input"]["context_packet"])
        )
        try:
            benchmark = run_benchmark(engine, repo_root, adapter_factory())
            if benchmark["case_count"] != 39 or benchmark["adversarial_case_count"] != 18:
                errors.append("Phase 2C benchmark count changed")
            if benchmark["reliability"]["benchmark_pass_count"] != 39:
                errors.append("offline Phase 2D benchmark did not pass all cases")
            if benchmark["safety"]["post_render_violation_count"]:
                errors.append("post-render validation failed for safe offline responses")

            for case in fixture["cases"]:
                plan = plan_question(case["question"], case["requested_mode"])
                if plan["planner_status"] != case["expected_plan_status"]:
                    errors.append(f"conversational planner mismatch: {case['case_id']}")
                run = run_conversation(
                    engine, adapter_factory(), case["question"], case["requested_mode"]
                )
                if run["final_status"] != "APPROVED" or not run["post_render_validation"]["passed"]:
                    errors.append(f"conversational safe flow failed: {case['case_id']}")

            packet = build_context_packet(
                engine, plan_question("What is the unit of LinearDensity?", "LINEAGE_AWARE")
            )
            unsafe = safe_proposal(packet)
            next(item for item in unsafe["assertions"] if item["classification"] == "INFERENCE")["classification"] = "FACT"
            repaired = run_conversation(
                engine, ScriptedModelAdapter([unsafe, safe_proposal(packet)]),
                packet["question"], packet["evidence_mode"],
            )
            if repaired["repair_status"] != "SUCCEEDED":
                errors.append("bounded inference-promotion repair failed")
            if "UNSUPPORTED_PROMOTION" not in {item["code"] for item in repaired["attempts"][0]["violations"]}:
                errors.append("inference promotion was not detected")

            malformed = run_conversation(
                engine, ScriptedModelAdapter(["invalid", "invalid"]),
                packet["question"], packet["evidence_mode"],
            )
            if malformed["final_status"] != "FAIL_CLOSED" or malformed["final_candidate"] is not None:
                errors.append("malformed output did not fail closed")

            safe_run = run_conversation(
                engine, adapter_factory(), packet["question"], packet["evidence_mode"]
            )
            tampered = copy.deepcopy(safe_run["rendered_answer"])
            tampered["text"] += " unsupported certainty"
            if validate_render(packet, safe_run["final_candidate"], tampered)["passed"]:
                errors.append("post-render validator accepted strengthened text")

            repeated = run_conversation(
                engine, adapter_factory(), packet["question"], packet["evidence_mode"]
            )
            if canonical_json(deterministic_run_projection(safe_run)) != canonical_json(deterministic_run_projection(repeated)):
                errors.append("deterministic Phase 2D projection changed across identical inputs")
        finally:
            engine.close()

    if hashes(input_paths(repo_root)) != before:
        errors.append("Phase 2D validation modified canonical or index inputs")
    tracked = subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "ls-files"], cwd=repo_root, text=True
    ).splitlines()
    if any(path.startswith(".cache/") or path.endswith(".sqlite3") or "__pycache__" in path for path in tracked):
        errors.append("generated cache/database is tracked")
    if errors:
        raise SystemExit("\n".join(errors))
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    print(
        f"Validated Phase 2D offline: 39 Phase 2C cases, 18 adversarial, "
        f"{len(fixture['cases'])} conversational variants; suite {elapsed_ms:.2f} ms."
    )


if __name__ == "__main__":
    main()
