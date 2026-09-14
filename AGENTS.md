# AGENTS.md — IconMaker

Hướng dẫn và luật cho agent làm việc trong dự án này. Mọi agent bắt buộc đọc file này trước khi làm việc.

## Dự án

- **Tên:** IconMaker
- **Mục đích:** Chuyển đổi ảnh **PNG → ICO** (icon) bằng Pillow, có giao diện **Tkinter** và **Launcher C#** chạy trên Windows.
- **Stack:** Python 3.13, Pillow, Tkinter (thư viện chuẩn), .NET / C# (launcher).
- **Trạng thái hiện tại:** Đã có đủ: converter PNG→ICO, GUI Tkinter (convert + đặt icon thư mục qua desktop.ini), sprite splitter OCR, icon quality pipeline, launcher C#, Makefile. Plan + trạng thái trong `.agents/README.md`.

## Đường dẫn quan trọng

| Đường dẫn | Nội dung |
| --- | --- |
| `AGENTS.md` | Luật dành cho agent (file này) |
| `.agents/README.md` | Bảng chỉ dẫn của toàn bộ `.agents/` |
| `.agents/plan/` | Các bản plan chi tiết từng phần |
| `.agents/decisions.md` | Nhật ký quyết định |
| `Makefile` | lối vào của mọi pipeline: `make help` liệt kê target |
| `.opencode/` | Cấu hình và agent của opencode |

## Luật bắt buộc

1. **Chỉ commit khi chạy được và test pass.** Chỉ được tạo commit khi phiên bản hiện tại chạy được và toàn bộ test case vượt qua. Không commit code dở dang (WIP).
2. **Test phải có ý nghĩa.** Test phải hook vào đúng file/hàm thật, vào những phần dễ hỏng (converter, xử lý ảnh, đường dẫn, edge case). Không viết test chỉ để cho đủ số lượng.
3. **Chủ động xóa test cũ.** Khi một test không còn phản ánh hành vi hiện tại, lỗi thời, hoặc thay thế được bằng test tốt hơn — hãy xóa/chỉnh nó, không giữ lại cho có.
4. **Ghi lại mọi quyết định.** Mỗi khi người dùng đưa ra một quyết định (chọn thư viện, thiết kế, quy trình, ...) → thêm một luật tương ứng vào file này kèm ngày tháng, đồng thời ghi vào `.agents/decisions.md`.
5. **Đọc plan trước khi code.** Trước khi triển khai, đọc `.agents/README.md` và các plan liên quan trong `.agents/plan/`.
6. **Cập nhật plan.** Sau khi hoàn thành một phần việc, cập nhật trạng thái vào plan tương ứng (đánh dấu `✅`, thêm ghi chú) để agent tiếp theo nắm được tình hình.
7. **Makefile là lối vào của mọi quy trình.** Khi thêm/thay đổi script hoặc entry point, phải cập nhật `Makefile` trong cùng lần thay đổi, và chạy target liên quan để kiểm chứng.
8. **Icon trỏ từ desktop.ini phải nằm ngoài app.** Trước khi ghi `desktop.ini`, icon `.ico` bắt buộc được copy vào thư viện icon ổn định của user (`~/OneDrive/Pictures/Icon`) bằng `foldericon.install_icon` — không bao giờ trỏ thẳng vào thư mục app, vì di chuyển app sẽ hỏng icon.
9. **Agent cấm tạo file ngoài thư mục app.** Chỉ có code của chính app Python (được test bằng `tmp_path`) mới được ghi vào các vị trí bên ngoài (như thư viện icon). Agent không được dùng lệnh shell để tạo/sửa file rác ngoài `IconMaker/`; mọi thử nghiệm phải dùng fixture `tmp_path` hoặc tự dọn dẹp ngay sau khi chạy (kể cả artifact trong `~/` và các thuộc tính `attrib` đã đặt lên file thật).

## Quy ước code

- Python: mã nguồn đặt trong `src/iconmaker/`, test trong `tests/` (dùng pytest).
- Launcher C#: đặt trong `launcher/`.
- Không thêm comment thừa. Viết code sạch, theo phong cách các file xung quanh.
- Không import thư viện nào chưa khai báo trong `requirements.txt`.
- Công việc phải tự kiểm chứng trước khi báo hoàn thành (chạy thử, chạy test).

## Nhật ký luật

Luật mới được thêm khi người dùng đưa ra quyết định (xem `.agents/decisions.md`).

- **2026-09-13 — L1:** Chỉ commit khi phiên bản chạy được và pass toàn bộ test (Luật 1).
- **2026-09-13 — L2:** Test phải có ý nghĩa, hook vào hàm thật, chủ động xóa test lỗi thời (Luật 2, 3).
- **2026-09-13 — L3:** Mọi quyết định của người dùng phải được ghi thành luật + vào decision log (Luật 4).
- **2026-09-14 — L4:** Makefile là lối vào của mọi pipeline; cập nhật Makefile cùng lần thay đổi entry point (Luật 7).
- **2026-09-14 — L5:** Icon dùng cho desktop.ini phải copy vào thư viện icon ổn định của user trước (Luật 8).
- **2026-09-14 — L6:** Agent không được tạo file bên ngoài thư mục app; chỉ code app (test qua tmp_path) mới được ghi ra ngoài, agent phải tự dọn mọi artifact (Luật 9).