#!/usr/bin/python

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import os
import re
import json
import time
import platform
from functools import partial
from utils import load_theme
import haptics
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes
    appid = 'kevinbot.kevinbot.runner._'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

SETTINGS = json.load(open("settings.json", "r"))
APPS = json.load(open("apps.json", "r"))
try:
    logging.basicConfig(filename='menu.log', filemode='w', level=SETTINGS["log_level"], format=f'{__file__}:%('
                                                                                               f'levelname)s - %('
                                                                                               f'message)s')
except KeyError:
    logging.basicConfig(filename='menu.log', filemode='w', level=logging.INFO, format=f'{__file__}:%(levelname)s - %('
                                                                                      f'message)s')
    logging.warning("log level has not been set")
    SETTINGS["log_level"] = 20
    with open('settings.json', 'w') as file:
        json.dump(SETTINGS, file, indent=2)

haptics.init(21)


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified':
            print("Reloading Theme")
            global SETTINGS, APPS
            time.sleep(0.1)  # wait a while
            # Event is modified, you can process it now
            SETTINGS = json.load(open("settings.json", "r"))
            APPS = json.load(open("apps.json", "r"))
            window.updateTheme.emit()


observer = Observer()
path = os.path.join(sys.argv[1] if len(sys.argv) > 1 else '.', "apps.json")
observer.schedule(Handler(), path, recursive=True)
observer.start()


def run_app(command):
    os.system(command)


def extract_digits(string):
    return [int(s) for s in re.findall(r'\d+', string)]


def hex2rgb(h):
    t = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return t[0], t[1], t[2]


class MainWindow(QMainWindow):

    updateTheme = pyqtSignal()

    # noinspection PyUnresolvedReferences
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot Runner")
        self.setObjectName("Kevinbot3_RemoteUI")

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.main_widget = QGroupBox("Kevinbot Runner | {}".format(time.strftime("%I:%M %p")))
        self.main_widget.setObjectName("Kevinbot3_RemoteUI_Group")
        self.setCentralWidget(self.main_widget)

        self.load_theme()

        self.updateTheme.connect(self.load_theme)

        effects = APPS["theme_effect"].strip().split()

        widget_effect = []
        for i in range(len(effects)):
            effect_type = effects[i].split(":")
            if effect_type[0] == "shadow":
                widget_effect.append(QGraphicsDropShadowEffect())
                is_blur = [i for i in effect_type if i.startswith('b')]
                is_color = [i for i in effect_type if i.startswith('c')]
                if is_blur[0].startswith('b'):
                    widget_effect[i].setBlurRadius(extract_digits(effect_type[1])[0])

                if is_color[0].startswith('c'):
                    widget_effect[i].setColor(QColor().fromRgb(hex2rgb(is_color[0][1:])[0],
                                                               hex2rgb(is_color[0][1:])[1],
                                                               hex2rgb(is_color[0][1:])[2]))
                    print(effect_type[1][1:].strip("'"))

        for e in widget_effect:
            self.main_widget.setGraphicsEffect(e)

        layout = QVBoxLayout()
        self.main_widget.setLayout(layout)

        # app grid
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        # app buttons
        for link in APPS["apps"]:
            button = haptics.HToolButton()
            button.setText(link["name"])
            button.clicked.connect(partial(run_app, link["launch"]))
            button.setObjectName("Kevinbot3_RemoteUI_Button")
            button.setStyleSheet("font-size: 17px; padding: 10px;")
            button.setFixedSize(QSize(116, 116))
            button.setIconSize(QSize(48, 48))
            if "*" not in link["icon"]:
                button.setIcon(QIcon(os.path.join("icons", link["icon"])))
            else:
                button.setIcon(QIcon().fromTheme(link["icon"].replace("*", "")))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            
            self.grid.addWidget(button, link["row"], link["col"])

        layout.addStretch()

        shutdown = QPushButton("Shutdown")
        shutdown.clicked.connect(self.shutdown)
        shutdown.setObjectName("Kevinbot3_RemoteUI_Button")
        shutdown.setStyleSheet("font-size: 20px;")
        shutdown.setMinimumHeight(48)
        layout.addWidget(shutdown)

        reboot = QPushButton("Reboot")
        reboot.clicked.connect(self.reboot)
        reboot.setObjectName("Kevinbot3_RemoteUI_Button")
        reboot.setStyleSheet("font-size: 20px;")
        reboot.setMinimumHeight(48)
        layout.addWidget(reboot)

        # timer to update time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def load_theme(self):
        # load theme
        with open(APPS["theme"], "r") as file:
            self.setStyleSheet(file.read())

    def shutdown(self):
        # confirm shutdown
        msg = QMessageBox(self)
        load_theme(msg, SETTINGS["window_properties"]["theme"])
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you sure you want to shutdown?")
        msg.setInformativeText("This will shutdown the computer.")
        msg.setWindowTitle("Shutdown")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec_()

        # if yes, shutdown
        if ret == QMessageBox.Yes:
            os.system(SETTINGS["shutdown_command"])
        
    def reboot(self):
        # confirm reboot
        msg = QMessageBox(self)
        load_theme(msg, SETTINGS["window_properties"]["theme"])
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you sure you want to reboot?")
        msg.setInformativeText("This will reboot the computer.")
        msg.setWindowTitle("Reboot")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec_()

        # if yes, reboot
        if ret == QMessageBox.Yes:
            os.system(SETTINGS["reboot_command"])

    def update_time(self):
        self.main_widget.setTitle("Kevinbot Runner | {}".format(time.strftime("%I:%M %p")))
        self.timer.start(1000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Runner")
    app.setApplicationVersion("1.0")
    window = MainWindow()
    app.exec_()
