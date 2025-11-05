import cv2
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import argparse
import sys
from threading import Thread
import time
import urllib3
from bs4 import BeautifulSoup
import re

# Tắt warning SSL cho dev tunnels
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SessionManager:
    """Quản lý session để bypass ngrok warning page"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Cấu hình retry
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Headers chuẩn
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def bypass_ngrok_warning(self, url):
        """
        Bypass ngrok warning page bằng cách:
        1. Truy cập URL lần đầu (nhận warning page)
        2. Phân tích HTML để lấy thông tin
        3. Gửi request mới với session đã được thiết lập
        """
        print(f"🔍 Đang kiểm tra URL: {url}")
        
        try:
            # Bước 1: Truy cập URL lần đầu
            print("   [1/4] Gửi request đầu tiên...")
            response = self.session.get(url, verify=False, timeout=10, allow_redirects=True)
            
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            # Kiểm tra xem có phải warning page không
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                print("   ⚠️  Phát hiện HTML response (có thể là warning page)")
                
                # Bước 2: Phân tích HTML
                print("   [2/4] Phân tích HTML...")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Tìm ngrok warning indicators
                is_ngrok_warning = False
                
                # Check 1: Tìm button "Visit Site"
                visit_button = soup.find('button', string=re.compile('Visit Site', re.I))
                if visit_button:
                    is_ngrok_warning = True
                    print("   ✓ Tìm thấy button 'Visit Site' - Đây là ngrok warning page")
                
                # Check 2: Tìm text về ngrok
                if 'ngrok-skip-browser-warning' in response.text:
                    is_ngrok_warning = True
                    print("   ✓ Tìm thấy 'ngrok-skip-browser-warning' - Đây là ngrok warning page")
                
                # Check 3: Tìm domain pattern
                if 'ngrok-free.app' in response.text or 'ngrok.com' in response.text:
                    is_ngrok_warning = True
                    print("   ✓ Tìm thấy ngrok domain - Đây là ngrok warning page")
                
                if is_ngrok_warning:
                    print("   [3/4] Bypass ngrok warning...")
                    
                    # Phương pháp 1: Thêm header đặc biệt
                    self.session.headers.update({
                        'ngrok-skip-browser-warning': 'true',
                        'Referer': url
                    })
                    
                    # Phương pháp 2: Gửi request mới với session đã thiết lập
                    print("   [4/4] Gửi request mới với session...")
                    response = self.session.get(url, verify=False, timeout=10, stream=True)
                    
                    new_content_type = response.headers.get('Content-Type', '').lower()
                    print(f"   ✓ Content-Type mới: {new_content_type}")
                    
                    if 'multipart' in new_content_type or 'image' in new_content_type:
                        print("   ✅ Đã bypass thành công! Nhận được video stream")
                        return response
                    elif 'text/html' in new_content_type:
                        print("   ⚠️  Vẫn nhận HTML, thử phương pháp khác...")
                        
                        # Phương pháp 3: Simulate click "Visit Site"
                        # Thêm cookies và headers như browser thật
                        self.session.headers.update({
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache',
                            'Upgrade-Insecure-Requests': '1'
                        })
                        
                        # Đợi một chút (simulate human behavior)
                        time.sleep(0.5)
                        
                        # Request lại
                        response = self.session.get(url, verify=False, timeout=10, stream=True)
                        new_content_type = response.headers.get('Content-Type', '').lower()
                        
                        if 'multipart' in new_content_type or 'image' in new_content_type:
                            print("   ✅ Bypass thành công sau lần thử thứ 2!")
                            return response
                        else:
                            print(f"   ❌ Không thể bypass. Content-Type: {new_content_type}")
                            return None
                    else:
                        return response
                else:
                    print("   ℹ️  Không phải ngrok warning page")
                    print("   💡 Có thể là lỗi server hoặc trang khác")
                    return None
            else:
                # Không phải HTML, có thể là stream rồi
                print("   ✅ Nhận được non-HTML response - Có thể là video stream")
                return response
                
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_stream_response(self, url):
        """Lấy stream response, tự động bypass warning nếu cần"""
        response = self.bypass_ngrok_warning(url)
        
        if response is None:
            print("\n❌ Không thể lấy stream!")
            return None
        
        # Kiểm tra cuối cùng
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'html' in content_type:
            print(f"\n❌ Vẫn nhận HTML sau khi bypass!")
            print(f"   Content-Type: {content_type}")
            print("\n💡 Giải pháp:")
            print("   1. Mở URL trong browser, click 'Visit Site' một lần")
            print("   2. Hoặc dùng ngrok paid để tắt warning page")
            print("   3. Hoặc dùng localhost trong LAN")
            return None
        
        print(f"\n✅ Thành công! Content-Type: {content_type}")
        return response


class VideoStreamDetector:
    """
    Class xử lý video stream và face detection với session management
    """
    def __init__(self, stream_url, window_name="Face Detection"):
        self.stream_url = stream_url
        self.window_name = window_name
        self.stopped = False
        self.frame = None
        self.grabbed = False
        
        # Session manager
        self.session_manager = SessionManager(stream_url)
        
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
            print(f"\n{'='*70}")
            print("🚀 BẮT ĐẦU KẾT NỐI VÀ BYPASS WARNING")
            print("="*70)
            
            # Sử dụng session manager để bypass warning
            stream = self.session_manager.get_stream_response(self.stream_url)
            
            if stream is None:
                self.stopped = True
                return
            
            print("\n" + "="*70)
            print("📹 BẮT ĐẦU ĐỌC VIDEO STREAM")
            print("="*70 + "\n")
            
            bytes_data = bytes()
            first_frame_received = False
            no_jpeg_count = 0
            max_no_jpeg = 100
            
            for chunk in stream.iter_content(chunk_size=8192):
                if self.stopped:
                    break
                
                bytes_data += chunk
                
                # Tìm JPEG boundary
                a = bytes_data.find(b'\xff\xd8')  # JPEG start
                b = bytes_data.find(b'\xff\xd9')  # JPEG end
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
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
                            print(f"✅ Đã nhận frame đầu tiên! Kích thước: {frame.shape}")
                            print(f"   Bắt đầu stream...\n")
                else:
                    no_jpeg_count += 1
                    if no_jpeg_count >= max_no_jpeg and not first_frame_received:
                        print(f"❌ Không nhận được JPEG data sau {max_no_jpeg} chunks!")
                        self.stopped = True
                        break
        
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
        """Phát hiện khuôn mặt trong frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, 'Face', (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)
        
        return frame, faces
    
    def add_info_overlay(self, frame, faces):
        """Thêm thông tin lên frame"""
        height, width = frame.shape[:2]
        
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            self.fps = self.frame_count / elapsed_time
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        info_texts = [
            f"Faces Detected: {len(faces)}",
            f"FPS: {self.fps:.1f}",
            f"Stream: {self.stream_url[:50]}..."
        ]
        
        y_offset = 25
        for i, text in enumerate(info_texts):
            color = (0, 255, 0) if (i == 0 and len(faces) > 0) else (255, 255, 255)
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25
        
        help_text = "Press 'q' or 'ESC' to quit | 's' to save screenshot"
        cv2.putText(frame, help_text, (10, height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run(self):
        """Chạy chương trình chính"""
        print("=" * 70)
        print("🎯 FACE DETECTION FROM VIDEO STREAM (WITH AUTO BYPASS)")
        print("=" * 70)
        
        self.start()
        
        print("\n⏳ Đang đợi frame đầu tiên...")
        print("   (Session đã được thiết lập, đang đọc stream...)")
        
        wait_count = 0
        max_wait = 150
        
        while not self.grabbed and not self.stopped and wait_count < max_wait:
            time.sleep(0.1)
            wait_count += 1
            
            if wait_count % 10 == 0 and wait_count > 0:
                print(f"   Đang đợi... ({wait_count//10}s)")
        
        if self.stopped or not self.grabbed:
            print("\n❌ Không thể lấy frame từ stream!")
            print("\n💡 Có thể do:")
            print("   - Warning page không thể bypass tự động")
            print("   - Server không trả về video stream")
            print("   - Kết nối bị gián đoạn")
            return
        
        print("\n📹 Đang hiển thị video với face detection...")
        print("   - Nhấn 'q' hoặc 'ESC' để thoát")
        print("   - Nhấn 's' để chụp ảnh màn hình\n")
        
        screenshot_count = 0
        
        try:
            while not self.stopped:
                grabbed, frame = self.read()
                
                if not grabbed or frame is None:
                    time.sleep(0.01)
                    continue
                
                processed_frame, faces = self.detect_faces(frame.copy())
                processed_frame = self.add_info_overlay(processed_frame, faces)
                
                cv2.imshow(self.window_name, processed_frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:
                    print("\n⏹️  Đang dừng...")
                    break
                elif key == ord('s'):
                    screenshot_count += 1
                    filename = f"screenshot_{screenshot_count}_{int(time.time())}.jpg"
                    cv2.imwrite(filename, processed_frame)
                    print(f"📸 Đã lưu: {filename}")
        
        except KeyboardInterrupt:
            print("\n⚠️  Đã dừng bởi người dùng")
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
        finally:
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
        description='Face Detection từ Video Stream (Auto Bypass ngrok warning)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Stream từ ngrok (tự động bypass warning)
  python face_detection_client_v2.py https://xxxx.ngrok-free.app/video_feed/0
  
  # Stream từ local server
  python face_detection_client_v2.py http://localhost:5000/video_feed/0
  
  # Stream với tên cửa sổ tùy chỉnh
  python face_detection_client_v2.py https://xxxx.ngrok-free.app/video_feed/0 -w "My Camera"

Chương trình này sẽ:
  1. Tự động phát hiện ngrok warning page
  2. Bypass warning page bằng cách thiết lập session đúng cách
  3. Duy trì session để stream liên tục
  4. Hiển thị face detection realtime
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
        default='Face Detection (Auto Bypass)',
        help='Tên cửa sổ hiển thị'
    )
    
    args = parser.parse_args()
    
    if not args.stream_url.startswith(('http://', 'https://', 'rtsp://')):
        print("❌ URL không hợp lệ! Phải bắt đầu với http://, https:// hoặc rtsp://")
        sys.exit(1)
    
    # Cần cài thêm beautifulsoup4
    try:
        import bs4
    except ImportError:
        print("❌ Thiếu thư viện beautifulsoup4!")
        print("📦 Cài đặt: pip install beautifulsoup4")
        sys.exit(1)
    
    detector = VideoStreamDetector(args.stream_url, args.window)
    detector.run()


if __name__ == '__main__':
    main()
