#!/usr/bin/env python3
"""Scan an exported public tree for anything that must not be published.

Fails closed (exit 1) on: LAN/private IPs, MAC addresses, the known device
serials, home/NAS filesystem paths, non-noreply email addresses, JPEG EXIF/XMP
metadata, oversized files, denied paths that slipped through, and broken
relative Markdown links.

    python3 tools/check_public_tree.py <dir>

With no <dir>, it exports to a temporary directory first and scans that, so it
can be run as a one-shot gate.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "public_export.json"

TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".jsonl", ".txt", ".cfg", ".ini",
                 ".gcode", ".csv", ".toml", ".yml", ".yaml", ".log"}

PATTERNS = {
    "lan_ipv4_192": re.compile(r"192\.168\.\d{1,3}\.\d{1,3}"),
    "private_ipv4_10": re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    "public_ipv6": re.compile(r"\b2[0-9a-fA-F]{3}:[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{0,4}){2,}\b"),
    "mac_address": re.compile(r"\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"),
    "home_path": re.compile(r"/Users/[A-Za-z0-9._-]+"),
    "nas_path": re.compile(r"/Volumes/[A-Za-z0-9 ._-]+"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}

# Real machine-identifying literals (serials etc.) that generic patterns can't
# catch live in a git-ignored private file so they never enter a committed file.
PRIVATE_LITERALS = HERE / "private_redactions.json"


def private_patterns() -> dict[str, "re.Pattern[str]"]:
    if not PRIVATE_LITERALS.is_file():
        return {}
    data = json.loads(PRIVATE_LITERALS.read_text(encoding="utf-8"))
    return {item["name"]: re.compile(re.escape(item["pattern"]))
            for item in data.get("literals", [])}
EMAIL_ALLOW = re.compile(r"@(users\.)?noreply\.github\.com$|@example\.(com|invalid|org)$")

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def rel_of(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def scan(root: Path, config: dict) -> list[str]:
    findings: list[str] = []
    deny = config["deny"] + config.get("private_only_tests", [])
    exceptions = config.get("deny_exceptions", [])
    max_bytes = int(config.get("max_file_bytes", 20 * 1024 * 1024))

    sys.path.insert(0, str(HERE))
    from jpeg_scrub import jpeg_metadata_markers

    patterns = {**PATTERNS, **private_patterns()}

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = rel_of(root, p)
        if rel in ("PUBLIC_EXPORT_MANIFEST.json", "LICENSE", "LICENSE-CODE"):
            continue

        # Denied path leaked through (ignore the license/manifest we just added).
        if matches_any(rel, deny) and not matches_any(rel, exceptions):
            findings.append(f"{rel}: denied path present in export")

        size = p.stat().st_size
        if size > max_bytes:
            findings.append(f"{rel}: {size} bytes exceeds max {max_bytes}")

        suffix = p.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            try:
                markers = jpeg_metadata_markers(p.read_bytes())
            except ValueError as exc:
                findings.append(f"{rel}: unreadable JPEG ({exc})")
            else:
                if markers:
                    findings.append(f"{rel}: JPEG metadata present {markers}")
            continue

        if suffix in TEXT_SUFFIXES:
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, ValueError):
                continue
            for name, rx in patterns.items():
                for m in rx.finditer(text):
                    if name == "email" and EMAIL_ALLOW.search(m.group(0)):
                        continue
                    line = text.count("\n", 0, m.start()) + 1
                    findings.append(f"{rel}:{line}: {name}: {m.group(0)!r}")
            if suffix == ".md":
                findings.extend(check_links(root, p, text))
    return findings


def check_links(root: Path, path: Path, text: str) -> list[str]:
    out = []
    for m in MD_LINK.finditer(text):
        target = m.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = target.split("#", 1)[0].split(" ", 1)[0]
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        if root.resolve() not in resolved.parents and resolved != root.resolve():
            # link points outside the exported tree
            out.append(f"{rel_of(root, path)}: link escapes export: {target}")
            continue
        if not resolved.exists():
            out.append(f"{rel_of(root, path)}: broken link: {target}")
    return out


def matches_any(path: str, globs: list[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(path, g):
            return True
        if g.endswith("/**") and (path == g[:-3] or path.startswith(g[:-2])):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dir", nargs="?", type=Path,
                        help="exported tree to scan (default: export to a temp dir first)")
    args = parser.parse_args()

    config = load_config()
    tmp = None
    if args.dir is None:
        import subprocess
        tmp = Path(tempfile.mkdtemp(prefix="fsk-public-"))
        rc = subprocess.run([sys.executable, str(HERE / "export_public.py"), str(tmp), "--force"])
        if rc.returncode != 0:
            print("export failed; cannot scan", file=sys.stderr)
            return 1
        target = tmp
    else:
        target = args.dir

    findings = scan(target, config)
    if findings:
        print(f"FAIL: {len(findings)} issue(s) in {target}:")
        for f in findings:
            print(f"  {f}")
        return 1
    print(f"OK: public tree at {target} is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
