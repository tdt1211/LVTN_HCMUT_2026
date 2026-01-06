import time
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI


class RFID_PN532_SPI:
    def __init__(self, cs=board.CE1, reset=None, debug=False):
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.cs_pin = digitalio.DigitalInOut(cs)

        self.reset_pin = None
        if reset is not None:
            self.reset_pin = digitalio.DigitalInOut(reset)

        time.sleep(0.3)

        self.pn532 = PN532_SPI(
            self.spi,
            self.cs_pin,
            reset=self.reset_pin,
            debug=debug
        )

        time.sleep(0.3)

        ic, ver, rev, support = self.pn532.firmware_version
        print(f"[PN532] Firmware {ver}.{rev}")

        self.pn532.SAM_configuration()

        # chống đọc trùng
        self._last_uid = None
        self._last_time = 0
        self._cooldown = 2.0  # giây

    def read_uid(self, timeout=1.0):
        """
        Timeout mềm + không treo
        """
        start = time.time()

        while time.time() - start < timeout:
            uid = self.pn532.read_passive_target(timeout=0.1)

            if uid:
                uid_hex = uid.hex()
                now = time.time()

                if uid_hex == self._last_uid and (now - self._last_time) < self._cooldown:
                    return None

                self._last_uid = uid_hex
                self._last_time = now
                return uid_hex

            time.sleep(0.05)  # nhả SPI

        return None
