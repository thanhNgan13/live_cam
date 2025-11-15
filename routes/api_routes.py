"""
API Routes - RESTful API endpoints
"""

from flask import Blueprint, request, jsonify, Response, send_file
from datetime import datetime
from pathlib import Path
from utils.data_manager import load_drivers_data, save_drivers_data
from yolo_processor import get_processor
from multi_camera_manager import get_multi_camera_manager, CameraInfo
from alert_logger import get_alert_logger

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
        processor.set_stream_url(stream_url, driver_id=str(driver_id))
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


@api_bp.route("/yolo/stats", methods=["GET"])
def get_yolo_stats():
    """
    API để lấy thống kê về alerts
    
    Returns:
        JSON với thống kê
    """
    try:
        processor = get_processor()
        stats = processor.alert_manager.get_statistics()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== Multi Camera APIs ====================


@api_bp.route("/cameras", methods=["GET"])
def get_all_cameras():
    """
    API lấy danh sách tất cả cameras đang hoạt động
    
    Returns:
        JSON với danh sách cameras
    """
    try:
        manager = get_multi_camera_manager()
        cameras = manager.get_all_cameras()
        
        return jsonify({
            "cameras": [
                {
                    "camera_id": cam.camera_id,
                    "driver_id": cam.driver_id,
                    "driver_name": cam.driver_name,
                    "stream_url": cam.stream_url,
                    "is_active": cam.is_active
                }
                for cam in cameras
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cameras/start/<int:driver_id>", methods=["POST"])
def start_camera(driver_id):
    """
    API để bắt đầu một camera mới
    
    Args:
        driver_id: ID của tài xế
        
    Returns:
        JSON response
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
        
        # Tạo camera info
        camera_info = CameraInfo(
            camera_id=f"cam_{driver_id}",
            driver_id=driver_id,
            driver_name=driver["name"],
            stream_url=stream_url
        )
        
        # Thêm camera
        manager = get_multi_camera_manager()
        success = manager.add_camera(camera_info)
        
        if success:
            return jsonify({
                "message": "Đã bắt đầu camera",
                "camera_id": camera_info.camera_id
            }), 200
        else:
            return jsonify({"error": "Không thể khởi động camera"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cameras/stop/<camera_id>", methods=["POST"])
def stop_camera(camera_id):
    """
    API để dừng một camera
    
    Args:
        camera_id: ID của camera
        
    Returns:
        JSON response
    """
    try:
        manager = get_multi_camera_manager()
        success = manager.remove_camera(camera_id)
        
        if success:
            return jsonify({"message": "Đã dừng camera"}), 200
        else:
            return jsonify({"error": "Không tìm thấy camera"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cameras/stream/<camera_id>")
def camera_video_stream(camera_id):
    """
    API để stream video từ một camera cụ thể
    
    Args:
        camera_id: ID của camera
        
    Returns:
        Response chứa video stream
    """
    try:
        manager = get_multi_camera_manager()
        processor = manager.get_camera(camera_id)
        
        if not processor:
            return jsonify({"error": "Không tìm thấy camera"}), 404
        
        return Response(
            processor.generate_frames(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cameras/stats", methods=["GET"])
def get_cameras_stats():
    """
    API lấy thống kê của tất cả cameras
    
    Returns:
        JSON với thống kê
    """
    try:
        manager = get_multi_camera_manager()
        stats = manager.get_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cameras/stop-all", methods=["POST"])
def stop_all_cameras():
    """
    API để dừng tất cả cameras
    
    Returns:
        JSON response
    """
    try:
        manager = get_multi_camera_manager()
        manager.stop_all()
        return jsonify({"message": "Đã dừng tất cả cameras"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== Alert Logs APIs ====================


@api_bp.route("/alert-logs", methods=["GET"])
def get_alert_logs():
    """
    API lấy alert logs
    Query params:
        - date: YYYY-MM-DD (optional, lấy logs theo ngày)
        - limit: số lượng logs (default: 100)
    
    Returns:
        JSON với danh sách logs
    """
    try:
        alert_logger = get_alert_logger()
        
        date_str = request.args.get('date')
        limit = int(request.args.get('limit', 100))
        
        if date_str:
            logs = alert_logger.get_logs_by_date(date_str)
        else:
            logs = alert_logger.get_all_logs(limit)
        
        return jsonify({
            "total": len(logs),
            "logs": logs
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/alert-logs/evidence/<path:filename>", methods=["GET"])
def get_evidence_file(filename):
    """
    API lấy file evidence (video/ảnh)
    
    Args:
        filename: Đường dẫn tương đối của file
    
    Returns:
        File evidence
    """
    try:
        evidence_dir = Path("alert_evidence")
        file_path = evidence_dir / filename
        
        if not file_path.exists():
            return jsonify({"error": "File không tồn tại"}), 404
        
        return send_file(str(file_path))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
