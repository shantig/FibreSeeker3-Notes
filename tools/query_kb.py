#!/usr/bin/env python3
"""CLI for the Phase 2B evidence-safe FibreSeeker query layer."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any, Callable

from query_engine import (
    VIEW_MODES,
    QueryEngine,
    build_index,
    ensure_index,
    pretty_json,
    sha256_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query canonical FibreSeeker evidence without conflating fact, lineage, or open questions."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    parser.add_argument("--view-mode", choices=VIEW_MODES, default="LINEAGE_AWARE")
    parser.add_argument("--format", choices=("json", "compact", "text"), default="text")
    parser.add_argument("--rebuild-index", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    index = sub.add_parser("index", help="Build, rebuild, or inspect the disposable SQLite index.")
    index.add_argument("action", choices=("build", "rebuild", "status"), default="status", nargs="?")

    entity = sub.add_parser("entity", help="Show an entity across versions.")
    entity.add_argument("identity")
    entity.add_argument("--version")
    entity.add_argument("--field")
    entity.add_argument("--graph", action="store_true")

    lineage = sub.add_parser("lineage", help="Trace exact-UUID lineage.")
    lineage.add_argument("identity")

    field = sub.add_parser("field", help="Trace a field across versions.")
    field.add_argument("field_name")
    field.add_argument("--identity")
    field.add_argument("--version")
    field.add_argument("--entity-type")
    field.add_argument("--limit", type=int, default=500)

    delta = sub.add_parser("delta", help="Show changes between two source versions.")
    delta.add_argument("from_version")
    delta.add_argument("to_version")
    delta.add_argument("--identity")
    delta.add_argument("--entity-type")
    delta.add_argument("--field")
    delta.add_argument("--classification")
    delta.add_argument("--limit", type=int, default=1000)

    source = sub.add_parser("source", help="Resolve provenance/acquisition metadata for a source ID.")
    source.add_argument("source_id")

    questions = sub.add_parser("questions", help="List unresolved semantics and resolution boundaries.")
    questions.add_argument("--field")
    questions.add_argument("--entity-type")
    questions.add_argument("--domain")
    questions.add_argument(
        "--requirement",
        choices=("STATIC_FIRST_PARTY", "VENDOR_CONFIRMATION", "OFFLINE_RUNTIME_TEST", "HARDWARE_EXPERIMENT"),
    )

    enum = sub.add_parser("enum", help="Show version-aware enum mappings and confidence.")
    enum.add_argument("field_name")
    enum.add_argument("--software")
    enum.add_argument("--value")

    view = sub.add_parser("view", help="Show a high-value engineering projection.")
    view.add_argument("view_name", choices=("machine", "materials", "profiles", "lineage"))
    view.add_argument("--identity")
    view.add_argument("--version")
    view.add_argument("--name")
    view.add_argument("--limit", type=int, default=25)

    material = sub.add_parser("material", help="Inspect a material and its canonical relationship graph.")
    material.add_argument("identity")

    profile = sub.add_parser("profile", help="Inspect a profile and its canonical relationship graph.")
    profile.add_argument("identity")

    answer = sub.add_parser("answer", help="Produce a structured engineering answer object.")
    answer.add_argument("answer_type", choices=("unit", "cutter-distance", "field"))
    answer.add_argument("field_name", nargs="?")
    answer.add_argument("--identity")

    benchmark = sub.add_parser("benchmark", help="Measure representative local query latency.")
    benchmark.add_argument("--iterations", type=int, default=20)
    return parser.parse_args()


def text_output(value: dict[str, Any]) -> str:
    if "answer_version" in value:
        lines = [
            f"answer={value['answer_status']} view={value['view_mode']} assertions={len(value['assertions'])}"
        ]
        for item in value["assertions"]:
            lines.append(
                f"[{item['classification']}/{item['evidence_scope']}] "
                f"{item['subject']} {item['predicate']}={item['value']!r} "
                f"unit={item.get('unit')!r} sources={','.join(item['source_ids'])}"
            )
        for conflict in value["conflicts"]:
            lines.append(f"[CONFLICT] {json.dumps(conflict, ensure_ascii=False, sort_keys=True)}")
        for question in value["open_questions"]:
            lines.append(
                f"[OPEN_QUESTION] {question.get('question_id')}: {question.get('title')} "
                f"requires={question.get('resolution_requirement')}"
            )
        lines.extend(f"warning: {warning}" for warning in value.get("warnings", []))
        return "\n".join(lines) + "\n"

    if "contract_version" in value:
        lines = [
            f"operation={value['query']['operation']} view={value['view_mode']} results={value['result_count']}"
        ]
        for item in value["results"]:
            payload = item["payload"]
            label = (
                payload.get("name") or payload.get("title") or payload.get("question_id")
                or payload.get("field") or payload.get("canonical_entity_id") or item["kind"]
            )
            version = payload.get("version") or payload.get("source_version_id") or ""
            lines.append(
                f"[{item['classification']}/{item['evidence_scope']}] {item['kind']} "
                f"{label} {version} sources={','.join(item['source_ids'])}"
            )
            if item["kind"] in {"field_observation", "enum_assertion"}:
                lines.append(f"  {json.dumps(payload, ensure_ascii=False, sort_keys=True)}")
        lines.extend(f"warning: {warning}" for warning in value["warnings"])
        return "\n".join(lines) + "\n"
    return pretty_json(value)


def benchmark(engine: QueryEngine, iterations: int, mode: str) -> dict[str, Any]:
    cases: dict[str, Callable[[], Any]] = {
        "entity_seeker": lambda: engine.entity(
            "83bf1039-8c9e-49fc-928f-2f94a2008d40", mode=mode, compact=True
        ),
        "field_cut_distance": lambda: engine.field_history(
            "CutDistance", mode=mode,
            identity="f3904c6f-c24e-4aff-ad9a-70405cc4df84", compact=True,
        ),
        "delta_rocket_v13_v15": lambda: engine.deltas(
            "rocket-v13", "rocket-v15", mode=mode, entity_type="profile", limit=2000
        ),
        "open_questions": lambda: engine.questions(mode="ALL_EVIDENCE"),
        "materials_view": lambda: engine.engineering_view(
            "materials", mode=mode, version="rocket-v15", limit=100
        ),
    }
    results = {}
    for name, callback in cases.items():
        callback()
        samples = []
        for _ in range(iterations):
            started = time.perf_counter_ns()
            callback()
            samples.append((time.perf_counter_ns() - started) / 1_000_000)
        ordered = sorted(samples)
        results[name] = {
            "iterations": iterations,
            "min_ms": round(ordered[0], 3),
            "median_ms": round(statistics.median(ordered), 3),
            "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3),
        }
    return {"benchmark_version": "1.0.0", "view_mode": mode, "cases": results}


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    db_path = (args.db or repo_root / ".cache/fibreseeker-query.sqlite3").resolve()

    if args.command == "index":
        if args.action in {"build", "rebuild"}:
            value = build_index(repo_root, db_path)
        else:
            value = ensure_index(repo_root, db_path, rebuild=args.rebuild_index)
            value["database_path"] = str(db_path)
            value["database_sha256"] = sha256_file(db_path)
        print(json.dumps(value, ensure_ascii=False, sort_keys=True) if args.format == "compact" else pretty_json(value), end="")
        return

    ensure_index(repo_root, db_path, rebuild=args.rebuild_index)
    engine = QueryEngine(repo_root, db_path)
    compact = args.format == "compact"
    try:
        if args.command == "entity":
            value = engine.graph(args.identity, args.view_mode, compact=True) if args.graph else engine.entity(
                args.identity, args.view_mode, args.version, args.field, compact
            )
        elif args.command == "lineage":
            value = engine.lineage(args.identity, args.view_mode)
        elif args.command == "field":
            value = engine.field_history(
                args.field_name, args.view_mode, args.identity, args.version,
                args.entity_type, compact, args.limit,
            )
        elif args.command == "delta":
            value = engine.deltas(
                args.from_version, args.to_version, args.view_mode, args.identity,
                args.entity_type, args.field, args.classification, args.limit,
            )
        elif args.command == "source":
            value = engine.source(args.source_id, args.view_mode)
        elif args.command == "questions":
            value = engine.questions(
                args.view_mode, args.field, args.entity_type, args.domain, args.requirement
            )
        elif args.command == "enum":
            parsed_value: Any = args.value
            if args.value is not None:
                try:
                    parsed_value = json.loads(args.value)
                except json.JSONDecodeError:
                    pass
            value = engine.enum(args.field_name, args.view_mode, args.software, parsed_value)
        elif args.command == "view":
            value = engine.engineering_view(
                args.view_name, args.view_mode, args.identity, args.version, args.name, args.limit
            )
        elif args.command in {"material", "profile"}:
            value = engine.graph(
                args.identity,
                args.view_mode,
                compact=True,
                domain="materials" if args.command == "material" else "profiles",
            )
            value["query"]["operation"] = args.command
        elif args.command == "answer":
            if args.answer_type == "unit":
                if not args.field_name:
                    raise SystemExit("answer unit requires FIELD")
                value = engine.answer_unit(args.field_name, args.view_mode)
            elif args.answer_type == "cutter-distance":
                value = engine.answer_cutter(args.view_mode)
            else:
                if not args.field_name:
                    raise SystemExit("answer field requires FIELD")
                value = engine.answer_field(args.field_name, args.identity, args.view_mode)
        elif args.command == "benchmark":
            value = benchmark(engine, args.iterations, args.view_mode)
        else:
            raise AssertionError(args.command)
    finally:
        engine.close()

    if args.format == "compact":
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    elif args.format == "json":
        print(pretty_json(value), end="")
    else:
        print(text_output(value), end="")


if __name__ == "__main__":
    main()
