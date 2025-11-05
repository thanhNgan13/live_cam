"""
Configuration - Cấu hình cho ứng dụng
"""

import os

# Server Configuration
HOST = "0.0.0.0"
PORT = 5002
DEBUG = True

# Data Configuration
DRIVERS_FILE = "drivers_data.json"

# Flask Configuration
JSON_AS_ASCII = False
JSON_SORT_KEYS = False

# Security (có thể thêm sau)
# SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

# Camera Server (mặc định)
DEFAULT_CAMERA_SERVER = "http://localhost:5001"
