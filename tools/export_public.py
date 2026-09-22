#!/usr/bin/env python3
"""Generate the curated public copy of the knowledge base.

Copies git-tracked files that match an include glob and no deny glob (from
tools/public_export.json), applies the text redactions, strips JPEG metadata,
adds the public LICENSE files, and writes PUBLIC_EXPORT_MANIFEST.json. Fails
closed: any file too large, any JPEG that will not parse, or an empty result
aborts the export.

    python3 tools/export_public.py <out_dir> [--force]

The output directory must be empty or new unless --force is given. This never
writes inside the repository and never pushes anything.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = HERE / "public_export.json"

TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".jsonl", ".txt", ".cfg", ".ini",
                 ".gcode", ".csv", ".toml", ".yml", ".yaml"}
JPEG_SUFFIXES = {".jpg", ".jpeg"}

LICENSE_MIT = """MIT License

Copyright (c) 2026 FibreSeeker-KB contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

LICENSE_DOCS = """The documentation and data in this repository (everything except the code in
tools/) are licensed under the Creative Commons Attribution 4.0 International
License (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/

The code in tools/ is licensed under the MIT License; see LICENSE-CODE.

FibreSeeker 3, FibreSeek, Rocket, Anisoprint, Aura and Composer are the marks of
their respective owners. This is an independent, unofficial knowledge base.
Preserved third-party source material remains under its original rights and is
indexed, not redistributed, here.
"""


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def tracked_files(repo: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True,
                         text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def matches_any(path: str, globs: list[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(path, g):
            return True
        # support "dir/**" matching the tree under dir
        if g.endswith("/**") and (path == g[:-3] or path.startswith(g[:-2])):
            return True
    return False


def select_files(config: dict, files: list[str]) -> list[str]:
    include = config["include"]
    deny = config["deny"] + config.get("private_only_tests", [])
    exceptions = config.get("deny_exceptions", [])
    selected = []
    for f in files:
        if not matches_any(f, include):
            continue
        if matches_any(f, deny) and not matches_any(f, exceptions):
            continue
        selected.append(f)
    return sorted(selected)


PRIVATE_LITERALS = HERE / "private_redactions.json"


def compile_redactions(config: dict):
    rules = [(r["name"], re.compile(r["pattern"]), r["replacement"])
             for r in config.get("redactions", [])]
    # Real machine-identifying literals (serials etc.) live in a git-ignored
    # private file so they never enter a committed file; escape them literally.
    if PRIVATE_LITERALS.is_file():
        data = json.loads(PRIVATE_LITERALS.read_text(encoding="utf-8"))
        for item in data.get("literals", []):
            rules.append((item["name"], re.compile(re.escape(item["pattern"])),
                          item["replacement"]))
    return rules


def redact_text(text: str, redactions) -> tuple[str, dict]:
    counts = {}
    for name, rx, repl in redactions:
        text, n = rx.subn(repl, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--force", action="store_true",
                        help="allow writing into a non-empty output directory")
    args = parser.parse_args()

    config = load_config()
    redactions = compile_redactions(config)
    max_bytes = int(config.get("max_file_bytes", 20 * 1024 * 1024))
    strip_jpeg = config.get("strip_jpeg_metadata", True)
    if strip_jpeg:
        sys.path.insert(0, str(HERE))
        from jpeg_scrub import strip_jpeg_metadata, jpeg_metadata_markers

    out = args.out_dir.resolve()
    if REPO in out.parents or out == REPO:
        parser.error("output directory must be outside the repository")
    if out.exists() and any(out.iterdir()) and not args.force:
        parser.error(f"{out} is not empty (use --force)")
    out.mkdir(parents=True, exist_ok=True)

    selected = select_files(config, tracked_files(REPO))
    if not selected:
        parser.error("no files selected — refusing to write an empty export")

    manifest = {
        "generated_from_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
            text=True, check=True).stdout.strip(),
        "source_repo": "FibreSeeker-KB (private)",
        "file_count": 0,
        "redaction_totals": {},
        "jpeg_stripped": 0,
        "files": {},
    }
    errors = []

    for rel in selected:
        src = REPO / rel
        if not src.is_file():
            continue
        size = src.stat().st_size
        if size > max_bytes:
            errors.append(f"{rel}: {size} bytes exceeds max {max_bytes}")
            continue
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        suffix = src.suffix.lower()

        if suffix in JPEG_SUFFIXES and strip_jpeg:
            raw = src.read_bytes()
            try:
                scrubbed = strip_jpeg_metadata(raw)
                leftover = jpeg_metadata_markers(scrubbed)
            except ValueError as exc:
                errors.append(f"{rel}: JPEG parse failed ({exc})")
                continue
            if leftover:
                errors.append(f"{rel}: metadata remained after strip: {leftover}")
                continue
            dst.write_bytes(scrubbed)
            manifest["jpeg_stripped"] += 1
            digest = hashlib.sha256(scrubbed).hexdigest()
        elif suffix in TEXT_SUFFIXES:
            try:
                text = src.read_text(encoding="utf-8")
            except (UnicodeDecodeError, ValueError):
                dst.write_bytes(src.read_bytes())
                digest = hashlib.sha256(src.read_bytes()).hexdigest()
            else:
                redacted, counts = redact_text(text, redactions)
                for k, v in counts.items():
                    manifest["redaction_totals"][k] = manifest["redaction_totals"].get(k, 0) + v
                dst.write_text(redacted, encoding="utf-8")
                digest = hashlib.sha256(redacted.encode("utf-8")).hexdigest()
        else:
            dst.write_bytes(src.read_bytes())
            digest = hashlib.sha256(src.read_bytes()).hexdigest()

        shutil.copymode(src, dst)  # preserve exec bit on scripts
        manifest["files"][rel] = {"sha256": digest, "bytes": (out / rel).stat().st_size}

    (out / "LICENSE").write_text(LICENSE_DOCS, encoding="utf-8")
    (out / "LICENSE-CODE").write_text(LICENSE_MIT, encoding="utf-8")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print(f"\nExport aborted with {len(errors)} error(s); {out} is incomplete.",
              file=sys.stderr)
        return 1

    manifest["file_count"] = len(manifest["files"])
    (out / "PUBLIC_EXPORT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Exported {manifest['file_count']} files to {out}")
    print(f"  JPEGs stripped: {manifest['jpeg_stripped']}")
    print(f"  Redactions: {manifest['redaction_totals'] or 'none'}")
    print("Next: python3 tools/check_public_tree.py", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
