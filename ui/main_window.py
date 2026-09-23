import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from typing import Callable, Optional

from models.job_position import JobPosition
from models.user import User
from services.auth_service import AuthService
from services.recruitment_mgr import RecruitmentManager
from services.job_crawler import JobCrawler
from ui.candidate_view import CandidateView


class MainWindow(tk.Tk):
    """
    Cửa sổ chính của Hệ thống Quản lý Tuyển dụng:
    - Menu bar: Hệ thống, Quản lý, Crawl dữ liệu, Thống kê.
    - Tabs quản lý thông minh (ttk.Notebook):
      + Tab 1: Quản lý Ứng viên (CandidateView + FunnelChart + CandidateCard).
      + Tab 2: Quản lý Vị trí Tuyển dụng (JobPosition CRUD đầy đủ).
      + Tab 3: Thu thập Tin tuyển dụng IT (JobCrawler UI với fallback offline).
    - Status bar cố định ở đáy: "Sẵn sàng | User: ... | Role: ... | Version 1.0.0".
    - Xử lý Đăng xuất mượt mà quay trở lại LoginWindow.
    - Tuân thủ quy tắc layout: bên trong LabelFrame chỉ dùng grid(), các container lớn dùng pack().
    """

    def __init__(
        self,
        auth_service: AuthService,
        recruitment_mgr: RecruitmentManager,
        job_crawler: JobCrawler,
        current_user: User,
        on_logout: Callable[[], None],
    ):
        super().__init__()
        self.auth_service = auth_service
        self.recruitment_mgr = recruitment_mgr
        self.job_crawler = job_crawler
        self.current_user = current_user
        self.on_logout = on_logout
        self._crawl_queue = queue.Queue()

        self.title("Hệ thống Quản lý Tuyển dụng - Đề tài 23")
        self.geometry("1100x720")
        self.minsize(980, 640)

        # Căn giữa cửa sổ
        self._center_window(1100, 720)

        self._build_menu()
        self._build_tabs()
        self._build_status_bar()

    def _center_window(self, width: int, height: int):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width // 2) - (width // 2))
        y = max(0, (screen_height // 2) - (height // 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    # =========================================================================
    # MENU BAR
    # =========================================================================
    def _build_menu(self):
        menubar = tk.Menu(self)

        # 1. Menu Hệ thống
        menu_system = tk.Menu(menubar, tearoff=0)
        menu_system.add_command(label="Đăng xuất", command=self.do_logout)
        menu_system.add_separator()
        menu_system.add_command(label="Thoát", command=self.destroy)
        menubar.add_cascade(label="Hệ thống", menu=menu_system)

        # 2. Menu Quản lý
        menu_mgmt = tk.Menu(menubar, tearoff=0)
        menu_mgmt.add_command(label="Ứng viên", command=lambda: self.notebook.select(0))
        menu_mgmt.add_command(label="Vị trí tuyển dụng", command=lambda: self.notebook.select(1))
        menubar.add_cascade(label="Quản lý", menu=menu_mgmt)

        # 3. Menu Crawl dữ liệu
        menu_crawl = tk.Menu(menubar, tearoff=0)
        menu_crawl.add_command(label="Crawl tin IT", command=lambda: self.notebook.select(2))
        menubar.add_cascade(label="Crawl dữ liệu", menu=menu_crawl)

        # 4. Menu Thống kê
        menu_stats = tk.Menu(menubar, tearoff=0)
        menu_stats.add_command(label="Funnel tuyển dụng", command=lambda: self.notebook.select(0))
        menubar.add_cascade(label="Thống kê", menu=menu_stats)

        self.config(menu=menubar)

    # =========================================================================
    # TABS (NOTEBOOK)
    # =========================================================================
    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Quản lý Ứng viên
        self.tab_candidates = CandidateView(
            self.notebook,
            recruitment_mgr=self.recruitment_mgr,
            current_user=self.current_user,
            on_data_changed=self.on_candidate_data_changed,
        )
        self.notebook.add(self.tab_candidates, text=" Ứng viên ")

        # Tab 2: Quản lý Vị trí Tuyển dụng
        self.tab_jobs = tk.Frame(self.notebook)
        self._build_jobs_tab()
        self.notebook.add(self.tab_jobs, text=" Vị trí tuyển dụng ")

        # Tab 3: Crawl Tin IT
        self.tab_crawler = tk.Frame(self.notebook)
        self._build_crawler_tab()
        self.notebook.add(self.tab_crawler, text=" Crawl tin IT ")

    # =========================================================================
    # TAB 2: QUẢN LÝ VỊ TRÍ TUYỂN DỤNG (JOB POSITIONS)
    # =========================================================================
    def _build_jobs_tab(self):
        parent = self.tab_jobs

        # 1. Khung Nhập liệu Vị trí Tuyển dụng (bên trên)
        self.job_form_frame = tk.LabelFrame(
            parent,
            text=" THÔNG TIN VỊ TRÍ TUYỂN DỤNG ",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=10,
        )
        self.job_form_frame.pack(fill="x", padx=10, pady=8)

        # Layout trong LabelFrame chỉ dùng grid()
        jf = self.job_form_frame

        tk.Label(jf, text="Mã vị trí:*").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_job_id = ttk.Entry(jf, width=16)
        self.ent_job_id.grid(row=0, column=1, sticky="w", padx=6, pady=4)

        tk.Label(jf, text="Tiêu đề:*").grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        self.ent_job_title = ttk.Entry(jf, width=28)
        self.ent_job_title.grid(row=0, column=3, sticky="ew", padx=6, pady=4)

        tk.Label(jf, text="Phòng ban:*").grid(row=0, column=4, sticky="w", padx=(10, 0), pady=4)
        self.ent_job_dept = ttk.Entry(jf, width=20)
        self.ent_job_dept.grid(row=0, column=5, sticky="ew", padx=6, pady=4)

        tk.Label(jf, text="Lương tối thiểu:*").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_job_min = ttk.Entry(jf, width=16)
        self.ent_job_min.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        tk.Label(jf, text="Lương tối đa:*").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=4)
        self.ent_job_max = ttk.Entry(jf, width=28)
        self.ent_job_max.grid(row=1, column=3, sticky="ew", padx=6, pady=4)

        tk.Label(jf, text="Chỉ tiêu (người):*").grid(row=1, column=4, sticky="w", padx=(10, 0), pady=4)
        self.ent_job_quota = ttk.Entry(jf, width=20)
        self.ent_job_quota.grid(row=1, column=5, sticky="ew", padx=6, pady=4)

        tk.Label(jf, text="Trạng thái:").grid(row=2, column=0, sticky="w", pady=4)
        self.cbo_job_status = ttk.Combobox(
            jf,
            values=[JobPosition.STATUS_DANG_TUYEN, JobPosition.STATUS_TAM_DUNG, JobPosition.STATUS_DA_DONG],
            width=14,
            state="readonly",
        )
        self.cbo_job_status.grid(row=2, column=1, sticky="w", padx=6, pady=4)
        self.cbo_job_status.set(JobPosition.STATUS_DANG_TUYEN)

        # Hàng nút tác vụ
        btn_box = tk.Frame(jf)
        btn_box.grid(row=3, column=0, columnspan=6, sticky="ew", pady=(10, 2))

        self.btn_job_add = ttk.Button(btn_box, text="Thêm vị trí", command=self.on_btn_job_add)
        self.btn_job_add.pack(side="left", padx=4)

        self.btn_job_update = ttk.Button(btn_box, text="Cập nhật", command=self.on_btn_job_update)
        self.btn_job_update.pack(side="left", padx=4)

        self.btn_job_delete = ttk.Button(btn_box, text="Xóa vị trí", command=self.on_btn_job_delete)
        self.btn_job_delete.pack(side="left", padx=4)

        # Phân quyền: Staff không thể xóa vị trí tuyển dụng
        if self.current_user.is_staff():
            self.btn_job_delete.config(state="disabled")

        self.btn_job_clear = ttk.Button(btn_box, text="Làm mới form", command=self.clear_job_form)
        self.btn_job_clear.pack(side="left", padx=4)

        # 2. Khung Bảng Danh sách Vị trí Tuyển dụng (bên dưới)
        self.job_table_frame = tk.LabelFrame(
            parent,
            text=" DANH SÁCH VỊ TRÍ TUYỂN DỤNG ",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
        )
        self.job_table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        columns = ("id", "title", "dept", "min_sal", "max_sal", "quota", "status")
        self.job_tree = ttk.Treeview(self.job_table_frame, columns=columns, show="headings", height=12)

        self.job_tree.heading("id", text="Mã vị trí")
        self.job_tree.heading("title", text="Tiêu đề chức danh")
        self.job_tree.heading("dept", text="Phòng ban")
        self.job_tree.heading("min_sal", text="Lương tối thiểu (VNĐ)")
        self.job_tree.heading("max_sal", text="Lương tối đa (VNĐ)")
        self.job_tree.heading("quota", text="Chỉ tiêu")
        self.job_tree.heading("status", text="Trạng thái")

        self.job_tree.column("id", width=100, anchor="center")
        self.job_tree.column("title", width=220, anchor="w")
        self.job_tree.column("dept", width=160, anchor="w")
        self.job_tree.column("min_sal", width=130, anchor="e")
        self.job_tree.column("max_sal", width=130, anchor="e")
        self.job_tree.column("quota", width=80, anchor="center")
        self.job_tree.column("status", width=110, anchor="center")

        scroll_job = ttk.Scrollbar(self.job_table_frame, orient="vertical", command=self.job_tree.yview)
        self.job_tree.configure(yscrollcommand=scroll_job.set)

        # Grid trong LabelFrame
        self.job_tree.grid(row=0, column=0, sticky="nsew")
        scroll_job.grid(row=0, column=1, sticky="ns")

        self.job_table_frame.grid_rowconfigure(0, weight=1)
        self.job_table_frame.grid_columnconfigure(0, weight=1)

        self.job_tree.bind("<<TreeviewSelect>>", self.on_job_tree_select)
        self.refresh_job_list()

    def refresh_job_list(self):
        """Cập nhật dữ liệu vào bảng vị trí tuyển dụng."""
        self.job_tree.delete(*self.job_tree.get_children())
        jobs = self.recruitment_mgr.get_jobs()
        for j in jobs:
            self.job_tree.insert(
                "",
                "end",
                iid=j.position_id,
                values=(
                    j.position_id,
                    j.title,
                    j.department,
                    f"{j.min_salary:,.0f}",
                    f"{j.max_salary:,.0f}",
                    j.quota,
                    j.status,
                ),
            )

    def on_job_tree_select(self, event):
        """Nạp thông tin vị trí vào form khi bấm chọn dòng."""
        selected = self.job_tree.selection()
        if not selected:
            return
        job_id = selected[0]
        job = self.recruitment_mgr.get_job_by_id(job_id)
        if not job:
            return

        self.ent_job_id.delete(0, "end")
        self.ent_job_id.insert(0, job.position_id)
        self.ent_job_id.config(state="disabled")

        self.ent_job_title.delete(0, "end")
        self.ent_job_title.insert(0, job.title)

        self.ent_job_dept.delete(0, "end")
        self.ent_job_dept.insert(0, job.department)

        self.ent_job_min.delete(0, "end")
        self.ent_job_min.insert(0, str(int(job.min_salary)))

        self.ent_job_max.delete(0, "end")
        self.ent_job_max.insert(0, str(int(job.max_salary)))

        self.ent_job_quota.delete(0, "end")
        self.ent_job_quota.insert(0, str(job.quota))

        self.cbo_job_status.set(job.status)

    def clear_job_form(self):
        """Xóa trắng form nhập vị trí."""
        self.ent_job_id.config(state="normal")
        self.ent_job_id.delete(0, "end")
        self.ent_job_title.delete(0, "end")
        self.ent_job_dept.delete(0, "end")
        self.ent_job_min.delete(0, "end")
        self.ent_job_max.delete(0, "end")
        self.ent_job_quota.delete(0, "end")
        self.cbo_job_status.set(JobPosition.STATUS_DANG_TUYEN)
        if self.job_tree.selection():
            self.job_tree.selection_remove(self.job_tree.selection())

    def _read_job_from_form(self) -> JobPosition:
        j_id = self.ent_job_id.get().strip()
        title = self.ent_job_title.get().strip()
        dept = self.ent_job_dept.get().strip()
        min_str = self.ent_job_min.get().strip()
        max_str = self.ent_job_max.get().strip()
        quota_str = self.ent_job_quota.get().strip()
        status = self.cbo_job_status.get().strip()

        if not j_id:
            raise ValueError("Vui lòng nhập Mã vị trí.")
        if not title:
            raise ValueError("Vui lòng nhập Tiêu đề vị trí.")
        if not dept:
            raise ValueError("Vui lòng nhập Phòng ban.")

        try:
            min_sal = float(min_str)
            max_sal = float(max_str)
        except ValueError:
            raise ValueError("Lương phải là số hợp lệ.")

        try:
            quota = int(quota_str)
        except ValueError:
            raise ValueError("Chỉ tiêu tuyển dụng phải là số nguyên.")

        return JobPosition(
            position_id=j_id,
            title=title,
            department=dept,
            min_salary=min_sal,
            max_salary=max_sal,
            quota=quota,
            status=status,
        )

    def on_btn_job_add(self):
        try:
            job = self._read_job_from_form()
            self.recruitment_mgr.create_job(job)
            messagebox.showinfo("Thành công", f"Đã thêm vị trí '{job.title}' thành công.")
            self.clear_job_form()
            self.refresh_job_list()
            self.tab_candidates.refresh_positions()
        except (ValueError, TypeError) as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể thêm vị trí: {e}")

    def on_btn_job_update(self):
        selected = self.job_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một vị trí để cập nhật.")
            return

        try:
            self.ent_job_id.config(state="normal")
            job = self._read_job_from_form()
            self.ent_job_id.config(state="disabled")

            self.recruitment_mgr.update_job(job)
            messagebox.showinfo("Thành công", f"Đã cập nhật vị trí '{job.title}' thành công.")
            self.refresh_job_list()
            self.tab_candidates.refresh_positions()
        except (ValueError, TypeError) as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể cập nhật: {e}")

    def on_btn_job_delete(self):
        selected = self.job_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một vị trí để xóa.")
            return

        job_id = selected[0]
        confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa vị trí '{job_id}'?")
        if not confirm:
            return

        try:
            self.recruitment_mgr.delete_job(job_id, current_user=self.current_user)
            messagebox.showinfo("Thành công", f"Đã xóa vị trí '{job_id}'.")
            self.clear_job_form()
            self.refresh_job_list()
            self.tab_candidates.refresh_positions()
        except PermissionError as e:
            messagebox.showerror("Không có quyền", str(e))
        except ValueError as e:
            messagebox.showerror("Ràng buộc dữ liệu", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể xóa: {e}")

    # =========================================================================
    # TAB 3: CRAWL TIN TUYỂN DỤNG IT
    # =========================================================================
    def _build_crawler_tab(self):
        parent = self.tab_crawler

        # Khung điều khiển Crawler (LabelFrame với grid)
        ctrl_frame = tk.LabelFrame(
            parent,
            text=" THÔNG SỐ CRAWL TIN TUYỂN DỤNG IT ",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=10,
        )
        ctrl_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(ctrl_frame, text="Từ khóa tìm kiếm (Keyword):").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_crawl_kw = ttk.Entry(ctrl_frame, width=20)
        self.ent_crawl_kw.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        self.ent_crawl_kw.insert(0, "python")

        tk.Label(ctrl_frame, text="Nguồn API (Source URL):").grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        self.ent_crawl_url = ttk.Entry(ctrl_frame, width=40)
        self.ent_crawl_url.grid(row=0, column=3, sticky="ew", padx=6, pady=4)
        self.ent_crawl_url.insert(0, self.job_crawler.DEFAULT_API_URL)

        self.btn_crawl = ttk.Button(ctrl_frame, text="Bắt đầu Crawl", command=self.do_crawl_jobs)
        self.btn_crawl.grid(row=0, column=4, padx=8, pady=4)

        # Nhãn hiển thị trạng thái crawl
        self.lbl_crawl_status = tk.Label(
            ctrl_frame,
            text="Sẵn sàng thu thập dữ liệu việc làm IT.",
            font=("Segoe UI", 9, "italic"),
            fg="#2980b9",
        )
        self.lbl_crawl_status.grid(row=1, column=0, columnspan=5, sticky="w", pady=(6, 0))

        # Khung bảng hiển thị tin crawl được
        res_frame = tk.LabelFrame(
            parent,
            text=" DANH SÁCH VIỆC LÀM IT ĐÃ THU THẬP ",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
        )
        res_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        columns = ("id", "title", "company", "location", "salary", "date", "tags")
        self.crawl_tree = ttk.Treeview(res_frame, columns=columns, show="headings", height=12)

        self.crawl_tree.heading("id", text="Mã việc làm")
        self.crawl_tree.heading("title", text="Tiêu đề tuyển dụng")
        self.crawl_tree.heading("company", text="Công ty")
        self.crawl_tree.heading("location", text="Địa điểm")
        self.crawl_tree.heading("salary", text="Mức lương")
        self.crawl_tree.heading("date", text="Ngày đăng")
        self.crawl_tree.heading("tags", text="Kỹ năng yêu cầu")

        self.crawl_tree.column("id", width=80, anchor="center")
        self.crawl_tree.column("title", width=220, anchor="w")
        self.crawl_tree.column("company", width=140, anchor="w")
        self.crawl_tree.column("location", width=130, anchor="center")
        self.crawl_tree.column("salary", width=140, anchor="center")
        self.crawl_tree.column("date", width=90, anchor="center")
        self.crawl_tree.column("tags", width=160, anchor="w")

        scroll_crawl = ttk.Scrollbar(res_frame, orient="vertical", command=self.crawl_tree.yview)
        self.crawl_tree.configure(yscrollcommand=scroll_crawl.set)

        self.crawl_tree.grid(row=0, column=0, sticky="nsew")
        scroll_crawl.grid(row=0, column=1, sticky="ns")

        res_frame.grid_rowconfigure(0, weight=1)
        res_frame.grid_columnconfigure(0, weight=1)

        # Nạp dữ liệu đã lưu từ trước (nếu có)
        self._load_existing_crawled_jobs()

    def _load_existing_crawled_jobs(self):
        saved = self.job_crawler.load_saved_crawled_jobs()
        if saved:
            self._display_crawled_jobs(saved)

    def _display_crawled_jobs(self, jobs):
        self.crawl_tree.delete(*self.crawl_tree.get_children())
        for j in jobs:
            self.crawl_tree.insert(
                "",
                "end",
                values=(
                    j.get("job_id", "--"),
                    j.get("title", "--"),
                    j.get("company", "--"),
                    j.get("location", "--"),
                    j.get("salary", "--"),
                    j.get("published_date", "--"),
                    j.get("tags", "--"),
                ),
            )

    def do_crawl_jobs(self):
        """Kích hoạt crawl tin IT trên worker thread riêng để không gây treo UI."""
        kw = self.ent_crawl_kw.get().strip() or "python"
        url = self.ent_crawl_url.get().strip() or None

        # Vô hiệu hóa nút và hiển thị trạng thái đang tải
        self.btn_crawl.config(state="disabled")
        self.lbl_crawl_status.config(text="Đang tải dữ liệu...", fg="#e67e22")

        # Worker thread xử lý request mạng hoàn toàn tách biệt với Tkinter main thread
        def worker():
            try:
                result = self.job_crawler.fetch_jobs(
                    keyword=kw,
                    source_url=url,
                    use_fallback_on_error=True,
                )
                self._crawl_queue.put(result)
            except Exception as ex:
                self._crawl_queue.put((False, [], f"Lỗi không xác định: {ex}"))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        # Main thread định kỳ kiểm tra queue sau mỗi 100ms
        self.after(100, self._poll_crawl_queue)

    def _poll_crawl_queue(self):
        """Main thread kiểm tra queue và cập nhật widget Tkinter an toàn."""
        try:
            success, jobs, message = self._crawl_queue.get_nowait()
        except queue.Empty:
            # Chưa có dữ liệu: tiếp tục chờ và poll lại sau 100ms
            self.after(100, self._poll_crawl_queue)
            return

        # Đã có dữ liệu trong main thread: phục hồi trạng thái nút và cập nhật UI
        self.btn_crawl.config(state="normal")
        self._display_crawled_jobs(jobs)

        if success:
            self.lbl_crawl_status.config(text=f"✔ {message}", fg="#27ae60")
            self.job_crawler.save_crawled_jobs(jobs)
            messagebox.showinfo("Thu thập hoàn tất", message)
        else:
            self.lbl_crawl_status.config(text=f"⚠ {message}", fg="#c0392b")
            messagebox.showwarning("Cảnh báo mạng", message)

    # =========================================================================
    # STATUS BAR & LOGOUT
    # =========================================================================
    def _build_status_bar(self):
        status_text = f"Sẵn sàng | User: {self.current_user.username} | Role: {self.current_user.role} | Version 1.0.0"
        self.lbl_statusbar = tk.Label(
            self,
            text=status_text,
            bd=1,
            relief="sunken",
            anchor="w",
            padx=10,
            pady=3,
            font=("Segoe UI", 9),
            bg="#f1f2f6",
            fg="#2f3542",
        )
        self.lbl_statusbar.pack(side="bottom", fill="x")

    def on_candidate_data_changed(self):
        """Callback khi ứng viên thay đổi: đồng bộ cập nhật sang các tab khác."""
        pass

    def do_logout(self):
        """Xác nhận và thực hiện đăng xuất."""
        confirm = messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?")
        if not confirm:
            return

        self.auth_service.logout()
        self.destroy()
        self.on_logout()
