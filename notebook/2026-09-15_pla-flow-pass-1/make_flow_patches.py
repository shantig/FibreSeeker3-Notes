#!/usr/bin/env python3
"""Build an OrcaSlicer flow-rate calibration print for Loom from the CLI.

OrcaSlicer's Calibration > Flow rate lives in the GUI. This reproduces its
patch print without the GUI:

1. `OrcaSlicer --export-3mf` turns Orca's bundled calibration model
   (`calib/filament_flow/flowrate-test-pass1.3mf` or `-pass2.3mf`, objects named
   `flowrate_<mod>` with `m` for minus) into a project 3mf.
2. The embedded project settings are replaced with Loom's resolved settings
   taken from a reference project 3mf, with the nozzle temperatures overridden.
3. Every patch object gets the per-object overrides Orca's calibration applies
   (`adjust_settings_for_flowrate_calib`), and `print_flow_ratio =
   (100 + mod) / 100` from its name.
4. The patch layout is recentred on the bed, patches get no brim, and
   `OrcaSlicer --arrange 0 --slice 0` produces the G-code.
5. The G-code is checked: each patch's top-surface extrusion per millimetre,
   relative to the `flowrate_0` patch, must equal its intended ratio. The
   build fails closed if any patch is off by more than 0.5 %.
6. With `--sample-id`, an ID tag from `experiments/Samples/make_sample_tag.py`
   is added as its own object, centred below the patches, and the build fails
   if the tag is missing from the G-code. Register the ID in
   `experiments/Samples/samples.jsonl`.

Usage:
  make_flow_patches.py --calib CALIB.3mf --reference LOOM.3mf --out DIR \
      [--sample-id X0001] [--name loom_flow_pass1]
      [--nozzle-temp 205] [--first-layer-temp 210]
      [--centre-x 150 --centre-y 150]
"""
import argparse
import json
import math
import re
import subprocess
import tempfile
import sys
import zipfile
from pathlib import Path

ORCA = "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer"
NAME_RE = re.compile(r"^flowrate_(m?)([0-9.]+)$")
TAG_NAME_RE = re.compile(r"^tag_(X\d{4})\.stl$")
REPO = Path(__file__).resolve().parents[3]
TAG_TOOL = REPO / "experiments/Samples/make_sample_tag.py"
TAG_GAP_Y = 24.0  # mm from the nearest patch row centre to the tag centre


def modifier_from_name(name):
    m = NAME_RE.match(name)
    if not m:
        sys.exit(f"unexpected calibration object name: {name!r}")
    value = float(m.group(2))
    return -value if m.group(1) else value


def per_object_overrides(project, ratio):
    """The overrides Orca's GUI flow calibration applies to every patch."""
    nozzle = float(project["nozzle_diameter"][0])
    layer = nozzle / 2.0
    width = nozzle * 1.2
    # Orca caps solid/top speeds by the filament's max volumetric speed.
    mm3_per_mm = (width - layer * (1 - math.pi / 4)) * layer
    max_speed = float(project["filament_max_volumetric_speed"][0]) / mm3_per_mm
    internal_solid = math.floor(min(float(project["internal_solid_infill_speed"]), max_speed))
    top_surface = math.floor(min(float(project["top_surface_speed"]), max_speed))
    return {
        "wall_loops": "3",
        "only_one_wall_top": "1",
        "thick_internal_bridges": "0",
        "sparse_infill_density": "35%",
        "min_width_top_surface": "100%",
        "bottom_shell_layers": "1",
        "top_shell_layers": "5",
        "detect_thin_wall": "1",
        "filter_out_gap_fill": "0",
        "sparse_infill_pattern": "zig-zag",
        "top_surface_line_width": f"{width:g}",
        "internal_solid_infill_line_width": f"{width:g}",
        "top_surface_pattern": "monotonic",
        "top_solid_infill_flow_ratio": "1",
        "infill_direction": "45",
        "solid_infill_direction": "135",
        "ironing_type": "no ironing",
        "internal_solid_infill_speed": str(internal_solid),
        "top_surface_speed": str(top_surface),
        "seam_slope_type": "none",
        "gap_fill_target": "nowhere",
        "print_flow_ratio": f"{ratio:g}",
        # Not part of Orca's calibration overrides: the Loom project default is
        # auto_brim, and brims collide on the calibration model's tight grid.
        "brim_type": "no_brim",
    }


