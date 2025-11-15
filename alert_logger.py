"""
Alert Logger - Lưu log alerts và evidence (video/ảnh)
"""

import os
import json
import cv2
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque
from loguru import logger


class AlertLogger:
    """Quản lý việc lưu log alerts và evidence"""
    
    def __init__(self, 
                 log_dir: str = "alert_logs",
                 evidence_dir: str = "alert_evidence",
                 video_duration: float = 5.0,
                 fps: int = 10):
        """
        Khởi tạo Alert Logger
        
        Args:
            log_dir: Thư mục lưu log JSON
            evidence_dir: Thư mục lưu video/ảnh evidence
            video_duration: Thời gian video clip (giây)
            fps: Frame rate cho video
        """
        self.log_dir = Path(log_dir)
        self.evidence_dir = Path(evidence_dir)
        self.video_duration = video_duration
        self.fps = fps
        
        # Tạo thư mục nếu chưa có
        self.log_dir.mkdir(exist_ok=True)
        self.evidence_dir.mkdir(exist_ok=True)
        
        # Buffer để lưu frames với timestamp (cho pre-event recording)
        # Lưu tuple: (timestamp, frame)
        max_buffer_frames = int(fps * video_duration * 2)  # x2 để đủ frames trước và sau
        self.frame_buffer = deque(maxlen=max_buffer_frames)
        self.buffer_lock = threading.Lock()
        
        # Video writer hiện tại
        self.current_writer = None
        self.recording_until = 0.0
        self.writer_lock = threading.Lock()
        
        logger.info(f"AlertLogger initialized - log_dir: {log_dir}, evidence_dir: {evidence_dir}")
    
    def add_frame_to_buffer(self, frame, timestamp=None):
        """
        Thêm frame vào buffer với timestamp (gọi liên tục từ video stream)
        
        Args:
            frame: Frame từ camera
            timestamp: Unix timestamp của frame (nếu None sẽ dùng time.time())
        """
        import time as time_module
        with self.buffer_lock:
            # Chỉ lưu frame nếu có kích thước hợp lệ
            if frame is not None and frame.size > 0:
                ts = timestamp if timestamp is not None else time_module.time()
                self.frame_buffer.append((ts, frame.copy()))
    
    def log_alert(self, 
                  alert_data: Dict,
                  driver_id: str = None,
                  save_evidence: bool = True) -> str:
        """
        Lưu log alert vào file JSON và tạo evidence
        
        Args:
            alert_data: Thông tin alert (behavior, message, timestamp, priority, etc.)
            driver_id: ID tài xế (optional)
            save_evidence: Có lưu video/ảnh không
            
        Returns:
            Path đến file evidence (nếu có)
        """
        try:
            # Tạo timestamp string
            dt = datetime.fromtimestamp(alert_data['timestamp'])
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H-%M-%S")
            
            # Tạo log entry
            log_entry = {
                "alert_id": f"{alert_data['behavior']}_{int(alert_data['timestamp'])}",
                "timestamp": alert_data['timestamp'],
                "datetime": dt.isoformat(),
                "behavior": alert_data['behavior'],
                "message": alert_data['message'],
                "priority": alert_data['priority'],
                "duration": alert_data.get('duration'),
                "driver_id": driver_id,
                "evidence_file": None
            }
            
            # Lưu evidence nếu cần
            evidence_path = None
            if save_evidence:
                evidence_path = self._save_evidence(
                    behavior=alert_data['behavior'],
                    timestamp=alert_data['timestamp'],
                    duration=alert_data.get('duration', 0),
                    date_str=date_str,
                    time_str=time_str
                )
                if evidence_path:
                    log_entry["evidence_file"] = str(evidence_path)
            
            # Lưu vào file JSON (theo ngày)
            log_file = self.log_dir / f"alerts_{date_str}.json"
            self._append_to_json_log(log_file, log_entry)
            
            logger.info(f"Alert logged: {log_entry['alert_id']}, evidence: {evidence_path}")
            return evidence_path
            
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
            return None
    
    def _save_evidence(self, 
                       behavior: str,
                       timestamp: float,
                       duration: float,
                       date_str: str,
                       time_str: str) -> Optional[Path]:
        """
        Lưu evidence (video hoặc ảnh) - extract frames theo timing của alert
        
        Args:
            behavior: Loại hành vi
            timestamp: Unix timestamp của alert
            duration: Thời gian kéo dài của lỗi (cho duration-based)
            date_str: String ngày (YYYY-MM-DD)
            time_str: String giờ (HH-MM-SS)
            
        Returns:
            Path đến file evidence
        """
        try:
            with self.buffer_lock:
                frame_buffer_copy = list(self.frame_buffer)
            
            if not frame_buffer_copy:
                logger.warning("No frames in buffer to save evidence")
                return None
            
            # Extract frames theo timing của alert
            # Lấy frames từ (timestamp - 2s) đến (timestamp + 1s) để capture đủ context
            alert_time = timestamp
            start_time = alert_time - 2.0  # 2s trước alert
            end_time = alert_time + 1.0    # 1s sau alert
            
            # Nếu có duration (duration-based alert), extend end_time
            if duration and duration > 0:
                end_time = alert_time + min(duration * 0.5, 2.0)  # Thêm 50% duration hoặc tối đa 2s
            
            # Filter frames trong khoảng thời gian
            relevant_frames = [
                frame for ts, frame in frame_buffer_copy 
                if start_time <= ts <= end_time
            ]
            
            if not relevant_frames:
                logger.warning(f"No frames found in time range [{start_time:.2f}, {end_time:.2f}]")
                # Fallback: lấy frames cuối buffer
                relevant_frames = [frame for _, frame in frame_buffer_copy[-30:]]
            
            logger.info(f"Extracted {len(relevant_frames)} frames for alert at {alert_time:.2f}s (range: {start_time:.2f}-{end_time:.2f})")
            
            # Tạo thư mục theo ngày
            daily_dir = self.evidence_dir / date_str
            daily_dir.mkdir(exist_ok=True)
            
            # Quyết định lưu video hay ảnh
            # Với duration-based (phone, sleepy_eye, look_away, yawn): lưu video
            # Với ảnh đơn lẻ: lưu ảnh
            if behavior in ['phone', 'sleepy_eye', 'look_away', 'yawn']:
                # Lưu video clip
                video_path = daily_dir / f"{behavior}_{time_str}.mp4"
                return self._save_video_clip(relevant_frames, video_path)
            else:
                # Lưu ảnh (lấy frame cuối)
                image_path = daily_dir / f"{behavior}_{time_str}.jpg"
                return self._save_image(relevant_frames[-1], image_path)
                
        except Exception as e:
            logger.error(f"Error saving evidence: {e}")
            return None
    
    def _save_video_clip(self, frames: List, output_path: Path) -> Optional[Path]:
        """
        Lưu video clip từ frames
        
        Args:
            frames: Danh sách frames
            output_path: Đường dẫn output
            
        Returns:
            Path đến video file
        """
        try:
            if not frames:
                return None
            
            # Lấy kích thước frame
            h, w = frames[0].shape[:2]
            
            # Tạo VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(output_path), fourcc, self.fps, (w, h))
            
            # Ghi tất cả frames
            for frame in frames:
                writer.write(frame)
            
            writer.release()
            
            # Kiểm tra file có tạo thành công không
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Video saved: {output_path}, {len(frames)} frames")
                return output_path
            else:
                logger.error(f"Video file not created: {output_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error saving video clip: {e}")
            return None
    
    def _save_image(self, frame, output_path: Path) -> Optional[Path]:
        """
        Lưu ảnh từ frame
        
        Args:
            frame: Frame cần lưu
            output_path: Đường dẫn output
            
        Returns:
            Path đến image file
        """
        try:
            success = cv2.imwrite(str(output_path), frame)
            if success:
                logger.info(f"Image saved: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to save image: {output_path}")
                return None
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return None
    
    def _append_to_json_log(self, log_file: Path, log_entry: Dict):
        """
        Thêm log entry vào file JSON
        
        Args:
            log_file: Đường dẫn file JSON
            log_entry: Entry cần thêm
        """
        try:
            # Đọc file hiện tại
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Thêm entry mới
            logs.append(log_entry)
            
            # Ghi lại file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error appending to JSON log: {e}")
    
    def get_logs_by_date(self, date_str: str) -> List[Dict]:
        """
        Lấy logs theo ngày
        
        Args:
            date_str: String ngày (YYYY-MM-DD)
            
        Returns:
            List các log entries
        """
        try:
            log_file = self.log_dir / f"alerts_{date_str}.json"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
    
    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """
        Lấy tất cả logs (gần nhất)
        
        Args:
            limit: Số lượng logs tối đa
            
        Returns:
            List các log entries
        """
        try:
            all_logs = []
            log_files = sorted(self.log_dir.glob("alerts_*.json"), reverse=True)
            
            for log_file in log_files:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    all_logs.extend(logs)
                    
                if len(all_logs) >= limit:
                    break
            
            # Sắp xếp theo timestamp giảm dần và giới hạn
            all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return all_logs[:limit]
            
        except Exception as e:
            logger.error(f"Error reading all logs: {e}")
            return []


# Singleton instance
_alert_logger_instance = None
_logger_lock = threading.Lock()


def get_alert_logger() -> AlertLogger:
    """
    Lấy singleton instance của AlertLogger
    
    Returns:
        AlertLogger instance
    """
    global _alert_logger_instance
    if _alert_logger_instance is None:
        with _logger_lock:
            if _alert_logger_instance is None:
                _alert_logger_instance = AlertLogger()
    return _alert_logger_instance
