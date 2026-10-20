try:
    from importlib import metadata

    __version__ = metadata.version("fscss")
except Exception:
    __version__ = "0.1.0"

from .core import compile, compile_file, compile_string
from .integrations import (
    compile_dir,
    init_django,
    init_flask,
    iter_fscss,
    watch_dir,
)

__all__ = [
    "compile_string",
    "compile_file",
    "compile",
    "compile_dir",
    "iter_fscss",
    "watch_dir",
    "init_flask",
    "init_django",
    "__version__",
]
