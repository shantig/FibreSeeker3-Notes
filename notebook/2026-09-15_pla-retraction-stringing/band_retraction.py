#!/usr/bin/env python3
"""Turn a normally-sliced OrcaSlicer G-code into a banded retraction test.

The sliced file must use relative E (`use_relative_e_distances = 1`), software
retraction (`use_firmware_retraction = 0`) and no wipe, so every retraction is a
bare `G1 E-<len> F<speed>` line and every deretraction its `G1 E<len> F<speed>`
partner. Each retract/deretract pair is rewritten together, so net extrusion is
unchanged; the band a pair belongs to is decided by the *retract*, which keeps
the pairs balanced across band boundaries.

Bands are given as `layer:length:speed` (speed in mm/s), e.g.

    band_retraction.py in.gcode out.gcode \
        --band 1:0.5:15 --band 26:0.5:35 --band 51:0.8:35

`--band N:...` applies from layer N until the next band's first layer.

Usage: band_retraction.py IN.gcode OUT.gcode --band L:LEN:SPEED [--band ...]
"""
import argparse
import re
import sys

RETRACT_RE = re.compile(r"^G1 E(-[0-9.]+) F([0-9]+)\s*$")
DERETRACT_RE = re.compile(r"^G1 E([0-9.]+) F([0-9]+)\s*$")
LAYER_RE = re.compile(r"^SET_PRINT_STATS_INFO CURRENT_LAYER=([0-9]+)\s*$")


def fmt_e(value):
    """Match OrcaSlicer's own E formatting (5 dp, leading zero dropped)."""
    s = f"{value:.5f}".rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s or "0"


def parse_band(spec):
    layer, length, speed = spec.split(":")
    return int(layer), float(length), float(speed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--band", action="append", required=True,
                    help="LAYER:LENGTH_MM:SPEED_MM_S")
    a = ap.parse_args()

    bands = sorted(parse_band(b) for b in a.band)
    if bands[0][0] != 1:
        sys.exit("first band must start at layer 1")

    def band_for(layer):
        chosen = bands[0]
        for b in bands:
            if b[0] <= layer:
                chosen = b
        return chosen

    lines = open(a.infile, encoding="utf-8", errors="surrogateescape").read().split("\n")
    out = []
    layer = 0
    pending = None      # (length, speed) owed to the next deretraction
    counts = {}
    emitted_band = None

    for ln in lines:
        m = LAYER_RE.match(ln)
        if m:
            layer = int(m.group(1))
            out.append(ln)
            continue

        m = RETRACT_RE.match(ln)
        if m:
            start, length, speed = band_for(layer)
            if pending is not None:
                sys.exit(f"retract at layer {layer} with an unmatched retract still open")
            pending = (length, speed)
            counts[(length, speed)] = counts.get((length, speed), 0) + 1
            if emitted_band != (start, length, speed):
                emitted_band = (start, length, speed)
                out.append(f"; FS-RETRACT BAND from layer {start}: "
                           f"length {length} mm, speed {speed} mm/s")
            out.append(f"G1 E-{fmt_e(length)} F{int(round(speed * 60))}")
            continue

        m = DERETRACT_RE.match(ln)
        if m:
            if pending is None:
                sys.exit(f"deretraction at layer {layer} with no matching retract")
            length, speed = pending
            pending = None
            out.append(f"G1 E{fmt_e(length)} F{int(round(speed * 60))}")
            continue

        out.append(ln)

    open(a.outfile, "w", encoding="utf-8", errors="surrogateescape").write("\n".join(out))
    print(f"{a.outfile}: {sum(counts.values())} retractions rewritten over {layer} layers")
    for (length, speed), n in sorted(counts.items()):
        print(f"  {length:>4} mm @ {speed:>4} mm/s : {n}")
    if pending is not None:
        print("  note: file ends retracted (final retract has no partner) — expected")


if __name__ == "__main__":
    main()
