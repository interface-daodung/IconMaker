"""Controller Build Launcher: giá trị mặc định + gọi service.launcher."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from core.paths import OUTPUT_ICONS
from service import launcher


def default_server_root() -> str:
    """Thư mục dialog chọn server mở sẵn (theo yêu cầu: C:\\Users\\inter\\Project)."""
    if launcher.DEFAULT_SERVER_ROOT.is_dir():
        return str(launcher.DEFAULT_SERVER_ROOT)
    return str(Path.home())


def icons_default_dir() -> str:
    """Thư mục output/icons tuyệt đối để dialog chọn icon mở thẳng vào."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / OUTPUT_ICONS
    if candidate.is_dir():
        return str(candidate)
    fallback = Path(OUTPUT_ICONS).resolve()
    return str(fallback) if fallback.is_dir() else str(candidate)


def suggest_name(server_dir: str | None) -> str:
    """Gợi ý tên launcher = tên thư mục server (giống build-launcher.ps1)."""
    raw = str(server_dir or "").strip()
    if not raw:
        return ""
    return Path(raw).name


def parse_launcher_name(raw: str | None, server_dir: str | None = None) -> str:
    """Tên user nhập (rỗng = lấy tên thư mục server), chuẩn hoá qua service."""
    if raw is None or not str(raw).strip():
        fallback = suggest_name(server_dir)
        if not fallback:
            raise ValueError("Hãy nhập tên launcher (vd MyServer).")
        return launcher.sanitize_launcher_name(fallback)
    return launcher.sanitize_launcher_name(raw)


def run_build(
    server_dir: str,
    icon_path: str | None,
    app_name: str | None,
    on_output: Callable[[str], None] | None = None,
) -> str:
    """Cài icon vào thư viện rồi build launcher, trả về đường dẫn .exe."""
    return launcher.run_build(server_dir, icon_path, app_name, on_output=on_output)
