#!/usr/bin/env python3
"""Generate the canonical FibreSeeker version chain and deterministic deltas."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from normalized_model import (
    SCHEMA_VERSION,
    alias_index,
    generate_branch_deltas,
    generate_foreign_key_relationships,
    generate_identity_links,
    generate_pair_deltas,
    load_json,
    load_manifest,
    normalize_source,
    output_file_hashes,
    unit_index,
    write_json,
    write_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--archive-root", type=Path, default=Path("<archive>/FibreSeeker-KB-Archive")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def generate(repo_root: Path, archive_root: Path, output_root: Path) -> None:
    normalized_root = repo_root / "data/profiles"
    config = load_json(normalized_root / "config/source_versions.json")
    aliases_registry = load_json(normalized_root / "registries/field_aliases.json")
    units_registry = load_json(normalized_root / "registries/unit_registry.json")
    manifest = load_manifest(repo_root / "sources/manifest.jsonl")
    aliases = alias_index(aliases_registry)
    units = unit_index(units_registry)

    version_records = {}
    source_outputs = []
    for definition in config["sources"]:
        source, records = normalize_source(
            definition, archive_root, config, manifest, aliases, units
        )
        source_outputs.append(source)
        version_records[source["source_version_id"]] = records
        write_jsonl(
            output_root / "versions" / source["source_version_id"] / "entities.jsonl",
            records,
        )

    links = generate_identity_links(version_records, config["comparison_pairs"])
    relationships = generate_foreign_key_relationships(version_records)
    write_jsonl(output_root / "identity/identity_links.jsonl", links)
    write_jsonl(output_root / "identity/foreign_key_relationships.jsonl", relationships)

    delta_counts = {}
    for from_version, to_version in config["comparison_pairs"]:
        deltas = generate_pair_deltas(version_records, from_version, to_version)
        comparison_id = f"{from_version}__{to_version}"
        write_jsonl(output_root / "deltas" / f"{comparison_id}.jsonl", deltas)
        delta_counts[comparison_id] = len(deltas)
    branch_deltas = generate_branch_deltas(version_records, config["branch_comparison"])
    branch_id = config["branch_comparison"]["comparison_id"]
    write_jsonl(output_root / "deltas" / f"{branch_id}.jsonl", branch_deltas)
    delta_counts[branch_id] = len(branch_deltas)

    entity_counts = {version: len(records) for version, records in version_records.items()}
    field_counts = {
        version: sum(len(record["fields"]) for record in records)
        for version, records in version_records.items()
    }
    duplicate_counts = {
        version: sum(record["duplicate_in_source"] for record in records)
        for version, records in version_records.items()
    }
    direct_aura_rocket_links = sum(
        link["from_source_version"].startswith("aura-")
        and link["to_source_version"].startswith("rocket-")
        for link in links
    )
    classification_counts = Counter()
    for path in sorted((output_root / "deltas").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            for classification in json.loads(line)["classifications"]:
                classification_counts[classification] += 1

    write_json(output_root / "sources.json", source_outputs)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "entity_counts": entity_counts,
        "field_counts": field_counts,
        "duplicate_occurrence_counts": duplicate_counts,
        "identity_link_count": len(links),
        "direct_aura_to_rocket_identity_link_count": direct_aura_rocket_links,
        "foreign_key_relationship_count": len(relationships),
        "delta_counts": delta_counts,
        "delta_classification_counts": dict(sorted(classification_counts.items())),
        "total_entities": sum(entity_counts.values()),
        "total_fields": sum(field_counts.values()),
    }
    summary["file_sha256"] = output_file_hashes(output_root)
    write_json(output_root / "summary.json", summary)


def compare_directories(expected: Path, actual: Path) -> list[str]:
    expected_files = {
        str(path.relative_to(expected)): path for path in expected.rglob("*") if path.is_file()
    }
    actual_files = {
        str(path.relative_to(actual)): path for path in actual.rglob("*") if path.is_file()
    }
    differences = []
    for name in sorted(set(expected_files) | set(actual_files)):
        if name not in expected_files:
            differences.append(f"unexpected generated file: {name}")
        elif name not in actual_files:
            differences.append(f"missing generated file: {name}")
        elif expected_files[name].read_bytes() != actual_files[name].read_bytes():
            differences.append(f"generated content differs: {name}")
    return differences


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output or repo_root / "data/profiles/generated"
    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix="fibreseeker-normalized-") as temporary:
        temporary_output = Path(temporary) / "generated"
        generate(repo_root, args.archive_root.resolve(), temporary_output)
        if args.check:
            differences = compare_directories(temporary_output, output)
            if differences:
                raise SystemExit("\n".join(differences))
            print("Normalized output is deterministic and current.")
            return
        if output.exists():
            shutil.rmtree(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(temporary_output, output)
        print(f"Generated normalized knowledge layer at {output}")


if __name__ == "__main__":
    main()
