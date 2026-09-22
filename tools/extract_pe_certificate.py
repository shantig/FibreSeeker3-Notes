#!/usr/bin/env python3
"""Extract Authenticode PKCS#7 records from a PE file without execution."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()

    data = args.input.read_bytes()
    if data[:2] != b"MZ":
        raise ValueError("not a DOS/PE file")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("missing PE signature")

    optional_header = pe_offset + 24
    magic = struct.unpack_from("<H", data, optional_header)[0]
    if magic == 0x10B:
        data_directory = optional_header + 96
    elif magic == 0x20B:
        data_directory = optional_header + 112
    else:
        raise ValueError(f"unsupported optional-header magic: {magic:#x}")

    certificate_offset, certificate_size = struct.unpack_from(
        "<II", data, data_directory + (4 * 8)
    )
    result = {
        "input": str(args.input),
        "certificate_table_offset": certificate_offset,
        "certificate_table_size": certificate_size,
        "certificates": [],
    }
    if not certificate_offset or not certificate_size:
        print(json.dumps(result, indent=2))
        return

    args.output_directory.mkdir(parents=True, exist_ok=True)
    cursor = certificate_offset
    end = certificate_offset + certificate_size
    index = 1
    while cursor + 8 <= end:
        length, revision, certificate_type = struct.unpack_from("<IHH", data, cursor)
        if length < 8 or cursor + length > len(data):
            raise ValueError("invalid WIN_CERTIFICATE length")
        body = data[cursor + 8 : cursor + length]
        output = args.output_directory / f"authenticode-{index}.p7b"
        if output.exists():
            raise FileExistsError(f"refusing to overwrite {output}")
        output.write_bytes(body)
        result["certificates"].append(
            {
                "index": index,
                "offset": cursor,
                "length": length,
                "revision": revision,
                "certificate_type": certificate_type,
                "output": str(output),
            }
        )
        cursor += (length + 7) & ~7
        index += 1

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
