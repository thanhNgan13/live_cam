"""
Multi Camera Manager - Quản lý nhiều camera streams
Chức năng:
- Hỗ trợ stream từ nhiều camera đồng thời
- Mỗi camera có processor và alert manager riêng
- Quản lý trạng thái của từng camera
"""

import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from loguru import logger
from alert_manager import AlertManager, Alert


@dataclass
class CameraInfo:
    """Thông tin về một camera"""
    camera_id: str
    driver_id: int
    driver_name: str
    stream_url: str
    is_active: bool = False


class SingleCameraProcessor:
    """
    Xử lý một camera đơn lẻ
    Tương tự YOLOStreamProcessor nhưng có thêm AlertManager
    """
    
    def __init__(self, camera_info: CameraInfo, model_path: str):
        """
        Khởi tạo processor cho một camera
        
        Args:
            camera_info: Thông tin camera
            model_path: Đường dẫn model YOLO
        """
        self.camera_info = camera_info
        self.model_path = model_path
        self.model = None
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.lock = threading.Lock()
        self.process_thread = None
        
        # Alert manager riêng cho camera này
        self.alert_manager = AlertManager()
        
        # Cấu hình
        self.conf_threshold = 0.5
        self.frame_skip = 5
        self.frame_count = 0
        self.last_detections = []
        
        # Thống kê
        self.stats = {
            "total_frames": 0,
            "processed_frames": 0,
            "total_alerts": 0,
            "fps": 0.0
        }
        self.last_fps_time = time.time()
        self.fps_frame_count = 0
        
        # Load model
        self.load_model()
    
    def load_model(self):
        """Load YOLO model"""
        try:
            logger.info(f"[{self.camera_info.camera_id}] Loading YOLO model...")
            self.model = YOLO(self.model_path)
            logger.success(f"[{self.camera_info.camera_id}] Model loaded successfully!")
        except Exception as e:
            logger.error(f"[{self.camera_info.camera_id}] Failed to load model: {e}")
            raise
    
    def start(self):
        """Bắt đầu xử lý"""
        if self.is_running:
            logger.warning(f"[{self.camera_info.camera_id}] Already running")
            return
        
        self.is_running = True
        self.camera_info.is_active = True
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        logger.info(f"[{self.camera_info.camera_id}] Started processing")
    
    def stop(self):
        """Dừng xử lý"""
        self.is_running = False
        self.camera_info.is_active = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info(f"[{self.camera_info.camera_id}] Stopped processing")
    
    def _process_loop(self):
        """Loop xử lý chính"""
        try:
            # Mở stream
            self.cap = cv2.VideoCapture(self.camera_info.stream_url)
            
            if not self.cap.isOpened():
                logger.error(f"[{self.camera_info.camera_id}] Cannot open stream")
                self.is_running = False
                return
            
            logger.success(f"[{self.camera_info.camera_id}] Stream opened")
            
            while self.is_running:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning(f"[{self.camera_info.camera_id}] Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                self.stats["total_frames"] += 1
                self.frame_count += 1
                
                # Chỉ detect trên một số frame
                if self.frame_count % self.frame_skip == 0:
                    self._detect_and_update(frame)
                    self.stats["processed_frames"] += 1
                
                # Vẽ boxes
                processed_frame = self._draw_boxes(frame, self.last_detections)
                
                # Vẽ thông tin camera và alerts lên frame
                processed_frame = self._draw_overlay(processed_frame)
                
                # Cập nhật frame
                with self.lock:
                    self.current_frame = processed_frame
                
                # Tính FPS
                self._update_fps()
        
        except Exception as e:
            logger.error(f"[{self.camera_info.camera_id}] Error: {e}")
        finally:
            if self.cap:
                self.cap.release()
    
    def _detect_and_update(self, frame):
        """Chạy detection và cập nhật alerts"""
        try:
            # YOLO detection
            results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = self.model.names[cls_id]
                    
                    if class_name == "natural":
                        continue
                    
                    detections.append((x1, y1, x2, y2, conf, class_name))
            
            self.last_detections = detections
            
            # Xử lý alerts
            alerts = self.alert_manager.process_detections(detections)
            if alerts:
                self.stats["total_alerts"] += len(alerts)
                # TODO: Phát âm thanh cảnh báo ở đây
        
        except Exception as e:
            logger.error(f"[{self.camera_info.camera_id}] Detection error: {e}")
    
    def _draw_boxes(self, frame, detections):
        """Vẽ bounding boxes"""
        annotated = frame.copy()
        
        for x1, y1, x2, y2, conf, class_name in detections:
            color = self._get_color_for_class(class_name)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"{class_name}: {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            cv2.rectangle(annotated, (x1, y1 - label_size[1] - 8), 
                         (x1 + label_size[0], y1), color, -1)
            
            text_color = (0, 0, 0) if class_name == "look_away" else (255, 255, 255)
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
        
        return annotated
    
    def _draw_overlay(self, frame):
        """Vẽ thông tin camera và alerts"""
        h, w = frame.shape[:2]
        
        # Background cho header
        cv2.rectangle(frame, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, 0), (w, 60), (255, 255, 255), 2)
        
        # Tên tài xế và camera - shorter text
        info_text = f"Cam: {self.camera_info.camera_id} | {self.camera_info.driver_name}"
        cv2.putText(frame, info_text, (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # FPS và stats
        stats_text = f"FPS: {self.stats['fps']:.1f} | Alerts: {self.stats['total_alerts']}"
        cv2.putText(frame, stats_text, (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Hiển thị alerts gần nhất - larger and cleaner
        recent_alerts = self.alert_manager.get_recent_alerts(3)
        if recent_alerts:
            y_offset = h - 60
            for i, alert in enumerate(reversed(recent_alerts)):
                # Background cho alert
                alert_bg_color = (0, 0, 200) if alert.priority == 1 else (0, 165, 255)
                cv2.rectangle(frame, (0, y_offset - 5), (w, y_offset + 30), alert_bg_color, -1)
                
                # Text alert - no emoji, larger font
                alert_text = alert.message
                cv2.putText(frame, alert_text, (15, y_offset + 18), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                y_offset -= 40
        
        return frame
    
    def _get_color_for_class(self, class_name):
        """Màu cho từng class"""
        color_map = {
            "sleepy_eye": (0, 0, 255),
            "yawn": (0, 140, 255),
            "look_away": (0, 255, 255),
            "phone": (255, 0, 255),
            "rub_eye": (60, 180, 255),
            "natural": (0, 255, 0),
        }
        return color_map.get(class_name, (255, 255, 255))
    
    def _update_fps(self):
        """Cập nhật FPS"""
        self.fps_frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.stats["fps"] = self.fps_frame_count / (current_time - self.last_fps_time)
            self.fps_frame_count = 0
            self.last_fps_time = current_time
    
    def get_current_frame(self):
        """Lấy frame hiện tại"""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
    
    def generate_frames(self):
        """Generator cho MJPEG stream"""
        while True:
            frame = self.get_current_frame()
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


class MultiCameraManager:
    """
    Quản lý nhiều camera streams
    """
    
    def __init__(self, model_path="./models/yolo_based/customized_yolo11s.pt"):
        """
        Khởi tạo Multi Camera Manager
        
        Args:
            model_path: Đường dẫn model YOLO
        """
        self.model_path = model_path
        self.cameras: Dict[str, SingleCameraProcessor] = {}
        self.lock = threading.Lock()
        logger.info("MultiCameraManager initialized")
    
    def add_camera(self, camera_info: CameraInfo) -> bool:
        """
        Thêm và bắt đầu một camera mới
        
        Args:
            camera_info: Thông tin camera
            
        Returns:
            True nếu thành công
        """
        with self.lock:
            try:
                if camera_info.camera_id in self.cameras:
                    logger.warning(f"Camera {camera_info.camera_id} already exists")
                    return False
                
                # Tạo processor mới
                processor = SingleCameraProcessor(camera_info, self.model_path)
                processor.start()
                
                self.cameras[camera_info.camera_id] = processor
                logger.success(f"Added camera {camera_info.camera_id}")
                return True
            
            except Exception as e:
                logger.error(f"Failed to add camera {camera_info.camera_id}: {e}")
                return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """
        Xóa một camera
        
        Args:
            camera_id: ID của camera
            
        Returns:
            True nếu thành công
        """
        with self.lock:
            if camera_id not in self.cameras:
                logger.warning(f"Camera {camera_id} not found")
                return False
            
            processor = self.cameras[camera_id]
            processor.stop()
            del self.cameras[camera_id]
            
            logger.info(f"Removed camera {camera_id}")
            return True
    
    def get_camera(self, camera_id: str) -> Optional[SingleCameraProcessor]:
        """
        Lấy processor của một camera
        
        Args:
            camera_id: ID của camera
            
        Returns:
            SingleCameraProcessor hoặc None
        """
        with self.lock:
            return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> List[CameraInfo]:
        """
        Lấy danh sách tất cả cameras
        
        Returns:
            List of CameraInfo
        """
        with self.lock:
            return [proc.camera_info for proc in self.cameras.values()]
    
    def stop_all(self):
        """Dừng tất cả cameras"""
        with self.lock:
            for processor in self.cameras.values():
                processor.stop()
            self.cameras.clear()
            logger.info("Stopped all cameras")
    
    def get_statistics(self) -> Dict:
        """
        Lấy thống kê của tất cả cameras
        
        Returns:
            Dict chứa thống kê
        """
        with self.lock:
            stats = {
                "total_cameras": len(self.cameras),
                "active_cameras": sum(1 for p in self.cameras.values() if p.is_running),
                "cameras": {}
            }
            
            for camera_id, processor in self.cameras.items():
                stats["cameras"][camera_id] = {
                    "driver_name": processor.camera_info.driver_name,
                    "is_active": processor.is_running,
                    "stats": processor.stats,
                    "recent_alerts": [
                        {
                            "message": alert.message,
                            "priority": alert.priority,
                            "class_name": alert.class_name
                        }
                        for alert in processor.alert_manager.get_recent_alerts(3)
                    ]
                }
            
            return stats


# Singleton instance
_multi_camera_manager = None


def get_multi_camera_manager() -> MultiCameraManager:
    """
    Lấy singleton instance của MultiCameraManager
    
    Returns:
        MultiCameraManager instance
    """
    global _multi_camera_manager
    if _multi_camera_manager is None:
        _multi_camera_manager = MultiCameraManager()
    return _multi_camera_manager
