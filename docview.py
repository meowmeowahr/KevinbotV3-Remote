import os
import platform
import sys
import json

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWebEngineWidgets import *
from qtpy.QtWidgets import *
from QCustomWidgets import KBMainWindow
import qtawesome as qta

from utils import load_theme, detect_dark

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes

    WIN_APP_ID = "kevinbot.kevinbot.remote.sysinfo"  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WIN_APP_ID)

settings = json.load(open("settings.json", encoding="utf-8"))


class MainWindow(KBMainWindow):
    """Kevinbot About App Window"""

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Remote Info")
        self.setWindowIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/help.svg"))
        )

        try:
            load_theme(
                self,
                settings["window_properties"]["theme"],
                settings["window_properties"]["theme_colors"],
            )
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.ensurePolished()
        if detect_dark(
            (
                QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                QColor(self.palette().color(QPalette.Window)).getRgb()[2],
            )
        ):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        self.browser.load(
            QUrl().fromLocalFile(
                os.path.split(os.path.abspath(__file__))[0] + r"/built_docs/index.html"
            )
        )

        self.close_button = QPushButton()
        self.close_button.setIcon(qta.icon("fa5s.window-close", color="#F44336"))
        self.close_button.setIconSize(QSize(22, 22))
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(QSize(36, 24))
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
