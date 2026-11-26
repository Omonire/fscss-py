import json

from fscss import cli
from fscss.environment import Check


def _ok_checks():
    return [
        Check("Python", "ok", "3.12"),
        Check("Node.js", "ok", "node (v20.0.0)"),
    ]


def test_version_command(capsys):
    assert cli.main(["version"]) == 0
    assert "fscss" in capsys.readouterr().out


def test_env_json(capsys):
    assert cli.main(["env", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert {"fscss", "python", "platform", "node_version", "engine"} <= set(payload)


def test_doctor_check_ok(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_all", _ok_checks)
    assert cli.main(["doctor", "--check"]) == 0


def test_doctor_check_fails(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "check_all",
        lambda: [Check("Node.js", "fail", "missing", "run fscss init")],
    )
    assert cli.main(["doctor", "--check"]) == 1


def test_doctor_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_all", _ok_checks)
    assert cli.main(["doctor", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["name"] == "Python"


def test_completion(capsys):
    assert cli.main(["completion", "bash"]) == 0
    assert "fscss" in capsys.readouterr().out


def test_report_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_all", _ok_checks)
    assert cli.main(["report", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["xfscss"] == "1.2.6"


def test_clean_only_removes_sibling_css(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.fscss").write_text("body{bg:red}", encoding="utf-8")
    (tmp_path / "a.css").write_text("old", encoding="utf-8")
    (tmp_path / "keep.css").write_text("hand-written", encoding="utf-8")

    assert cli.main(["clean", str(tmp_path)]) == 0
    assert not (tmp_path / "a.css").exists()
    assert (tmp_path / "keep.css").exists()


def test_clean_dry_run(tmp_path, capsys):
    (tmp_path / "a.fscss").write_text("body{bg:red}", encoding="utf-8")
    (tmp_path / "a.css").write_text("old", encoding="utf-8")

    assert cli.main(["clean", str(tmp_path), "--dry-run"]) == 0
    assert (tmp_path / "a.css").exists()
    assert "Would delete" in capsys.readouterr().out


def test_init_ready_skips_install(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "check_all", _ok_checks)
    calls = []
    monkeypatch.setattr(cli, "run_install", lambda pm: calls.append(pm) or 0)

    assert cli.main(["init", "--yes", "--no-config"]) == 0
    assert calls == []


def test_init_missing_node_without_manager(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "check_all",
        lambda: [Check("Node.js", "fail", "missing")],
    )
    monkeypatch.setattr(cli, "detect_package_managers", lambda: [])

    assert cli.main(["init", "--yes", "--no-config"]) == 2


def test_init_installs_with_yes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    results = [
        [Check("Node.js", "fail", "missing")],
        [Check("Node.js", "ok", "node (v20.0.0)")],
    ]
    monkeypatch.setattr(cli, "check_all", lambda: results.pop(0))
    monkeypatch.setattr(cli, "detect_package_managers", lambda: ["winget"])
    installed = []
    monkeypatch.setattr(cli, "run_install", lambda pm: installed.append(pm) or 0)
    monkeypatch.setattr(cli, "install_command", lambda pm: ["winget", "install", "node"])

    assert cli.main(["init", "--yes", "--no-config"]) == 0
    assert installed == ["winget"]
