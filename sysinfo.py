import os
import platform
import sys
import json

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from QCustomWidgets import KBMainWindow
import qtawesome as qta

from utils import load_theme, detect_dark, get_size, is_using_venv, is_pi

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes

    WIN_APP_ID = 'kevinbot.kevinbot.remote.sysinfo'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WIN_APP_ID)

settings = json.load(open("settings.json", encoding="utf-8"))


class MainWindow(KBMainWindow):
    """ Kevinbot About App Window """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Remote Info")

        try:
            load_theme(self, settings["window_properties"]["theme"],
                       settings["window_properties"]["theme_colors"])
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(
                            QPalette.Window)).getRgb()[1],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[2])):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.title = QLabel("Kevinbot Remote System Info")
        self.title.setStyleSheet("font-size: 22px; font-weight: bold")
        self.layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.version = QLabel("Version: {}".format(open("version.txt", "r").read()))
        self.version.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.version, alignment=Qt.AlignmentFlag.AlignLeft)

        self.using_pi = QLabel("Using Raspberry Pi: {}".format(is_pi()))
        self.using_pi.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.using_pi, alignment=Qt.AlignmentFlag.AlignLeft)

        self.installed_themes = QLabel("Runner Themes: {}".format(os.listdir(os.path.join(os.curdir, "themepacks"))))
        self.layout.addWidget(self.installed_themes, alignment=Qt.AlignmentFlag.AlignLeft)

        self.kbot_size = QLabel("Remote System Storage Usage: {}MB (Mega)".format(round(get_size() / 1000 / 1000, 2)))
        self.layout.addWidget(self.kbot_size, alignment=Qt.AlignmentFlag.AlignLeft)

        self.is_venv = QLabel("Using Virtual Environment: {}".format(is_using_venv()))
        self.layout.addWidget(self.is_venv, alignment=Qt.AlignmentFlag.AlignLeft)

        self.platform = QLabel("Platform: {}".format(platform.platform()))
        self.layout.addWidget(self.platform, alignment=Qt.AlignmentFlag.AlignLeft)

        self.python_version = QLabel("Python Version: {}".format(platform.python_version()))
        self.layout.addWidget(self.python_version, alignment=Qt.AlignmentFlag.AlignLeft)

        self.qt_version = QLabel("PyQt Version: {}".format(PYQT_VERSION_STR))
        self.layout.addWidget(self.qt_version, alignment=Qt.AlignmentFlag.AlignLeft)

        self.pyqt_config = QLabel("PyQt Config: {}".format(PYQT_CONFIGURATION))
        self.layout.addWidget(self.pyqt_config, alignment=Qt.AlignmentFlag.AlignLeft)

        self.env_vars_label = QLabel("Environment Variables:")
        self.layout.addWidget(self.env_vars_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.env_vars = QPlainTextEdit()
        self.env_vars.setReadOnly(True)
        self.layout.addWidget(self.env_vars, alignment=Qt.AlignmentFlag.AlignBaseline)

        for name, value in os.environ.items():
            self.env_vars.appendPlainText("{0}: {1}".format(name, value))

        self.layout.addStretch()

        self.close_button = QPushButton()
        self.close_button.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.close_button.setIconSize(QSize(32, 32))
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(QSize(36, 36))
        self.layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Remote Info")
    app.setApplicationVersion("1.0")
    window = MainWindow()
    sys.exit(app.exec_())
