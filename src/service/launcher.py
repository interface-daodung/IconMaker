"""Build launcher tray (.exe) cho 1 thư mục server qua `launcher/build-launcher.ps1`.

Quy trình: validate thư mục server + tên launcher, copy icon đã chọn vào
thư viện icon ổn định của user (như tool Icon thư mục — Luật 8) rồi mới
gọi script build. Icon trong thư viện mang tên `<ten-launcher>.ico` để
dễ đối chiếu với file `.exe` đầu ra.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from core.paths import OUTPUT_ICONS, OUTPUT_LAUNCHER
from service import foldericon

DEFAULT_SERVER_ROOT = Path(r"C:\Users\inter\Project")
BUILD_MODES = ("framework", "standalone")
DEFAULT_MODE = "framework"

_INVALID_NAME_CHARS = set('<>:"/\\|?*')


def sanitize_launcher_name(name: str | Path | None) -> str:
    """Tên launcher hiển thị: cắt trắng đầu/cuối, cấm rỗng và ký tự Windows."""
    raw = str(name or "").strip()
    if not raw:
        raise ValueError("Hay nhap ten launcher (vd MyServer).")
    if any(ch in _INVALID_NAME_CHARS for ch in raw):
        raise ValueError(f"Ten launcher chua ky tu cam <>:\"/\\|?*: {raw!r}")
    if any(ord(ch) < 32 for ch in raw):
        raise ValueError(f"Ten launcher chua ky tu dieu khien: {raw!r}")
    return raw


def project_clean_name(name: str) -> str:
    """Ten project C# (giong build-launcher.ps1: chi giu chu/so/gach duoi)."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "", name)
    if not clean:
        return "ServerLauncher"
    if clean[0].isdigit():
        clean = f"App_{clean}"
    return clean


def validate_server_dir(server_dir: str | Path) -> Path:
    """Thu muc server phai ton tai va la thu muc, tra ve duong dan tuyet doi."""
    raw = str(server_dir or "").strip()
    if not raw:
        raise ValueError("Hay chon thu muc server (trong C:\\Users\\inter\\Project).")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Khong tim thay thu muc server: {path}")
    return path


def build_script_path() -> Path:
    """Duong dan tuyet doi toi launcher/build-launcher.ps1 (neo theo repo root)."""
    root = Path(__file__).resolve().parents[2]
    return root / "launcher" / "build-launcher.ps1"


def default_icon() -> Path | None:
    """ICO moi nhat trong output/icons (neo theo repo root), chua co thi None."""
    root = Path(__file__).resolve().parents[2]
    candidate = root / OUTPUT_ICONS
    if not candidate.is_dir():
        return None
    from core.file_utils import newest_file

    return newest_file(candidate, ".ico")


def install_build_icon(
    icon_path: str | Path,
    app_name: str,
    store_dir: str | Path | None = None,
) -> Path:
    """Copy icon vao thu vien on dinh, dat ten theo launcher (`<ten>.ico`).

    Ten launcher khong dat duoc thanh ten file thi giu ten goc cua icon.
    """
    try:
        new_name = foldericon.sanitize_icon_name(app_name)
    except ValueError:
        new_name = None
    return foldericon.install_icon(icon_path, store_dir, new_name)


def _hidden_popen_kwargs() -> dict:
    """Tham so an cua so console cua tien trinh con tren Windows.

    powershell.exe la console-app nen mac dinh tu bat 1 cua so console rieng
    (ke ca khi GUI chay bang pythonw) - dat CREATE_NO_WINDOW + SW_HIDE de
    log chi hien trong tab GUI, khong nhay console ngoai.
    """
    if sys.platform != "win32":
        return {}
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return {"startupinfo": startup, "creationflags": subprocess.CREATE_NO_WINDOW}


def stream_command(cmd: list[str], on_output: Callable[[str], None]) -> int:
    """Chay `cmd`, goi `on_output` voi tung dong log (stdout+stderr), tra ve ma thoat."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        bufsize=1,
        shell=False,
        **_hidden_popen_kwargs(),
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        on_output(line.rstrip("\r\n"))
    return proc.wait()


def build_command(
    server_dir: str | Path,
    app_name: str,
    icon_path: str | Path,
    out_dir: str | Path | None = None,
    mode: str = DEFAULT_MODE,
) -> list[str]:
    """Cau lenh powershell goi build-launcher.ps1 voi du tham so."""
    if mode not in BUILD_MODES:
        raise ValueError(f"Mode phai la mot trong {list(BUILD_MODES)}, nhan duoc {mode!r}")
    out = Path(out_dir) if out_dir else OUTPUT_LAUNCHER
    return [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(build_script_path()),
        "-ServerDir",
        str(server_dir),
        "-Name",
        app_name,
        "-Icon",
        str(icon_path),
        "-OutDir",
        str(out),
        "-Mode",
        mode,
    ]


def run_build(
    server_dir: str | Path,
    icon_path: str | Path | None,
    app_name: str | Path | None,
    out_dir: str | Path | None = None,
    mode: str = DEFAULT_MODE,
    on_output: Callable[[str], None] | None = None,
) -> str:
    """Validate -> cai icon vao thu vien -> chay build, tra ve duong dan .exe.

    - `icon_path` trong thi dung ICO moi nhat trong output/icons.
    - `app_name` trong thi lay ten thu muc server (giong build-launcher.ps1).
    - `on_output` (vd tab GUI) nhan tung dong log build theo thoi gian thuc;
      bo trong thi gom log va chi hien khi build loi (dung cho CLI).
    """
    server = validate_server_dir(server_dir)
    icon_src = str(icon_path or "").strip() if icon_path else ""
    if not icon_src:
        latest = default_icon()
        if latest is None:
            raise FileNotFoundError(
                f"Chua co ICO nao trong {OUTPUT_ICONS} - chay icons truoc hoac chon 1 file .ico."
            )
        icon_src = str(latest)
    name = sanitize_launcher_name(app_name) if str(app_name or "").strip() else server.name
    installed = install_build_icon(icon_src, name)
    cmd = build_command(server, name, installed, out_dir, mode)
    if on_output is None:
        result = subprocess.run(
            cmd, capture_output=True, check=False, shell=False, **_hidden_popen_kwargs()
        )
        returncode = result.returncode
        detail = (result.stdout + result.stderr).decode(errors="replace").strip()
    else:
        lines: list[str] = []

        def collect(line: str) -> None:
            lines.append(line)
            on_output(line)

        returncode = stream_command(cmd, collect)
        detail = "\n".join(lines).strip()
    if returncode != 0:
        raise RuntimeError(f"Build launcher that bai (ma {returncode}): {detail}")
    out = Path(out_dir) if out_dir else OUTPUT_LAUNCHER
    exe = out / f"{project_clean_name(name)}.exe"
    if not exe.is_file():
        resolved = Path(out).resolve() / f"{project_clean_name(name)}.exe"
        if not resolved.is_file():
            raise RuntimeError(f"Build xong nhung khong thay file: {exe}")
        return str(resolved)
    return str(exe)
