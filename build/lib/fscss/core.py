import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

__all__ = ["compile_string", "compile_file", "compile"]


def _find_node() -> Optional[str]:
    """Find node executable."""
    for name in ("node", "nodejs"):
        if shutil.which(name):
            return name
    return None


def _get_vendor_fscss_bin() -> Path:
    """Path to vendored FSCSS bin script."""
    here = Path(__file__).parent
    bin_path = here / "_vendor" / "xfscss" / "bin" / "fscss.js"
    return bin_path


def compile_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    cwd: Optional[Union[str, Path]] = None,
) -> str:
    """Compile an FSCSS file to CSS.

    Returns the stdout/stderr combined output from the compiler.
    """
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    node = _find_node()
    if node is None:
        raise RuntimeError(
            "Node.js is required to compile FSCSS. Please install Node.js (https://nodejs.org/)."
        )

    bin_path = _get_vendor_fscss_bin()
    if not bin_path.exists():
        raise RuntimeError(f"Vendored FSCSS compiler not found: {bin_path}")

    workdir = cwd or input_path.parent

    try:
        result = subprocess.run(
            [node, str(bin_path), str(input_path), str(output_path)],
            cwd=str(workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )
        return result.stdout or ""
    except subprocess.CalledProcessError as e:
        msg = e.stdout or e.stderr or str(e)
        raise RuntimeError(msg.strip()) from e


def compile_string(
    source: str,
    *,
    input_dir: Union[str, Path] = ".",
    output_path: Optional[Union[str, Path]] = None,
) -> str:
    """Compile FSCSS source string to CSS string.

    If output_path is not provided, compiled CSS is returned as a string.
    """
    if output_path is None:
        # Write to temp file
        input_dir = Path(input_dir).resolve()
        input_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fscss", dir=str(input_dir), delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            tmp_in = Path(f.name)
        tmp_out = tmp_in.with_suffix(".css")
        try:
            compile_file(tmp_in, tmp_out, cwd=input_dir)
            css = tmp_out.read_text(encoding="utf-8")
            return css
        finally:
            try:
                tmp_in.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                tmp_out.unlink(missing_ok=True)
            except Exception:
                pass
    else:
        # Write source to temp input in same dir as output for relative imports
        output_path = Path(output_path).resolve()
        out_dir = output_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fscss", dir=str(out_dir), delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            tmp_in = Path(f.name)
        try:
            compile_file(tmp_in, output_path, cwd=out_dir)
            return output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        finally:
            try:
                tmp_in.unlink(missing_ok=True)
            except Exception:
                pass


compile = compile_file
