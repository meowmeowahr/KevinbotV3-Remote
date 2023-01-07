#!/usr/bin/python

import json
import platform
import sys

# noinspection PyPackageRequirements
from PyQt5.QtCore import *
# noinspection PyPackageRequirements
from PyQt5.QtGui import *
# noinspection PyPackageRequirements
from PyQt5.QtWidgets import *
from utils import load_theme, detect_dark

import haptics

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes

    app_id = 'kevinbot.kevinbot.remote.about'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

settings = json.load(open("settings.json", "r"))

haptics.init(21)


class MainWindow(QMainWindow):
    # noinspection PyUnresolvedReferences,PyArgumentList
    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        self.setWindowTitle("About Kevinbot Remote")
        self.setObjectName("Kevinbot3_RemoteUI")
        
        try:
            load_theme(self, settings["window_properties"]["theme"], settings["window_properties"]["theme_colors"])
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[1],
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
        self.icon_layout.addWidget(self.icon)

        self.name_text = QLabel("Kevinbot v3 Remote")
        self.name_text.setStyleSheet("font-size: 30px; font-weight: bold;")
        self.name_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_text)

        self.version = QLabel("Version: " + open("version.txt").read())
        self.version.setStyleSheet("font-size: 24px; font-weight: semibold;")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.version)

        self.credits_box = QTextEdit()
        self.credits_box.setReadOnly(True)
        self.credits_box.setText("<p>Kevinbot and Kevinbot Software created by Kevin Ahr <br>"
                                 "PyQtDarkTheme created by Yunosuke Ohsugi <br>"
                                 "BreezeStyleSheets created by Alexander Huszagh </p>")
        self.credits_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def toggle_credits(self):
        if self.credits.isChecked():
            self.credits_box.show()
            self.anim = QPropertyAnimation(self.credits_box, b"maximumHeight")
            self.anim.setStartValue(0)
            self.anim.setEndValue(100)
            self.anim.setDuration(100)
            self.anim.start()
        else:
            # noinspection PyAttributeOutsideInit
            self.anim = QPropertyAnimation(self.credits_box, b"maximumHeight")
            self.anim.setStartValue(100)
            self.anim.setEndValue(0)
            self.anim.setDuration(100)
            self.anim.start()
            self.anim.finished.connect(self.credits_box.hide)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("About Kevinbot Remote")
    app.setApplicationVersion("1.0")
    app.setWindowIcon(QIcon("icons/icon.svg"))
    window = MainWindow()
    sys.exit(app.exec_())
