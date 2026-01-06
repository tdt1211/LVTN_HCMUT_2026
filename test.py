# main_fsm.py
import time
import os
import json
import datetime
import psutil

from module.train import train_model
from module.recognize import quick_recognize
from module.delete import delete_employee
from module.capture import get_global_session


# =========================
# FSM STATES
# =========================
STATE_MENU      = "MENU"
STATE_REGISTER  = "REGISTER"
STATE_TRAIN     = "TRAIN"
STATE_CHECKIN   = "CHECKIN"
STATE_CHECKOUT  = "CHECKOUT"
STATE_DELETE    = "DELETE"
STATE_EXIT      = "EXIT"

state = STATE_MENU


# =========================
# UTILS
# =========================
def show_resource_usage():
    process = psutil.Process(os.getpid())
    ram_mb = process.memory_info().rss / 1024 / 1024
    print(f"[SYSTEM] RAM usage: {ram_mb:.1f} MB")


def show_menu():
    print("\n========= MENU =========")
    print("1. Register new employee")
    print("2. Train recognition model")
    print("3. Check-in (face recognition)")
    print("4. Check-out (face recognition)")
    print("5. Delete employee")
    print("0. Exit")
    print("========================")


def write_attendance(name, entry_type, log_file="attendance_log.json"):
    now = datetime.datetime.now()
    entry = {
        "name": name,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "type": entry_type
    }

    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append(entry)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# =========================
# FSM ACTIONS (ONE-SHOT)
# =========================
def action_register():
    name = input("Enter employee name: ").strip()
    if not name:
        print("[WARNING] Invalid name")
        return
    capture_images(name)


def action_train():
    print("[INFO] Training model...")
    train_model()


def action_checkin():
    print("[INFO] Starting CHECK-IN recognition...")
    name = quick_recognize("in", num_samples=10, timeout=20)

    if name and name != "Unknow":
        print(f"[SUCCESS] Check-in successful: {name}")
        write_attendance(name, "in")
    else:
        print("[ERROR] Face recognition failed")


def action_checkout():
    print("[INFO] Starting CHECK-OUT recognition...")
    name = quick_recognize("out", num_samples=10, timeout=20)

    if name and name != "Unknow":
        print(f"[SUCCESS] Check-out successful: {name}")
        write_attendance(name, "out")
    else:
        print("[ERROR] Face recognition failed")


def action_delete():
    name = input("Enter employee name to delete: ").strip()
    if not name:
        print("[WARNING] Invalid name")
        return
    delete_employee(name)


# =========================
# FSM LOOP
# =========================
while state != STATE_EXIT:
    show_resource_usage()

    if state == STATE_MENU:
        show_menu()
        choice = input("Select option: ").strip()

        if choice == "1":
            state = STATE_REGISTER
        elif choice == "2":
            state = STATE_TRAIN
        elif choice == "3":
            state = STATE_CHECKIN
        elif choice == "4":
            state = STATE_CHECKOUT
        elif choice == "5":
            state = STATE_DELETE
        elif choice == "0":
            state = STATE_EXIT
        else:
            print("[WARNING] Invalid selection")

    elif state == STATE_REGISTER:
        action_register()
        state = STATE_MENU

    elif state == STATE_TRAIN:
        action_train()
        state = STATE_MENU

    elif state == STATE_CHECKIN:
        action_checkin()     # called ONCE
        state = STATE_MENU

    elif state == STATE_CHECKOUT:
        action_checkout()    # called ONCE
        state = STATE_MENU

    elif state == STATE_DELETE:
        action_delete()
        state = STATE_MENU

    time.sleep(0.2)

print("Program terminated.")
