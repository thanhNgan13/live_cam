"""
API Routes - RESTful API endpoints
"""

from flask import Blueprint, request, jsonify, Response
from datetime import datetime
from utils.data_manager import load_drivers_data, save_drivers_data
from yolo_processor import get_processor

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


# ==================== YOLO Detection APIs ====================


@api_bp.route("/yolo/start/<int:driver_id>", methods=["POST"])
def start_yolo_detection(driver_id):
    """
    API để bắt đầu YOLO detection cho một tài xế

    Args:
        driver_id: ID của tài xế cần detect

    Returns:
        JSON response với status
    """
    try:
        # Lấy thông tin tài xế
        data = load_drivers_data()
        driver = next((d for d in data["drivers"] if d["id"] == driver_id), None)

        if not driver:
            return jsonify({"error": "Không tìm thấy tài xế"}), 404

        stream_url = driver.get("stream_url")
        if not stream_url:
            return jsonify({"error": "Tài xế chưa có stream URL"}), 400

        # Khởi động YOLO processor
        processor = get_processor()
        processor.set_stream_url(stream_url)
        processor.start_processing()

        return jsonify({"message": "Đã bắt đầu YOLO detection", "driver_id": driver_id, "stream_url": stream_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/yolo/stop", methods=["POST"])
def stop_yolo_detection():
    """
    API để dừng YOLO detection

    Returns:
        JSON response với status
    """
    try:
        processor = get_processor()
        processor.stop_processing()

        return jsonify({"message": "Đã dừng YOLO detection"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/yolo/stream")
def yolo_video_stream():
    """
    API để stream video đã được YOLO detect

    Returns:
        Response chứa video stream (MJPEG format)
    """
    try:
        processor = get_processor()
        return Response(processor.generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
