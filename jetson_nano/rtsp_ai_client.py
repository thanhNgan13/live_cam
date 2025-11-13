import cv2

# Thay IP_JETSON bằng IP thật của Jetson
RTSP_URL = "rtsp://192.168.1.3:8554/cam"


def main():
    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print(f"Không mở được stream: {RTSP_URL}")
        return

    print("Đang đọc RTSP stream, nhấn q để thoát...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không đọc được frame (mất kết nối?)")
            break

        # TODO: xử lý AI ở đây, ví dụ:
        # result = model(frame)

        # Hiển thị cho debug, có thể bỏ nếu không cần
        cv2.imshow("RTSP Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
