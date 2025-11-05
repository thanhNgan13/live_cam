import cv2
import numpy as np
import os

# Tắt log cảnh báo của OpenCV để giảm nhiễu
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

def find_available_cameras(max_cameras=10):
    """
    Tìm kiếm tất cả các camera khả dụng trên hệ thống
    
    Args:
        max_cameras: Số lượng camera tối đa để kiểm tra (mặc định 10)
    
    Returns:
        List các index của camera khả dụng
    """
    available_cameras = []
    
    print("Đang kiểm tra các camera khả dụng...")
    
    # Tắm log cảnh báo tạm thời
    cv2.setLogLevel(0)
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Sử dụng DirectShow trên Windows
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
                print(f"[OK] Tìm thấy camera {i}")
            cap.release()
    
    # Bật lại log
    cv2.setLogLevel(3)
    
    return available_cameras

def display_cameras(camera_indices):
    """
    Hiển thị video từ tất cả các camera trong các cửa sổ riêng biệt
    
    Args:
        camera_indices: List các index của camera cần hiển thị
    """
    if not camera_indices:
        print("Không tìm thấy camera nào!")
        return
    
    # Mở tất cả các camera và kiểm tra kỹ hơn
    cameras = []
    failed_cameras = []
    
    print("\nĐang khởi tạo các camera...")
    for idx in camera_indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            # Thử đọc 1 frame để đảm bảo camera hoạt động
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                cameras.append((idx, cap))
                # Đặt độ phân giải (tùy chọn)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                print(f"[OK] Camera {idx} sẵn sàng")
            else:
                failed_cameras.append(idx)
                cap.release()
                print(f"[ERROR] Camera {idx} không thể đọc frame")
        else:
            failed_cameras.append(idx)
            print(f"[ERROR] Camera {idx} không mở được")
        
        if not cameras:
            print("\n[ERROR] Không có camera nào hoạt động được!")
            if failed_cameras:
                print(f"Camera lỗi: {failed_cameras}")
            return
        
        print(f"\n[OK] Đang hiển thị {len(cameras)} camera hoạt động")
        if failed_cameras:
            print(f"[WARNING] Camera không hoạt động: {failed_cameras}")
    print("Nhấn 'q' hoặc 'ESC' để thoát\n")
    
    # Đếm lỗi liên tiếp cho mỗi camera
    error_counts = {idx: 0 for idx, _ in cameras}
    max_errors = 30  # Số lỗi tối đa trước khi loại bỏ camera
    
    # Vòng lặp hiển thị video
    while cameras:
        cameras_to_remove = []
        
        for idx, cap in cameras:
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Reset error count khi đọc thành công
                error_counts[idx] = 0
                
                # Thêm text hiển thị số camera
                cv2.putText(frame, f'Camera {idx}', (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Hiển thị FPS (tùy chọn)
                fps = cap.get(cv2.CAP_PROP_FPS)
                cv2.putText(frame, f'FPS: {fps:.1f}', (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Hiển thị frame
                cv2.imshow(f'Camera {idx}', frame)
            else:
                # Tăng error count
                error_counts[idx] += 1
                if error_counts[idx] >= max_errors:
                    print(f"[WARNING] Camera {idx} bị lỗi quá nhiều, đang loại bỏ...")
                    cameras_to_remove.append((idx, cap))
        
        # Loại bỏ camera lỗi
        for cam_tuple in cameras_to_remove:
            idx, cap = cam_tuple
            cap.release()
            cv2.destroyWindow(f'Camera {idx}')
            cameras.remove(cam_tuple)
            print(f"[STOP] Đã đóng camera {idx}")
        
        # Kiểm tra phím nhấn
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' hoặc ESC
            break
    
    # Giải phóng tài nguyên
    print("\nĐang đóng các camera...")
    for idx, cap in cameras:
        cap.release()
    cv2.destroyAllWindows()

def main():
    """
    Hàm chính của chương trình
    """
    print("=" * 50)
    print("CHUONG TRINH KIEM TRA VA HIEN THI CAMERA")
    print("=" * 50)
    print()
    
    # Tìm các camera khả dụng
    available_cameras = find_available_cameras(max_cameras=10)
    
    if available_cameras:
        print(f"\n[OK] Tổng số camera tìm thấy: {len(available_cameras)}")
        print(f"Danh sách camera: {available_cameras}")
        print()
        
        # Hiển thị các camera
        display_cameras(available_cameras)
    else:
        print("\n[ERROR] Không tìm thấy camera nào trên hệ thống!")
        print("Vui lòng kiểm tra:")
        print("  - Camera đã được kết nối chưa")
        print("  - Driver camera đã được cài đặt chưa")
        print("  - Camera có đang được sử dụng bởi ứng dụng khác không")
    
    print("\n[OK] Chương trình đã kết thúc.")

if __name__ == "__main__":
    main()
