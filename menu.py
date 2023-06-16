#!/usr/bin/python
import importlib

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *

import utils
from QCustomWidgets import KBMainWindow
import qtawesome as qta
import sys
import os
import re
import json
import time
import platform
from functools import partial
from utils import load_theme, detect_dark, AppLauncher, is_using_venv
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
    logging.basicConfig(filename='menu.log', filemode='w', level=settings["log_level"])
except KeyError as e:
    logging.basicConfig(filename='menu.log', filemode='w', level=logging.INFO)
    logging.warning("log level has not been set")
    settings["log_level"] = 20
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)
    print(e)

haptics.init(21)

# load runner theme flat setting
if "theme_flat" not in settings["apps"]:
    settings["apps"]["theme_flat"] = False  # save default
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return None
        else:
            logging.debug("Reloaded Settings")
            global settings
            time.sleep(0.2)  # wait a while
            # Event is modified, you can process it now
            settings = json.load(open("settings.json", "r"))
            window.updateTheme.emit()


def run_app(command, gui=True):
    if is_using_venv():
        if platform.system() == "Windows":
            command = command.replace("python3", os.path.join(os.curdir, "venv\\Scripts\\python.exe"))
        elif platform.system() == "Linux":
            command = command.replace("python3", os.path.join(os.curdir, "venv\\bin\\python"))

    logging.info(f"Running command: {command}")

    if gui:
        window.main_widget.setEnabled(False)

    launcher.set_script(command)
    if gui:
        launcher.set_finished(lambda: window.main_widget.setEnabled(True))
    launcher.launch()


def extract_digits(string):
    return [int(s) for s in re.findall(r'\d+', string)]


def hex2rgb(h):
    t = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return t[0], t[1], t[2]


