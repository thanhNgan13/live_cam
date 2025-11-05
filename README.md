# Camera Streaming Server 🎥

Hệ thống streaming camera qua web với face detection tích hợp.

## 📦 Cài đặt

```powershell
# Cài đặt các package cần thiết
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## 🚀 Chạy Server

```powershell
# Khởi động server
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_stream_server.py
```

Server sẽ chạy tại: `http://localhost:5000`

## 🌐 Các đường dẫn (Routes)

### Trang web:

- **Trang chủ**: `http://localhost:5000/`
  - Hiển thị tất cả camera với preview
- **Xem camera**: `http://localhost:5000/camera-{n}`
  - Ví dụ: `http://localhost:5000/camera-1`
  - Xem camera số 1
- **Xem camera + Face Detection**: `http://localhost:5000/camera-{n}?detect=true`
  - Ví dụ: `http://localhost:5000/camera-1?detect=true`
  - Xem camera số 1 với face detection

### API Endpoints:

- **Danh sách camera**: `http://localhost:5000/cameras`
  - Trả về JSON danh sách camera
- **Video stream**: `http://localhost:5000/video_feed/{n}`
  - Ví dụ: `http://localhost:5000/video_feed/1`
  - Stream video từ camera số 1
- **Video stream + Face Detection**: `http://localhost:5000/video_feed/{n}?detect=true`
  - Ví dụ: `http://localhost:5000/video_feed/1?detect=true`
  - Stream video với face detection

## 🧪 Test Client

Để test và xem stream từ một chương trình Python khác:

```powershell
# Xem stream camera 1
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_client.py http://localhost:5000/video_feed/1

# Xem stream camera 1 với face detection
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_client.py http://localhost:5000/video_feed/1?detect=true
```

## 📝 Tính năng

✅ **Multi-camera support**: Hỗ trợ nhiều camera cùng lúc
✅ **Live streaming**: Stream video realtime qua HTTP
✅ **Face detection**: Phát hiện và khoanh vùng khuôn mặt
✅ **Multi-viewer**: Nhiều người xem cùng lúc
✅ **Responsive UI**: Giao diện web đẹp, responsive
✅ **Thread-safe**: Xử lý an toàn với nhiều request đồng thời

## 🎯 Cách sử dụng trong ứng dụng khác

### 1. Trong HTML:

```html
<!-- Xem camera 1 -->
<img src="http://localhost:5000/video_feed/1" alt="Camera 1" />

<!-- Xem camera 1 với face detection -->
<img
  src="http://localhost:5000/video_feed/1?detect=true"
  alt="Camera 1 with Face Detection"
/>
```

### 2. Trong Python:

```python
import cv2
import requests
import numpy as np

# Lấy stream
stream = requests.get('http://localhost:5000/video_feed/1?detect=true', stream=True)

bytes_data = bytes()
for chunk in stream.iter_content(chunk_size=1024):
    bytes_data += chunk
    a = bytes_data.find(b'\xff\xd8')
    b = bytes_data.find(b'\xff\xd9')

    if a != -1 and b != -1:
        jpg = bytes_data[a:b+2]
        bytes_data = bytes_data[b+2:]
        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('Camera', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
```

### 3. Trong JavaScript:

```javascript
// Xem stream trong <img> tag
document.getElementById("camera").src =
  "http://localhost:5000/video_feed/1?detect=true";
```

## 🛠️ Cấu trúc files

```
live_cam/
├── camera_viewer.py          # Xem camera trực tiếp (desktop app)
├── camera_stream_server.py   # Web server streaming
├── camera_client.py          # Client test để xem stream
├── requirements.txt          # Dependencies
└── README.md                # Tài liệu này
```

## ⚙️ Tùy chỉnh

### Thay đổi port:

Sửa trong `camera_stream_server.py`:

```python
app.run(host='0.0.0.0', port=8080)  # Đổi từ 5000 sang 8080
```

### Thay đổi độ phân giải:

Sửa trong `init_cameras()`:

```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # Tăng từ 640
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   # Tăng từ 480
```

### Thay đổi chất lượng JPEG:

Sửa trong `generate_frames()`:

```python
cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])  # Tăng từ 85
```

## 🔒 Lưu ý bảo mật

⚠️ Server này chỉ nên dùng trong mạng nội bộ (LAN)
⚠️ Không expose ra Internet mà không có authentication
⚠️ Để production, nên thêm SSL/TLS và authentication

## 📞 Truy cập từ thiết bị khác

Từ máy khác trong cùng mạng LAN:

```
http://<IP_CỦA_MÁY_SERVER>:5000/
```

Ví dụ: `http://192.168.1.100:5000/`
