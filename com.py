# XBee Communication wrapper for Kevinbot v3
import logging
import time
import serial
from serial.serialutil import SerialException
import xbee as xbee_com
import platform


# detect if an actual raspberry pi is being used
def is_pi():
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
    except KeyError:
        PORT = "/dev/ttyS0"
else:
    try:
        import json
        with open("settings.json", "r") as f:
            settings = json.load(f)
            if platform.system() == "Windows":
                PORT = settings["ports"]["win_port"]
            else:
                PORT = settings["ports"]["linux_port"]
    except KeyError:
        PORT = "/dev/ttyS0"

BAUD = 230400

xb = None
ser = None


def init(callback=None):
    global xb, ser
    try:
        ser = serial.Serial(PORT, BAUD)
    except SerialException:
        try:
            # noinspection PyUnresolvedReferences
            import sys
            # noinspection PyUnresolvedReferences,PyPackageRequirements
            from qtpy.QtWidgets import QApplication, QMessageBox, QInputDialog
            _ = QApplication(sys.argv)
            # noinspection PyTypeChecker
            resp, _ = QInputDialog.getText(None, f"Port Not Found", "Type the correct port")
            ser = serial.Serial(resp, BAUD)
        except ImportError:
            print(f"Port \"{PORT}\" Not Found")
    xb = xbee_com.XBee(ser, escaped=False, callback=callback)


def _send_data(data):
    # noinspection PyUnresolvedReferences
    xb.send("tx", dest_addr=b'\x00\x00', data=bytes("{}\r".format(data), 'utf-8'))


def txstr(string):
    logging.debug("Sent: " + string)
    _send_data(string)


def txcv(cmd, val, delay=0):
    # see if val is a list or a string
    if isinstance(val, list) or isinstance(val, tuple):
        val = str(val).strip('[]()').replace(', ', ',')
        
    txstr(cmd + "=" + str(val))
    time.sleep(delay)


def txmot(vals):
    # send motor values to the xbee
    txcv("left_us", vals[0])
    txcv("right_us", vals[1])


def txstop():
    txstr("stop")


def txshut():
    txstr("shutdown")
