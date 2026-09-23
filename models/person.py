from abc import ABC, abstractmethod
import re

# Regex chuẩn cho Email
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$')

# Regex cho số điện thoại di động Việt Nam: 10 chữ số, bắt đầu bằng 03, 05, 07, 08, 09
PHONE_REGEX = re.compile(r'^(03|05|07|08|09)\d{8}$')


class Person(ABC):
    """
    Lớp trừu tượng đại diện cho một con người trong hệ thống.
    Áp dụng tính đóng gói (Encapsulation) qua thuộc tính private và @property/@setter.
    """

    def __init__(self, person_id: str, full_name: str, email: str, phone: str):
        self._person_id = ""
        self._full_name = ""
        self._email = ""
        self._phone = ""

        # Thiết lập thông qua setter để thực hiện validation tự động
        self.person_id = person_id
        self.full_name = full_name
        self.email = email
        self.phone = phone

    # --- Property: person_id ---
    @property
    def person_id(self) -> str:
        return self._person_id

    @person_id.setter
    def person_id(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mã định danh (ID) không được để trống.")
        self._person_id = str(value).strip()

    # --- Property: full_name ---
    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Họ và tên không được để trống.")
        self._full_name = str(value).strip()

    # --- Property: email ---
    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        val = str(value).strip() if value else ""
        if not val or not EMAIL_REGEX.match(val):
            raise ValueError(f"Email không hợp lệ: '{value}'. Vui lòng nhập đúng định dạng (vd: user@example.com).")
        self._email = val

    # --- Property: phone ---
    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str):
        val = str(value).strip() if value else ""
        if not val or not PHONE_REGEX.match(val):
            raise ValueError(
                f"Số điện thoại không hợp lệ: '{value}'. Số điện thoại di động VN phải có đúng 10 số và bắt đầu bằng 03, 05, 07, 08 hoặc 09."
            )
        self._phone = val

    # --- Abstract Methods ---
    @abstractmethod
    def to_dict(self) -> dict:
        """Chuyển đổi đối tượng thành dictionary để tuần tự hóa JSON."""
        pass

    @abstractmethod
    def get_role_display(self) -> str:
        """Trả về chuỗi hiển thị vai trò trong hệ thống."""
        pass
