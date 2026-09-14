"""Test icons.py — ICO chất lượng cao từ sprite (không biến dạng, giữ size lớn)."""

from pathlib import Path

from PIL import Image

from core import convert, icons
from tests.test_converter import ico_frame_sizes


def _sprite(w, h, color=(255, 0, 0, 255)):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (w, h), color))
    return img


def test_pad_to_square_keeps_aspect_and_centers():
    src = _sprite(400, 200)
    out = icons.pad_to_square(src)
    assert out.size == (400, 400)
    assert out.getpixel((200, 200)) == (255, 0, 0, 255)
    assert out.getpixel((200, 0))[3] == 0
    assert out.getpixel((200, 399))[3] == 0


def test_sprite_to_ico_keeps_proportions_no_squash(tmp_path):
    """Sprite 400x200: band màu ở size 32 phải cao ~16px (nửa khung), không full."""
    p = tmp_path / "s.png"
    _sprite(400, 200).save(p)
    ico = tmp_path / "s.ico"
    icons.sprite_to_ico(p, ico, sizes=[32])
    with Image.open(ico) as f:
        f.size = (32, 32)
        frame = f.convert("RGBA")
    col = [frame.getpixel((16, y))[3] for y in range(32)]
    opaque_rows = sum(1 for a in col if a > 128)
    assert 12 <= opaque_rows <= 20, f"tỉ lệ bị méo: {opaque_rows}/32"


def test_sprite_to_ico_contains_all_requested_sizes(tmp_path):
    p = tmp_path / "s.png"
    _sprite(120, 80).save(p)
    ico = tmp_path / "s.ico"
    icons.sprite_to_ico(p, ico, sizes=[16, 48, 256])
    assert ico_frame_sizes(ico) == {(16, 16), (48, 48), (256, 256)}


def test_large_frame_stays_png_compressed_in_ico(tmp_path):
    """Frame 256px phải là PNG lossless trong ICO (không phải BMP 256)."""
    p = tmp_path / "s.png"
    _sprite(300, 300).save(p)
    ico_path = tmp_path / "s.ico"
    icons.sprite_to_ico(p, ico_path, sizes=[256])
    data = ico_path.read_bytes()
    entry = data[6:22]
    off = int.from_bytes(entry[12:16], "little")
    assert data[off : off + 8].startswith(b"\x89PNG")


def test_default_sizes_when_none(tmp_path):
    p = tmp_path / "s.png"
    _sprite(300, 300).save(p)
    ico = tmp_path / "s.ico"
    icons.sprite_to_ico(p, ico)
    assert ico_frame_sizes(ico) == {(s, s) for s in convert.get_default_sizes()}


def test_build_from_sprites_flattens_with_sheet_prefix(tmp_path):
    a = tmp_path / "sprites_out" / "0"
    b = tmp_path / "sprites_out" / "1"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    _sprite(300, 250).save(a / "001-games.png")
    _sprite(280, 310).save(b / "002-code.png")
    written = icons.build_from_sprites(tmp_path / "sprites_out", tmp_path / "icon_out")
    out_root = tmp_path / "icon_out"
    assert [p.name for p in written] == ["0-001-games.ico", "1-002-code.ico"]
    assert all(p.parent == out_root for p in written), "mọi icon phải cùng 1 tầng"
    assert sorted(p.name for p in out_root.iterdir()) == ["0-001-games.ico", "1-002-code.ico"]
    for p in written:
        assert ico_frame_sizes(p) >= {(256, 256), (32, 32)}


def test_same_caption_in_two_sheets_does_not_collide(tmp_path):
    s = tmp_path / "sprites_out"
    (s / "2").mkdir(parents=True)
    (s / "3").mkdir()
    _sprite(300, 250).save(s / "2" / "004-gitlab.png")
    _sprite(300, 250).save(s / "3" / "004-gitlab.png")
    written = icons.build_from_sprites(s, tmp_path / "icon_out")
    assert [p.name for p in written] == ["2-004-gitlab.ico", "3-004-gitlab.ico"]


def test_build_from_sprites_empty_dir(tmp_path):
    (tmp_path / "sprites_out").mkdir()
    assert icons.build_from_sprites(tmp_path / "sprites_out", tmp_path / "icon_out") == []
