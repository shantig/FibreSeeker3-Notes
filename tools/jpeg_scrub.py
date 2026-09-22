#!/usr/bin/env python3
"""Pure-stdlib JPEG metadata stripping and detection.

`strip_jpeg_metadata(data)` returns JPEG bytes with every APPn segment except
APP0 (JFIF) removed, which drops EXIF (APP1, where GPS lives), XMP, ICC in APP2,
and Photoshop/IPTC in APP13. `jpeg_metadata_markers(data)` reports which such
segments are present, for the scanner.
"""

from __future__ import annotations

# APP1..APP15 markers (0xFFE1..0xFFEF); APP0 (0xFFE0, JFIF) is structural, kept.
_METADATA_APP = set(range(0xE1, 0xF0))


def _iter_segments(data: bytes):
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG (missing SOI)")
    i = 2
    n = len(data)
    while i < n - 1:
        if data[i] != 0xFF:
            raise ValueError(f"bad marker at offset {i}")
        marker = data[i + 1]
        if marker == 0xD9:  # EOI
            yield ("marker", marker, i, i + 2)
            i += 2
            break
        if marker == 0xDA:  # SOS: entropy-coded data follows to EOI
            yield ("sos", marker, i, n)
            i = n
            break
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:  # RSTn / TEM: no length
            yield ("marker", marker, i, i + 2)
            i += 2
            continue
        seg_len = int.from_bytes(data[i + 2:i + 4], "big")
        end = i + 2 + seg_len
        yield ("segment", marker, i, end)
        i = end


def jpeg_metadata_markers(data: bytes) -> list[str]:
    """Return the names of metadata segments present (empty means clean)."""
    found = []
    for kind, marker, _start, _end in _iter_segments(data):
        if kind == "segment" and marker in _METADATA_APP:
            found.append(f"APP{marker - 0xE0}")
    return found


def strip_jpeg_metadata(data: bytes) -> bytes:
    """Return JPEG bytes with all metadata APP segments removed."""
    out = bytearray(b"\xff\xd8")
    for kind, marker, start, end in _iter_segments(data):
        if start == 0 and end == 2:  # the SOI we already wrote
            continue
        if kind == "segment" and marker in _METADATA_APP:
            continue  # drop EXIF/XMP/ICC/IPTC
        out += data[start:end]
    return bytes(out)


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        raw = open(path, "rb").read()
        print(path, jpeg_metadata_markers(raw))
