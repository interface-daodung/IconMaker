"""Tách sprite từ ảnh nền đen: xóa nền -> nối vùng -> cắt từng sprite -> trim.

Pipeline:
1. Nền đen = pixel có R,G,B đều <= `threshold` (phủ các mẫu #111214, #101213,
   #121315) VÀ nối liền với biên ảnh (8-hướng) -> nền tối BÊN TRONG sprite
   (mắt, viền) không bị khoét thủng.
2. Các vùng không-nền còn lại được gán nhãn 4-hướng; mỗi vùng >= `min_area`
   là một sprite (lọc chữ caption/nhiễu nhỏ), bbox đã trim sát mép pixel.
"""

from __future__ import annotations

import re
from array import array
from collections import deque
from pathlib import Path

from PIL import Image

NEAR_BLACK_THRESHOLD = 32  # phủ các mẫu #111214, #101213, #121315 (0x10..0x15)
DEFAULT_MIN_AREA = 2000    # bỏ vụn/nhiễu nhỏ
ROW_TOLERANCE = 32         # hai sprite cách nhau <= số px này theo trục y thì cùng hàng
CAPTION_V_TOL = 15         # caption được phép overlap mép dưới sprite bao nhiêu px
CAPTION_MAX_GAP = 240      # khoảng cách dọc tối đa sprite -> caption
OCR_MIN_SCORE = 0.5


def _near_black_at(data: bytes, i: int, threshold: int) -> bool:
    j = 3 * i
    return data[j] <= threshold and data[j + 1] <= threshold and data[j + 2] <= threshold


def _flood_background(rgb: Image.Image, threshold: int) -> bytearray:
    """bytearray đánh dấu 1 tại pixel gần đen nối liền với biên ảnh (8-hướng)."""
    w, h = rgb.size
    data = rgb.tobytes()
    bg = bytearray(w * h)
    dq: deque[int] = deque()

    def seed(i: int) -> None:
        if not bg[i] and _near_black_at(data, i, threshold):
            bg[i] = 1
            dq.append(i)

    for x in range(w):
        seed(x)
        seed((h - 1) * w + x)
    for y in range(1, h - 1):
        seed(y * w)
        seed(y * w + w - 1)

    # Loang 4-hướng: hai sprite chỉ chạm NHAU qua khe chéo vẫn được giữ nguyên;
    # nền len qua khe chéo hẹp giữa hai sprite cũng không "ăn thủng" sprite
    # vì nền đen thật luôn liên tục 4-hướng ở vùng rộng.
    while dq:
        i = dq.popleft()
        x, y = i % w, i // w
        for j in (
            i - 1 if x > 0 else -1,
            i + 1 if x < w - 1 else -1,
            i - w if y > 0 else -1,
            i + w if y < h - 1 else -1,
        ):
            if j >= 0 and not bg[j] and _near_black_at(data, j, threshold):
                bg[j] = 1
                dq.append(j)
    return bg


def _label_regions(bg: bytearray, w: int, h: int) -> tuple[array, int]:
    """Gán nhãn 4-hướng cho từng vùng liền mạch không phải nền."""
    labels = array("i", bytes(4 * w * h))
    nxt = 0
    dq: deque[int] = deque()
    for start in range(w * h):
        if bg[start] or labels[start]:
            continue
        nxt += 1
        labels[start] = nxt
        dq.append(start)
        while dq:
            i = dq.popleft()
            x, y = i % w, i // w
            for j in (
                i - 1 if x > 0 else -1,
                i + 1 if x < w - 1 else -1,
                i - w if y > 0 else -1,
                i + w if y < h - 1 else -1,
            ):
                if j >= 0 and not bg[j] and not labels[j]:
                    labels[j] = nxt
                    dq.append(j)
    return labels, nxt


def _region_boxes(
    labels: array, total: int, w: int, h: int
) -> dict[int, tuple[int, int, int, int, int]]:
    """lab -> (area, x0, y0, x1, y1) của mọi vùng."""
    areas = [0] * (total + 1)
    mins_x = [w] * (total + 1)
    maxs_x = [-1] * (total + 1)
    mins_y = [h] * (total + 1)
    maxs_y = [-1] * (total + 1)
    for y in range(h):
        base = y * w
        for x in range(w):
            lab = labels[base + x]
            if lab:
                areas[lab] += 1
                if x < mins_x[lab]:
                    mins_x[lab] = x
                if x > maxs_x[lab]:
                    maxs_x[lab] = x
                if y < mins_y[lab]:
                    mins_y[lab] = y
                if y > maxs_y[lab]:
                    maxs_y[lab] = y
    return {
        lab: (areas[lab], mins_x[lab], mins_y[lab], maxs_x[lab], maxs_y[lab])
        for lab in range(1, total + 1)
        if areas[lab]
    }


