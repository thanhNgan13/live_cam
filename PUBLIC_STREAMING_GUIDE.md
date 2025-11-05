# 🌐 Hướng dẫn Public Camera Stream

## ❌ Vấn đề hiện tại

Dev Tunnels đang yêu cầu authentication, trả về trang HTML GitHub thay vì video stream.

## ✅ Giải pháp

### **Cách 1: Sử dụng ngrok (Khuyên dùng)**

1. **Tải ngrok**: https://ngrok.com/download

2. **Giải nén và chạy**:

```powershell
# Di chuyển vào thư mục chứa ngrok.exe
cd path\to\ngrok

# Public port 5000
.\ngrok.exe http 5000
```

3. **Copy URL từ ngrok**:

```
Forwarding   https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:5000
```

4. **Sử dụng URL ngrok**:

```powershell
# Xem trong browser
https://xxxx-xxxx-xxxx.ngrok-free.app/camera-0

# Xem với face detection client
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py https://xxxx-xxxx-xxxx.ngrok-free.app/video_feed/0
```

### **Cách 2: Cấu hình Dev Tunnel cho anonymous**

Trong VS Code Terminal:

```powershell
# Tạo tunnel mới với anonymous access
devtunnel user login

# Tạo tunnel
devtunnel create --allow-anonymous

# Forward port 5000
devtunnel port create -p 5000 --protocol https

# Host tunnel
devtunnel host
```

Sau đó copy URL và sử dụng.

### **Cách 3: Sử dụng trong LAN (không cần public)**

Nếu chỉ cần truy cập trong mạng nội bộ:

```powershell
# Lấy IP của máy
ipconfig

# Tìm IPv4 Address, ví dụ: 192.168.1.100
```

Sau đó truy cập từ máy khác:

```
http://192.168.1.100:5000/camera-0
```

Face detection client:

```powershell
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py http://192.168.1.100:5000/video_feed/0
```

### **Cách 4: Sử dụng localhost tunnel khác**

**LocalTunnel** (miễn phí, không cần đăng ký):

```powershell
# Cài đặt (cần Node.js)
npm install -g localtunnel

# Chạy
lt --port 5000
```

**CloudFlare Tunnel** (miễn phí, ổn định):

```powershell
# Tải cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Chạy
cloudflared tunnel --url http://localhost:5000
```

## 🧪 Test xem tunnel hoạt động chưa

Sau khi có URL public, test bằng:

```powershell
# Debug stream
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py <YOUR_PUBLIC_URL>/video_feed/0

# Kiểm tra xem có JPEG markers không
# Phải thấy: ✓ Tìm thấy JPEG image!
```

## 📝 Ví dụ với ngrok

```powershell
# Terminal 1: Chạy server
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe camera_stream_server.py

# Terminal 2: Chạy ngrok
ngrok http 5000

# Terminal 3: Test
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe debug_stream.py https://xxxx.ngrok-free.app/video_feed/0

# Nếu thấy JPEG markers, chạy client:
D:/DUT_ITF/Semester_9th/IoT/live_cam/.venv/Scripts/python.exe face_detection_client.py https://xxxx.ngrok-free.app/video_feed/0
```

## ⚠️ Lưu ý

- **ngrok free**: URL thay đổi mỗi lần restart
- **Dev Tunnels**: Cần config anonymous access
- **LAN**: Chỉ hoạt động trong mạng nội bộ
- **Firewall**: Có thể cần tắt firewall hoặc add exception

## 💡 Giải pháp tôi recommend

**Cho development/testing**: ngrok (nhanh, đơn giản)
**Cho production**: CloudFlare Tunnel hoặc VPS với Nginx
**Cho LAN**: Truy cập trực tiếp qua IP
