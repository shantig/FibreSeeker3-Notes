#!/usr/bin/env python3
"""Rebuild a printable solid (binary STL) from a sliced G-code file.

For each layer it takes the outermost perimeter loops of one feature section,
fills them with the even-odd rule (so holes stay holes), grows the filled area
by half a line width (the toolpath is the centre of the extrusion), and stacks
the layers as a voxel solid whose surface is written as an STL.

The result is the printed shape, not the original CAD: it is quantised to the
raster cell in X/Y and to the layer height in Z. Good enough to reprint the same
part with different settings; not a replacement for the real model.

Usage:
  gcode_to_solid_stl.py IN.gcode OUT.stl [--sections "Inset XP,Inset 0"] [--tool T1]
      [--width 0.42] [--cell 0.2] [--skip-sections "Skirt,Priming line"]
"""
import argparse
import math
import re
import struct
import sys
from collections import defaultdict

LAYER_RE = re.compile(r"^;\s*LAYER:(\d+)(?:\s*\[([\d.]+)\])?")
SECTION_RE = re.compile(r"^;\s*(.+?)\s+start$")
WORD_RE = re.compile(r"([XYEUV])(-?[\d.]+)")


def parse_loops(path, sections, tool, skip):
    """Return {layer_index: (z, [loop, …])} with loops as lists of (x, y)."""
    layers = {}
    cur_layer = None
    z = 0.0
    sec = None
    cur_tool = None
    x = y = None
    loop = []
    out = defaultdict(list)
    zs = {}
    for line in open(path, errors="replace"):
        c = line.strip()
        m = LAYER_RE.match(c)
        if m:
            cur_layer = int(m.group(1))
            if m.group(2):
                z = float(m.group(2))
            zs[cur_layer] = z
            loop = []
            continue
        m = SECTION_RE.match(c)
        if m:
            if len(loop) > 2:
                out[cur_layer].append(loop)
            loop = []
            sec = m.group(1)
            continue
        if re.match(r"^T\d", c):
            cur_tool = c.split()[0]
            continue
        if not c.startswith(("G0", "G1")):
            continue
        w = dict(WORD_RE.findall(c.split(";")[0]))
        if "X" not in w and "Y" not in w:
            continue
        nx = float(w.get("X", x if x is not None else 0.0))
        ny = float(w.get("Y", y if y is not None else 0.0))
        extruding = float(w.get("E", 0)) > 0 or float(w.get("V", 0)) > 0
        if extruding and sec in sections and (tool is None or cur_tool == tool) and sec not in skip:
            if not loop and x is not None:
                loop.append((x, y))
            loop.append((nx, ny))
        else:
            if len(loop) > 2:
                out[cur_layer].append(loop)
            loop = []
        x, y = nx, ny
    if len(loop) > 2:
        out[cur_layer].append(loop)
    for layer, loops in out.items():
        layers[layer] = (zs.get(layer, 0.0), loops)
    return layers


