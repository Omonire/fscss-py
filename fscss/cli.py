from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import compile_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fscss",
        description="Compile FSCSS files to CSS.",
    )
    parser.add_argument("input", nargs="?", help="Input .fscss file")
    parser.add_argument("output", nargs="?", help="Output .css file (default: input with .css)")
    parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        help="Watch the input file and recompile on changes.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show the fscss version and exit.",
    )
    return parser


def _resolve_outputs(input_path: str, output_path: str | None) -> tuple[str, str]:
    if output_path:
        return input_path, output_path
    return input_path, str(Path(input_path).with_suffix(".css"))


def _watch(input_path: str, output_path: str) -> int:
    import time

    from .integrations import watch_dir

    src = Path(input_path).resolve()
    try:
        out = compile_file(input_path, output_path)
        if out:
            print(out, end="")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

    print(f"Watching {src} for changes... (Ctrl+C to stop)")
    watch_dir(src.parent, callback=lambda s, o: print(f"[fscss] recompiled {s} -> {o}"))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from . import __version__

        print(f"fscss {__version__}")
        return 0

    if not args.input:
        parser.print_help(sys.stderr)
        return 1

    input_path, output_path = _resolve_outputs(args.input, args.output)

    if args.watch:
        return _watch(input_path, output_path)

    try:
        out = compile_file(input_path, output_path)
        if out:
            print(out, end="")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
