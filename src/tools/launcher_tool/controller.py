"""Controller Build Launcher: gia tri mac dinh + goi service.launcher."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from core.paths import OUTPUT_ICONS
from service import launcher


def default_server_root() -> str:
    """Thu muc dialog chon server mo san (theo yeu cau: C:\\Users\\inter\\Project)."""
    if launcher.DEFAULT_SERVER_ROOT.is_dir():
        return str(launcher.DEFAULT_SERVER_ROOT)
    return str(Path.home())


def icons_default_dir() -> str:
    """Thu muc output/icons tuyet doi de dialog chon icon mo thang vao."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / OUTPUT_ICONS
    if candidate.is_dir():
        return str(candidate)
    fallback = Path(OUTPUT_ICONS).resolve()
    return str(fallback) if fallback.is_dir() else str(candidate)


def suggest_name(server_dir: str | None) -> str:
    """Goi y ten launcher = ten thu muc server (giong build-launcher.ps1)."""
    raw = str(server_dir or "").strip()
    if not raw:
        return ""
    return Path(raw).name


def parse_launcher_name(raw: str | None, server_dir: str | None = None) -> str:
    """Ten user nhap (rong = lay ten thu muc server), chuan hoa qua service."""
    if raw is None or not str(raw).strip():
        fallback = suggest_name(server_dir)
        if not fallback:
            raise ValueError("Hay nhap ten launcher (vd MyServer).")
        return launcher.sanitize_launcher_name(fallback)
    return launcher.sanitize_launcher_name(raw)


def run_build(
    server_dir: str,
    icon_path: str | None,
    app_name: str | None,
    on_output: Callable[[str], None] | None = None,
) -> str:
    """Cai icon vao thu vien roi build launcher, tra ve duong dan .exe."""
    return launcher.run_build(server_dir, icon_path, app_name, on_output=on_output)
