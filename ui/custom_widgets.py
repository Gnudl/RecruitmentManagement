import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.candidate import Candidate


class CandidateCard(tk.Frame):
    """
    Component tùy biến hiển thị chi tiết hồ sơ ứng viên được chọn (Candidate Card).
    - Tự động thay đổi màu viền và huy hiệu theo trạng thái của ứng viên.
    - Đảm bảo quy tắc layout: bên trong LabelFrame chỉ dùng grid().
    """

    # Bảng màu đại diện theo trạng thái tuyển dụng
    STATUS_COLORS = {
        Candidate.STATUS_NOP_HO_SO: "#2980b9",   # Xanh dương
        Candidate.STATUS_DUYET_CV: "#16a085",    # Xanh mòng két
        Candidate.STATUS_PV_VONG_1: "#f39c12",   # Cam tươi
        Candidate.STATUS_PV_VONG_2: "#d35400",   # Cam đậm
        Candidate.STATUS_DAT_OFFER: "#27ae60",   # Xanh lá cây
        Candidate.STATUS_LOAI: "#c0392b",        # Đỏ
    }
    DEFAULT_COLOR = "#7f8c8d"

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Container chính dạng LabelFrame
        self.card_frame = tk.LabelFrame(
            self,
            text=" HỒ SƠ ỨNG VIÊN ĐƯỢC CHỌN ",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=10,
            relief="solid",
            bd=2,
        )
        self.card_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Toàn bộ widget con bên trong LabelFrame chỉ dùng grid()
        self._build_widgets()
        self.clear()

    def _build_widgets(self):
        # 1. Tên ứng viên
        self.lbl_name = tk.Label(
            self.card_frame,
            text="Chưa chọn ứng viên",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            fg="#2c3e50",
        )
        self.lbl_name.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # 2. Vị trí tuyển dụng
        self.lbl_position = tk.Label(
            self.card_frame,
            text="Vị trí: --",
            font=("Segoe UI", 10, "italic"),
            anchor="w",
            fg="#7f8c8d",
        )
        self.lbl_position.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Dải phân cách
        self.separator = ttk.Separator(self.card_frame, orient="horizontal")
        self.separator.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # 3. Mã ứng viên
        tk.Label(self.card_frame, text="Mã ID:", font=("Segoe UI", 9, "bold"), anchor="w").grid(
            row=3, column=0, sticky="w", pady=2
        )
        self.lbl_id = tk.Label(self.card_frame, text="--", font=("Segoe UI", 9), anchor="w")
        self.lbl_id.grid(row=3, column=1, sticky="w", padx=8, pady=2)

        # 4. Email
        tk.Label(self.card_frame, text="Email:", font=("Segoe UI", 9, "bold"), anchor="w").grid(
            row=4, column=0, sticky="w", pady=2
        )
        self.lbl_email = tk.Label(self.card_frame, text="--", font=("Segoe UI", 9), anchor="w")
        self.lbl_email.grid(row=4, column=1, sticky="w", padx=8, pady=2)

        # 5. Số điện thoại
        tk.Label(self.card_frame, text="Điện thoại:", font=("Segoe UI", 9, "bold"), anchor="w").grid(
            row=5, column=0, sticky="w", pady=2
        )
        self.lbl_phone = tk.Label(self.card_frame, text="--", font=("Segoe UI", 9), anchor="w")
        self.lbl_phone.grid(row=5, column=1, sticky="w", padx=8, pady=2)

        # 6. Kinh nghiệm
        tk.Label(self.card_frame, text="Kinh nghiệm:", font=("Segoe UI", 9, "bold"), anchor="w").grid(
            row=6, column=0, sticky="w", pady=2
        )
        self.lbl_experience = tk.Label(self.card_frame, text="--", font=("Segoe UI", 9), anchor="w")
        self.lbl_experience.grid(row=6, column=1, sticky="w", padx=8, pady=2)

        # 7. Điểm đánh giá
        tk.Label(self.card_frame, text="Điểm phỏng vấn:", font=("Segoe UI", 9, "bold"), anchor="w").grid(
            row=7, column=0, sticky="w", pady=2
        )
        self.lbl_score = tk.Label(self.card_frame, text="--", font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_score.grid(row=7, column=1, sticky="w", padx=8, pady=2)

        # 8. Trạng thái / Vòng tuyển dụng
        tk.Label(self.card_frame, text="Trạng thái:", font=("Segoe UI", 9, "bold"), anchor="w").grid(
            row=8, column=0, sticky="w", pady=4
        )
        self.lbl_status = tk.Label(
            self.card_frame,
            text="Chưa có dữ liệu",
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=self.DEFAULT_COLOR,
            padx=8,
            pady=3,
            relief="flat",
        )
        self.lbl_status.grid(row=8, column=1, sticky="w", padx=8, pady=4)

        # Cấu hình co giãn cột
        self.card_frame.columnconfigure(1, weight=1)

    def update_candidate(self, candidate: Optional[Candidate]):
        """Cập nhật giao diện thẻ với thông tin của đối tượng Candidate."""
        if not candidate:
            self.clear()
            return

        self.lbl_name.config(text=candidate.full_name)
        self.lbl_position.config(text=f"Vị trí ứng tuyển: {candidate.position_id}")
        self.lbl_id.config(text=candidate.person_id)
        self.lbl_email.config(text=candidate.email)
        self.lbl_phone.config(text=candidate.phone)
        self.lbl_experience.config(text=f"{candidate.experience_years} năm")

        score_text = f"{candidate.interview_score:.1f} / 100"
        score_color = "#27ae60" if candidate.interview_score >= 80 else ("#e67e22" if candidate.interview_score >= 50 else "#c0392b")
        self.lbl_score.config(text=score_text, fg=score_color)

        status_color = self.STATUS_COLORS.get(candidate.status, self.DEFAULT_COLOR)
        self.lbl_status.config(text=candidate.status, bg=status_color)
        self.card_frame.config(highlightbackground=status_color, highlightcolor=status_color)

    def clear(self):
        """Khôi phục trạng thái mặc định khi chưa có ứng viên nào được chọn."""
        self.lbl_name.config(text="Chưa chọn ứng viên", fg="#7f8c8d")
        self.lbl_position.config(text="Vui lòng bấm vào danh sách ứng viên để xem chi tiết")
        self.lbl_id.config(text="--")
        self.lbl_email.config(text="--")
        self.lbl_phone.config(text="--")
        self.lbl_experience.config(text="--")
        self.lbl_score.config(text="--", fg="#2c3e50")
        self.lbl_status.config(text="Chưa chọn", bg=self.DEFAULT_COLOR)
        self.card_frame.config(highlightbackground=self.DEFAULT_COLOR, highlightcolor=self.DEFAULT_COLOR)
