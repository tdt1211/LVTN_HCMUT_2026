from RPLCD.i2c import CharLCD
import time
import datetime
import os
import json
import socket
import subprocess
import threading

import board

from module.keypad import read_keypad
from module.RFID import RFID_PN532_SPI
from module.recognize import quick_recognize
from app import app
from module.camera_manager import CameraManager
from module.buzzer import Buzzer

# ================= FLASK =================
def start_flask():
    # Chạy trên port khác hoặc đảm bảo app.py không chiếm Camera khi chưa cần
    app.run(host="0.0.0.0", port=5001, debug=False)

threading.Thread(target=start_flask, daemon=True).start()


# ================= CONSTANTS =================
AUTHORIZED_UID = "8731d595"

STATE_MENU = "MENU"
STATE_REGISTER = "REGISTER"
# Checkin/Checkout sẽ xử lý trực tiếp, không cần state treo

state = STATE_MENU
last_key = None
hold_start = None
reboot_input = ""
buzzer = Buzzer(pin=22)

STATE_REBOOT_AUTH = "REBOOT_AUTH"

REBOOT_PASS = "121103"
HOLD_TIME = 3.0  # seconds

# ================= HARDWARE =================
#rfid = RFID_PN532_SPI(cs=board.CE1, reset=None, debug=False)
lcd = CharLCD("PCF8574", 0x27, cols=20, rows=4)

def init_rfid(max_retry=5, delay=1.5):
    for attempt in range(1, max_retry + 1):
        try:
            print(f"[RFID] Init attempt {attempt}/{max_retry}")
            rfid = RFID_PN532_SPI(
                cs=board.CE1,
                reset=None,
                debug=False
            )
            # test nhẹ để chắc chắn SPI OK
            uid = rfid.read_uid(timeout=0.1)
            print("[RFID] Init success")
            return rfid
        except Exception as e:
            print(f"[RFID] Init failed: {e}")
            time.sleep(delay)

    print("[RFID] Init failed after retries")
    return None

rfid = None
time.sleep(2)   # cho SPI + PN532 ổn định sau boot
rfid = init_rfid()

