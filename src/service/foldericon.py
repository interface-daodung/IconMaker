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
_INVALID_NAME_CHARS = set('<>:"/\\|?*')


def sanitize_icon_name(name: str | Path) -> str:
    """Chuẩn hoá tên file .ico do user nhập, luôn có hậu tố .ico.

    - Cắt khoảng trắng đầu/cuối, tự thêm `.ico` nếu thiếu.
    - Từ chối tên rỗng, `.`, `..`, chứa ký tự cấm Windows hoặc
      kết thúc bằng dấu chấm/khoảng trắng (Explorer cắt ngầm).
    """
    raw = str(name).strip()
    if not raw:
        raise ValueError("Tên icon mới không được để trống.")
    candidate = Path(raw)
    if candidate.name != raw or raw in (".", ".."):
        raise ValueError(f"Tên icon không hợp lệ: {raw!r}")
    stem = candidate.stem.strip().rstrip(".")
    suffix = candidate.suffix.lower()
    if suffix and suffix != ".ico":
        raise ValueError(f"Tên icon phải có đuôi .ico, nhận được '{candidate.suffix}'")
    if not stem or stem in (".", ".."):
        raise ValueError(f"Tên icon không hợp lệ: {raw!r}")
    if any(ch in _INVALID_NAME_CHARS for ch in stem):
        raise ValueError(f"Tên icon chứa ký tự cấm <>:\"/\\|?*: {stem!r}")
    if any(ord(ch) < 32 for ch in stem):
        raise ValueError(f"Tên icon chứa ký tự điều khiển: {stem!r}")
    return f"{stem}.ico"


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


def install_icon(
    icon_path: str | Path,
    store_dir: str | Path | None = None,
    new_name: str | None = None,
) -> Path:
    """Copy file .ico vào thư viện icon, trả về đường dẫn đích đã cài.

    - Trung dung voi ban ghi cua thu vien: tai dung file cu (khong nhan ban).
    - Cung ten khac noi dung: them hau to ` (n)` de hong va file da tro toi.
    - `new_name` (tùy chọn): tên mới do user đặt, chuẩn hoá qua
      `sanitize_icon_name` trước khi lưu (để trống/None = giữ tên gốc).
    """
    src = Path(icon_path)
    if not src.is_file():
        raise FileNotFoundError(f"Không tìm thấy file icon: {src}")
    if src.suffix.lower() not in ICO_EXTENSIONS:
        raise ValueError(f"Icon phải là file .ico, nhận được '{src.suffix or 'không phần mở rộng'}'")
    store = Path(store_dir) if store_dir else icon_store_dir()
    store.mkdir(parents=True, exist_ok=True)

    data = src.read_bytes()
    filename = sanitize_icon_name(new_name) if new_name and str(new_name).strip() else src.name
    base = store / filename
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
    """Entry point: python -m core.foldericon [icon.ico] <thu_muc> [--store <dir>] [--name <ten>]"""
    from core.file_utils import newest_file
    from core.paths import OUTPUT_ICONS

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="replace")
    args = [a for a in list(sys.argv[1:] if argv is None else argv) if a]
    store: str | None = None
    new_name: str | None = None
    for flag, slot in (("--store", "store"), ("--name", "new_name")):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 >= len(args):
                print(f"Lỗi: {flag} cần giá trị kèm theo", file=sys.stderr)
                return 2
            if slot == "store":
                store = args[idx + 1]
            else:
                new_name = args[idx + 1]
            del args[idx : idx + 2]
    if len(args) == 2:
        icon_arg, folder = args
    elif len(args) == 1:
        latest = newest_file(OUTPUT_ICONS, ".ico")
        if latest is None:
            print(
                f"Lỗi: chưa có ICO nào trong {OUTPUT_ICONS}"
                " — chạy icons trước hoặc truyền <icon.ico>",
                file=sys.stderr,
            )
            return 1
        icon_arg, folder = str(latest), args[0]
    else:
        print("Dùng: python -m core.foldericon [icon.ico] <thu_muc> [--store <dir>] [--name <ten>]")
        return 2
    try:
        installed = install_icon(icon_arg, store, new_name)
        ini = set_folder_icon(folder, installed)
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    print(f"Icon đã cài: {installed}\ndesktop.ini: {ini}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
