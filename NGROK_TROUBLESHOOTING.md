# 🎯 Hướng dẫn khắc phục ngrok trả về HTML

## ❌ Vấn đề

Ngrok trả về HTML thay vì video stream vì:

1. Server chưa chạy khi ngrok khởi động
2. Ngrok free có warning page
3. Ngrok forward sai port

## ✅ Giải pháp - Làm theo thứ tự

### Bước 1: Dừng tất cả

```powershell
# Dừng server và ngrok cũ
# Nhấn Ctrl+C trong terminal của server
# Nhấn Ctrl+C trong terminal của ngrok
```

### Bước 2: Khởi động lại đúng thứ tự

**Terminal 1: Khởi động Camera Server**

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_stream_server.py
```

Đợi đến khi thấy:

```
✅ Server sẵn sàng với X camera
 * Running on http://127.0.0.1:5000
```

**Terminal 2: Test local trước**

```powershell
# Test xem server local hoạt động chưa
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py http://localhost:5000/video_feed/0
```

Phải thấy:

```
✓ Tìm thấy --frame tại vị trí 0
✓ Tìm thấy Content-Type: image/jpeg
```

**Terminal 3: Khởi động ngrok**

```powershell
# Chuyển đến thư mục chứa ngrok
cd C:\ngrok  # Hoặc đường dẫn bạn đã giải nén

# Khởi động ngrok
.\ngrok.exe http 5000
```

**Terminal 4: Test ngrok URL**

```powershell
# Copy URL từ ngrok, ví dụ: https://xxxx.ngrok-free.app
# Test debug:
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py https://xxxx.ngrok-free.app/video_feed/0
```

Nếu thấy:

```
✓ Tìm thấy JPEG image!
```

Thì chạy face detection:

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py https://xxxx.ngrok-free.app/video_feed/0
```

## 🔍 Troubleshooting

### Lỗi: Vẫn thấy HTML

```powershell
# Kiểm tra server có chạy không
curl http://localhost:5000/cameras

# Phải trả về JSON: {"cameras":[0],"count":1}
```

### Lỗi: Connection refused

- Server chưa chạy
- Firewall chặn port 5000
- Chạy: `netstat -ano | findstr :5000` để xem port có mở không

### Lỗi: ngrok không forward

- Kiểm tra ngrok đang forward port nào (xem trong terminal ngrok)
- Đảm bảo ngrok forward đúng port 5000

## 💡 Quick Check Script

Chạy script này để check tất cả:

```powershell
# Check 1: Server local
Write-Host "Check 1: Server local"
curl http://localhost:5000/cameras

# Check 2: Video feed local
Write-Host "`nCheck 2: Video feed local"
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py http://localhost:5000/video_feed/0

# Check 3: Ngrok URL (thay YOUR_NGROK_URL)
Write-Host "`nCheck 3: Ngrok URL"
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py https://YOUR_NGROK_URL.ngrok-free.app/video_feed/0
```

## 🎯 Checklist

- [ ] Server đã chạy và hiển thị "Running on http://127.0.0.1:5000"
- [ ] Test local thành công: `http://localhost:5000/cameras` trả về JSON
- [ ] Debug local thấy JPEG markers
- [ ] ngrok đã khởi động và hiển thị URL
- [ ] Debug ngrok URL thấy JPEG markers
- [ ] Face detection client chạy thành công

## 📞 Nếu vẫn lỗi

Gửi cho tôi output của:

```powershell
# 1. Output từ server terminal
# 2. Output từ ngrok terminal
# 3. Output từ debug_stream với localhost
# 4. Output từ debug_stream với ngrok URL
```
