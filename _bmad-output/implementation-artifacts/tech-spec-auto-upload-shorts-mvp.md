---
title: 'Auto Upload Shorts qua LDPlayer MVP'
slug: 'auto-upload-shorts-mvp'
created: '2026-03-20'
status: 'Completed'
stepsCompleted: [1, 2, 3, 4, 5]
tech_stack: ['python', 'uiautomator2', 'gdown']
files_to_modify: ['main.py', 'src/drive_sync.py', 'src/android_auto.py', 'src/db_manager.py', 'data/titles.txt']
code_patterns: ['Modular CLI', 'Single-threaded loop', 'Robust Error/Pop-up Handling']
test_patterns: ['pytest']
review_notes: |
  Adversarial review completed.
  Findings: 3 total, 3 fixed, 0 skipped.
  Resolution approach: Auto-fix.
---

# Đặc tả Kỹ thuật (Tech-Spec): Auto Upload Shorts qua LDPlayer (Bản MVP)

**Ngày tạo:** 2026-03-20

## Tổng quan (Overview)

### Tuyên bố Vấn đề (Problem Statement)
Việc tải lên thủ công hàng trăm video Shorts dạng ảnh tĩnh tốn quá nhiều thời gian và các cách upload từ máy tính (PC) hiện tại không hỗ trợ việc chèn nhạc nền xu hướng (trending music) được tích hợp sẵn trên ứng dụng YouTube di động. Người sáng tạo nội dung gặp khó khăn để "scale" (mở rộng quy mô) nếu họ muốn giữ được các đặc quyền/thuật toán của nền tảng Shorts nguyên bản.

### Giải pháp (Solution)
Một công cụ CLI (Giao diện Dòng lệnh) bằng Python có khả năng quét và tải ảnh trực tiếp từ thư mục Google Drive, lọc ảnh để chống trùng lặp qua một cơ sở dữ liệu (Database) theo dõi cục bộ, và tự động hóa thao tác trình giả lập LDPlayer qua `uiautomator2` để mở YouTube App, tạo video 5 giây có nhạc trending và đăng tải tự động.

### Phạm vi (Scope)

**Trong phạm vi (In Scope):**
- Tải file từ đường dẫn chia sẻ (shareable link) của Google Drive. Lọc tự động chỉ lấy đúng định dạng ảnh (ví dụ: `.png`, `.jpg`).
- Theo dõi ID ảnh cục bộ bằng mã băm (SHA-256) của file để chống trùng lặp chính xác 100%.
- Kịch bản `uiautomator2` tự động điều khiển LDPlayer: Xử lý pop-up bất ngờ, vuốt tìm ứng dụng YouTube, tải lên ảnh tĩnh, chọn kho nhạc, xử lý delay của UI, thêm tiêu đề ngẫu nhiên từ thư viện `titles.txt` và ấn hoàn tất Upload.
- Giao diện CLI xuất ra tiến trình log, tự động dọn dẹp file ảnh tạm (Garbage Collection) sau khi upload thành công hoặc khi xảy ra sự cố ngoại lệ.

**Nằm ngoài Phạm vi (Out of Scope):**
- Giao diện người dùng đồ họa (GUI).
- Chạy đa luồng nhiều máy ảo LDPlayer cùng lúc.
- Tiêu đề sinh ra bằng Trí tuệ Nhân tạo (chỉ dùng danh sách tĩnh quay vòng).
- Tự động vượt CAPTCHA nâng cao của Google nếu bị chặn.

## Bối cảnh Lập trình (Context for Development)

### Cấu trúc Mã nguồn (Codebase Patterns)
- **Kiến trúc Khởi tạo (Clean Slate Project):** Không bị trói buộc vì code cũ.
- **Kiến trúc Module hóa (Modular Architecture):** Giao diện chính nối kết tuần tự với các module độc lập như Drive Sync, Android Auto, Local DB. Vòng điều khiển (loop) chạy đơn luồng `main.py` có cơ chế `try...except` cứng cáp để bỏ qua (skip) ảnh lỗi và tiếp tục.

### Thư mục và File Tham chiếu (Files to Reference)

| File | Chức năng (Purpose) |
| ---- | ------- |
| `main.py` | Cửa ngõ CLI và Vòng lặp tự động hóa (Automation Loop) chính. Điều hướng logic và báo cáo log. |
| `src/drive_sync.py` | Nhúng `gdown`, có hàm tiện ích giải nén và lọc định dạng file rác (đảm bảo chỉ nhận ảnh hợp lệ). |
| `src/android_auto.py` | Code sử dụng `uiautomator2` để nhận diện nút bấm (Text/Description) trên LDPlayer, setup các lệnh `wait(timeout)` cứng để tránh vỡ thao tác khi lag mạng. Tích hợp ngắt và đóng lệnh pop-up như Ads/Updates. |
| `src/db_manager.py` | Quản lý File `history.sqlite` (SQLite bảo vệ an toàn khỏi việc tham nhũng dữ liệu I/O khi sập máy) để lưu dấu băm SHA-256 của file ảnh. |
| `data/titles.txt` | Nơi chứa các mẫu Caption ngẫu nhiên sẽ được chọn khi đăng lên Youtube. |

