from types import SimpleNamespace

from fscss import environment


def test_parse_node_version():
    assert environment.parse_node_version("v20.11.1") == (20, 11, 1)
    assert environment.parse_node_version("20.0.0") == (20, 0, 0)
    assert environment.parse_node_version("not a version") is None


def test_engine_path_points_at_vendor():
    assert environment.engine_path().name == "fscss.js"
    assert "_vendor" in environment.engine_path().parts


def test_detect_package_managers_orders_by_preference(monkeypatch):
    installed = {"winget", "scoop"}
    monkeypatch.setattr(
        environment.shutil,
        "which",
        lambda name: f"/bin/{name}" if name in installed else None,
    )
    assert environment.detect_package_managers("Windows") == ["winget", "scoop"]


def test_node_version_reads_subprocess(monkeypatch):
    monkeypatch.setattr(
        environment.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="v21.4.2\n"),
    )
    assert environment.node_version("node") == (21, 4, 2)


def _node_check(checks):
    return next(c for c in checks if c.name == "Node.js")


def test_check_all_missing_node(monkeypatch):
    monkeypatch.setattr(environment, "find_node", lambda: None)
    checks = environment.check_all()
    assert _node_check(checks).status == "fail"


def test_check_all_old_node(monkeypatch):
    monkeypatch.setattr(environment, "find_node", lambda: "node")
    monkeypatch.setattr(environment, "node_version", lambda node=None: (18, 0, 0))
    checks = environment.check_all()
    assert _node_check(checks).status == "fail"
    assert "need 20+" in _node_check(checks).detail


def test_check_all_good_node(monkeypatch):
    monkeypatch.setattr(environment, "find_node", lambda: "node")
    monkeypatch.setattr(environment, "node_version", lambda node=None: (20, 1, 0))
    checks = environment.check_all()
    assert _node_check(checks).status == "ok"
