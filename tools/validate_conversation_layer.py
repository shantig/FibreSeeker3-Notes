#!/usr/bin/env python3
"""Validate Phase 2E contracts, coverage, safety, determinism, and hygiene."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

from conversation_composition import deterministic_composition_projection, empty_state, run_composed_turn
from conversational_kb import safe_proposal
from evaluate_conversation_coverage import evaluate_coverage, load_cases
from llm_adapter import ScriptedModelAdapter
from query_engine import QueryEngine, build_index, canonical_json, input_paths


def _hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    before = _hashes(input_paths(repo_root))
    started = time.perf_counter_ns()
    for name in (
        "conversation-state.schema.json", "conversation-composition.schema.json",
        "llm-model-result-v2.schema.json",
    ):
        try:
            schema = json.loads((repo_root / "data/profiles/schemas" / name).read_text(encoding="utf-8"))
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"unexpected schema draft: {name}")
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid schema {name}: {error}")

    cases = load_cases(repo_root)
    if not 100 <= len(cases) <= 200:
        errors.append(f"coverage fixture count outside reviewable target: {len(cases)}")
    with tempfile.TemporaryDirectory(prefix="fibreseeker-phase2e-validation-") as directory:
        db = Path(directory) / "query.sqlite3"
        build_index(repo_root, db)
        engine = QueryEngine(repo_root, db)
        adapter = lambda: ScriptedModelAdapter(  # noqa: E731
            lambda request: safe_proposal(request["input"]["context_packet"])
        )
        try:
            coverage = evaluate_coverage(engine, repo_root)
            if coverage["pass_count"] != len(cases):
                errors.append("one or more Phase 2E coverage fixtures failed")
            if coverage["coverage"]["incorrect_intent_decomposition"]:
                errors.append("fixture evaluation found incorrect intent decomposition")
            if coverage["coverage"]["incorrect_reference_resolution"]:
                errors.append("fixture evaluation found incorrect reference resolution")
            if coverage["safety"]["post_render_violation_count"]:
                errors.append("fixture evaluation found post-render violations")
            first = run_composed_turn(engine, adapter(), "LinearDensity and CutDistance?", empty_state())
            second = run_composed_turn(engine, adapter(), "LinearDensity and CutDistance?", empty_state())
            if canonical_json(deterministic_composition_projection(first)) != canonical_json(deterministic_composition_projection(second)):
                errors.append("composed semantic output is not byte deterministic")
            failed = run_composed_turn(
                engine, ScriptedModelAdapter(["bad", "bad"]),
                "What unit is LinearDensity?", empty_state(),
            )
            if failed["updated_state"] != empty_state():
                errors.append("rejected turn became conversational authority")
        finally:
            engine.close()

    if _hashes(input_paths(repo_root)) != before:
        errors.append("Phase 2E validation modified canonical inputs")
    tracked = subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "ls-files"], cwd=repo_root, text=True
    ).splitlines()
    forbidden = [
        path for path in tracked
        if path.endswith(".sqlite3") or "__pycache__" in path or path.startswith(".cache/")
        or path.endswith(".credentials") or path.endswith(".env")
    ]
    if forbidden:
        errors.append(f"generated/credential artifacts tracked: {forbidden}")
    if errors:
        raise SystemExit("\n".join(errors))
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    print(
        f"Validated Phase 2E offline: {len(cases)} fixtures, {coverage['pass_count']} passed, "
        f"{coverage['coverage']['fully_covered']} full, "
        f"{coverage['coverage']['partially_covered']} partial, "
        f"{coverage['coverage']['deterministic_safe_failure']} safe failure; "
        f"suite {elapsed_ms:.2f} ms."
    )


if __name__ == "__main__":
    main()
