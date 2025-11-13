import cv2
import numpy as np
import argparse
import sys
import time
from threading import Thread


class RTSPFaceDetector:
    """
    Class xử lý RTSP video stream và face detection
    """

    def __init__(self, rtsp_url, window_name="RTSP Face Detection"):
        self.rtsp_url = rtsp_url
        self.window_name = window_name
        self.stopped = False
        self.frame = None
        self.grabbed = False
        self.cap = None

        # Load Haar Cascade cho face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Thống kê
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.last_fps_count = 0

    def connect(self):
        """Kết nối đến RTSP stream"""
        print(f"\n{'='*70}")
        print("KẾT NỐI ĐÉN RTSP STREAM")
        print("=" * 70)
        print(f"URL: {self.rtsp_url}")

        try:
            # Khởi tạo VideoCapture với RTSP URL
            self.cap = cv2.VideoCapture(self.rtsp_url)

            # Cấu hình buffer để giảm độ trễ
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Kiểm tra kết nối
            if not self.cap.isOpened():
                print("\n[ERROR] Không thể mở RTSP stream!")
                print("\n[INFO] Kiểm tra:")
                print("   - URL RTSP có đúng không?")
                print("   - Camera có đang hoạt động không?")
                print("   - Mạng có kết nối được không?")
                return False

            # Đọc thử frame đầu tiên
            ret, frame = self.cap.read()
            if ret and frame is not None:
                print(f"\n[OK] Kết nối thành công!")
                print(f"   - Kích thước frame: {frame.shape}")
                print(f"   - FPS: {self.cap.get(cv2.CAP_PROP_FPS):.1f}")
                self.frame = frame
                self.grabbed = True
                return True
            else:
                print("\n[ERROR] Không thể đọc frame từ stream!")
                return False

        except Exception as e:
            print(f"\n[ERROR] Lỗi kết nối: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start(self):
        """Bắt đầu thread đọc stream"""
        Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        """Thread liên tục đọc frame từ RTSP stream"""
        try:
            while not self.stopped:
                if self.cap is None or not self.cap.isOpened():
                    print("[WARNING] Stream bị ngắt kết nối!")
                    time.sleep(1)
                    # Thử kết nối lại
                    print("[INFO] Đang thử kết nối lại...")
                    if not self.connect():
                        self.stopped = True
                        break
                    continue

                ret, frame = self.cap.read()

                if ret and frame is not None:
                    self.frame = frame
                    self.grabbed = True
                    self.frame_count += 1
                else:
                    print("[WARNING] Không đọc được frame, đang thử lại...")
                    time.sleep(0.1)

        except Exception as e:
            print(f"[ERROR] Lỗi trong thread update: {e}")
            import traceback
            traceback.print_exc()
            self.stopped = True

    def read(self):
        """Đọc frame hiện tại"""
        return self.grabbed, self.frame

    def stop(self):
        """Dừng stream"""
        self.stopped = True
        if self.cap is not None:
            self.cap.release()

    def detect_faces(self, frame):
        """Phát hiện khuôn mặt trong frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Phát hiện khuôn mặt
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        # Vẽ rectangle và thông tin lên frame
        for x, y, w, h in faces:
            # Rectangle xung quanh khuôn mặt
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Text "Face"
            cv2.putText(
                frame,
                "Face",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Điểm chính giữa khuôn mặt
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)

        return frame, faces

    def calculate_fps(self):
        """Tính FPS thực tế"""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed >= 1.0:  # Cập nhật FPS mỗi giây
            fps = (self.frame_count - self.last_fps_count) / elapsed
            self.fps = fps
            self.last_fps_time = current_time
            self.last_fps_count = self.frame_count

        return self.fps

    def add_info_overlay(self, frame, faces):
        """Thêm thông tin lên frame"""
        height, width = frame.shape[:2]

        # Tính FPS
        current_fps = self.calculate_fps()

        # Vẽ background cho text
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Thông tin hiển thị
        info_texts = [
            f"Faces Detected: {len(faces)}",
            f"FPS: {current_fps:.1f}",
            f"Total Frames: {self.frame_count}",
        ]

        y_offset = 25
        for i, text in enumerate(info_texts):
            color = (0, 255, 0) if (i == 0 and len(faces) > 0) else (255, 255, 255)
            cv2.putText(
                frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
            y_offset += 25

        # Help text
        help_text = "Press 'q' or 'ESC' to quit | 's' to save screenshot | 'r' to reconnect"
        cv2.putText(
            frame,
            help_text,
            (10, height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        return frame

    def run(self):
        """Chạy chương trình chính"""
        print("=" * 70)
        print("FACE DETECTION FROM RTSP STREAM")
        print("=" * 70)

        # Kết nối đến RTSP
        if not self.connect():
            print("\n[ERROR] Không thể kết nối đến RTSP stream!")
            return

        # Bắt đầu thread đọc frame
        self.start()

        print("\n[INFO] Đang hiển thị video với face detection...")
        print("   - Nhấn 'q' hoặc 'ESC' để thoát")
        print("   - Nhấn 's' để chụp ảnh màn hình")
        print("   - Nhấn 'r' để kết nối lại\n")

        screenshot_count = 0

        try:
            while not self.stopped:
                grabbed, frame = self.read()

                if not grabbed or frame is None:
                    time.sleep(0.01)
                    continue

                # Detect faces và vẽ lên frame
                processed_frame, faces = self.detect_faces(frame.copy())

                # Thêm thông tin overlay
                processed_frame = self.add_info_overlay(processed_frame, faces)

                # Hiển thị frame
                cv2.imshow(self.window_name, processed_frame)

                # Xử lý phím bấm
                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:  # 'q' hoặc ESC
                    print("\n[STOP] Đang dừng...")
                    break
                elif key == ord("s"):  # Chụp màn hình
                    screenshot_count += 1
                    filename = f"rtsp_screenshot_{screenshot_count}_{int(time.time())}.jpg"
                    cv2.imwrite(filename, processed_frame)
                    print(f"[OK] Đã lưu: {filename}")
                elif key == ord("r"):  # Kết nối lại
                    print("\n[INFO] Đang kết nối lại...")
                    self.stop()
                    time.sleep(0.5)
                    if self.connect():
                        self.stopped = False
                        self.start()
                        print("[OK] Đã kết nối lại thành công!")
                    else:
                        print("[ERROR] Không thể kết nối lại!")
                        break

        except KeyboardInterrupt:
            print("\n[WARNING] Đã dừng bởi người dùng (Ctrl+C)")
        except Exception as e:
            print(f"\n[ERROR] Lỗi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
            cv2.destroyAllWindows()

            # Thống kê
            total_time = time.time() - self.start_time
            avg_fps = self.frame_count / total_time if total_time > 0 else 0

            print()
            print("[STATS] Thống kê:")
            print(f"   - Tổng frames: {self.frame_count}")
            print(f"   - FPS trung bình: {avg_fps:.2f}")
            print(f"   - Thời gian chạy: {total_time:.1f}s")
            print()
            print("[OK] Chương trình đã kết thúc")


def main():
    """Hàm main"""
    parser = argparse.ArgumentParser(
        description="Face Detection từ RTSP Stream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # RTSP stream từ camera IP
  python face_detection_rtsp.py rtsp://192.168.1.100:554/stream
  
  # RTSP với username và password
  python face_detection_rtsp.py rtsp://admin:password@192.168.1.100:554/stream
  
  # RTSP với tên cửa sổ tùy chỉnh
  python face_detection_rtsp.py rtsp://192.168.1.100:554/stream -w "Camera 1"

Định dạng RTSP URL:
  rtsp://[username:password@]host[:port]/path
  
Ví dụ:
  - rtsp://192.168.1.100:554/stream
  - rtsp://admin:12345@192.168.1.100:554/live/ch00_0
  - rtsp://camera.local:8554/stream1

Phím điều khiển:
  - 'q' hoặc 'ESC': Thoát chương trình
  - 's': Chụp ảnh màn hình
  - 'r': Kết nối lại stream
        """,
    )

    parser.add_argument(
        "rtsp_url",
        nargs="?",
        default="",
        help="URL RTSP của camera (ví dụ: rtsp://192.168.1.100:554/stream)",
    )

    parser.add_argument(
        "-w", "--window", default="RTSP Face Detection", help="Tên cửa sổ hiển thị"
    )

    args = parser.parse_args()

    # Kiểm tra URL
    if not args.rtsp_url:
        print("[ERROR] Vui lòng cung cấp URL RTSP!")
        print("\nVí dụ:")
        print("  python face_detection_rtsp.py rtsp://192.168.1.100:554/stream")
        print("\nHoặc xem thêm: python face_detection_rtsp.py --help")
        sys.exit(1)

    if not args.rtsp_url.startswith("rtsp://"):
        print("[ERROR] URL không hợp lệ! URL RTSP phải bắt đầu với 'rtsp://'")
        print(f"\nURL nhận được: {args.rtsp_url}")
        print("\nĐịnh dạng đúng:")
        print("  rtsp://[username:password@]host[:port]/path")
        print("\nVí dụ:")
        print("  rtsp://192.168.1.100:554/stream")
        print("  rtsp://admin:password@192.168.1.100:554/live")
        sys.exit(1)

    # Tạo detector và chạy
    detector = RTSPFaceDetector(args.rtsp_url, args.window)
    detector.run()


if __name__ == "__main__":
    main()
