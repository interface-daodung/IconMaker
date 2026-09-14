"""Test sprites.split — hook vào các điểm dễ hỏng của thuật toán xóa nền đen."""

from __future__ import annotations

from PIL import Image

from iconmaker import sprites


def _canvas(w=200, h=200, shade=(0x12, 0x13, 0x15)):
    return Image.new("RGB", (w, h), shade)


def _rect(img, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            img.putpixel((x, y), color)


def test_black_background_removed_and_sprites_trimmed():
    img = _canvas()
    _rect(img, 20, 20, 59, 59, (255, 0, 0))
    _rect(img, 140, 140, 179, 179, (0, 255, 0))
    sprites_out = sprites.split_sprites(img, min_area=500)
    assert len(sprites_out) == 2
    a, b = sprites_out
    assert a.size == (40, 40)  # đã trim sát mép
    assert b.size == (40, 40)
    assert a.getpixel((0, 0)) == (255, 0, 0, 255)
    assert b.getpixel((39, 39)) == (0, 255, 0, 255)
    # ảnh RGBA nên có alpha = 0 ở đâu đó nếu bbox chứa khoảng trống;
    # ở đây bbox kín nên không còn trong suốt
    assert a.getchannel("A").getextrema() == (255, 255)


def test_interior_dark_pixels_are_not_holed_out():
    """Đốm đen KÍN BÊN TRONG sprite (mắt) phải giữ nguyên, không bị khoét."""
    img = _canvas()
    _rect(img, 30, 30, 69, 69, (255, 255, 255))
    _rect(img, 45, 45, 54, 54, (0, 0, 0))  # con mắt đen, không chạm biên
    (spr,) = sprites.split_sprites(img, min_area=500)
    assert spr.size == (40, 40)
    assert spr.getchannel("A").getextrema()[0] == 255, "đốm đen bên trong bị đục thủng"
    assert spr.getpixel((15, 15)) == (0, 0, 0, 255)


def test_transparent_gap_splits_two_sprites_not_merged():
    """Hai sprite cách nhau 3px nền đen phải tách riêng."""
    img = _canvas()
    _rect(img, 10, 50, 48, 89, (255, 255, 255))
    _rect(img, 53, 50, 91, 89, (255, 255, 255))
    out = sprites.split_sprites(img, min_area=500)
    assert len(out) == 2
    assert all(s.size == (39, 40) for s in out)


def test_sprite_touching_border_is_not_eaten_by_flood_fill():
    """Sprite dính mép ảnh: vùng sáng giữ được, nền không lan vào."""
    img = _canvas()
    _rect(img, 0, 0, 29, 29, (200, 30, 30))  # chạm gốc trên-trái
    out = sprites.split_sprites(img, min_area=100)
    assert len(out) == 1
    assert out[0].size == (30, 30)
    assert out[0].getpixel((0, 0)) == (200, 30, 30, 255)


def test_reading_order_is_row_then_column():
    """Lưới 2x3: thứ tự phải là (0,0),(0,1),(0,2),(1,0),(1,1),(1,2)."""
    img = _canvas(400, 300)
    for row in range(2):
        for col in range(3):
            _rect(img, 20 + col * 120, 20 + row * 130, 20 + col * 120 + 59, 20 + row * 130 + 59,
                  (row * 50 + 10, col * 50 + 10, 200))
    out = sprites.split_sprites(img, min_area=500)
    assert len(out) == 6
    # ảnh đầu là góc trên-trái (tô màu row0col0)
    assert out[0].getpixel((0, 0)) == (10, 10, 200, 255)
    # ảnh thứ 4 là đầu hàng hai (row1col0)
    assert out[3].getpixel((0, 0)) == (60, 10, 200, 255)


def test_small_noise_below_min_area_is_ignored():
    img = _canvas()
    _rect(img, 50, 50, 89, 89, (255, 255, 255))
    img.putpixel((150, 150), (255, 255, 255))  # 1px nhiễu
    out = sprites.split_sprites(img, min_area=100)
    assert len(out) == 1


def test_varied_dark_background_shades_all_removed():
    """Nền lẫn các mẫu #101213/#121315 vẫn bị xóa; thân tối KÍN trong
    viền sáng được nạp vào sprite (không biến mất, không thủng)."""
    img = Image.new("RGB", (200, 200))
    for y in range(200):
        for x in range(200):
            img.putpixel((x, y), (0x10, 0x12, 0x13) if (x + y) % 2 else (0x12, 0x13, 0x15))
    _rect(img, 60, 60, 99, 99, (255, 255, 255))    # viền sáng chứa sprite
    _rect(img, 65, 65, 94, 94, (0x11, 0x12, 0x14))  # thân tối nằm kín
    out = sprites.split_sprites(img, min_area=500)
    assert len(out) == 1
    (spr,) = out
    assert spr.getchannel("A").getextrema()[0] == 255, "thân tối bên trong bị đục thủng"
    assert spr.getpixel((0, 0)) == (255, 255, 255, 255)
    assert spr.getpixel((5, 5)) == (0x11, 0x12, 0x14, 255)


def test_remove_black_background_keeps_canvas_size():
    img = _canvas()
    _rect(img, 50, 50, 69, 69, (255, 0, 0))
    out = sprites.remove_black_background(img)
    assert out.size == img.size
    assert out.getpixel((0, 0))[3] == 0
    assert out.getpixel((55, 55))[3] == 255


def test_all_black_image_returns_no_sprites():
    assert sprites.split_sprites(_canvas()) == []


# ---------- caption matching (OCR được mock qua caption_boxes/associate_captions) ----------


def _rects(*items):
    """items: (x0,y0,x1,y1,text,score) -> định dạng kết quả thô của RapidOCR."""
    out = []
    for x0, y0, x1, y1, text, score in items:
        box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        out.append((box, text, score))
    return out


def test_caption_below_sprite_is_associated():
    boxes = [(10, 10, 100, 100), (150, 10, 240, 100)]
    rects = sprites.caption_boxes(
        _rects((30, 110, 80, 130, "games", 0.9), (160, 110, 220, 130, "code", 0.9))
    )
    assert sprites.associate_captions(boxes, rects) == ["games", "code"]


def test_text_inside_icon_is_not_a_caption():
    """Text nằm GIỮA sprite (vd '</>') không được tính là caption."""
    boxes = [(10, 10, 100, 100)]
    rects = sprites.caption_boxes(_rects((30, 40, 80, 60, "</>", 0.99)))
    assert sprites.associate_captions(boxes, rects) == [None]


def test_caption_too_far_below_is_ignored():
    boxes = [(10, 10, 100, 100)]
    y = 100 + sprites.CAPTION_MAX_GAP + 50
    rects = sprites.caption_boxes(_rects((30, y, 80, y + 20, "far", 0.9)))
    assert sprites.associate_captions(boxes, rects) == [None]


def test_caption_picks_nearest_row_sprite():
    """Caption giữa hai hàng -> thuộc sprite phía trên nó, không phải hàng dưới."""
    boxes = [(10, 10, 100, 100), (10, 200, 100, 290)]
    rects = sprites.caption_boxes(_rects((30, 115, 80, 135, "games", 0.9)))
    assert sprites.associate_captions(boxes, rects) == ["games", None]


def test_low_confidence_text_is_dropped():
    boxes = [(10, 10, 100, 100)]
    rects = sprites.caption_boxes(
        _rects((30, 110, 80, 130, "rac", 0.2), (90, 110, 100, 130, "ok", 0.9))
    )
    assert sprites.associate_captions(boxes, rects) == ["ok"]


def test_multiple_captions_on_same_sprite_join_left_to_right():
    boxes = [(0, 0, 400, 100)]
    rects = sprites.caption_boxes(
        _rects((200, 110, 260, 130, "md", 0.9), (20, 110, 90, 130, "skill", 0.9))
    )
    assert sprites.associate_captions(boxes, rects) == ["skill md"]


def test_sanitize_name_strips_illegal_windows_chars():
    assert sprites.sanitize_name('con:/ "path"<>|?*') == "con path"
    assert sprites.sanitize_name("  spaced..name. ") == "spaced..name"
    assert sprites.sanitize_name("::") is None


def test_unique_name_appends_counter():
    used: set[str] = set()
    a = sprites._unique("games", used, 1)
    b = sprites._unique("games", used, 2)
    assert (a, b) == ("games", "games (2)")


def test_process_file_names_sprites_by_caption(tmp_path, monkeypatch):
    """E2E không cần OCR thật: monkeypatch get_ocr bằng engine giả."""
    img = Image.new("RGB", (300, 260), (0x12, 0x13, 0x15))
    _rect(img, 20, 20, 90, 110, (255, 255, 255))   # sprite 1
    _rect(img, 150, 20, 220, 110, (255, 0, 0))     # sprite 2
    src = tmp_path / "sheet.png"
    img.save(src)

    class FakeOCR:
        def __call__(self, _path):
            results = [
                ([(40, 120), (70, 120), (70, 140), (40, 140)], "games", "0.9"),
                ([(160, 120), (210, 120), (210, 140), (160, 140)], "co/de", "0.9"),
            ]
            return results, None

    monkeypatch.setattr(sprites, "get_ocr", lambda: FakeOCR())
    written = sprites.process_file(src, tmp_path / "out")
    names = [p.name for p in written]
    assert names == ["001-games.png", "002-code.png"]
    for p in written:
        assert p.is_file() and Image.open(p).mode == "RGBA"


def test_process_file_without_caption_uses_plain_index(tmp_path, monkeypatch):
    img = _canvas()
    _rect(img, 20, 20, 90, 90, (255, 255, 255))
    src = tmp_path / "one.png"
    img.save(src)

    class EmptyOCR:
        def __call__(self, _path):
            return None, None

    monkeypatch.setattr(sprites, "get_ocr", lambda: EmptyOCR())
    written = sprites.process_file(src, tmp_path / "out")
    assert [p.name for p in written] == ["001.png"]
