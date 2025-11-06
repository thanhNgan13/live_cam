from flask import render_template, jsonify, Response
from camera_utils import cameras, get_frame, generate_frames


def register_routes(app):
    """Đăng ký tất cả routes cho Flask app"""

    
