import tempfile
from pathlib import Path

import pytest

import fscss
from fscss import core


def test_compile_string_basic():
    css = fscss.compile_string("body{bg:red}")
    assert "red" in css


def test_compile_string_to_output():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out.css"
        css = fscss.compile_string("h1{c:blue}", output_path=out)
        assert out.exists()
        assert "blue" in css


def test_compile_file():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        src = d / "t.fscss"
        src.write_text("h1{c:blue}")
        out = d / "t.css"
        fscss.compile_file(src, out)
        assert out.exists()
        assert "blue" in out.read_text()


def test_compile_alias():
    assert fscss.compile is fscss.compile_file


def test_compile_file_missing_node(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "_node_cache", None)
    monkeypatch.setattr(core.shutil, "which", lambda name: None)
    src = tmp_path / "a.fscss"
    src.write_text("body{bg:red}")
    with pytest.raises(RuntimeError, match="Node.js is required"):
        fscss.compile_file(src, tmp_path / "a.css")


def test_compile_file_invalid_syntax():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        src = d / "bad.fscss"
        src.write_text("@import(nonexistent_file_xyz as x)")
        out = d / "bad.css"
        out.write_text("")
        # Should not raise; compiler reports failure inline
        fscss.compile_file(src, out)
