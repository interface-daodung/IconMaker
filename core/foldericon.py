"""Đặt icon cho thư mục Windows qua file ẩn desktop.ini.

Quy tắc (Luật 8 trong AGENTS.md): đường dẫn ghi vào desktop.ini là đường dẫn
tuyệt đối, nên icon phải được copy vào THƯ VIỆN ICON ỔN ĐỊNH của user
(mac dinh `~/OneDrive/Pictures/Icon`) trước khi trỏ tới — không dùng icon
nam trong thu muc app, vi di chuyen app se hong icon.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

INI_NAME = "desktop.ini"
ICO_EXTENSIONS = {".ico"}


def icon_store_dir() -> Path:
    """Thu vu icon on dinh cua user, khong phu thuoc vi tri app.

    Thu tu uu tien: gia trị env ICONMAKER_ICON_STORE -> thu muc `Icon` đã tồn
    tại trong Pictures (OneDrive trước) -> `~/OneDrive/Pictures/Icon` (nếu có
    OneDrive) -> `~/Pictures/Icon`.
    """
    override = os.environ.get("ICONMAKER_ICON_STORE")
    if override:
        return Path(override)
    home = Path.home()
    candidates = [home / "OneDrive" / "Pictures" / "Icon", home / "Pictures" / "Icon"]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    if (home / "OneDrive").is_dir():
        return home / "OneDrive" / "Pictures" / "Icon"
    return home / "Pictures" / "Icon"


def install_icon(icon_path: str | Path, store_dir: str | Path | None = None) -> Path:
    """Copy file .ico vào thư viện icon, trả về đường dẫn đích đã cài.

    - Trung dung voi ban ghi cua thu vien: tai dung file cu (khong nhan ban).
    - Cung ten khac noi dung: them hau to ` (n)` de hong va file da tro toi.
    """
    src = Path(icon_path)
    if not src.is_file():
        raise FileNotFoundError(f"Không tìm thấy file icon: {src}")
    if src.suffix.lower() not in ICO_EXTENSIONS:
        raise ValueError(f"Icon phải là file .ico, nhận được '{src.suffix or 'không phần mở rộng'}'")
    store = Path(store_dir) if store_dir else icon_store_dir()
    store.mkdir(parents=True, exist_ok=True)

    data = src.read_bytes()
    base = store / src.name
    n = 1
    while True:
        dest = base if n == 1 else base.with_name(f"{base.stem} ({n}){base.suffix}")
        if not dest.exists():
            dest.write_bytes(data)
            return dest
        if dest.read_bytes() == data:
            return dest
        n += 1


def make_ini_content(icon_path: str | Path) -> str:
    """Nội dung desktop.ini trỏ icon tới `icon_path` (bỏ qua image index 0)."""
    resolved = Path(icon_path).resolve()
    return f"[.ShellClassInfo]\nIconResource={resolved},0\n"


def _run_attrib(*args: str) -> None:
    result = subprocess.run(
        ("attrib", *args), capture_output=True, check=False, shell=False
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).decode(errors="replace").strip()
        raise RuntimeError(f"attrib {' '.join(args)} thất bại (mã {result.returncode}): {detail}")


def refresh_explorer_cache() -> None:
    """Best-effort: bảo Explorer đọc lại bộ nhớ đệm icon/hiển thị."""
    if sys.platform != "win32":
        return
    subprocess.run(("ie4uinit.exe", "-show"), capture_output=True, check=False, shell=False)


def set_folder_icon(folder_path: str | Path, icon_path: str | Path) -> str:
    """Ghi desktop.ini (an) cho thư mục và đặt thuộc tính Windows cần thiết.

    - `icon_path` phai la du dan tuyet doi ON DINH (dung install_icon truoc).
    - desktop.ini cu (neu co) duoc go bo -h -s -r de ghi de duoc.
    - Tra ve du dan desktop.ini da ghi.
    """
    folder = Path(folder_path).resolve()
    icon = Path(icon_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {folder}")
    if not icon.is_file():
        raise FileNotFoundError(f"Không tìm thấy file icon: {icon}")

    ini = folder / INI_NAME
    if ini.exists():
        _run_attrib("-h", "-s", "-r", str(ini))
    ini.write_text(make_ini_content(icon), encoding="utf-8")
    _run_attrib("+h", "+s", str(ini))
    _run_attrib("+r", str(folder))
    refresh_explorer_cache()
    return str(ini)


def main(argv: list[str] | None = None) -> int:
    """Entry point: python -m iconmaker.foldericon <icon.ico> <thu_muc> [--store <dir>]"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="replace")
    args = list(sys.argv[1:] if argv is None else argv)
    store: str | None = None
    if "--store" in args:
        idx = args.index("--store")
        if idx + 1 >= len(args):
            print("Lỗi: --store cần đường dẫn kèm theo", file=sys.stderr)
            return 2
        store = args[idx + 1]
        del args[idx : idx + 2]
    if len(args) != 2:
        print("Dùng: python -m iconmaker.foldericon <icon.ico> <thu_muc> [--store <dir>]")
        return 2
    try:
        installed = install_icon(args[0], store)
        ini = set_folder_icon(args[1], installed)
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    print(f"Icon đã cài: {installed}\ndesktop.ini: {ini}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
