import pytest

from fscss import node_install


def test_winget_command_targets_node_lts():
    command = node_install.install_command("winget", system="Windows")
    assert "OpenJS.NodeJS.LTS" in command


def test_brew_command():
    assert node_install.install_command("brew", system="Darwin") == ["brew", "install", "node"]


def test_rejects_unknown_manager():
    with pytest.raises(node_install.UnsupportedPackageManager):
        node_install.install_command("does-not-exist", system="Linux")


def test_rejects_wrong_platform():
    with pytest.raises(node_install.UnsupportedPackageManager):
        node_install.install_command("winget", system="Linux")


def test_run_install_uses_command(monkeypatch):
    calls = []
    monkeypatch.setattr(
        node_install.subprocess,
        "run",
        lambda command: calls.append(command) or type("R", (), {"returncode": 0})(),
    )
    assert node_install.run_install("brew", system="Darwin") == 0
    assert calls == [["brew", "install", "node"]]
