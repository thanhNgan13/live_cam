# YOLO Multi-Stream Detection Architecture

## 🎯 Tổng quan

Hệ thống hỗ trợ **multi-stream detection** - cho phép detect nhiều camera đồng thời mà không bị conflict.

## 🏗️ Kiến trúc

### Multi-Instance Pattern

```python
# yolo_processor.py
_processor_instances = {
    "http://localhost:5000/video_feed/0": YOLOStreamProcessor(),
    "http://localhost:5000/video_feed/1": YOLOStreamProcessor(),
    "http://localhost:5000/video_feed/2": YOLOStreamProcessor(),
}
```

**Mỗi stream_url có 1 processor riêng:**
- ✅ Không conflict giữa các stream
- ✅ Detect nhiều camera cùng lúc
- ✅ Auto cleanup khi stop
- ✅ Resource management tự động

## 📊 Luồng hoạt động

### Khi Client 1 bật detection:

```javascript
// Client 1: Driver A
POST /api/yolo/start
{
    "stream_url": "http://localhost:5000/video_feed/0"
}

→ Tạo YOLOStreamProcessor() cho stream 0
→ Start detection thread
→ Client 1 xem: GET /api/yolo/stream?stream_url=...video_feed/0
```

### Khi Client 2 bật detection (đồng thời):

```javascript
// Client 2: Driver B
POST /api/yolo/start
{
    "stream_url": "http://localhost:5000/video_feed/1"
}

→ Tạo YOLOStreamProcessor() MỚI cho stream 1
→ Start detection thread MỚI
→ Client 2 xem: GET /api/yolo/stream?stream_url=...video_feed/1
```

**Kết quả:** ✅ Cả 2 client đều xem stream riêng, không ảnh hưởng nhau!

## 🔧 API Changes

### 1. POST /api/yolo/start

**Request:**
```json
{
    "stream_url": "http://localhost:5000/video_feed/0"
}
```

**Response:**
```json
{
    "message": "Đã bắt đầu YOLO detection",
    "stream_url": "http://localhost:5000/video_feed/0"
}
```

**Behavior:**
- Tạo processor mới nếu stream_url chưa có
- Nếu đã tồn tại và đang chạy → trả về message thông báo
- Không ghi đè processor của stream khác

### 2. GET /api/yolo/stream

**Query Parameters:**
```
stream_url: URL của stream cần xem (required)
```

**Example:**
```
GET /api/yolo/stream?stream_url=http://localhost:5000/video_feed/0
```

**Response:** MJPEG stream với bounding boxes

### 3. POST /api/yolo/stop

**Request:**
```json
{
    "stream_url": "http://localhost:5000/video_feed/0"
}
```

**Response:**
```json
{
    "message": "Đã dừng YOLO detection",
    "stream_url": "http://localhost:5000/video_feed/0"
}
```

**Behavior:**
- Stop detection thread cho stream này
- Xóa processor khỏi dictionary
- Không ảnh hưởng đến stream khác

### 4. GET /api/yolo/active-streams (NEW)

**Response:**
```json
{
    "active_streams": [
        "http://localhost:5000/video_feed/0",
        "http://localhost:5000/video_feed/1"
    ],
    "count": 2
}
```

**Use case:** Kiểm tra xem stream nào đang được detect

## 💻 Frontend Integration

### Driver View Page

```javascript
// Start YOLO Detection
async function toggleYOLODetection() {
    const originalStreamUrl = '{{ driver.stream_url }}';
    
    // Start
    await fetch('/api/yolo/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stream_url: originalStreamUrl })
    });
    
    // Chuyển sang YOLO stream với stream_url parameter
    videoStream.src = `/api/yolo/stream?stream_url=${encodeURIComponent(originalStreamUrl)}&t=${Date.now()}`;
    
    // Stop
    await fetch('/api/yolo/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stream_url: originalStreamUrl })
    });
    
    // Quay về stream gốc
    videoStream.src = `${originalStreamUrl}?t=${Date.now()}`;
}
```