### Quyết định Kỹ thuật (Technical Decisions)
- **Tự động hóa LDPlayer:** Sử dụng thư viện `uiautomator2` thay vì `adb` thô sơ. Điều này cho phép script dò tìm UI thông minh (`wait_until_visible()`), bỏ qua các thay đổi thiết kế nho nhỏ trên màn hình, cũng như đóng các hộp thoại làm phiền tự nguyện.
- **Tích hợp Google Drive:** `gdown` để lấy tốc độ phát triển cực cao, khỏi mất công xin cấp phép Google OAuth phức tạp.
- **Cơ sở dữ liệu cục bộ (Local DB):** Đã nâng cấp lên `SQLite` 1 bảng đơn giản thay vì JSON để đảm bảo ACID (không mất dữ liệu (corrupt) khi bị thoát app tắt máy giữa chừng).

## Kế hoạch Cài đặt (Implementation Plan)

### Các Nhiệm vụ (Tasks)

- [x] Nhiệm vụ 1: Thiết lập cấu trúc dự án và biến cấu hình CLI.
  - File: `main.py`, `requirements.txt`, `data/titles.txt`
  - Hành động: Viết Parser `argparse` nhận link Drive. Setup Thư viện Log (lưu log file `.log` và in ra màn hình). Thêm `uiautomator2`, `gdown` vào `requirements.txt`.
- [x] Nhiệm vụ 2: Lập trình xử lý đồng bộ Google Drive.
  - File: `src/drive_sync.py`
  - Hành động: Viết hàm `download_and_filter(drive_url: str, temp_dir: str)`. Dùng gdown lấy nội dung folder. Xóa mọi thư mục/file không phải đuôi ảnh và trả về **mảng chứa Absolute Path của đúng ảnh**.
- [x] Nhiệm vụ 3: Thiết lập SQLite chống trùng lặp & Băm File.
  - File: `src/db_manager.py`
  - Hành động: Băm file ảnh thành chuỗi SHA-256. Mở kết nối SQLite lưu bảng `uploaded_history(hash_id PRIMARY KEY, uploaded_at)`. Hàm `is_uploaded()` và `mark_success()`. Đảm bảo an toàn I/O.
- [x] Nhiệm vụ 4: Kịch bản YouTube UI cứng cáp.
  - File: `src/android_auto.py`
  - Hành động: Sáng tạo bộ máy tương tác UI. Khởi động app YouTube. Cài đặt thao tác `try..except` kiểm tra pop-up cập nhật/ads (đóng nó lại). Tạo Short -> Chọn thư viện -> Ấn "Tiếp" -> Mặc định chọn một bài nhạc bất kỳ từ danh sách "Thịnh hành" -> Chọn Text ngẫu nhiên từ `data/titles.txt`. Bấm "Tải Short Lên". Kiểm chứng trạng thái Upload qua thanh thông báo (Toast) thành công.
- [x] Nhiệm vụ 5: Khớp nối Vòng lặp (Control Loop) & Dọn Dẹp (Garbage Collection).
  - File: `main.py`
  - Hành động: Chốt tiến trình (Workflow flow): Lấy ảnh -> Tính Hash -> Lọc DB -> Gọi Android Upload -> Báo log/Lưu DB -> **Xóa ảnh khỏi ổ cứng (`os.remove()`)** để nhường chỗ (Dọn rác). Tiếp tục ở ảnh tiếp theo.

### Tiêu chí Nghiệm thu (Acceptance Criteria)

- [x] AC 1: (Given) Cho một thư mục Drive gồm 4 ảnh và 1 file PDF rác, (When) khi chạy tool, (Then) công cụ chỉ tải về nguyên xi 4 ảnh và bỏ qua được file kia ở phân vùng `/temp`.
- [x] AC 2: (Given) Nạp vào 4 ảnh (đã up 2 ảnh vào DB SQLite bằng Hashes), (When) vòng điều hướng chính kích hoạt, (Then) Tool ngó lơ 2 file trùng dẫu tên có khác và chỉ đẩy lên 2 ảnh gốc mới toanh hoàn toàn.
- [x] AC 3: (Given) Máy ảo LDPlayer đang load, (When) khi thực thi thao tác `upload()`, (Then) nếu bị dính màn báo lỗi/Popup Update, code tự đóng được Pop-up đó và tiếp tục tiến tới giao diện Upload.
- [x] AC 4: (Given) Sau khi nhấn Tải lên (Upload Short), (When) khi tiến trình Youtube đang tải video mất 5s, (Then) kịch bản sẽ CHỜ cho đến khi xuất hiện trạng thái thông báo tải thành công trước khi ghi "Uploaded Success" vào DB & xóa file ảnh tạm. Nếu lỗi time-out sau 60 giây, cấm ghi vào Local DB.

## Thông tin bổ sung (Additional Context)

### Phụ thuộc (Dependencies)
- Python 3.9+
- Thư viện: `uiautomator2`, `gdown`, `sqlite3`, `pytest`.
- Phải kết nối LDPlayer sẵn bằng ADB trên local port `localhost:5555`. 

### Chiến lược Test thử nghiệm (Testing Strategy)
- Thử nghiệm trên Channel (Kênh) Youtube nháp/trắng ở lần đầu tích hợp mạch luân phiên End-to-End.
- Hỗ trợ thêm tham số `--dry-run` chạy luồng điều khiển (không bấm Next lên YouTube).
- `pytest` với Data giả giả lập DB và module băm SHA-256 bằng ảnh nhỏ không cần khởi chạy Device.

### Chú ý (Notes)
- Giao diện của YouTube thỉnh thoảng cập nhật các text trên Label, Kỹ thuật viên (Code Agent) CẦN cố gắng sử dụng nhận diện UI có độ chịu lỗi (tolerance) bằng XPath cấu trúc lớn thay vì text cứng ở nút.
