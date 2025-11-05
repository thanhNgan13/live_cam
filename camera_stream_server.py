import cv2
import numpy as np
import os
from flask import Flask, Response, render_template_string, jsonify
import threading
import time
import socket

# Tắt log cảnh báo của OpenCV
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
cv2.setLogLevel(0)

app = Flask(__name__)

# Dictionary lưu trữ camera instances
cameras = {}
camera_locks = {}

# Load Haar Cascade cho face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")  # type: ignore


def find_available_cameras(max_cameras=10):
    """Tìm tất cả camera khả dụng"""
    available_cameras = []
    print("Đang quét camera...")

    for i in range(max_cameras):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                available_cameras.append(i)
                print(f"[OK] Tìm thấy camera {i}")
            cap.release()

    return available_cameras


def init_cameras():
    """Khởi tạo tất cả camera"""
    available = find_available_cameras()

    for cam_id in available:
        cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cameras[cam_id] = cap
            camera_locks[cam_id] = threading.Lock()
            print(f"[OK] Camera {cam_id} đã sẵn sàng")

    return list(cameras.keys())


def get_frame(camera_id, detect_face=False):
    """Đọc frame từ camera"""
    if camera_id not in cameras:
        return None

    with camera_locks[camera_id]:
        cap = cameras[camera_id]
        ret, frame = cap.read()

        if not ret or frame is None:
            return None

        # Face detection nếu được yêu cầu
        if detect_face:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Vẽ box cho mỗi khuôn mặt
            for x, y, w, h in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Hiển thị số khuôn mặt
            cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Thêm info camera
        cv2.putText(
            frame, f"Camera {camera_id}", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        return frame


def generate_frames(camera_id, detect_face=False):
    """Generator cho video streaming"""
    while True:
        frame = get_frame(camera_id, detect_face)

        if frame is None:
            time.sleep(0.1)
            continue

        # Encode frame thành JPEG
        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # Yield frame theo format multipart
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


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


# HTML template cho trang xem camera
CAMERA_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Camera {{ camera_id }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            color: #4CAF50;
            margin-bottom: 10px;
        }
        .container {
            max-width: 1200px;
            width: 100%;
        }
        .video-container {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        img {
            width: 100%;
            height: auto;
            border-radius: 5px;
            display: block;
        }
        .controls {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        button, a.button {
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
        }
        button:hover, a.button:hover {
            background: #45a049;
        }
        button.active {
            background: #ff9800;
        }
        .info {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .status {
            color: #4CAF50;
            font-weight: bold;
        }
        a {
            color: #4CAF50;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📹 Camera {{ camera_id }}</h1>
        
        <div class="video-container">
            <img src="/video_feed/{{ camera_id }}{{ '?detect=true' if detect_face else '' }}" 
                 alt="Camera {{ camera_id }}" id="videoFeed">
            
            <div class="controls">
                <button onclick="toggleDetection()" id="detectBtn">
                    {{ 'Tắt' if detect_face else 'Bật' }} Face Detection
                </button>
                <a href="/" class="button">🏠 Trang chủ</a>
                <a href="/cameras" class="button">📋 Danh sách camera</a>
            </div>
        </div>
        
        <div class="info">
            <p><span class="status">● Đang live</span></p>
            <p>Đường dẫn stream: <code>/video_feed/{{ camera_id }}</code></p>
            <p>Đường dẫn với face detection: <code>/video_feed/{{ camera_id }}?detect=true</code></p>
        </div>
    </div>

    <script>
        function toggleDetection() {
            const currentUrl = window.location.href;
            if (currentUrl.includes('detect=true')) {
                window.location.href = '/camera-{{ camera_id }}';
            } else {
                window.location.href = '/camera-{{ camera_id }}?detect=true';
            }
        }
        
        // Update button state
        const btn = document.getElementById('detectBtn');
        if ('{{ detect_face }}' === 'True') {
            btn.classList.add('active');
        }
    </script>
</body>
</html>
"""

# HTML template cho trang chủ
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Camera Streaming Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .camera-card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }
        .camera-card:hover {
            transform: translateY(-5px);
        }
        .camera-preview {
            width: 100%;
            height: 200px;
            background: #1a1a1a;
            border-radius: 5px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        .camera-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        h3 {
            margin: 0 0 10px 0;
            color: #4CAF50;
        }
        .links {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        a {
            padding: 10px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            text-align: center;
            transition: background 0.2s;
        }
        a:hover {
            background: #45a049;
        }
        .info {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        code {
            background: #1a1a1a;
            padding: 2px 6px;
            border-radius: 3px;
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Camera Streaming Server</h1>
        
        <div class="info">
            <h3>📡 Server đang chạy</h3>
            <p>Tổng số camera: <strong>{{ camera_count }}</strong></p>
            <p>Danh sách camera: <strong>{{ camera_list }}</strong></p>
        </div>
        
        <div class="camera-grid">
            {% for cam_id in cameras %}
            <div class="camera-card">
                <div class="camera-preview">
                    <img src="/video_feed/{{ cam_id }}" alt="Camera {{ cam_id }}">
                </div>
                <h3>📹 Camera {{ cam_id }}</h3>
                <div class="links">
                    <a href="/camera-{{ cam_id }}">Xem Camera</a>
                    <a href="/camera-{{ cam_id }}?detect=true">Xem với Face Detection</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""


# Routes
@app.route("/")
def index():
    """Trang chủ"""
    return render_template_string(
        HOME_PAGE_TEMPLATE,
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

    detect_face = request.args.get("detect", "false").lower() == "true"

    return render_template_string(CAMERA_PAGE_TEMPLATE, camera_id=camera_id, detect_face=detect_face)


@app.route("/video_feed/<int:camera_id>")
def video_feed(camera_id):
    """Stream video từ camera"""
    if camera_id not in cameras:
        return f"Camera {camera_id} không tồn tại!", 404

    detect_face = request.args.get("detect", "false").lower() == "true"

    return Response(generate_frames(camera_id, detect_face), mimetype="multipart/x-mixed-replace; boundary=frame")


def cleanup():
    """Giải phóng tài nguyên khi tắt server"""
    print("\nĐang đóng tất cả camera...")
    for cam_id, cap in cameras.items():
        cap.release()
    print("[OK] Đã đóng tất cả camera")


if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA STREAMING SERVER")
    print("=" * 60)
    print()

    # Lấy host/port từ biến môi trường (nếu có) để dễ cấu hình
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))

    # Kiểm tra port có thể bind được trước khi mở camera
    if not is_port_available(host, port):
        print(f"[ERROR] Port {port} trên host {host} không thể sử dụng (bị chiếm hoặc bị chặn).")
        print("Hãy kiểm tra process đang dùng port này (PowerShell):")
        print(f"  netstat -aon | findstr :{port}")
        print(f"hoặc:\n  Get-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess")
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
        print(f"   - Camera {cam_id} + Face Detection: http://localhost:{port}/camera-{cam_id}?detect=true")
        print(f"   - Stream {cam_id}: http://localhost:{port}/video_feed/{cam_id}")

    print()
    print("[WARNING] Nhấn Ctrl+C để dừng server")
    print("=" * 60)
    print()

    try:
        # Import request ở đây để tránh lỗi
        from flask import request

        app.run(host=host, port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[STOP] Đang dừng server...")
    finally:
        cleanup()
