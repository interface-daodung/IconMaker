"""Entry point dòng lệnh: python -m iconmaker.cli <nguon.png> <dich.ico> [sizes...]"""

from __future__ import annotations

import sys

from iconmaker import converter


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not 2 <= len(args) <= 8:
        print(f"Dùng: {sys.argv[0]} <nguon.png> <dich.ico> [kích_thước...]")
        print(f"Mặc định: {converter.DEFAULT_SIZES}")
        return 2
    try:
        sizes = [int(a) for a in args[2:]] or None
        out = converter.convert_png_to_ico(args[0], args[1], sizes)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())