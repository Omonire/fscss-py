import sys
from pathlib import Path

from .core import compile_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fscss <input.fscss> [output.css]", file=sys.stderr)
        return 1

    arg = sys.argv[1]
    if arg in ("--help", "-h"):
        print("Usage: fscss <input.fscss> [output.css]")
        print("  Compile FSCSS files to CSS")
        return 0
    if arg in ("--version", "-v"):
        from . import __version__
        print(f"fscss {__version__}")
        return 0

    input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        p = Path(input_path)
        output_path = p.with_suffix(".css")

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
