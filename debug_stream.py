import requests
import sys

def debug_stream(url):
    """Debug xem stream trả về gì"""
    print(f"🔍 Đang kiểm tra stream: {url}")
    print("=" * 70)
    
    try:
        # Kết nối
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'ngrok-skip-browser-warning': 'true'  # Bypass ngrok warning page
        }
        
        response = requests.get(url, stream=True, timeout=10, headers=headers, verify=False)
        
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        print("\n📦 Đang đọc 10KB dữ liệu đầu tiên...")
        
        data = b''
        for chunk in response.iter_content(chunk_size=1024):
            data += chunk
            if len(data) >= 10240:  # 10KB
                break
        
        print(f"\n✓ Đã đọc {len(data)} bytes")
        
        # Tìm JPEG markers
        jpeg_start = data.find(b'\xff\xd8')
        jpeg_end = data.find(b'\xff\xd9')
        
        print(f"\n🔎 Phân tích dữ liệu:")
        print(f"   JPEG start marker (\\xff\\xd8) tại vị trí: {jpeg_start}")
        print(f"   JPEG end marker (\\xff\\xd9) tại vị trí: {jpeg_end}")
        
        if jpeg_start != -1 and jpeg_end != -1:
            print(f"   ✓ Tìm thấy JPEG image! Kích thước: {jpeg_end - jpeg_start + 2} bytes")
        else:
            print(f"   ❌ Không tìm thấy JPEG markers!")
        
        # Hiển thị 200 bytes đầu tiên (hex)
        print(f"\n📄 100 bytes đầu tiên (hex):")
        hex_data = data[:100].hex()
        for i in range(0, len(hex_data), 32):
            print(f"   {hex_data[i:i+32]}")
        
        # Hiển thị dạng text (nếu có)
        print(f"\n📝 100 bytes đầu tiên (text):")
        try:
            text_data = data[:100].decode('utf-8', errors='ignore')
            print(f"   {repr(text_data)}")
        except:
            print("   (Không thể decode thành text)")
        
        # Kiểm tra boundary
        boundary_markers = [
            b'--frame',
            b'--boundary',
            b'Content-Type: image/jpeg',
            b'multipart/x-mixed-replace'
        ]
        
        print(f"\n🔍 Tìm kiếm boundary markers:")
        for marker in boundary_markers:
            pos = data.find(marker)
            if pos != -1:
                print(f"   ✓ Tìm thấy {marker.decode('utf-8', errors='ignore')} tại vị trí {pos}")
            else:
                print(f"   ✗ Không tìm thấy {marker.decode('utf-8', errors='ignore')}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "http://localhost:5000/video_feed/0"
        print(f"💡 Sử dụng URL mặc định: {url}")
        print(f"   Hoặc: python debug_stream.py <URL>\n")
    
    debug_stream(url)
