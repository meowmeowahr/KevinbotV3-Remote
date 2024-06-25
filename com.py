# XBee Communication wrapper for Kevinbot v3
import os
import time
from typing import Iterable, Union, Callable, Any, Optional

import serial
from serial.serialutil import SerialException
import xbee as xbee_com
import platform

import log

import sys
# noinspection PyUnresolvedReferences,PyPackageRequirements
from qtpy.QtWidgets import QApplication, QMessageBox, QInputDialog

logger = log.setup(os.path.basename(__file__).rstrip(".py"), log.AUTO)

# detect if an actual Raspberry Pi is being used
def is_pi() -> bool:
    try:
        if "Raspberry" in open("/sys/firmware/devicetree/base/model", "r").readline():
            return True
        else:
            return False
    except IOError:
        return False


if is_pi():
    try:
        import json

        with open("settings.json", "r") as f:
            settings = json.load(f)
        PORT = settings["ports"]["pi_port"]
        logger.debug(f"Using Raspberry Pi port, {PORT}")
    except KeyError:
        PORT = "/dev/ttyS0"
        logger.debug(f"Using default port, {PORT}")
else:
    try:
        import json

        with open("settings.json", "r") as f:
            settings = json.load(f)
            if platform.system() == "Windows":
                PORT = settings["ports"]["win_port"]
                logger.debug(f"Using Windows port, {PORT}")
            else:
                PORT = settings["ports"]["linux_port"]
                logger.debug(f"Using Linux port, {PORT}")
    except KeyError:
        PORT = "/dev/ttyS0"
        logger.debug(f"Using default port, {PORT}")

BAUD: int = 460800

xb: Optional[xbee_com.XBee] = None
ser: Optional[serial.Serial] = None


def init(callback: Optional[Callable[[str], Any]] =None, qapp: QApplication=None):
    global xb, ser
    try:
        ser = serial.Serial(PORT, BAUD)
    except (SerialException, FileNotFoundError):
        try:
            if not qapp:
                qapp = QApplication(sys.argv)
            # noinspection PyTypeChecker
            resp, _ = QInputDialog.getText(
                None, f"Port Not Found", "Type the correct port"
            )
            if not resp.lower() == "dummy":
                ser = serial.Serial(resp, BAUD)
            else:
                ser = None
                logger.debug("Activated dummy port mode")
        except ImportError:
            logger.error(f'Port "{PORT}" Not Found')
    if ser:
        xb = xbee_com.XBee(ser, escaped=False, callback=callback)


def _send_data(data: str):
    # noinspection PyUnresolvedReferences
    if xb:
        xb.send("tx", dest_addr=b"\x00\x00", data=bytes("{}\r".format(data), "utf-8"))


def txstr(data: str):
    logger.trace("Sent: " + data)
    _send_data(data)


def txcv(cmd: str, val: str, delay: int=0):
    # see if val is a list or a string
    if isinstance(val, list) or isinstance(val, tuple):
        val = str(val).strip("[]()").replace(", ", ",")

    txstr(cmd + "=" + str(val))
    time.sleep(delay)


def txmot(vals: Union[list[int, int], tuple[int, int]]):
    # send motor values to the xbee
    txcv("left_motor", vals[0])
    txcv("right_motor", vals[1])


def txstop():
    txstr("stop")


def tx_e_stop():
    txstr("request.estop")
