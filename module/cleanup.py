import json
import os
from datetime import datetime

LOG_FILE = "attendance_log.json"
TIME_FMT = "%Y-%m-%d %H:%M:%S"


def cleanup_attendance_log(log_file=LOG_FILE):
    if not os.path.exists(log_file):
        return False

    with open(log_file, "r", encoding="utf-8") as f:
        logs = json.load(f)

    # Giữ system init
    system_logs = [
        e for e in logs
        if e.get("name") == "_SYSTEM_" and e.get("type") == "init"
    ]

    # Gom theo user + ngày
    grouped = {}
    for e in logs:
        if e["name"] == "_SYSTEM_":
            continue

        dt = datetime.strptime(e["datetime"], TIME_FMT)
        day = dt.date().isoformat()  # YYYY-MM-DD
        key = (e["name"], day)

        grouped.setdefault(key, []).append(e)

    result_logs = system_logs[:]

    for (name, day), entries in grouped.items():
        entries.sort(
            key=lambda x: datetime.strptime(x["datetime"], TIME_FMT)
        )

        last_in = None
        last_pair = None

        for e in entries:
            if e["type"] == "in":
                last_in = e
            elif e["type"] == "out" and last_in:
                last_pair = (last_in, e)
                last_in = None

        # Chỉ giữ 1 cặp in-out cuối của NGÀY ĐÓ
        if last_pair:
            result_logs.extend(last_pair)

    # Sort toàn bộ theo thời gian
    result_logs.sort(
        key=lambda x: datetime.strptime(x["datetime"], TIME_FMT)
    )

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result_logs, f, ensure_ascii=False, indent=2)

    return True
