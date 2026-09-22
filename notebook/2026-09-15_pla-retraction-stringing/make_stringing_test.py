#!/usr/bin/env python3
"""Generate a two-pillar stringing/retraction test STL (binary).

Two rectangular pillars separated by a travel gap. The slicer must travel
between them on every layer, so unretracted ooze shows up as strings in the gap.

Usage: make_stringing_test.py OUT.stl [--size 8] [--height 30] [--pitch 60]
"""
import argparse
import struct


def box(x0, y0, z0, dx, dy, dz):
    """Return a list of (v0, v1, v2) triangles for an axis-aligned box."""
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    p = {
        0: (x0, y0, z0), 1: (x1, y0, z0), 2: (x1, y1, z0), 3: (x0, y1, z0),
        4: (x0, y0, z1), 5: (x1, y0, z1), 6: (x1, y1, z1), 7: (x0, y1, z1),
    }
    quads = [
        (0, 3, 2, 1),  # bottom (-Z)
        (4, 5, 6, 7),  # top (+Z)
        (0, 1, 5, 4),  # -Y
        (1, 2, 6, 5),  # +X
        (2, 3, 7, 6),  # +Y
        (3, 0, 4, 7),  # -X
    ]
    tris = []
    for a, b, c, d in quads:
        tris.append((p[a], p[b], p[c]))
        tris.append((p[a], p[c], p[d]))
    return tris


def normal(t):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    m = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
    return nx / m, ny / m, nz / m


def write_stl(path, tris, header=b"stringing test"):
    with open(path, "wb") as fh:
        fh.write(header.ljust(80, b"\0")[:80])
        fh.write(struct.pack("<I", len(tris)))
        for t in tris:
            fh.write(struct.pack("<3f", *normal(t)))
            for v in t:
                fh.write(struct.pack("<3f", *v))
            fh.write(struct.pack("<H", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--size", type=float, default=8.0, help="pillar footprint (mm)")
    ap.add_argument("--height", type=float, default=30.0, help="pillar height (mm)")
    ap.add_argument("--pitch", type=float, default=60.0, help="centre-to-centre spacing (mm)")
    a = ap.parse_args()

    half = a.size / 2.0
    tris = []
    for cx in (-a.pitch / 2.0, a.pitch / 2.0):
        tris += box(cx - half, -half, 0.0, a.size, a.size, a.height)
    write_stl(a.out, tris)
    print(
        f"{a.out}: {len(tris)} triangles, 2 pillars {a.size}x{a.size}x{a.height} mm, "
        f"pitch {a.pitch} mm (gap {a.pitch - a.size:.1f} mm)"
    )


if __name__ == "__main__":
    main()
