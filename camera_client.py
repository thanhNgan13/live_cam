import cv2
import requests
import numpy as np

def test_camera_stream(camera_url, detect_face=False):
    """
    Test và hiển thị camera stream từ server
    
    Args:
        camera_url: URL của camera stream, ví dụ: http://localhost:5000/video_feed/1
        detect_face: True nếu muốn kèm face detection
    """
    print(f"🔗 Đang kết nối tới: {camera_url}")
    
    if detect_face and '?' not in camera_url:
        camera_url += '?detect=true'
    
    # Tạo stream
    stream = requests.get(camera_url, stream=True, timeout=5)
    
    if stream.status_code != 200:
        print(f"❌ Lỗi: Không thể kết nối (Status code: {stream.status_code})")
        return
    
    print("✓ Kết nối thành công!")
    print("📹 Đang hiển thị stream... (Nhấn 'q' để thoát)")
    
    bytes_data = bytes()
    
    try:
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            
            # Tìm boundary của JPEG
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                # Decode và hiển thị
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    cv2.imshow('Camera Stream Test', frame)
                
                # Nhấn 'q' để thoát
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    
    except KeyboardInterrupt:
        print("\n⚠️ Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
    finally:
        cv2.destroyAllWindows()
        print("✓ Đã đóng stream")

if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("🧪 CAMERA STREAM CLIENT TEST")
    print("=" * 60)
    print()
    
    # Ví dụ sử dụng
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # URL mặc định
        url = "http://localhost:5000/video_feed/1"
        print(f"💡 Sử dụng URL mặc định: {url}")
        print(f"   Hoặc chạy: python camera_client.py <URL>")
        print()
    
    # Kiểm tra nếu muốn face detection
    detect = 'detect=true' in url.lower()
    
    test_camera_stream(url, detect)
