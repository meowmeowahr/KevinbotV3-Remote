#!/usr/bin/python

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta
import sys
import os
import re
import json
import time
import platform
from functools import partial
from utils import load_theme, detect_dark
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

settings = json.load(open("settings.json", "r"))

# load dev mode settings
if "dev_mode" in settings:
    DEV_MODE = settings["dev_mode"]
else:
    settings["dev_mode"] = False  # save default
    DEV_MODE = settings["dev_mode"]
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

try:
    logging.basicConfig(filename='menu.log', filemode='w', level=settings["log_level"], format=f'{__file__}:%('
                                                                                               f'levelname)s - %('
                                                                                               f'message)s')
except KeyError:
    logging.basicConfig(filename='menu.log', filemode='w', level=logging.INFO, format=f'{__file__}:%(levelname)s - %('
                                                                                      f'message)s')
    logging.warning("log level has not been set")
    settings["log_level"] = 20
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

haptics.init(21)

# load runner theme flat setting
if "theme_flat" not in settings["apps"]:
    settings["apps"]["theme_flat"] = False  # save default
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified':
            print("Reloading Settings")
            global settings
            time.sleep(0.1)  # wait a while
            # Event is modified, you can process it now
            settings = json.load(open("settings.json", "r"))
            window.updateTheme.emit()


observer = Observer()
path = os.path.join(sys.argv[1] if len(sys.argv) > 1 else '.', "settings.json")
observer.schedule(Handler(), path, recursive=True)
observer.start()


def run_app(command):
    os.system(command)


def extract_digits(string):
    return [int(s) for s in re.findall(r'\d+', string)]


def hex2rgb(h):
    t = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return t[0], t[1], t[2]


