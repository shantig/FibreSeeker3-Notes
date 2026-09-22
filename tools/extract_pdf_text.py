#!/usr/bin/env python3
import argparse
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record_id")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    if args.destination.exists():
        raise SystemExit(f"refusing to overwrite {args.destination}")

    reader = PdfReader(args.source)
    args.destination.parent.mkdir(parents=True, exist_ok=False)
    with args.destination.open("w", encoding="utf-8") as output:
        output.write(f"record_id: {args.record_id}\n")
        output.write(f"source: {args.source}\n")
        output.write(f"pages: {len(reader.pages)}\n\n")
        for page_number, page in enumerate(reader.pages, start=1):
            output.write(f"\n===== PAGE {page_number} =====\n")
            output.write(page.extract_text() or "")
            output.write("\n")


if __name__ == "__main__":
    main()
