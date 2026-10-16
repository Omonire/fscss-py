"""Framework integrations for FSCSS.

These helpers compile .fscss files to .css at startup (and optionally watch
for changes during development). They have no hard dependency on any web
framework - each helper is written defensively so importing this module never
requires Flask/Django/etc.
"""

import os
import time
import threading
from pathlib import Path
from typing import Iterable, Optional, Union

from .core import compile_file

__all__ = ["compile_dir", "iter_fscss", "watch_dir", "init_flask", "init_django"]

PathLike = Union[str, Path]


def iter_fscss(directory: PathLike, recursive: bool = True) -> Iterable[Path]:
    """Yield all .fscss files under ``directory``."""
    root = Path(directory)
    pattern = "**/*.fscss" if recursive else "*.fscss"
    return sorted(root.glob(pattern))


def compile_dir(directory: PathLike, recursive: bool = True) -> list:
    """Compile every .fscss file in ``directory`` to a sibling .css file.

    Returns a list of (input, output) tuples that were compiled.
    """
    compiled = []
    for src in iter_fscss(directory, recursive=recursive):
        out = src.with_suffix(".css")
        compile_file(src, out)
        compiled.append((src, out))
    return compiled


def watch_dir(directory: PathLike, interval: float = 1.0, callback=None) -> threading.Thread:
    """Watch ``directory`` for .fscss changes and recompile in a daemon thread.

    Returns the running thread.
    """
    root = Path(directory)
    mtimes = {}

    def _snapshot():
        snap = {}
        for src in iter_fscss(root):
            try:
                snap[src] = src.stat().st_mtime
            except OSError:
                pass
        return snap

    def _loop():
        mtimes.update(_snapshot())
        while True:
            time.sleep(interval)
            new = _snapshot()
            for src, mtime in new.items():
                if mtimes.get(src) != mtime:
                    out = src.with_suffix(".css")
                    try:
                        compile_file(src, out)
                        if callback:
                            callback(src, out)
                    except Exception as e:  # pragma: no cover - dev helper
                        print(f"[fscss] compile failed for {src}: {e}")
            mtimes.clear()
            mtimes.update(new)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread


def init_flask(
    app=None,
    *,
    directory: Optional[PathLike] = None,
    watch: Optional[bool] = None,
) -> None:
    """Compile FSCSS assets for a Flask app.

    Compiles ``app.static_folder`` (or ``directory``) on startup. When
    ``watch`` is True (default in debug mode), a background thread recompiles
    on change.

    Usage::

        from flask import Flask
        import fscss
        app = Flask(__name__)
        fscss.init_flask(app)
    """
    if directory is None:
        if app is not None and getattr(app, "static_folder", None):
            directory = app.static_folder
        else:
            directory = "static"

    if watch is None:
        watch = bool(app is not None and getattr(app, "debug", False))

    compile_dir(directory)
    if watch:
        watch_dir(directory)


def init_django(directory: Optional[PathLike] = None) -> None:
    """Compile FSCSS assets for a Django project.

    Call from an AppConfig.ready() or settings module. ``directory`` defaults
    to ``<BASE_DIR>/static`` when Django is configured.
    """
    if directory is None:
        try:
            from django.conf import settings  # type: ignore

            base = getattr(settings, "BASE_DIR", None)
            directory = Path(base) / "static" if base else "static"
        except Exception:
            directory = "static"
    compile_dir(directory)