def _area(loop):
    a = 0.0
    pts = loop if loop[0] == loop[-1] else loop + [loop[0]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        a += ax * by - bx * ay
    return a / 2.0


def _inside(pt, loop):
    x, y = pt
    pts = loop if loop[0] == loop[-1] else loop + [loop[0]]
    inside = False
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if (ay > y) != (by > y):
            xint = ax + (y - ay) * (bx - ax) / (by - ay)
            if x < xint:
                inside = not inside
    return inside


def _min_gap(loop, parent):
    """Smallest distance from this loop to the parent outline (point to segment)."""
    pts = parent if parent[0] == parent[-1] else parent + [parent[0]]
    segs = list(zip(pts, pts[1:]))
    step = max(1, len(loop) // 200)
    best = float("inf")
    for x, y in loop[::step]:
        for (ax, ay), (bx, by) in segs:
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
            ex, ey = ax + t * dx - x, ay + t * dy - y
            d = ex * ex + ey * ey
            if d < best:
                best = d
    return math.sqrt(best)


def classify(loops, width):
    """Split loops into solid outlines and holes, dropping concentric walls.

    A loop nested inside another is a hole only if it stands clear of its
    parent; a loop that hugs its parent within ~1.5 line widths is the next
    wall of the same region and is dropped.
    """
    loops = [l for l in loops if abs(_area(l)) > width * width]
    loops.sort(key=lambda l: -abs(_area(l)))
    solids, holes = [], []
    for i, loop in enumerate(loops):
        probe = loop[len(loop) // 3]
        parent = None
        for cand in loops[:i]:
            if _inside(probe, cand):
                parent = cand  # loops are sorted big to small, so the last hit is the closest
        if parent is None:
            solids.append(loop)
        elif _min_gap(loop, parent) < 1.5 * width:
            continue  # concentric wall of the same region
        elif parent in holes:
            solids.append(loop)
        else:
            holes.append(loop)
    return solids, holes


def fill_polygon(mask, loop, x0, y0, nx, ny, cell, value=1):
    edges = []
    pts = loop if loop[0] == loop[-1] else loop + [loop[0]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if ay != by:
            edges.append((ax, ay, bx, by))
    for j in range(ny):
        yc = y0 + (j + 0.5) * cell
        xs = []
        for ax, ay, bx, by in edges:
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        row = j * nx
        for k in range(0, len(xs) - 1, 2):
            i0 = max(0, int(math.floor((xs[k] - x0) / cell)))
            i1 = min(nx - 1, int(math.ceil((xs[k + 1] - x0) / cell)) - 1)
            for i in range(i0, i1 + 1):
                mask[row + i] = value


def fill_mask(loops, x0, y0, nx, ny, cell, width):
    """Filled cross-section: solid outlines minus holes."""
    solids, holes = classify(loops, width)
    mask = bytearray(nx * ny)
    for loop in solids:
        fill_polygon(mask, loop, x0, y0, nx, ny, cell, 1)
    for loop in holes:
        fill_polygon(mask, loop, x0, y0, nx, ny, cell, 0)
    return mask


def dilate(mask, nx, ny, radius_cells):
    for _ in range(radius_cells):
        new = bytearray(mask)
        for j in range(ny):
            row = j * nx
            for i in range(nx):
                if mask[row + i]:
                    continue
                if ((i and mask[row + i - 1]) or (i + 1 < nx and mask[row + i + 1])
                        or (j and mask[row - nx + i]) or (j + 1 < ny and mask[row + nx + i])):
                    new[row + i] = 1
        mask = new
    return mask


def write_stl(path, tris, header=b"gcode_to_solid_stl"):
    with open(path, "wb") as fh:
        fh.write(header.ljust(80, b"\0")[:80])
        fh.write(struct.pack("<I", len(tris)))
        for (a, b, c) in tris:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
            m = math.sqrt(sum(v * v for v in n)) or 1.0
            fh.write(struct.pack("<3f", *(v / m for v in n)))
            for v in (a, b, c):
                fh.write(struct.pack("<3f", *v))
            fh.write(b"\0\0")


def quad(tris, p1, p2, p3, p4):
    tris.append((p1, p2, p3))
    tris.append((p1, p3, p4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gcode")
    ap.add_argument("out")
    ap.add_argument("--sections", default="Inset XP,Inset 0",
                    help="wall sections to take loops from (comma separated)")
    ap.add_argument("--tool", default="T1")
    ap.add_argument("--width", type=float, default=0.42, help="line width of that section (mm)")
    ap.add_argument("--cell", type=float, default=0.2, help="raster cell size (mm)")
    ap.add_argument("--skip-sections", default="Skirt,Priming line")
    a = ap.parse_args()

    skip = {s.strip() for s in a.skip_sections.split(",") if s.strip()}
    sections = {t.strip() for t in a.sections.split(",") if t.strip()}
    layers = parse_loops(a.gcode, sections, a.tool, skip)
    if not layers:
        sys.exit(f"no loops found for sections {sorted(sections)} / tool {a.tool}")
    order = sorted(layers)
    pts = [p for layer in order for loop in layers[layer][1] for p in loop]
    margin = a.width + 2 * a.cell
    x0, x1 = min(p[0] for p in pts) - margin, max(p[0] for p in pts) + margin
    y0, y1 = min(p[1] for p in pts) - margin, max(p[1] for p in pts) + margin
    nx = int(math.ceil((x1 - x0) / a.cell))
    ny = int(math.ceil((y1 - y0) / a.cell))
    grow = max(1, int(round((a.width / 2) / a.cell)))

    zs = [layers[l][0] for l in order]
    tops = zs[1:] + [zs[-1] + (zs[-1] - zs[-2] if len(zs) > 1 else 0.2)]
    masks = []
    for layer, z, ztop in zip(order, zs, tops):
        m = fill_mask(layers[layer][1], x0, y0, nx, ny, a.cell, a.width)
        masks.append(dilate(m, nx, ny, grow))
    empty = bytearray(nx * ny)

    tris = []
    for idx, (z, ztop) in enumerate(zip(zs, tops)):
        zb = z - (zs[idx] - zs[idx - 1] if idx else zs[0])
        zb = max(0.0, zb)
        m = masks[idx]
        below = masks[idx - 1] if idx else empty
        above = masks[idx + 1] if idx + 1 < len(masks) else empty
        for j in range(ny):
            row = j * nx
            yA, yB = y0 + j * a.cell, y0 + (j + 1) * a.cell
            for i in range(nx):
                if not m[row + i]:
                    continue
                xA, xB = x0 + i * a.cell, x0 + (i + 1) * a.cell
                if not below[row + i]:
                    quad(tris, (xA, yA, zb), (xA, yB, zb), (xB, yB, zb), (xB, yA, zb))
                if not above[row + i]:
                    quad(tris, (xA, yA, z), (xB, yA, z), (xB, yB, z), (xA, yB, z))
                if i == 0 or not m[row + i - 1]:
                    quad(tris, (xA, yA, zb), (xA, yA, z), (xA, yB, z), (xA, yB, zb))
                if i + 1 >= nx or not m[row + i + 1]:
                    quad(tris, (xB, yA, zb), (xB, yB, zb), (xB, yB, z), (xB, yA, z))
                if j == 0 or not m[row - nx + i]:
                    quad(tris, (xA, yA, zb), (xB, yA, zb), (xB, yA, z), (xA, yA, z))
                if j + 1 >= ny or not m[row + nx + i]:
                    quad(tris, (xA, yB, zb), (xA, yB, z), (xB, yB, z), (xB, yB, zb))
    write_stl(a.out, tris)
    area = sum(sum(m) for m in masks) * a.cell * a.cell
    height = tops[-1]
    print(f"{a.out}: {len(tris)} triangles, {len(order)} layers, "
          f"{x1 - x0:.1f} x {y1 - y0:.1f} x {height:.2f} mm bounding box, "
          f"solid volume ≈ {area * (zs[1] - zs[0] if len(zs) > 1 else 0.2):.0f} mm³")


if __name__ == "__main__":
    main()
