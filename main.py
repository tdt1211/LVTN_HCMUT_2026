# main.py
from module.capture import get_global_session
from module.train import train_model
#from module.recognize import recognize, quick_recognize
from module.delete import delete_employee

import psutil, os, json, datetime

def show_resource_usage():
    process = psutil.Process(os.getpid())
    print("RAM usage (MB):", process.memory_info().rss / (1024 * 1024))

def menu():
    print("1. Thêm người mới")
    print("2. Huấn luyện model")
    print("3. Check-in (thủ công)")
    print("4. Check-out (thủ công)")
    print("5. Chấm công (nhận diện)")
    print("6. Xóa nhân viên")
    print("0. Thoát")


def write_attendance(name, entry_type, log_file='attendance_log.json'):
    now = datetime.datetime.now()
    entry = {
        'name': name,
        'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
        'type': entry_type
    }
    # load
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
    else:
        logs = []
    logs.append(entry)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    if entry_type == 'out':
        # compute duration from last 'in' today
        today = now.strftime('%Y-%m-%d')
        last_in = None
        for e in reversed(logs[:-1]):
            if e.get('name') == name and e.get('type') == 'in' and e.get('datetime', '').startswith(today):
                try:
                    last_in = datetime.datetime.strptime(e['datetime'], '%Y-%m-%d %H:%M:%S')
                    break
                except Exception:
                    last_in = None
        if last_in:
            duration = now - last_in
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            print(f"[INFO] {name} worked {hours}h {minutes}m today")

while True:
    show_resource_usage()
    menu()
    print("CPU (%):", psutil.cpu_percent(interval=0.2))
    print("RAM:", psutil.Process(os.getpid()).memory_info().rss / (1024*1024), "MB")
    choice = input("Chọn chức năng: ")
    if choice == "1":
        name = input("Nhập tên nhân viên: ")
        capture_images(name)
    elif choice == "2":
        train_model()
        '''
    elif choice == "3":
        print('Bắt đầu quick recognition để check-in...')
        name = quick_recognize('in', num_samples=10, timeout=20)
        if name:
            print(f'Check-in: {name}')
        else:
            print('Không xác định được người check-in.')
    elif choice == "4":
        print('Bắt đầu quick recognition để check-out...')
        name = quick_recognize('out', num_samples=10, timeout=20)
        if name:
            print(f'Check-out: {name}')
        else:
            print('Không xác định được người check-out.')
    elif choice == "5":
        quick_recognize()
    '''
    elif choice == "6":
        name = input("Nhập tên nhân viên cần xóa: ")
        delete_employee(name)
    elif choice == "0":
        break
    else:
        print("Lựa chọn không hợp lệ.")

