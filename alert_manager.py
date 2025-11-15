"""
Alert Manager - Quản lý cảnh báo thông minh cho YOLO detection
Chức năng:
- Theo dõi các hành vi nguy hiểm theo thời gian
- Phát cảnh báo khi phát hiện vi phạm
- Hỗ trợ nhiều loại rule (duration-based, frequency-based)
"""

import time
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from loguru import logger
import threading


@dataclass
class DetectionEvent:
    """Sự kiện phát hiện một hành vi"""
    class_name: str
    timestamp: float
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)


@dataclass
class AlertRule:
    """Quy tắc cảnh báo cho một loại hành vi"""
    class_name: str
    alert_type: str  # 'duration' hoặc 'frequency'
    
    # Cho duration-based
    min_duration: float = 0.0  # Thời gian tối thiểu (giây)
    max_gap: float = 2.0  # Khoảng cách tối đa giữa 2 detection (giây)
    
    # Cho frequency-based
    max_count: int = 0  # Số lần tối đa
    time_window: float = 60.0  # Trong khoảng thời gian (giây)
    min_occurrence_duration: float = 0.0  # Thời gian tối thiểu cho mỗi lần (giây)
    
    # Cho custom_yawn (time windows đặc biệt)
    yawn_time_windows: List[Tuple[float, float]] = field(default_factory=list)  # [(start, end), ...]
    
    # Cấu hình chung
    cooldown: float = 10.0  # Thời gian chờ giữa 2 cảnh báo (giây)
    priority: int = 1  # Mức độ ưu tiên (1=cao, 3=thấp)
    message: str = ""  # Thông điệp cảnh báo


@dataclass
class Alert:
    """Cảnh báo được tạo ra"""
    rule_name: str
    class_name: str
    timestamp: float
    message: str
    priority: int
    metadata: Dict = field(default_factory=dict)


