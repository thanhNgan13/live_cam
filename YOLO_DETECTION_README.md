# YOLO Detection Integration

## 📋 Tổng quan

Module này tích hợp YOLO detection vào web admin để phát hiện hành vi lái xe nguy hiểm từ video stream.

## 🎯 Chức năng

- ✅ Load YOLO model (customized_yolo11s.pt)
- ✅ Đọc video stream từ URL camera
- ✅ Detect các hành vi: sleepy_eye, yawn, look_away, phone, rub_eye, natural
- ✅ Vẽ bounding boxes với màu sắc khác nhau cho mỗi loại
- ✅ Stream video đã được detect qua web

## 🚀 Cách sử dụng

### 1. Kiểm tra model YOLO

Model phải được đặt tại:
```
models/yolo_based/customized_yolo11s.pt
```

### 2. Khởi động server

```bash
python admin_app.py
```

Server sẽ chạy tại: http://localhost:5002

### 3. Truy cập trang test

Mở trình duyệt và truy cập:
```
http://localhost:5002/yolo-test
```

### 4. Sử dụng

1. **Chọn tài xế** từ dropdown list
2. **Nhấn "Bắt đầu Detection"** để:
   - Load YOLO model
   - Kết nối đến camera stream
   - Bắt đầu detect và hiển thị kết quả
3. **Xem video** với bounding boxes được vẽ tự động
4. **Nhấn "Dừng Detection"** để dừng processing

## 📡 API Endpoints

### Start Detection
```
POST /api/yolo/start/<driver_id>
```
Bắt đầu YOLO detection cho tài xế

**Response:**
```json
{
    "message": "Đã bắt đầu YOLO detection",
    "driver_id": 1,
    "stream_url": "http://..."
}
```

### Stop Detection
```
POST /api/yolo/stop
```
Dừng YOLO detection

**Response:**
```json
{
    "message": "Đã dừng YOLO detection"
}
```

### Video Stream
```
GET /api/yolo/stream
```
Stream video đã được detect (MJPEG format)

## 🎨 Màu sắc Bounding Boxes

- 🔴 **Đỏ**: `sleepy_eye`, `phone` (Nguy hiểm cao)
- 🟠 **Cam**: `yawn` (Nguy hiểm trung bình)
- 🟡 **Vàng**: `rub_eye` (Cảnh báo)
- 🔵 **Xanh cam nhạt**: `look_away` (Mất tập trung)
- 🟢 **Xanh lá**: `natural` (Bình thường)

## 🔧 Cấu hình

Trong file `yolo_processor.py`:

```python
self.conf_threshold = 0.5  # Ngưỡng confidence (0.0 - 1.0)
self.frame_skip = 2        # Bỏ qua frame để tăng FPS
```

### Điều chỉnh confidence threshold:
- Tăng lên (0.6, 0.7): Ít false positive, nhưng có thể miss một số detection
- Giảm xuống (0.3, 0.4): Nhiều detection hơn, nhưng có thể có false positive

### Điều chỉnh frame skip:
- Tăng lên (3, 4): FPS cao hơn, nhưng detect ít hơn
- Giảm xuống (1, 0): Detect mọi frame, FPS thấp hơn

## 📁 Cấu trúc Files

```
web_streaming/
├── yolo_processor.py          # Core YOLO processing logic
├── routes/
│   ├── api_routes.py          # API endpoints (đã thêm YOLO APIs)
│   └── admin_routes.py        # Web routes (đã thêm /yolo-test)
├── templates/
│   └── admin/
│       └── yolo_test.html     # Trang test YOLO detection
└── models/
    └── yolo_based/
        └── customized_yolo11s.pt  # YOLO model
```

## ⚙️ Technical Details

### YOLOStreamProcessor Class

**Methods:**
- `load_model()`: Load YOLO model từ file .pt
- `set_stream_url(url)`: Set URL của camera stream
- `start_processing()`: Bắt đầu xử lý video trong background thread
- `stop_processing()`: Dừng xử lý
- `get_current_frame()`: Lấy frame hiện tại đã được detect
- `generate_frames()`: Generator để stream qua HTTP (MJPEG)

**Threading:**
- Sử dụng threading để không block Flask server
- Lock để đồng bộ hóa việc truy cập frame
- Daemon thread tự động tắt khi app tắt

## 🐛 Troubleshooting

### Model không load được
```
ERROR: Failed to load YOLO model
```
**Giải pháp:** Kiểm tra đường dẫn model và đảm bảo file `.pt` tồn tại

### Stream không hiển thị
```
❌ Không thể kết nối đến video stream
```
**Giải pháp:** 
- Kiểm tra URL camera có đúng không
- Kiểm tra camera có đang chạy không
- Thử truy cập URL trực tiếp trong trình duyệt

### FPS thấp
**Giải pháp:**
- Tăng `frame_skip` trong `yolo_processor.py`
- Giảm resolution của camera
- Sử dụng GPU nếu có

### Memory leak
**Giải pháp:**
- Nhớ gọi `stop_processing()` khi không dùng
- Không mở nhiều stream cùng lúc

## 📝 TODO

- [ ] Thêm statistics (FPS, số lượng detection)
- [ ] Lưu video đã detect
- [ ] Gửi alert qua Telegram khi phát hiện nguy hiểm
- [ ] Support multiple streams cùng lúc
- [ ] Thêm confidence threshold control trong UI

## 🎓 Classes được detect

Model detect 6 classes:
1. **natural**: Lái xe bình thường
2. **sleepy_eye**: Mắt buồn ngủ
3. **yawn**: Ngáp
4. **look_away**: Nhìn hướng khác
5. **phone**: Sử dụng điện thoại
6. **rub_eye**: Dụi mắt

---

Tạo bởi: YOLO Detection Integration Module