def _merge_holes_into_hosts(
    labels: array, w: int, h: int, info: dict, min_area: int
) -> dict[int, tuple[int, int, int, int]]:
    """Gộp mọi vùng có bbox nằm trọn trong bbox vùng khác (lỗ/khối tối trong
    sprite, chi tiết nằm trong bao) vào chủ ngoài cùng, rồi giữ các chủ còn
    tổng diện tích >= min_area. Vụn nằm ngoài mọi sprite bị loại.
    """
    regions = sorted(
        info.items(),
        key=lambda kv: (kv[1][3] - kv[1][1] + 1) * (kv[1][4] - kv[1][2] + 1),
    )
    parent: dict[int, int] = {}
    for i, (lab, (_, x0, y0, x1, y1)) in enumerate(regions):
        for j in range(i + 1, len(regions)):
            host, (harea, hx0, hy0, hx1, hy1) = regions[j]
            box_area = (hx1 - hx0 + 1) * (hy1 - hy0 + 1)
            sub_area = (x1 - x0 + 1) * (y1 - y0 + 1)
            if box_area > sub_area and hx0 <= x0 and hy0 <= y0 and x1 <= hx1 and y1 <= hy1:
                parent[lab] = host
                break

    def root_of(lab: int) -> int:
        while lab in parent:
            lab = parent[lab]
        return lab

    totals: dict[int, int] = {}
    bboxes: dict[int, tuple[int, int, int, int]] = {}
    for lab, (area, x0, y0, x1, y1) in info.items():
        root = root_of(lab)
        totals[root] = totals.get(root, 0) + area
        if root != lab:
            for y in range(y0, y1 + 1):
                base = y * w
                for x in range(x0, x1 + 1):
                    if labels[base + x] == lab:
                        labels[base + x] = root
        if root not in bboxes:
            bboxes[root] = (x0, y0, x1, y1)
        else:
            bx0, by0, bx1, by1 = bboxes[root]
            bboxes[root] = (min(bx0, x0), min(by0, y0), max(bx1, x1), max(by1, y1))
    return {lab: b for lab, b in bboxes.items() if totals[lab] >= min_area}


def _reading_order(
    boxes: dict[int, tuple[int, int, int, int]],
) -> list[tuple[int, tuple[int, int, int, int]]]:
    """Sắp xếp sprite theo thứ tự đọc: gom thành hàng (y gần nhau), trái -> phải."""
    rows: list[list[tuple[int, tuple[int, int, int, int]]]] = []
    for item in sorted(boxes.items(), key=lambda kv: kv[1][1]):
        for row in rows:
            if abs(row[-1][1][1] - item[1][1]) <= ROW_TOLERANCE:
                row.append(item)
                break
        else:
            rows.append([item])
    return [it for row in sorted(rows, key=lambda r: min(b[1] for b in r)) for it in sorted(row, key=lambda b: b[1][0])]


