import os
import platform
import sys
import json

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

import SlidingStackedWidget
import strings
from QCustomWidgets import KBMainWindow
import qtawesome as qta

from utils import load_theme, detect_dark
import haptics

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes

    WIN_APP_ID = 'kevinbot.kevinbot.remote.sysinfo'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WIN_APP_ID)

settings = json.load(open("settings.json", encoding="utf-8"))

haptics.init(21)


class MainWindow(KBMainWindow):
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

        self.widget = SlidingStackedWidget.SlidingStackedWidget()
        self.setCentralWidget(self.widget)

        self.home_layout = QVBoxLayout()
        self.home_widget = QWidget()
        self.home_widget.setLayout(self.home_layout)
        self.widget.addWidget(self.home_widget)

        self.graph_layout = QVBoxLayout()
        self.graph_widget = QWidget()
        self.graph_widget.setLayout(self.graph_layout)
        self.widget.addWidget(self.graph_widget)

        self.title = QLabel("Image Viewer")
        self.title.setStyleSheet("font-size: 22px; font-weight: bold; font-family: Roboto;")
        self.home_layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.graph_button = haptics.HPushButton(strings.IMVIEW_GRAPH_A)
        self.graph_button.setObjectName("Kevinbot3_RemoteUI_SMenuButton")
        self.graph_button.setStyleSheet("text-align: left;")
        self.graph_button.setIcon(qta.icon("mdi.chart-line", color=self.fg_color))
        self.graph_button.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.graph_button.setIconSize(QSize(48, 48))
        self.home_layout.addWidget(self.graph_button)

        self.home_layout.addStretch()

        self.close_button = QPushButton()
        self.close_button.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.close_button.setIconSize(QSize(32, 32))
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(QSize(36, 36))
        self.home_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        model = ImageModel()
        model.setStringList(os.listdir(os.path.join(os.curdir, "mpu_graph_images")))

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.graph_list = ImageListView()
        self.graph_list.setViewMode(QListView.IconMode)
        self.graph_list.setModel(self.proxy_model)
        self.graph_list.clicked.connect(self.select)
        self.graph_layout.addWidget(self.graph_list)

        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.back_button.setIconSize(QSize(32, 32))
        self.back_button.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.back_button.setFixedSize(QSize(36, 36))
        self.graph_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)


        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def select(self):
        indexes = self.graph_list.selectedIndexes()
        item = indexes[0].data()
        print(item)


class ImageListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def resizeEvent(self, event):
        width = self.viewport().width() - 30

        tile_width = width / 3
        icon_width = int(tile_width * 0.8)
        tile_width = int(tile_width)

        self.setGridSize(QSize(tile_width, tile_width))
        self.setIconSize(QSize(icon_width, icon_width))

        return super().resizeEvent(event)


class ImageModel(QStringListModel):

    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def data(self, index, role):
        if role == Qt.ItemDataRole.DecorationRole:
            icon_string = self.data(index, role=Qt.ItemDataRole.DisplayRole)
            image = QPixmap(os.path.join(os.curdir, "mpu_graph_images", icon_string))\
                .scaledToWidth(180, mode=Qt.TransformationMode.SmoothTransformation)

            return image
        return super().data(index, role)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Remote Info")
    app.setApplicationVersion("1.0")

    # Font
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Roboto-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Roboto-Bold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Lato-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(os.curdir, "res/fonts/Lato-Bold.ttf"))

    window = MainWindow()
    sys.exit(app.exec_())
