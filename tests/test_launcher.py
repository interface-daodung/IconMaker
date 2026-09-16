"""Test tool Build Launcher: sanitize tên, validate, lệnh build, cài icon."""

from pathlib import Path

import pytest

from service import launcher
from tools.launcher_tool import controller


def test_sanitize_launcher_name_ok():
    assert launcher.sanitize_launcher_name("  MyServer ") == "MyServer"


def test_sanitize_launcher_name_rejects_blank_and_bad_chars():
    with pytest.raises(ValueError):
        launcher.sanitize_launcher_name("   ")
    with pytest.raises(ValueError):
        launcher.sanitize_launcher_name("a/b")


def test_project_clean_name_mirrors_ps1():
    assert launcher.project_clean_name("My Server!") == "MyServer"
    assert launcher.project_clean_name("9lives") == "App_9lives"
    assert launcher.project_clean_name("!!!") == "ServerLauncher"


def test_validate_server_dir_ok_and_missing(tmp_path):
    assert launcher.validate_server_dir(tmp_path).is_dir()
    with pytest.raises(FileNotFoundError):
        launcher.validate_server_dir(tmp_path / "khong-co")
    with pytest.raises(ValueError):
        launcher.validate_server_dir("  ")


def test_install_build_icon_names_after_app(tmp_path, monkeypatch):
    monkeypatch.setenv("ICONMAKER_ICON_STORE", str(tmp_path / "store"))
    src = tmp_path / "raw.ico"
    src.write_bytes(b"fake-ico-bytes")
    dest = launcher.install_build_icon(src, "MyServer")
    assert dest == tmp_path / "store" / "MyServer.ico"
    assert dest.read_bytes() == b"fake-ico-bytes"


def test_install_build_icon_keeps_original_when_name_invalid(tmp_path, monkeypatch):
    monkeypatch.setenv("ICONMAKER_ICON_STORE", str(tmp_path / "store"))
    src = tmp_path / "raw.ico"
    src.write_bytes(b"fake-ico-bytes")
    dest = launcher.install_build_icon(src, "a/b")
    assert dest == tmp_path / "store" / "raw.ico"


def test_build_command_carries_all_args(tmp_path):
    cmd = launcher.build_command(
        tmp_path / "srv", "MyServer", tmp_path / "i.ico", tmp_path / "out", "framework"
    )
    assert cmd[:4] == ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"]
    assert "-ServerDir" in cmd and str(tmp_path / "srv") in cmd
    assert "-Name" in cmd and "MyServer" in cmd
    assert "-Icon" in cmd and "-OutDir" in cmd and "-Mode" in cmd
    with pytest.raises(ValueError):
        launcher.build_command("srv", "N", "i.ico", mode="sieu-toc")


def test_run_build_installs_icon_then_runs_ps1(tmp_path, monkeypatch):
    server = tmp_path / "srv"
    server.mkdir()
    icon = tmp_path / "raw.ico"
    icon.write_bytes(b"fake-ico-bytes")
    monkeypatch.setenv("ICONMAKER_ICON_STORE", str(tmp_path / "store"))
    seen: dict = {}

    class FakeResult:
        returncode = 0
        stdout = b""
        stderr = b""

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        exe = tmp_path / "out" / "MyServer.exe"
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_bytes(b"fake-exe")
        return FakeResult()

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)
    exe = launcher.run_build(server, icon, "MyServer", tmp_path / "out")
    assert exe == str(tmp_path / "out" / "MyServer.exe")
    assert (tmp_path / "store" / "MyServer.ico").is_file()
    assert "-ServerDir" in seen["cmd"]


def test_run_build_raises_when_ps1_fails(tmp_path, monkeypatch):
    server = tmp_path / "srv"
    server.mkdir()
    icon = tmp_path / "raw.ico"
    icon.write_bytes(b"fake-ico-bytes")
    monkeypatch.setenv("ICONMAKER_ICON_STORE", str(tmp_path / "store"))

    class FakeResult:
        returncode = 1
        stdout = b""
        stderr = "boom".encode()

    monkeypatch.setattr(
        launcher.subprocess, "run", lambda cmd, **kwargs: FakeResult()
    )
    with pytest.raises(RuntimeError):
        launcher.run_build(server, icon, "MyServer", tmp_path / "out")


def test_controller_parse_name_blank_falls_back_to_folder():
    assert controller.parse_launcher_name("  ", r"C:\Users\inter\Project\Demo") == "Demo"
    assert controller.parse_launcher_name("My App") == "My App"
    with pytest.raises(ValueError):
        controller.parse_launcher_name(None, None)


def test_controller_default_server_root_is_project():
    assert controller.default_server_root() == str(launcher.DEFAULT_SERVER_ROOT)


def test_controller_run_build_forwards(monkeypatch):
    seen: dict = {}

    def fake_run_build(server, icon, name, out_dir=None, mode="framework", on_output=None):
        seen.update(server=server, icon=icon, name=name, on_output=on_output)
        return "out.exe"

    monkeypatch.setattr(launcher, "run_build", fake_run_build)
    assert controller.run_build("srv", "i.ico", "N") == "out.exe"
    assert seen == {"server": "srv", "icon": "i.ico", "name": "N", "on_output": None}


def test_hidden_popen_kwargs_hides_console():
    kwargs = launcher._hidden_popen_kwargs()
    import subprocess
    import sys

    if sys.platform == "win32":
        assert kwargs["creationflags"] == subprocess.CREATE_NO_WINDOW
        assert kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW
    else:
        assert kwargs == {}


def test_stream_command_calls_back_per_line(monkeypatch):
    import io
    import subprocess

    lines: list[str] = []
    seen: dict = {}

    class FakeProc:
        stdout = io.StringIO("dong 1\r\ndong 2\n")

        def wait(self):
            return 0

    def fake_popen(cmd, **kwargs):
        seen.update(kwargs)
        assert kwargs.get("stdout") == subprocess.PIPE
        return FakeProc()

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)
    assert launcher.stream_command(["dummy"], lines.append) == 0
    assert lines == ["dong 1", "dong 2"]
    import sys

    if sys.platform == "win32":
        assert seen["creationflags"] == subprocess.CREATE_NO_WINDOW
        assert "startupinfo" in seen


def test_run_build_streams_log_when_callback(tmp_path, monkeypatch):
    import io

    server = tmp_path / "srv"
    server.mkdir()
    icon = tmp_path / "raw.ico"
    icon.write_bytes(b"fake-ico-bytes")
    monkeypatch.setenv("ICONMAKER_ICON_STORE", str(tmp_path / "store"))
    logged: list[str] = []

    class FakeProc:
        stdout = io.StringIO("build ok\n")

        def wait(self):
            exe = tmp_path / "out" / "MyServer.exe"
            exe.parent.mkdir(parents=True, exist_ok=True)
            exe.write_bytes(b"fake-exe")
            return 0

    monkeypatch.setattr(
        launcher.subprocess, "Popen", lambda cmd, **kwargs: FakeProc()
    )
    exe = launcher.run_build(
        server, icon, "MyServer", tmp_path / "out", on_output=logged.append
    )
    assert exe == str(tmp_path / "out" / "MyServer.exe")
    assert logged == ["build ok"]
