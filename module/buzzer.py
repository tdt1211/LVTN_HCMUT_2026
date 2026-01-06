import RPi.GPIO as GPIO
import time

class Buzzer:
    def __init__(self, pin=22):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def beep(self, duration=0.3):
        """
        Kêu buzzer trong duration (giây)
        """
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(self.pin, GPIO.LOW)

    def beep_times(self, times=1, duration=0.1, gap=0.1):
        """
        Kêu nhiều lần
        """
        for _ in range(times):
            self.beep(duration)
            time.sl
