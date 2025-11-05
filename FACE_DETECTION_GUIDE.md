# 🎯 Face Detection Client - Hướng dẫn sử dụng

Chương trình Python độc lập để nhận video stream và hiển thị face detection trên Windows.

## 📋 Mô tả

Chương trình này:

- ✅ Nhận đầu vào là URL của video stream
- ✅ Phát hiện khuôn mặt realtime bằng Haar Cascade
- ✅ Hiển thị box màu xanh quanh khuôn mặt
- ✅ Hiển thị thống kê (FPS, số khuôn mặt)
- ✅ Hỗ trợ chụp ảnh màn hình
- ✅ Xử lý đa luồng để stream mượt mà

## 🚀 Cách sử dụng

### 1. Khởi động server (Terminal 1)

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_stream_server.py
```

### 2. Chạy face detection client (Terminal 2)

**Cách 1: Sử dụng URL mặc định**

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py
```

**Cách 2: Chỉ định URL stream**

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://localhost:5000/video_feed/0
```

**Cách 3: Stream từ camera khác**

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://localhost:5000/video_feed/1
```

**Cách 4: Stream từ máy khác trong mạng**

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://192.168.1.100:5000/video_feed/0
```

**Cách 5: Tùy chỉnh tên cửa sổ**

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://localhost:5000/video_feed/0 -w "Camera Phòng Khách"
```

## ⌨️ Phím tắt

Khi chương trình đang chạy:

- **`q`** hoặc **`ESC`** - Thoát chương trình
- **`s`** - Chụp ảnh màn hình (lưu vào thư mục hiện tại)

## 📊 Thông tin hiển thị

Trên màn hình sẽ hiển thị:

1. **Faces Detected: X** - Số khuôn mặt phát hiện được (màu xanh nếu > 0)
2. **FPS: XX.X** - Tốc độ khung hình (frames per second)
3. **Stream: URL** - Đường dẫn stream đang xem
4. **Box màu xanh** - Khoanh vùng khuôn mặt
5. **Điểm đỏ** - Tâm của khuôn mặt
6. **Text "Face"** - Nhãn cho mỗi khuôn mặt

## 🎯 Ví dụ thực tế

### Ví dụ 1: Xem camera cục bộ với face detection

```powershell
# Terminal 1: Khởi động server
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_stream_server.py

# Terminal 2: Xem với face detection
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py
```

### Ví dụ 2: Xem nhiều camera cùng lúc

```powershell
# Terminal 1: Server
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_stream_server.py

# Terminal 2: Camera 0
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://localhost:5000/video_feed/0 -w "Camera 0"

# Terminal 3: Camera 1
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://localhost:5000/video_feed/1 -w "Camera 1"
```

### Ví dụ 3: Xem từ máy khác trong mạng

```powershell
# Trên máy client (không cần server)
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://192.168.1.23:5000/video_feed/0
```

## 🔧 Tùy chỉnh

### Thay đổi độ nhạy face detection

Sửa trong file `face_detection_client.py`:

```python
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,      # Giảm để detect nhiều hơn (1.05 - 1.3)
    minNeighbors=5,       # Giảm để detect nhiều hơn (3 - 10)
    minSize=(30, 30),     # Kích thước khuôn mặt tối thiểu
)
```

### Thay đổi màu box

```python
cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#                                         ^^^^^^^^^
#                                         (B, G, R)
# Ví dụ:
# (0, 255, 0)   -> Xanh lá
# (255, 0, 0)   -> Xanh dương
# (0, 0, 255)   -> Đỏ
# (255, 255, 0) -> Cyan
```

### Thay đổi độ dày box

```python
cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#                                                     ^
#                                                     độ dày (pixels)
```

## 📸 Screenshots

Khi nhấn phím `s`, ảnh sẽ được lưu với tên:

```
screenshot_1_1699180234.jpg
screenshot_2_1699180235.jpg
...
```

Format: `screenshot_{số thứ tự}_{timestamp}.jpg`

## 🐛 Xử lý lỗi

### Lỗi: "Không thể kết nối"

- Kiểm tra server đã chạy chưa
- Kiểm tra URL có đúng không
- Kiểm tra firewall/antivirus

### Lỗi: "Không thể lấy frame"

- Stream có thể bị gián đoạn
- Kiểm tra kết nối mạng
- Thử khởi động lại server

### FPS thấp

- Giảm độ phân giải camera trong server
- Đóng các ứng dụng nặng khác
- Kiểm tra CPU usage

## 📦 Dependencies

```
opencv-python  # Xử lý video và face detection
numpy         # Xử lý mảng
requests      # HTTP client
```

## 💡 Tips

1. **Ánh sáng tốt** = Face detection tốt hơn
2. **Khuôn mặt thẳng** được detect dễ hơn khuôn mặt nghiêng
3. **Khoảng cách 0.5-2m** từ camera là tốt nhất
4. Có thể chạy **nhiều client** cùng lúc với 1 server
5. Stream URL có thể là từ **bất kỳ nguồn nào** (không chỉ server của chúng ta)

## 🎓 Học thêm

Để cải thiện face detection:

- Thử dùng **DNN face detector** (chính xác hơn)
- Thử dùng **MTCNN** (detect góc nghiêng tốt hơn)
- Thử dùng **face_recognition** library (có thể nhận diện người)

## 🔗 Tích hợp

Chương trình này có thể nhận stream từ:

- ✅ Server Flask của chúng ta
- ✅ IP Camera (MJPEG stream)
- ✅ RTSP stream
- ✅ Bất kỳ HTTP video stream nào

Chỉ cần đường dẫn trả về MJPEG format!