## 🔍 Code Structure

### yolo_processor.py

```python
# Multi-instance management
_processor_instances = {}

def get_processor(stream_url):
    """Lấy hoặc tạo processor cho stream_url"""
    if stream_url not in _processor_instances:
        processor = YOLOStreamProcessor()
        processor.set_stream_url(stream_url)
        _processor_instances[stream_url] = processor
    return _processor_instances[stream_url]

def remove_processor(stream_url):
    """Xóa processor khi stop"""
    if stream_url in _processor_instances:
        _processor_instances[stream_url].stop_processing()
        del _processor_instances[stream_url]

def get_active_streams():
    """Lấy danh sách stream đang active"""
    return [url for url, proc in _processor_instances.items() 
            if proc.is_running]
```

### api_routes.py

```python
@api_bp.route("/yolo/start", methods=["POST"])
def start_yolo_detection():
    stream_url = request.get_json().get("stream_url")
    
    # Mỗi stream có processor riêng
    processor = get_processor(stream_url)
    
    if processor.is_running:
        return jsonify({"message": "Stream đang được detect"})
    
    processor.start_processing()
    return jsonify({"message": "Đã bắt đầu YOLO detection"})

@api_bp.route("/yolo/stream")
def yolo_video_stream():
    stream_url = request.args.get("stream_url")
    
    # Lấy processor của stream cụ thể
    processor = get_processor(stream_url)
    
    return Response(processor.generate_frames(), 
                   mimetype="multipart/x-mixed-replace; boundary=frame")

@api_bp.route("/yolo/stop", methods=["POST"])
def stop_yolo_detection():
    stream_url = request.get_json().get("stream_url")
    
    # Xóa processor của stream này (không ảnh hưởng stream khác)
    remove_processor(stream_url)
    
    return jsonify({"message": "Đã dừng YOLO detection"})
```

## 📈 Performance Considerations

### Memory Management

**Mỗi processor chiếm:**
- YOLO model: ~20MB (shared across instances)
- Frame buffer: ~5MB per stream
- Thread overhead: ~1MB per stream

**Ví dụ:** 5 streams đồng thời:
- Memory: ~20MB + (5 × 6MB) = ~50MB
- CPU: 5 detection threads (có thể config `frame_skip` để giảm tải)

### Resource Cleanup

**Auto cleanup khi:**
1. Client gọi `/api/yolo/stop` → Remove processor ngay lập tức
2. Stream error → Thread tự dừng
3. Server restart → Clear tất cả instances

### Optimization Tips

```python
# Trong yolo_processor.py
class YOLOStreamProcessor:
    def __init__(self):
        self.frame_skip = 5  # ← Tăng nếu CPU yếu
        self.conf_threshold = 0.5  # ← Tăng để giảm detections
```

## 🧪 Testing Multi-Stream

### Test Case 1: 2 Streams Đồng Thời

```bash
# Terminal 1
curl -X POST http://localhost:5002/api/yolo/start \
  -H "Content-Type: application/json" \
  -d '{"stream_url": "http://localhost:5000/video_feed/0"}'

# Terminal 2
curl -X POST http://localhost:5002/api/yolo/start \
  -H "Content-Type: application/json" \
  -d '{"stream_url": "http://localhost:5000/video_feed/1"}'

# Check active streams
curl http://localhost:5002/api/yolo/active-streams

# Result:
{
  "active_streams": [
    "http://localhost:5000/video_feed/0",
    "http://localhost:5000/video_feed/1"
  ],
  "count": 2
}
```

### Test Case 2: Stop Một Stream

```bash
# Stop stream 0
curl -X POST http://localhost:5002/api/yolo/stop \
  -H "Content-Type: application/json" \
  -d '{"stream_url": "http://localhost:5000/video_feed/0"}'

# Check active streams
curl http://localhost:5002/api/yolo/active-streams

# Result: Stream 1 vẫn chạy
{
  "active_streams": [
    "http://localhost:5000/video_feed/1"
  ],
  "count": 1
}
```