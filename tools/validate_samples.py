#!/usr/bin/env python3
"""Validate the physical sample registry (experiments/Samples/samples.jsonl)."""

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

REQUIRED = {
    "sample_id": str, "printed_date": str, "printer": str, "title": str,
    "material": str, "print_file": str, "print_file_sha256": str, "record": str,
    "pieces": list, "photos": list, "id_marking": str, "archive_status": str,
    "provenance_class": str, "notes": str,
}
ID_RE = re.compile(r"^X(\d{4})$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ID_MARKING = {"embossed-tag", "handwritten", "none"}
ARCHIVE_STATUS = {"archived", "unknown", "discarded"}


def fail(message):
    raise ValueError(message)


def validate(repo):
    path = repo / "experiments/Samples/samples.jsonl"
    lines = [(n, l) for n, l in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if l.strip()]
    if not lines:
        fail(f"{path}: no samples")
    for expected, (n, line) in enumerate(lines, start=1):
        where = f"samples.jsonl:{n}"
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as error:
            fail(f"{where}: {error}")
        for key, kind in REQUIRED.items():
            if not isinstance(rec.get(key), kind):
                fail(f"{where}: missing or mistyped field {key!r}")
        extra = set(rec) - set(REQUIRED)
        if extra:
            fail(f"{where}: unknown fields {sorted(extra)}")
        m = ID_RE.match(rec["sample_id"])
        if not m:
            fail(f"{where}: bad sample_id {rec['sample_id']!r}")
        if int(m.group(1)) != expected:
            fail(f"{where}: {rec['sample_id']} out of sequence; expected X{expected:04d}")
        where = f"{where} ({rec['sample_id']})"
        try:
            date.fromisoformat(rec["printed_date"])
        except ValueError:
            fail(f"{where}: printed_date must be YYYY-MM-DD")
        if rec["provenance_class"] != "EXPERIMENTAL":
            fail(f"{where}: provenance_class must be EXPERIMENTAL")
        if rec["id_marking"] not in ID_MARKING:
            fail(f"{where}: id_marking must be one of {sorted(ID_MARKING)}")
        if rec["archive_status"] not in ARCHIVE_STATUS:
            fail(f"{where}: archive_status must be one of {sorted(ARCHIVE_STATUS)}")
        if not rec["pieces"]:
            fail(f"{where}: at least one piece is required")
        labels = []
        for piece in rec["pieces"]:
            if not (isinstance(piece, dict) and set(piece) == {"label", "description"}
                    and all(isinstance(v, str) and v for v in piece.values())):
                fail(f"{where}: each piece needs non-empty label and description only")
            labels.append(piece["label"])
        if len(labels) != len(set(labels)):
            fail(f"{where}: duplicate piece labels")
        for key in ("print_file", "record"):
            target = (repo / rec[key]).resolve()
            if repo.resolve() not in target.parents or not target.is_file():
                fail(f"{where}: {key} {rec[key]!r} is not a file in the repository")
        if not SHA_RE.match(rec["print_file_sha256"]):
            fail(f"{where}: print_file_sha256 is not a lowercase SHA-256")
        digest = hashlib.sha256((repo / rec["print_file"]).read_bytes()).hexdigest()
        if digest != rec["print_file_sha256"]:
            fail(f"{where}: print_file SHA-256 mismatch")
    return len(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        count = validate(args.repo)
    except ValueError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"Validated {count} physical sample record(s).")


if __name__ == "__main__":
    main()