def _extract_sprites(
    img: Image.Image,
    threshold: int = NEAR_BLACK_THRESHOLD,
    min_area: int = DEFAULT_MIN_AREA,
) -> list[tuple[tuple[int, int, int, int], Image.Image]]:
    """Internal: trả về (bbox, ảnh RGBA đã trim) theo thứ tự đọc."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    bg = _flood_background(rgb, threshold)
    labels, total = _label_regions(bg, w, h)
    boxes = _merge_holes_into_hosts(
        labels, w, h, _region_boxes(labels, total, w, h), min_area
    )
    if not boxes:
        return []

    src = rgb.load()
    out_list: list[tuple[tuple[int, int, int, int], Image.Image]] = []
    for lab, (x0, y0, x1, y1) in _reading_order(boxes):
        out = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 1), (0, 0, 0, 0))
        out_px = out.load()
        for oy in range(y1 - y0 + 1):
            row = (y0 + oy) * w
            for ox in range(x1 - x0 + 1):
                i = row + x0 + ox
                if labels[i] == lab:
                    out_px[ox, oy] = (*src[i % w, y0 + oy], 255)
        out_list.append(((x0, y0, x1, y1), out))
    return out_list


def split_sprites(
    img: Image.Image,
    threshold: int = NEAR_BLACK_THRESHOLD,
    min_area: int = DEFAULT_MIN_AREA,
) -> list[Image.Image]:
    """Danh sách sprite RGBA đã trim, đọc theo thứ tự từ trái sang, trên xuống.

    Mỗi ảnh chỉ chứa pixel của đúng một vùng; khoảng trống trong suốt bên
    trong bbox (kể cả vùng tối bị coi là nền lọt trong sprite) giữ nguyên.
    """
    return [sprite for _, sprite in _extract_sprites(img, threshold, min_area)]


_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_name(text: str) -> str | None:
    """Chuyển text OCR thành tên file hợp lệ trên Windows; None nếu rỗng."""
    t = _ILLEGAL.sub("", text)
    t = re.sub(r"\s+", " ", t).strip().rstrip(".")
    return t or None


def caption_boxes(ocr_results) -> list[tuple[float, float, float, float, str]]:
    """Lọc kết quả RapidOCR -> (x0,y0,x1,y1,text) với confidence đủ cao."""
    rects = []
    for box, text, score in ocr_results or []:
        try:
            if float(score) < OCR_MIN_SCORE:
                continue
        except (TypeError, ValueError):
            pass
        clean = sanitize_name(text)
        if not clean:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        rects.append((min(xs), min(ys), max(xs), max(ys), clean))
    return rects


def associate_captions(
    sprite_boxes: list[tuple[int, int, int, int]],
    rects: list[tuple[float, float, float, float, str]],
) -> list[str | None]:
    """Gán caption cho sprite nằm NGAY TRÊN nó.

    Điều kiện: tâm caption nằm trong biên ngang của sprite, mép trên caption
    nằm từ đáy sprite trở xuống (cho phép `CAPTION_V_TOL` overlap) và không
    quá xa (`CAPTION_MAX_GAP`). Text nằm TRONG icon (phía trên đáy sprite)
    bị loại. Nếu nhiều caption hợp lệ, nối theo thứ tự từ trái sang.
    """
    groups: list[list[tuple[float, str]]] = [[] for _ in sprite_boxes]
    for cx0, cy0, cx1, cy1, text in rects:
        cx = (cx0 + cx1) / 2
        best: tuple[float, int] | None = None
        for si, (x0, y0, x1, y1) in enumerate(sprite_boxes):
            if not x0 <= cx <= x1:
                continue
            gap = cy0 - y1
            if gap < -CAPTION_V_TOL or gap > CAPTION_MAX_GAP:
                continue
            if best is None or gap < best[0]:
                best = (gap, si)
        if best is not None:
            groups[best[1]].append((cx0, text))
    return [
        " ".join(t for _, t in sorted(g)) if g else None for g in groups
    ]


def remove_black_background(
    img: Image.Image, threshold: int = NEAR_BLACK_THRESHOLD
) -> Image.Image:
    """Toàn bộ ảnh gốc với nền đen (nối biên) chuyển thành trong suốt."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    bg = _flood_background(rgb, threshold)
    out = rgb.convert("RGBA")
    px = out.load()
    for i in range(w * h):
        if bg[i]:
            px[i % w, i // w] = (0, 0, 0, 0)
    return out


_ocr_engine = None


def get_ocr():
    """RapidOCR (ONNXRuntime) nạp lười, dùng chung một engine."""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR

        _ocr_engine = RapidOCR()
    return _ocr_engine


def _unique(name: str, used: set[str], fallback: int) -> str:
    candidate = name or f"{fallback:03d}"
    if candidate in used:
        i = 2
        while f"{candidate} ({i})" in used:
            i += 1
        candidate = f"{candidate} ({i})"
    used.add(candidate)
    return candidate


def process_file(
    path: str | Path,
    out_dir: str | Path,
    threshold: int = NEAR_BLACK_THRESHOLD,
    min_area: int = DEFAULT_MIN_AREA,
    use_ocr: bool = True,
) -> list[Path]:
    """Tách sprite một file ảnh vào `out_dir/<tên file>/`.

    Tên file: `NNN_<caption OCR>.png` theo thứ tự đọc; nếu không có OCR hoặc
    không đọc được caption thì chỉ dùng `NNN.png`.
    """
    p = Path(path)
    with Image.open(p) as img:
        extracted = _extract_sprites(img, threshold, min_area)
        rects: list = []
        if use_ocr and extracted:
            ocr_results, _ = get_ocr()(str(p))
            rects = caption_boxes(ocr_results)

    dest_dir = Path(out_dir) / p.stem
    dest_dir.mkdir(parents=True, exist_ok=True)
    captions = associate_captions([box for box, _ in extracted], rects)
    written: list[Path] = []
    used: set[str] = set()
    for idx, ((_x0, _y0, _x1, _y1), sprite), caption in zip(
        range(1, len(extracted) + 1), extracted, captions
    ):
        if caption:
            name = _unique(caption, used, idx)
            out_path = dest_dir / f"{idx:03d}-{name}.png"
        else:
            out_path = dest_dir / f"{idx:03d}.png"
        sprite.save(out_path)
        written.append(out_path)
    return written
