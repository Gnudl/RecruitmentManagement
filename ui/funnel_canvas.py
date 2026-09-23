import tkinter as tk
from typing import Dict, Any, Optional, List


class FunnelCanvas(tk.Canvas):
    """
    Component vẽ biểu đồ phễu tuyển dụng tùy biến (Funnel Chart) bằng tk.Canvas:
    - Thể hiện trực quan quy trình tuyển dụng qua từng tầng:
      Nộp hồ sơ -> Duyệt CV -> Phỏng vấn vòng 1 -> Phỏng vấn vòng 2 -> Đạt/Offer.
    - Trạng thái 'Loại' được tổng hợp thành chỉ số rơi rụng (Rejected Metric) độc lập.
    - Hiển thị đầy đủ: Tên vòng, Số lượng ứng viên, Tỷ lệ phần trăm chuyển đổi (%).
    - Tự động điều chỉnh kích thước theo sự kiện <Configure> của cửa sổ.
    - Xử lý an toàn khi không có dữ liệu (hiển thị thông báo, không crash).
    """

    # Bảng màu sắc nét cho từng tầng của phễu tuyển dụng
    STAGE_COLORS = [
        "#3498db",  # Nộp hồ sơ (Xanh dương)
        "#1abc9c",  # Duyệt CV (Xanh ngọc)
        "#f39c12",  # Phỏng vấn vòng 1 (Cam sáng)
        "#e67e22",  # Phỏng vấn vòng 2 (Cam đậm)
        "#27ae60",  # Đạt/Offer (Xanh lá trúng tuyển)
    ]
    REJECTED_COLOR = "#c0392b"  # Đỏ cho ứng viên bị loại

    SEQUENTIAL_STAGES = [
        "Nộp hồ sơ",
        "Duyệt CV",
        "Phỏng vấn vòng 1",
        "Phỏng vấn vòng 2",
        "Đạt/Offer",
    ]

    def __init__(self, parent, *args, **kwargs):
        kwargs.setdefault("bg", "#ffffff")
        kwargs.setdefault("highlightthickness", 1)
        kwargs.setdefault("highlightbackground", "#dcdde1")
        super().__init__(parent, *args, **kwargs)

        self._stats_data: Optional[Dict[str, Any]] = None
        self.bind("<Configure>", self._on_resize)

    def set_statistics(self, stats: Optional[Dict[str, Any]]):
        """Tiếp nhận số liệu từ RecruitmentManager.get_funnel_statistics() và vẽ lại phễu."""
        self._stats_data = stats
        self.draw()

    def _on_resize(self, event):
        """Tự động tính toán lại tỷ lệ vẽ khi Canvas thay đổi kích thước."""
        self.draw()

    def draw(self):
        """Vẽ toàn bộ biểu đồ phễu."""
        self.delete("all")

        width = self.winfo_width()
        height = self.winfo_height()

        # Kiểm tra nếu chưa hiển thị trên màn hình
        if width <= 10 or height <= 10:
            width = int(self.cget("width")) or 400
            height = int(self.cget("height")) or 300

        # Kiểm tra trường hợp không có dữ liệu hoặc danh sách rỗng
        if not self._stats_data or self._stats_data.get("total", 0) == 0:
            self.create_text(
                width / 2,
                height / 2,
                text="Chưa có dữ liệu tuyển dụng",
                font=("Segoe UI", 12, "italic"),
                fill="#7f8c8d",
            )
            return

        total = self._stats_data.get("total", 0)
        hired = self._stats_data.get("hired_count", 0)
        rejected = self._stats_data.get("rejected_count", 0)
        hire_rate = self._stats_data.get("hire_rate", 0.0)

        # Lấy dữ liệu cho 5 tầng chuyển tiếp liên tục
        stage_dict = {s["name"]: s for s in self._stats_data.get("stages", [])}

        funnel_items = []
        for name in self.SEQUENTIAL_STAGES:
            item = stage_dict.get(name, {"count": 0, "percentage": 0.0})
            funnel_items.append({
                "name": name,
                "count": item.get("count", 0),
                "percentage": item.get("percentage", 0.0),
            })

        num_stages = len(funnel_items)
        top_margin = 15
        bottom_margin = 45  # Dành chỗ cho thanh thống kê Loại / Đạt
        left_margin = 25
        right_margin = 25

        available_height = height - top_margin - bottom_margin
        stage_height = available_height / num_stages
        padding = 4

        max_w = width - left_margin - right_margin
        min_w = max_w * 0.35  # Độ rộng tầng đáy phễu tối thiểu

        # Vẽ từng tầng hình thang chuyển tiếp
        for i, item in enumerate(funnel_items):
            color = self.STAGE_COLORS[i % len(self.STAGE_COLORS)]

            # Tính toán độ rộng giảm dần hình phễu
            w_top = max_w - (i * (max_w - min_w) / num_stages)
            w_bot = max_w - ((i + 1) * (max_w - min_w) / num_stages)

            y_top = top_margin + i * stage_height + padding
            y_bot = top_margin + (i + 1) * stage_height - padding

            center_x = width / 2
            x1_top = center_x - w_top / 2
            x2_top = center_x + w_top / 2
            x1_bot = center_x - w_bot / 2
            x2_bot = center_x + w_bot / 2

            # Tọa độ 4 đỉnh hình thang
            points = [x1_top, y_top, x2_top, y_top, x2_bot, y_bot, x1_bot, y_bot]
            self.create_polygon(points, fill=color, outline="#ffffff", width=1.5)

            # Chữ hiển thị trên từng tầng (Tên, Số lượng, %)
            label_text = f"{item['name']}: {item['count']} ứng viên ({item['percentage']}%)"
            y_mid = (y_top + y_bot) / 2

            self.create_text(
                center_x,
                y_mid,
                text=label_text,
                font=("Segoe UI", 9, "bold"),
                fill="#ffffff",
            )

        # Vẽ chỉ số rơi rụng (Rejected) và Trúng tuyển (Offer) ở đáy Canvas
        footer_y = height - 20
        reject_pct = round((rejected / total * 100), 1) if total > 0 else 0.0

        # Huy hiệu Trúng tuyển (Offer)
        self.create_text(
            left_margin + 90,
            footer_y,
            text=f"✔ Trúng tuyển: {hired} ({hire_rate}%)",
            font=("Segoe UI", 9, "bold"),
            fill="#27ae60",
        )

        # Huy hiệu Bị loại (Rejected)
        self.create_text(
            width - right_margin - 80,
            footer_y,
            text=f"✖ Đã loại: {rejected} ({reject_pct}%)",
            font=("Segoe UI", 9, "bold"),
            fill=self.REJECTED_COLOR,
        )
