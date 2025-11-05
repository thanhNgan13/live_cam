"""
Admin Application - Quản lý tài xế và giám sát video
Cấu trúc:
- routes/: Chứa các blueprint routes (admin_routes, api_routes)
- utils/: Chứa các helper functions (data_manager)
- templates/admin/: Chứa các HTML templates
"""

from flask import Flask
from routes import admin_bp, api_bp
from utils import init_drivers_data


def create_app():
    """Factory function để tạo Flask app"""
    app = Flask(__name__)

    # Cấu hình
    app.config["JSON_AS_ASCII"] = False
    app.config["JSON_SORT_KEYS"] = False

    # Đăng ký blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app


# Tạo app instance
app = create_app()


# Tạo app instance
app = create_app()


if __name__ == "__main__":
    # Khởi tạo dữ liệu
    init_drivers_data()

    print("\n" + "=" * 70)
    print("🚗 ADMIN PANEL - QUẢN LÝ TÀI XẾ")
    print("=" * 70)
    print("\n📂 Cấu trúc:")
    print("   - routes/: Admin & API routes")
    print("   - utils/: Data manager & helpers")
    print("   - templates/admin/: HTML templates")
    print("\n🌐 Server đang chạy tại: http://localhost:5002")
    print("💡 Mở trình duyệt và truy cập URL trên để sử dụng")
    print("⚠️  Nhấn Ctrl+C để dừng server\n")

    app.run(host="0.0.0.0", port=5002, debug=True, threaded=True)
