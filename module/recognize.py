# module/recognize.py
import cv2
import datetime
import json
import os
from picamera2 import Picamera2
import time
from module.camera_manager import CameraManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HAAR_FACE = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")


def load_label_map(path="models/label_map.txt"):
    with open(path, "r") as f:
        return {int(line.split(":")[0]): line.strip().split(":")[1] for line in f}
'''
def recognize(model_path="models/face_model.yml"):
    import time
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    labels = load_label_map()
    #picam2 = Picamera2()
    config = picam2.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)

    picam2.start()
    time.sleep(1)
    cam = picam2.capture_array()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print("[INFO] Starting face recognition. Press ESC to quit.")
    last_checkin = {}
    log_file = "attendance_log.json"
    # Load old log if exists
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                attendance_log = json.load(f)
            except Exception:
                attendance_log = []
    else:
        attendance_log = []
    while True:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.1, 4)  # tăng độ nhạy: giảm scaleFactor và minNeighbors

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            id_, confidence = recognizer.predict(face)
            now = datetime.datetime.now()
            if confidence < 80:  # tăng ngưỡng để nhận diện dễ hơn
                    name = labels.get(id_, "Unknown")
                    last_time = last_checkin.get(name)
                    if name != "Unknown":
                        if not last_time or (now - last_time).total_seconds() >= 30:
                            last_checkin[name] = now
                            cv2.putText(img, f"{name} ({int(confidence)}%)", (x, y-10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            print(f"[ATTENDANCE] {now.strftime('%Y-%m-%d %H:%M:%S')}: {name}")
                            # Determine check-in or check-out based on today's records
                            today_str = now.strftime('%Y-%m-%d')
                            # filter entries for this user and date
                            user_today = [e for e in attendance_log if e.get('name') == name and e.get('datetime', '').startswith(today_str)]
                            entry_type = 'in'
                            if user_today:
                                # look at last entry type; if last was 'in', then this is 'out'
                                last_entry = user_today[-1]
                                if last_entry.get('type') == 'in':
                                    entry_type = 'out'

                            entry = {
                                'name': name,
                                'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                                'type': entry_type
                            }
                            attendance_log.append(entry)
                            # if it's a checkout, compute duration from last check-in
                            if entry_type == 'out':
                                # find last 'in' for today
                                last_in = None
                                for e in reversed(attendance_log[:-1]):
                                    if e.get('name') == name and e.get('type') == 'in' and e.get('datetime', '').startswith(today_str):
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

                            with open(log_file, "w", encoding="utf-8") as f:
                                json.dump(attendance_log, f, ensure_ascii=False, indent=2)
                        else:
                            cv2.putText(img, f"{name}", (x, y-10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        cv2.putText(img, "Unknown", (x, y-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            else:
                cv2.putText(img, "Unknown", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 255, 0), 2)

        cv2.imshow('Recognition', img)
        if cv2.waitKey(1) == 27:
            break

    #cam.release()
    #cv2.destroyAllWindows()
'''

def quick_recognize(mode='in', num_samples=10, timeout=20, model_path="models/face_model.yml"):
    """Quick recognition session: collect `num_samples` predictions (or until timeout seconds),
    choose the most frequent recognized name and write a single attendance entry with given mode ('in' or 'out').
    Returns the recognized name or None.
    """
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(model_path)
    except Exception as e:
        print('[ERROR] Could not read model:', e)
        return None
    labels = load_label_map()
    #picam2 = Picamera2()
    #config = picam2.create_still_configuration(
    #    main={"size": (640, 480), "format": "RGB888"}
    #)
    #picam2.configure(config)

    #picam2.start()
    #time.sleep(1)
    #cam = picam2.capture_array()
    detector = cv2.CascadeClassifier(HAAR_FACE)
    camera = CameraManager()
    counts = {}
    total = 0
    start = datetime.datetime.now()

    print(f"[INFO] Quick recognize for {mode}: collecting up to {num_samples} samples...")
    while total < num_samples and (datetime.datetime.now() - start).total_seconds() < timeout:
        #img = cam
        img = camera.capture()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            try:
                id_, confidence = recognizer.predict(face)
            except Exception:
                continue
                
            if confidence < 80:
                name = labels.get(id_, None)
                if name and name != 'Unknown':
                    counts[name] = counts.get(name, 0) + 1
                    total += 1
            else:
                # count as unknown (ignored)
                total += 1
            # small delay
            if total >= num_samples:
                break

    #cam.release()
    #cv2.destroyAllWindows()

    if not counts:
        print('[INFO] No recognized person found in quick session.')
        return None

    # choose most frequent
    name = max(counts.items(), key=lambda x: x[1])[0]
    '''
    now = datetime.datetime.now()
    log_file = 'attendance_log.json'
    # load existing
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                attendance_log = json.load(f)
        except Exception:
            attendance_log = []
    else:
        attendance_log = []

    entry = {'name': name, 'datetime': now.strftime('%Y-%m-%d %H:%M:%S'), 'type': mode}
    attendance_log.append(entry)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(attendance_log, f, ensure_ascii=False, indent=2)

    if mode == 'out':
        # compute duration from last 'in' today
        today = now.strftime('%Y-%m-%d')
        last_in = None
        for e in reversed(attendance_log[:-1]):
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
    #picam2.close()
    '''
    print(f"[INFO] Quick recognize result: {name} (mode={mode})")
    return name