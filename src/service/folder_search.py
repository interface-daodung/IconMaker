"""Tìm hàng loạt thư mục theo tên chính xác (cú pháp `*<tên>`).

Quy tắc (tab Icon thư mục):
- Đầu vào `*<tên>` = tìm mọi thư mục có tên đúng bằng `<tên>`
  (không phân biệt hoa/thường).
- Mặc định chỉ quét `Path.home()` (`C:\\Users\\<user>`).
- Tùy chọn quét thêm các ổ đĩa khác (checkbox từng ổ ở GUI).
- Luôn bỏ qua cây %TEMP%/%TMP%/%AppData%/%LocalAppData%.
- Dưới home: bỏ qua mọi nhánh có phần bắt đầu bằng `.`
  (`.cache`, `.vscode`, ...). Ngoài home (ổ khác): `.` được phép.
- Không đi xuyên symlink/junction, bỏ qua thư mục ẩn/system (Windows).
"""

from __future__ import annotations

import os
import string
from collections.abc import Iterable
from pathlib import Path

_INVALID_NAME_CHARS = set('<>:"/\\|?*')


def is_batch_input(raw: str | None) -> bool:
    """True khi đầu vào là cú pháp hàng loạt `*<tên>`."""
    return str(raw or "").strip().startswith("*")


def parse_batch_name(raw: str | None) -> str:
    """Tách tên thư mục từ `*<tên>`, raise ValueError khi rỗng/sai."""
    text = str(raw or "").strip()
    if not text.startswith("*"):
        raise ValueError(f"Không phải cú pháp hàng loạt '*<tên>': {raw!r}")
    name = text[1:].strip()
    if not name or name in (".", ".."):
        raise ValueError("Tên sau '*' không được để trống.")
    if not name.strip(" ."):
        raise ValueError("Tên sau '*' không được toàn dấu chấm/khoảng trắng.")
    if "/" in name or "\\" in name:
        raise ValueError(f"Tên thư mục không chứa dấu / hoặc \\: {name!r}")
    if any(ch in _INVALID_NAME_CHARS for ch in name):
        raise ValueError(f"Tên thư mục chứa ký tự cấm <>:\"/\\|?*: {name!r}")
    if any(ord(ch) < 32 for ch in name):
        raise ValueError(f"Tên thư mục chứa ký tự điều khiển: {name!r}")
    return name


def default_root() -> Path:
    """Thư mục quét mặc định: home của user (`C:\\Users\\<user>`)."""
    return Path.home()


def system_skip_dirs() -> list[Path]:
    """Các cây hệ thống luôn bỏ qua: TEMP/TMP/AppData/LocalAppData."""
    roots: list[Path] = []
    for key in ("TEMP", "TMP", "APPDATA", "LOCALAPPDATA"):
        value = os.environ.get(key)
        if value:
            try:
                roots.append(Path(value).resolve())
            except OSError:
                continue
    seen: list[Path] = []
    for path in roots:
        if path not in seen:
            seen.append(path)
    return seen


def list_drives() -> list[str]:
    """Liệt kê ổ đĩa khả dụng (Windows `C:\\`...; nền tảng khác:[])."""
    if os.name != "nt":
        return []
    drives: list[str] = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def list_extra_drives(home: Path | None = None) -> list[str]:
    """Các ổ đĩa ngoài ổ chứa home (để GUI dựng checkbox)."""
    base = home or default_root()
    try:
        home_anchor = Path(base.resolve().anchor).as_posix().lower()
    except OSError:
        home_anchor = ""
    return [d for d in list_drives() if Path(d).as_posix().lower() != home_anchor]


def _is_hidden_win(path: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes

        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == 0xFFFFFFFF:
            return False
        return bool(attrs & 0x2) or bool(attrs & 0x4)
    except (OSError, AttributeError):
        return False


def _under_any(path: Path, roots: list[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    for root in roots:
        try:
            if resolved == root or resolved.is_relative_to(root):
                return True
        except (OSError, ValueError):
            continue
    return False


def _has_dot_part(path: Path, home: Path) -> bool:
    try:
        rel = path.resolve().relative_to(home.resolve())
    except (OSError, ValueError):
        return False
    return any(part.startswith(".") for part in rel.parts)


def find_folders_by_name(
    name: str,
    roots: Iterable[str | Path] | None = None,
    home_root: Path | None = None,
    skip_dirs: Iterable[str | Path] | None = None,
) -> list[str]:
    """Quét `roots` tìm thư mục có tên đúng bằng `name` (case-insensitive).

    - `roots` trống = chỉ quét home.
    - `skip_dirs=None` = dùng `system_skip_dirs()` (TEMP/AppData);
      truyền `[]` để tắt (hữu ích cho test dưới %TEMP%).
    - Dưới `home_root`: nhánh có phần bắt đầu `.` bị cắt, ngoài ra giữ.
    - Luôn cắt cây skip, thư mục ẩn/system, không follow link.
    """
    target = name.strip()
    if not target:
        raise ValueError("Tên thư mục cần tìm không được để trống.")
    home = Path(home_root) if home_root else default_root()
    scan: list[Path] = [Path(r) for r in roots] if roots else [home]
    skip = [Path(p) for p in skip_dirs] if skip_dirs is not None else system_skip_dirs()
    want = target.lower()
    found: list[str] = []
    stack: list[Path] = [p for p in scan if Path(p).is_dir()]
    visited: set[str] = set()
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                entries = list(it)
        except (PermissionError, FileNotFoundError, OSError, NotADirectoryError):
            continue
        for entry in entries:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if not is_dir:
                continue
            child = Path(entry.path)
            try:
                key = str(child.resolve())
            except OSError:
                key = str(child.absolute())
            if key.lower() in visited:
                continue
            visited.add(key.lower())
            if _under_any(child, skip):
                continue
            try:
                under_home = child.resolve().is_relative_to(home.resolve())
            except (OSError, ValueError):
                under_home = False
            if under_home and _has_dot_part(child, home):
                continue
            if under_home and _is_hidden_win(child):
                continue
            try:
                if child.name.lower() == want:
                    found.append(str(child))
            except OSError:
                continue
            if entry.is_symlink():
                continue
            stack.append(child)
    found.sort(key=str.lower)
    return found
