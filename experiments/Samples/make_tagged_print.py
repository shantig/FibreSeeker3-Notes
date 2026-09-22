#!/usr/bin/env python3
"""Slice any model(s) for Loom with a printed sample-ID tag on the same plate.

1. `make_sample_tag.py` writes the tag STL for the sample ID.
2. `OrcaSlicer --export-3mf` combines the model(s) and the tag into one project.
3. The project settings are replaced with a reference project's resolved
   settings (e.g. `notebook/2026-09-14_pla-temperature-tower/loom_T1.3mf`) plus
   explicit `--set key=value` overrides for what changed since.
4. `OrcaSlicer --arrange 1 --slice 0` lays out and slices the plate.
5. Checks: the tag object is in the G-code, and every override appears in the
   G-code's config block with the requested value. Fails closed otherwise.

The reference-project route exists because OrcaSlicer's CLI will not load
user presets that do not inherit from a system preset ("process not compatible
with printer"). Compare the reference against the live presets before relying
on it.

Usage:
  make_tagged_print.py --sample-id X0008 --reference LOOM.3mf --out DIR --name NAME \
      [--set nozzle_temperature=205 --set filament_flow_ratio=0.96 ...] MODEL [MODEL ...]
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ORCA = "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer"
TAG_TOOL = Path(__file__).resolve().parent / "make_sample_tag.py"


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tempfile.gettempdir())
    if result.returncode != 0:
        sys.exit(f"command failed ({result.returncode}): {' '.join(map(str, cmd))}\n{result.stdout[-2000:]}{result.stderr[-2000:]}")
    return result


def apply_override(project, key, value):
    if key not in project:
        sys.exit(f"--set {key}: not a key in the reference project settings")
    current = project[key]
    project[key] = [value] * max(1, len(current)) if isinstance(current, list) else value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-id", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("models", nargs="+")
    a = ap.parse_args()

    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())
    tag = work / f"tag_{a.sample_id}.stl"
    run([sys.executable, str(TAG_TOOL), a.sample_id, str(tag)])

    exported = work / "export.3mf"
    run([ORCA, "--arrange", "1", "--export-3mf", str(exported),
         *[str(Path(m).resolve()) for m in a.models], str(tag)])

    with zipfile.ZipFile(a.reference) as ref:
        project = json.loads(ref.read("Metadata/project_settings.config"))
    overrides = {}
    for item in a.set:
        key, sep, value = item.partition("=")
        if not sep:
            sys.exit(f"--set needs KEY=VALUE, got {item!r}")
        apply_override(project, key, value)
        overrides[key] = value

    project_3mf = out / f"{a.name}.3mf"
    with zipfile.ZipFile(exported) as src, zipfile.ZipFile(project_3mf, "w", zipfile.ZIP_DEFLATED) as z:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "Metadata/project_settings.config":
                data = json.dumps(project, indent=1).encode()
            z.writestr(item, data)

    slice_dir = work / "slice"
    slice_dir.mkdir()
    run([ORCA, "--arrange", "1", "--slice", "0", "--outputdir", str(slice_dir), str(project_3mf)])
    gcode = out / f"{a.name}.gcode"
    (slice_dir / "plate_1.gcode").replace(gcode)

    text = gcode.read_text(encoding="utf-8", errors="replace")
    if f"; printing object tag_{a.sample_id}.stl" not in text:
        sys.exit(f"FAIL: tag {a.sample_id} is not in the G-code")
    for key, value in overrides.items():
        m = re.search(rf"^; {re.escape(key)} = (.*)$", text, re.M)
        if not m or m.group(1).split(",")[0].strip().strip('"') != value:
            sys.exit(f"FAIL: G-code has {key} = {m.group(1) if m else None!r}, expected {value!r}")
    xs, ys = [], []
    for m in re.finditer(r"^G1 X(-?[0-9.]+) Y(-?[0-9.]+)[^\n]*E[0-9.]", text, re.M):
        xs.append(float(m.group(1)))
        ys.append(float(m.group(2)))
    header = {k: re.search(rf"^; {re.escape(k)}\s*[:=]\s*(.*)$", text, re.M) for k in
              ("estimated printing time (normal mode)", "total layer number", "filament used [g]", "max_z_height")}
    print(gcode)
    for k, m in header.items():
        print(f"  {k}: {m.group(1).strip() if m else '?'}")
    print(f"  extrusion bounds X {min(xs):.1f}-{max(xs):.1f}  Y {min(ys):.1f}-{max(ys):.1f}")
    print(f"OK: tag {a.sample_id} present; overrides confirmed: {overrides}")


if __name__ == "__main__":
    main()
