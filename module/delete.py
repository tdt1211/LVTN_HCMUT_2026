import os
import shutil

def delete_employee(name, data_path="data"):
    emp_path = os.path.join(data_path, name)
    if os.path.exists(emp_path) and os.path.isdir(emp_path):
        shutil.rmtree(emp_path)
        print(f"[INFO] Đã xóa nhân viên {name} và toàn bộ dữ liệu.")
    else:
        print(f"[WARN] Không tìm thấy nhân viên {name}.")
