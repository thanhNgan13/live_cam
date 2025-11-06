import cv2
import os
import socket
from flask import Flask, Response, jsonify, render_template
from flask_cors import CORS

from camera_utils import generate_frames, get_frame, init_cameras, cleanup, cameras
from routes import register_routes

# Tắt log cảnh báo của OpenCV
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
cv2.setLogLevel(0)

app = Flask(__name__, template_folder="templates")

# Enable CORS cho tất cả routes
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

@app.route("/")
def index():
    """Trang chủ"""
    return render_template(
        "index.html",
        cameras=list(cameras.keys()),
        camera_count=len(cameras),
        camera_list=str(list(cameras.keys())),
    )

@app.route("/cameras")
def list_cameras():
    """API trả về danh sách camera"""
    return jsonify({"cameras": list(cameras.keys()), "count": len(cameras)})

@app.route("/camera-<int:camera_id>")
def camera_page(camera_id):
    """Trang xem camera cụ thể"""
    if camera_id not in cameras:
        return f"Camera {camera_id} không tồn tại!", 404

    return render_template("camera_view.html", camera_id=camera_id)

@app.route("/video_feed/<int:camera_id>")
def video_feed(camera_id):
    """Stream video từ camera"""
    if camera_id not in cameras:
        return f"Camera {camera_id} không tồn tại!", 404

    return Response(generate_frames(camera_id), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/snapshot/<int:camera_id>")
def snapshot(camera_id):
    """Lấy một frame tĩnh (snapshot) từ camera"""
    if camera_id not in cameras:
        return f"Camera {camera_id} không tồn tại!", 404

    frame = get_frame(camera_id)

    if frame is None:
        return "Không thể lấy frame từ camera!", 500

    # Encode frame thành JPEG
    import cv2

    ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ret:
        return "Lỗi encode frame!", 500

    # Trả về ảnh JPEG
    response = Response(buffer.tobytes(), mimetype="image/jpeg")
    # Thêm CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


def is_port_available(host: str, port: int) -> bool:
    """Kiểm tra xem port có thể bind được hay không (True nếu rảnh)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Không cho phép reuse để kiểm tra chính xác
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.bind((host, int(port)))
        sock.close()
        return True
    except OSError:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA STREAMING SERVER - JETSON NANO")
    print("=" * 60)
    print()

    # Lấy host/port từ biến môi trường (nếu có) để dễ cấu hình
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))

    # Kiểm tra port có thể bind được trước khi mở camera
    if not is_port_available(host, port):
        print(f"[ERROR] Port {port} trên host {host} không thể sử dụng.")
        print("Hãy kiểm tra process đang dùng port này (PowerShell):")
        print(f"  netstat -aon | findstr :{port}")
        exit(1)

    # Khởi tạo camera
    available_cameras = init_cameras()

    if not available_cameras:
        print("[ERROR] Không tìm thấy camera nào!")
        exit(1)

    print()
    print(f"[OK] Server sẵn sàng với {len(available_cameras)} camera")
    print(f"Danh sách camera: {available_cameras}")
    print()
    print("Truy cập:")
    print(f"   - Trang chủ: http://localhost:{port}/")
    print(f"   - API cameras: http://localhost:{port}/cameras")

    for cam_id in available_cameras:
        print(f"   - Camera {cam_id}: http://localhost:{port}/camera-{cam_id}")
        print(f"   - Stream {cam_id}: http://localhost:{port}/video_feed/{cam_id}")
        print(f"   - Snapshot {cam_id}: http://localhost:{port}/snapshot/{cam_id}")

    print()
    print("[WARNING] Nhấn Ctrl+C để dừng server")
    print("=" * 60)
    print()

    try:
        app.run(host=host, port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[STOP] Đang dừng server...")
    finally:
        cleanup()
