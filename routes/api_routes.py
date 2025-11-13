"""
API Routes - RESTful API endpoints
"""

from flask import Blueprint, request, jsonify, Response
from datetime import datetime
from utils.data_manager import load_drivers_data, save_drivers_data
from yolo_processor import get_processor, remove_processor, get_active_streams

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


@api_bp.route("/yolo/start", methods=["POST"])
def start_yolo_detection():
    """
    API để bắt đầu YOLO detection

    Request body:
        {
            "stream_url": "http://localhost:5000/video_feed/0"
        }

    Returns:
        JSON response với status
    """
    try:
        request_data = request.get_json()

        if not request_data:
            return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

        stream_url = request_data.get("stream_url")
        if not stream_url:
            return jsonify({"error": "Thiếu stream_url trong request"}), 400

        # Lấy hoặc tạo processor cho stream này
        processor = get_processor(stream_url)
        
        # Nếu đang chạy rồi thì không cần start lại
        if processor.is_running:
            return jsonify({"message": "Stream đang được detect", "stream_url": stream_url}), 200
        
        processor.start_processing()

        return jsonify({"message": "Đã bắt đầu YOLO detection", "stream_url": stream_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/yolo/stop", methods=["POST"])
def stop_yolo_detection():
    """
    API để dừng YOLO detection

    Request body:
        {
            "stream_url": "http://localhost:5000/video_feed/0"
        }

    Returns:
        JSON response với status
    """
    try:
        request_data = request.get_json()

        if not request_data:
            return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

        stream_url = request_data.get("stream_url")
        if not stream_url:
            return jsonify({"error": "Thiếu stream_url trong request"}), 400

        # Xóa processor cho stream này
        remove_processor(stream_url)

        return jsonify({"message": "Đã dừng YOLO detection", "stream_url": stream_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/yolo/stream")
def yolo_video_stream():
    """
    API để stream video đã được YOLO detect

    Query params:
        stream_url: URL của stream gốc

    Returns:
        Response chứa video stream (MJPEG format)
    """
    try:
        stream_url = request.args.get("stream_url")
        
        if not stream_url:
            return jsonify({"error": "Thiếu stream_url trong query params"}), 400
        
        processor = get_processor(stream_url)
        
        if not processor.is_running:
            return jsonify({"error": "Stream chưa được khởi động"}), 400
        
        return Response(processor.generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/yolo/active-streams", methods=["GET"])
def get_yolo_active_streams():
    """
    API để lấy danh sách các stream đang được YOLO detect

    Returns:
        JSON response với danh sách stream URLs
    """
    try:
        active_streams = get_active_streams()
        return jsonify({
            "active_streams": active_streams,
            "count": len(active_streams)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
