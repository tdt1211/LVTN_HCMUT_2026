from picamera2 import Picamera2
import time

class CameraManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.picam2 = None
        return cls._instance

    def start(self):
        if self.picam2 is None:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            time.sleep(1)
            print("[CAMERA] Started")

    def capture(self):
        if self.picam2:
            return self.picam2.capture_array()
        return None

    def stop(self):
        if self.picam2:
            self.picam2.close()
            self.picam2 = None
            print("[CAMERA] Stopped")
