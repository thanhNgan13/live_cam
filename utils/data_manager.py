"""
Data Manager - Quản lý dữ liệu tài xế
"""

import json
import os

# File lưu trữ dữ liệu tài xế
DRIVERS_FILE = "drivers_data.json"


def init_drivers_data():
    """Khởi tạo dữ liệu mẫu nếu file chưa tồn tại"""
    if not os.path.exists(DRIVERS_FILE):
        sample_data = {
            "drivers": [
                {
                    "id": 1,
                    "name": "Nguyễn Văn A",
                    "license": "B2-123456",
                    "phone": "0901234567",
                    "stream_url": "http://localhost:5001/video_feed/0",
                    "status": "active",
                    "created_at": "2025-11-01 08:00:00",
                },
                {
                    "id": 2,
                    "name": "Trần Thị B",
                    "license": "C-789012",
                    "phone": "0912345678",
                    "stream_url": "http://localhost:5001/video_feed/1",
                    "status": "active",
                    "created_at": "2025-11-02 09:00:00",
                },
                {
                    "id": 3,
                    "name": "Lê Văn C",
                    "license": "B2-345678",
                    "phone": "0923456789",
                    "stream_url": "http://localhost:5001/video_feed/0",
                    "status": "inactive",
                    "created_at": "2025-11-03 10:00:00",
                },
            ]
        }
        save_drivers_data(sample_data)
        return sample_data
    return load_drivers_data()


def load_drivers_data():
    """Đọc dữ liệu tài xế từ file JSON"""
    try:
        with open(DRIVERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"drivers": []}


def save_drivers_data(data):
    """Lưu dữ liệu tài xế vào file JSON"""
    with open(DRIVERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
