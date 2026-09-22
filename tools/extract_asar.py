#!/usr/bin/env python3
"""List or statically extract an Electron ASAR archive without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path, PurePosixPath


def read_header(path: Path) -> tuple[dict, int]:
    with path.open("rb") as handle:
        prefix = handle.read(16)
        if len(prefix) != 16:
            raise ValueError("ASAR header is truncated")
        marker, pickle_size, payload_size, json_size = struct.unpack("<4I", prefix)
        if marker != 4 or pickle_size != payload_size + 4:
            raise ValueError("unsupported ASAR header")
        raw = handle.read(json_size)
    return json.loads(raw), 8 + pickle_size


def walk(node: dict, prefix: PurePosixPath = PurePosixPath()) -> list[tuple[PurePosixPath, dict]]:
    output = []
    for name, child in sorted(node.get("files", {}).items()):
        path = prefix / name
        if "files" in child:
            output.extend(walk(child, path))
        else:
            output.append((path, child))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--extract", type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    header, data_offset = read_header(archive)
    files = walk(header)
    if args.extract is None:
        for path, entry in files:
            print(f"{entry.get('size', 0)}\t{path}")
        return
    destination = args.extract.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with archive.open("rb") as source:
        for relative, entry in files:
            if entry.get("unpacked"):
                raise ValueError(f"unpacked ASAR entry requires companion directory: {relative}")
            target = (destination / Path(*relative.parts)).resolve()
            if destination not in target.parents:
                raise ValueError(f"unsafe ASAR path: {relative}")
            size = int(entry["size"])
            source.seek(data_offset + int(entry["offset"]))
            data = source.read(size)
            if len(data) != size:
                raise ValueError(f"truncated ASAR entry: {relative}")
            expected = entry.get("integrity", {}).get("hash")
            if expected and hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f"integrity mismatch: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(f"Extracted {len(files)} files to {destination}; integrity checked where declared")


if __name__ == "__main__":
    main()
