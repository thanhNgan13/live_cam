"""
Admin Application - Quản lý tài xế và giám sát video
Cấu trúc:
- routes/: Chứa các blueprint routes (admin_routes, api_routes)
- utils/: Chứa các helper functions (data_manager)
- templates/admin/: Chứa các HTML templates
"""

from flask import Flask, request
from flask_socketio import SocketIO, emit
from routes import admin_bp, api_bp
from utils import init_drivers_data
from yolo_processor import get_processor


def create_app():
    """Factory function để tạo Flask app"""
    app = Flask(__name__)

    # Cấu hình
    app.config["JSON_AS_ASCII"] = False
    app.config["JSON_SORT_KEYS"] = False
    app.config["SECRET_KEY"] = "yolo-detection-secret-key"

    # Đăng ký blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app


# Tạo app instance
app = create_app()

# Khởi tạo SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


# WebSocket Events
@socketio.on("connect")
def handle_connect():
    """Xử lý khi client kết nối"""
    print(f"[WebSocket] Client connected: {request.sid if 'request' in dir() else 'unknown'}")
    emit("connection_response", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """Xử lý khi client ngắt kết nối"""
    print(f"[WebSocket] Client disconnected")


@socketio.on("start_yolo_stream")
def handle_start_stream(data):
    """Bắt đầu YOLO stream qua WebSocket"""
    try:
        stream_url = data.get("stream_url")
        if not stream_url:
            emit("error", {"message": "Thiếu stream_url"})
            return

        # Lưu session ID của client hiện tại
        client_sid = request.sid

        # Lấy processor cho stream này
        processor = get_processor(stream_url)

        # Set callback để emit frames qua WebSocket
        def emit_frame(frame_bytes):
            # Gửi binary trực tiếp, không cần base64 (tiết kiệm ~33% bandwidth)
            socketio.emit("yolo_frame", frame_bytes, room=client_sid, namespace="/")

        processor.set_frame_callback(emit_frame)

        # Start processing nếu chưa chạy
        if not processor.is_running:
            processor.start_processing()

        emit("stream_started", {"stream_url": stream_url})
        print(f"[WebSocket] Started YOLO stream: {stream_url}")

    except Exception as e:
        emit("error", {"message": str(e)})
        print(f"[WebSocket] Error starting stream: {e}")


@socketio.on("stop_yolo_stream")
def handle_stop_stream(data):
    """Dừng YOLO stream qua WebSocket"""
    try:
        stream_url = data.get("stream_url")
        if not stream_url:
            emit("error", {"message": "Thiếu stream_url"})
            return

        processor = get_processor(stream_url)

        # Remove callback
        processor.set_frame_callback(None)

        emit("stream_stopped", {"stream_url": stream_url})
        print(f"[WebSocket] Stopped YOLO stream: {stream_url}")

    except Exception as e:
        emit("error", {"message": str(e)})
        print(f"[WebSocket] Error stopping stream: {e}")


if __name__ == "__main__":
    # Khởi tạo dữ liệu
    init_drivers_data()

    print("\n" + "=" * 70)
    print("🚗 ADMIN PANEL - QUẢN LÝ TÀI XẾ (WebSocket Enabled)")
    print("=" * 70)
    print("\n📂 Cấu trúc:")
    print("   - routes/: Admin & API routes")
    print("   - utils/: Data manager & helpers")
    print("   - templates/admin/: HTML templates")
    print("\n🌐 Server đang chạy tại: http://localhost:5002")
    print("🔌 WebSocket enabled cho real-time YOLO streaming")
    print("💡 Mở trình duyệt và truy cập URL trên để sử dụng")
    print("⚠️  Nhấn Ctrl+C để dừng server\n")

    # Chạy với SocketIO thay vì app.run()
    socketio.run(app, host="0.0.0.0", port=5002, debug=True, allow_unsafe_werkzeug=True)
