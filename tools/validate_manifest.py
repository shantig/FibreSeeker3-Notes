#!/usr/bin/env python3

import argparse
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


TYPE_MAP = {
    "integer": int,
    "null": type(None),
    "object": dict,
    "string": str,
}


def parse_args():
    parser = argparse.ArgumentParser(description="Validate the FibreSeeker JSONL manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("schema", type=Path)
    return parser.parse_args()


def check_format(value, format_name):
    if value is None:
        return
    if format_name == "uri":
        parsed = urlsplit(value)
        if not parsed.scheme or (parsed.scheme in {"http", "https"} and not parsed.netloc):
            raise ValueError(f"invalid URI: {value}")
    elif format_name == "date-time":
        datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_property(name, value, definition):
    expected_names = definition.get("type")
    if expected_names:
        if isinstance(expected_names, str):
            expected_names = [expected_names]
        expected_types = tuple(TYPE_MAP[type_name] for type_name in expected_names)
        if not isinstance(value, expected_types) or (
            isinstance(value, bool) and "integer" in expected_names
        ):
            raise ValueError(f"{name}: unexpected type {type(value).__name__}")
    if "enum" in definition and value not in definition["enum"]:
        raise ValueError(f"{name}: value is not in enum")
    if isinstance(value, str):
        if len(value) < definition.get("minLength", 0):
            raise ValueError(f"{name}: string is too short")
        if "pattern" in definition and not re.fullmatch(definition["pattern"], value):
            raise ValueError(f"{name}: value does not match pattern")
        check_format(value, definition.get("format"))
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in definition and value < definition["minimum"]:
            raise ValueError(f"{name}: value is below minimum")
        if "maximum" in definition and value > definition["maximum"]:
            raise ValueError(f"{name}: value is above maximum")


def main():
    args = parse_args()
    schema = json.loads(args.schema.read_text())
    required = set(schema["required"])
    properties = schema["properties"]
    record_ids = set()
    records = []
    errors = []
    record_count = 0

    for line_number, line in enumerate(args.manifest.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        record_count += 1
        try:
            record = json.loads(line)
            missing = required - record.keys()
            extra = record.keys() - properties.keys()
            if missing:
                raise ValueError(f"missing fields: {sorted(missing)}")
            if schema.get("additionalProperties") is False and extra:
                raise ValueError(f"unexpected fields: {sorted(extra)}")
            for name, value in record.items():
                validate_property(name, value, properties[name])
            record_id = record["record_id"]
            if record_id in record_ids:
                raise ValueError(f"duplicate record_id: {record_id}")
            record_ids.add(record_id)
            records.append(record)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            errors.append(f"line {line_number}: {error}")

    for record in records:
        supersedes_id = record["supersedes_id"]
        if supersedes_id is not None and supersedes_id not in record_ids:
            errors.append(f"{record['record_id']}: unknown supersedes_id: {supersedes_id}")
        if supersedes_id == record["record_id"]:
            errors.append(f"{record['record_id']}: record cannot supersede itself")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"Validated {record_count} records; all IDs are unique.")


if __name__ == "__main__":
    main()