class BehaviorTracker:
    """Theo dõi một loại hành vi cụ thể"""
    
    def __init__(self, rule: AlertRule):
        self.rule = rule
        self.events = deque()  # Lưu các DetectionEvent
        self.last_alert_time = 0.0
        self.state = "idle"  # idle, tracking, alerting
        self.tracking_start_time = None
        
        # Cho frequency-based với min_occurrence_duration
        # Lưu danh sách các occurrences đã hoàn thành (timestamp_start, duration)
        self.valid_occurrences = deque()  # [(start_time, duration), ...]
        self.current_occurrence_start = None
        self.detection_gap_threshold = 0.5  # 0.5 giây gap = kết thúc occurrence
        
        # Cho custom_yawn (time windows đặc biệt)
        self.yawn_first_time = None  # Thời điểm ngáp lần đầu
        self.yawn_count = 0  # Số lần ngáp trong các time windows
        
    def add_detection(self, event: DetectionEvent) -> Optional[Alert]:
        """
        Thêm một detection event và kiểm tra có cần cảnh báo không
        
        Args:
            event: DetectionEvent
            
        Returns:
            Alert nếu cần cảnh báo, None nếu không
        """
        current_time = event.timestamp
        
        # Thêm event vào danh sách
        self.events.append(event)
        
        # Xóa các events cũ
        self._cleanup_old_events(current_time)
        
        # Kiểm tra cooldown
        if current_time - self.last_alert_time < self.rule.cooldown:
            return None
        
        # Kiểm tra theo loại rule
        if self.rule.alert_type == "duration":
            return self._check_duration_rule(current_time)
        elif self.rule.alert_type == "frequency":
            return self._check_frequency_rule_with_duration(current_time)
        elif self.rule.alert_type == "custom_yawn":
            return self._check_custom_yawn_rule(current_time)
        
        return None
    
    def _cleanup_old_events(self, current_time: float):
        """Xóa các events quá cũ"""
        if self.rule.alert_type == "duration":
            # Giữ events trong max_gap
            while self.events and current_time - self.events[0].timestamp > self.rule.max_gap * 2:
                self.events.popleft()
        else:
            # Giữ events trong time_window
            while self.events and current_time - self.events[0].timestamp > self.rule.time_window:
                self.events.popleft()
    
    def _check_duration_rule(self, current_time: float) -> Optional[Alert]:
        """
        Kiểm tra rule dựa trên thời gian liên tục
        
        Logic:
        - Nếu liên tục phát hiện (gap < max_gap) trong min_duration -> cảnh báo
        - Cho phép gián đoạn ngắn (natural) nhưng vẫn tính là liên tục
        """
        if len(self.events) < 2:
            return None
        
        # Tìm chuỗi detection liên tục
        continuous_start = None
        continuous_duration = 0.0
        
        for i in range(len(self.events) - 1):
            gap = self.events[i + 1].timestamp - self.events[i].timestamp
            
            if gap <= self.rule.max_gap:
                if continuous_start is None:
                    continuous_start = self.events[i].timestamp
                continuous_duration = self.events[i + 1].timestamp - continuous_start
            else:
                # Reset nếu gap quá lớn
                continuous_start = None
                continuous_duration = 0.0
        
        # Debug log
        if len(self.events) > 0:
            logger.debug(f"[{self.rule.class_name}] Events: {len(self.events)}, Duration: {continuous_duration:.2f}s, Required: {self.rule.min_duration}s")
        
        # Log chi tiết hơn cho look_away
        if self.rule.class_name == "look_away" and len(self.events) > 0:
            logger.info(f"[look_away] Checking... events={len(self.events)}, duration={continuous_duration:.2f}s (need {self.rule.min_duration}s)")
        
        # Kiểm tra có đủ duration không
        if continuous_duration >= self.rule.min_duration:
            self.last_alert_time = current_time
            logger.warning(f"🚨 [{self.rule.class_name}] ALERT! Duration: {continuous_duration:.2f}s")
            return Alert(
                rule_name=f"{self.rule.class_name}_duration",
                class_name=self.rule.class_name,
                timestamp=current_time,
                message=self.rule.message,
                priority=self.rule.priority,
                metadata={
                    "duration": round(continuous_duration, 2),
                    "start_time": continuous_start
                }
            )
        
        return None
    
    def _check_frequency_rule(self, current_time: float) -> Optional[Alert]:
        """
        Kiểm tra rule dựa trên tần suất (legacy - không dùng min_occurrence_duration)
        
        Logic:
        - Đếm số lần phát hiện trong time_window
        - Nếu >= max_count -> cảnh báo
        """
        # Đếm số events trong time_window
        count = 0
        for event in self.events:
            if current_time - event.timestamp <= self.rule.time_window:
                count += 1
        
        # Debug log
        logger.debug(f"[{self.rule.class_name}] Count: {count}/{self.rule.max_count} in {self.rule.time_window}s window")
        
        if count >= self.rule.max_count:
            self.last_alert_time = current_time
            logger.warning(f"🚨 [{self.rule.class_name}] ALERT! Count: {count}/{self.rule.max_count}")
            return Alert(
                rule_name=f"{self.rule.class_name}_frequency",
                class_name=self.rule.class_name,
                timestamp=current_time,
                message=self.rule.message,
                priority=self.rule.priority,
                metadata={
                    "count": count,
                    "time_window": self.rule.time_window
                }
            )
        
        return None
    
    def _check_frequency_rule_with_duration(self, current_time: float) -> Optional[Alert]:
        """
        Kiểm tra rule frequency với điều kiện mỗi occurrence phải kéo dài >= min_occurrence_duration
        
        Logic:
        - Tìm các occurrences (chuỗi detections liên tục)
        - Mỗi occurrence phải kéo dài >= min_occurrence_duration mới tính
        - Đếm số occurrences hợp lệ trong time_window
        - Nếu >= max_count -> cảnh báo
        
        Ví dụ với yawn:
        - Mỗi lần ngáp phải >= 1s
        - 3 lần ngáp trong 60s -> cảnh báo
        """
        if not self.events:
            return None
        
        # Xóa occurrences cũ khỏi time_window
        while self.valid_occurrences and current_time - self.valid_occurrences[0][0] > self.rule.time_window:
            self.valid_occurrences.popleft()
        
        # Tìm occurrences từ events
        # Nhóm các events liên tục (gap < detection_gap_threshold) thành 1 occurrence
        occurrences = []  # [(start_time, end_time, duration), ...]
        
        if len(self.events) > 0:
            current_occurrence_start = self.events[0].timestamp
            current_occurrence_end = self.events[0].timestamp
            
            for i in range(1, len(self.events)):
                gap = self.events[i].timestamp - self.events[i-1].timestamp
                
                if gap <= self.detection_gap_threshold:
                    # Vẫn trong cùng occurrence
                    current_occurrence_end = self.events[i].timestamp
                else:
                    # Kết thúc occurrence hiện tại
                    duration = current_occurrence_end - current_occurrence_start
                    if duration >= self.rule.min_occurrence_duration:
                        occurrences.append((current_occurrence_start, current_occurrence_end, duration))
                    
                    # Bắt đầu occurrence mới
                    current_occurrence_start = self.events[i].timestamp
                    current_occurrence_end = self.events[i].timestamp
            
            # Kiểm tra occurrence cuối (đang diễn ra)
            duration = current_occurrence_end - current_occurrence_start
            if duration >= self.rule.min_occurrence_duration:
                occurrences.append((current_occurrence_start, current_occurrence_end, duration))
        
        # Cập nhật valid_occurrences với occurrences mới (không trùng lặp)
        for occ_start, occ_end, occ_duration in occurrences:
            # Kiểm tra xem occurrence này đã được đếm chưa
            already_counted = False
            for valid_start, valid_duration in self.valid_occurrences:
                if abs(occ_start - valid_start) < 0.5:  # Cùng occurrence (trong 0.5s)
                    already_counted = True
                    break
            
            if not already_counted:
                self.valid_occurrences.append((occ_start, occ_duration))
        
        # Xóa lại occurrences cũ sau khi cập nhật
        while self.valid_occurrences and current_time - self.valid_occurrences[0][0] > self.rule.time_window:
            self.valid_occurrences.popleft()
        
        # Đếm số occurrences hợp lệ
        valid_count = len(self.valid_occurrences)
        
        # Debug log
        logger.info(f"[{self.rule.class_name}] Valid occurrences: {valid_count}/{self.rule.max_count} (min_duration={self.rule.min_occurrence_duration}s)")
        
        if valid_count >= self.rule.max_count:
            self.last_alert_time = current_time
            logger.warning(f"🚨 [{self.rule.class_name}] ALERT! {valid_count} occurrences (each >= {self.rule.min_occurrence_duration}s)")
            return Alert(
                rule_name=f"{self.rule.class_name}_frequency",
                class_name=self.rule.class_name,
                timestamp=current_time,
                message=self.rule.message,
                priority=self.rule.priority,
                metadata={
                    "count": valid_count,
                    "time_window": self.rule.time_window,
                    "min_occurrence_duration": self.rule.min_occurrence_duration
                }
            )
        
        return None
    
    def _check_custom_yawn_rule(self, current_time: float) -> Optional[Alert]:
        """
        Kiểm tra rule yawn với time windows đặc biệt
        
        Logic:
        - Lần đầu ngáp: start timer (yawn_first_time)
        - 0-10s: Bỏ qua (không tính)
        - 10-30s: Ngáp -> count = 1
        - 30-60s: Ngáp -> count = 2 -> ALERT!
        - >60s: Reset về 0
        
        Args:
            current_time: Thời gian hiện tại
            
        Returns:
            Alert nếu đạt điều kiện (count=2 trong 30-60s)
        """
        if not self.events:
            return None
        
        # Lấy detection mới nhất
        latest_event = self.events[-1]
        
        # Nếu chưa có yawn_first_time, set lần đầu
        if self.yawn_first_time is None:
            self.yawn_first_time = latest_event.timestamp
            self.yawn_count = 0
            logger.info(f"[Yawn] First yawn detected at {self.yawn_first_time:.2f}s")
            return None
        
        # Tính thời gian từ lần ngáp đầu tiên
        elapsed = current_time - self.yawn_first_time
        
        # Nếu > 60s: Reset
        if elapsed > 60.0:
            logger.info(f"[Yawn] Reset after {elapsed:.2f}s > 60s")
            self.yawn_first_time = latest_event.timestamp
            self.yawn_count = 0
            return None
        
        # 0-10s: Bỏ qua
        if elapsed < 10.0:
            logger.debug(f"[Yawn] In 0-10s window ({elapsed:.2f}s), ignoring...")
            return None
        
        # 10-30s: Tăng count lên 1 (chỉ tăng 1 lần)
        if 10.0 <= elapsed < 30.0:
            if self.yawn_count == 0:
                # Kiểm tra có phải detection mới không (tránh đếm nhiều lần)
                # Chỉ tăng count nếu event mới xuất hiện trong window này
                if abs(latest_event.timestamp - current_time) < 0.5:  # Detection trong 0.5s gần đây
                    self.yawn_count = 1
                    logger.info(f"[Yawn] Count = 1 at {elapsed:.2f}s (in 10-30s window)")
            return None
        
        # 30-60s: Tăng count lên 2 -> ALERT!
        if 30.0 <= elapsed <= 60.0:
            if self.yawn_count == 1:
                # Detection mới trong window 30-60s
                if abs(latest_event.timestamp - current_time) < 0.5:
                    self.yawn_count = 2
                    logger.warning(f"🚨 [Yawn] Count = 2 at {elapsed:.2f}s (in 30-60s window) -> ALERT!")
                    
                    # Reset để không trigger liên tục
                    self.last_alert_time = current_time
                    self.yawn_first_time = None
                    self.yawn_count = 0
                    
                    return Alert(
                        rule_name=f"{self.rule.class_name}_custom_yawn",
                        class_name=self.rule.class_name,
                        timestamp=current_time,
                        message=self.rule.message,
                        priority=self.rule.priority,
                        metadata={
                            "yawn_count": 2,
                            "elapsed_time": round(elapsed, 2)
                        }
                    )
        
        return None
    
    def reset(self):
        """Reset trạng thái"""
        self.events.clear()
        self.state = "idle"
        self.tracking_start_time = None