def init_attendance_log(log_file="attendance_log.json"):
    if not os.path.exists(log_file):
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "name": "_SYSTEM_",
                    "datetime": "1970-01-01 00:00:00",
                    "type": "init"
                }
            ], f, indent=2)
        return

    with open(log_file, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
        except:
            logs = []

    if len(logs) == 0:
        logs.append({
            "name": "_SYSTEM_",
            "datetime": "1970-01-01 00:00:00",
            "type": "init"
        })
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
init_attendance_log()
# ================= LCD HELPERS =================
def lcd_reset():
    try:
        lcd.clear()
        lcd.home()
    except Exception as e:
        print("[ERROR] LCD reset failed:", e)
        lcd.clear()
        lcd.home()


def lcd_show(lines):
    lcd_reset()
    for i, line in enumerate(lines[:4]):
        lcd.cursor_pos = (i, 0)
        lcd.write_string(line[:20])

def do_reboot():
    lcd_show([
        "System rebooting",
        "Please wait...",
        "",
        ""
    ])
    time.sleep(1)
    subprocess.run(["sudo", "/sbin/reboot"])

camera = CameraManager()
camera.start()

# ================= ATTENDANCE =================
def can_write_attendance(name, entry_type, min_interval=1):
    if not name:
        return "INVALID_NAME"

    if not os.path.exists("attendance_log.json"):
        return "OK" if entry_type == "in" else "NOT_CHECKED_IN"

    with open("attendance_log.json", "r", encoding="utf-8") as f:
        logs = json.load(f)

    # tìm bản ghi cuối cùng của người này
    last_record = None
    for e in reversed(logs):
        if e["name"] == name:
            last_record = e
            break

    # chưa từng checkin
    if last_record is None:
        return "OK" if entry_type == "in" else "NOT_CHECKED_IN"

    last_time = datetime.datetime.strptime(
        last_record["datetime"], "%Y-%m-%d %H:%M:%S"
    )

    # chống spam
    #if (datetime.datetime.now() - last_time).total_seconds() < min_interval:
    #    return "TOO_FAST"

    # trùng trạng thái
    if last_record["type"] == entry_type:
        return "DUPLICATE"

    # checkout khi chưa checkin
    if last_record["type"] == "out" and entry_type == "out":
        return "NOT_CHECKED_IN"

    # hợp lệ: in → out hoặc out → in
    return "OK"

def write_attendance(name, entry_type, log_file="attendance_log.json"):
    now = datetime.datetime.now()
    entry = {
        "name": name,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "type": entry_type,
    }

    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    else:
        logs = []

    logs.append(entry)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def has_any_checkin(name, log_file="attendance_log.json"):
    if not os.path.exists(log_file):
        return False

    with open(log_file, "r", encoding="utf-8") as f:
        logs = json.load(f)

    for e in logs:
        if e["name"] == name and e["type"] == "in":
            return True

    return False

def is_log_empty(log_file="attendance_log.json"):
    if not os.path.exists(log_file):
        return True
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
        return len(logs) == 0
    except:
        return True

def get_last_state(name, log_file="attendance_log.json"):
    if not os.path.exists(log_file):
        return None

    with open(log_file, "r", encoding="utf-8") as f:
        logs = json.load(f)

    for e in reversed(logs):
        if e["name"] == name:
            return e["type"]  # "in" hoặc "out"

    return None

# ================= UI SCREENS =================
def show_menu():
    lcd_show([
        "1. Checkin",
        "2. Checkout",
        "3. Register",
        "MAIN MENU",
    ])


def show_register_wait():
    lcd_show([
        "Register mode",
        "Scan RFID...",
        "",
        "# to back",
    ])


def show_access(msg):
    lcd_show([
        msg,
        "",
        "# to back",
        "",
    ])


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No IP"


# ================= LOGIC HANDLERS =================
def process_recognition(mode):
    """
    Hàm xử lý logic nhận diện trọn gói
    mode: 'in' hoặc 'out'
    """
    print(f"[RECOGNITION] START | mode={mode}")
    # 1. Thông báo đang chạy
    title = "Checkin" if mode == 'in' else "Checkout"
    lcd_show([
        title,
        "Camera loading...",
        "Please wait...",
        ""
    ])
    print("[RECOGNITION] Calling quick_recognize()")

    # 2. Thực hiện nhận diện (Block code)
    # Tăng timeout lên một chút để đảm bảo camera khởi động kịp
    #name = quick_recognize(mode, num_samples=10, timeout=30)
    try:
        name = quick_recognize(mode, num_samples=10, timeout=10)
        print("[RECOGNITION] Result:", name)
    except Exception as e:
        print("[ERROR] quick_recognize failed:", e)
        name = None
    last_state = get_last_state(name)
    if mode == "out" and last_state != "in":
        lcd_show([
            "INVALID ACTION",
            f"{name}",
            "Not checked in",
            ""
        ])
        time.sleep(2)
        show_menu()
        return

    action = "CHECK-IN" if mode == "in" else "CHECK-OUT"
    result = can_write_attendance(name, mode)
    # 3. Hiển thị kết quả
    if name and name != "Unknow":
        if result == "OK":
            write_attendance(name, mode)
            if mode == "in":
                lcd_show([
                    f"{action} SUCCESS",
                    f"Hi, {name}",
                    "Have a nice day!",
                    "Saved!"
                ])
                buzzer.beep()
            elif mode == "out":
                lcd_show([
                    f"{action} SUCCESS",
                    f"Goodbye, {name}",
                    "See you later!",
                    "Saved!"
                ])
                buzzer.beep()

        else:
            ERROR_MAP = {
                "DUPLICATE": ["DUPLICATE ENTRY", name, f"Already {action}", ""],
                "NOT_CHECKED_IN": ["INVALID ACTION", name, "Not checked in", ""],
                #"TOO_FAST": ["PLEASE WAIT", name, "Try later", ""],
                "INVALID_NAME": ["ERROR", "Invalid user", "", ""]
            }
            lcd_show(ERROR_MAP.get(result, ["ERROR", "", "", ""]))
    else:
        lcd_show([
            "FAILED",
            "No face detected",
            "Try again!",
            ""
        ])
    print("[RECOGNITION] END")
    # 4. Quan trọng: Dừng màn hình 3s để người dùng đọc kết quả
    time.sleep(3)
    
    # 5. Tự động quay về Menu
    show_menu()


# ================= START =================
lcd_reset()
show_menu()

try:
    while True:
        print("[LOOP] Main loop alive | State:", state)
        key = read_keypad()
        if key:
            print("[KEYPAD] Key pressed:", key)

        # Logic chống dội phím (Debounce) cơ bản
        if key == last_key and key is not None:
            time.sleep(0.1)
            continue
        
        last_key = key

        # Nếu không nhấn gì thì bỏ qua vòng lặp
        if key is None:
            time.sleep(0.1)
            # Riêng chế độ REGISTER cần chạy liên tục để quét thẻ
            if state == STATE_REGISTER:
                pass # Để nó chạy xuống logic bên dưới
            else:
                continue

        # ===== HOLD * TO REBOOT =====
        if key == "*":
            if hold_start is None:
                hold_start = time.time()
            elif time.time() - hold_start >= HOLD_TIME:
                state = STATE_REBOOT_AUTH
                reboot_input = ""
                lcd_show([
                    "REBOOT MODE",
                    "Enter pass:",
                    "",
                    "# cancel"
                ])
                hold_start = None
            time.sleep(0.1)
            continue
        else:
            hold_start = None

        # ===== GLOBAL BACK BUTTON =====
        if key == "#":
            state = STATE_MENU
            show_menu()
            continue

        # ===== TRAINING MODE =====
        if key == "9":
            lcd_show([
                "Training mode",
                "Camera loading...",
                "Please wait...",
                ""
            ])
            try:
                from module.train import train_model
                train_model()
                lcd_show([
                    "Training complete",
                    "",
                    "Returning to menu",
                    ""
                ])
                time.sleep(2)
            except Exception as e:
                print("[ERROR] Training failed:", e)
                lcd_show([
                    "Training failed",
                    "",
                    "Returning to menu",
                    ""
                ])
                time.sleep(2)
            show_menu()
            continue
        # ===== STATE: MENU =====
        if state == STATE_MENU:
            if key == "1":
                print("[MENU] Checkin selected")
                # Thay vì đổi state, ta gọi hàm xử lý luôn
                process_recognition("in")
                # Sau khi xử lý xong, mặc định vẫn ở MENU

            elif key == "2":
                process_recognition("out")
                print("[MENU] Checkout selected")

            elif key == "3":
                state = STATE_REGISTER
                show_register_wait()

        # ===== STATE: REGISTER =====
        # Register cần loop để chờ quẹt thẻ, nên giữ nguyên logic state
        elif state == STATE_REGISTER:
            # Chỉ quét thẻ nếu không bấm phím nào (key is None)
            if key is None:
                try:
                    uid = rfid.read_uid(timeout=0.1) # Timeout ngắn để vòng lặp check key #
                except Exception as e:
                    print(f"[RFID] Error reading UID: {e}")
                    uid = None
                if uid:
                    if uid == AUTHORIZED_UID:
                        ip = get_ip()
                        lcd_show([
                            "AUTHORIZED",
                            f"IP: {ip}",
                            "Port: 5001",
                            "# to back"
                        ])
                        # Chờ bấm # để thoát, không tự thoát
                        # Có thể thêm vòng lặp con ở đây nếu muốn treo màn hình IP
                        while read_keypad() != "#":
                            time.sleep(0.1)
                        state = STATE_MENU
                        show_menu()
                    else:
                        lcd_show(["Access Denied", "", "Try again", "# to back"])
                        time.sleep(2)
                        show_register_wait()
        # ===== STATE: REBOOT AUTH =====
        elif state == STATE_REBOOT_AUTH:
            if key == "#":
                state = STATE_MENU
                show_menu()
                continue

            if key is not None and key.isdigit():
                reboot_input += key
                lcd_show([
                    "REBOOT MODE",
                    "Enter pass:",
                    "*" * len(reboot_input),
                    ""
                ])

                if len(reboot_input) >= len(REBOOT_PASS):
                    if reboot_input == REBOOT_PASS:
                        do_reboot()
                    else:
                        lcd_show([
                            "WRONG PASSWORD",
                            "",
                            "Access denied",
                            ""
                        ])
                        time.sleep(2)
                        state = STATE_MENU
                        show_menu()

        time.sleep(0.1)

except KeyboardInterrupt:
    lcd_show([
        "System Stopped",
        "Goodbye!",
        "",
        ""
    ])
    try:
        lcd.close()
    except:
        pass