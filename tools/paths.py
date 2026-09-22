#!/usr/bin/env python3
"""Repository layout constants and legacy-path resolution.

The repository directories were reorganized on 2026-09-22 (see
`sources/PATH_MIGRATION_2026-09-22.json`). The acquisition ledger
`sources/manifest.jsonl` is append-only: a record keeps the `local_path` that
was true when the source was acquired, and is never rewritten in place. Any
tool that opens a recorded path must therefore resolve it through
`resolve_recorded_path()` first.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Repository-relative layout constants.
DOCS = "docs"
NOTEBOOK = "notebook"
EXPERIMENTS = "experiments"
PROFILES = "data/profiles"
OPERATIONAL = "data/operational"
SOURCES = "sources"
MANIFEST = "sources/manifest.jsonl"
MANIFEST_SCHEMA = "sources/manifests/manifest.schema.json"
LOOM_SOURCES = "sources/loom"
FIRMWARE_PACKAGES = "sources/firmware-packages"
VENDOR_DOCS = "sources/vendor-docs"
PROJECT = "project"

MIGRATION_FILE = "sources/PATH_MIGRATION_2026-09-22.json"

# Pre-2026-09-22 prefix -> current prefix. Longest prefix wins.
_LEGACY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("_sources/loom", LOOM_SOURCES),
    ("_sources/firmware", "sources/firmware"),
    ("_sources", SOURCES),
    ("_tools", "tools"),
    ("01_FibreSeek/Firmware", "docs/firmware"),
    ("01_FibreSeek/Loom", "docs/loom"),
    ("01_FibreSeek/Technical", "docs/machine"),
    ("01_FibreSeek/Rocket", "docs/slicer"),
    ("01_FibreSeek/Manuals", f"{VENDOR_DOCS}/manuals"),
    ("01_FibreSeek", VENDOR_DOCS),
    ("02_Anisoprint_Legacy/Aura", "docs/slicer/aura"),
    ("05_Profiles/Normalized", PROFILES),
    ("06_Operational_Knowledge", OPERATIONAL),
    ("07_Troubleshooting/Loom/2026-09-12_P2_load_wait_insert", f"{NOTEBOOK}/2026-09-12_plastic2-load-failure"),
    ("07_Troubleshooting/Loom/2026-09-12_calibration_bed_leveling", f"{NOTEBOOK}/2026-09-12_calibration-and-bed-leveling"),
    ("07_Troubleshooting/Loom/2026-09-12_fibre_not_loaded_hmi", f"{NOTEBOOK}/2026-09-12_fibre-shown-not-loaded"),
    ("07_Troubleshooting/Loom/2026-09-14-T1", f"{NOTEBOOK}/2026-09-14_pla-temperature-tower"),
    ("07_Troubleshooting/Loom/2026-09-15-T1", f"{NOTEBOOK}/2026-09-15_pla-retraction-stringing"),
    ("07_Troubleshooting/Loom/2026-09-15-T2", f"{NOTEBOOK}/2026-09-15_pla-flow-pass-1"),
    ("07_Troubleshooting/Loom/2026-09-15-T3", f"{NOTEBOOK}/2026-09-15_pla-flow-pass-2"),
    ("07_Troubleshooting/Loom/2026-09-15-T4", f"{NOTEBOOK}/2026-09-15_benchy-X0008-plastic2"),
    ("07_Troubleshooting/Loom/2026-09-15-T5", f"{NOTEBOOK}/2026-09-15_pla-scraper-rebuild"),
    ("07_Troubleshooting/Loom/2026-09-15-T6", f"{NOTEBOOK}/2026-09-15_scraper-retraction-retest-X0010"),
    ("07_Troubleshooting/Loom/2026-09-15-T7", f"{NOTEBOOK}/2026-09-15_benchy-X0011-plastic1"),
    ("07_Troubleshooting/Loom/2026-09-16-T1", f"{NOTEBOOK}/2026-09-16_composite-hotend-heater-check"),
    ("07_Troubleshooting/Loom/2026-09-17-T1", f"{NOTEBOOK}/2026-09-17_calibration-before-after"),
    ("07_Troubleshooting/Loom", NOTEBOOK),
    ("09_Community", "docs/community"),
    ("10_Experiments", EXPERIMENTS),
    ("00_START_HERE", PROJECT),
)


def resolve_recorded_path(recorded: str | Path, repo_root: Path | None = None) -> Path:
    """Return the current location of a path recorded before the 2026-09-22 move.

    Absolute paths (NAS archive originals) are returned unchanged. Relative
    paths that already exist under `repo_root` are returned unchanged, so a
    record written after the move needs no mapping.
    """
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    text = str(recorded)
    path = Path(text)
    if path.is_absolute():
        return path
    if (root / path).exists():
        return root / path
    if path.suffix == ".fibrepack":
        # Firmware packages left 01_FibreSeek/Firmware for the source archive,
        # while the analysis documents moved to docs/firmware.
        return root / FIRMWARE_PACKAGES / path.name
    for old, new in sorted(_LEGACY_PREFIXES, key=lambda pair: -len(pair[0])):
        if text == old or text.startswith(old + "/"):
            return root / (new + text[len(old):])
    return root / path


def legacy_prefixes() -> dict[str, str]:
    """Expose the migration map, e.g. for writing or checking the migration file."""
    return dict(_LEGACY_PREFIXES)


def write_migration_file(repo_root: Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    target = root / MIGRATION_FILE
    payload = {
        "migrated": "2026-09-22",
        "note": (
            "Repository directory reorganization. Keys are pre-2026-09-22 "
            "repository-relative prefixes; values are the current ones. "
            "sources/manifest.jsonl keeps its original local_path values; "
            "tools resolve them through tools/paths.py."
        ),
        "prefixes": dict(_LEGACY_PREFIXES),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    print(write_migration_file())