ITEM_RE = re.compile(r'(<item objectid="(\d+)"[^>]*transform=")([^"]+)(")')


def recentre(model_xml, cx, cy, tag_ids=()):
    """Centre the patch layout on (cx, cy); put any tag item centred below it."""
    items = ITEM_RE.findall(model_xml)
    patch = [t for t in items if t[1] not in tag_ids]
    if not patch:
        sys.exit("calibration model has no build items")
    xs = [float(t[2].split()[9]) for t in patch]
    ys = [float(t[2].split()[10]) for t in patch]
    dx = cx - (min(xs) + max(xs)) / 2
    dy = cy - (min(ys) + max(ys)) / 2
    tag_y = min(ys) + dy - TAG_GAP_Y

    def shift(m):
        v = m.group(3).split()
        if len(v) != 12:
            sys.exit(f"unexpected transform: {m.group(3)}")
        if m.group(2) in tag_ids:
            v[9], v[10] = f"{cx:g}", f"{tag_y:g}"
        else:
            v[9] = f"{float(v[9]) + dx:g}"
            v[10] = f"{float(v[10]) + dy:g}"
        return m.group(1) + " ".join(v) + m.group(4)

    return ITEM_RE.sub(shift, model_xml)


def build(args):
    # OrcaSlicer does not resolve relative output paths against our cwd.
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    calib = str(Path(args.calib).resolve())
    exported = out / "_export.3mf"
    project_3mf = out / f"{args.name}.3mf"

    inputs = [calib]
    if args.sample_id:
        tag_stl = Path(tempfile.gettempdir()) / f"tag_{args.sample_id}.stl"
        subprocess.run([sys.executable, str(TAG_TOOL), args.sample_id, str(tag_stl)],
                       check=True, capture_output=True)
        inputs.append(str(tag_stl))
    subprocess.run([ORCA, "--arrange", "0", "--export-3mf", str(exported), *inputs],
                   check=True, capture_output=True, cwd=tempfile.gettempdir())

    with zipfile.ZipFile(args.reference) as ref:
        project = json.loads(ref.read("Metadata/project_settings.config"))
    project["nozzle_temperature"] = [str(args.nozzle_temp)]
    project["nozzle_temperature_initial_layer"] = [str(args.first_layer_temp)]

    src = zipfile.ZipFile(exported)
    model_settings = src.read("Metadata/model_settings.config").decode("utf-8")

    ratios = {}
    tag_ids = set()

    def add_overrides(match):
        block = match.group(0)
        obj_id = re.match(r'<object id="(\d+)">', block).group(1)
        name = re.search(r'<metadata key="name" value="([^"]+)"/>', block).group(1)
        anchor = '<metadata key="extruder" value="1"/>'
        if block.count(anchor) < 1:
            sys.exit(f"object {name}: no extruder metadata to anchor overrides")
        tag = TAG_NAME_RE.match(name)
        if tag:
            if tag.group(1) != args.sample_id:
                sys.exit(f"tag object {name} does not match --sample-id {args.sample_id}")
            tag_ids.add(obj_id)
            # The tag prints with the project's normal settings; only drop the brim.
            return block.replace(anchor, anchor + '\n    <metadata key="brim_type" value="no_brim"/>', 1)
        ratio = round((100 + modifier_from_name(name)) / 100, 6)
        ratios[name] = ratio
        extra = "".join(f'\n    <metadata key="{k}" value="{v}"/>'
                        for k, v in per_object_overrides(project, ratio).items())
        return block.replace(anchor, anchor + extra, 1)

    model_settings = re.sub(r"<object id=\"\d+\">.*?</object>", add_overrides,
                            model_settings, flags=re.S)
    if len(ratios) < 2 or "flowrate_0" not in ratios:
        sys.exit(f"expected flowrate_* objects including flowrate_0, got {sorted(ratios)}")

    model = src.read("3D/3dmodel.model").decode("utf-8")
    if args.sample_id and len(tag_ids) != 1:
        sys.exit(f"expected exactly one tag object for {args.sample_id}, found {len(tag_ids)}")
    model = recentre(model, args.centre_x, args.centre_y, tag_ids)

    with zipfile.ZipFile(project_3mf, "w", zipfile.ZIP_DEFLATED) as z:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "3D/3dmodel.model":
                data = model.encode("utf-8")
            elif item.filename == "Metadata/project_settings.config":
                data = json.dumps(project, indent=1).encode()
            elif item.filename == "Metadata/model_settings.config":
                data = model_settings.encode("utf-8")
            z.writestr(item, data)
    src.close()
    exported.unlink()

    slice_dir = out / "_slice"
    slice_dir.mkdir(exist_ok=True)
    subprocess.run([ORCA, "--arrange", "0", "--slice", "0", "--outputdir", str(slice_dir),
                    str(project_3mf)], check=True, capture_output=True, cwd=tempfile.gettempdir())
    gcode = out / f"{args.name}.gcode"
    (slice_dir / "plate_1.gcode").replace(gcode)
    slice_dir.rmdir()
    return gcode, ratios


