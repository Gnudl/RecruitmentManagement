import unittest
from abc import ABC

from models.person import Person
from models.candidate import Candidate
from models.user import User
from models.job_position import JobPosition


class TestModels(unittest.TestCase):
    def test_person_abstraction(self):
        """Kiểm tra Person là lớp trừu tượng, không thể khởi tạo trực tiếp."""
        self.assertTrue(issubclass(Person, ABC))
        with self.assertRaises(TypeError):
            Person("P01", "Nguyen Van A", "a@gmail.com", "0912345678")

    def test_email_validation(self):
        """Kiểm tra regex validation cho email."""
        # Email hợp lệ
        c = Candidate("C01", "Nguyen Van A", "test.user@company.vn", "0912345678", "DEV_PY")
        self.assertEqual(c.email, "test.user@company.vn")

        # Email không hợp lệ: thiếu domain, thiếu @, v.v.
        invalid_emails = ["nguyenvana@", "nguyenvana", "@gmail.com", "user@domain."]
        for bad_email in invalid_emails:
            with self.assertRaises(ValueError, msg=f"Nên báo lỗi với email: {bad_email}"):
                c.email = bad_email

    def test_phone_validation(self):
        """Kiểm tra regex validation cho số điện thoại di động VN (03, 05, 07, 08, 09 - 10 số)."""
        valid_phones = ["0987654321", "0323456789", "0567891234", "0771234567", "0888888888"]
        c = Candidate("C01", "Nguyen Van A", "valid@email.com", "0912345678", "DEV_PY")
        for phone in valid_phones:
            c.phone = phone
            self.assertEqual(c.phone, phone)

        # Số không hợp lệ: 9 số, 11 số, đầu số lạ (01, 02, 04), chứa chữ
        invalid_phones = ["098765432", "09876543210", "0123456789", "0243456789", "09abcdefgh"]
        for bad_phone in invalid_phones:
            with self.assertRaises(ValueError, msg=f"Nên báo lỗi với SĐT: {bad_phone}"):
                c.phone = bad_phone

    def test_candidate_properties_and_score(self):
        """Kiểm tra các thuộc tính của Candidate và ràng buộc điểm phỏng vấn [0, 100]."""
        c = Candidate(
            person_id="C100",
            full_name="Tran Thi B",
            email="thib@gmail.com",
            phone="0399887766",
            position_id="POS_PY",
            experience_years=2.5,
            status=Candidate.STATUS_NOP_HO_SO,
            interview_score=75.0,
        )
        self.assertEqual(c.get_role_display(), "Ứng viên")
        self.assertEqual(c.interview_score, 75.0)

        # Điểm < 0 hoặc > 100 phải báo lỗi
        with self.assertRaises(ValueError):
            c.interview_score = -5.0
        with self.assertRaises(ValueError):
            c.interview_score = 105.0

        # Số năm kinh nghiệm âm phải báo lỗi
        with self.assertRaises(ValueError):
            c.experience_years = -1

        # Trạng thái không hợp lệ
        with self.assertRaises(ValueError):
            c.status = "Trạng thái giả mạo"

        # Serialization
        data = c.to_dict()
        self.assertEqual(data["person_id"], "C100")
        c2 = Candidate.from_dict(data)
        self.assertEqual(c2.person_id, c.person_id)
        self.assertEqual(c2.full_name, c.full_name)

    def test_user_properties_and_role(self):
        """Kiểm tra lớp User, băm mật khẩu và phân quyền Admin/Staff."""
        u = User(
            person_id="U01",
            full_name="Admin Master",
            email="admin@system.local",
            phone="0901234567",
            username="admin",
            password_hash="mock_hash_value",
            role=User.ROLE_ADMIN,
        )
        self.assertTrue(u.is_admin())
        self.assertFalse(u.is_staff())
        self.assertIn("Admin", u.get_role_display())

        # Role không hợp lệ
        with self.assertRaises(ValueError):
            u.role = "SuperUser"

        # Serialization
        u_dict = u.to_dict()
        u2 = User.from_dict(u_dict)
        self.assertEqual(u2.username, "admin")
        self.assertTrue(u2.is_admin())

    def test_job_position_validation(self):
        """Kiểm tra JobPosition: min_salary <= max_salary và quota > 0."""
        job = JobPosition(
            position_id="POS01",
            title="Senior Python Developer",
            department="Phòng Kỹ thuật",
            min_salary=20000000,
            max_salary=35000000,
            quota=3,
        )
        self.assertEqual(job.quota, 3)

        # Quota <= 0 báo lỗi
        with self.assertRaises(ValueError):
            job.quota = 0
        with self.assertRaises(ValueError):
            job.quota = -2

        # min_salary > max_salary báo lỗi
        with self.assertRaises(ValueError):
            job.set_salary_range(40000000, 30000000)

        # Serialization
        job_dict = job.to_dict()
        job2 = JobPosition.from_dict(job_dict)
        self.assertEqual(job2.position_id, "POS01")
        self.assertEqual(job2.min_salary, 20000000)


if __name__ == "__main__":
    unittest.main()
