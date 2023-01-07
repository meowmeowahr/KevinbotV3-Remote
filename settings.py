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
from QCustomWidgets import QSpinner, QNamedLineEdit
from SlidingStackedWidget import SlidingStackedWidget
from json_editor import Editor
from utils import load_theme, detect_dark, is_tool, is_pi
import qtawesome as qta
import xscreensaver_config.ConfigParser as xSc

import haptics
import strings

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# windows support
if platform.system() == "Windows":
    import ctypes

    app_id = 'kevinbot.kevinbot.runner._'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

settings = json.load(open("settings.json", "r"))
app_settings = json.load(open("apps.json", "r"))

# load stick size settings
if "joystick_size" in settings:
    JOYSTICK_SIZE = settings["joystick_size"]
else:
    settings["joystick_size"] = 80  # save default
    JOYSTICK_SIZE = settings["joystick_size"]
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

# load stick mode settings
if "joystick_type" in settings:
    if settings["joystick_type"] == "digital":
        ANALOG_STICK = False
    else:
        ANALOG_STICK = True

else:
    settings["joystick_type"] = "analog"  # save default
    if settings["joystick_type"] == "digital":
        ANALOG_STICK = False
    else:
        ANALOG_STICK = True
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

# load runner theme flat setting
if not "theme_flat" in settings["apps"]:
    settings["apps"]["theme_flat"] = False  # save default
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

THEME_PAIRS = [
    ("Kevinbot Dark (Deprecated)", "classic"),
    ("QDarkTheme Dark (Customizable)", "qdarktheme", ["Default", "Purple"]),
    ("QDarkTheme Light", "qdarktheme_light"),
    ("High Contrast Dark", "highcontrast"),
    ("Breeze Dark", "breeze_dark"),
    ("Breeze Light", "breeze_light"),
    ("System (Debug)", "null")
]

haptics.init(21)


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


# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    # noinspection PyArgumentList
    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        self.slider_style = SliderProxyStyle(QSlider().style())
        self.setWindowTitle("Kevinbot Remote Settings")
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

        self.main_widget = SlidingStackedWidget(self)
        self.setCentralWidget(self.main_widget)

        self.home_widget = QWidget()
        self.main_widget.addWidget(self.home_widget)

        self.adv_widget = QGroupBox(strings.SETTINGS_ADV_G)
        self.adv_widget.setObjectName("Kevinbot3_RemoteUI_Group")
        self.main_widget.addWidget(self.adv_widget)

        self.adv_layout = QVBoxLayout()
        self.adv_widget.setLayout(self.adv_layout)

        self.adv_editor = Editor()
        self.adv_layout.addWidget(self.adv_editor)

        self.adv_bottom_layout = QHBoxLayout()
        self.adv_layout.addLayout(self.adv_bottom_layout)

        self.adv_exit_button = haptics.HPushButton()
        self.adv_exit_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_exit_button.clicked.connect(lambda: self.main_widget.slideInIdx(0))
        self.adv_exit_button.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.adv_exit_button.setIconSize(QSize(32, 32))
        self.adv_exit_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_exit_button)

        self.adv_save_button = haptics.HPushButton()
        self.adv_save_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_save_button.clicked.connect(self.adv_editor.saveFile)
        self.adv_save_button.setIcon(qta.icon("fa5s.save", color=self.fg_color))
        self.adv_save_button.setIconSize(QSize(32, 32))
        self.adv_save_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_save_button)

        self.adv_expand_all_button = haptics.HPushButton()
        self.adv_expand_all_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_expand_all_button.clicked.connect(self.adv_editor.expandAll)
        self.adv_expand_all_button.setIcon(qta.icon("fa5s.caret-down", color=self.fg_color))
        self.adv_expand_all_button.setIconSize(QSize(32, 32))
        self.adv_expand_all_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_expand_all_button)

        self.adv_collapse_all_button = haptics.HPushButton()
        self.adv_collapse_all_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_collapse_all_button.clicked.connect(self.adv_editor.collapseAll)
        self.adv_collapse_all_button.setIcon(qta.icon("fa5s.caret-up", color=self.fg_color))
        self.adv_collapse_all_button.setIconSize(QSize(32, 32))
        self.adv_collapse_all_button.setFixedSize(QSize(36, 36))
        self.adv_bottom_layout.addWidget(self.adv_collapse_all_button)

        self.warning = QLabel(strings.SETTINGS_ADV_WARNING)
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

        self.web_widget = QWidget()
        self.main_widget.addWidget(self.web_widget)

        self.remote_widget = QWidget()
        self.main_widget.addWidget(self.remote_widget)

        self.remote_layout = QVBoxLayout()
        self.remote_widget.setLayout(self.remote_layout)

        self.web_layout = QVBoxLayout()
        self.web_widget.setLayout(self.web_layout)

        self.main_layout = QVBoxLayout()
        self.home_widget.setLayout(self.main_layout)

        self.display_button = haptics.HPushButton(strings.SETTINGS_DISPLAY_OPT)
        self.display_button.setStyleSheet("text-align: left;")
        self.display_button.setIcon(qta.icon("fa5s.paint-roller", color=self.fg_color))
        self.display_button.clicked.connect(lambda: self.main_widget.slideInIdx(2))
        self.display_button.setIconSize(QSize(48, 48))
        self.main_layout.addWidget(self.display_button)

        self.robot_button = haptics.HPushButton(strings.SETTINGS_ROBOT_OPT)
        self.robot_button.setStyleSheet("text-align: left;")
        self.robot_button.setIcon(qta.icon("fa5s.robot", color=self.fg_color))
        self.robot_button.clicked.connect(lambda: self.main_widget.slideInIdx(3))
        self.robot_button.setIconSize(QSize(48, 48))
        self.main_layout.addWidget(self.robot_button)

        self.remote_button = haptics.HPushButton(strings.SETTINGS_REMOTE_OPT)
        self.remote_button.setStyleSheet("text-align: left;")
        self.remote_button.setIcon(qta.icon("fa5s.tablet-alt", color=self.fg_color))
        self.remote_button.clicked.connect(lambda: self.main_widget.slideInIdx(5))
        self.remote_button.setIconSize(QSize(48, 48))
        self.main_layout.addWidget(self.remote_button)

        self.web_button = haptics.HPushButton(strings.SETTINGS_BROWSER_OPT)
        self.web_button.setStyleSheet("text-align: left;")
        self.web_button.setIcon(qta.icon("fa5s.globe", color=self.fg_color))
        self.web_button.clicked.connect(lambda: self.main_widget.slideInIdx(4))
        self.web_button.setIconSize(QSize(48, 48))
        self.main_layout.addWidget(self.web_button)

        self.adv_button = haptics.HPushButton(strings.SETTINGS_ADVANCED_OPT)
        self.adv_button.setStyleSheet("text-align: left;")
        self.adv_button.setIcon(qta.icon("fa5s.tools", color=self.fg_color))
        self.adv_button.setObjectName("Kevinbot3_RemoteUI_Button")
        self.adv_button.setIconSize(QSize(48, 48))
        self.adv_button.clicked.connect(lambda: self.main_widget.slideInIdx(1))
        self.main_layout.addWidget(self.adv_button)

        # Screen Brightness
        self.screen_bright_box = QGroupBox(strings.SETTINGS_SCREEN_BR_G)
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
            pass
        else:
            result = subprocess.result = subprocess.run(['cat', settings["backlight_dir"] + "brightness"],
                                                        stdout=subprocess.PIPE)
            self.screen_bright_slider.setValue(int(result.stdout))

        self.display_layout.addWidget(self.screen_bright_box)

        self.theme_box = QGroupBox(strings.SETTINGS_RUN_THEME_G)
        self.theme_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.theme_layout = QHBoxLayout()
        self.theme_box.setLayout(self.theme_layout)
        self.display_layout.addWidget(self.theme_box)

        self.theme_picker = QComboBox()
        self.theme_picker.setObjectName("Kevinbot3_RemoteUI_Combo")
        self.theme_picker.blockSignals(True)
        self.theme_picker.currentIndexChanged.connect(self.change_theme)
        self.theme_picker.setFixedHeight(36)
        self.theme_layout.addWidget(self.theme_picker)

        self.runner_theme_flat = QCheckBox(strings.SETTINGS_TICK_FLAT)
        self.runner_theme_flat.setFixedWidth(self.runner_theme_flat.sizeHint().width())
        self.runner_theme_flat.setChecked(settings["apps"]["theme_flat"])
        self.runner_theme_flat.clicked.connect(self.runner_theme_flat_changed)
        self.theme_layout.addWidget(self.runner_theme_flat)

        self.app_theme_box = QGroupBox(strings.SETTINGS_APP_THEME_G)
        self.app_theme_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.app_theme_layout = QHBoxLayout()
        self.app_theme_box.setLayout(self.app_theme_layout)
        self.display_layout.addWidget(self.app_theme_box)

        self.app_theme_picker = QComboBox()
        self.app_theme_picker.setObjectName("Kevinbot3_RemoteUI_Combo")
        self.app_theme_picker.blockSignals(True)
        self.app_theme_picker.currentIndexChanged.connect(self.change_app_theme)
        self.app_theme_picker.setFixedHeight(36)
        self.app_theme_layout.addWidget(self.app_theme_picker)

        self.app_theme_customizer = QComboBox()
        self.app_theme_customizer.setPlaceholderText("Default")
        self.app_theme_customizer.setFixedWidth(120)
        self.app_theme_customizer.currentIndexChanged.connect(self.change_app_theme)
        self.app_theme_layout.addWidget(self.app_theme_customizer)

        for name in settings["apps"]["themes"]:
            self.theme_picker.addItem(name)
        self.theme_picker.setCurrentIndex(settings["apps"]["themes"].index(settings["apps"]["theme_name"]))
        self.theme_picker.blockSignals(False)

        for pair in THEME_PAIRS:
            self.app_theme_picker.addItem(pair[0])
            if pair[1] == settings["window_properties"]["theme"]:
                self.app_theme_picker.setCurrentText(pair[0])
                if "custom" in str(pair[0]).lower():
                    self.app_theme_customizer.setEnabled(True)
                    self.app_theme_customizer.addItems(pair[2])
                else:
                    self.app_theme_customizer.setEnabled(False)
                    for i in range(self.app_theme_customizer.count()):
                        self.app_theme_customizer.removeItem(i)
        self.app_theme_picker.blockSignals(False)

        try:
            self.app_theme_customizer.setCurrentText(settings["window_properties"]["theme_colors"])
        except NameError:
            pass

        self.animation_box = QGroupBox(strings.SETTINGS_ANIM_SPD_G)
        self.animation_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.animation_layout = QVBoxLayout()
        self.animation_box.setLayout(self.animation_layout)
        self.display_layout.addWidget(self.animation_box)

        self.animation_spinner = QSpinner()
        self.animation_spinner.spinbox.setMaximum(500)
        self.animation_spinner.spinbox.setMinimum(50)
        self.animation_spinner.spinbox.setSingleStep(25)
        self.animation_spinner.spinbox.valueChanged.connect(self.set_animation_speed)
        self.animation_spinner.setValue(settings["window_properties"]["animation_speed"])
        self.animation_layout.addWidget(self.animation_spinner)

        if is_tool("xscreensaver"):
            self.ss_box = QGroupBox(strings.SETTINGS_XSC_G)
            self.ss_box.setObjectName("Kevinbot3_RemoteUI_Group")
            self.ss_box_layout = QVBoxLayout()
            self.ss_box.setLayout(self.ss_box_layout)
            self.display_layout.addWidget(self.ss_box)

            self.xsc_config = xSc.ConfigParser("/home/$USER/.xscreensaver".replace("$USER", os.getenv("USER")))

            self.preview_ss_button = QPushButton(strings.SETTINGS_XSC_PREVIEW_B)
            self.preview_ss_button.clicked.connect(lambda: os.system("xscreensaver-command -activate"))

            self.ss_timeout_spinner = QSpinner(strings.SETTINGS_XSC_TIME_S)
            self.ss_timeout_spinner.setSuffix(strings.SETTINGS_XSC_TIME_SUF)
            self.ss_timeout_spinner.spinbox.valueChanged.connect(self.ss_timeout_changed)
            self.ss_timeout_spinner.setValue(int(self.xsc_config.read()["timeout"].split(":")[1]))

            self.ss_enable_checkbox = QCheckBox(strings.SETTINGS_TICK_ENABLE)
            self.ss_enable_checkbox.stateChanged.connect(self.ss_enable_changed)
            
            if self.xsc_config.read()["mode"] == "one":
                self.ss_timeout_spinner.setDisabled(False)
                self.ss_enable_checkbox.setChecked(True)
            else:
                self.ss_timeout_spinner.setDisabled(True)
                self.ss_enable_checkbox.setChecked(False)

            self.ss_box_layout.addWidget(self.ss_enable_checkbox)
            self.ss_box_layout.addWidget(self.ss_timeout_spinner)
            self.ss_box_layout.addWidget(self.preview_ss_button)

        self.exit_themes = haptics.HPushButton()
        self.exit_themes.clicked.connect(lambda: self.main_widget.slideInIdx(0))
        self.exit_themes.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_themes.setFixedSize(QSize(36, 36))
        self.exit_themes.setIconSize(QSize(32, 32))
        self.display_layout.addWidget(self.exit_themes)

        self.speed_box = QGroupBox(strings.SETTINGS_SPEED_G)
        self.speed_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.speed_layout = QHBoxLayout()
        self.speed_box.setLayout(self.speed_layout)
        self.robot_layout.addWidget(self.speed_box)

        self.max_us_label = QLabel(strings.SETTINGS_MAX_US_L)
        self.max_us_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.speed_layout.addWidget(self.max_us_label)

        self.max_us_spinner = QSpinner()
        self.max_us_spinner.setMaximum(1400)
        self.max_us_spinner.setMinimum(1000)
        self.max_us_spinner.setSingleStep(25)
        self.max_us_spinner.setValue(settings["max_us"])
        self.max_us_spinner.spinbox.valueChanged.connect(self.max_us_changed)
        self.speed_layout.addWidget(self.max_us_spinner)

        # Camera URL

        self.cam_url = QGroupBox(strings.SETTINGS_CAM_URL_G)
        self.cam_url.setObjectName("Kevinbot3_RemoteUI_Group")
        self.cam_layout = QHBoxLayout()
        self.cam_url.setLayout(self.cam_layout)
        self.robot_layout.addWidget(self.cam_url)

        self.cam_url_input = QLineEdit()
        self.cam_url_input.setObjectName("Kevinbot3_RemoteUI_SpeechInput")
        self.cam_url_input.setText(settings["camera_url"])
        self.cam_url_input.setFixedHeight(32)
        self.cam_url_input.textChanged.connect(self.save_url)
        self.cam_url_input.setStyleSheet("font-size: 14px;")
        self.cam_layout.addWidget(self.cam_url_input)

        self.cam_validate = QPushButton(strings.SETTINGS_VALIDATE_URL_B)
        self.cam_validate.setFixedHeight(32)
        self.cam_validate.setFixedWidth(self.cam_validate.sizeHint().width() + 10)
        self.cam_validate.clicked.connect(self.validate_url)
        self.cam_validate.setObjectName("Kevinbot3_RemoteUI_Button")
        self.cam_layout.addWidget(self.cam_validate)

        self.exit_robot = haptics.HPushButton()
        self.exit_robot.clicked.connect(lambda: self.main_widget.slideInIdx(0))
        self.exit_robot.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_robot.setFixedSize(QSize(36, 36))
        self.exit_robot.setIconSize(QSize(32, 32))
        self.robot_layout.addWidget(self.exit_robot)

        self.homepage_box = QGroupBox(strings.SETTINGS_HOMEPAGE_G)
        self.homepage_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.homepage_layout = QVBoxLayout()
        self.homepage_box.setLayout(self.homepage_layout)
        self.web_layout.addWidget(self.homepage_box)

        self.homepage_line = QLineEdit()
        self.homepage_line.setPlaceholderText("http://www.example.com")
        self.homepage_line.setText(settings["homepage"])
        self.homepage_line.textChanged.connect(self.update_homepage)
        self.homepage_layout.addWidget(self.homepage_line)

        self.exit_web = haptics.HPushButton()
        self.exit_web.clicked.connect(lambda: self.main_widget.slideInIdx(0))
        self.exit_web.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_web.setFixedSize(QSize(36, 36))
        self.exit_web.setIconSize(QSize(32, 32))
        self.web_layout.addWidget(self.exit_web)

        self.remote_box = QGroupBox(strings.SETTINGS_REMOTE_G)
        self.remote_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.remote_box_layout = QVBoxLayout()
        self.remote_box.setLayout(self.remote_box_layout)
        self.remote_layout.addWidget(self.remote_box)

        self.name_edit = QNamedLineEdit(strings.SETTINGS_NICKNAME_L)
        self.remote_box_layout.addWidget(self.name_edit)
        try:
            self.name_edit.lineedit.setText(settings["name"])
        except KeyError:
            self.name_edit.lineedit.setText("KBOT_REMOTE")
        self.name_edit.lineedit.textChanged.connect(self.name_change)

        self.joy_size_layout = QHBoxLayout()
        self.remote_box_layout.addLayout(self.joy_size_layout)

        self.joy_size_label = QLabel(strings.SETTINGS_STICK_SIZE_L)
        self.joy_size_layout.addWidget(self.joy_size_label)

        self.small_joy_radio = QRadioButton(strings.SETTINGS_RAD_SMALL)
        self.small_joy_radio.clicked.connect(lambda: self.set_joy_size(60))
        self.joy_size_layout.addWidget(self.small_joy_radio)

        self.large_joy_radio = QRadioButton(strings.SETTINGS_RAD_LARGE)
        self.large_joy_radio.clicked.connect(lambda: self.set_joy_size(80))
        self.joy_size_layout.addWidget(self.large_joy_radio)

        self.xlarge_joy_radio = QRadioButton(strings.SETTINGS_RAD_X_LARGE)
        self.xlarge_joy_radio.clicked.connect(lambda: self.set_joy_size(86))
        self.joy_size_layout.addWidget(self.xlarge_joy_radio)

        if settings["joystick_size"] == 60:
            self.small_joy_radio.setChecked(True)
        elif settings["joystick_size"] == 80:
            self.large_joy_radio.setChecked(True)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.remote_box_layout.addWidget(self.line)

        self.joy_mode_group = QButtonGroup()

        self.joy_mode_layout = QHBoxLayout()
        self.remote_box_layout.addLayout(self.joy_mode_layout)

        self.joy_mode_label = QLabel(strings.SETTINGS_STICK_MODE_L)
        self.joy_mode_layout.addWidget(self.joy_mode_label)

        self.analog_joy_radio = QRadioButton(strings.SETTINGS_RAD_ANALOG)
        self.analog_joy_radio.clicked.connect(lambda: self.set_joy_mode("analog"))
        self.joy_mode_group.addButton(self.analog_joy_radio)
        self.joy_mode_layout.addWidget(self.analog_joy_radio)

        self.digital_joy_radio = QRadioButton(strings.SETTINGS_RAD_DIGITAL)
        self.digital_joy_radio.clicked.connect(lambda: self.set_joy_mode("digital"))
        self.joy_mode_group.addButton(self.digital_joy_radio)
        self.joy_mode_layout.addWidget(self.digital_joy_radio)

        if settings["joystick_type"] == "analog":
            self.analog_joy_radio.setChecked(True)
        elif settings["joystick_type"] == "digital":
            self.digital_joy_radio.setChecked(True)

        self.exit_remote = haptics.HPushButton()
        self.exit_remote.clicked.connect(lambda: self.main_widget.slideInIdx(0))
        self.exit_remote.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_remote.setFixedSize(QSize(36, 36))
        self.exit_remote.setIconSize(QSize(32, 32))
        self.remote_layout.addWidget(self.exit_remote)

        # Exit
        self.exit_layout = QHBoxLayout()
        self.exit_button = haptics.HPushButton()
        self.exit_button.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.exit_button.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.exit_button.setIconSize(QSize(32, 32))
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setFixedSize(QSize(36, 36))
        self.exit_layout.addWidget(self.exit_button)
        self.main_layout.addLayout(self.exit_layout)

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def change_backlight(self):
        if is_pi():
            os.system(f"echo {self.screen_bright_slider.value()} > {settings['backlight_dir']}brightness")
        else:
            print(f"Brightness: {self.screen_bright_slider.value()}")

    def validate_url(self):
        if uri_validator(self.cam_url_input.text()):
            message = QMessageBox(self)
            message.setIcon(QMessageBox.Information)
            message.setText(strings.SETTINGS_MSG_VALID_URL)
            message.setWindowTitle(strings.SETTINGS_WIN_URL_VALIDATOR)
            message.exec_()
        else:
            message = QMessageBox(self)
            message.setIcon(QMessageBox.Warning)
            message.setText(strings.SETTINGS_MSG_INVALID_URL)
            message.setWindowTitle(strings.SETTINGS_WIN_URL_VALIDATOR)
            message.exec_()

    def save_url(self):
        settings["camera_url"] = self.cam_url_input.text()
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def max_us_changed(self):
        settings["max_us"] = self.max_us_spinner.spinbox.value()
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    @staticmethod
    def set_joy_size(value):
        settings["joystick_size"] = value
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    @staticmethod
    def set_joy_mode(value):
        settings["joystick_type"] = value
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def change_theme(self):
        index = self.theme_picker.currentIndex()
        file_name = settings["apps"]["theme_files"][index]
        effect = settings["apps"]["theme_effects"][index]
        settings["apps"]["theme"] = file_name
        settings["apps"]["theme_effect"] = effect
        settings["apps"]["theme_name"] = self.theme_picker.currentText()

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def change_app_theme(self):
        combo_val = self.app_theme_picker.currentText()
        for pair in THEME_PAIRS:
            if pair[0] == combo_val:
                settings["window_properties"]["theme"] = pair[1]
                    
                if "custom" in str(pair[0]).lower():
                    self.app_theme_customizer.setEnabled(True)
                    if settings["window_properties"]["theme_colors"] == "null":
                        settings["window_properties"]["theme_colors"] = pair[2][0]
                else:
                    self.app_theme_customizer.setEnabled(False)
                    settings["window_properties"]["theme_colors"] = "null"

        settings["window_properties"]["theme_colors"] = self.app_theme_customizer.currentText()

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        load_theme(self, settings["window_properties"]["theme"], settings["window_properties"]["theme_colors"])

    def update_homepage(self):
        settings["homepage"] = self.homepage_line.text()

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def set_animation_speed(self):
        settings["window_properties"]["animation_speed"] = self.animation_spinner.spinbox.value()

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def ss_timeout_changed(self):
        value = self.ss_timeout_spinner.spinbox.value()
        self.xsc_config.update({"timeout": "0:{}:0".format(value)})   
        self.xsc_config.save()     

    def ss_enable_changed(self):
        enabled = self.ss_enable_checkbox.isChecked()
        if enabled:
            self.ss_timeout_spinner.setDisabled(False)
            self.xsc_config.update({"mode": "one"})   
        else:
            self.ss_timeout_spinner.setDisabled(True)
            self.xsc_config.update({"mode": "off"})
         
        self.xsc_config.save()     

    def name_change(self):
        name = self.name_edit.lineedit.text()
        settings["name"] = name

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def runner_theme_flat_changed(self):
        settings["apps"]["theme_flat"] = self.runner_theme_flat.isChecked()
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Remote Settings")
    app.setApplicationVersion("1.0")
    app.setWindowIcon(QIcon("icons/settings.svg"))
    window = MainWindow()
    sys.exit(app.exec_())
