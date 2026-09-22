#!/usr/bin/env python3
"""Extract readable text from an archived HTML document without network access."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg", "noscript"}:
            self._ignored_depth += 1
        elif not self._ignored_depth and tag in {
            "article",
            "br",
            "div",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "header",
            "li",
            "main",
            "p",
            "section",
            "table",
            "td",
            "th",
            "tr",
        }:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg", "noscript"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
        elif not self._ignored_depth and tag in {
            "article",
            "div",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "header",
            "li",
            "main",
            "p",
            "section",
            "table",
            "tr",
        }:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self._parts.append(data)

    def text(self) -> str:
        lines: list[str] = []
        for line in "".join(self._parts).splitlines():
            normalized = " ".join(line.split())
            if normalized and (not lines or normalized != lines[-1]):
                lines.append(normalized)
        return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    extractor = TextExtractor()
    extractor.feed(args.input.read_text(encoding="utf-8", errors="replace"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(extractor.text(), encoding="utf-8")


if __name__ == "__main__":
    main()
