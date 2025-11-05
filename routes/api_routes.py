"""
API Routes - RESTful API endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.data_manager import load_drivers_data, save_drivers_data

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/drivers", methods=["GET"])
def get_drivers():
    """API lấy danh sách tài xế"""
    data = load_drivers_data()
    return jsonify(data["drivers"])


@api_bp.route("/drivers/<int:driver_id>", methods=["GET"])
def get_driver(driver_id):
    """API lấy thông tin một tài xế"""
    data = load_drivers_data()
    driver = next((d for d in data["drivers"] if d["id"] == driver_id), None)

    if not driver:
        return jsonify({"error": "Không tìm thấy tài xế"}), 404

    return jsonify(driver)


@api_bp.route("/drivers", methods=["POST"])
def add_driver():
    """API thêm tài xế mới"""
    new_driver = request.get_json()

    if not new_driver:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    data = load_drivers_data()

    # Tạo ID mới
    max_id = max([d["id"] for d in data["drivers"]], default=0)
    new_driver["id"] = max_id + 1
    new_driver["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_driver["status"] = new_driver.get("status", "active")

    data["drivers"].append(new_driver)
    save_drivers_data(data)

    return jsonify(new_driver), 201


@api_bp.route("/drivers/<int:driver_id>", methods=["PUT"])
def update_driver(driver_id):
    """API cập nhật thông tin tài xế"""
    update_data = request.get_json()

    if not update_data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    data = load_drivers_data()
    driver = next((d for d in data["drivers"] if d["id"] == driver_id), None)

    if not driver:
        return jsonify({"error": "Không tìm thấy tài xế"}), 404

    driver.update(update_data)
    save_drivers_data(data)

    return jsonify(driver)


@api_bp.route("/drivers/<int:driver_id>", methods=["DELETE"])
def delete_driver(driver_id):
    """API xóa tài xế"""
    data = load_drivers_data()
    data["drivers"] = [d for d in data["drivers"] if d["id"] != driver_id]
    save_drivers_data(data)

    return jsonify({"message": "Đã xóa tài xế"}), 200
