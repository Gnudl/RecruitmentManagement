import csv
import os
from typing import Optional, List, Dict, Any

from models.candidate import Candidate
from models.job_position import JobPosition
from models.user import User
from services.file_manager import FileManager


class RecruitmentManager:
    """
    Quản lý toàn bộ nghiệp vụ tuyển dụng:
    1. Quản lý Ứng viên (Candidate):
       - CRUD: create, get, update, delete (phân quyền: Staff không được xóa).
       - Kiểm tra trùng lặp ID, ràng buộc email, phone, score, experience.
       - Tìm kiếm không phân biệt hoa thường theo họ tên hoặc số điện thoại.
       - Lọc kết hợp theo vị trí tuyển dụng và trạng thái.
    2. Quản lý Vị trí tuyển dụng (JobPosition):
       - CRUD: create, get, update, delete (chỉ Admin được xóa).
       - Ràng buộc lương min <= max, quota > 0.
    3. Thống kê Phễu tuyển dụng (Funnel Statistics):
       - Tính số lượng và tỷ lệ rơi rụng theo từng vòng tuyển dụng.
    4. Xuất dữ liệu CSV:
       - Xuất danh sách ứng viên chuẩn UTF-8-SIG (tương thích Excel tiếng Việt).
    """

    DEFAULT_CANDIDATES_FILE = "data/candidates.json"
    DEFAULT_JOBS_FILE = "data/jobs.json"

    FUNNEL_STAGES = [
        Candidate.STATUS_NOP_HO_SO,
        Candidate.STATUS_DUYET_CV,
        Candidate.STATUS_PV_VONG_1,
        Candidate.STATUS_PV_VONG_2,
        Candidate.STATUS_DAT_OFFER,
        Candidate.STATUS_LOAI,
    ]

    CSV_HEADERS = [
        "ID",
        "Họ tên",
        "Email",
        "Số điện thoại",
        "Vị trí",
        "Kinh nghiệm",
        "Trạng thái",
        "Điểm",
    ]

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        candidates_file: Optional[str] = None,
        jobs_file: Optional[str] = None,
    ):
        self.file_manager = file_manager or FileManager()
        self.candidates_file = candidates_file or self.DEFAULT_CANDIDATES_FILE
        self.jobs_file = jobs_file or self.DEFAULT_JOBS_FILE

    # =========================================================================
    # CANDIDATE CRUD & OPERATIONS
    # =========================================================================

    def get_candidates(self) -> List[Candidate]:
        """Lấy toàn bộ danh sách ứng viên từ file JSON."""
        raw_list = self.file_manager.read_json(self.candidates_file, default=[])
        candidates = []
        for item in raw_list:
            try:
                candidates.append(Candidate.from_dict(item))
            except Exception:
                continue
        return candidates

    def _save_candidates(self, candidates: List[Candidate]) -> None:
        """Lưu danh sách ứng viên vào file JSON an toàn (có auto-backup)."""
        data = [c.to_dict() for c in candidates]
        self.file_manager.write_json(self.candidates_file, data, backup=True)

    def get_candidate_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Tìm kiếm ứng viên theo ID."""
        if not candidate_id:
            return None
        clean_id = str(candidate_id).strip().lower()
        for c in self.get_candidates():
            if c.person_id.lower() == clean_id:
                return c
        return None

    def create_candidate(self, candidate: Candidate) -> Candidate:
        """
        Thêm mới một ứng viên:
        - Kiểm tra trùng ID (không phân biệt hoa thường).
        - Ghi vào candidates.json có sao lưu .bak tự động.
        """
        if not isinstance(candidate, Candidate):
            raise TypeError("Dữ liệu phải là một đối tượng Candidate.")

        candidates = self.get_candidates()
        # Kiểm tra trùng ID
        for existing in candidates:
            if existing.person_id.lower() == candidate.person_id.lower():
                raise ValueError(f"Mã ứng viên '{candidate.person_id}' đã tồn tại trong hệ thống. Không thể thêm trùng.")

        candidates.append(candidate)
        self._save_candidates(candidates)
        return candidate

    def update_candidate(self, candidate: Candidate) -> Candidate:
        """Cập nhật thông tin ứng viên đã có trong hệ thống."""
        if not isinstance(candidate, Candidate):
            raise TypeError("Dữ liệu phải là một đối tượng Candidate.")

        candidates = self.get_candidates()
        found = False
        for i, existing in enumerate(candidates):
            if existing.person_id.lower() == candidate.person_id.lower():
                candidates[i] = candidate
                found = True
                break

        if not found:
            raise ValueError(f"Không tìm thấy ứng viên có mã '{candidate.person_id}' để cập nhật.")

        self._save_candidates(candidates)
        return candidate

    def delete_candidate(self, candidate_id: str, current_user: Optional[User] = None) -> bool:
        """
        Xóa ứng viên khỏi hệ thống:
        - Ràng buộc phân quyền: Chỉ Admin mới có quyền xóa. Staff bị từ chối với PermissionError.
        """
        if current_user is not None:
            if not current_user.is_admin():
                raise PermissionError("Nhân viên (Staff) không có quyền xóa ứng viên. Chỉ Quản trị viên (Admin) mới có quyền này.")

        candidates = self.get_candidates()
        initial_count = len(candidates)
        candidates = [c for c in candidates if c.person_id.lower() != str(candidate_id).strip().lower()]

        if len(candidates) == initial_count:
            raise ValueError(f"Không tìm thấy ứng viên có mã '{candidate_id}' để xóa.")

        self._save_candidates(candidates)
        return True

    def search_candidates(self, keyword: str, candidates: Optional[List[Candidate]] = None) -> List[Candidate]:
        """
        Tìm kiếm ứng viên theo họ tên hoặc số điện thoại:
        - Không phân biệt hoa thường (case-insensitive).
        - Hỗ trợ tiếng Việt Unicode (ví dụ: 'nguyễn' khớp cả 'Nguyễn Văn A' và 'Trần NGUYỄN').
        """
        source = candidates if candidates is not None else self.get_candidates()
        if not keyword or not str(keyword).strip():
            return source

        term = str(keyword).strip().lower()
        results = []
        for c in source:
            # Khớp tên hoặc số điện thoại
            if term in c.full_name.lower() or term in c.phone:
                results.append(c)
        return results

    def filter_candidates(
        self,
        position_id: Optional[str] = None,
        status: Optional[str] = None,
        candidates: Optional[List[Candidate]] = None,
    ) -> List[Candidate]:
        """Lọc ứng viên kết hợp theo vị trí tuyển dụng và trạng thái."""
        source = candidates if candidates is not None else self.get_candidates()
        results = source

        if position_id and str(position_id).strip() and str(position_id).strip() != "Tất cả":
            pos = str(position_id).strip().lower()
            results = [c for c in results if c.position_id.lower() == pos]

        if status and str(status).strip() and str(status).strip() != "Tất cả":
            stat = str(status).strip().lower()
            results = [c for c in results if c.status.lower() == stat]

        return results

    def query_candidates(
        self,
        keyword: Optional[str] = None,
        position_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Candidate]:
        """Tìm kiếm và lọc kết hợp trên danh sách ứng viên."""
        results = self.get_candidates()
        if keyword:
            results = self.search_candidates(keyword, results)
        if position_id or status:
            results = self.filter_candidates(position_id, status, results)
        return results

    # =========================================================================
    # JOB POSITION CRUD & OPERATIONS
    # =========================================================================

    def get_jobs(self) -> List[JobPosition]:
        """Lấy toàn bộ danh sách vị trí tuyển dụng."""
        raw_list = self.file_manager.read_json(self.jobs_file, default=[])
        jobs = []
        for item in raw_list:
            try:
                jobs.append(JobPosition.from_dict(item))
            except Exception:
                continue
        return jobs

    def _save_jobs(self, jobs: List[JobPosition]) -> None:
        """Lưu danh sách vị trí tuyển dụng an toàn."""
        data = [j.to_dict() for j in jobs]
        self.file_manager.write_json(self.jobs_file, data, backup=True)

    def get_job_by_id(self, position_id: str) -> Optional[JobPosition]:
        """Tìm vị trí tuyển dụng theo mã position_id."""
        if not position_id:
            return None
        clean_id = str(position_id).strip().lower()
        for j in self.get_jobs():
            if j.position_id.lower() == clean_id:
                return j
        return None

    def create_job(self, job: JobPosition) -> JobPosition:
        """Thêm mới vị trí tuyển dụng (kiểm tra trùng mã)."""
        if not isinstance(job, JobPosition):
            raise TypeError("Dữ liệu phải là một đối tượng JobPosition.")

        jobs = self.get_jobs()
        for existing in jobs:
            if existing.position_id.lower() == job.position_id.lower():
                raise ValueError(f"Mã vị trí tuyển dụng '{job.position_id}' đã tồn tại trong hệ thống.")

        jobs.append(job)
        self._save_jobs(jobs)
        return job

    def update_job(self, job: JobPosition) -> JobPosition:
        """Cập nhật thông tin vị trí tuyển dụng."""
        if not isinstance(job, JobPosition):
            raise TypeError("Dữ liệu phải là một đối tượng JobPosition.")

        jobs = self.get_jobs()
        found = False
        for i, existing in enumerate(jobs):
            if existing.position_id.lower() == job.position_id.lower():
                jobs[i] = job
                found = True
                break

        if not found:
            raise ValueError(f"Không tìm thấy vị trí tuyển dụng có mã '{job.position_id}' để cập nhật.")

        self._save_jobs(jobs)
        return job

    def delete_job(self, position_id: str, current_user: Optional[User] = None) -> bool:
        """
        Xóa vị trí tuyển dụng:
        - Chỉ Admin mới được quyền xóa.
        - Kiểm tra xem có ứng viên nào đang ứng tuyển vào vị trí này không.
        """
        if current_user is not None and not current_user.is_admin():
            raise PermissionError("Chỉ Quản trị viên (Admin) mới có quyền xóa vị trí tuyển dụng.")

        clean_id = str(position_id).strip().lower()

        # Kiểm tra ràng buộc tham chiếu ứng viên
        for c in self.get_candidates():
            if c.position_id.lower() == clean_id:
                raise ValueError(
                    f"Không thể xóa vị trí '{position_id}' vì hiện đang có ứng viên [{c.person_id} - {c.full_name}] ứng tuyển."
                )

        jobs = self.get_jobs()
        initial_count = len(jobs)
        jobs = [j for j in jobs if j.position_id.lower() != clean_id]

        if len(jobs) == initial_count:
            raise ValueError(f"Không tìm thấy vị trí tuyển dụng có mã '{position_id}' để xóa.")

        self._save_jobs(jobs)
        return True

    # =========================================================================
    # FUNNEL STATISTICS
    # =========================================================================

    def get_funnel_statistics(self) -> Dict[str, Any]:
        """
        Tính toán số lượng và tỷ lệ rơi rụng theo từng vòng tuyển dụng.
        Dữ liệu được chuẩn bị sẵn sàng để FunnelCanvas vẽ biểu đồ.
        """
        candidates = self.get_candidates()
        total_candidates = len(candidates)

        # Đếm số lượng ứng viên theo từng trạng thái
        counts_by_status = {stage: 0 for stage in self.FUNNEL_STAGES}
        for c in candidates:
            if c.status in counts_by_status:
                counts_by_status[c.status] += 1
            else:
                counts_by_status[c.status] = 1

        stages_data = []
        for stage in self.FUNNEL_STAGES:
            cnt = counts_by_status.get(stage, 0)
            pct = round((cnt / total_candidates * 100), 1) if total_candidates > 0 else 0.0
            stages_data.append({
                "name": stage,
                "count": cnt,
                "percentage": pct,
            })

        hired_count = counts_by_status.get(Candidate.STATUS_DAT_OFFER, 0)
        rejected_count = counts_by_status.get(Candidate.STATUS_LOAI, 0)

        return {
            "total": total_candidates,
            "stages": stages_data,
            "hired_count": hired_count,
            "rejected_count": rejected_count,
            "hire_rate": round((hired_count / total_candidates * 100), 1) if total_candidates > 0 else 0.0,
        }

    # =========================================================================
    # CSV EXPORT
    # =========================================================================

    def export_candidates_to_csv(self, filepath: str, candidates: Optional[List[Candidate]] = None) -> str:
        """
        Xuất danh sách ứng viên ra file CSV với bảng mã UTF-8-SIG (tương thích hoàn hảo với Excel).
        Nếu không truyền danh sách candidates thì xuất toàn bộ ứng viên hiện có.
        """
        source = candidates if candidates is not None else self.get_candidates()
        abs_path = self.file_manager.resolve_path(filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            # Ghi dòng tiêu đề
            writer.writerow(self.CSV_HEADERS)

            # Ghi từng dòng dữ liệu
            for c in source:
                writer.writerow([
                    c.person_id,
                    c.full_name,
                    c.email,
                    c.phone,
                    c.position_id,
                    c.experience_years,
                    c.status,
                    c.interview_score,
                ])

        return abs_path
