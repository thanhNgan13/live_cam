"""
YOLO Processor - Xử lý detection cho video stream
Chức năng:
- Load YOLO model
- Đọc stream từ URL
- Detect và vẽ bounding boxes
- Stream lại video đã được detect
"""

import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from loguru import logger
import torch


class YOLOStreamProcessor:
    """Class xử lý video stream với YOLO detection"""

    def __init__(self, model_path="./models/yolo_based/customized_yolo11s.pt"):
        """
        Khởi tạo YOLO processor

        Args:
            model_path: Đường dẫn đến model YOLO
        """
        self.model_path = model_path
        self.model = None
        self.stream_url = None
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.lock = threading.Lock()
        self.detection_thread = None

        # Cấu hình detection
        self.conf_threshold = 0.5  # Ngưỡng confidence
        self.frame_skip = 3  # Bỏ qua nhiều frame để giảm lag (tăng từ 2 lên 5)
        self.frame_count = 0

        # Lưu trữ detections cuối cùng để vẽ lại trên mọi frame
        self.last_detections = []  # [(x1, y1, x2, y2, conf, class_name), ...]

        # WebSocket callback để emit frames
        self.frame_callback = None

        # FPS tracking
        self.fps_start_time = None
        self.fps_frame_count = 0
        self.fps_log_interval = 60  # Log FPS mỗi 60 frames
        self.current_fps = 0.0  # FPS hiện tại để vẽ lên frame

        # GPU info
        self.gpu_info = "CPU"  # Mặc định CPU

        # Load model
        self.load_model()

    def load_model(self):
        """Load YOLO model"""
        try:
            logger.info(f"Loading YOLO model from {self.model_path}")
            self.model = YOLO(self.model_path)

            # Kiểm tra GPU
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
                self.gpu_info = f"{gpu_name} ({gpu_memory:.1f}GB)"
                logger.success(f"✓ YOLO model loaded successfully!")
                logger.success(f"✓ GPU: {self.gpu_info}")
                logger.success(f"✓ CUDA Version: {torch.version.cuda}")
            else:
                self.gpu_info = "CPU (No GPU)"
                logger.warning("⚠ GPU not available - running on CPU")
                logger.warning("⚠ Performance will be significantly slower")

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def set_stream_url(self, url):
        """
        Set URL của camera stream

        Args:
            url: URL của camera stream
        """
        self.stream_url = url
        logger.info(f"Stream URL set to: {url}")

    def set_frame_callback(self, callback):
        """
        Set callback function để emit frames qua WebSocket

        Args:
            callback: Function nhận frame_bytes làm parameter
        """
        self.frame_callback = callback
        logger.info("Frame callback set for WebSocket streaming")

    def start_processing(self):
        """Bắt đầu xử lý video stream"""
        if self.is_running:
            logger.warning("Processor is already running")
            return

        if not self.stream_url:
            logger.error("Stream URL not set")
            return

        self.is_running = True
        self.detection_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.detection_thread.start()
        logger.info("Started video processing")

    def stop_processing(self):
        """Dừng xử lý video stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Stopped video processing")

    def _process_loop(self):
        """Loop chính để xử lý video"""
        try:
            # Mở video stream
            self.cap = cv2.VideoCapture(self.stream_url)

            if not self.cap.isOpened():
                logger.error(f"Cannot open stream: {self.stream_url}")
                self.is_running = False
                return

            logger.info("Video stream opened successfully")

            # Khởi tạo FPS tracking
            self.fps_start_time = time.time()
            self.fps_frame_count = 0

            while self.is_running:
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning("Failed to read frame, retrying...")
                    time.sleep(0.1)
                    continue

                # Tăng frame counter
                self.frame_count += 1
                self.fps_frame_count += 1

                # Tính FPS hiện tại
                if self.fps_frame_count > 1:  # Tránh chia cho 0
                    elapsed = time.time() - self.fps_start_time
                    if elapsed > 0:
                        self.current_fps = self.fps_frame_count / elapsed

                # Log FPS định kỳ
                if self.fps_frame_count % self.fps_log_interval == 0:
                    elapsed = time.time() - self.fps_start_time
                    fps = self.fps_frame_count / elapsed
                    logger.info(
                        f"📊 FPS: {fps:.2f} | Frames: {self.fps_frame_count} | Detection every {self.frame_skip} frames"
                    )
                    # Reset counter
                    self.fps_start_time = time.time()
                    self.fps_frame_count = 0

                # Chỉ chạy detection trên một số frame
                if self.frame_count % self.frame_skip == 0:
                    # Chạy detection và cập nhật last_detections
                    self._detect_and_update(frame)

                # Luôn vẽ bounding boxes (dùng detection cũ nếu không chạy detection mới)
                processed_frame = self._draw_boxes(frame, self.last_detections)

                # Vẽ performance stats lên frame
                processed_frame = self._draw_performance_stats(processed_frame)

                # Lưu frame đã xử lý
                with self.lock:
                    self.current_frame = processed_frame

                # Emit frame qua WebSocket callback nếu có
                if self.frame_callback:
                    try:
                        # Encode frame thành JPEG
                        ret, buffer = cv2.imencode(".jpg", processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if ret:
                            frame_bytes = buffer.tobytes()
                            self.frame_callback(frame_bytes)
                    except Exception as e:
                        logger.error(f"Error in frame callback: {e}")

        except Exception as e:
            logger.error(f"Error in process loop: {e}")
        finally:
            if self.cap:
                self.cap.release()

    def _detect_and_update(self, frame):
        """
        Chạy detection và cập nhật last_detections

        Args:
            frame: Frame từ video
        """
        try:
            # Chạy YOLO detection
            results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)

            # Cập nhật detections
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Lấy thông tin box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = self.model.names[cls_id]

                    # Bỏ qua class "natural"
                    if class_name == "natural":
                        continue

                    detections.append((x1, y1, x2, y2, conf, class_name))

            # Cập nhật last_detections
            self.last_detections = detections

        except Exception as e:
            logger.error(f"Error in detection: {e}")

    def _draw_boxes(self, frame, detections):
        """
        Vẽ bounding boxes lên frame

        Args:
            frame: Frame từ video
            detections: List of (x1, y1, x2, y2, conf, class_name)

        Returns:
            Frame đã được vẽ bounding boxes
        """
        annotated_frame = frame.copy()

        for x1, y1, x2, y2, conf, class_name in detections:
            # Chọn màu theo class
            color = self._get_color_for_class(class_name)

            # Vẽ bounding box (giảm độ dày từ 2 xuống 1)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 1)

            # Vẽ label
            label = f"{class_name}: {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            # Vẽ background cho text
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 8), (x1 + label_size[0], y1), color, -1)

            # Chọn màu chữ: đen cho look_away (nền vàng), trắng cho các class khác
            text_color = (0, 0, 0) if class_name == "look_away" else (255, 255, 255)

            # Vẽ text (giảm font size và thickness)
            cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)

        return annotated_frame

    def _draw_performance_stats(self, frame):
        """
        Vẽ performance stats lên frame (FPS, GPU info)

        Args:
            frame: Frame đã vẽ bounding boxes

        Returns:
            Frame với performance overlay
        """
        h, w = frame.shape[:2]

        # Thông tin hiển thị
        fps_text = f"FPS: {self.current_fps:.1f}"
        gpu_text = f"Device: {self.gpu_info}"
        objects_text = f"Objects: {len(self.last_detections)}"

        # Cấu hình hiển thị
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        padding = 10
        line_height = 30

        # Vẽ nền semi-transparent cho stats panel
        overlay = frame.copy()
        panel_height = line_height * 3 + padding * 2
        cv2.rectangle(overlay, (10, 10), (400, 10 + panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Vẽ text
        y_offset = 10 + padding + 20
        cv2.putText(frame, fps_text, (20, y_offset), font, font_scale, (0, 255, 0), thickness)
        y_offset += line_height
        cv2.putText(frame, gpu_text, (20, y_offset), font, font_scale, (0, 255, 255), thickness)
        y_offset += line_height
        cv2.putText(frame, objects_text, (20, y_offset), font, font_scale, (255, 255, 255), thickness)

        return frame

    def _detect_and_draw(self, frame):
        """
        DEPRECATED: Sử dụng _detect_and_update + _draw_boxes thay thế
        Chạy detection và vẽ bounding boxes

        Args:
            frame: Frame từ video

        Returns:
            Frame đã được vẽ bounding boxes
        """
        try:
            # Chạy YOLO detection
            results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)

            # Vẽ bounding boxes
            annotated_frame = frame.copy()

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Lấy thông tin box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = self.model.names[cls_id]

                    # Bỏ qua class "natural" - không vẽ bounding box
                    if class_name == "natural":
                        continue

                    # Chọn màu theo class
                    color = self._get_color_for_class(class_name)

                    # Vẽ bounding box
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

                    # Vẽ label
                    label = f"{class_name}: {conf:.2f}"
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

                    # Vẽ background cho text
                    cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)

                    # Vẽ text
                    cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            return annotated_frame

        except Exception as e:
            logger.error(f"Error in detection: {e}")
            return frame

    def _get_color_for_class(self, class_name):
        """
        Lấy màu cho từng loại class

        Args:
            class_name: Tên class

        Returns:
            Tuple màu BGR
        """
        color_map = {
            "sleepy_eye": (0, 0, 255),  # Đỏ tươi - nguy hiểm cao nhất
            "yawn": (0, 140, 255),  # Cam đậm - buồn ngủ
            "look_away": (0, 255, 255),  # Vàng - mất tập trung
            "phone": (255, 0, 255),  # Tím/Hồng - dùng điện thoại
            "rub_eye": (60, 180, 255),  # Cam nhạt - dụi mắt
            "natural": (0, 255, 0),  # Xanh lá - bình thường
        }
        return color_map.get(class_name, (255, 255, 255))  # Trắng - mặc định

    def get_current_frame(self):
        """
        Lấy frame hiện tại đã được xử lý

        Returns:
            Frame đã được detect (numpy array) hoặc None
        """
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def generate_frames(self):
        """
        Generator để stream frames qua HTTP (MJPEG)

        Yields:
            Bytes của frame dưới dạng JPEG
        """
        while True:
            frame = self.get_current_frame()

            if frame is None:
                time.sleep(0.1)
                continue

            # Encode frame thành JPEG
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            # Yield frame theo format MJPEG
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


# Multi-instance management - Mỗi stream_url có 1 processor riêng
_processor_instances = {}


def get_processor(stream_url):
    """
    Lấy hoặc tạo processor cho stream_url cụ thể

    Args:
        stream_url: URL của stream cần detect

    Returns:
        YOLOStreamProcessor instance cho stream đó
    """
    global _processor_instances

    if stream_url not in _processor_instances:
        logger.info(f"Creating new YOLO processor for stream: {stream_url}")
        processor = YOLOStreamProcessor()
        processor.set_stream_url(stream_url)
        _processor_instances[stream_url] = processor

    return _processor_instances[stream_url]


def remove_processor(stream_url):
    """
    Xóa processor cho stream_url cụ thể

    Args:
        stream_url: URL của stream cần xóa processor
    """
    global _processor_instances

    if stream_url in _processor_instances:
        logger.info(f"Removing YOLO processor for stream: {stream_url}")
        _processor_instances[stream_url].stop_processing()
        del _processor_instances[stream_url]


def get_active_streams():
    """
    Lấy danh sách các stream đang active

    Returns:
        List of stream URLs đang được detect
    """
    return [url for url, proc in _processor_instances.items() if proc.is_running]
