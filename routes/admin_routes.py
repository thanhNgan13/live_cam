"""
Admin Routes - Các routes cho giao diện web admin
"""

from flask import Blueprint, render_template
from utils.data_manager import load_drivers_data

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
def index():
    """Trang chủ - Danh sách tài xế"""
    data = load_drivers_data()
    return render_template("admin/dashboard/index.html", drivers=data["drivers"])


@admin_bp.route("/driver/<int:driver_id>")
def view_driver(driver_id):
    """Trang xem video của tài xế"""
    import time

    data = load_drivers_data()
    driver = next((d for d in data["drivers"] if d["id"] == driver_id), None)

    if not driver:
        return "Không tìm thấy tài xế!", 404

    timestamp = int(time.time())
    return render_template("admin/driver_view/index.html", driver=driver, timestamp=timestamp)


@admin_bp.route("/add-driver")
def add_driver_page():
    """Trang thêm tài xế mới"""
    return render_template("admin/add_driver/index.html")


@admin_bp.route("/edit-driver/<int:driver_id>")
def edit_driver_page(driver_id):
    """Trang chỉnh sửa tài xế"""
    data = load_drivers_data()
    driver = next((d for d in data["drivers"] if d["id"] == driver_id), None)

    if not driver:
        return "Không tìm thấy tài xế!", 404

    return render_template("admin/edit_driver/index.html", driver=driver)


@admin_bp.route("/yolo-test")
def yolo_test():
    """Trang test YOLO detection"""
    return render_template("admin/yolo_test.html")


@admin_bp.route("/multi-camera")
def multi_camera():
    """Trang giám sát nhiều camera"""
    return render_template("admin/multi_camera_view.html")


@admin_bp.route("/alert-logs")
def alert_logs():
    """Trang xem alert logs"""
    return render_template("admin/alert_logs/index.html")
