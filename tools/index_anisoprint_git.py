#!/usr/bin/env python3
"""Create a deterministic, static index for the two Phase 2F-A Git corpora."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


TARGETS = {
    "aura-docs": {
        "source_id": "AP-114",
        "expected_commit": "3fa58f9590b581a3df3da6cd4f1c4ba919599bc0",
        "repository_url": "https://github.com/anisoprint/aura-docs",
        "license": "CC-BY-4.0",
        "paths": [
            "LICENSE", "docs/aura/macrolayers/index.md", "docs/aura/entities/index.md",
            "docs/aura/supports/index.md", "docs/aura/layuprule/index.md",
            "docs/aura/premium/masks/index.md", "docs/aura/premium/cli/index.md",
            "package.json",
        ],
    },
    "MKA-firmware": {
        "source_id": "AP-115",
        "expected_commit": "6e02973b1b8f325040cc3dbf66ac545ffc5c06b3",
        "repository_url": "https://github.com/anisoprint/MKA-firmware",
        "license": "GPL-3.0-or-later",
        "paths": [
            "LICENSE", "GCodes.md", "src/core/commands/gcode/composer/m1001_m1002.h",
            "src/core/commands/gcode/composer/m1010_m1011.h",
            "src/core/commands/gcode/composer/m704.h", "src/core/tools/tools.cpp",
            "src/lcd/nextion_hmi/PrintPause.cpp",
            "config/COMPOSER_A4_I/Configuration_Core.h",
        ],
    },
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aura-docs", type=Path, required=True)
    parser.add_argument("--mka-firmware", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/operational/corpus/github_index.json"))
    args = parser.parse_args()
    repos = {"aura-docs": args.aura_docs, "MKA-firmware": args.mka_firmware}
    corpus = []
    for name, spec in TARGETS.items():
        repo = repos[name]
        commit = git(repo, "rev-parse", "HEAD")
        if commit != spec["expected_commit"]:
            raise SystemExit(f"{name}: expected {spec['expected_commit']}, got {commit}")
        files = []
        for rel in spec["paths"]:
            path = repo / rel
            if not path.is_file():
                raise SystemExit(f"{name}: missing indexed path {rel}")
            data = path.read_bytes()
            files.append({"path": rel, "byte_size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        corpus.append({
            "name": name, "source_id": spec["source_id"], "repository_url": spec["repository_url"],
            "indexed_ref": git(repo, "branch", "--show-current") or "detached",
            "commit_sha": commit, "commit_date": git(repo, "show", "-s", "--format=%cI", "HEAD"),
            "license": spec["license"], "inspection_mode": "STATIC_ONLY",
            "indexed_files": files,
        })
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": "1.0.0", "corpora": corpus}, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {sum(len(c['indexed_files']) for c in corpus)} files across {len(corpus)} immutable commits.")


if __name__ == "__main__":
    main()
