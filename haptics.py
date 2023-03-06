from PyQt5.QtWidgets import QPushButton, QToolButton
from utils import is_pi
import time
import threading

try:
    import RPi.GPIO as GPIO
except ImportError:
    pass
    # from RPiSim.GPIO import GPIO as io
    # do not use GPIO sim

_pin = None


def init(pin):
    global _pin
    _pin = pin
    if is_pi():
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(pin, GPIO.OUT)
    else:
        print(f"Haptics Initialized at Pin: {pin}")
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(pin, GPIO.OUT)
        except (TypeError, NameError):
            pass


def haptic(duration=0.02):
    if is_pi():
        GPIO.output(_pin, 1)
        time.sleep(duration)
        GPIO.output(_pin, 0)
    else:
        try:
            GPIO.output(_pin, 1)
            time.sleep(duration)
            GPIO.output(_pin, 0)
        except (TypeError, NameError):
            pass


class HPushButton(QPushButton):
    def __init__(self, name=""):
        super(HPushButton, self).__init__()
        self.pressed.connect(self._run_haptic)
        self.setText(name)

    @staticmethod
    def _run_haptic():
        thread = threading.Thread(target=haptic)
        thread.start()


class HToolButton(QToolButton):
    def __init__(self):
        super(HToolButton, self).__init__()
        self.pressed.connect(self._run_haptic)

    @staticmethod
    def _run_haptic():
        thread = threading.Thread(target=haptic)
        thread.start()