def measure(gcode):
    """Top-surface extrusion per mm of travel, per object."""
    per_obj = {}
    obj = None
    kind = None
    x = y = None
    for line in open(gcode, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("; printing object "):
            obj = line[len("; printing object "):].split(" id:")[0]
            continue
        if line.startswith("; stop printing object"):
            obj = None
            continue
        if line.startswith(";TYPE:"):
            kind = line[len(";TYPE:"):]
            continue
        if not (line.startswith("G1 ") or line.startswith("G0 ")):
            if line.startswith(("G2 ", "G3 ")):
                # arcs are not used on top surfaces; keep position current
                for axis, val in re.findall(r"([XY])(-?[0-9.]+)", line):
                    if axis == "X":
                        x = float(val)
                    else:
                        y = float(val)
            continue
        words = dict(re.findall(r"([XYZEF])(-?[0-9.]+)", line))
        nx = float(words["X"]) if "X" in words else x
        ny = float(words["Y"]) if "Y" in words else y
        e = float(words.get("E", 0))
        if obj and kind == "Top surface" and e > 0 and x is not None and ("X" in words or "Y" in words):
            dist = math.hypot(nx - x, ny - y)
            if dist > 0:
                tot = per_obj.setdefault(obj, [0.0, 0.0])
                tot[0] += e
                tot[1] += dist
        x, y = nx, ny
    return {k: v[0] / v[1] for k, v in per_obj.items() if v[1] > 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--nozzle-temp", type=int, default=205)
    ap.add_argument("--first-layer-temp", type=int, default=210)
    ap.add_argument("--sample-id",
                    help="physical sample ID (X0001); prints an ID tag below the patches")
    ap.add_argument("--name", default="loom_flow_pass1",
                    help="basename for the output .3mf and .gcode")
    ap.add_argument("--centre-x", type=float, default=150.0)
    ap.add_argument("--centre-y", type=float, default=150.0)
    args = ap.parse_args()

    gcode, ratios = build(args)
    rates = measure(gcode)
    missing = sorted(set(ratios) - set(rates))
    if missing:
        sys.exit(f"no top-surface extrusion measured for: {missing}")
    base = rates["flowrate_0"]
    worst = 0.0
    print(f"{gcode}")
    print(f"{'object':<14}{'intended':>9}{'measured':>10}{'error %':>9}")
    for name in sorted(ratios, key=lambda n: ratios[n]):
        measured = rates[name] / base
        err = (measured / ratios[name] - 1) * 100
        worst = max(worst, abs(err))
        print(f"{name:<14}{ratios[name]:>9.3f}{measured:>10.4f}{err:>9.2f}")
    if worst > 0.5:
        sys.exit(f"FAIL: a patch's measured flow differs from intent by {worst:.2f} %")
    print(f"OK: all patches within {worst:.2f} % of intended flow ratio")
    xs, ys = extrusion_bounds(gcode)
    print(f"extrusion bounds X {min(xs):.1f}-{max(xs):.1f}  Y {min(ys):.1f}-{max(ys):.1f}")
    if args.sample_id:
        text = Path(gcode).read_text(encoding="utf-8", errors="replace")
        if f"; printing object tag_{args.sample_id}.stl" not in text:
            sys.exit(f"FAIL: tag {args.sample_id} is not in the G-code")
        print(f"OK: tag {args.sample_id} printed with the patches")


def extrusion_bounds(gcode):
    xs, ys = [], []
    for line in open(gcode, encoding="utf-8", errors="replace"):
        m = re.match(r"^G1 X(-?[0-9.]+) Y(-?[0-9.]+).*E[0-9.]", line)
        if m:
            xs.append(float(m.group(1)))
            ys.append(float(m.group(2)))
    return xs, ys


if __name__ == "__main__":
    main()
