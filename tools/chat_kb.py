#!/usr/bin/env python3
"""Minimal local Phase 2D conversational harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from conversational_kb import run_conversation
from evaluate_live_agent import make_adapter
from query_engine import QueryEngine, VIEW_MODES, ensure_index, pretty_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask one evidence-bounded FibreSeeker-KB question.")
    parser.add_argument("question")
    parser.add_argument("--adapter", choices=("codex-cli", "openai-responses"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--view-mode", choices=VIEW_MODES)
    parser.add_argument("--repair-attempts", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    db_path = (args.db or repo_root / ".cache/fibreseeker-query.sqlite3").resolve()
    ensure_index(repo_root, db_path)
    engine = QueryEngine(repo_root, db_path)
    try:
        run = run_conversation(
            engine, make_adapter(args.adapter, args.model, args.timeout),
            args.question, args.view_mode, max_repair_attempts=args.repair_attempts,
        )
    finally:
        engine.close()
    if args.json:
        print(pretty_json(run), end="")
    else:
        print(run["rendered_answer"]["text"])


if __name__ == "__main__":
    main()
