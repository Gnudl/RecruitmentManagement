import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Callable

from models.candidate import Candidate
from models.user import User
from services.recruitment_mgr import RecruitmentManager
from ui.custom_widgets import CandidateCard
from ui.funnel_canvas import FunnelCanvas


class CandidateView(tk.Frame):
    """
    Khu vực Quản lý Ứng viên:
    - Giao diện gồm 3 tầng:
      1. Khung Nhập liệu (Trái) & Khung Tìm kiếm / Bộ lọc (Phải).
      2. Bảng Danh sách ứng viên (Treeview có tô màu trạng thái).
      3. Biểu đồ Funnel Chart (Trái) & Thẻ CandidateCard chi tiết (Phải).
    - Tuân thủ nghiêm ngặt quy tắc Layout:
      + Container cấp ngoài dùng pack().
      + Bên trong mỗi LabelFrame CHỈ DÙNG grid().
    - Tuân thủ nguyên tắc phân quyền: Staff không thể xóa ứng viên.
    """

    def __init__(
        self,
        parent,
        recruitment_mgr: RecruitmentManager,
        current_user: User,
        on_data_changed: Optional[Callable] = None,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.recruitment_mgr = recruitment_mgr
        self.current_user = current_user
        self.on_data_changed = on_data_changed

        self.selected_candidate_id: Optional[str] = None

        self._build_layout()
        self.refresh_all()

    def _build_layout(self):
        # =====================================================================
        # TẦNG 1: KHUNG NHẬP LIỆU VÀ TÌM KIẾM / LỌC
        # =====================================================================
        top_container = tk.Frame(self)
        top_container.pack(fill="x", padx=8, pady=6)

        # 1.1. Khung Nhập liệu (bên trái)
        self.form_frame = tk.LabelFrame(
            top_container,
            text=" THÔNG TIN ỨNG VIÊN ",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
        )
        self.form_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self._build_form_grid()

        # 1.2. Khung Tìm kiếm & Bộ lọc (bên phải)
        self.filter_frame = tk.LabelFrame(
            top_container,
            text=" TÌM KIẾM & BỘ LỌC ",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
        )
        self.filter_frame.pack(side="right", fill="both", expand=True, padx=(4, 0))
        self._build_filter_grid()

        # =====================================================================
        # TẦNG 2: DANH SÁCH ỨNG VIÊN (TREEVIEW)
        # =====================================================================
        list_container = tk.Frame(self)
        list_container.pack(fill="both", expand=True, padx=8, pady=4)

        self.table_frame = tk.LabelFrame(
            list_container,
            text=" DANH SÁCH ỨNG VIÊN TUYỂN DỤNG ",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=6,
        )
        self.table_frame.pack(fill="both", expand=True)
        self._build_table_grid()

        # =====================================================================
        # TẦNG 3: FUNNEL CHART VÀ CANDIDATE CARD
        # =====================================================================
        bottom_container = tk.Frame(self)
        bottom_container.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # 3.1. Funnel Chart (Trái)
        self.funnel_box = tk.LabelFrame(
            bottom_container,
            text=" BIỂU ĐỒ PHỄU TUYỂN DỤNG (FUNNEL) ",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=6,
        )
        self.funnel_box.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.funnel_canvas = FunnelCanvas(self.funnel_box, height=190)
        self.funnel_canvas.pack(fill="both", expand=True)

        # 3.2. Candidate Card (Phải)
        self.card_box = tk.LabelFrame(
            bottom_container,
            text=" CHI TIẾT ỨNG VIÊN ",
            font=("Segoe UI", 9, "bold"),
            padx=4,
            pady=4,
        )
        self.card_box.pack(side="right", fill="both", expand=True, padx=(4, 0))
        self.candidate_card = CandidateCard(self.card_box)
        self.candidate_card.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # XÂY DỰNG GRID TRONG KHUNG NHẬP LIỆU
    # -------------------------------------------------------------------------
    def _build_form_grid(self):
        f = self.form_frame

        # Dòng 0: Mã ứng viên & Họ tên
        tk.Label(f, text="Mã ứng viên:*", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=3)
        self.ent_id = ttk.Entry(f, width=16)
        self.ent_id.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        tk.Label(f, text="Họ và tên:*", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(10, 0), pady=3)
        self.ent_name = ttk.Entry(f, width=22)
        self.ent_name.grid(row=0, column=3, sticky="ew", padx=5, pady=3)

        # Dòng 1: Email & Số điện thoại
        tk.Label(f, text="Email:*", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_email = ttk.Entry(f, width=16)
        self.ent_email.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(f, text="Số ĐT:*", font=("Segoe UI", 9)).grid(row=1, column=2, sticky="w", padx=(10, 0), pady=3)
        self.ent_phone = ttk.Entry(f, width=22)
        self.ent_phone.grid(row=1, column=3, sticky="ew", padx=5, pady=3)

        # Dòng 2: Vị trí tuyển dụng & Kinh nghiệm
        tk.Label(f, text="Vị trí:*", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=3)
        self.cbo_position = ttk.Combobox(f, width=14, state="readonly")
        self.cbo_position.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(f, text="Kinh nghiệm (năm):", font=("Segoe UI", 9)).grid(row=2, column=2, sticky="w", padx=(10, 0), pady=3)
        self.ent_exp = ttk.Entry(f, width=22)
        self.ent_exp.grid(row=2, column=3, sticky="w", padx=5, pady=3)

        # Dòng 3: Vòng tuyển dụng & Điểm đánh giá
        tk.Label(f, text="Vòng/Trạng thái:", font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=3)
        self.cbo_status = ttk.Combobox(f, values=Candidate.VALID_STATUSES, width=14, state="readonly")
        self.cbo_status.grid(row=3, column=1, sticky="ew", padx=5, pady=3)
        self.cbo_status.set(Candidate.STATUS_NOP_HO_SO)

        tk.Label(f, text="Điểm PV (0-100):", font=("Segoe UI", 9)).grid(row=3, column=2, sticky="w", padx=(10, 0), pady=3)
        self.ent_score = ttk.Entry(f, width=22)
        self.ent_score.grid(row=3, column=3, sticky="w", padx=5, pady=3)
        self.ent_score.insert(0, "0")

        # Dòng 4: Hàng nút bấm tác vụ
        btn_box = tk.Frame(f)
        btn_box.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        self.btn_add = ttk.Button(btn_box, text="Thêm", command=self.on_btn_add_click)
        self.btn_add.pack(side="left", padx=4)

        self.btn_update = ttk.Button(btn_box, text="Cập nhật", command=self.on_btn_update_click)
        self.btn_update.pack(side="left", padx=4)

        self.btn_delete = ttk.Button(btn_box, text="Xóa", command=self.on_btn_delete_click)
        self.btn_delete.pack(side="left", padx=4)

        # Ràng buộc phân quyền: Nếu là Staff, vô hiệu hóa nút xóa
        if self.current_user.is_staff():
            self.btn_delete.config(state="disabled")

        self.btn_clear = ttk.Button(btn_box, text="Làm mới form", command=self.clear_form)
        self.btn_clear.pack(side="left", padx=4)

    # -------------------------------------------------------------------------
    # XÂY DỰNG GRID TRONG KHUNG TÌM KIẾM & BỘ LỌC
    # -------------------------------------------------------------------------
    def _build_filter_grid(self):
        f = self.filter_frame

        # Dòng 0: Từ khóa tìm kiếm
        tk.Label(f, text="Từ khóa (Tên / SĐT):", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=4)
        self.ent_search = ttk.Entry(f, width=22)
        self.ent_search.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.ent_search.bind("<Return>", lambda e: self.on_btn_search_click())

        self.btn_search = ttk.Button(f, text="Tìm kiếm", command=self.on_btn_search_click)
        self.btn_search.grid(row=0, column=2, sticky="w", padx=4, pady=4)

        # Dòng 1: Lọc theo Vị trí tuyển dụng
        tk.Label(f, text="Lọc theo Vị trí:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_filter_pos = ttk.Combobox(f, width=20, state="readonly")
        self.cbo_filter_pos.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        self.cbo_filter_pos.bind("<<ComboboxSelected>>", lambda e: self.on_btn_filter_click())

        # Dòng 2: Lọc theo Trạng thái / Vòng
        tk.Label(f, text="Lọc theo Trạng thái:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        status_options = ["Tất cả"] + Candidate.VALID_STATUSES
        self.cbo_filter_status = ttk.Combobox(f, values=status_options, width=20, state="readonly")
        self.cbo_filter_status.grid(row=2, column=1, sticky="ew", padx=6, pady=4)
        self.cbo_filter_status.set("Tất cả")
        self.cbo_filter_status.bind("<<ComboboxSelected>>", lambda e: self.on_btn_filter_click())

        # Dòng 3: Nút Lọc, Đặt lại & Xuất CSV
        action_box = tk.Frame(f)
        action_box.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        ttk.Button(action_box, text="Lọc dữ liệu", command=self.on_btn_filter_click).pack(side="left", padx=4)
        ttk.Button(action_box, text="Đặt lại bộ lọc", command=self.reset_filter).pack(side="left", padx=4)
        ttk.Button(action_box, text="Xuất CSV báo cáo", command=self.export_csv).pack(side="right", padx=4)

    # -------------------------------------------------------------------------
    # XÂY DỰNG GRID TRONG BẢNG DỮ LIỆU TREEVIEW
    # -------------------------------------------------------------------------
    def _build_table_grid(self):
        f = self.table_frame

        columns = ("id", "name", "email", "phone", "position", "exp", "score", "status")
        self.tree = ttk.Treeview(f, columns=columns, show="headings", height=8, selectmode="browse")

        self.tree.heading("id", text="Mã ID")
        self.tree.heading("name", text="Họ và tên")
        self.tree.heading("email", text="Email")
        self.tree.heading("phone", text="Số điện thoại")
        self.tree.heading("position", text="Vị trí")
        self.tree.heading("exp", text="Kinh nghiệm")
        self.tree.heading("score", text="Điểm PV")
        self.tree.heading("status", text="Trạng thái / Vòng")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("name", width=140, anchor="w")
        self.tree.column("email", width=160, anchor="w")
        self.tree.column("phone", width=100, anchor="center")
        self.tree.column("position", width=90, anchor="center")
        self.tree.column("exp", width=80, anchor="center")
        self.tree.column("score", width=70, anchor="center")
        self.tree.column("status", width=130, anchor="center")

        # Cấu hình màu sắc nổi bật cho các trạng thái tuyển dụng
        self.tree.tag_configure("tag_offer", background="#d4efdf", foreground="#196f3d")   # Xanh lá nhẹ
        self.tree.tag_configure("tag_loai", background="#fadbd8", foreground="#943126")    # Đỏ nhạt
        self.tree.tag_configure("tag_interview", background="#fef9e7", foreground="#7d6608") # Vàng nhạt

        # Thanh cuộn dọc
        scrollbar = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)

        # Bắt sự kiện chọn dòng
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    # -------------------------------------------------------------------------
    # TẢI DỮ LIỆU & CẬP NHẬT GIAO DIỆN
    # -------------------------------------------------------------------------
    def refresh_positions(self):
        """Cập nhật danh sách vị trí tuyển dụng vào các combobox."""
        jobs = self.recruitment_mgr.get_jobs()
        job_ids = [j.position_id for j in jobs]

        self.cbo_position["values"] = job_ids
        if job_ids and not self.cbo_position.get():
            self.cbo_position.set(job_ids[0])

        filter_options = ["Tất cả"] + job_ids
        self.cbo_filter_pos["values"] = filter_options
        if not self.cbo_filter_pos.get():
            self.cbo_filter_pos.set("Tất cả")

    def load_candidates_to_tree(self, candidates: List[Candidate]):
        """Nạp danh sách ứng viên vào Treeview."""
        self.tree.delete(*self.tree.get_children())

        for c in candidates:
            # Gán tag tô màu theo trạng thái
            tag = ""
            if c.status == Candidate.STATUS_DAT_OFFER:
                tag = "tag_offer"
            elif c.status == Candidate.STATUS_LOAI:
                tag = "tag_loai"
            elif c.status in [Candidate.STATUS_PV_VONG_1, Candidate.STATUS_PV_VONG_2]:
                tag = "tag_interview"

            self.tree.insert(
                "",
                "end",
                iid=c.person_id,
                values=(
                    c.person_id,
                    c.full_name,
                    c.email,
                    c.phone,
                    c.position_id,
                    f"{c.experience_years} năm",
                    f"{c.interview_score:.1f}",
                    c.status,
                ),
                tags=(tag,) if tag else (),
            )

    def refresh_all(self):
        """Làm mới toàn bộ dữ liệu: vị trí, ứng viên, biểu đồ phễu, thẻ chi tiết."""
        self.refresh_positions()
        all_candidates = self.recruitment_mgr.get_candidates()
        self.load_candidates_to_tree(all_candidates)

        # Cập nhật Funnel Chart
        funnel_stats = self.recruitment_mgr.get_funnel_statistics()
        self.funnel_canvas.set_statistics(funnel_stats)

        # Xóa form nếu ứng viên được chọn không còn tồn tại
        if self.selected_candidate_id:
            curr = self.recruitment_mgr.get_candidate_by_id(self.selected_candidate_id)
            if curr:
                self.candidate_card.update_candidate(curr)
            else:
                self.clear_form()

        if self.on_data_changed:
            self.on_data_changed()

    def on_tree_select(self, event):
        """Khi chọn một dòng trong bảng: nạp thông tin vào form và CandidateCard."""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        c_id = selected_items[0]
        candidate = self.recruitment_mgr.get_candidate_by_id(c_id)
        if not candidate:
            return

        self.selected_candidate_id = candidate.person_id

        # Nạp dữ liệu vào form nhập liệu
        self.ent_id.delete(0, "end")
        self.ent_id.insert(0, candidate.person_id)
        self.ent_id.config(state="disabled")  # Không cho sửa ID khi cập nhật

        self.ent_name.delete(0, "end")
        self.ent_name.insert(0, candidate.full_name)

        self.ent_email.delete(0, "end")
        self.ent_email.insert(0, candidate.email)

        self.ent_phone.delete(0, "end")
        self.ent_phone.insert(0, candidate.phone)

        self.cbo_position.set(candidate.position_id)

        self.ent_exp.delete(0, "end")
        self.ent_exp.insert(0, str(candidate.experience_years))

        self.cbo_status.set(candidate.status)

        self.ent_score.delete(0, "end")
        self.ent_score.insert(0, str(candidate.interview_score))

        # Cập nhật CandidateCard
        self.candidate_card.update_candidate(candidate)

    def clear_form(self):
        """Xóa trắng form nhập liệu để chuẩn bị thêm mới."""
        self.selected_candidate_id = None
        self.ent_id.config(state="normal")
        self.ent_id.delete(0, "end")
        self.ent_name.delete(0, "end")
        self.ent_email.delete(0, "end")
        self.ent_phone.delete(0, "end")
        self.ent_exp.delete(0, "end")
        self.ent_score.delete(0, "end")
        self.ent_score.insert(0, "0")
        self.cbo_status.set(Candidate.STATUS_NOP_HO_SO)

        # Bỏ chọn trên Treeview
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

        self.candidate_card.clear()

    # -------------------------------------------------------------------------
    # XỬ LÝ CÁC TÁC VỤ CRUD
    # -------------------------------------------------------------------------
    def _read_candidate_from_form(self) -> Candidate:
        """Đọc và tạo đối tượng Candidate từ các trường trong form."""
        c_id = self.ent_id.get().strip()
        name = self.ent_name.get().strip()
        email = self.ent_email.get().strip()
        phone = self.ent_phone.get().strip()
        pos = self.cbo_position.get().strip()
        exp_str = self.ent_exp.get().strip() or "0"
        score_str = self.ent_score.get().strip() or "0"
        status = self.cbo_status.get().strip()

        if not c_id:
            raise ValueError("Vui lòng nhập Mã ứng viên.")
        if not name:
            raise ValueError("Vui lòng nhập Họ và tên ứng viên.")
        if not pos:
            raise ValueError("Vui lòng chọn Vị trí ứng tuyển.")

        try:
            exp = float(exp_str)
        except ValueError:
            raise ValueError("Kinh nghiệm phải là một con số.")

        try:
            score = float(score_str)
        except ValueError:
            raise ValueError("Điểm phỏng vấn phải là một con số.")

        # Khởi tạo Candidate (Model sẽ tự động kiểm tra regex email, phone, range điểm)
        return Candidate(
            person_id=c_id,
            full_name=name,
            email=email,
            phone=phone,
            position_id=pos,
            experience_years=exp,
            status=status,
            interview_score=score,
        )

    def on_btn_add_click(self):
        """Xử lý sự kiện Thêm ứng viên."""
        try:
            candidate = self._read_candidate_from_form()
            self.recruitment_mgr.create_candidate(candidate)
            messagebox.showinfo("Thành công", f"Đã thêm mới ứng viên '{candidate.full_name}' thành công.")
            self.clear_form()
            self.refresh_all()
        except (ValueError, TypeError) as val_err:
            messagebox.showerror("Lỗi dữ liệu", str(val_err))
        except Exception as err:
            messagebox.showerror("Lỗi hệ thống", f"Không thể thêm ứng viên: {err}")

    def on_btn_update_click(self):
        """Xử lý sự kiện Cập nhật thông tin ứng viên."""
        if not self.selected_candidate_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một ứng viên trong danh sách để cập nhật.")
            return

        try:
            # Cho phép đọc ID hiện tại
            self.ent_id.config(state="normal")
            candidate = self._read_candidate_from_form()
            self.ent_id.config(state="disabled")

            self.recruitment_mgr.update_candidate(candidate)
            messagebox.showinfo("Thành công", f"Đã cập nhật ứng viên '{candidate.full_name}' thành công.")
            self.refresh_all()
        except (ValueError, TypeError) as val_err:
            messagebox.showerror("Lỗi dữ liệu", str(val_err))
        except Exception as err:
            messagebox.showerror("Lỗi hệ thống", f"Không thể cập nhật ứng viên: {err}")

    def on_btn_delete_click(self):
        """Xử lý sự kiện Xóa ứng viên (Admin only, có xác nhận)."""
        if not self.selected_candidate_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một ứng viên trong danh sách để xóa.")
            return

        # Xác nhận thao tác xóa
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa ứng viên có mã '{self.selected_candidate_id}' không?",
        )
        if not confirm:
            return

        try:
            self.recruitment_mgr.delete_candidate(self.selected_candidate_id, current_user=self.current_user)
            messagebox.showinfo("Thành công", f"Đã xóa ứng viên '{self.selected_candidate_id}' thành công.")
            self.clear_form()
            self.refresh_all()
        except PermissionError as perm_err:
            messagebox.showerror("Không có quyền", str(perm_err))
        except ValueError as val_err:
            messagebox.showerror("Lỗi dữ liệu", str(val_err))
        except Exception as err:
            messagebox.showerror("Lỗi hệ thống", f"Không thể xóa ứng viên: {err}")

    # -------------------------------------------------------------------------
    # TÌM KIẾM, LỌC & XUẤT CSV
    # -------------------------------------------------------------------------
    def on_btn_search_click(self):
        """Tìm kiếm theo từ khóa."""
        kw = self.ent_search.get().strip()
        pos = self.cbo_filter_pos.get().strip()
        status = self.cbo_filter_status.get().strip()

        results = self.recruitment_mgr.query_candidates(
            keyword=kw,
            position_id=pos if pos != "Tất cả" else None,
            status=status if status != "Tất cả" else None,
        )
        self.load_candidates_to_tree(results)

    def on_btn_filter_click(self):
        """Thực hiện lọc kết hợp."""
        self.on_btn_search_click()

    def reset_filter(self):
        """Đặt lại toàn bộ bộ lọc về mặc định."""
        self.ent_search.delete(0, "end")
        self.cbo_filter_pos.set("Tất cả")
        self.cbo_filter_status.set("Tất cả")
        self.load_candidates_to_tree(self.recruitment_mgr.get_candidates())

    def export_csv(self):
        """Xuất danh sách ứng viên hiện đang hiển thị ra file CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file (*.csv)", "*.csv"), ("All files", "*.*")],
            title="Lưu danh sách ứng viên trúng tuyển / báo cáo",
            initialfile="danh_sach_ung_vien.csv",
        )
        if not filepath:
            return

        try:
            # Lấy danh sách ID đang hiển thị trên bảng Treeview
            displayed_ids = self.tree.get_children()
            selected_candidates = []
            for item_id in displayed_ids:
                c = self.recruitment_mgr.get_candidate_by_id(item_id)
                if c:
                    selected_candidates.append(c)

            self.recruitment_mgr.export_candidates_to_csv(filepath, selected_candidates)
            messagebox.showinfo("Thành công", f"Xuất báo cáo thành công.\nFile đã lưu tại: {filepath}")
        except Exception as e:
            messagebox.showerror("Lỗi xuất file", f"Không thể xuất file CSV: {e}")
