"""Lỗi custom của IconMaker (kế thừa từ ValueError/OSError để code cũ vẫn bắt được)."""

from __future__ import annotations


class IconMakerError(Exception):
    """Lỗi gốc của mọi lỗi do IconMaker tự phát hiện."""


class BadImageError(IconMakerError, ValueError):
    """File không phải ảnh đọc được, hoặc sai định dạng yêu cầu."""


class BadSizeError(IconMakerError, ValueError):
    """Kích thước/bán kính bo góc không hợp lệ."""


class MissingFileError(IconMakerError, FileNotFoundError):
    """Không tìm thấy file/thư mục đầu vào."""
