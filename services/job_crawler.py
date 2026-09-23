import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import requests

from services.file_manager import FileManager


class JobCrawler:
    """
    Dịch vụ thu thập thông tin việc làm IT từ các nguồn API:
    - Sử dụng thư viện `requests` để gửi HTTP request an toàn với timeout.
    - Xử lý toàn diện các ngoại lệ mạng: ConnectionError, Timeout, HTTPError, RequestException.
    - Xử lý response JSON sai cú pháp hoặc dữ liệu trả về không chuẩn.
    - Không bao giờ làm crash ứng dụng khi mất kết nối mạng.
    - Tích hợp mock/fallback data để demo mượt mà cả trong môi trường offline.
    - Lưu dữ liệu đã chuẩn hóa vào data/crawled_jobs.json qua FileManager.
    """

    DEFAULT_CRAWLED_FILE = "data/crawled_jobs.json"
    DEFAULT_API_URL = "https://remotive.com/api/remote-jobs"
    REQUEST_TIMEOUT = 5  # Giây

    # Dữ liệu fallback dự phòng phục vụ demo khi không có kết nối internet
    FALLBACK_JOBS = [
        {
            "job_id": "CRAWL_01",
            "title": "Senior Python Backend Developer (FastAPI/Django)",
            "company": "VinTech Solutions",
            "location": "Hà Nội / Hybrid",
            "salary": "35,000,000 - 55,000,000 VNĐ",
            "url": "https://example.com/jobs/python-sr",
            "tags": "Python, Django, FastAPI, PostgreSQL",
            "published_date": "2026-09-20",
            "description": "Phát triển hệ thống microservices backend hiệu năng cao bằng Python FastAPI và Docker.",
        },
        {
            "job_id": "CRAWL_02",
            "title": "Fullstack React & Node.js Engineer",
            "company": "FPT Software",
            "location": "TP. Hồ Chí Minh",
            "salary": "25,000,000 - 40,000,000 VNĐ",
            "url": "https://example.com/jobs/fullstack-react",
            "tags": "React, TypeScript, Node.js, Next.js",
            "published_date": "2026-09-21",
            "description": "Xây dựng các web app tương tác cao, thiết kế RESTful API và tối ưu trải nghiệm UI/UX.",
        },
        {
            "job_id": "CRAWL_03",
            "title": "DevOps & Cloud Specialist (AWS/Kubernetes)",
            "company": "VNG Corporation",
            "location": "TP. Hồ Chí Minh / Remote",
            "salary": "30,000,000 - 50,000,000 VNĐ",
            "url": "https://example.com/jobs/devops-aws",
            "tags": "Kubernetes, Docker, AWS, CI/CD",
            "published_date": "2026-09-22",
            "description": "Quản trị hạ tầng đám mây AWS, triển khai hệ thống CI/CD pipeline và giám sát cụm K8s.",
        },
        {
            "job_id": "CRAWL_04",
            "title": "AI & Data Engineer (Machine Learning/PyTorch)",
            "company": "Viettel AI Lab",
            "location": "Hà Nội",
            "salary": "35,000,000 - 60,000,000 VNĐ",
            "url": "https://example.com/jobs/ai-engineer",
            "tags": "Python, PyTorch, BigData, NLP",
            "published_date": "2026-09-22",
            "description": "Nghiên cứu và triển khai mô hình học sâu, xử lý đường ống dữ liệu quy mô lớn.",
        },
        {
            "job_id": "CRAWL_05",
            "title": "Automation QA Tester (Python/Selenium)",
            "company": "CMC Global",
            "location": "Đà Nẵng",
            "salary": "18,000,000 - 28,000,000 VNĐ",
            "url": "https://example.com/jobs/qa-automation",
            "tags": "Python, Selenium, PyTest, API Testing",
            "published_date": "2026-09-23",
            "description": "Viết kịch bản kiểm thử tự động cho hệ thống web và mobile, tối ưu regression testing.",
        },
    ]

    def __init__(self, file_manager: Optional[FileManager] = None, crawled_file: Optional[str] = None):
        self.file_manager = file_manager or FileManager()
        self.crawled_file = crawled_file or self.DEFAULT_CRAWLED_FILE

    def normalize_job_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Chuẩn hóa dữ liệu thô từ API trả về danh sách dict theo cấu trúc thống nhất:
        job_id, title, company, location, salary, url, tags, published_date, description.
        """
        normalized_jobs = []

        if not raw_data:
            return normalized_jobs

        # Xử lý trường hợp raw_data là dict chứa key 'jobs' (như API Remotive) hoặc list
        items = []
        if isinstance(raw_data, dict):
            items = raw_data.get("jobs", raw_data.get("data", []))
            if not items and "id" in raw_data:
                items = [raw_data]
        elif isinstance(raw_data, list):
            items = raw_data

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            job_id = str(item.get("id") or f"JOB_{idx + 1}")
            title = str(item.get("title") or item.get("job_title") or "Chưa có tiêu đề").strip()
            company = str(item.get("company_name") or item.get("company") or "Ẩn danh").strip()
            location = str(item.get("candidate_required_location") or item.get("location") or "Toàn quốc / Remote").strip()
            salary = str(item.get("salary") or "Thỏa thuận").strip()
            url = str(item.get("url") or item.get("link") or "").strip()

            tags_raw = item.get("tags") or item.get("category") or ""
            if isinstance(tags_raw, list):
                tags = ", ".join(str(t) for t in tags_raw)
            else:
                tags = str(tags_raw)

            pub_date = str(item.get("publication_date") or item.get("published_date") or datetime.now().strftime("%Y-%m-%d"))
            desc = str(item.get("description") or "").strip()
            # Giới hạn độ dài mô tả để hiển thị giao diện gọn gàng
            if len(desc) > 300:
                desc = desc[:300] + "..."

            normalized_jobs.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "url": url,
                "tags": tags,
                "published_date": pub_date,
                "description": desc,
            })

        return normalized_jobs

    def fetch_jobs(
        self,
        keyword: str = "python",
        source_url: Optional[str] = None,
        use_fallback_on_error: bool = True,
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Gửi yêu cầu tới API để lấy danh sách việc làm IT:
        - Bắt an toàn toàn bộ exception mạng.
        - Trả về tuple (success: bool, jobs: list, message: str).
        - Nếu có lỗi và use_fallback_on_error=True, trả về dữ liệu fallback kèm thông báo cảnh báo.
        """
        url = source_url or f"{self.DEFAULT_API_URL}?search={keyword}&limit=10"
        jobs: List[Dict[str, Any]] = []

        try:
            response = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                headers={"User-Agent": "RecruitmentApp/1.0 (IT Job Crawler)"}
            )
            response.raise_for_status()

            try:
                raw_json = response.json()
            except (json.JSONDecodeError, ValueError) as json_err:
                msg = f"Dữ liệu phản hồi từ máy chủ không phải JSON hợp lệ ({json_err})."
                if use_fallback_on_error:
                    return False, self.FALLBACK_JOBS, f"{msg} Đã kích hoạt dữ liệu dự phòng offline."
                return False, [], msg

            jobs = self.normalize_job_data(raw_json)
            if not jobs and use_fallback_on_error:
                jobs = self.FALLBACK_JOBS
                return True, jobs, "Không tìm thấy việc làm mới từ API. Đã nạp dữ liệu mẫu."

            return True, jobs, f"Thu thập thành công {len(jobs)} tin tuyển dụng IT từ API."

        except requests.exceptions.ConnectionError as conn_err:
            msg = f"Lỗi kết nối mạng (ConnectionError): Không thể kết nối tới máy chủ tuyển dụng."
            if use_fallback_on_error:
                return False, self.FALLBACK_JOBS, f"{msg} Đã kích hoạt dữ liệu dự phòng offline."
            return False, [], msg

        except requests.exceptions.Timeout as timeout_err:
            msg = f"Hết thời gian chờ phản hồi (Timeout sau {self.REQUEST_TIMEOUT}s)."
            if use_fallback_on_error:
                return False, self.FALLBACK_JOBS, f"{msg} Đã kích hoạt dữ liệu dự phòng offline."
            return False, [], msg

        except requests.exceptions.RequestException as req_err:
            msg = f"Lỗi yêu cầu HTTP ({req_err})."
            if use_fallback_on_error:
                return False, self.FALLBACK_JOBS, f"{msg} Đã kích hoạt dữ liệu dự phòng offline."
            return False, [], msg

        except Exception as general_err:
            msg = f"Lỗi không xác định khi crawl dữ liệu: {general_err}"
            if use_fallback_on_error:
                return False, self.FALLBACK_JOBS, f"{msg} Đã kích hoạt dữ liệu dự phòng offline."
            return False, [], msg

    def save_crawled_jobs(self, jobs: List[Dict[str, Any]], filepath: Optional[str] = None) -> None:
        """Lưu danh sách tin tuyển dụng đã thu thập vào file JSON."""
        target_path = filepath or self.crawled_file
        self.file_manager.write_json(target_path, jobs, backup=False)

    def load_saved_crawled_jobs(self, filepath: Optional[str] = None) -> List[Dict[str, Any]]:
        """Đọc danh sách tin tuyển dụng đã lưu trong file JSON."""
        target_path = filepath or self.crawled_file
        return self.file_manager.read_json(target_path, default=[])
