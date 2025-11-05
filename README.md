# 🎥 Camera Streaming & Face Detection System

Hệ thống streaming camera qua web với face detection tích hợp, hỗ trợ tự động bypass ngrok warning page.

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Cài đặt](#-cài-đặt)
- [Sử dụng](#-sử-dụng)
- [Cấu trúc Project](#-cấu-trúc-project)
- [Troubleshooting](#-troubleshooting)

## ✨ Tính năng

### 🖥️ Camera Streaming Server
- ✅ Stream nhiều camera cùng lúc qua HTTP
- ✅ Web interface đẹp, responsive
- ✅ API endpoints để tích hợp
- ✅ Face detection tích hợp sẵn trên server
- ✅ Hỗ trợ nhiều người xem đồng thời

### 🎯 Face Detection Client  
- ✅ Nhận video stream từ bất kỳ URL nào
- ✅ **Tự động bypass ngrok warning page**
- ✅ Face detection realtime với OpenCV
- ✅ Hiển thị thống kê (FPS, số khuôn mặt)
- ✅ Chụp ảnh màn hình
- ✅ Session management thông minh

### 🌐 Public Streaming
- ✅ Hỗ trợ ngrok, dev tunnels, cloudflare
- ✅ Hoặc sử dụng trong mạng LAN

## 🚀 Cài đặt

### 1. Clone project

```powershell
cd D:\DUT_ITF\Semester_9th\IoT\live_cam
```

### 2. Cài đặt dependencies

```powershell
# Kích hoạt virtual environment
.venv\Scripts\Activate.ps1

# Cài đặt packages
pip install -r requirements.txt
```

### 3. Dependencies chính

- `opencv-python` - Xử lý video và face detection
- `flask` - Web server
- `requests` - HTTP client
- `beautifulsoup4` - Parse HTML (bypass ngrok warning)
- `numpy` - Xử lý mảng

## 📖 Sử dụng

### 🎬 Scenario 1: Sử dụng Local (trong cùng máy)

**Terminal 1: Khởi động server**
```powershell
.venv\Scripts\python.exe camera_stream_server.py
```

**Terminal 2: Xem với face detection**
```powershell
# Cách 1: Dùng client v2 (khuyên dùng - có auto bypass)
.venv\Scripts\python.exe face_detection_client_v2.py http://localhost:5000/video_feed/0

# Cách 2: Xem trực tiếp trên desktop
.venv\Scripts\python.exe camera_viewer.py
```

**Hoặc mở browser:**
- Trang chủ: http://localhost:5000/
- Camera 0: http://localhost:5000/camera-0
- Camera với face detection: http://localhost:5000/camera-0?detect=true

---

### 🌐 Scenario 2: Public qua Internet (ngrok)

**Terminal 1: Khởi động server**
```powershell
.venv\Scripts\python.exe camera_stream_server.py
```

**Terminal 2: Khởi động ngrok**
```powershell
ngrok http 5000
```

Copy URL ngrok (ví dụ: `https://xxxx.ngrok-free.app`)

**Terminal 3: Xem từ bất kỳ đâu**
```powershell
# Tự động bypass ngrok warning page!
.venv\Scripts\python.exe face_detection_client_v2.py https://xxxx.ngrok-free.app/video_feed/0
```

---

### 🏠 Scenario 3: Trong mạng LAN

**Bước 1: Lấy IP máy server**
```powershell
ipconfig
# Tìm IPv4 Address, ví dụ: 192.168.1.100
```

**Bước 2: Khởi động server**
```powershell
.venv\Scripts\python.exe camera_stream_server.py
```

**Bước 3: Từ máy khác trong mạng**
```powershell
# Hoặc mở browser
http://192.168.1.100:5000/

# Hoặc dùng face detection client
python face_detection_client_v2.py http://192.168.1.100:5000/video_feed/0
```

## 📁 Cấu trúc Project

```
live_cam/
├── 📄 camera_stream_server.py      # Web server streaming camera
├── 📄 face_detection_client_v2.py  # Client với auto bypass ngrok (KHUYÊN DÙNG)
├── 📄 camera_viewer.py             # Xem camera trực tiếp trên desktop
├── 📄 debug_stream.py              # Tool debug stream format
├── 📄 requirements.txt             # Dependencies
└── 📖 README.md                    # Tài liệu này
```

### Chi tiết các file

| File | Mục đích | Khi nào dùng |
|------|----------|--------------|
| `camera_stream_server.py` | Web server stream camera | Luôn cần chạy để có stream |
| `face_detection_client_v2.py` | Client xem stream + face detection | **Khuyên dùng** - Tự động bypass ngrok |
| `camera_viewer.py` | Xem camera desktop (không qua web) | Xem nhanh camera local |
| `debug_stream.py` | Debug format của stream | Khi stream bị lỗi, cần kiểm tra |

## ⌨️ Phím tắt

### Face Detection Client:
- **`q`** hoặc **`ESC`** - Thoát
- **`s`** - Chụp ảnh màn hình

### Camera Viewer:
- **`q`** hoặc **`ESC`** - Thoát

## 🔧 API Endpoints

| Endpoint | Mô tả | Ví dụ |
|----------|-------|-------|
| `GET /` | Trang chủ | http://localhost:5000/ |
| `GET /cameras` | API danh sách camera (JSON) | http://localhost:5000/cameras |
| `GET /camera-{n}` | Trang xem camera n | http://localhost:5000/camera-0 |
| `GET /camera-{n}?detect=true` | Xem camera n + face detection | http://localhost:5000/camera-0?detect=true |
| `GET /video_feed/{n}` | Stream video từ camera n | http://localhost:5000/video_feed/0 |
| `GET /video_feed/{n}?detect=true` | Stream + face detection | http://localhost:5000/video_feed/0?detect=true |

## 🛠️ Troubleshooting

### Lỗi: "Không tìm thấy camera"
```powershell
# Chạy để test camera
.venv\Scripts\python.exe camera_viewer.py
```
- Kiểm tra camera đã kết nối chưa
- Kiểm tra camera có bị app khác dùng không
- Thử rút và cắm lại camera

### Lỗi: "Import cv2 not found"
```powershell
# Cài lại opencv
pip install opencv-python --force-reinstall
```

### Lỗi: ngrok trả về HTML
```powershell
# Dùng client v2 (tự động bypass)
.venv\Scripts\python.exe face_detection_client_v2.py <NGROK_URL>

# Hoặc debug
.venv\Scripts\python.exe debug_stream.py <NGROK_URL>
```

### Lỗi: Connection refused
- Kiểm tra server đã chạy chưa
- Kiểm tra port 5000 có bị chiếm không: `netstat -ano | findstr :5000`
- Kiểm tra firewall

### FPS thấp
- Giảm resolution trong `camera_stream_server.py`:
  ```python
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Giảm từ 640
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240) # Giảm từ 480
  ```

## 🎓 Tùy chỉnh

### Thay đổi port server
Trong `camera_stream_server.py`:
```python
app.run(host='0.0.0.0', port=8080)  # Đổi từ 5000 sang 8080
```

### Thay đổi độ nhạy face detection
Trong `face_detection_client_v2.py`:
```python
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,    # Giảm để detect nhiều hơn (1.05-1.3)
    minNeighbors=5,     # Giảm để detect nhiều hơn (3-10)
    minSize=(30, 30),   # Kích thước tối thiểu
)
```

### Thay đổi màu box face detection
```python
cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#                                         ^^^^^^^^^^
#                                         (B, G, R)
# Màu khác:
# (255, 0, 0)   -> Xanh dương
# (0, 0, 255)   -> Đỏ
# (255, 255, 0) -> Cyan
```

## 📦 Public Streaming Options

### 1. ngrok (Khuyên dùng cho testing)
```powershell
ngrok http 5000
```
- ✅ Miễn phí, dễ dùng
- ✅ Client v2 tự động bypass warning
- ❌ URL đổi mỗi lần restart (free)

### 2. CloudFlare Tunnel (Cho production)
```powershell
cloudflared tunnel --url http://localhost:5000
```
- ✅ Ổn định, nhanh
- ✅ URL cố định
- ❌ Cần setup account

### 3. LAN (Trong mạng nội bộ)
```powershell
# Không cần tool, dùng IP trực tiếp
http://192.168.1.X:5000
```
- ✅ Nhanh nhất
- ✅ Không cần internet
- ❌ Chỉ trong mạng

## 🎯 Quick Start

**Cách nhanh nhất để bắt đầu:**

```powershell
# 1. Khởi động server
.venv\Scripts\python.exe camera_stream_server.py

# 2. Mở browser
start http://localhost:5000

# 3. Hoặc dùng face detection client
.venv\Scripts\python.exe face_detection_client_v2.py http://localhost:5000/video_feed/0
```

## 📝 Requirements

- Python 3.11+
- Windows 10/11 (hoặc Linux/Mac với điều chỉnh nhỏ)
- Webcam/USB Camera
- 4GB RAM (khuyên dùng)

## 🤝 Credits

- OpenCV - Computer vision library
- Flask - Web framework
- ngrok - Tunneling service
- BeautifulSoup - HTML parser

## 📄 License

MIT License - Tự do sử dụng cho mục đích học tập và thương mại.

---

**Made with ❤️ for IoT Course - DUT**
