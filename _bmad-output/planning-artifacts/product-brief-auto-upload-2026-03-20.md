---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
date: 2026-03-20
author: Nguyenquocbao
---

# Product Brief: auto-upload

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Tóm tắt Dự án (Executive Summary)

Dự án **auto-upload** là một công cụ quy mô cá nhân được thiết kế để tự động hóa hoàn toàn quy trình tạo và đăng tải YouTube Shorts số lượng lớn. Thay vì phải dựng sẵn video hoàn chỉnh (render video), công cụ này nhận đầu vào chỉ là các bức ảnh tĩnh đã ghép chữ được lấy tự động từ một thư mục Google Drive. Bằng cách điều khiển giả lập Android (LDPlayer), công cụ sẽ tự động thao tác trên app YouTube Mobile để đưa ảnh tĩnh lên, tận dụng trình chỉnh sửa native của YouTube để chèn nhạc đề xuất, thiết lập thời lượng (khoảng 5s) và xuất bản hàng loạt thành các video Shorts. Công cụ cũng tích hợp cơ chế theo dõi lịch sử để đảm bảo tuyệt đối không đăng tải trùng lặp (duplicate) các bức ảnh đã lên kênh. Điều này giúp giải phóng hoàn toàn sức lao động thủ công, tối ưu hóa thời gian và khai thác lợi thế kho nhạc có sẵn của YouTube.

---

## Tầm nhìn Cốt lõi (Core Vision)

### Tuyên bố Vấn đề (Problem Statement)

Việc xuất bản YouTube Shorts số lượng lớn tốn rất nhiều thời gian nếu thực hiện bằng tay. Nhu cầu cốt lõi là tạo ra các luồng nội dung dựa trên nền ảnh tĩnh (như trích dẫn, câu nói, meme ảnh ghép chữ) kèm nhạc theo xu hướng. Quá trình xuất bản thủ công từng ảnh một, tải ảnh xuống từ đám mây và tìm cách tránh đăng lại những ảnh cũ là quá trình rất nhàm chán và không thể mở rộng quy mô.

### Tác động của Vấn đề (Problem Impact)

Nếu không có sự tự động hóa, người sáng tạo nội dung sẽ bị giới hạn ở một số lượng nhỏ video được đăng mỗi ngày do thời gian thao tác trên điện thoại mất quá lâu. Điều này cản trở việc xây dựng luồng traffic lớn từ Shorts, gây ra sự hao mòn sức lực vì những tác vụ lặp đi lặp lại như lựa chọn, phân loại ảnh và ghi nhớ xem ảnh nào đã đăng.

### Tại sao các Giải pháp hiện tại không đủ đáp ứng (Why Existing Solutions Fall Short)

Các công cụ tự động đăng tải (auto-upload) hiện tại trên máy tính thường yêu cầu đầu vào phải là một video đã được render hoàn chỉnh (cả hình và tiếng) trữ sẵn ở ổ cứng Local máy tính. Trình duyệt PC không hỗ trợ tính năng chọn ảnh tĩnh và tự chèn ghép nhạc native như trên ứng dụng YouTube Mobile. Hơn nữa, những tool này thiếu đi sự tích hợp liền mạch thẳng từ kho lưu trữ Google Drive và thường thiếu cơ chế chống trùng lặp hiệu quả cho các file tĩnh.

### Giải pháp Đề xuất (Proposed Solution)

Phát triển một công cụ tự động hóa thao tác (Macro/RPA) chạy trên môi trường giả lập nền tảng di động (cụ thể là LDPlayer). Công cụ sẽ:
1. **Kết nối trực tiếp:** Cung cấp đường dẫn hoặc ID một thư mục Google Drive, tool tự động quét và tải ảnh tĩnh về máy tính/giả lập.
2. **Chống trùng lặp (Deduplication):** Tích hợp tính năng đối chiếu và ghi nhận lịch sử (qua cơ sở dữ liệu nhỏ hoặc cache) để đánh dấu các ảnh đã đăng, bỏ qua các ảnh cũ.
3. **Tự động hóa LDPlayer:** Tự động hóa các thao tác click chuột/vuốt chạm trên LDPlayer để khởi động app YouTube.
4. **Xử lý nội dung:** Đẩy ảnh tĩnh lên, chọn nhạc từ danh sách gợi ý của nền tảng (trending sound), cài đặt thời lượng chạy khung hình (5 giây).
5. **Xuất bản:** Tự động hoàn tất quy trình upload, thêm tag/mô tả và chuyển sang ảnh tiếp theo.

### Các Điểm khác biệt Chính (Key Differentiators)

