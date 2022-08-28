# XBee Communication wrapper for Kevinbot v3
import time
import serial
from serial.serialutil import SerialException
import xbee as xbee_com


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
    PORT = "/dev/ttyS0"
else:
    PORT = '/dev/ttyUSB0'

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
            # noinspection PyUnresolvedReferences
            from PyQt5.QtWidgets import QApplication, QMessageBox
            _ = QApplication(sys.argv)
            mess = QMessageBox()
            mess.setText(f"Port {PORT} Not Found")
            mess.setStandardButtons(QMessageBox.Ok)
            mess.exec_()
        except ImportError:
            print(f"Port \"{PORT}\" Not Found")
    xb = xbee_com.XBee(ser, escaped=False, callback=callback)


def _send_data(data):
    # noinspection PyUnresolvedReferences
    xb.send("tx", dest_addr=b'\x00\x00', data=bytes("{}\r".format(data), 'utf-8'))


def txstr(string):
    print("Sent: " + string)
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


def txshut():
    txstr("shutdown")
