"""
Module cầu nối file_manager.py tại thư mục gốc trỏ tới services.file_manager.
Đảm bảo khả năng import linh hoạt cho toàn bộ dự án.
"""
from services.file_manager import FileManager, JSONCorruptedError, get_base_dir

__all__ = ["FileManager", "JSONCorruptedError", "get_base_dir"]