class MainWindow(KBMainWindow):
    updateTheme = Signal()

    # noinspection PyUnresolvedReferences,PyArgumentList
    def __init__(self):
        super(MainWindow, self).__init__()
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
            if utils.is_pi():
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)
            else:
                self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.editMode = False
        self.editBtn = None
        self.btn_index_list = []

        for btn in settings["apps"]["apps"]:
            self.btn_index_list.append(btn["id"])

        self.root_widget = QStackedWidget()
        self.setCentralWidget(self.root_widget)

        self.main_widget = QGroupBox("Kevinbot Runner | {}".format(time.strftime("%I:%M %p")))
        self.main_widget.setObjectName("Kevinbot3_RemoteUI_Group")
        self.root_widget.addWidget(self.main_widget)

        self.load_theme()

        self.updateTheme.connect(self.load_theme)

        layout = QVBoxLayout()
        self.main_widget.setLayout(layout)

        # app grid
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.add_apps()

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
            self.dev_close.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
            self.dev_close.clicked.connect(self.close)
            self.dev_layout.addWidget(self.dev_close)

            self.dev_sysinfo = haptics.HPushButton("Launch System Info App")
            self.dev_sysinfo.setIcon(qta.icon("fa5s.search", color=self.fg_color))
            self.dev_sysinfo.clicked.connect(lambda: run_app("python3 sysinfo.py", gui=False))
            self.dev_layout.addWidget(self.dev_sysinfo)

            self.dev_layout.addStretch()

        # Edit Toolbar
        self.edit_toolbar = QToolBar(self)
        self.edit_toolbar.setMovable(False)
        self.edit_toolbar.setMinimumWidth(125)
        self.edit_toolbar.setIconSize(QSize(32, 32))
        self.edit_toolbar.hide()

        self.edit_exit_action = QAction("Cancel")
        self.edit_exit_action.triggered.connect(self.exit_edit_mode)
        self.edit_exit_action.setIcon(QIcon(qta.icon("fa5s.backspace", color=QColor("#0288D1"))))
        self.edit_toolbar.addAction(self.edit_exit_action)

        # timer to update time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def load_theme(self):
        try:
            # load theme from module
            theme = importlib.import_module(f"themepacks.{settings['apps']['theme'][:-3]}")

            self.setStyleSheet(theme.QSS)  # set style sheet

            if not theme.EFFECTS == ['none']:
                widget_effect = None
                effect_type = theme.EFFECTS.split(":")
                if effect_type[0] == "shadow":
                    widget_effect = QGraphicsDropShadowEffect(self)
                    is_blur = [i for i in effect_type if i.startswith('b')]
                    is_color = [i for i in effect_type if i.startswith('c')]
                    if is_blur[0].startswith('b'):
                        widget_effect.setBlurRadius(extract_digits(effect_type[1])[0])

                    if is_color[0].startswith('c'):
                        widget_effect.setColor(QColor().fromRgb(hex2rgb(is_color[0][1:])[0],
                                                                hex2rgb(is_color[0][1:])[1],
                                                                hex2rgb(is_color[0][1:])[2]))
                if not settings["apps"]["theme_flat"]:
                    self.main_widget.setGraphicsEffect(widget_effect)
            else:
                self.main_widget.setGraphicsEffect(None)

            if settings["apps"]["theme_flat"]:
                self.main_widget.setGraphicsEffect(None)
        except (ModuleNotFoundError, NameError) as err:
            print(f"Theme could not be loaded {err}")

    def shutdown(self):
        # confirm shutdown
        msg = QMessageBox(self)
        load_theme(msg, settings["window_properties"]["theme"])
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you sure you want to shutdown?")
        msg.setInformativeText("This will shutdown the computer.")
        msg.setWindowTitle("Shutdown")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec_()

        # if yes, shutdown
        if ret == QMessageBox.Yes:
            os.system(settings["shutdown_command"])

    def reboot(self):
        # confirm reboot
        msg = QMessageBox(self)
        load_theme(msg, settings["window_properties"]["theme"])
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you sure you want to reboot?")
        msg.setInformativeText("This will reboot the computer.")
        msg.setWindowTitle("Reboot")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec_()

        # if yes, reboot
        if ret == QMessageBox.Yes:
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

            self.edit_toolbar.move(QPoint(btn.pos().x() +
                                          int((btn.geometry().width() - self.edit_toolbar.geometry().width()) / 2),
                                          btn.pos().y() + btn.geometry().height() + 2))
            self.edit_toolbar.show()

            self.edit_left_action = QAction("Left")
            self.edit_left_action.triggered.connect(lambda: self.left_edit_mode(index))
            self.edit_left_action.setIcon(QIcon(qta.icon("fa5s.caret-left", color=QColor("#0288D1"))))
            self.edit_toolbar.addAction(self.edit_left_action)

            self.edit_right_action = QAction("Right")
            self.edit_right_action.triggered.connect(lambda: self.right_edit_mode(index))
            self.edit_right_action.setIcon(QIcon(qta.icon("fa5s.caret-right", color=QColor("#0288D1"))))
            self.edit_toolbar.addAction(self.edit_right_action)

    def right_edit_mode(self, index):
        index_pos = self.btn_index_list.index(index)
        self.btn_index_list.remove(index)
        self.btn_index_list.insert(index_pos + 1, index)

        for pos in range(len(settings["apps"]["apps"])):
            if settings["apps"]["apps"][pos]["id"] == index:
                app_item = settings["apps"]["apps"][pos]
                settings["apps"]["apps"].pop(pos)
                settings["apps"]["apps"].insert(pos + 1, app_item)
                break

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        self.exit_edit_mode()
        self.add_apps()

    def left_edit_mode(self, index):
        index_pos = self.btn_index_list.index(index)
        self.btn_index_list.remove(index)
        self.btn_index_list.insert(index_pos - 1, index)

        for pos in range(len(settings["apps"]["apps"])):
            if settings["apps"]["apps"][pos]["id"] == index:
                app_item = settings["apps"]["apps"][pos]
                settings["apps"]["apps"].pop(pos)
                settings["apps"]["apps"].insert(pos - 1, app_item)
                break

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        self.exit_edit_mode()
        self.add_apps()

    def exit_edit_mode(self):
        self.editMode = False
        self.edit_toolbar.hide()

    def start_check_hold(self, btn, index):
        if not self.editMode:
            QTimer.singleShot(1000, lambda: self.check_hold(btn, index))

    def button_released(self, cmd):
        if not self.editMode:
            run_app(cmd)

    def add_apps(self, max_x=5):
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        # app buttons
        btn_idx = 0
        for link in settings["apps"]["apps"]:
            button = haptics.HToolButton()
            button.setText(link["name"])
            button.pressed.connect(partial(self.start_check_hold, button, link["id"]))
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

    # Font
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Roboto-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Roboto-Bold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Lato-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Lato-Bold.ttf"))

    # Window
    window = MainWindow()

    # File Observer
    observer = Observer()
    path = os.getcwd()
    observer.schedule(Handler(), path, recursive=True)
    observer.start()

    # App Launcher
    launcher = AppLauncher()

    app.exec_()
