"""Định nghĩa các format ảnh/icon mà IconMaker hỗ trợ."""

from __future__ import annotations

PNG_EXTENSIONS = {".png"}
ICO_EXTENSIONS = {".ico"}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
WEBP_EXTENSIONS = {".webp"}

READABLE_IMAGE_EXTENSIONS = PNG_EXTENSIONS | JPEG_EXTENSIONS | WEBP_EXTENSIONS
