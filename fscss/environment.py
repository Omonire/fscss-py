"""Environment detection for the FSCSS Python wrapper.

Everything here is read-only: it answers "can this machine run fscss?" without
installing anything. See :mod:`fscss.node_install` for the install step.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "MIN_NODE",
    "Check",
    "detect_package_managers",
    "engine_path",
    "find_node",
    "node_version",
    "check_all",
]

MIN_NODE = (20, 0, 0)
MIN_PYTHON = (3, 7, 0)

_PM_PREFERENCE = {
    "Windows": ["winget", "choco", "scoop"],
    "Darwin": ["brew"],
    "Linux": ["apt", "dnf", "pacman", "zypper", "apk"],
}


@dataclass
class Check:
    """Result of a single environment check."""

    name: str
    status: str  # "ok" | "warn" | "fail"
    detail: str
    hint: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def engine_path() -> Path:
    """Return the path to the vendored xfscss entry script."""
    return Path(__file__).parent / "_vendor" / "xfscss" / "bin" / "fscss.js"


def _node_candidates() -> list[Path]:
    """Common install locations to check after a package manager runs.

    The current process may not see an updated PATH, so look in the places the
    supported package managers use.
    """
    home = Path.home()
    system = platform.system()
    candidates: list[Path] = []
    if system == "Windows":
        for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                candidates.append(Path(base) / "nodejs" / "node.exe")
        candidates.append(home / "scoop" / "shims" / "node.exe")
        candidates.append(Path("C:/ProgramData/chocolatey/bin/node.exe"))
    elif system == "Darwin":
        candidates.extend([Path("/opt/homebrew/bin/node"), Path("/usr/local/bin/node")])
    else:
        candidates.extend([Path("/usr/bin/node"), Path("/usr/local/bin/node")])
    return candidates


def find_node() -> str | None:
    """Locate a Node executable.

    Order: ``FSCSS_NODE`` override, ``PATH`` (``node`` then ``nodejs``), then
    well-known package-manager install locations.
    """
    override = os.environ.get("FSCSS_NODE")
    if override:
        return override
    for name in ("node", "nodejs"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in _node_candidates():
        if candidate.exists():
            return str(candidate)
    return None


def parse_node_version(output: str) -> tuple[int, int, int] | None:
    """Parse ``node --version`` output (e.g. ``v20.11.1``)."""
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", output or "")
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def node_version(node: str | None = None) -> tuple[int, int, int] | None:
    """Return the version of ``node`` (or the discovered one) as a tuple."""
    node = node or find_node()
    if not node:
        return None
    try:
        result = subprocess.run(
            [node, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_node_version(result.stdout or "")


def format_version(version: tuple[int, int, int] | None) -> str:
    if not version:
        return "unknown"
    return ".".join(str(part) for part in version)


def detect_package_managers(system: str | None = None) -> list[str]:
    """Return available package managers, ordered by platform preference."""
    system = system or platform.system()
    available = []
    for name in _PM_PREFERENCE.get(system, []):
        if shutil.which(name):
            available.append(name)
    return available


def _write_access_check() -> Check:
    cwd = os.getcwd()
    try:
        with tempfile.NamedTemporaryFile(dir=cwd, delete=True):
            pass
    except OSError as exc:
        return Check(
            "Write access",
            "fail",
            f"{cwd}: {exc}",
            "Run fscss from a directory you can write to, or use an explicit output path.",
        )
    return Check("Write access", "ok", cwd)


def check_all() -> list[Check]:
    """Run every environment check and return the results."""
    checks: list[Check] = []

    py_version = tuple(sys.version_info[:3])
    checks.append(
        Check(
            "Python",
            "ok" if py_version >= MIN_PYTHON else "fail",
            f"{platform.python_version()} ({sys.executable})",
            "Install Python 3.7 or newer from https://python.org/.",
        )
    )

    checks.append(Check("Platform", "ok", f"{platform.system()} {platform.machine()}"))

    engine = engine_path()
    checks.append(
        Check(
            "FSCSS engine",
            "ok" if engine.exists() else "fail",
            str(engine),
            "Reinstall the fscss package; the vendored compiler is missing.",
        )
    )

    node = find_node()
    if not node:
        checks.append(
            Check(
                "Node.js",
                "fail",
                "not found",
                "Run `fscss init` to install Node.js 20+.",
            )
        )
    else:
        version = node_version(node)
        if version is None:
            checks.append(
                Check(
                    "Node.js",
                    "fail",
                    f"{node} (could not read version)",
                    "Check that `node --version` works, then run `fscss doctor` again.",
                )
            )
        elif version < MIN_NODE:
            checks.append(
                Check(
                    "Node.js",
                    "fail",
                    f"{node} (v{format_version(version)}; need 20+)",
                    "Run `fscss init` to install a supported Node.js.",
                )
            )
        else:
            checks.append(Check("Node.js", "ok", f"{node} (v{format_version(version)})"))

    checks.append(_write_access_check())

    managers = detect_package_managers()
    checks.append(
        Check(
            "Package managers",
            "ok" if managers else "warn",
            ", ".join(managers) if managers else "none detected",
            "Install winget/brew/apt or install Node.js manually from https://nodejs.org/.",
        )
    )

    return checks
