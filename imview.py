import os
import platform
import sys
import json
import time

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

        self.im_dir = ""
        self.pixmap = QPixmap(self.im_dir)
        self.scale_factor = 1

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

        self.model = ImageModel()
        self.model.setStringList(os.listdir(os.path.join(os.curdir, "mpu_graph_images")))

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.graph_list = ImageListView()
        self.graph_list.setViewMode(QListView.IconMode)
        self.graph_list.setModel(self.proxy_model)
        self.graph_list.clicked.connect(self.select)
        self.graph_list.doubleClicked.connect(self.view_image)
        QScroller.grabGesture(self.graph_list, QScroller.LeftMouseButtonGesture)  # enable single-touch scroll
        self.graph_layout.addWidget(self.graph_list)

        self.picker_bottom_layout = QHBoxLayout()
        self.graph_layout.addLayout(self.picker_bottom_layout)

        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.back_button.setIconSize(QSize(32, 32))
        self.back_button.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.back_button.setFixedSize(QSize(36, 36))
        self.picker_bottom_layout.addWidget(self.back_button)

        self.time_label = QLabel(strings.IMVIEW_TIME.format(strings.UNKNOWN))
        self.picker_bottom_layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.im_view_widget = QWidget()
        self.widget.addWidget(self.im_view_widget)
        self.im_view_layout = QVBoxLayout()
        self.im_view_widget.setLayout(self.im_view_layout)

        self.picker_bottom_layout = QHBoxLayout()
        self.graph_layout.addLayout(self.picker_bottom_layout)

        self.image_area = QScrollArea()
        self.image_area.setWidgetResizable(True)
        self.im_view_layout.addWidget(self.image_area)

        self.image = QLabel()
        self.image.setPixmap(self.pixmap)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        QScroller.grabGesture(self.image_area, QScroller.LeftMouseButtonGesture)  # enable single-touch scroll
        self.image_area.setWidget(self.image)

        self.viewer_bottom_layout = QHBoxLayout()
        self.im_view_layout.addLayout(self.viewer_bottom_layout)

        self.viewer_back_button = QPushButton()
        self.viewer_back_button.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.viewer_back_button.setIconSize(QSize(32, 32))
        self.viewer_back_button.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.viewer_back_button.setFixedSize(QSize(36, 36))
        self.viewer_bottom_layout.addWidget(self.viewer_back_button)

        self.viewer_delete = QPushButton()
        self.viewer_delete.setIcon(qta.icon("mdi.delete", color="#F44336"))
        self.viewer_delete.setIconSize(QSize(32, 32))
        self.viewer_delete.clicked.connect(self.delete)
        self.viewer_delete.setFixedSize(QSize(36, 36))
        self.viewer_bottom_layout.addWidget(self.viewer_delete)

        self.viewer_bottom_layout.addStretch()

        self.viewer_zoom_out = QPushButton()
        self.viewer_zoom_out.setIcon(qta.icon("mdi.magnify-minus", color=self.fg_color))
        self.viewer_zoom_out.setIconSize(QSize(32, 32))
        self.viewer_zoom_out.clicked.connect(lambda: self.zoom(-0.1))
        self.viewer_zoom_out.setFixedSize(QSize(36, 36))
        self.viewer_bottom_layout.addWidget(self.viewer_zoom_out)

        self.viewer_zoom_in = QPushButton()
        self.viewer_zoom_in.setIcon(qta.icon("mdi.magnify-plus", color=self.fg_color))
        self.viewer_zoom_in.setIconSize(QSize(32, 32))
        self.viewer_zoom_in.clicked.connect(lambda: self.zoom(0.1))
        self.viewer_zoom_in.setFixedSize(QSize(36, 36))
        self.viewer_bottom_layout.addWidget(self.viewer_zoom_in)

        self.zoom_label = QLabel(f"Zoom: {self.scale_factor * 100}")
        self.viewer_bottom_layout.addWidget(self.zoom_label)

        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def select(self):
        indexes = self.graph_list.selectedIndexes()
        item = indexes[0].data()
        self.im_dir = os.path.join(os.curdir, "mpu_graph_images", item)
        timestamp = os.path.getmtime(self.im_dir)
        self.time_label.setText(strings.IMVIEW_TIME.format(time.ctime(timestamp)))
        self.pixmap = QPixmap(self.im_dir)
        self.image.setPixmap(self.pixmap.scaledToWidth(round(self.pixmap.width() * self.scale_factor),
                                                       mode=Qt.TransformationMode.SmoothTransformation))

    def view_image(self):
        self.select()
        self.widget.slideInIdx(2)

    def zoom(self, factor):
        if int((self.scale_factor + factor) * 100) in range(10, 210):
            self.scale_factor += factor
            self.image.setPixmap(self.pixmap.scaledToWidth(round(self.pixmap.width() * self.scale_factor),
                                                           mode=Qt.TransformationMode.SmoothTransformation))
            self.zoom_label.setText(f"Zoom: {int(self.scale_factor * 100)}")

    def delete(self):
        os.remove(self.im_dir)
        self.model.setStringList(os.listdir(os.path.join(os.curdir, "mpu_graph_images")))
        self.widget.slideInIdx(1)


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
    if not os.path.exists(os.path.join(os.curdir, "mpu_graph_images")):
        os.mkdir(os.path.join(os.curdir, "mpu_graph_images"))

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
