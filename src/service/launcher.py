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
USAGE = (
    "Dùng: python -m service.launcher <thu_muc_server> "
    "[--icon <file.ico>] [--name <ten>] [--out <dir>] [--mode framework|standalone]"
)

_INVALID_NAME_CHARS = set('<>:"/\\|?*')


def sanitize_launcher_name(name: str | Path | None) -> str:
    """Tên launcher hiển thị: cắt trắng đầu/cuối, cấm rỗng và ký tự Windows."""
    raw = str(name or "").strip()
    if not raw:
        raise ValueError("Hãy nhập tên launcher (vd MyServer).")
    if any(ch in _INVALID_NAME_CHARS for ch in raw):
        raise ValueError(f"Tên launcher chứa ký tự cấm <>:\"/\\|?*: {raw!r}")
    if any(ord(ch) < 32 for ch in raw):
        raise ValueError(f"Tên launcher chứa ký tự điều khiển: {raw!r}")
    return raw


def project_clean_name(name: str) -> str:
    """Tên project C# (giống build-launcher.ps1: chỉ giữ chữ/số/gạch dưới)."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "", name)
    if not clean:
        return "ServerLauncher"
    if clean[0].isdigit():
        clean = f"App_{clean}"
    return clean


def validate_server_dir(server_dir: str | Path) -> Path:
    """Thư mục server phải tồn tại và là thư mục, trả về đường dẫn tuyệt đối."""
    raw = str(server_dir or "").strip()
    if not raw:
        raise ValueError("Hãy chọn thư mục server (trong C:\\Users\\inter\\Project).")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục server: {path}")
    return path


def build_script_path() -> Path:
    """Đường dẫn tuyệt đối tới launcher/build-launcher.ps1 (neo theo repo root)."""
    root = Path(__file__).resolve().parents[2]
    return root / "launcher" / "build-launcher.ps1"


def default_icon() -> Path | None:
    """ICO mới nhất trong output/icons (neo theo repo root), chưa có thì None."""
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
    """Copy icon vào thư viện ổn định, đặt tên theo launcher (`<ten>.ico`).

    Tên launcher không đặt được thành tên file thì giữ tên gốc của icon.
    """
    try:
        new_name = foldericon.sanitize_icon_name(app_name)
    except ValueError:
        new_name = None
    return foldericon.install_icon(icon_path, store_dir, new_name)


def _hidden_popen_kwargs() -> dict:
    """Tham số ẩn cửa sổ console của tiến trình con trên Windows.

    powershell.exe là console-app nên mặc định tự bật 1 cửa sổ console riêng
    (kể cả khi GUI chạy bằng pythonw) — đặt CREATE_NO_WINDOW + SW_HIDE để
    log chỉ hiện trong tab GUI, không nháy console ngoài.
    """
    if sys.platform != "win32":
        return {}
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return {"startupinfo": startup, "creationflags": subprocess.CREATE_NO_WINDOW}


def stream_command(cmd: list[str], on_output: Callable[[str], None]) -> int:
    """Chạy `cmd`, gọi `on_output` với từng dòng log (stdout+stderr), trả về mã thoát."""
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
    """Câu lệnh powershell gọi build-launcher.ps1 với đủ tham số."""
    if mode not in BUILD_MODES:
        raise ValueError(f"Mode phải là một trong {list(BUILD_MODES)}, nhận được {mode!r}")
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
    """Validate → cài icon vào thư viện → chạy build, trả về đường dẫn .exe.

    - `icon_path` trống thì dùng ICO mới nhất trong output/icons.
    - `app_name` trống thì lấy tên thư mục server (giống build-launcher.ps1).
    - `on_output` (vd tab GUI) nhận từng dòng log build theo thời gian thực;
      bỏ trống thì gom log và chỉ hiện khi build lỗi (dùng cho CLI).
    """
    server = validate_server_dir(server_dir)
    icon_src = str(icon_path or "").strip() if icon_path else ""
    if not icon_src:
        latest = default_icon()
        if latest is None:
            raise FileNotFoundError(
                f"Chưa có ICO nào trong {OUTPUT_ICONS} — chạy icons trước hoặc chọn 1 file .ico."
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
        raise RuntimeError(f"Build launcher thất bại (mã {returncode}): {detail}")
    out = Path(out_dir) if out_dir else OUTPUT_LAUNCHER
    exe = out / f"{project_clean_name(name)}.exe"
    if not exe.is_file():
        resolved = Path(out).resolve() / f"{project_clean_name(name)}.exe"
        if not resolved.is_file():
            raise RuntimeError(f"Build xong nhưng không thấy file: {exe}")
        return str(resolved)
    return str(exe)


def main(argv: list[str] | None = None) -> int:
    """Entry point: python -m service.launcher <server> [--icon] [--name] [--out] [--mode]"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="replace")
    args = [a for a in list(sys.argv[1:] if argv is None else argv) if a]
    opts: dict[str, str] = {}
    rest: list[str] = []
    i = 0
    while i < len(args):
        if args[i] in ("--icon", "--name", "--out", "--mode") and i + 1 < len(args):
            opts[args[i]] = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    if len(rest) != 1:
        print(USAGE)
        return 2
    try:
        exe = run_build(
            rest[0],
            opts.get("--icon"),
            opts.get("--name"),
            opts.get("--out"),
            opts.get("--mode", DEFAULT_MODE),
        )
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    print(f"Launcher đã build: {exe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
