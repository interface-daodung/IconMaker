"""Test đổi định dạng ảnh tại service.format_convert (pixel thật, không mở GUI)."""

from pathlib import Path

import pytest
from PIL import Image

from core.exceptions import BadImageError, MissingFileError
from service import format_convert
from service.format_convert import (
    clamp_quality,
    compress_bytes,
    compressed_preview,
    convert_format_file,
    normalize_ext,
    target_formats,
)


def _make(path: Path, fmt: str = "PNG", size=(120, 80), mode="RGBA", color=(200, 100, 50, 255)):
    img = Image.new(mode, size, color)
    img.save(path, format=fmt)
    img.close()
    return str(path)


def test_normalize_ext_maps_jpeg_to_jpg_and_dots():
    assert normalize_ext(".jpeg") == ".jpg"
    assert normalize_ext(".PNG") == ".png"
    assert normalize_ext("webp") == ".webp"
    with pytest.raises(ValueError):
        normalize_ext(".gif")


def test_clamp_quality_bounds():
    assert clamp_quality(100) == 100
    assert clamp_quality(1) == 1
    with pytest.raises(ValueError):
        clamp_quality(0)
    with pytest.raises(ValueError):
        clamp_quality(101)
    with pytest.raises(ValueError):
        clamp_quality("abc")


def test_target_formats_are_the_other_two():
    assert target_formats(".png") == [".jpg", ".webp"]
    assert target_formats(".jpg") == [".png", ".webp"]
    assert target_formats(".webp") == [".png", ".jpg"]
    assert target_formats("src.jpeg") == [".png", ".webp"]


def test_compress_bytes_returns_nonempty_for_all_formats(tmp_path):
    src = _make(tmp_path / "a.png")
    with Image.open(src) as img:
        png = compress_bytes(img, ".png")
        jpg = compress_bytes(img, ".jpg", 90)
        webp = compress_bytes(img, ".webp", 90)
    assert png and jpg and webp


def test_lower_quality_creates_smaller_jpeg(tmp_path):
    src = _make(tmp_path / "noisy.png", "PNG", size=(300, 300))
    img = Image.open(src)
    data_high = compress_bytes(img, ".jpg", 100)
    img.seek(0)
    data_low = compress_bytes(img, ".jpg", 5)
    img.close()
    assert len(data_low) < len(data_high)


def test_compressed_preview_keeps_size_and_loads(tmp_path):
    src = _make(tmp_path / "src.png")
    with Image.open(src) as img:
        prev = compressed_preview(img, ".jpg", 60)
        assert prev.size == img.size
        prev.close()
        prev2 = compressed_preview(img, ".webp", 50)
        assert prev2.size == img.size
        prev2.close()


def test_convert_png_to_jpg(tmp_path):
    src = _make(tmp_path / "logo.png")
    out = convert_format_file(src, tmp_path / "out", fmt=".jpg", quality=90)
    assert out == str(tmp_path / "out" / "logo.jpg")
    with Image.open(out) as saved:
        assert saved.format == "JPEG"
        assert saved.mode == "RGB"
        assert saved.size == (120, 80)


def test_convert_png_to_webp_keeps_alpha(tmp_path):
    src = _make(tmp_path / "logo.png")
    out = convert_format_file(src, tmp_path / "out", fmt=".webp", quality=80)
    with Image.open(out) as saved:
        assert saved.format == "WEBP"
        assert saved.size == (120, 80)


def test_convert_jpg_to_png(tmp_path):
    src = _make(tmp_path / "photo.jpg", "JPEG", mode="RGB", size=(200, 100))
    out = convert_format_file(src, tmp_path / "out", fmt=".png")
    with Image.open(out) as saved:
        assert saved.format == "PNG"
        assert saved.size == (200, 100)


def test_convert_webp_to_jpg(tmp_path):
    src = _make(tmp_path / "pic.webp", "WEBP")
    out = convert_format_file(src, tmp_path / "out", fmt=".jpg", quality=70)
    with Image.open(out) as saved:
        assert saved.format == "JPEG"
        assert saved.size == (120, 80)


def test_same_format_rejected(tmp_path):
    src = _make(tmp_path / "a.png")
    with pytest.raises(ValueError):
        convert_format_file(src, tmp_path / "out", fmt=".png")


def test_jpeg_alias_maps_to_jpg_and_is_allowed(tmp_path):
    src = _make(tmp_path / "a.png")
    out = convert_format_file(src, tmp_path / "out", fmt=".jpeg")
    assert out.endswith("a.jpg")


def test_missing_source_raises(tmp_path):
    with pytest.raises(MissingFileError):
        convert_format_file(tmp_path / "nope.png", fmt=".jpg")


def test_wrong_input_extension_raises(tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("hello", encoding="utf-8")
    with pytest.raises(BadImageError):
        convert_format_file(txt, fmt=".jpg")


def test_broken_png_raises(tmp_path, broken_file):
    with pytest.raises(BadImageError):
        convert_format_file(broken_file, fmt=".jpg")


def test_out_dir_created_and_stem_kept(tmp_path):
    src = _make(tmp_path / "vecto.webp", "WEBP")
    out = convert_format_file(src, tmp_path / "nested" / "deep", fmt=".png")
    assert Path(out).is_file()
    assert Path(out).name == "vecto.png"


def test_cli_requires_fmt_value(tmp_path, capsys):
    assert format_convert.main(["--fmt"]) == 2
    assert format_convert.main(["--quality", "abc"]) == 2
    capsys.readouterr()


def test_cli_convert_with_flags(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    src = _make(tmp_path / "cli.png")
    assert format_convert.main([src, "--fmt", ".webp", "--quality", "70"]) == 0
    assert (tmp_path / "output" / "convert_format" / "cli.webp").is_file()
    assert format_convert.main([src, "--fmt", ".png"]) == 1  # trùng đuôi -> lỗi
    capsys.readouterr()


def test_cli_defaults_to_input_output_dirs(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert format_convert.main([]) == 1  # input/ trống -> lỗi
    (tmp_path / "input").mkdir()
    _make(tmp_path / "input" / "t.png")
    assert format_convert.main([]) == 0
    assert (tmp_path / "output" / "convert_format" / "t.jpg").is_file()
    capsys.readouterr()