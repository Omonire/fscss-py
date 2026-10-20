import subprocess
import sys
import tempfile
from pathlib import Path


def test_cli_basic():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        src = d / "a.fscss"
        src.write_text("body{bg:#000}")
        out = d / "a.css"
        r = subprocess.run(
            [sys.executable, "-m", "fscss", str(src), str(out)],
            cwd=td,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert r.returncode == 0
        assert out.exists()


def test_cli_version():
    r = subprocess.run(
        [sys.executable, "-m", "fscss", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert r.returncode == 0
    assert "fscss" in r.stdout


def test_cli_no_args():
    r = subprocess.run(
        [sys.executable, "-m", "fscss"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert r.returncode == 1

