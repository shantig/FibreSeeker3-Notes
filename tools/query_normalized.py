#!/usr/bin/env python3
"""Query canonical entity/field history without a database server."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from normalized_model import load_jsonl, normalize_uuid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--field")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    normalized_uuid = normalize_uuid(args.uuid)
    if not normalized_uuid:
        raise SystemExit("--uuid must be a UUID")
    canonical_id = f"uuid:{normalized_uuid}"
    generated = args.repo_root.resolve() / "data/profiles/generated"
    history = []
    for path in sorted((generated / "versions").glob("*/entities.jsonl")):
        for record in load_jsonl(path):
            if record["canonical_entity_id"] != canonical_id:
                continue
            item = {
                "source_version_id": record["source_version_id"],
                "entity_type": record["entity_type"],
                "entity_record_id": record["entity_record_id"],
                "vendor_name": record["vendor_name"],
                "source_ids": record["source_ids"],
                "provenance_class": record["provenance_class"],
            }
            if args.field:
                if args.field not in record["fields"]:
                    continue
                item["field"] = record["fields"][args.field]
            else:
                item["fields"] = record["fields"]
            history.append(item)
    links = [
        link
        for link in load_jsonl(generated / "identity/identity_links.jsonl")
        if link["canonical_entity_id"] == canonical_id
    ]
    deltas = []
    for path in sorted((generated / "deltas").glob("*.jsonl")):
        deltas.extend(
            record
            for record in load_jsonl(path)
            if record["canonical_entity_id"] == canonical_id
            and (not args.field or record["field_name"] == args.field)
        )
    print(
        json.dumps(
            {"canonical_entity_id": canonical_id, "history": history, "links": links, "deltas": deltas},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
