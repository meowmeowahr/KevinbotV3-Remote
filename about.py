#!/usr/bin/python

"""
Kevinbot About App
"""

import json
import os.path
import platform
import sys

# noinspection PyPackageRequirements
from qtpy.QtCore import *
# noinspection PyPackageRequirements
from qtpy.QtGui import *
# noinspection PyPackageRequirements
from qtpy.QtWidgets import *

from QCustomWidgets import KBMainWindow

from utils import load_theme, detect_dark

import haptics

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes

    WIN_APP_ID = 'kevinbot.kevinbot.remote.about'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WIN_APP_ID)

settings = json.load(open("settings.json", encoding="utf-8"))

haptics.init(21)


class MainWindow(KBMainWindow):
    """ Kevinbot About App Window """
    # noinspection PyUnresolvedReferences,PyArgumentList
    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        self.setWindowTitle("About Kevinbot Remote")
        self.setObjectName("Kevinbot3_RemoteUI")

        try:
            load_theme(self, settings["window_properties"]["theme"],
                       settings["window_properties"]["theme_colors"])
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.ee_count = 0

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(
                            QPalette.Window)).getRgb()[1],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[2])):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.icon_layout = QHBoxLayout()
        self.layout.addLayout(self.icon_layout)

        self.icon = QLabel()
        self.icon.setPixmap(QPixmap("icons/icon.svg"))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setScaledContents(True)
        self.icon.setFixedSize(QSize(192, 192))
        self.icon.mousePressEvent = self.ee_click
        self.icon_layout.addWidget(self.icon)

        self.name_text = QLabel("Kevinbot v3 Remote")
        self.name_text.setStyleSheet("font-size: 30px; font-weight: bold; font-family: Roboto;")
        self.name_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_text)

        self.version = QLabel("Version: " + open("version.txt", encoding="utf-8").read())
        self.version.setStyleSheet("font-size: 24px; font-weight: semibold; font-family: Roboto;")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.version)

        self.qt_version = QLabel("PyQt Version: " + PYQT_VERSION_STR)
        self.qt_version.setStyleSheet("font-size: 22px; font-weight: normal; font-family: Roboto;")
        self.qt_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.qt_version)

        self.credits_box = QTextEdit()
        self.credits_box.setReadOnly(True)
        self.credits_box.setStyleSheet("font-family: Roboto;")
        self.credits_box.setText("<p>Kevinbot and Kevinbot Software created by Kevin Ahr <br>"
                                 "PyQtDarkTheme created by Yunosuke Ohsugi <br>"
                                 "BreezeStyleSheets created by Alexander Huszagh <br>"
                                 "Syntax Highlighting based on: "
                                 "https://github.com/art1415926535/PyQt5-syntax-highlighting <br>"
                                 "QSuperDial based on: "
                                 "https://github.com/Vampouille/superboucle/blob/master/superboucle/qsuperdial.py <br>"
                                 "Roboto Font by Christian Robertson<br>"
                                 "Lato Font by Łukasz Dziedzic</p>")
        self.credits_box.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        QScroller.grabGesture(self.credits_box, QScroller.LeftMouseButtonGesture)  # enable single-touch scroll
        self.credits_box.hide()
        self.layout.addWidget(self.credits_box)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.credits = haptics.HPushButton("Credits")
        self.credits.setCheckable(True)
        self.credits.setChecked(False)
        self.credits.toggled.connect(self.toggle_credits)
        self.button_layout.addWidget(self.credits)

        self.close_button = haptics.HPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.close_button)

        self.open_animation = QPropertyAnimation(self.credits_box, b"maximumHeight")
        self.open_animation.setStartValue(0)
        self.open_animation.setEndValue(100)
        self.open_animation.setDuration(100)

        self.close_animation = QPropertyAnimation(self.credits_box, b"maximumHeight")
        self.close_animation.setStartValue(100)
        self.close_animation.setEndValue(0)
        self.close_animation.setDuration(100)
        self.close_animation.start()
        self.close_animation.finished.connect(self.credits_box.hide)

        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def toggle_credits(self):
        """
        Show/Hide Credits Panel
        """

        if self.credits.isChecked():
            self.credits_box.show()
            self.open_animation.start()
        else:
            # noinspection PyAttributeOutsideInit
            self.close_animation.start()

    def ee_click(self, event):
        self.ee_count += 1

        if self.ee_count == 10:
            self.ee_count = 0
            # easter egg
            self.icon.setPixmap(QPixmap(os.path.join(os.curdir, "icons/bot-trans.png")))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("About Kevinbot Remote")
    app.setApplicationVersion("1.0")
    app.setWindowIcon(QIcon("icons/icon.svg"))

    # Font
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Roboto-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Roboto-Bold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Lato-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Lato-Bold.ttf"))

    window = MainWindow()
    sys.exit(app.exec_())
