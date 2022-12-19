#!/usr/bin/python

from xbee.backend.base import TimeoutException as XBee_Timeout
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from settings import SETTINGS
from utils import load_theme, detect_dark
import qtawesome as qta
import threading
import strings
import sys
import com
from queue import Queue

__version__ = "v1.0.0"
__author__ = "Kevin Ahr"

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

command_queue = Queue()


class Window(QWidget):
    # noinspection PyArgumentList
    def __init__(self, *args):
        QWidget.__init__(self, *args)

        load_theme(self, SETTINGS["window_properties"]["theme"])

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[2])):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        self.hex_mode = False

        self.setObjectName("Kevinbot3_RemoteUI")

        self.textbox = QTextEdit()
        self.textbox.setObjectName("Kevinbot3_RemoteUI_TextEdit")
        self.textbox.setReadOnly(True)
        self.layout = QVBoxLayout()

        self.bottom_layout = QHBoxLayout()
        self.top_layout = QHBoxLayout()

        self.layout.addLayout(self.top_layout)
        self.layout.addWidget(self.textbox)
        self.layout.addLayout(self.bottom_layout)
        self.setLayout(self.layout)

        self.tx_line = QLineEdit()
        self.tx_line.setObjectName("Kevinbot3_RemoteUI_SpeechInput")
        self.tx_line.setPlaceholderText("Data to Send")
        self.tx_line.returnPressed.connect(self.tx_data)
        self.top_layout.addWidget(self.tx_line)

        self.clear_button = QPushButton(strings.CLEAR)
        self.clear_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.clear_button.setStyleSheet("font-size: 16px")
        self.clear_button.setFixedHeight(36)
        self.clear_button.setFixedWidth(64)
        self.clear_button.clicked.connect(self.textbox.clear)
        self.bottom_layout.addWidget(self.clear_button)

        self.utf8_radio = QRadioButton("UTF-8")
        self.utf8_radio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.utf8_radio.setChecked(True)
        self.utf8_radio.toggled.connect(self.enable_utf8)
        self.bottom_layout.addWidget(self.utf8_radio)

        self.hex_radio = QRadioButton("HEX")
        self.hex_radio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.hex_radio.toggled.connect(self.enable_hex)
        self.bottom_layout.addWidget(self.hex_radio)

        self.bottom_layout.addStretch()

        self.shutdown = QPushButton()
        self.shutdown.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.shutdown.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.shutdown.setIconSize(QSize(32, 32))
        self.shutdown.clicked.connect(self.close)
        self.shutdown.setFixedSize(QSize(36, 36))
        self.bottom_layout.addWidget(self.shutdown)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.add_to_textbox)
        self.update_timer.start(10)

        self.serial_th = threading.Thread(target=self.target, daemon=True)
        self.serial_th.start()

        if EMULATE_REAL_REMOTE:
            self.setFixedSize(QSize(800, 480))
            self.setWindowFlags(Qt.FramelessWindowHint)

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def display(self, s):
        command_queue.put(s)

    def add_to_textbox(self):
        if not command_queue.empty():
            self.textbox.append(command_queue.get())

    def ser_in(self, s):  # Write incoming serial data to screen
        self.display(s)

    def target(self):  # Run serial reader thread

        while True:
            try:
                data = com.xb.wait_read_frame(1)
            except XBee_Timeout:
                continue
            red = "<span style=\" font-size:12pt; color:#ef0000;\" >"
            val = red + "RX ⇒  " + data["rf_data"].decode("UTF-8").strip("\r") + "<span>"
            if not self.hex_mode:
                self.display(val)
            else:
                self.display(red + "RX ⇒  " +
                             " ".join("{:02x}".format(ord(c)) for c in data["rf_data"].decode("UTF-8")) + "<span>")

    def tx_data(self):
        blue = '<span style=" font-size:12pt; color:#0000ef;" >'
        val = blue + 'TX ⇐  ' + self.tx_line.text() + '<span>'
        com.txstr(self.tx_line.text())
        if not self.hex_mode:
            self.display(val)
        else:
            self.display(blue + 'TX ⇐  ' +
                         ' '.join('{:02x}'.format(ord(c)) for c in self.tx_line.text() + '\r') + '<span>')

    def enable_utf8(self):
        self.hex_mode = False
        self.textbox.clear()

    def enable_hex(self):
        self.hex_mode = True
        self.textbox.clear()


if __name__ == "__main__":
    com.init()
    app = QApplication(sys.argv)
    app.setApplicationVersion(__version__)
    app.setApplicationName('Kevinbot XBee Terminal')
    w = Window()
    w.setWindowTitle('Kevinbot XBee Terminal')
    sys.exit(app.exec_())
