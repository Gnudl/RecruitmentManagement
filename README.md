# Hệ Thống Quản Lý Tuyển Dụng (Đề tài 23)

Ứng dụng Desktop quản lý tuyển dụng xây dựng bằng **Python Tkinter** theo mô hình **OOP phân tầng (Layered Architecture)**, lưu trữ dữ liệu an toàn với cơ chế Atomic Write, tự động sao lưu và phục hồi khi xảy ra sự cố, phân quyền người dùng và kiểm thử tự động toàn diện.

---

## 🏗️ Kiến Trúc Hệ Thống (Layered OOP)

Hệ thống được thiết kế theo 4 tầng kiến trúc độc lập, tuân thủ nguyên lý Đóng gói, Kế thừa, Đa hình và Trừu tượng:

```text
DeTai23/
├── models/             # TẦNG DỮ LIỆU & RÀNG BUỘC (OOP Models)
│   ├── person.py       # Lớp trừu tượng Person(ABC) - Regex Email & SĐT di động VN
│   ├── candidate.py    # Lớp Candidate kế thừa Person (vòng tuyển dụng, điểm 0-100)
│   ├── user.py         # Lớp User kế thừa Person (phân quyền Admin/Staff, SHA-256)
│   └── job_position.py # Lớp JobPosition (min_salary <= max_salary, quota > 0)
├── file_manager.py     # TẦNG LƯU TRỮ AN TOÀN (Atomic write, auto-backup, auto-recovery)
├── services/           # TẦNG NGHIỆP VỤ (Business Services)
│   ├── auth_service.py # Xác thực, session, băm SHA-256, kiểm tra quyền Admin/Staff
│   ├── recruitment_mgr.py # CRUD ứng viên & vị trí, tìm kiếm tiếng Việt, xuất CSV
│   └── job_crawler.py  # Thu thập tin IT qua API, đa luồng an toàn, fallback offline
├── ui/                 # TẦNG GIAO DIỆN (Tkinter GUI - Bên trong LabelFrame chỉ dùng grid)
│   ├── custom_widgets.py # CandidateCard đổi màu viền theo trạng thái ứng viên
│   ├── funnel_canvas.py  # FunnelCanvas vẽ tay biểu đồ phễu chuyển đổi trên Canvas
│   ├── candidate_view.py # Form nhập liệu, Treeview đổi màu tag, bộ lọc kết hợp
│   ├── login_window.py   # Cửa sổ đăng nhập (ẩn password *, bắt phím Enter)
│   └── main_window.py    # Cửa sổ chính (Notebook 3 tab, worker thread, status bar)
├── data/               # Dữ liệu JSON (users.json, jobs.json, candidates.json, crawled_jobs.json)
├── backups/            # Thư mục lưu trữ tự động các bản sao lưu .bak
├── tests/              # Bộ kiểm thử tự động (40 tests đạt 100% PASS)
├── dist/               # File thực thi độc lập QuanLyTuyenDung.exe
└── main.py             # Điểm khởi chạy ứng dụng
```

---

## ✨ Tính Năng Nổi Bật

1. **Bảo mật & Phân quyền**:
   - Mật khẩu người dùng được băm một chiều bằng thuật toán **SHA-256**, không bao giờ lưu plaintext.
   - **Admin**: Toàn quyền thao tác (Thêm, Sửa, Xóa ứng viên & Vị trí, Xuất báo cáo, Crawl tin IT).
   - **Staff**: Chỉ được xem và cập nhật điểm/vòng tuyển dụng; nút Xóa bị vô hiệu hóa trên giao diện và được bảo vệ nghiêm ngặt ở cả tầng Service bằng `PermissionError`.

2. **Validation Chặt Chẽ bằng Regular Expression**:
   - Email kiểm tra chuẩn định dạng (chặn các lỗi như `nguyenvana@`).
   - Số điện thoại di động Việt Nam: Bắt buộc đúng 10 chữ số và bắt đầu bằng các đầu số hợp lệ `03`, `05`, `07`, `08`, `09`.
   - Điểm phỏng vấn giới hạn nghiêm ngặt trong đoạn `[0, 100]`.

