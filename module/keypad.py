# keypad.py
import RPi.GPIO as GPIO
import time
GPIO.setwarnings(False)

# Row và Col theo GPIO bạn cung cấp
ROWS = [5, 6, 13, 26]    # R1-R4
COLS = [16, 12, 17]       # C1-C3

KEYS = [
    ['1','2','3'],
    ['4','5','6'],
    ['7','8','9'],
    ['*','0','#']
]

GPIO.setmode(GPIO.BCM)


# Setup rows as output (default HIGH)
for row in ROWS:
    GPIO.setup(row, GPIO.OUT)
    GPIO.output(row, GPIO.HIGH)

# Setup cols as input pull-up
for col in COLS:
    GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def read_keypad():
    for r_idx, row in enumerate(ROWS):
        GPIO.output(row, GPIO.LOW)  # active row

        for c_idx, col in enumerate(COLS):
            if GPIO.input(col) == GPIO.LOW:
                time.sleep(0.25)  # debounce
                GPIO.output(row, GPIO.HIGH)
                return KEYS[r_idx][c_idx]

        GPIO.output(row, GPIO.HIGH)
    return None


# Demo chạy riêng
if __name__ == "__main__":
    try:
        while True:
            key = read_keypad()
            if key:
                print(f"Key Pressed: {key}")
            time.sleep(0.05)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Exiting")
    finally:
        GPIO.cleanup()

