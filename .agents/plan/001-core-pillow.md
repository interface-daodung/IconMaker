# Plan 001 — Core: Chuyển đổi PNG → ICO bằng Pillow

**Trạng thái:** ✅ Hoàn thành (2026-09-13). Code: `src/iconmaker/converter.py`, test: `tests/test_converter.py` (32/32 pass).

**Ghi chú triển khai:** Pillow `_save ICO` bỏ mọi size lớn hơn ảnh GỐC → phải dùng frame LỚN NHẤT làm base ảnh khi lưu (đã xử lý + test `test_default_sizes_all_present_in_output`).

## Mục tiêu

Module Thuần Python (không phụ thuộc UI) chuyển ảnh PNG thành file `.ico`.

## Trách nhiệm (đề xuất cho `converter.py`)

- `convert_png_to_ico(source: str, dest: str, sizes: list[int]) -> None` — hàm chính.
  - Đọc ảnh PNG bằng Pillow.
  - Convert về **RGBA** nếu cần (icon yêu cầu alpha; ảnh RGB phải thêm kênh alpha).
  - Resize về từng kích thước trong `sizes` (mặc định `[16, 24, 32, 48, 64, 128, 256]`).
  - Lưu `.ico` với tất cả kích thước (tham số `sizes` của Pillow).
- `get_default_sizes() -> list[int]` — danh sách kích thước mặc định.
- Trả về path output hoặc raise lỗi rõ ràng thay vì fail im lặng.

## Những điểm dễ hỏng (bắt buộc test — xem plan 004)

1. **Ảnh không phải PNG / hỏng / không đọc được** → exception rõ ràng.
2. **Ảnh RGB (không alpha)** → vẫn phải ra icon hợp lệ (thêm alpha, không vỡ màu).
3. **Ảnh có alpha (RGBA)** → giữ nguyên alpha.
4. **Kích thước nguồn nhỏ hơn kích thước icon** → UPSCALE đúng (`Image.Resampling.LANCZOS`), không crash.
5. **Đường dẫn đích không tồn tại** → tạo thư mục con cần thiết.
6. **Sizes chứa 0 / rỗng / trùng lặp** → xử lý hoặc raise lỗi hợp lệ.
7. **Output thực sự là file ICO đọc lại được** bằng Pillow và chứa đúng số lượng size.
8. **Tên file không hợp lệ / đường dẫn có ký tự đặc biệt (unicode)** trên Windows.
9. **Ảnh rất lớn** → không treo / không bộ nhớ đầy (test với ảnh ~4000×4000).

## Quy ước

- GPL nên đặt trong `src/iconmaker/converter.py`.
- Không dùng Tkinter trong module này.
- Sử dụng `Image.Resampling.LANCZOS` cho resize.
- `requirements.txt` phải có `Pillow`.

## Khung test (tests/test_converter.py)

- Tạo ảnh test bằng Pillow ngay trong conftest/fixture (không cần file mẫu bên ngoài).
- Test phải gọi **hàm thật** `convert_png_to_ico`, kiểm tra output đọc lại được bằng Pillow.

## Ghi chú triển khai

(Để trống — agent triển khai điền vào sau khi xong.)