3. **Lưu Trữ Tệp An Toàn Tuyệt Đối**:
   - Ghi file nguyên tử (Atomic Write): Ghi ra file `.tmp` trong cùng thư mục, `fsync()` ghi xuống đĩa rồi mới hoán đổi bằng `os.replace()`.
   - Tự động sao lưu bản `.bak` trước khi ghi đè dữ liệu.
   - Chống crash khi gặp file 0-byte (tự trả về `[]`).
   - Tự động phục hồi từ bản sao lưu `.bak` gần nhất khi file JSON bị lỗi cú pháp.

4. **Biểu Đồ Phễu Tuyển Dụng (Funnel Canvas)**:
   - Vẽ tay hoàn toàn bằng `tk.Canvas`, tự động co giãn theo kích thước cửa sổ.
   - Thể hiện tỷ lệ chuyển đổi qua 5 vòng: `Nộp hồ sơ` $\to$ `Duyệt CV` $\to$ `Phỏng vấn vòng 1` $\to$ `Phỏng vấn vòng 2` $\to$ `Đạt/Offer`.
   - Chỉ số ứng viên `Loại` được tách biệt ở chân biểu đồ.

5. **Crawl Tin Việc Làm IT Không Treo UI (Multithreading)**:
   - Chạy HTTP Request trên `threading.Thread(daemon=True)` kết hợp `queue.Queue` và `after()`.
   - Bắt toàn bộ lỗi mạng `ConnectionError`, `Timeout` êm dịu, tự động chuyển sang dữ liệu mẫu offline để demo.

6. **Xuất Báo Cáo CSV Chuẩn Tiếng Việt**:
   - Định dạng bảng mã `utf-8-sig` (tương thích hiển thị tiếng Việt có dấu trên Microsoft Excel mà không bị lỗi font).

---

## 🔑 Tài Khoản Đăng Nhập Mẫu

| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn |
|---|---|---|---|
| **Quản trị viên (Admin)** | `admin` | `admin123` | Toàn quyền hệ thống (CRUD Ứng viên & Vị trí, Crawl, Xuất CSV) |
| **Nhân viên (Staff)** | `staff` | `staff123` | Xem danh sách, cập nhật điểm và vòng tuyển dụng (Không được xóa) |

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Yêu cầu môi trường
- Python 3.10 trở lên
- Thư viện: `requests`

```bash
pip install requests
```

### 2. Khởi chạy từ mã nguồn
```bash
python main.py
```

### 3. Chạy file thực thi `.exe` độc lập (Không cần cài Python)
Truy cập thư mục `dist/` và nhấp đúp vào:
```text
dist/QuanLyTuyenDung.exe
```

---

## 🧪 Chạy Kiểm Thử Tự Động (Unit & Integration Tests)

Chạy toàn bộ 40 ca kiểm thử bao phủ toàn bộ các tầng:
```bash
python -m unittest discover -s tests
```
Tất cả các ca kiểm thử:
- Kiểm tra tính trừu tượng và Encapsulation của Models.
- Kiểm tra cơ chế sao lưu, atomic write và tự phục hồi của FileManager.
- Kiểm tra bảo mật mật khẩu SHA-256, phân quyền Admin/Staff của Services.
- Kiểm tra tính non-blocking của Worker Thread trong UI.
đều đạt **PASS 100%**.

---

## 📦 Đóng Gói Thành File Thực Thi (.exe)

Nếu cần đóng gói lại ứng dụng bằng PyInstaller:
```bash
pyinstaller --onefile --windowed --name QuanLyTuyenDung main.py
```
File thực thi độc lập sẽ được tạo ra tại thư mục `dist/QuanLyTuyenDung.exe`.