- **Đường dẫn siêu tốc từ Đám mây (Cloud to Platform):** Quy trình một điểm chạm cho phép tài nguyên từ Google Drive đi thẳng lên YouTube Shorts mà không cần người dùng tải về chỉnh tay.
- **Tiết kiệm tài nguyên render:** Không cần sử dụng sức mạnh đồ họa PC để render hàng ngàn video cứng; YouTube sẽ tự xử lý việc biến ảnh tĩnh và nhạc thành video Shorts.
- **Tận dụng lợi thế Music:** Khai thác được thuật toán và kho nhạc bắt tai trực tiếp từ kho ứng dụng của YouTube Mobile, tránh được rủi ro bản quyền của các tool render trên PC.
- **Chạy ổn định & tránh trùng lặp:** Tập trung vào độ ổn định khi chạy qua giả lập LDPlayer và cơ chế chống đăng lặp (dedup) để tránh vô tình đăng lại cùng một nội dung.

---

## Khách hàng Mục tiêu (Target Users)

### Người dùng Chính (Primary Users)

**Nhà Sáng tạo Nội dung Độc lập (Solo Content Creator - Điển hình: Bạn)**
- **Bối cảnh:** Xây dựng kênh YouTube cá nhân với số lượng nội dung lớn, tập trung vào mô hình video Shorts dựa trên ảnh tĩnh (trích dẫn, meme, text).
- **Mục tiêu / Nhu cầu:** Cần tối đa hóa sản lượng xuất bản video (mass-produce) trên kênh mỗi ngày mà không bị kìm chân bởi các thao tác tay lặp đi lặp lại. Đánh giá cao hiệu suất và sự tối giản, ưu tiên giao diện cửa sổ dòng lệnh (Terminal/CLI) thay vì giao diện người dùng (UI) phức tạp.
- **Nỗi đau hiện tại:** Quá trình tải, đăng ảnh và thêm nhạc trên điện thoại tiêu tốn năng lượng và thời gian khổng lồ đáng ra phải dùng để thiết kế/sáng tạo nội dung mới.

### Người dùng Phụ (Secondary Users)

*(Tạm thời: N/A - Không ưu tiên)*
- Tool này hiện chỉ nhắm vào mục tiêu tối ưu cho cá nhân tác giả, do đó không đòi hỏi thiết kế giao diện phổ thông, thân thiện cho những người kém kỹ thuật (như nhân viên không rành IT hay người dùng đại chúng). Tuy nhiên, thiết kế dòng lệnh vẫn cho phép các kỹ thuật viên hoặc quản trị kênh khác dễ dàng tái sử dụng trong tương lai.

### Hành trình Sử dụng (User Journey)

Hành trình tối ưu lý tưởng diễn ra qua 4 bước:
1. **Chuẩn bị Tài nguyên:** Người dùng tạo sẵn hàng chục/trăm ảnh tĩnh thiết kế bằng Photoshop/Canva và đưa tất cả vào một thư mục Google Drive cố định.
2. **Khởi chạy (Onboarding):** Người dùng cấu hình các biến môi trường trong file `.env` (ví dụ `DRIVE_URL` hoặc `LOCAL_DIR`, `ADB_SERIAL`), sau đó chạy `python main.py`.
3. **Thực thi Ngầm (Core Usage):** Người dùng có thể để công cụ chạy trong nền. Công cụ tự động kết nối Drive kéo ảnh về ➡️ Khởi động LDPlayer ➡️ Vòng lặp xử lý: chọn ảnh ➡️ đưa vào YouTube App ➡️ chọn nhạc thịnh hành ~5 giây ➡️ đặt caption ➡️ hoàn tất thao tác đăng/lưu nháp theo cấu hình ➡️ lưu lịch sử chống trùng ➡️ tiếp tục.
4. **Khoảnh khắc Thành công (Success Moment):** Người dùng quay lại máy tính, nhìn màn hình Terminal báo cáo xanh mướt: "Hoàn tất upload 100/100 video". Công việc nặng nhọc ngày hôm đó hoàn thành trong 1 giây bấm lệnh.

---

## Thước đo Thành công (Success Metrics)

### Mục tiêu Thành công của Người dùng (User Success)
- **Tự động hóa rảnh tay (Hands-free automation):** Xóa bỏ hoàn toàn thời gian phải ngồi thao tác trên màn hình điện thoại/máy tính để tự upload. Chỉ cần nạp thư mục Drive và ấn chạy lệnh duy nhất.
- **Giải phóng năng lượng:** Tiết kiệm hàng giờ đồng hồ mỗi ngày khỏi công việc nhàm chán, để 100% chất xám phục vụ cho sáng tạo ảnh thiết kế.
- **Sự an tâm tuyệt đối:** Hệ thống chống trùng lặp (Deduplication) theo dõi vĩnh viễn lịch sử ảnh, bảo vệ kênh không bao giờ gặp án phạt re-upload vô ý.

