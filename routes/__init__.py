"""
Routes package
Chứa các blueprint routes cho ứng dụng
"""

from .admin_routes import admin_bp
from .api_routes import api_bp

__all__ = ["admin_bp", "api_bp"]
