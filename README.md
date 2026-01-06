# Hệ Thống Nhận Diện Khuôn Mặt & Chấm Công

Phiên bản rút gọn và cập nhật README cho repository. Chương trình dùng camera để nhận diện khuôn mặt (OpenCV LBPH) và lưu lịch sử chấm công trong `attendance_log.json`.

**Entrypoint chính:** `main-run.py` (chạy UI keypad, LCD, RFID, camera, và một Flask nhỏ ở port 5001).

## Tóm tắt chức năng
- Checkin / Checkout bằng nhận diện khuôn mặt.
- Đăng ký nhanh bằng RFID (chế độ Register trong menu).
- Huấn luyện mô hình từ thư mục `data/` (LBPH) và lưu vào `models/face_model.yml`.
- Giao diện web đơn giản chạy từ `app.py` (port 5001).

## Yêu cầu
- Python 3.15+ (môi trường virtualenv khuyến nghị)
- Thư viện: cài bằng `pip install -r requirements.txt` (đã có trong repo).
- Phần cứng: webcam USB hoặc Pi Camera; nếu dùng Raspberry Pi, đảm bảo driver/thuộc tính camera đã bật.

## Cài đặt nhanh
Linux / Raspberry Pi (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Chạy hệ thống
- Kết nối camera và (tuỳ chọn) RFID, LCD, keypad như phần cứng trong dự án.
- Khởi động:

```bash
python3 main-run.py
```

Khi chạy, chương trình sẽ:
- Khởi động một thread Flask (serve `app.py`) tại `http://0.0.0.0:5001`.
- Khởi tạo CameraManager, LCD, Buzzer, và (nếu có) module RFID.

## Điều khiển (trên keypad)
- `1`: Checkin (gọi `quick_recognize(mode='in')`)
- `2`: Checkout (gọi `quick_recognize(mode='out')`)
- `3`: Chuyển sang chế độ Register (quét RFID)
- `9`: Bắt đầu huấn luyện (gọi `module.train.train_model()`)
- Nhấn giữ `*` → vào chế độ reboot (yêu cầu mã `121103` để xác thực)

Kết quả chấm công được lưu vào `attendance_log.json` với các trường: `name`, `datetime`, `type` (`in`/`out`).

## Cấu trúc chính của repo
- `main-run.py` : Trình điều khiển chính (menu, luồng chính, gọi `quick_recognize`, start Flask).
- `app.py` : Ứng dụng Flask nhỏ (chạy song song trên port 5001).
- `module/` : Các module phần cứng và chức năng (camera, keypad, RFID, train, recognize, ...).
- `data/` : Ảnh thô theo từng nhân viên (thư mục con mỗi người).
- `models/` : `face_model.yml` và `label_map.txt`.
- `attendance_log.json` : Lịch sử chấm công.

## Huấn luyện mô hình
- Để huấn luyện, đảm bảo `data/` chứa thư mục con cho mỗi nhân viên, mỗi thư mục chứa ảnh grayscale/ảnh mặt.
- Bạn có thể nhấn `9` trên keypad khi chương trình `main-run.py` đang chạy để huấn luyện.
- Chạy thủ công (ví dụ để train offline):

```bash
python3 -c "from module.train import train_model; train_model()"
```

Sau khi huấn luyện, kết quả sẽ được lưu vào `models/face_model.yml` và `models/label_map.txt`.

## Lưu ý triển khai trên Raspberry Pi
- OpenCV có thể khó cài đặt trực tiếp trên Pi; cân nhắc cài các phụ thuộc hệ thống hoặc dùng wheel đã build sẵn.
- Nếu muốn tiết kiệm tài nguyên: train trên máy mạnh rồi copy `models/face_model.yml` sang Pi.

## Một số lưu ý kỹ thuật
- `quick_recognize()` trong `module/recognize.py` sử dụng LBPH và trả về tên được nhận diện nhiều nhất trong một phiên thu mẫu.
- `module/train.py` xây dựng `label_map.txt` theo chỉ số và tên thư mục trong `data/`.
- `main-run.py` chứa logic kiểm tra trạng thái (duplicate check, not checked in, ...), và màn hình LCD thông báo cho người dùng.

## Khắc phục sự cố nhanh
- Nếu không nhận camera: kiểm tra `dmesg`, `v4l2-ctl --list-devices`, và quyền truy cập `/dev/video*`.
- Nếu model không load: kiểm tra đường dẫn `models/face_model.yml` và quyền đọc.
- Nếu nhận diện kém: tăng số ảnh mỗi người, cải thiện ánh sáng, hoặc tăng ngưỡng confidence trong `module/recognize.py`.

## Gợi ý bước tiếp theo
- Kiểm tra và cấu hình camera trên thiết bị mục tiêu.
- Chạy `python3 main-run.py` và thử thao tác `1/2/3/9` để xác nhận phần cứng và luồng.
- Nếu muốn, tôi có thể: thêm script CLI để train/run nhanh, hoặc tạo hướng dẫn cấu hình Raspberry Pi cụ thể.

---
File này được viết lại để tập trung vào cách dùng `main-run.py` và cấu trúc hiện tại của project.
Mô tả các module chính

- `module/capture.py`: Thu webcam, phát hiện khuôn mặt, lưu ảnh vào `data/<name>/`.
