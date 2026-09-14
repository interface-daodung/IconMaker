# Plan 004 — Chiến lược Testing

**Trạng thái:** ✅ Chiến lược đã chốt — áp dụng khi có code.

## Nguyên tắc (bắt nguồn từ Luật 2, 3 trong AGENTS.md)

1. **Test phải có ý nghĩa.** Mỗi test phải hook vào **file/hàm thật** và bảo vệ một hành vi **dễ hỏng** cụ thể. Không viết test chỉ để đủ số lượng.
2. **Test phải trả lời "điều gì sẽ vỡ nếu tôi xóa dòng này?"** — nếu không có câu trả lời, xóa test đó.
3. **Chủ động xóa test lỗi thời.** Test không còn phản ánh hành vi hiện tại → sửa hoặc xóa ngay, không giữ lại cho có.
4. **Chạy được trong CI/máy thường.** Không phụ thuộc GUI hiển thị, không cần file mẫu bên ngoài.
5. **Chỉ commit khi toàn bộ test pass** (Luật 1).

## Vùng bắt buộc phải có test (hook vào hàm dễ hỏng)

| Vùng | File | Loại test |
| --- | --- | --- |
| Đọc ảnh hỏng / không phải PNG | `converter.py` | pytest.raises |
| Ảnh RGB không alpha | `converter.py` | output hợp lệ, có alpha |
| Ảnh RGBA | `converter.py` | giữ alpha |
| Upscale ảnh nhỏ | `converter.py` | kích thước đúng, không crash |
| Sizes hợp lệ / bất hợp lệ | `converter.py` | list đúng / raise |
| File ICO đọc lại được + đủ sizes | `converter.py` | đọc lại bằng Pillow, đếm size |
| Đường dẫn: thiếu thư mục, unicode, trùng tên | `converter.py`, `gui.py` (logic thuần) | tạo thư mục / suy tên output đúng |
| Ảnh lớn | `converter.py` | hoàn thành, không OOM |

## Vùng KHÔNG viết test (tránh test giả)

- Vẽ widget Tkinter / sự kiện GUI hiển thị.
- Vòng lặp đời sống của Launcher C# (chỉ test tay khi build).

## Kỹ thuật khuyến nghị

- Fixture tạo ảnh test ngay trong `tests/conftest.py` bằng Pillow → không cần file mẫu.
- Assert bằng cách **đọc lại output bằng chính Pillow** (mở `.ico`, kiểm tra `n_frames`/kích thước) thay vì chỉ kiểm tra file tồn tại.
- Nếu một nhóm test đoán mò chức năng không tồn tại → xóa, không sửa hàm để "nuôi" test.

## Checklist khi một phần code hoàn thành

- [ ] Test gọi hàm thật (không mock tràn lan).
- [ ] Mỗi test bảo vệ đúng một hành vi dễ hỏng.
- [ ] Chạy `pytest` → pass 100%.
- [ ] Không còn test lỗi thời (đã xóa/chỉnh).
- [ ] Cập nhật plan tương ứng lên trạng thái phù hợp.