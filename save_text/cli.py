"""Command line interface for :mod:`save_text`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from . import save_text, save_text_lines


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Save text content to a file")
    parser.add_argument("path", type=Path, help="Destination file path")
    parser.add_argument(
        "content",
        nargs="*",
        help="Text fragments to write. If omitted, --stdin must be used.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the file instead of overwriting it.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read the content to write from standard input.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding (default: %(default)s).",
    )
    parser.add_argument(
        "--no-trailing-newline",
        action="store_true",
        help="Do not ensure a trailing newline is present in the output.",
    )
    parser.add_argument(
        "--newline",
        default="\n",
        help="Newline character used when joining multiple fragments.",
    )

    args = parser.parse_args(list(argv))

    if args.stdin and args.content:
        parser.error("--stdin cannot be used together with positional content arguments")

    if not args.stdin and not args.content:
        parser.error("Either provide content arguments or specify --stdin")

    return args


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    content: Iterable[str]
    if args.stdin:
        content_text = sys.stdin.read()
        save_text(
            content_text,
            args.path,
            encoding=args.encoding,
            append=args.append,
            ensure_trailing_newline=not args.no_trailing_newline,
        )
    else:
        content = args.content
        save_text_lines(
            content,
            args.path,
            encoding=args.encoding,
            append=args.append,
            newline=args.newline,
            ensure_trailing_newline=not args.no_trailing_newline,
        )

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
