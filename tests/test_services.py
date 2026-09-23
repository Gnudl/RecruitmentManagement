import csv
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
import requests

from models.candidate import Candidate
from models.job_position import JobPosition
from models.user import User
from services.file_manager import FileManager
from services.auth_service import AuthService
from services.recruitment_mgr import RecruitmentManager
from services.job_crawler import JobCrawler


class TestServices(unittest.TestCase):
    def setUp(self):
        # Tạo thư mục tạm độc lập cho mỗi test
        self.test_dir = tempfile.mkdtemp()
        self.base_dir = os.path.join(self.test_dir, "app")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.backup_dir = os.path.join(self.base_dir, "backups")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        self.users_file = os.path.join(self.data_dir, "users.json")
        self.candidates_file = os.path.join(self.data_dir, "candidates.json")
        self.jobs_file = os.path.join(self.data_dir, "jobs.json")
        self.crawled_file = os.path.join(self.data_dir, "crawled_jobs.json")

        self.fm = FileManager(base_dir=self.base_dir, backup_dir=self.backup_dir)
        self.auth = AuthService(file_manager=self.fm, users_file=self.users_file)
        self.recruitment = RecruitmentManager(
            file_manager=self.fm,
            candidates_file=self.candidates_file,
            jobs_file=self.jobs_file,
        )
        self.crawler = JobCrawler(file_manager=self.fm, crawled_file=self.crawled_file)

    def tearDown(self):
        # Dọn dẹp toàn bộ dữ liệu tạm
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. Login Admin
    def test_01_login_admin(self):
        admin = self.auth.login("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, User.ROLE_ADMIN)
        self.assertTrue(self.auth.is_admin())
        self.assertFalse(self.auth.is_staff())
        self.assertTrue(self.auth.is_logged_in())

    # 2. Login Staff
    def test_02_login_staff(self):
        staff = self.auth.login("staff", "staff123")
        self.assertIsNotNone(staff)
        self.assertEqual(staff.role, User.ROLE_STAFF)
        self.assertFalse(self.auth.is_admin())
        self.assertTrue(self.auth.is_staff())
        self.assertTrue(self.auth.is_logged_in())

    # 3. Sai password
    def test_03_login_wrong_password(self):
        user = self.auth.login("admin", "sai_mat_khau_123")
        self.assertIsNone(user)
        self.assertFalse(self.auth.is_logged_in())

    # 4. Hash và verify password
    def test_04_hash_verify_password(self):
        pwd = "MySecretPassword@2026"
        hashed = AuthService.hash_password(pwd)
        # Chuỗi SHA-256 phải là chuỗi hex 64 ký tự
        self.assertEqual(len(hashed), 64)
        self.assertNotEqual(pwd, hashed)

        self.assertTrue(AuthService.verify_password(pwd, hashed))
        self.assertFalse(AuthService.verify_password("wrong_password", hashed))

    # 5. Candidate ID trùng
    def test_05_candidate_duplicate_id(self):
        c1 = Candidate("C001", "Nguyễn Văn A", "a@example.com", "0912345678", "DEV_PY")
        self.recruitment.create_candidate(c1)

        c2_duplicate = Candidate("C001", "Trần Văn Khác", "khac@example.com", "0987654321", "DEV_PY")
        with self.assertRaises(ValueError) as ctx:
            self.recruitment.create_candidate(c2_duplicate)
        self.assertIn("đã tồn tại", str(ctx.exception))

    # 6. CRUD Candidate
    def test_06_crud_candidate(self):
        # Create
        c = Candidate("C002", "Lê Văn Ban", "ban@example.com", "0988776655", "DEV_PY", 2.0, Candidate.STATUS_NOP_HO_SO, 80.0)
        self.recruitment.create_candidate(c)

        # Read
        retrieved = self.recruitment.get_candidate_by_id("C002")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.full_name, "Lê Văn Ban")

        # Update
        retrieved.interview_score = 92.5
        retrieved.status = Candidate.STATUS_DUYET_CV
        self.recruitment.update_candidate(retrieved)

        updated = self.recruitment.get_candidate_by_id("C002")
        self.assertEqual(updated.interview_score, 92.5)
        self.assertEqual(updated.status, Candidate.STATUS_DUYET_CV)

    # 7. Staff không được delete Candidate
    def test_07_staff_cannot_delete_candidate(self):
        c = Candidate("C003", "Phạm Văn Can", "can@example.com", "0977665544", "DEV_PY")
        self.recruitment.create_candidate(c)

        staff_user = self.auth.login("staff", "staff123")
        self.assertIsNotNone(staff_user)

        with self.assertRaises(PermissionError) as ctx:
            self.recruitment.delete_candidate("C003", current_user=staff_user)
        self.assertIn("không có quyền xóa", str(ctx.exception))

        # Đảm bảo ứng viên vẫn còn trong danh sách
        self.assertIsNotNone(self.recruitment.get_candidate_by_id("C003"))

    # 8. Admin delete Candidate
    def test_08_admin_delete_candidate(self):
        c = Candidate("C004", "Hoàng Văn Dũng", "dung@example.com", "0966554433", "DEV_PY")
        self.recruitment.create_candidate(c)

        admin_user = self.auth.login("admin", "admin123")
        self.assertIsNotNone(admin_user)

        deleted = self.recruitment.delete_candidate("C004", current_user=admin_user)
        self.assertTrue(deleted)
        self.assertIsNone(self.recruitment.get_candidate_by_id("C004"))

    # 9. Search không phân biệt hoa thường & Unicode tiếng Việt
    def test_09_search_case_insensitive_vietnamese(self):
        c1 = Candidate("C01", "Nguyễn Văn A", "a@test.com", "0911111111", "DEV")
        c2 = Candidate("C02", "Trần NGUYỄN", "b@test.com", "0922222222", "DEV")
        c3 = Candidate("C03", "Lê Hoàng Phúc", "c@test.com", "0933333333", "QA")
        self.recruitment.create_candidate(c1)
        self.recruitment.create_candidate(c2)
        self.recruitment.create_candidate(c3)

        # Tìm 'nguyễn' (chữ thường) phải khớp cả 'Nguyễn Văn A' và 'Trần NGUYỄN'
        results = self.recruitment.search_candidates("nguyễn")
        ids = [c.person_id for c in results]
        self.assertIn("C01", ids)
        self.assertIn("C02", ids)
        self.assertNotIn("C03", ids)

        # Tìm số điện thoại
        phone_results = self.recruitment.search_candidates("222222")
        self.assertEqual(len(phone_results), 1)
        self.assertEqual(phone_results[0].person_id, "C02")

    # 10. Filter position + status kết hợp
    def test_10_filter_position_and_status(self):
        c1 = Candidate("C1", "A", "a@test.com", "0911111111", "DEV_PY", status=Candidate.STATUS_DUYET_CV)
        c2 = Candidate("C2", "B", "b@test.com", "0922222222", "DEV_PY", status=Candidate.STATUS_NOP_HO_SO)
        c3 = Candidate("C3", "C", "c@test.com", "0933333333", "DEV_FE", status=Candidate.STATUS_DUYET_CV)
        self.recruitment.create_candidate(c1)
        self.recruitment.create_candidate(c2)
        self.recruitment.create_candidate(c3)

        # Lọc kết hợp position="DEV_PY" VÀ status="Duyệt CV"
        filtered = self.recruitment.filter_candidates(position_id="DEV_PY", status=Candidate.STATUS_DUYET_CV)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].person_id, "C1")

    # 11. CRUD JobPosition
    def test_11_crud_job_position(self):
        admin_user = self.auth.login("admin", "admin123")

        # Create
        job = JobPosition("POS_TEST", "Test Engineer", "QA Department", 15000000, 25000000, 2)
        self.recruitment.create_job(job)

        # Read
        saved_job = self.recruitment.get_job_by_id("POS_TEST")
        self.assertIsNotNone(saved_job)
        self.assertEqual(saved_job.title, "Test Engineer")

        # Update
        saved_job.quota = 5
        self.recruitment.update_job(saved_job)
        self.assertEqual(self.recruitment.get_job_by_id("POS_TEST").quota, 5)

        # Delete (chỉ Admin)
        self.assertTrue(self.recruitment.delete_job("POS_TEST", current_user=admin_user))
        self.assertIsNone(self.recruitment.get_job_by_id("POS_TEST"))

    # 12. Funnel statistics
    def test_12_funnel_statistics(self):
        # Thêm 5 ứng viên với các trạng thái khác nhau
        self.recruitment.create_candidate(Candidate("F1", "U1", "u1@test.com", "0901111111", "P", status=Candidate.STATUS_NOP_HO_SO))
        self.recruitment.create_candidate(Candidate("F2", "U2", "u2@test.com", "0902222222", "P", status=Candidate.STATUS_DUYET_CV))
        self.recruitment.create_candidate(Candidate("F3", "U3", "u3@test.com", "0903333333", "P", status=Candidate.STATUS_PV_VONG_1))
        self.recruitment.create_candidate(Candidate("F4", "U4", "u4@test.com", "0904444444", "P", status=Candidate.STATUS_DAT_OFFER))
        self.recruitment.create_candidate(Candidate("F5", "U5", "u5@test.com", "0905555555", "P", status=Candidate.STATUS_LOAI))

        stats = self.recruitment.get_funnel_statistics()
        self.assertEqual(stats["total"], 5)
        self.assertEqual(stats["hired_count"], 1)
        self.assertEqual(stats["rejected_count"], 1)
        self.assertEqual(stats["hire_rate"], 20.0)

        # Kiểm tra danh sách stages có đủ 6 trạng thái chuẩn
        self.assertEqual(len(stats["stages"]), 6)
        stage_names = [s["name"] for s in stats["stages"]]
        self.assertIn("Nộp hồ sơ", stage_names)
        self.assertIn("Đạt/Offer", stage_names)

    # 13. CSV export (UTF-8-SIG)
    def test_13_csv_export(self):
        c = Candidate("C_CSV", "Nguyễn Văn Đạt", "dat@test.vn", "0987654321", "DEV", 3.0, Candidate.STATUS_DAT_OFFER, 95.0)
        self.recruitment.create_candidate(c)

        csv_path = os.path.join(self.data_dir, "export_hired.csv")
        self.recruitment.export_candidates_to_csv(csv_path)

        self.assertTrue(os.path.exists(csv_path))
        # Đọc lại kiểm tra BOM UTF-8-SIG và nội dung tiếng Việt
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
            self.assertEqual(reader[0], RecruitmentManager.CSV_HEADERS)
            self.assertEqual(reader[1][0], "C_CSV")
            self.assertEqual(reader[1][1], "Nguyễn Văn Đạt")
            self.assertEqual(reader[1][6], "Đạt/Offer")

    # 14. Crawler xử lý ConnectionError không crash
    def test_14_crawler_handles_connection_error(self):
        with patch("requests.get") as mock_get:
            # Giả lập rớt mạng hoàn toàn
            mock_get.side_effect = requests.exceptions.ConnectionError("No internet connection")

            # Gọi crawler với use_fallback_on_error=True
            success, jobs, message = self.crawler.fetch_jobs(
                keyword="python",
                source_url="http://invalid.domain.xyz/jobs",
                use_fallback_on_error=True,
            )

            # Ứng dụng không crash, trả về thông báo lỗi và dữ liệu fallback để demo
            self.assertFalse(success)
            self.assertIn("ConnectionError", message)
            self.assertTrue(len(jobs) > 0)
            self.assertEqual(jobs[0]["job_id"], "CRAWL_01")

            # Kiểm tra lưu vào file JSON
            self.crawler.save_crawled_jobs(jobs)
            saved = self.crawler.load_saved_crawled_jobs()
            self.assertEqual(len(saved), len(jobs))


if __name__ == "__main__":
    unittest.main()
