import cv2
import os
import time
import threading
from typing import Optional
from module.camera_manager import CameraManager
from module.train import train_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HAAR_FRONT = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
HAAR_PROFILE = os.path.join(BASE_DIR, "haarcascade_profileface.xml")

FRAME_SIZE = (640, 480)
JPEG_QUALITY = 80

FRONT_COUNT = 20
LEFT_COUNT = 15
RIGHT_COUNT = 15
CAPTURE_DELAY = 0.4


class Session:
    def __init__(self, save_path="data"):
        self.save_path = save_path
        self.camera = CameraManager()

        self.name: Optional[str] = None
        self.status = "idle"
        self.message = ""

        self.counts = {"FRONT": 0, "LEFT": 0, "RIGHT": 0}
        self.targets = {
            "FRONT": FRONT_COUNT,
            "LEFT": LEFT_COUNT,
            "RIGHT": RIGHT_COUNT
        }

        self._frame = None
        self._lock = threading.Lock()
        self._reader_running = False
        self._reader_thread = None

        self.frontal = cv2.CascadeClassifier(HAAR_FRONT)
        self.profile = cv2.CascadeClassifier(HAAR_PROFILE)

        if self.frontal.empty() or self.profile.empty():
            raise RuntimeError("Failed to load Haar cascades")

    # ===== READER =====
    def start_reader(self):
        if self._reader_running:
            return

        self._reader_running = True
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True
        )
        self._reader_thread.start()

    def _reader_loop(self):
        while self._reader_running:
            frame = self.camera.capture()
            if frame is not None:
                with self._lock:
                    self._frame = frame.copy()
            time.sleep(0.03)

    def stop(self):
        self._reader_running = False
        if self._reader_thread:
            self._reader_thread.join(timeout=2)
            self._reader_thread = None

    # ===== PUBLIC =====
    def start_preview(self, name: str):
        self.name = name
        self.status = "preview"
        self.message = "Ready"
        self.counts = {"FRONT": 0, "LEFT": 0, "RIGHT": 0}
        self.start_reader()

    def get_frame_jpeg(self):
        with self._lock:
            frame = None if self._frame is None else self._frame.copy()

        if frame is None:
            return None

        if self.message:
            cv2.putText(
                frame, self.message, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0, (0, 0, 255), 2
            )

        ret, buf = cv2.imencode(
            ".jpg", frame,
            [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        )
        return buf.tobytes() if ret else None

    # ===== CAPTURE =====
    def start_capture(self):
        if self.status == "capturing" or not self.name:
            return

        self.status = "capturing"
        save_dir = os.path.join(self.save_path, self.name)
        os.makedirs(save_dir, exist_ok=True)

        idx = 0
        last = 0
        stage = "FRONT"

        while True:
            with self._lock:
                frame = None if self._frame is None else self._frame.copy()

            if frame is None:
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            now = time.time()
            if now - last < CAPTURE_DELAY:
                continue

            if stage == "FRONT":
                self.message = f"Look straight {self.counts['FRONT']}/{FRONT_COUNT}"
                faces = self.frontal.detectMultiScale(gray, 1.2, 5)
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    cv2.imwrite(f"{save_dir}/{idx+1}.jpg", gray[y:y+h, x:x+w])
                    idx += 1
                    self.counts["FRONT"] += 1
                    last = now
                    if self.counts["FRONT"] >= FRONT_COUNT:
                        stage = "LEFT"

            elif stage == "LEFT":
                self.message = f"Turn LEFT {self.counts['LEFT']}/{LEFT_COUNT}"
                faces = self.profile.detectMultiScale(gray, 1.2, 4)
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    cv2.imwrite(f"{save_dir}/{idx+1}.jpg", gray[y:y+h, x:x+w])
                    idx += 1
                    self.counts["LEFT"] += 1
                    last = now
                    if self.counts["LEFT"] >= LEFT_COUNT:
                        stage = "RIGHT"

            elif stage == "RIGHT":
                self.message = f"Turn RIGHT {self.counts['RIGHT']}/{RIGHT_COUNT}"
                flipped = cv2.flip(gray, 1)
                faces = self.profile.detectMultiScale(flipped, 1.2, 4)
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    x0 = gray.shape[1] - x - w
                    cv2.imwrite(f"{save_dir}/{idx+1}.jpg", gray[y:y+h, x0:x0+w])
                    idx += 1
                    self.counts["RIGHT"] += 1
                    last = now
                    if self.counts["RIGHT"] >= RIGHT_COUNT:
                        break

            #time.sleep(0.03)

        self.status = "done"
        self.message = f"Captured {idx} images"
        #train_model()
        print("[CAPTURE] Loop finished")
        self.status = "training"
        self.message = "Training model..."

        print("[TRAIN] Starting training...")
        train_model()
        print("[TRAIN] Done")

        self.status = "done"
        self.message = "Training completed"



_GLOBAL_SESSION: Optional[Session] = None

def get_global_session() -> Session:
    global _GLOBAL_SESSION
    if _GLOBAL_SESSION is None:
        _GLOBAL_SESSION = Session()
    return _GLOBAL_SESSION
