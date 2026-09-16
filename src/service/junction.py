"""Tạo Junction Point: `mklink /J <link> <target>` + `attrib +r <link> /l`.

Junction cho phép một đường dẫn ảo (thường nằm trong OneDrive) trỏ tới thư
mục thật ở ổ khác mà không cần quyền admin. `attrib +r <link> /l` đặt thuộc
tính chỉ-đọc trên CHÍNH reparse point (không đụng thư mục thật) để Explorer
cho phép hiển thị icon tuỳ chỉnh theo desktop.ini bên trong.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def validate_junction_paths(
    link: str | Path, target: str | Path
) -> tuple[Path, Path]:
    """Kiểm tra trước khi tạo, trả về (link, target) dạng tuyệt đối.

    - `link` phải CHƯA tồn tại (mklink sẽ tạo nó); thư mục cha phải có thật.
    - `target` phải là thư mục có thật.
    """
    raw_link = str(link).strip()
    raw_target = str(target).strip()
    if not raw_link:
        raise ValueError("Thiếu đường dẫn ảo (junction sẽ tạo).")
    if not raw_target:
        raise ValueError("Thiếu đường dẫn thật (thư mục nguồn).")
    link_p = Path(raw_link).expanduser().resolve()
    target_p = Path(raw_target).expanduser().resolve()
    if link_p == target_p:
        raise ValueError("Đường dẫn ảo và đường dẫn thật trùng nhau.")
    if link_p.exists():
        raise FileExistsError(
            f"Đường dẫn ảo đã tồn tại: {link_p}\n"
            "Xoá hoặc di chuyển nó trước khi tạo junction."
        )
    if not link_p.parent.is_dir():
        raise FileNotFoundError(
            f"Thư mục cha của đường dẫn ảo không tồn tại: {link_p.parent}"
        )
    if not target_p.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục thật: {target_p}")
    return link_p, target_p


def build_link_command(link: str | Path, target: str | Path) -> list[str]:
    """Câu lệnh mklink /J (mklink là builtin của cmd nên phải chạy qua cmd /c)."""
    return ["cmd", "/c", "mklink", "/J", str(link), str(target)]


def _run_attrib(*args: str) -> None:
    result = subprocess.run(
        ("attrib", *args), capture_output=True, check=False, shell=False
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).decode(errors="replace").strip()
        raise RuntimeError(f"attrib {' '.join(args)} thất bại (mã {result.returncode}): {detail}")


def set_link_readonly(link: str | Path) -> None:
    """`attrib +r <link> /l`: chỉ-đọc trên chính junction, không lan vào target.

    KHÔNG được resolve() link: sẽ đi xuyên reparse point tới thư mục thật.
    """
    _run_attrib("+r", os.path.abspath(str(link)), "/l")


def create_junction(
    link: str | Path, target: str | Path, readonly: bool = True
) -> Path:
    """Tạo junction `link -> target`; `readonly=True` chạy thêm attrib +r /l.

    Trả về đường dẫn link đã tạo.
    """
    if sys.platform != "win32":
        raise RuntimeError("Junction (mklink /J) chỉ khả dụng trên Windows.")
    link_p, target_p = validate_junction_paths(link, target)
    result = subprocess.run(
        build_link_command(link_p, target_p),
        capture_output=True,
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).decode(errors="replace").strip()
        raise RuntimeError(f"mklink /J thất bại (mã {result.returncode}): {detail}")
    if readonly:
        set_link_readonly(link_p)
    return link_p
