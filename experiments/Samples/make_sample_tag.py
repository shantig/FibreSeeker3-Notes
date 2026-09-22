#!/usr/bin/env python3
"""Generate a small printable ID tag (binary STL) with raised 5x7 dot-matrix text.

The tag is printed alongside a test sample so the physical piece can be traced
to its entry in `experiments/Samples/samples.jsonl`. Text is built from
axis-aligned boxes: each glyph row's pixel runs are merged into rectangles, and
identical runs in consecutive rows are merged vertically, so boxes touch but
never overlap.

Usage:
  make_sample_tag.py X0008 OUT.stl [--pixel 0.8] [--base 1.0] [--relief 0.6]
  make_sample_tag.py X0008 --preview      # print the bitmap, write nothing
"""
import argparse
import re
import struct
import sys

# Classic 5x7 glyphs; '0' is slashed so it cannot be read as a letter O.
FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
}
ID_RE = re.compile(r"^X\d{4}$")


def box(x0, y0, z0, x1, y1, z1):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, d in quads:
        tris += [(p[a], p[b], p[c]), (p[a], p[c], p[d])]
    return tris


def bitmap(text):
    """Return the text as rows of 0/1 (top row first), one blank column between glyphs."""
    rows = [""] * 7
    for i, ch in enumerate(text):
        if ch not in FONT:
            sys.exit(f"no glyph for {ch!r}")
        for r in range(7):
            rows[r] += ("0" if i else "") + FONT[ch][r]
    return rows


def rectangles(rows):
    """Merge pixels into non-overlapping rectangles (col0, col1_excl, row0, row1_excl)."""
    runs_per_row = []
    for row in rows:
        runs, c = [], 0
        while c < len(row):
            if row[c] == "1":
                start = c
                while c < len(row) and row[c] == "1":
                    c += 1
                runs.append((start, c))
            else:
                c += 1
        runs_per_row.append(runs)
    rects, open_rects = [], {}
    for r, runs in enumerate(runs_per_row):
        still = {}
        for run in runs:
            if run in open_rects:
                still[run] = open_rects.pop(run)
            else:
                still[run] = r
        for run, r0 in open_rects.items():
            rects.append((run[0], run[1], r0, r))
        open_rects = still
    for run, r0 in open_rects.items():
        rects.append((run[0], run[1], r0, len(rows)))
    return rects


def normal(t):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
    ux, uy, uz, vx, vy, vz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    m = sum(v * v for v in n) ** 0.5 or 1.0
    return tuple(v / m for v in n)


def build(text, pixel, base, relief, margin):
    rows = bitmap(text)
    cols = len(rows[0])
    width = cols * pixel + 2 * margin
    height = 7 * pixel + 2 * margin
    tris = box(0, 0, 0, width, height, base)
    for c0, c1, r0, r1 in rectangles(rows):
        # row 0 is the top of the text, i.e. the largest Y
        tris += box(margin + c0 * pixel, margin + (7 - r1) * pixel, base,
                    margin + c1 * pixel, margin + (7 - r0) * pixel, base + relief)
    # centre on the origin in X/Y so a 3mf build item places the tag's centre
    dx, dy = width / 2, height / 2
    tris = [tuple((x - dx, y - dy, z) for x, y, z in t) for t in tris]
    return tris, width, height, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample_id")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--pixel", type=float, default=0.8, help="dot size in mm")
    ap.add_argument("--base", type=float, default=1.0, help="tag plate thickness in mm")
    ap.add_argument("--relief", type=float, default=0.6, help="raised text height in mm")
    ap.add_argument("--margin", type=float, default=1.6, help="border around text in mm")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    if not ID_RE.match(a.sample_id):
        sys.exit(f"sample id must look like X0001, got {a.sample_id!r}")
    tris, w, h, rows = build(a.sample_id, a.pixel, a.base, a.relief, a.margin)
    if a.preview or not a.out:
        print("\n".join(r.replace("1", "#").replace("0", ".") for r in rows))
        print(f"tag {w:.1f} x {h:.1f} x {a.base + a.relief:.1f} mm, {len(tris)} triangles")
        return
    with open(a.out, "wb") as fh:
        fh.write(f"sample tag {a.sample_id}".encode().ljust(80, b"\0"))
        fh.write(struct.pack("<I", len(tris)))
        for t in tris:
            fh.write(struct.pack("<3f", *normal(t)))
            for v in t:
                fh.write(struct.pack("<3f", *v))
            fh.write(b"\0\0")
    print(f"{a.out}: {a.sample_id} tag {w:.1f} x {h:.1f} x {a.base + a.relief:.1f} mm, {len(tris)} triangles")


if __name__ == "__main__":
    main()
