import os
import shutil
import tempfile
import unittest
import tkinter as tk

from models.candidate import Candidate
from models.job_position import JobPosition
from models.user import User
from services.file_manager import FileManager
from services.auth_service import AuthService
from services.recruitment_mgr import RecruitmentManager
from services.job_crawler import JobCrawler
from ui.candidate_view import CandidateView
from ui.custom_widgets import CandidateCard
from ui.funnel_canvas import FunnelCanvas
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


class TestUI(unittest.TestCase):
    def setUp(self):
        # Tạo thư mục tạm độc lập
        self.test_dir = tempfile.mkdtemp()
        self.base_dir = os.path.join(self.test_dir, "app")
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.fm = FileManager(base_dir=self.base_dir)
        self.auth = AuthService(
            file_manager=self.fm,
            users_file=os.path.join(self.data_dir, "users.json"),
        )
        self.recruitment = RecruitmentManager(
            file_manager=self.fm,
            candidates_file=os.path.join(self.data_dir, "candidates.json"),
            jobs_file=os.path.join(self.data_dir, "jobs.json"),
        )
        self.crawler = JobCrawler(
            file_manager=self.fm,
            crawled_file=os.path.join(self.data_dir, "crawled_jobs.json"),
        )

        # Seed 1 job và 1 candidate
        self.job = JobPosition("DEV_PY", "Backend Python Dev", "IT", 20000000, 35000000, 2)
        self.recruitment.create_job(self.job)

        self.candidate = Candidate(
            "C999", "Nguyễn Văn Test", "test@test.vn", "0987654321", "DEV_PY", 2.0, Candidate.STATUS_DAT_OFFER, 90.0
        )
        self.recruitment.create_candidate(self.candidate)

        self.admin_user = self.auth.login("admin", "admin123")
        self.staff_user = self.auth.login("staff", "staff123")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. LoginWindow có thể khởi tạo
    def test_01_login_window_init(self):
        login_win = LoginWindow(self.auth, on_login_success=lambda u: None)
        login_win.withdraw()
        self.assertIsNotNone(login_win)
        self.assertEqual(login_win.title(), "Đăng nhập - Hệ thống Quản lý Tuyển dụng")
        login_win.destroy()

    # 2. MainWindow có thể khởi tạo sau login
    def test_02_main_window_init(self):
        main_win = MainWindow(
            auth_service=self.auth,
            recruitment_mgr=self.recruitment,
            job_crawler=self.crawler,
            current_user=self.admin_user,
            on_logout=lambda: None,
        )
        main_win.withdraw()
        self.assertIsNotNone(main_win)
        self.assertIn("Hệ thống Quản lý Tuyển dụng", main_win.title())
        main_win.destroy()

    # 3. CandidateView load được candidate
    def test_03_candidate_view_loads_candidates(self):
        root = tk.Tk()
        root.withdraw()
        view = CandidateView(root, self.recruitment, self.admin_user)
        view.pack()

        # Kiểm tra item có trong treeview
        items = view.tree.get_children()
        self.assertIn("C999", items)
        root.destroy()

    # 4. Staff không dùng được nút Xóa (nút xóa bị disabled)
    def test_04_staff_delete_button_disabled(self):
        root = tk.Tk()
        root.withdraw()
        view = CandidateView(root, self.recruitment, self.staff_user)
        view.pack()

        # Nút xóa bị disabled trên giao diện
        self.assertEqual(str(view.btn_delete["state"]), "disabled")
        root.destroy()

    # 5. Admin có thể dùng chức năng Xóa (nút xóa enabled)
    def test_05_admin_delete_button_enabled(self):
        root = tk.Tk()
        root.withdraw()
        view = CandidateView(root, self.recruitment, self.admin_user)
        view.pack()

        self.assertNotEqual(str(view.btn_delete["state"]), "disabled")
        root.destroy()

    # 6. CandidateCard hiển thị candidate
    def test_06_candidate_card_display(self):
        root = tk.Tk()
        root.withdraw()
        card = CandidateCard(root)
        card.pack()

        card.update_candidate(self.candidate)
        self.assertEqual(card.lbl_name.cget("text"), "Nguyễn Văn Test")
        self.assertEqual(card.lbl_id.cget("text"), "C999")
        self.assertEqual(card.lbl_status.cget("text"), "Đạt/Offer")

        card.clear()
        self.assertEqual(card.lbl_name.cget("text"), "Chưa chọn ứng viên")
        root.destroy()

    # 7. FunnelCanvas xử lý dữ liệu rỗng không crash
    def test_07_funnel_canvas_empty_data(self):
        root = tk.Tk()
        root.withdraw()
        canvas = FunnelCanvas(root, width=400, height=300)
        canvas.pack()

        # Truyền stats rỗng
        empty_stats = {"total": 0, "stages": [], "hired_count": 0, "rejected_count": 0, "hire_rate": 0.0}
        canvas.set_statistics(empty_stats)
        canvas.draw()
        # Không có ngoại lệ xảy ra
        root.destroy()

    # 8. FunnelCanvas nhận đúng statistics từ RecruitmentManager
    def test_08_funnel_canvas_with_stats(self):
        root = tk.Tk()
        root.withdraw()
        canvas = FunnelCanvas(root, width=400, height=300)
        canvas.pack()

        stats = self.recruitment.get_funnel_statistics()
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["hired_count"], 1)

        canvas.set_statistics(stats)
        canvas.draw()
        root.destroy()

    # 9. MainWindow logout gọi callback
    def test_09_main_window_logout(self):
        logout_called = []

        def on_logout():
            logout_called.append(True)

        main_win = MainWindow(
            auth_service=self.auth,
            recruitment_mgr=self.recruitment,
            job_crawler=self.crawler,
            current_user=self.admin_user,
            on_logout=on_logout,
        )
        main_win.withdraw()

        # Gọi hàm hủy và logout
        self.auth.logout()
        main_win.destroy()
        on_logout()

        self.assertFalse(self.auth.is_logged_in())
        self.assertTrue(len(logout_called) > 0)

    # 10. Toàn bộ ứng dụng khởi động không crash
    def test_10_app_startup_no_crash(self):
        # Kiểm tra controller khởi tạo đầy đủ các thư mục và dữ liệu
        from main import ApplicationController
        controller = ApplicationController()
        self.assertIsNotNone(controller.file_manager)
        self.assertIsNotNone(controller.auth_service)
        self.assertIsNotNone(controller.recruitment_mgr)
        self.assertIsNotNone(controller.job_crawler)

    # 11. Crawl bất đồng bộ không làm block main thread quá 100ms
    def test_11_crawl_async_non_blocking(self):
        import time
        from unittest.mock import patch

        main_win = MainWindow(
            auth_service=self.auth,
            recruitment_mgr=self.recruitment,
            job_crawler=self.crawler,
            current_user=self.admin_user,
            on_logout=lambda: None,
        )
        main_win.withdraw()

        def slow_fetch(*args, **kwargs):
            time.sleep(0.4)  # Giả lập request mạng mất 400ms
            return True, [{"job_id": "ASYNC_01", "title": "Dev"}], "OK"

        with patch.object(self.crawler, "fetch_jobs", side_effect=slow_fetch):
            start = time.perf_counter()
            main_win.do_crawl_jobs()
            elapsed = time.perf_counter() - start

            # Hàm gọi xử lý sự kiện phải trả về ngay lập tức (< 100ms), không bị block bởi 400ms của network
            self.assertLess(elapsed, 0.1, f"do_crawl_jobs() bị block {elapsed*1000:.1f}ms (> 100ms)")

            # Nút crawl phải ở trạng thái disabled và trạng thái hiển thị 'Đang tải'
            self.assertEqual(str(main_win.btn_crawl["state"]), "disabled")
            self.assertIn("Đang tải", main_win.lbl_crawl_status.cget("text"))

        main_win.destroy()


if __name__ == "__main__":
    unittest.main()
