import cv2
import numpy as np
import requests
import argparse
import sys
from threading import Thread
import time
import urllib3

# Tắt warning SSL cho dev tunnels
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VideoStreamDetector:
    """
    Class xử lý video stream và face detection
    """
    def __init__(self, stream_url, window_name="Face Detection"):
        self.stream_url = stream_url
        self.window_name = window_name
        self.stopped = False
        self.frame = None
        self.grabbed = False
        
        # Load Haar Cascade cho face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Thống kê
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
    def start(self):
        """Bắt đầu thread đọc stream"""
        Thread(target=self.update, args=(), daemon=True).start()
        return self
    
    def update(self):
        """Thread liên tục đọc frame từ stream"""
        try:
            print(f"🔗 Đang kết nối tới: {self.stream_url}")
            
            # Headers để giả lập browser và bypass ngrok warning
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'multipart/x-mixed-replace,*/*',
                'ngrok-skip-browser-warning': 'true'  # Bypass ngrok warning page
            }
            
            # Kết nối tới stream với timeout dài hơn cho HTTPS
            stream = requests.get(
                self.stream_url, 
                stream=True, 
                timeout=30,
                headers=headers,
                verify=False  # Bỏ qua SSL verification cho dev tunnels
            )
            
            if stream.status_code != 200:
                print(f"❌ Lỗi kết nối: HTTP {stream.status_code}")
                self.stopped = True
                return
            
            # Kiểm tra Content-Type
            content_type = stream.headers.get('Content-Type', '')
            if 'html' in content_type.lower():
                print(f"❌ Lỗi: Server trả về HTML thay vì video stream!")
                print(f"   Content-Type: {content_type}")
                print(f"\n💡 Có thể do:")
                print(f"   - Dev Tunnel yêu cầu authentication")
                print(f"   - URL không đúng")
                print(f"   - Server không chạy")
                print(f"\n📖 Xem hướng dẫn: PUBLIC_STREAMING_GUIDE.md")
                self.stopped = True
                return
            
            print("✓ Kết nối thành công!")
            print(f"   Content-Type: {content_type}")
            
            bytes_data = bytes()
            first_frame_received = False
            no_jpeg_count = 0
            max_no_jpeg = 100  # Dừng sau 100 chunk không có JPEG
            
            for chunk in stream.iter_content(chunk_size=8192):  # Tăng buffer size
                if self.stopped:
                    break
                
                bytes_data += chunk
                
                # Tìm JPEG boundary
                a = bytes_data.find(b'\xff\xd8')  # JPEG start
                b = bytes_data.find(b'\xff\xd9')  # JPEG end
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    # Reset counter
                    no_jpeg_count = 0
                    
                    # Decode frame
                    frame = cv2.imdecode(
                        np.frombuffer(jpg, dtype=np.uint8), 
                        cv2.IMREAD_COLOR
                    )
                    
                    if frame is not None:
                        self.frame = frame
                        self.grabbed = True
                        self.frame_count += 1
                        
                        if not first_frame_received:
                            first_frame_received = True
                            print(f"✓ Đã nhận frame đầu tiên! Kích thước: {frame.shape}")
                else:
                    # Không tìm thấy JPEG trong chunk này
                    no_jpeg_count += 1
                    if no_jpeg_count >= max_no_jpeg and not first_frame_received:
                        print(f"❌ Không nhận được JPEG data sau {max_no_jpeg} chunks!")
                        print(f"   Stream có thể không phải là video stream.")
                        print(f"   Thử debug: python debug_stream.py {self.stream_url}")
                        self.stopped = True
                        break
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi kết nối: {e}")
            self.stopped = True
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
            self.stopped = True
    
    def read(self):
        """Đọc frame hiện tại"""
        return self.grabbed, self.frame
    
    def stop(self):
        """Dừng stream"""
        self.stopped = True
    
    def detect_faces(self, frame):
        """
        Phát hiện khuôn mặt trong frame
        
        Returns:
            frame: Frame đã được vẽ box
            faces: Danh sách tọa độ khuôn mặt
        """
        # Chuyển sang grayscale để detect
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Vẽ box cho mỗi khuôn mặt
        for (x, y, w, h) in faces:
            # Vẽ hình chữ nhật màu xanh lá
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Thêm text "Face"
            cv2.putText(
                frame, 
                'Face', 
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2
            )
            
            # Vẽ điểm tâm
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)
        
        return frame, faces
    
    def add_info_overlay(self, frame, faces):
        """Thêm thông tin lên frame"""
        height, width = frame.shape[:2]
        
        # Tính FPS
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            self.fps = self.frame_count / elapsed_time
        
        # Background cho text (semi-transparent)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Thông tin
        info_texts = [
            f"Faces Detected: {len(faces)}",
            f"FPS: {self.fps:.1f}",
            f"Stream: {self.stream_url[:50]}..."
        ]
        
        y_offset = 25
        for i, text in enumerate(info_texts):
            if i == 0:
                color = (0, 255, 0) if len(faces) > 0 else (255, 255, 255)
            else:
                color = (255, 255, 255)
            
            cv2.putText(
                frame, 
                text, 
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                color, 
                2
            )
            y_offset += 25
        
        # Hướng dẫn
        help_text = "Press 'q' or 'ESC' to quit | 's' to save screenshot"
        cv2.putText(
            frame,
            help_text,
            (10, height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        return frame
    
    def run(self):
        """Chạy chương trình chính"""
        print("=" * 70)
        print("🎯 FACE DETECTION FROM VIDEO STREAM")
        print("=" * 70)
        print()
        
        # Bắt đầu stream
        self.start()
        
        # Đợi frame đầu tiên (tăng thời gian đợi cho HTTPS)
        print("⏳ Đang đợi frame đầu tiên...")
        print("   (Có thể mất vài giây với HTTPS/dev tunnels...)")
        wait_count = 0
        max_wait = 150  # Tăng từ 50 lên 150 (15 giây)
        
        while not self.grabbed and not self.stopped and wait_count < max_wait:
            time.sleep(0.1)
            wait_count += 1
            
            # Hiển thị tiến trình
            if wait_count % 10 == 0:
                print(f"   Đang đợi... ({wait_count//10}s)")
        
        if self.stopped or not self.grabbed:
            print("❌ Không thể lấy frame từ stream!")
            print("💡 Gợi ý:")
            print("   - Kiểm tra URL có đúng không")
            print("   - Thử mở URL trong browser xem có stream không")
            print("   - Kiểm tra kết nối mạng")
            print("   - Server có thể đang bận, thử lại sau")
            return
        
        print("✓ Đã nhận frame đầu tiên!")
        print()
        print("📹 Đang hiển thị video với face detection...")
        print("   - Nhấn 'q' hoặc 'ESC' để thoát")
        print("   - Nhấn 's' để chụp ảnh màn hình")
        print()
        
        screenshot_count = 0
        
        # Vòng lặp chính
        try:
            while not self.stopped:
                grabbed, frame = self.read()
                
                if not grabbed or frame is None:
                    time.sleep(0.01)
                    continue
                
                # Detect faces
                processed_frame, faces = self.detect_faces(frame.copy())
                
                # Thêm overlay info
                processed_frame = self.add_info_overlay(processed_frame, faces)
                
                # Hiển thị
                cv2.imshow(self.window_name, processed_frame)
                
                # Xử lý phím
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:  # 'q' hoặc ESC
                    print("\n⏹️  Đang dừng...")
                    break
                elif key == ord('s'):  # 's' để save screenshot
                    screenshot_count += 1
                    filename = f"screenshot_{screenshot_count}_{int(time.time())}.jpg"
                    cv2.imwrite(filename, processed_frame)
                    print(f"📸 Đã lưu: {filename}")
        
        except KeyboardInterrupt:
            print("\n⚠️  Đã dừng bởi người dùng")
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
        finally:
            # Cleanup
            self.stop()
            cv2.destroyAllWindows()
            
            print()
            print("📊 Thống kê:")
            print(f"   - Tổng frames: {self.frame_count}")
            print(f"   - FPS trung bình: {self.fps:.2f}")
            print(f"   - Thời gian chạy: {time.time() - self.start_time:.1f}s")
            print()
            print("✓ Chương trình đã kết thúc")


def main():
    """Hàm main"""
    parser = argparse.ArgumentParser(
        description='Face Detection từ Video Stream',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Stream từ local server
  python face_detection_client.py http://localhost:5000/video_feed/0
  
  # Stream từ IP camera
  python face_detection_client.py http://192.168.1.100:8080/video
  
  # Stream với tên cửa sổ tùy chỉnh
  python face_detection_client.py http://localhost:5000/video_feed/1 -w "My Camera"
        """
    )
    
    parser.add_argument(
        'stream_url',
        nargs='?',
        default='http://localhost:5000/video_feed/0',
        help='URL của video stream (mặc định: http://localhost:5000/video_feed/0)'
    )
    
    parser.add_argument(
        '-w', '--window',
        default='Face Detection',
        help='Tên cửa sổ hiển thị (mặc định: Face Detection)'
    )
    
    args = parser.parse_args()
    
    # Kiểm tra URL
    if not args.stream_url.startswith(('http://', 'https://', 'rtsp://')):
        print("❌ URL không hợp lệ! Phải bắt đầu với http://, https:// hoặc rtsp://")
        sys.exit(1)
    
    # Khởi tạo và chạy detector
    detector = VideoStreamDetector(args.stream_url, args.window)
    detector.run()


if __name__ == '__main__':
    main()