### Mục tiêu Dự án & Hiệu suất (Project & Performance Objectives)
- **Khối lượng sản xuất cao (Mass Production):** Đẩy nhanh quá trình bao phủ nội dung kênh (phủ traffic diện rộng) với hàng trăm Shorts được lên sóng đều đặn.
- **Độ bền bỉ (Stability):** Tool có khả năng duy trì thao tác giả lập LDPlayer mà không bị mắc kẹt do treo app YouTube, xử lý mềm mại các đoạn trễ (lag) của hệ điều hành ảo.

### Chỉ số Đo lường Hiệu quả (Key Performance Indicators - KPIs)
- **KPI Sản lượng (Throughput):** Duy trì tải lên thành công và ổn định từ 100 đến 200 video Shorts trong mỗi phiên chạy liên tục mà không bắt buộc khởi động lại tool.
- **KPI Chống Trùng lặp (Deduplication Rate):** Đạt 100% độ chính xác trong việc đối chiếu, bỏ qua các ảnh trong thư mục Google Drive đã từng xuất bản trước đó.
- **KPI Thực thi (Execution Rate):** Đạt tỷ lệ hoàn tất luồng (đến bước cuối xuất bản hoặc lưu nháp theo cấu hình) > 95% trên tổng số ảnh nạp vào. Cho phép biên độ lỗi vặt nhỏ (mạng nghẽn, LDPlayer kẹt pop-up) với khả năng hệ thống tự bỏ qua (skip error) và đi tiếp tới ảnh sau.

---

## Phạm vi Phiên bản Đầu tiên (MVP Scope)

### Tính năng Cốt lõi (Core Features)
- **Hệ thống Dữ liệu Đầu vào (Google Drive Integration):** Tự động truy cập URL thư mục Google Drive được cung cấp, quét và tải các ảnh tĩnh mới nhất theo định dạng chuẩn mà không cần thao tác tải file thủ công.
- **Bảo vệ Nội dung Kênh (Local Tracking & Deduplication):** Một cơ sở dữ liệu nhỏ (Local JSON/SQLite) đóng vai trò sổ cái (ledger), lưu trữ mã định danh của ảnh đã được xử lý để ngăn chặn tuyệt đối tình trạng upload trùng lặp.
- **Động cơ Tự động hóa (App Automation Runtime):** Kịch bản Auto click/Vuốt mô phỏng thao tác trên LDPlayer, tự động trình diễn chuỗi hành động: Khởi động YouTube App ➡️ Chọn tính năng tạo Shorts ➡️ Nạp ảnh ➡️ Gắn nhạc phổ biến tự động (chỉnh về 5 giây) ➡️ Trích xuất mô tả ngẫu nhiên từ thư viện định sẵn ➡️ Đăng tải.
- **Tối ưu Hóa Hiển thị (CLI-based Interface):** Lược bỏ hoàn toàn UI nặng nề. Toàn bộ thông tin báo lỗi, logs, số lượng đăng tải sẽ hiển thị trên màn hình Terminal (Command Line).

### Nằm ngoài Phạm vi MVP (Out of Scope for MVP)
- Xây dựng Giao diện đồ họa người dùng đồ sộ (GUI).
- Chạy đa thiết bị, đa luồng LDPlayer hay quản lý luân phiên nhiều tài khoản YouTube cùng lúc (Chỉ tập trung 1 tài khoản/1 máy hiện tại).
- Ứng dụng LLMs (ChatGPT/Claude,...) để sinh Tiêu đề/Phân tích nội dung theo ảnh thời gian thực.
- Xử lý phức tạp các cửa sổ bảo mật (CAPTCHA) bất ngờ do hệ thống bảo mật của Google.

### Tiêu chí Thành công của bản MVP (MVP Success Criteria)
- Đạt được vòng chạy khép kín (E2E Run): Lấy link URL Drive ảo ➡️ Bắn được luồng lên YouTube qua LDPlayer thành công trọn vẹn.
- Ở lần thử nghiệm quy mô thật đầu tiên, tool vượt qua mốc xử lý thành công không đứt gãy 100 file ảnh liên tiếp.
- Cơ chế Deduplicate hoạt động kiểm chứng được thông qua việc từ chối upload các file mang yếu tố lặp lại.

### Tầm nhìn Tương lai (Future Vision)
- **Quản lý Tập trung (v2.0):** Phát triển Giao diện bảng điều khiển (Dashboard) quản trị hàng loạt, cho phép bạn bật tắt nhiều luồng LDPlayer song song cho hàng chục kênh YouTube vệ tinh khác nhau cùng lúc.
- **Trở thành SaaS AI (v3.0):** Khi thuật toán đã quá ổn định, tích hợp AI tự động lên title/hashtags và thương mại hóa, đóng gói bán/cấp phép Tool dưới dạng giải pháp All-In-One dành cho giới làm Content YouTube Faceless (không lộ mặt).
