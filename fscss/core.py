import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

__all__ = ["compile_string", "compile_file", "compile"]

_node_cache: Optional[str] = None


def _read_text_normalized(path: Path) -> str:
    """Read a file as text, stripping BOMs and tolerating common encodings."""
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le")
    if data.startswith(b"\xfe\xff"):
        return data[2:].decode("utf-16-be")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8")
    try:
        return data.decode("utf-8")
    except UnicodeError:
        for enc in ("utf-16-le", "utf-16-be", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeError:
                continue
        return data.decode("utf-8", errors="replace")


def _find_node() -> Optional[str]:
    """Find node executable (``FSCSS_NODE`` overrides PATH lookup)."""
    global _node_cache
    override = os.environ.get("FSCSS_NODE")
    if override:
        return override
    if _node_cache is not None:
        return _node_cache
    for name in ("node", "nodejs"):
        found = shutil.which(name)
        if found:
            _node_cache = name
            return _node_cache
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
    timeout: Optional[float] = None,
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

    compiled_input = input_path
    temp_input: Optional[Path] = None
    raw = input_path.read_bytes()
    needs_utf8 = (
        raw.startswith(b"\xff\xfe")
        or raw.startswith(b"\xfe\xff")
        or raw.startswith(b"\xef\xbb\xbf")
    )
    if not needs_utf8:
        try:
            raw.decode("utf-8")
        except UnicodeError:
            needs_utf8 = True
    if needs_utf8:
        fd, tmp_name = tempfile.mkstemp(suffix=".fscss", dir=str(input_path.parent))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(_read_text_normalized(input_path))
        temp_input = Path(tmp_name)
        compiled_input = temp_input

    try:
        result = subprocess.run(
            [node, str(bin_path), str(compiled_input), str(output_path)],
            cwd=str(workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
            timeout=timeout,
        )
        return result.stdout or ""
    except subprocess.TimeoutExpired as e:
        out = e.stdout or e.stderr
        if out:
            msg = out.decode(errors="replace") if isinstance(out, bytes) else out
        else:
            msg = str(e)
        raise RuntimeError(f"Compilation timed out: {msg}".strip()) from e
    except subprocess.CalledProcessError as e:
        msg = e.stdout or e.stderr or str(e)
        raise RuntimeError(msg.strip()) from e
    finally:
        if temp_input is not None:
            try:
                temp_input.unlink()
            except OSError:
                pass


def compile_string(
    source: str,
    *,
    input_dir: Union[str, Path] = ".",
    output_path: Optional[Union[str, Path]] = None,
    timeout: Optional[float] = None,
) -> str:
    """Compile FSCSS source string to CSS string.

    If output_path is not provided, compiled CSS is returned as a string.
    """
    input_dir = Path(input_dir).resolve()
    input_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(suffix=".fscss", dir=str(input_dir))
    tmp_in = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(source)
        if output_path is None:
            with tempfile.TemporaryDirectory() as td:
                tmp_out = Path(td) / "tmp.css"
                compile_file(tmp_in, tmp_out, cwd=input_dir, timeout=timeout)
                return _read_text_normalized(tmp_out) if tmp_out.exists() else ""
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        compile_file(tmp_in, output_path, cwd=input_dir, timeout=timeout)
        return _read_text_normalized(output_path) if output_path.exists() else ""
    finally:
        try:
            tmp_in.unlink()
        except OSError:
            pass


compile = compile_file