class MainWindow(QMainWindow):
    updateTheme = pyqtSignal()

    # noinspection PyUnresolvedReferences
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot Runner")
        self.setObjectName("Kevinbot3_RemoteUI")

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[2])):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.editMode = False
        self.editBtn = None
        self.btn_index_list = []

        for app in settings["apps"]["apps"]:
            self.btn_index_list.append(app["id"])

        self.root_widget = QStackedWidget()
        self.setCentralWidget(self.root_widget)

        self.main_widget = QGroupBox("Kevinbot Runner | {}".format(time.strftime("%I:%M %p")))
        self.main_widget.setObjectName("Kevinbot3_RemoteUI_Group")
        self.root_widget.addWidget(self.main_widget)

        self.load_theme()

        self.updateTheme.connect(self.load_theme)

        effects = settings["apps"]["theme_effect"].strip().split()

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
        if not settings["apps"]["theme_flat"]:
            for e in widget_effect:
                self.main_widget.setGraphicsEffect(e)

        layout = QVBoxLayout()
        self.main_widget.setLayout(layout)

        # app grid
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.add_apps(self.grid)

        layout.addStretch()

        shutdown = QPushButton("Shutdown")
        shutdown.clicked.connect(self.shutdown)
        shutdown.setObjectName("Kevinbot3_RemoteUI_Button")
        shutdown.setStyleSheet("font-size: 20px;")
        shutdown.setMinimumHeight(48)
        layout.addWidget(shutdown)

        if not DEV_MODE:
            reboot = QPushButton("Reboot")
            reboot.clicked.connect(self.reboot)
            reboot.setObjectName("Kevinbot3_RemoteUI_Button")
            reboot.setStyleSheet("font-size: 20px;")
            reboot.setMinimumHeight(48)
            layout.addWidget(reboot)
        else:
            self.reboot_layout = QHBoxLayout()
            layout.addLayout(self.reboot_layout)

            reboot = QPushButton("Reboot")
            reboot.clicked.connect(self.reboot)
            reboot.setObjectName("Kevinbot3_RemoteUI_Button")
            reboot.setStyleSheet("font-size: 20px;")
            reboot.setMinimumHeight(48)
            self.reboot_layout.addWidget(reboot)

            self.dev_button = QPushButton("Dev Options")
            self.dev_button.clicked.connect(self.open_dev)
            self.dev_button.setObjectName("Kevinbot3_RemoteUI_Button")
            self.dev_button.setStyleSheet("font-size: 20px;")
            self.dev_button.setMinimumHeight(48)
            self.reboot_layout.addWidget(self.dev_button)

            self.dev_widget = QWidget()
            self.root_widget.addWidget(self.dev_widget)

            self.dev_root_layout = QHBoxLayout()
            self.dev_widget.setLayout(self.dev_root_layout)

            self.exit_dev = haptics.HPushButton()
            self.exit_dev.clicked.connect(lambda: self.root_widget.setCurrentIndex(0))
            self.exit_dev.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
            self.exit_dev.setFixedSize(QSize(36, 36))
            self.exit_dev.setIconSize(QSize(32, 32))
            self.dev_root_layout.addWidget(self.exit_dev)

            self.dev_layout = QVBoxLayout()
            self.dev_root_layout.addLayout(self.dev_layout)

            self.dev_close = haptics.HPushButton("Close Kevinbot Runner")
            self.dev_close.clicked.connect(self.close)
            self.dev_layout.addWidget(self.dev_close)

            try:
                with open("version.txt") as f:
                    version = f.read()
            except FileNotFoundError:
                version = "Unknown"

            self.dev_version = QLabel(f"RemoteVersion: {version}")
            self.dev_layout.addWidget(self.dev_version)

            self.dev_layout.addStretch()

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
        with open(settings["apps"]["theme"], "r") as file:
            self.setStyleSheet(file.read())

        effects = settings["apps"]["theme_effect"].strip().split()
        if not effects == ['none']:
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
            if not settings["apps"]["theme_flat"]:
                for e in widget_effect:
                    self.main_widget.setGraphicsEffect(e)
        else:
            self.main_widget.setGraphicsEffect(None)

        if settings["apps"]["theme_flat"]:
            self.main_widget.setGraphicsEffect(None)

    def shutdown(self):
        # confirm shutdown
        msg = QMessageBox(self)
        load_theme(msg, settings["window_properties"]["theme"])
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Are you sure you want to shutdown?")
        msg.setInformativeText("This will shutdown the computer.")
        msg.setWindowTitle("Shutdown")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = msg.exec_()

        # if yes, shutdown
        if ret == QMessageBox.StandardButton.Yes:
            os.system(settings["shutdown_command"])

    def reboot(self):
        # confirm reboot
        msg = QMessageBox(self)
        load_theme(msg, settings["window_properties"]["theme"])
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Are you sure you want to reboot?")
        msg.setInformativeText("This will reboot the computer.")
        msg.setWindowTitle("Reboot")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = msg.exec_()

        # if yes, reboot
        if ret == QMessageBox.StandardButton.Yes:
            os.system(settings["reboot_command"])

    def open_dev(self):
        self.root_widget.setCurrentIndex(1)

    def update_time(self):
        self.main_widget.setTitle("Kevinbot Runner | {}".format(time.strftime("%I:%M %p")))
        self.timer.start(1000)

    def check_hold(self, btn, index):
        if btn.isDown():
            self.editMode = True
            self.editBtn = btn

            self.edit_toolbar = QToolBar(self)
            self.edit_toolbar.setMovable(False)
            self.edit_toolbar.setMinimumWidth(150)

            self.edit_toolbar.move(QPoint(btn.pos().x() + int((btn.geometry().width() - self.edit_toolbar.geometry().width()) / 2), btn.pos().y() + btn.geometry().height() + 2))
            self.edit_toolbar.show()

            self.edit_left_action = QAction("LFT")
            self.edit_left_action.triggered.connect(lambda: self.left_edit_mode(index))
            self.edit_toolbar.addAction(self.edit_left_action)

            self.edit_right_action = QAction("RT")
            self.edit_right_action.triggered.connect(lambda: self.right_edit_mode(index))
            self.edit_toolbar.addAction(self.edit_right_action)

            self.edit_exit_action = QAction("END")
            self.edit_exit_action.triggered.connect(self.exit_edit_mode)
            self.edit_toolbar.addAction(self.edit_exit_action)

    def right_edit_mode(self, index):
        index_pos = self.btn_index_list.index(index)
        self.btn_index_list.remove(index)
        self.btn_index_list.insert(index_pos+1, index)

        for pos in range(len(settings["apps"]["apps"])):
            if settings["apps"]["apps"][pos]["id"] == index:
                app_item = settings["apps"]["apps"][pos]
                settings["apps"]["apps"].pop(pos)
                settings["apps"]["apps"].insert(pos+1, app_item)
                break

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        self.exit_edit_mode()
        self.add_apps(self.grid)

    def left_edit_mode(self, index):
        index_pos = self.btn_index_list.index(index)
        self.btn_index_list.remove(index)
        self.btn_index_list.insert(index_pos-1, index)

        for pos in range(len(settings["apps"]["apps"])):
            if settings["apps"]["apps"][pos]["id"] == index:
                app_item = settings["apps"]["apps"][pos]
                settings["apps"]["apps"].pop(pos)
                settings["apps"]["apps"].insert(pos-1, app_item)
                break

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        self.exit_edit_mode()
        self.add_apps(self.grid)

    def exit_edit_mode(self):
        self.edit_left_action.deleteLater()
        self.edit_right_action.deleteLater()
        self.edit_exit_action.deleteLater()
        self.edit_toolbar.deleteLater()
        self.editMode = False

    def start_check_hold(self, cmd, btn, index):
        if not self.editMode:
            QTimer.singleShot(1000, lambda: self.check_hold(btn, index))

    def button_released(self, cmd):
        if not self.editMode:
            run_app(cmd)

    def add_apps(self, grid, max_x=5):
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)

        # app buttons
        btn_idx = 0
        for link in settings["apps"]["apps"]:
            button = haptics.HToolButton()
            button.setText(link["name"])
            button.pressed.connect(partial(self.start_check_hold, link["launch"], button, link["id"]))
            button.released.connect(partial(self.button_released, link["launch"]))
            button.setObjectName("Kevinbot3_RemoteUI_Button")
            button.setStyleSheet("font-size: 17px; padding: 10px;")
            button.setFixedSize(QSize(116, 116))
            button.setIconSize(QSize(48, 48))
            if "*" not in link["icon"]:
                button.setIcon(QIcon(os.path.join("icons", link["icon"])))
            else:
                button.setIcon(QIcon().fromTheme(link["icon"].replace("*", "")))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

            self.grid.addWidget(button, btn_idx // max_x, btn_idx % max_x)
            btn_idx += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Runner")
    app.setApplicationVersion("1.0")
    window = MainWindow()
    app.exec_()