class AlertManager:
    """
    Quản lý cảnh báo cho toàn bộ hệ thống
    """
    
    # Định nghĩa các rules mặc định
    DEFAULT_RULES = [
        # Phone: Sử dụng điện thoại >= 1.5 giây
        AlertRule(
            class_name="phone",
            alert_type="duration",
            min_duration=1.5,
            max_gap=0.8,
            cooldown=10.0,
            priority=1,
            message="CANH BAO: Dang dung dien thoai!"
        ),
        
        # Yawn: Custom time windows
        # 0-10s: ignore, 10-30s: count=1, 30-60s: count=2->alert, >60s: reset
        AlertRule(
            class_name="yawn",
            alert_type="custom_yawn",
            cooldown=15.0,
            priority=2,
            message="CANH BAO: Ngap qua nhieu!"
        ),
        
        # Sleepy Eye: Mắt buồn ngủ liên tục >= 2.5 giây
        AlertRule(
            class_name="sleepy_eye",
            alert_type="duration",
            min_duration=2.5,
            max_gap=2.0,
            cooldown=10.0,
            priority=1,
            message="NGUY HIEM: Buon ngu!"
        ),
        
        # Look Away: Nhìn ra ngoài >= 1.5 giây
        AlertRule(
            class_name="look_away",
            alert_type="duration",
            min_duration=1.5,
            max_gap=0.8,
            cooldown=8.0,
            priority=2,
            message="CANH BAO: Mat tap trung!"
        ),
    ]
    
    def __init__(self, rules: List[AlertRule] = None):
        """
        Khởi tạo Alert Manager
        
        Args:
            rules: Danh sách rules, nếu None sẽ dùng DEFAULT_RULES
        """
        self.rules = rules if rules else self.DEFAULT_RULES
        self.trackers: Dict[str, BehaviorTracker] = {}
        self.alerts_history = deque(maxlen=100)  # Lưu 100 alerts gần nhất
        self.lock = threading.Lock()
        
        # Tạo trackers cho mỗi rule
        for rule in self.rules:
            self.trackers[rule.class_name] = BehaviorTracker(rule)
        
        logger.info(f"AlertManager initialized with {len(self.rules)} rules")
    
    def process_detections(self, detections: List[Tuple]) -> List[Alert]:
        """
        Xử lý danh sách detections và trả về các alerts
        
        Args:
            detections: List of (x1, y1, x2, y2, conf, class_name)
            
        Returns:
            List of Alerts
        """
        with self.lock:
            alerts = []
            current_time = time.time()
            
            # Tạo DetectionEvent cho mỗi detection
            for x1, y1, x2, y2, conf, class_name in detections:
                if class_name == "natural":
                    continue
                
                # Log look_away detections
                if class_name == "look_away":
                    logger.info(f"[look_away] Detection: conf={conf:.2f}")
                
                event = DetectionEvent(
                    class_name=class_name,
                    timestamp=current_time,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2)
                )
                
                # Gửi event đến tracker tương ứng
                if class_name in self.trackers:
                    alert = self.trackers[class_name].add_detection(event)
                    if alert:
                        alerts.append(alert)
                        self.alerts_history.append(alert)
                        logger.warning(f"🚨 ALERT: {alert.message}")
            
            return alerts
    
    def get_recent_alerts(self, count: int = 10) -> List[Alert]:
        """
        Lấy các alerts gần nhất
        
        Args:
            count: Số lượng alerts cần lấy
            
        Returns:
            List of Alerts
        """
        with self.lock:
            return list(self.alerts_history)[-count:]
    
    def reset_tracker(self, class_name: str):
        """Reset tracker cho một class"""
        with self.lock:
            if class_name in self.trackers:
                self.trackers[class_name].reset()
                logger.info(f"Reset tracker for {class_name}")
    
    def reset_all_trackers(self):
        """Reset tất cả trackers"""
        with self.lock:
            for tracker in self.trackers.values():
                tracker.reset()
            logger.info("Reset all trackers")
    
    def get_statistics(self) -> Dict:
        """
        Lấy thống kê về các alerts
        
        Returns:
            Dict chứa thống kê
        """
        with self.lock:
            stats = {
                "total_alerts": len(self.alerts_history),
                "alerts_by_class": defaultdict(int),
                "alerts_by_priority": defaultdict(int),
                "active_alerts": [],
                "recent_alerts": []
            }
            
            for alert in self.alerts_history:
                stats["alerts_by_class"][alert.class_name] += 1
                stats["alerts_by_priority"][alert.priority] += 1
            
            # Lấy 10 alerts gần nhất với format đầy đủ cho chat box
            for alert in list(self.alerts_history)[-10:]:
                alert_data = {
                    "behavior": alert.class_name,
                    "message": alert.message,
                    "timestamp": alert.timestamp,  # Unix timestamp
                    "priority": alert.priority,
                    "duration": alert.metadata.get("duration") if alert.metadata else None
                }
                stats["active_alerts"].append(alert_data)
            
            # Giữ lại recent_alerts với format cũ cho backward compatibility
            for alert in list(self.alerts_history)[-5:]:
                stats["recent_alerts"].append({
                    "class_name": alert.class_name,
                    "message": alert.message,
                    "timestamp": datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S"),
                    "priority": alert.priority,
                    "metadata": alert.metadata
                })
            
            return stats


# Singleton instance
_alert_manager_instance = None


def get_alert_manager() -> AlertManager:
    """
    Lấy singleton instance của AlertManager
    
    Returns:
        AlertManager instance
    """
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
    return _alert_manager_instance
