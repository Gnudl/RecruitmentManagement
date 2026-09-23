from models.person import Person


class Candidate(Person):
    """
    Lớp Candidate đại diện cho hồ sơ ứng viên tuyển dụng.
    Kế thừa từ Person và bổ sung các thuộc tính tuyển dụng:
    _position_id, _experience_years, _status, _interview_score.
    """

    # Danh mục các vòng/trạng thái tuyển dụng chuẩn
    STATUS_NOP_HO_SO = "Nộp hồ sơ"
    STATUS_DUYET_CV = "Duyệt CV"
    STATUS_PV_VONG_1 = "Phỏng vấn vòng 1"
    STATUS_PV_VONG_2 = "Phỏng vấn vòng 2"
    STATUS_DAT_OFFER = "Đạt/Offer"
    STATUS_LOAI = "Loại"

    VALID_STATUSES = [
        STATUS_NOP_HO_SO,
        STATUS_DUYET_CV,
        STATUS_PV_VONG_1,
        STATUS_PV_VONG_2,
        STATUS_DAT_OFFER,
        STATUS_LOAI,
    ]

    def __init__(
        self,
        person_id: str,
        full_name: str,
        email: str,
        phone: str,
        position_id: str,
        experience_years: float = 0.0,
        status: str = STATUS_NOP_HO_SO,
        interview_score: float = 0.0,
    ):
        # Gọi hàm khởi tạo của lớp cha Person
        super().__init__(person_id, full_name, email, phone)

        self._position_id = ""
        self._experience_years = 0.0
        self._status = self.STATUS_NOP_HO_SO
        self._interview_score = 0.0

        # Gán qua setter để kiểm tra ràng buộc nghiệp vụ
        self.position_id = position_id
        self.experience_years = experience_years
        self.status = status
        self.interview_score = interview_score

    # --- Property: position_id ---
    @property
    def position_id(self) -> str:
        return self._position_id

    @position_id.setter
    def position_id(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mã vị trí ứng tuyển không được để trống.")
        self._position_id = str(value).strip()

    # --- Property: experience_years ---
    @property
    def experience_years(self) -> float:
        return self._experience_years

    @experience_years.setter
    def experience_years(self, value: float):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Số năm kinh nghiệm phải là số.")
        if val < 0:
            raise ValueError("Số năm kinh nghiệm không thể là số âm.")
        self._experience_years = val

    # --- Property: status ---
    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        val = str(value).strip() if value else ""
        if val not in self.VALID_STATUSES:
            raise ValueError(
                f"Trạng thái '{value}' không hợp lệ. Phải là một trong: {', '.join(self.VALID_STATUSES)}"
            )
        self._status = val

    # --- Property: interview_score ---
    @property
    def interview_score(self) -> float:
        return self._interview_score

    @interview_score.setter
    def interview_score(self, value: float):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Điểm phỏng vấn phải là một số.")
        if not (0.0 <= val <= 100.0):
            raise ValueError(f"Điểm phỏng vấn phải nằm trong khoảng từ 0 đến 100 (nhận được: {value}).")
        self._interview_score = val

    # --- Method Overriding ---
    def to_dict(self) -> dict:
        """Tuần tự hóa đối tượng Candidate thành dictionary."""
        return {
            "person_id": self._person_id,
            "full_name": self._full_name,
            "email": self._email,
            "phone": self._phone,
            "position_id": self._position_id,
            "experience_years": self._experience_years,
            "status": self._status,
            "interview_score": self._interview_score,
        }

    def get_role_display(self) -> str:
        """Hiển thị vai trò của Candidate."""
        return "Ứng viên"

    def __str__(self) -> str:
        return (
            f"Ứng viên [{self._person_id}] {self._full_name} | Vị trí: {self._position_id} | "
            f"Trạng thái: {self._status} | Điểm: {self._interview_score} | KN: {self._experience_years} năm"
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Candidate":
        """Khởi tạo đối tượng Candidate từ dictionary."""
        return cls(
            person_id=data.get("person_id", ""),
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            position_id=data.get("position_id", ""),
            experience_years=data.get("experience_years", 0.0),
            status=data.get("status", cls.STATUS_NOP_HO_SO),
            interview_score=data.get("interview_score", 0.0),
        )
