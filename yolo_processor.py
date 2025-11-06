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
        self.frame_skip = 5  # Bỏ qua nhiều frame để giảm lag (tăng từ 2 lên 5)
        self.frame_count = 0

        # Lưu trữ detections cuối cùng để vẽ lại trên mọi frame
        self.last_detections = []  # [(x1, y1, x2, y2, conf, class_name), ...]

        # Load model
        self.load_model()

    def load_model(self):
        """Load YOLO model"""
        try:
            logger.info(f"Loading YOLO model from {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.success("YOLO model loaded successfully!")
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

            while self.is_running:
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning("Failed to read frame, retrying...")
                    time.sleep(0.1)
                    continue

                # Tăng frame counter
                self.frame_count += 1

                # Chỉ chạy detection trên một số frame
                if self.frame_count % self.frame_skip == 0:
                    # Chạy detection và cập nhật last_detections
                    self._detect_and_update(frame)

                # Luôn vẽ bounding boxes (dùng detection cũ nếu không chạy detection mới)
                processed_frame = self._draw_boxes(frame, self.last_detections)

                # Lưu frame đã xử lý
                with self.lock:
                    self.current_frame = processed_frame

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


# Singleton instance
_processor_instance = None


def get_processor():
    """
    Lấy singleton instance của YOLOStreamProcessor

    Returns:
        YOLOStreamProcessor instance
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = YOLOStreamProcessor()
    return _processor_instance
