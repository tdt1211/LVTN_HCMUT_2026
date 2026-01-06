# Hệ Thống Nhận Diện Khuôn Mặt & Chấm Công

Đây là một chương trình nhận diện khuôn mặt đơn giản để phục vụ mục đích chấm công.
Chương trình sử dụng ảnh thu từ webcam để thu thập dữ liệu, huấn luyện một mô hình nhận diện (OpenCV LBPH) và nhận diện trong thời gian thực để ghi nhận lịch sử chấm công.

**Ngôn ngữ:** Python

**Tổng quan nhanh:**
- Thêm nhân viên bằng cách chụp nhiều ảnh khuôn mặt và lưu vào thư mục `data/<TênNhânVien>/`.
- Huấn luyện mô hình từ dữ liệu trong `data/` và lưu file mô hình tại `models/face_model.yml`.
- Chạy chế độ nhận diện để chấm công; kết quả chấm công lưu vào `attendance_log.json`.

**Tính năng chính**
- Thu thập ảnh khuôn mặt cho từng nhân viên.
- Huấn luyện mô hình nhận diện khuôn mặt (LBPH).
- Nhận diện và ghi nhận thời gian chấm công.
- Xóa dữ liệu nhân viên khi cần.

**Yêu cầu (Dependencies)**
- Python 3.7+
- Thư viện Python (có trong `requirements.txt`): `opencv-python`, `numpy`, `psutil` ...
- Webcam tương thích hoặc Raspberry Pi Camera (nếu triển khai trên Pi).

Cài đặt nhanh (Windows / PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Nếu dùng Linux / Raspberry Pi (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Cấu trúc thư mục**

```
attendance_log.json         # Lịch sử chấm công (JSON)
main.py                     # Menu chính / entrypoint
requirements.txt
data/                       # Thư mục chứa ảnh theo từng nhân viên
	<PersonName>/           # e.g. data/TranHau/
models/                     # Mô hình và label map
	face_model.yml
	label_map.txt
module/                     # Các module chức năng
	capture.py              # Thu thập ảnh
	train.py                # Huấn luyện model
	recognize.py            # Nhận diện + chấm công
	delete.py               # Xóa dữ liệu nhân viên
```

Hướng dẫn sử dụng

1) Thêm người mới (chụp ảnh):

```powershell
py main.py
# Chọn 1 -> nhập tên nhân viên -> hệ thống sẽ mở webcam và lưu ảnh vào data/<Tên>/
```

2) Huấn luyện model:

```powershell
py main.py
# Chọn 2 -> chương trình sẽ quét thư mục `data/` và huấn luyện model, lưu tại `models/face_model.yml`
```

3) Nhận diện & chấm công:

```powershell
py main.py
# Chọn 3 -> mở webcam, nhận diện khuôn mặt realtime và ghi vào `attendance_log.json`
```

4) Xóa nhân viên:

```powershell
py main.py
# Chọn 4 -> nhập tên nhân viên -> xóa thư mục dữ liệu và cập nhật label map
```

Mô tả các module chính
- `module/capture.py`: Thu webcam, phát hiện khuôn mặt, lưu ảnh vào `data/<name>/`.
- `module/train.py`: Đọc ảnh từ `data/`, ánh xạ label, huấn luyện LBPH face recognizer, lưu `face_model.yml` và `label_map.txt`.
- `module/recognize.py`: Nạp model và label map, mở webcam, nhận diện khuôn mặt, ghi thời gian chấm công vào `attendance_log.json`.
- `module/delete.py`: Xóa dữ liệu của một nhân viên (thư mục trong `data/`) và cập nhật label map nếu cần.

Định dạng và tệp kết quả
- `attendance_log.json`: lưu danh sách các bản ghi chấm công theo định dạng JSON (tên, thời gian, kết quả nhận diện).
- `models/face_model.yml`: file mô hình OpenCV LBPH.
- `models/label_map.txt`: ánh xạ giữa chỉ số label và tên nhân viên.

Triển khai trên Raspberry Pi — Đánh giá khả quan

- Khả thi: Chương trình này dùng phương pháp LBPH (OpenCV) và xử lý bằng CPU, nên VÔ CÙNG KHẢ THI để chạy trên Raspberry Pi, đặc biệt là dòng Raspberry Pi 4 (RAM >= 2GB, tốt nhất 4GB trở lên).
- Khuyến nghị phần cứng: Raspberry Pi 4 (4GB), nguồn ổn định, camera chất lượng (Pi Camera v2 hoặc webcam USB), thẻ microSD tốc độ cao hoặc SSD USB để giảm I/O.
- Tối ưu hoá khi chuyển sang Pi:
	- Cài đặt `opencv-python` có thể chậm/khó trên Pi; cân nhắc cài từ nguồn hoặc dùng gói `opencv-contrib-python` đã biên dịch cho Pi.
	- Giảm độ phân giải khung hình (ví dụ 320x240) để cải thiện FPS và giảm tải CPU.
	- Giảm tần suất nhận diện (ví dụ chỉ nhận diện mỗi 0.5–1s) để tiết kiệm CPU.
	- Thực hiện huấn luyện (train) trên máy mạnh hơn (PC) rồi chỉ deploy file `models/face_model.yml` lên Pi, vì huấn luyện có thể tiêu tốn nhiều tài nguyên.
	- Nếu cần nhận diện nhanh và chính xác hơn, cân nhắc dùng bộ tăng tốc phần cứng (Google Coral USB TPU) hoặc chuyển sang model nhẹ chạy trên TFLite.
- Kết luận ngắn: Với các tối ưu cơ bản và Pi 4 trở lên, khả năng chạy realtime cho mục đích chấm công (thay vì ứng dụng latency thấp) là khả quan. Huấn luyện trực tiếp trên Pi không được khuyến nghị trừ khi số lượng ảnh rất nhỏ.

Gợi ý khắc phục sự cố
- Nếu không nhận camera: kiểm tra quyền truy cập thiết bị, đúng index camera hoặc driver trên Pi.
- Nếu OpenCV gặp lỗi khi cài: thử cài các phụ thuộc hệ thống (`libatlas`, `libjasper`, `libqt`...) hoặc cài OpenCV từ nguồn.
- Nếu kết quả nhận diện kém: đảm bảo đủ ảnh (góc nhìn, ánh sáng), tăng lượng ảnh cho mỗi người, chuẩn hoá độ phân giải ảnh.

Liên hệ / Bản quyền
- Tập tin mẫu này là tài liệu nội bộ cho dự án.
- Nếu cần hỗ trợ triển khai lên Raspberry Pi hoặc cải tiến mô hình, có thể mở issue hoặc liên hệ tác giả dự án.

