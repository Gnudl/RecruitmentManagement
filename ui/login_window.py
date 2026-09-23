import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from models.user import User
from services.auth_service import AuthService


class LoginWindow(tk.Tk):
    """
    Cửa sổ Đăng nhập người dùng vào Hệ thống Tuyển dụng:
    - Cho phép nhập Username và Password (ẩn bằng ký tự '*').
    - Gọi trực tiếp AuthService.login() để kiểm tra mật khẩu qua SHA-256.
    - Đóng LoginWindow và chuyển giao quyền điều khiển sang MainWindow khi đăng nhập thành công.
    - Hỗ trợ phím Enter để đăng nhập nhanh.
    """

    def __init__(self, auth_service: AuthService, on_login_success: Callable[[User], None]):
        super().__init__()
        self.auth_service = auth_service
        self.on_login_success = on_login_success

        self.title("Đăng nhập - Hệ thống Quản lý Tuyển dụng")
        self.geometry("420x330")
        self.resizable(False, False)

        # Căn giữa cửa sổ trên màn hình
        self._center_window(420, 330)

        self._build_ui()

    def _center_window(self, width: int, height: int):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # Tiêu đề ứng dụng
        lbl_header = tk.Label(
            self,
            text="HỆ THỐNG QUẢN LÝ TUYỂN DỤNG",
            font=("Segoe UI", 14, "bold"),
            fg="#2c3e50",
            pady=15,
        )
        lbl_header.pack()

        lbl_sub = tk.Label(
            self,
            text="Vui lòng đăng nhập để tiếp tục làm việc",
            font=("Segoe UI", 9, "italic"),
            fg="#7f8c8d",
        )
        lbl_sub.pack(pady=(0, 10))

        # Khung chứa form đăng nhập (LabelFrame - quy tắc: bên trong chỉ dùng grid)
        frame_login = tk.LabelFrame(
            self,
            text=" THÔNG TIN TÀI KHOẢN ",
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=15,
        )
        frame_login.pack(padx=25, pady=5, fill="x")

        # 1. Tên đăng nhập
        tk.Label(frame_login, text="Tên đăng nhập:", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.ent_username = ttk.Entry(frame_login, width=24, font=("Segoe UI", 9))
        self.ent_username.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        self.ent_username.focus_set()

        # 2. Mật khẩu
        tk.Label(frame_login, text="Mật khẩu:", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.ent_password = ttk.Entry(frame_login, width=24, show="*", font=("Segoe UI", 9))
        self.ent_password.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        # Bắt sự kiện phím Enter
        self.ent_username.bind("<Return>", lambda e: self.do_login())
        self.ent_password.bind("<Return>", lambda e: self.do_login())

        # 3. Nút Đăng nhập
        self.btn_login = ttk.Button(self, text="ĐĂNG NHẬP", command=self.do_login)
        self.btn_login.pack(pady=12, ipadx=10, ipady=3)

        # Gợi ý tài khoản mẫu
        lbl_hint = tk.Label(
            self,
            text="Tài khoản mẫu: Admin (admin / admin123) | Staff (staff / staff123)",
            font=("Segoe UI", 8),
            fg="#95a5a6",
        )
        lbl_hint.pack(side="bottom", pady=8)

    def do_login(self):
        """Xử lý xác thực đăng nhập qua AuthService."""
        username = self.ent_username.get().strip()
        password = self.ent_password.get()

        if not username:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tên đăng nhập.")
            self.ent_username.focus_set()
            return

        if not password:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mật khẩu.")
            self.ent_password.focus_set()
            return

        # Gọi AuthService để đối soát SHA-256
        user = self.auth_service.login(username, password)
        if user:
            # Đăng nhập thành công: hủy cửa sổ login và gọi callback mở MainWindow
            self.destroy()
            self.on_login_success(user)
        else:
            messagebox.showerror(
                "Đăng nhập thất bại",
                "Tên đăng nhập hoặc mật khẩu không chính xác!\nVui lòng kiểm tra lại.",
            )
            self.ent_password.delete(0, "end")
            self.ent_password.focus_set()
