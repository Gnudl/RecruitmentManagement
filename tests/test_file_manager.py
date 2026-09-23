import os
import json
import shutil
import tempfile
import unittest

from services.file_manager import FileManager, JSONCorruptedError


class TestFileManager(unittest.TestCase):
    def setUp(self):
        # Sử dụng thư mục tạm riêng biệt cho mỗi test để không ảnh hưởng dữ liệu thật
        self.test_dir = tempfile.mkdtemp()
        self.base_dir = os.path.join(self.test_dir, "app")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.backup_dir = os.path.join(self.base_dir, "backups")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        self.fm = FileManager(base_dir=self.base_dir, backup_dir=self.backup_dir)

    def tearDown(self):
        # Dọn dẹp toàn bộ thư mục tạm sau khi test xong
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_not_exist(self):
        """Test khi file không tồn tại: tự động tạo file với giá trị mặc định [] và trả về []."""
        file_path = os.path.join(self.data_dir, "new_file.json")
        self.assertFalse(os.path.exists(file_path))

        data = self.fm.read_json(file_path)
        self.assertEqual(data, [])
        self.assertTrue(os.path.exists(file_path))

    def test_file_zero_byte(self):
        """Test file 0-byte: trả về [] an toàn mà không crash ứng dụng."""
        zero_file = os.path.join(self.data_dir, "empty.json")
        with open(zero_file, "w", encoding="utf-8") as f:
            pass  # Tạo file kích thước đúng 0 byte

        self.assertEqual(os.path.getsize(zero_file), 0)
        data = self.fm.read_json(zero_file)
        self.assertEqual(data, [])

    def test_valid_json(self):
        """Test ghi và đọc JSON hợp lệ bình thường."""
        target_file = os.path.join(self.data_dir, "valid.json")
        sample_data = [
            {"id": "C01", "name": "Nguyễn Văn A", "status": "Duyệt CV"},
            {"id": "C02", "name": "Trần Thị B", "status": "Đạt/Offer"}
        ]
        self.fm.write_json(target_file, sample_data, backup=False)

        loaded_data = self.fm.read_json(target_file)
        self.assertEqual(loaded_data, sample_data)

    def test_corrupted_json_with_valid_backup(self):
        """Test JSON sai cú pháp: tự động khôi phục từ bản backup hợp lệ gần nhất."""
        target_file = os.path.join(self.data_dir, "candidates.json")
        original_data = [{"id": "C100", "full_name": "Lê Văn C", "score": 90}]

        # 1. Ghi dữ liệu ban đầu
        self.fm.write_json(target_file, original_data, backup=False)

        # 2. Tạo bản backup hợp lệ của dữ liệu này
        self.fm.create_backup(target_file)

        # 3. Làm hỏng cú pháp file chính (Corrupted JSON)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("{ 'invalid_json': unclosed bracket, 123... ")

        # 4. Đọc file -> FileManager phải tự tìm backup và phục hồi
        recovered_data = self.fm.read_json(target_file)
        self.assertEqual(recovered_data, original_data)

        # 5. Kiểm tra nội dung file chính đã được khôi phục cú pháp hợp lệ
        with open(target_file, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        self.assertEqual(disk_data, original_data)

    def test_corrupted_json_without_backup(self):
        """Test JSON sai cú pháp nhưng KHÔNG có backup nào: ném ngoại lệ JSONCorruptedError rõ ràng."""
        target_file = os.path.join(self.data_dir, "corrupted_no_bak.json")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("this is completely invalid json syntax !!!")

        with self.assertRaises(JSONCorruptedError):
            self.fm.read_json(target_file)

    def test_backup_before_write(self):
        """Test cơ chế tự động backup dữ liệu cũ trước khi ghi dữ liệu mới."""
        target_file = os.path.join(self.data_dir, "tracked.json")
        old_data = [{"version": 1, "note": "old content"}]
        new_data = [{"version": 2, "note": "new content"}]

        # Ghi dữ liệu ban đầu
        self.fm.write_json(target_file, old_data, backup=False)

        # Ghi dữ liệu mới với backup=True
        self.fm.write_json(target_file, new_data, backup=True)

        # Kiểm tra file chính đã mang dữ liệu mới
        current_data = self.fm.read_json(target_file)
        self.assertEqual(current_data, new_data)

        # Kiểm tra thư mục backup có chứa dữ liệu CŨ
        backup_file = self.fm.find_latest_valid_backup(target_file)
        self.assertIsNotNone(backup_file)
        with open(backup_file, "r", encoding="utf-8") as bf:
            backed_up_data = json.load(bf)
        self.assertEqual(backed_up_data, old_data)

    def test_atomic_write(self):
        """Test tính nguyên tử: không để lại file rác .tmp khi ghi thành công."""
        target_file = os.path.join(self.data_dir, "atomic_test.json")
        payload = {"title": "Atomic Write Verification", "status": "OK"}

        self.fm.write_json(target_file, payload, backup=False)

        self.assertTrue(os.path.exists(target_file))
        # Không được có file .tmp nào còn sót lại trong thư mục
        tmp_files = [f for f in os.listdir(self.data_dir) if f.endswith(".tmp")]
        self.assertEqual(len(tmp_files), 0)

        # Đọc dữ liệu kiểm chứng
        loaded = self.fm.read_json(target_file)
        self.assertEqual(loaded, payload)

    def test_auto_create_directories(self):
        """Test tự động tạo cấu trúc thư mục lồng nhau nếu chưa tồn tại."""
        deep_file = os.path.join(self.base_dir, "nested", "subfolder", "data.json")
        self.assertFalse(os.path.exists(os.path.dirname(deep_file)))

        self.fm.write_json(deep_file, {"status": "created"}, backup=False)
        self.assertTrue(os.path.exists(deep_file))

        loaded = self.fm.read_json(deep_file)
        self.assertEqual(loaded, {"status": "created"})


if __name__ == "__main__":
    unittest.main()
