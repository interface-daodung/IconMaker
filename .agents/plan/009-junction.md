# Plan 009 — Tool tạo Junction Point

**Trạng thái:** ✅ Hoàn thành (2026-09-14) — quyết định [D25].

## Yêu cầu

- GUI cho phép chọn **đường dẫn ảo** (link, nằm trong OneDrive) + **thư mục thật**
  (nguồn dữ liệu ở ổ mới), bấm nút để tạo junction.
- Cơ chế: `mklink /J "<ảo>" "<thật>"` (mklink là builtin của cmd nên chạy qua
  `cmd /c`), rồi `attrib +r "<ảo>" /l` để Explorer hiển thị được icon tuỳ chỉnh.
- **Ràng buộc quan trọng:** `attrib +r ... /l` phải tác động trên CHÍNH reparse
  point — KHÔNG được `resolve()` link trước khi gọi attrib, vì resolve() đi
  xuyên junction tới thư mục thật và sẽ đặt `+r` nhầm vào dữ liệu gốc.

## Thiết kế (`src/service/junction.py`)

- `validate_junction_paths(link, target)` — trả về cặp đường dẫn tuyệt đối;
  từ chối: input rỗng, link == target, link đã tồn tại (`FileExistsError`, check
  bằng `exists()` trước khi tạo), cha của link không tồn tại, target không phải
  thư mục có thật (`FileNotFoundError`).
- `build_link_command(link, target)` — `["cmd", "/c", "mklink", "/J", ...]`, test
  được mà không chạy lệnh thật.
- `set_link_readonly(link)` — `attrib +r <abspath-không-resolve> /l`.
- `create_junction(link, target, readonly=True)` — validate → mklink → (tuỳ chọn)
  attrib, trả về Path link; Windows-only (`sys.platform != "win32"` thì lỗi rõ).
- CLI: `python -m service.junction <ảo> <thật> [--no-readonly]`.
  `make junction JLINK=... JTARGET=... [JNO=1]`.
- GUI (`tools/junction_tool/`): controller `join_link_path(parent, name)` ghép
  đường dẫn ảo từ thư mục cha (nhập/pick) + tên mới (paste thẳng đường dẫn đủ
  vào ô cha thì bỏ trống tên), `parse_inputs` check rỗng, `run_create` gọi
  service; view Tab "Junction" có checkbox `+r /l` (mặc định bật).

## Đã kiểm chứng

- 10 test `tests/test_junction.py`: validate (rỗng/trùng/tồn tại/mất cha/mất
  target), hình dạng lệnh mklink, từ chối non-Windows; trên Windows thật: tạo
  junction trong `tmp_path` đọc được file xuyên link, `is_junction()`,
  `os.lstat` có `FILE_ATTRIBUTE_READONLY` khi bật / không có khi tắt, dọn bằng
  `attrib -r /l` + `rmdir` (chỉ xoá link, giữ nguyên target).
- 5 test chain/parse trong `tests/test_tools_logic.py` + cập nhật expected list
  registry. CLI chạy thật qua `%TEMP%` (readonly chỉ trên link, target sạch),
  artifact tự dọn ngay.
