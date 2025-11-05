# 🔧 Cài đặt Dev Tunnel cho Windows

## Cách 1: Cài qua winget (Khuyên dùng)

```powershell
winget install Microsoft.devtunnel
```

Sau khi cài xong, restart PowerShell rồi chạy:

```powershell
devtunnel user login
```

## Cách 2: Tải trực tiếp

1. Truy cập: https://aka.ms/devtunnels/download
2. Tải file Windows (devtunnel-windows-x64.zip)
3. Giải nén vào thư mục, ví dụ: `C:\devtunnel\`
4. Thêm vào PATH hoặc chạy trực tiếp:

```powershell
cd C:\devtunnel
.\devtunnel.exe user login
```

## Cách 3: Dùng ngrok thay thế (Đơn giản hơn)

### Tải ngrok:

1. Truy cập: https://ngrok.com/download
2. Tải file Windows (zip)
3. Giải nén ra thư mục, ví dụ: `C:\ngrok\`

### Sử dụng ngrok:

```powershell
# Chạy ngrok
cd C:\ngrok
.\ngrok.exe http 5000

# Hoặc nếu đã thêm vào PATH:
ngrok http 5000
```

Sau đó copy URL dạng: `https://xxxx-xxxx.ngrok-free.app`

### Test với URL ngrok:

```powershell
# Debug stream
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py https://xxxx-xxxx.ngrok-free.app/video_feed/0

# Nếu OK, chạy face detection
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py https://xxxx-xxxx.ngrok-free.app/video_feed/0
```

## Cách 4: Sử dụng CloudFlare Tunnel (Miễn phí, ổn định)

```powershell
# Tải từ: https://github.com/cloudflare/cloudflared/releases
# Hoặc dùng winget:
winget install --id Cloudflare.cloudflared

# Chạy:
cloudflared tunnel --url http://localhost:5000
```

## 💡 So sánh các giải pháp:

| Giải pháp      | Ưu điểm                 | Nhược điểm                      |
| -------------- | ----------------------- | ------------------------------- |
| **ngrok**      | Đơn giản, nhanh, web UI | URL đổi mỗi lần restart (free)  |
| **Dev Tunnel** | Tích hợp VS Code        | Cần cài đặt, setup phức tạp hơn |
| **CloudFlare** | Ổn định, nhanh          | Cần account CloudFlare          |
| **LAN**        | Không cần internet      | Chỉ trong mạng nội bộ           |

## 🎯 Khuyến nghị:

**Cho testing nhanh**: Dùng **ngrok**
**Cho production**: Dùng **CloudFlare Tunnel** hoặc VPS
**Cho LAN**: Truy cập trực tiếp qua IP

---

## ✅ Kiểm tra nhanh

Bạn đã thử ngrok chưa? Từ lịch sử terminal tôi thấy:

```
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py https://healthy-amazed-hog.ngrok-free.app/video_feed/0
```

URL ngrok có hoạt động không? Nếu có vấn đề gì, cho tôi biết output!
