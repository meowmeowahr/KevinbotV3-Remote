from PyQt5.QtWidgets import QPushButton, QToolButton
from utils import is_pi
import time
import threading

try:
    # noinspection PyPep8Naming
    import RPi.GPIO as io
except ImportError:
    # noinspection PyPep8Naming
    try:
        # from RPiSim.GPIO import GPIO as io
        pass  # do not use GPIO sim
    except ImportError:
        pass

_pin = None


def init(pin):
    global _pin
    _pin = pin
    if is_pi():
        io.setmode(io.BCM)
        io.setwarnings(False)
        io.setup(pin, io.OUT)
    else:
        print(f"Haptics Initialized at Pin: {pin}")
        try:
            io.setmode(io.BCM)
            io.setwarnings(False)
            io.setup(pin, io.OUT)
        except (TypeError, NameError):
            pass


def haptic(duration=0.02):
    if is_pi():
        io.output(_pin, 1)
        time.sleep(duration)
        io.output(_pin, 0)
    else:
        try:
            io.output(_pin, 1)
            time.sleep(duration)
            io.output(_pin, 0)
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
