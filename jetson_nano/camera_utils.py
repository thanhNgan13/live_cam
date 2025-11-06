import cv2
import threading
import time

# Dictionary lưu trữ camera instances
cameras = {}
camera_locks = {}


def find_available_cameras(max_cameras=10):
    """Tìm tất cả camera khả dụng"""
    available_cameras = []
    print("Đang quét camera...")

    for i in range(max_cameras):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                available_cameras.append(i)
                print(f"[OK] Tìm thấy camera {i}")
            cap.release()

    return available_cameras


def init_cameras():
    """Khởi tạo tất cả camera"""
    available = find_available_cameras()

    for cam_id in available:
        cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cameras[cam_id] = cap
            camera_locks[cam_id] = threading.Lock()
            print(f"[OK] Camera {cam_id} đã sẵn sàng")

    return list(cameras.keys())


def get_frame(camera_id):
    """Đọc frame từ camera"""
    if camera_id not in cameras:
        return None

    with camera_locks[camera_id]:
        cap = cameras[camera_id]
        ret, frame = cap.read()

        if not ret or frame is None:
            return None

        # Thêm info camera
        cv2.putText(
            frame, f"Camera {camera_id}", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        return frame


def generate_frames(camera_id):
    """Generator cho video streaming"""
    while True:
        frame = get_frame(camera_id)

        if frame is None:
            time.sleep(0.1)
            continue

        # Encode frame thành JPEG
        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # Yield frame theo format multipart
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


def cleanup():
    """Giải phóng tài nguyên khi tắt server"""
    print("\nĐang đóng tất cả camera...")
    for cam_id, cap in cameras.items():
        cap.release()
    print("[OK] Đã đóng tất cả camera")
