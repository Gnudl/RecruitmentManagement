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


class TestFullFlowVerification(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.base_dir = os.path.join(self.test_dir, "app")
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.fm = FileManager(base_dir=self.base_dir)
        self.auth = AuthService(file_manager=self.fm, users_file=os.path.join(self.data_dir, "users.json"))
        self.recruitment = RecruitmentManager(
            file_manager=self.fm,
            candidates_file=os.path.join(self.data_dir, "candidates.json"),
            jobs_file=os.path.join(self.data_dir, "jobs.json"),
        )
        self.crawler = JobCrawler(
            file_manager=self.fm,
            crawled_file=os.path.join(self.data_dir, "crawled_jobs.json"),
        )

        # Seed initial job
        self.recruitment.create_job(JobPosition("DEV_PY", "Python Dev", "IT", 20000000, 35000000, 2))

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_checklist_flow(self):
        # 1. Login hoạt động (Admin + Staff)
        admin = self.auth.login("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_admin())

        staff = self.auth.login("staff", "staff123")
        self.assertIsNotNone(staff)
        self.assertTrue(staff.is_staff())

        # 2. Candidate CRUD hoạt động
        c = Candidate("C_TEST_01", "Trần Test", "tran@test.vn", "0912345678", "DEV_PY", 2.0, Candidate.STATUS_NOP_HO_SO, 75.0)
        self.recruitment.create_candidate(c)
        self.assertIsNotNone(self.recruitment.get_candidate_by_id("C_TEST_01"))

        c.status = Candidate.STATUS_DAT_OFFER
        self.recruitment.update_candidate(c)
        self.assertEqual(self.recruitment.get_candidate_by_id("C_TEST_01").status, Candidate.STATUS_DAT_OFFER)

        # 3. Search & Filter hoạt động
        search_res = self.recruitment.search_candidates("trần")
        self.assertEqual(len(search_res), 1)

        filter_res = self.recruitment.filter_candidates(position_id="DEV_PY", status=Candidate.STATUS_DAT_OFFER)
        self.assertEqual(len(filter_res), 1)

        # 4. Permission UI & Service hoạt động
        # Staff không được xóa
        with self.assertRaises(PermissionError):
            self.recruitment.delete_candidate("C_TEST_01", current_user=staff)

        # Admin xóa thành công
        deleted = self.recruitment.delete_candidate("C_TEST_01", current_user=admin)
        self.assertTrue(deleted)
        self.assertIsNone(self.recruitment.get_candidate_by_id("C_TEST_01"))

        # 5. Job CRUD hoạt động
        job2 = JobPosition("QA_TEST", "QA Lead", "QA", 15000000, 25000000, 1)
        self.recruitment.create_job(job2)
        self.assertIsNotNone(self.recruitment.get_job_by_id("QA_TEST"))

        job2.quota = 3
        self.recruitment.update_job(job2)
        self.assertEqual(self.recruitment.get_job_by_id("QA_TEST").quota, 3)

        self.assertTrue(self.recruitment.delete_job("QA_TEST", current_user=admin))
        self.assertIsNone(self.recruitment.get_job_by_id("QA_TEST"))

        # 6. FunnelCanvas & CandidateCard hoạt động
        root = tk.Tk()
        root.withdraw()

        card = CandidateCard(root)
        card.pack()
        test_c = Candidate("C_CARD", "Card Test", "c@test.vn", "0988776655", "DEV_PY", 3.0, Candidate.STATUS_PV_VONG_1, 80.0)
        card.update_candidate(test_c)
        self.assertEqual(card.lbl_name.cget("text"), "Card Test")
        card.clear()

        canvas = FunnelCanvas(root, width=400, height=200)
        canvas.pack()
        stats = self.recruitment.get_funnel_statistics()
        canvas.set_statistics(stats)
        canvas.draw()

        # 7. CSV Export hoạt động
        csv_file = os.path.join(self.data_dir, "test_export.csv")
        self.recruitment.export_candidates_to_csv(csv_file, [test_c])
        self.assertTrue(os.path.exists(csv_file))

        # 8. Crawler UI & Service hoạt động
        success, jobs, msg = self.crawler.fetch_jobs(use_fallback_on_error=True)
        self.assertTrue(len(jobs) > 0)

        # 9. MainWindow chạy ổn định và Logout
        main_win = MainWindow(
            auth_service=self.auth,
            recruitment_mgr=self.recruitment,
            job_crawler=self.crawler,
            current_user=admin,
            on_logout=lambda: None,
        )
        main_win.withdraw()
        self.assertEqual(main_win.current_user.username, "admin")
        self.auth.logout()
        self.assertFalse(self.auth.is_logged_in())
        main_win.destroy()
        root.destroy()


if __name__ == "__main__":
    unittest.main()
