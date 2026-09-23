import os
import sys

from models.candidate import Candidate
from models.job_position import JobPosition
from services.file_manager import FileManager, get_base_dir
from services.auth_service import AuthService
from services.recruitment_mgr import RecruitmentManager
from services.job_crawler import JobCrawler
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def initialize_directories(base_dir: str):
    """Đảm bảo các thư mục dữ liệu và sao lưu cần thiết tồn tại."""
    data_dir = os.path.join(base_dir, "data")
    backups_dir = os.path.join(base_dir, "backups")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(backups_dir, exist_ok=True)


def seed_sample_data_if_needed(fm: FileManager, recruitment_mgr: RecruitmentManager):
    """Khởi tạo dữ liệu mẫu phong phú ban đầu nếu chưa có dữ liệu."""
    # 1. Khởi tạo vị trí tuyển dụng mẫu
    jobs = recruitment_mgr.get_jobs()
    if not jobs:
        sample_jobs = [
            JobPosition("DEV_PY", "Senior Python Backend Developer", "Phòng Kỹ thuật", 25000000, 45000000, 3),
            JobPosition("DEV_FE", "Frontend React Specialist", "Phòng Kỹ thuật", 20000000, 35000000, 2),
            JobPosition("QA_QC", "Automation QA Tester", "Phòng QA/QC", 18000000, 28000000, 2),
            JobPosition("DEVOPS", "DevOps Cloud Engineer", "Phòng Hạ tầng", 28000000, 48000000, 1),
            JobPosition("DATA_AI", "AI & Data Engineer", "Viện Công nghệ AI", 30000000, 55000000, 2),
        ]
        for job in sample_jobs:
            recruitment_mgr.create_job(job)

    # 2. Khởi tạo ứng viên mẫu trải đều các vòng tuyển dụng
    candidates = recruitment_mgr.get_candidates()
    if not candidates:
        sample_candidates = [
            Candidate("C001", "Nguyễn Văn An", "an.nguyen@gmail.com", "0981234567", "DEV_PY", 3.5, Candidate.STATUS_DAT_OFFER, 92.0),
            Candidate("C002", "Trần NGUYỄN Bảo", "bao.tran@outlook.com", "0912345678", "DEV_PY", 2.0, Candidate.STATUS_PV_VONG_2, 85.0),
            Candidate("C003", "Lê Thị Cẩm", "cam.le@yahoo.com", "0356789123", "DEV_FE", 1.5, Candidate.STATUS_PV_VONG_1, 78.0),
            Candidate("C004", "Phạm Quốc Dũng", "dung.pham@company.vn", "0778899001", "DEVOPS", 4.0, Candidate.STATUS_DUYET_CV, 65.0),
            Candidate("C005", "Hoàng Minh Em", "em.hoang@gmail.com", "0888999111", "QA_QC", 1.0, Candidate.STATUS_NOP_HO_SO, 0.0),
            Candidate("C006", "Vũ Đình Phúc", "phuc.vu@fpt.edu.vn", "0933221100", "DATA_AI", 5.0, Candidate.STATUS_DAT_OFFER, 96.0),
            Candidate("C007", "Đỗ Thị Quỳnh", "quynh.do@tech.vn", "0567123456", "DEV_FE", 0.5, Candidate.STATUS_LOAI, 40.0),
        ]
        for c in sample_candidates:
            recruitment_mgr.create_candidate(c)


class ApplicationController:
    """Điều phối vòng đời ứng dụng: LoginWindow <-> MainWindow."""

    def __init__(self):
        self.base_dir = get_base_dir()
        initialize_directories(self.base_dir)

        self.file_manager = FileManager(base_dir=self.base_dir)
        self.auth_service = AuthService(file_manager=self.file_manager)
        self.recruitment_mgr = RecruitmentManager(file_manager=self.file_manager)
        self.job_crawler = JobCrawler(file_manager=self.file_manager)

        # Khởi tạo dữ liệu mẫu nếu cần
        seed_sample_data_if_needed(self.file_manager, self.recruitment_mgr)

    def start(self):
        """Khởi động ứng dụng bằng cửa sổ Đăng nhập."""
        self.show_login()

    def show_login(self):
        """Hiển thị cửa sổ đăng nhập."""
        login_win = LoginWindow(
            auth_service=self.auth_service,
            on_login_success=self.on_login_success,
        )
        login_win.mainloop()

    def on_login_success(self, current_user):
        """Callback khi đăng nhập thành công: mở MainWindow."""
        main_win = MainWindow(
            auth_service=self.auth_service,
            recruitment_mgr=self.recruitment_mgr,
            job_crawler=self.job_crawler,
            current_user=current_user,
            on_logout=self.show_login,
        )
        main_win.mainloop()


if __name__ == "__main__":
    app = ApplicationController()
    app.start()
