#!/usr/bin/python

import json
import os
import platform
import sys
import subprocess
from urllib.parse import urlparse

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from SlidingStackedWidget import SlidingStackedWidget
from json_editor import Editor
from QSpinner import QSpinner
from utils import load_theme, detect_dark
import qtawesome as qta

from com import is_pi

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes
    app_id = 'kevinbot.kevinbot.runner._'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

SETTINGS = json.load(open("settings.json", "r"))
APPS = json.load(open("apps.json", "r"))

THEME_PAIRS = [
    ("Kevinbot Dark", "classic"),
    ("QDarkTheme Dark", "qdarktheme"),
    ("QDarkTheme Light", "qdarktheme_light")
]


def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


class SliderProxyStyle(QProxyStyle):
    # noinspection PyMethodOverriding
    def pixelMetric(self, metric, option, widget):
        if metric == QStyle.PM_SliderThickness:
            return 25
        elif metric == QStyle.PM_SliderLength:
            return 22
        return super().pixelMetric(metric, option, widget)


class MainWindow(QMainWindow):
    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        self.slider_style = SliderProxyStyle(QSlider().style())
        self.setWindowTitle("Kevinbot Remote Settings")
        self.setObjectName("Kevinbot3_RemoteUI")
        load_theme(self, SETTINGS["window_properties"]["theme"])

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

        self.main_widget = SlidingStackedWidget(self)
        self.setCentralWidget(self.main_widget)

        self.home_widget = QWidget()
        self.main_widget.addWidget(self.home_widget)

        self.adv_widget = QGroupBox("Advanced Settings")
        self.adv_widget.setObjectName("Kevinbot3_RemoteUI_Group")
        self.main_widget.addWidget(self.adv_widget)

        self.adv_layout = QVBoxLayout()
        self.adv_widget.setLayout(self.adv_layout)

        self.adv_editor = Editor()
        self.adv_layout.addWidget(self.adv_editor)

        self.adv_bottom_layout = QHBoxLayout()
        self.adv_layout.addLayout(self.adv_bottom_layout)

        self.adv_exit_button = QPushButton()
        self.adv_exit_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_exit_button.clicked.connect(lambda: self.main_widget.slideInIdx(0))
        self.adv_exit_button.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.adv_exit_button.setIconSize(QSize(32, 32))
        self.adv_exit_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_exit_button)

        self.adv_save_button = QPushButton()
        self.adv_save_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_save_button.clicked.connect(self.adv_editor.saveFile)
        self.adv_save_button.setIcon(qta.icon("fa5s.save", color=self.fg_color))
        self.adv_save_button.setIconSize(QSize(32, 32))
        self.adv_save_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_save_button)

        self.adv_expand_all_button = QPushButton()
        self.adv_expand_all_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_expand_all_button.clicked.connect(self.adv_editor.expandAll)
        self.adv_expand_all_button.setIcon(qta.icon("fa5s.caret-down", color=self.fg_color))
        self.adv_expand_all_button.setIconSize(QSize(32, 32))
        self.adv_expand_all_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_expand_all_button)

        self.adv_collapse_all_button = QPushButton()
        self.adv_collapse_all_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_collapse_all_button.clicked.connect(self.adv_editor.collapseAll)
        self.adv_collapse_all_button.setIcon(qta.icon("fa5s.caret-up", color=self.fg_color))
        self.adv_collapse_all_button.setIconSize(QSize(32, 32))
        self.adv_collapse_all_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_collapse_all_button)

        self.warning = QLabel("WARNING: Changing some of these settings may damage your remote or robot.")
        self.warning.setObjectName("Kevinbot3_RemoteUI_Warning")
        self.warning.setFixedHeight(36)
        self.warning.setAlignment(Qt.AlignCenter)
        self.adv_bottom_layout.addWidget(self.warning)

        self.display_widget = QWidget()
        self.main_widget.addWidget(self.display_widget)

        self.display_layout = QVBoxLayout()
        self.display_widget.setLayout(self.display_layout)

        self.robot_widget = QWidget()
        self.main_widget.addWidget(self.robot_widget)

        self.robot_layout = QVBoxLayout()
        self.robot_widget.setLayout(self.robot_layout)


        self.main_layout = QVBoxLayout()
        self.home_widget.setLayout(self.main_layout)

        self.display_button = QPushButton("Display and Theme Settings")
        self.display_button.setStyleSheet("text-align: left;")
        self.display_button.setIcon(qta.icon("fa5s.paint-roller", color=self.fg_color))
        self.display_button.clicked.connect(lambda: self.main_widget.setCurrentIndex(2))
        self.display_button.setIconSize(QSize(48,48))
        self.main_layout.addWidget(self.display_button)

        self.robot_button = QPushButton("Robot Settings")
        self.robot_button.setStyleSheet("text-align: left;")
        self.robot_button.setIcon(qta.icon("fa5s.robot", color=self.fg_color))
        self.robot_button.clicked.connect(lambda: self.main_widget.setCurrentIndex(3))
        self.robot_button.setIconSize(QSize(48,48))
        self.main_layout.addWidget(self.robot_button)

        # Screen Brightness
        self.screen_bright_box = QGroupBox("Screen Brightness")
        self.screen_bright_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.screen_bright_layout = QVBoxLayout()
        self.screen_bright_box.setLayout(self.screen_bright_layout)

        self.screen_bright_slider = QSlider(Qt.Horizontal)
        self.screen_bright_slider.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.screen_bright_slider.setRange(20, 255)
        self.screen_bright_slider.valueChanged.connect(self.change_backlight)
        self.screen_bright_slider.setStyle(self.slider_style)
        self.screen_bright_layout.addWidget(self.screen_bright_slider)

        if not is_pi():
            self.screen_bright_box.setDisabled(True)
            warning = QLabel("Screen Brightness is not supported on your device")
            self.screen_bright_layout.addWidget(warning)
        else:
            result = subprocess.result = subprocess.run(['cat', SETTINGS["backlight_dir"] + "brightness"],
                                                        stdout=subprocess.PIPE)
            self.screen_bright_slider.setValue(int(result.stdout))

        self.display_layout.addWidget(self.screen_bright_box)

        self.theme_box = QGroupBox("Runner Theme")
        self.theme_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.theme_layout = QVBoxLayout()
        self.theme_box.setLayout(self.theme_layout)
        self.display_layout.addWidget(self.theme_box)

        self.theme_picker = QComboBox()
        self.theme_picker.setObjectName("Kevinbot3_RemoteUI_Combo")
        self.theme_picker.blockSignals(True)
        self.theme_picker.currentIndexChanged.connect(self.change_theme)
        self.theme_picker.setFixedHeight(36)
        self.theme_layout.addWidget(self.theme_picker)

        self.app_theme_box = QGroupBox("App Theme")
        self.app_theme_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.app_theme_layout = QVBoxLayout()
        self.app_theme_box.setLayout(self.app_theme_layout)
        self.display_layout.addWidget(self.app_theme_box)

        self.app_theme_picker = QComboBox()
        self.app_theme_picker.setObjectName("Kevinbot3_RemoteUI_Combo")
        self.app_theme_picker.blockSignals(True)
        self.app_theme_picker.currentIndexChanged.connect(self.change_app_theme)
        self.app_theme_picker.setFixedHeight(36)
        self.app_theme_layout.addWidget(self.app_theme_picker)

        for name in APPS["themes"]:
            self.theme_picker.addItem(name)
        self.theme_picker.setCurrentIndex(APPS["themes"].index(APPS["theme_name"]))
        self.theme_picker.blockSignals(False)

        for pair in THEME_PAIRS:
            self.app_theme_picker.addItem(pair[0])

            if pair[1] == SETTINGS["window_properties"]["theme"]:
                self.app_theme_picker.setCurrentText(pair[0])
        self.app_theme_picker.blockSignals(False)

        self.exit_themes = QPushButton()
        self.exit_themes.clicked.connect(lambda: self.main_widget.setCurrentIndex(0))
        self.exit_themes.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_themes.setFixedSize(QSize(36, 36))
        self.exit_themes.setIconSize(QSize(32, 32))
        self.display_layout.addWidget(self.exit_themes)

        self.speed_box = QGroupBox("Robot Speed")
        self.speed_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.speed_layout = QHBoxLayout()
        self.speed_box.setLayout(self.speed_layout)
        self.robot_layout.addWidget(self.speed_box)

        self.max_us_label = QLabel("Max µS:")
        self.max_us_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.speed_layout.addWidget(self.max_us_label)

        self.max_us_spinner = QSpinner()
        self.max_us_spinner.setMaximum(1500)
        self.max_us_spinner.setMinimum(1000)
        self.max_us_spinner.setSingleStep(25)
        self.max_us_spinner.setValue(SETTINGS["max_us"])
        self.max_us_spinner.spinbox.valueChanged.connect(self.max_us_changed)
        self.speed_layout.addWidget(self.max_us_spinner)

        # Camera URL

        self.cam_url = QGroupBox("Camera URL")
        self.cam_url.setObjectName("Kevinbot3_RemoteUI_Group")
        self.cam_layout = QHBoxLayout()
        self.cam_url.setLayout(self.cam_layout)
        self.robot_layout.addWidget(self.cam_url)

        self.cam_url_input = QLineEdit()
        self.cam_url_input.setObjectName("Kevinbot3_RemoteUI_SpeechInput")
        self.cam_url_input.setText(SETTINGS["camera_url"])
        self.cam_url_input.setFixedHeight(32)
        self.cam_url_input.textChanged.connect(self.save_url)
        self.cam_url_input.setStyleSheet("font-size: 14px;")
        self.cam_layout.addWidget(self.cam_url_input)

        self.cam_validate = QPushButton("Validate URL")
        self.cam_validate.setFixedHeight(32)
        self.cam_validate.setFixedWidth(self.cam_validate.sizeHint().width() + 10)
        self.cam_validate.clicked.connect(self.validate_url)
        self.cam_validate.setObjectName("Kevinbot3_RemoteUI_Button")
        self.cam_layout.addWidget(self.cam_validate)

        self.exit_robot = QPushButton()
        self.exit_robot.clicked.connect(lambda: self.main_widget.setCurrentIndex(0))
        self.exit_robot.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_robot.setFixedSize(QSize(36, 36))
        self.exit_robot.setIconSize(QSize(32, 32))
        self.robot_layout.addWidget(self.exit_robot)

        # Exit
        self.exit_layout = QHBoxLayout()
        self.exit_button = QPushButton()
        self.exit_button.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.exit_button.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.exit_button.setIconSize(QSize(32, 32))
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setFixedSize(QSize(36, 36))
        self.exit_layout.addWidget(self.exit_button)
        self.main_layout.addLayout(self.exit_layout)

        # Advanced Settings
        self.adv_button = QPushButton("Advanced Settings")
        self.adv_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_button.setStyleSheet("font-size: 14px;")
        self.adv_button.setFixedHeight(36)
        self.adv_button.clicked.connect(lambda: self.main_widget.slideInIdx(1))
        self.exit_layout.addWidget(self.adv_button)

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def load_theme(self):
        with open("theme.qss", "r") as file:
            self.setStyleSheet(file.read())

    def change_backlight(self):
        if is_pi():
            os.system(f"echo {self.screen_bright_slider.value()} > {SETTINGS['backlight_dir']}brightness")
        else:
            print(f"Brightness: {self.screen_bright_slider.value()}")

    def validate_url(self):
        if uri_validator(self.cam_url_input.text()):
            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setText("URL is Valid")
            message.setWindowTitle("URL Validation")
            message.exec_()
        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Warning)
            message.setText("URL is Invalid")
            message.setWindowTitle("URL Validation")
            message.exec_()

    def save_url(self):
        SETTINGS["camera_url"] = self.cam_url_input.text()
        with open('settings.json', 'w') as file:
            json.dump(SETTINGS, file, indent=2)

    def max_us_changed(self):
        SETTINGS["max_us"] = self.max_us_spinner.spinbox.value()
        with open('settings.json', 'w') as file:
            json.dump(SETTINGS, file, indent=2)

    def change_theme(self):
        index = self.theme_picker.currentIndex()
        file_name = APPS["theme_files"][index]
        effect = APPS["theme_effects"][index]
        APPS["theme"] = file_name
        APPS["theme_effect"] = effect
        APPS["theme_name"] = self.theme_picker.currentText()

        with open('apps.json', 'w') as file:
            json.dump(APPS, file, indent=2)

    def change_app_theme(self):
        combo_val = self.app_theme_picker.currentText()
        for pair in THEME_PAIRS:
            if pair[0] == combo_val:
                SETTINGS["window_properties"]["theme"] = pair[1]

        with open('settings.json', 'w') as file:
            json.dump(SETTINGS, file, indent=2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Remote Settings")
    app.setApplicationVersion("1.0")
    app.setWindowIcon(QIcon("icons/settings.svg"))
    window = MainWindow()
    sys.exit(app.exec_())
