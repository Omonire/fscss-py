"""Install Node.js through the platform's package manager.

Only the commands below are ever executed. Installation is never automatic:
callers must confirm first (the CLI does this interactively).
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess

from .environment import detect_package_managers

__all__ = [
    "INSTALL_COMMANDS",
    "UnsupportedPackageManager",
    "detect_package_managers",
    "install_command",
    "run_install",
]


class UnsupportedPackageManager(ValueError):
    """Raised when a package manager has no known install command."""


INSTALL_COMMANDS = {
    "winget": [
        "winget",
        "install",
        "--id",
        "OpenJS.NodeJS.LTS",
        "-e",
        "--accept-package-agreements",
        "--accept-source-agreements",
    ],
    "choco": ["choco", "install", "nodejs-lts", "-y"],
    "scoop": ["scoop", "install", "nodejs-lts"],
    "brew": ["brew", "install", "node"],
    "apt": ["apt-get", "install", "-y", "nodejs"],
    "dnf": ["dnf", "install", "-y", "nodejs"],
    "pacman": ["pacman", "-S", "--noconfirm", "nodejs"],
    "zypper": ["zypper", "install", "-y", "nodejs"],
    "apk": ["apk", "add", "nodejs"],
}

_PLATFORM_MANAGERS = {
    "Windows": ["winget", "choco", "scoop"],
    "Darwin": ["brew"],
    "Linux": ["apt", "dnf", "pacman", "zypper", "apk"],
}


def install_command(pm: str, system: str | None = None) -> list[str]:
    """Return the command used to install Node.js with ``pm``."""
    if pm not in INSTALL_COMMANDS:
        raise UnsupportedPackageManager(f"No install command for package manager: {pm}")

    system = system or platform.system()
    allowed = _PLATFORM_MANAGERS.get(system)
    if allowed is not None and pm not in allowed:
        raise UnsupportedPackageManager(f"{pm} is not supported on {system}")

    command = list(INSTALL_COMMANDS[pm])
    if pm in ("apt", "dnf", "zypper") and _needs_sudo():
        command = ["sudo"] + command
    return command


def _needs_sudo() -> bool:
    geteuid = getattr(os, "geteuid", None)
    if not callable(geteuid) or geteuid() == 0:
        return False
    return shutil.which("sudo") is not None


def run_install(pm: str, system: str | None = None) -> int:
    """Run the package manager install command, inheriting the terminal.

    Inherited stdio lets ``sudo``/UAC prompts work normally.
    """
    command = install_command(pm, system=system)
    try:
        return subprocess.run(command).returncode
    except OSError as exc:
        raise UnsupportedPackageManager(f"Could not run {command[0]}: {exc}") from exc
