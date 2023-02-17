#!/usr/bin/python
import importlib
import json
import os
import platform
import sys
import subprocess
from urllib.parse import urlparse

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from QCustomWidgets import QSpinner, QNamedLineEdit, KBMainWindow
from SlidingStackedWidget import SlidingStackedWidget
from json_editor import Editor
from utils import load_theme, detect_dark, is_tool, is_pi
import qtawesome as qta
import xscreensaver_config.ConfigParser as xSc

import haptics
import strings
from functools import partial

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
if "theme_flat" not in settings["apps"]:
    settings["apps"]["theme_flat"] = False  # save default
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

THEME_PAIRS = [
    ("Kevinbot Dark", "qdarktheme_kbot"),
    ("QDarkTheme Dark", "qdarktheme", ["Default", "Teal", "Green", "Purple", "Orange", "Red", "White"]),
    ("QDarkTheme Light", "qdarktheme_light", ["Default", "Teal", "Green", "Purple", "Orange", "Red", "Black"]),
    ("High Contrast", "highcontrast", ["Default", "Light"]),
    ("Breeze Dark", "breeze_dark"),
    ("Breeze Light", "breeze_light"),
    ("Kevinbot Dark (Old)", "classic"),
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
class MainWindow(KBMainWindow):
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

        self.adv_warning = QLabel(strings.SETTINGS_ADV_WARNING)
        self.adv_warning.setObjectName("Kevinbot3_RemoteUI_Warning")
        self.adv_warning.setStyleSheet("color: #ffffff;"
                                       "background-color: #df574d;"
                                       "height: 36px;"
                                       "font-weight: bold;")
        self.adv_warning.setFixedHeight(36)
        self.adv_warning.setFrameStyle(QFrame.Shape.Box)
        self.adv_warning.setAlignment(Qt.AlignCenter)
        self.adv_bottom_layout.addWidget(self.adv_warning)

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

        self.app_theme_widget = QWidget()
        self.main_widget.addWidget(self.app_theme_widget)

        self.remote_widget = QWidget()
        self.main_widget.addWidget(self.remote_widget)

        self.runner_theme_widget = QWidget()
        self.main_widget.addWidget(self.runner_theme_widget)

        self.remote_layout = QVBoxLayout()
        self.remote_widget.setLayout(self.remote_layout)

        self.web_layout = QVBoxLayout()
        self.web_widget.setLayout(self.web_layout)

        self.app_theme_layout = QVBoxLayout()
        self.app_theme_widget.setLayout(self.app_theme_layout)

        self.runner_theme_layout = QVBoxLayout()
        self.runner_theme_widget.setLayout(self.runner_theme_layout)

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
        self.remote_button.clicked.connect(lambda: self.main_widget.slideInIdx(6))
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

        self.animation_box = QGroupBox(strings.SETTINGS_ANIM_G)
        self.animation_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.animation_layout = QVBoxLayout()
        self.animation_box.setLayout(self.animation_layout)
        self.display_layout.addWidget(self.animation_box)

        self.animation_spinner = QSpinner(text=strings.SETTINGS_ANIM_SPEED, icon_color=self.fg_color)
        self.animation_spinner.spinbox.setMaximum(500)
        self.animation_spinner.spinbox.setMinimum(50)
        self.animation_spinner.spinbox.setSingleStep(25)
        self.animation_spinner.spinbox.valueChanged.connect(self.set_animation_speed)
        self.animation_spinner.setValue(settings["window_properties"]["animation_speed"])
        self.animation_layout.addWidget(self.animation_spinner)

        # App Themes

        self.app_themes_button = haptics.HPushButton(strings.SETTINGS_APP_THEMES)
        self.app_themes_button.setStyleSheet("text-align: left;")
        self.app_themes_button.setIcon(qta.icon("fa5s.palette", color=self.fg_color))
        self.app_themes_button.clicked.connect(lambda: self.main_widget.slideInIdx(5))
        self.app_themes_button.setIconSize(QSize(36, 36))
        self.display_layout.addWidget(self.app_themes_button)

        self.app_themes_scroll = QScrollArea()
        QScroller.grabGesture(self.app_themes_scroll, QScroller.LeftMouseButtonGesture)  # enable single-touch scroll
        self.app_themes_scroll.setWidgetResizable(True)
        self.app_theme_layout.addWidget(self.app_themes_scroll)

        self.app_theme_scroll_widget = QWidget()
        self.app_themes_scroll.setWidget(self.app_theme_scroll_widget)

        self.app_themes_scroll_layout = QGridLayout()
        self.app_theme_scroll_widget.setLayout(self.app_themes_scroll_layout)

        for i in range(len(THEME_PAIRS)):
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            self.app_themes_scroll_layout.addWidget(frame, i // 3, i % 3)

            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)

            image = QLabel()
            image.setAlignment(Qt.AlignCenter)
            image.setPixmap(QPixmap(os.path.join(os.curdir, "res/theme_previews", THEME_PAIRS[i][1] + ".png")))
            frame_layout.addWidget(image)

            label = QLabel(THEME_PAIRS[i][0])
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14px")
            frame_layout.addWidget(label)

            button_layout = QHBoxLayout()
            frame_layout.addLayout(button_layout)

            enable = haptics.HPushButton("Enable")
            if settings["window_properties"]["theme"] == THEME_PAIRS[i][1]:
                enable.setText("Active")
                enable.setEnabled(False)
            button_layout.addWidget(enable)

            if len(THEME_PAIRS[i]) == 3:
                customizer = QComboBox()
                customizer.setPlaceholderText("Default")
                customizer.setFixedWidth(120)
                customizer.setEnabled(not enable.isEnabled())
                customizer.currentIndexChanged.connect(partial(self.activate_custom, customizer))
                button_layout.addWidget(customizer)

                for item in THEME_PAIRS[i][2]:
                    customizer.addItem(item)
                    if settings["window_properties"]["theme"] == THEME_PAIRS[i][1] and len(THEME_PAIRS[i]) == 3:
                        customizer.setCurrentText(settings["window_properties"]["theme_colors"])

                enable.clicked.connect(partial(self.activate_theme, THEME_PAIRS[i][1], enable, customizer))
            else:
                enable.clicked.connect(partial(self.activate_theme, THEME_PAIRS[i][1], enable))

        # Runner Themes

        self.runner_themes_button = haptics.HPushButton(strings.SETTINGS_RUNNER_THEMES)
        self.runner_themes_button.setStyleSheet("text-align: left;")
        self.runner_themes_button.setIcon(qta.icon("fa5s.rocket", color=self.fg_color))
        self.runner_themes_button.clicked.connect(lambda: self.main_widget.slideInIdx(7))
        self.runner_themes_button.setIconSize(QSize(36, 36))
        self.display_layout.addWidget(self.runner_themes_button)

        self.runner_themes_scroll = QScrollArea()
        QScroller.grabGesture(self.runner_themes_scroll,
                              QScroller.LeftMouseButtonGesture)  # enable single-touch scroll
        self.runner_themes_scroll.setWidgetResizable(True)
        self.runner_theme_layout.addWidget(self.runner_themes_scroll)

        self.runner_theme_scroll_widget = QWidget()
        self.runner_themes_scroll.setWidget(self.runner_theme_scroll_widget)

        self.runner_themes_scroll_layout = QGridLayout()
        self.runner_theme_scroll_widget.setLayout(self.runner_themes_scroll_layout)

        runner_theme_pairs = []

        for filename in os.listdir(os.path.join(os.curdir, "themepacks")):
            if not filename == "__pycache__":
                theme = importlib.import_module(f"themepacks.{filename[:-3]}")
                runner_theme_pairs.append((filename, theme.NAME))

        for i in range(len(runner_theme_pairs)):
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            self.runner_themes_scroll_layout.addWidget(frame, i // 3, i % 3)

            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)

            image = QLabel()
            image.setAlignment(Qt.AlignCenter)
            if os.path.exists(os.path.join(os.curdir, "res/runner_theme_previews",
                                           runner_theme_pairs[i][1].replace(" ", "_") + ".png")):
                image.setPixmap(QPixmap(os.path.join(os.curdir, "res/runner_theme_previews",
                                                     runner_theme_pairs[i][1].replace(" ", "_") + ".png")))
            else:
                image.setPixmap(QPixmap(os.path.join(os.curdir, "res/runner_theme_previews/unknown.png")))
            frame_layout.addWidget(image)

            label = QLabel(runner_theme_pairs[i][1])
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14px")
            frame_layout.addWidget(label)

            button_layout = QHBoxLayout()
            frame_layout.addLayout(button_layout)

            enable = haptics.HPushButton("Enable")
            enable.clicked.connect(partial(self.set_runner_theme, runner_theme_pairs[i][0], enable))
            if settings["apps"]["theme"] == runner_theme_pairs[i][0]:
                enable.setText("Active")
                enable.setEnabled(False)
            button_layout.addWidget(enable)

        self.exit_app_themes = haptics.HPushButton()
        self.exit_app_themes.clicked.connect(lambda: self.main_widget.slideInIdx(2))
        self.exit_app_themes.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_app_themes.setFixedSize(QSize(36, 36))
        self.exit_app_themes.setIconSize(QSize(32, 32))
        self.app_theme_layout.addWidget(self.exit_app_themes)

        self.runner_themes_bottom = QHBoxLayout()
        self.runner_theme_layout.addLayout(self.runner_themes_bottom)

        self.exit_runner_themes = haptics.HPushButton()
        self.exit_runner_themes.clicked.connect(lambda: self.main_widget.slideInIdx(2))
        self.exit_runner_themes.setIcon(qta.icon("fa5s.arrow-alt-circle-left", color=self.fg_color))
        self.exit_runner_themes.setFixedSize(QSize(36, 36))
        self.exit_runner_themes.setIconSize(QSize(32, 32))
        self.runner_themes_bottom.addWidget(self.exit_runner_themes)

        self.runner_themes_bottom.addStretch()

        self.runner_theme_flat = QCheckBox(strings.SETTINGS_TICK_FLAT)
        self.runner_theme_flat.setChecked(settings["apps"]["theme_flat"])
        self.runner_theme_flat.clicked.connect(self.runner_theme_flat_changed)
        self.runner_themes_bottom.addWidget(self.runner_theme_flat)

        if is_tool("xscreensaver"):
            self.ss_box = QGroupBox(strings.SETTINGS_XSC_G)
            self.ss_box.setObjectName("Kevinbot3_RemoteUI_Group")
            self.ss_box_layout = QVBoxLayout()
            self.ss_box.setLayout(self.ss_box_layout)
            self.display_layout.addWidget(self.ss_box)

            self.xsc_config = xSc.ConfigParser("/home/$USER/.xscreensaver".replace("$USER", os.getenv("USER")))

            self.preview_ss_button = QPushButton(strings.SETTINGS_XSC_PREVIEW_B)
            self.preview_ss_button.clicked.connect(lambda: os.system("xscreensaver-command -activate"))

            self.ss_timeout_spinner = QSpinner(strings.SETTINGS_XSC_TIME_S, icon_color=self.fg_color)
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

        self.max_us_spinner = QSpinner(icon_color=self.fg_color)
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

        if settings["dev_mode"]:
            self.createDevTools()

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

    def set_runner_theme(self, name, button):
        settings["apps"]["theme"] = name
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        for i in range(self.runner_themes_scroll_layout.count()):
            self.runner_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout().itemAt(0).widget() \
                .setEnabled(True)  # enable button
            self.runner_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout().itemAt(0).widget() \
                .setText("Enable")  # set button text

        button.setText("Active")
        button.setEnabled(False)

    def change_theme(self):
        index = self.theme_picker.currentIndex()
        file_name = settings["apps"]["theme_files"][index]
        settings["apps"]["theme"] = file_name
        settings["apps"]["theme_name"] = self.theme_picker.currentText()

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

    def activate_theme(self, theme, button, customizer=None):
        settings["window_properties"]["theme"] = theme

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        load_theme(self, settings["window_properties"]["theme"], settings["window_properties"]["theme_colors"])

        for i in range(self.app_themes_scroll_layout.count()):
            self.app_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout().itemAt(0).widget() \
                .setEnabled(True)  # enable button
            self.app_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout().itemAt(0).widget() \
                .setText("Enable")  # set button text
            if len(self.app_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout()) > 1:
                self.app_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout().itemAt(1).widget() \
                    .setEnabled(False)  # disable combobox
                self.app_themes_scroll_layout.itemAt(i).widget().layout().itemAt(2).layout().itemAt(1).widget() \
                    .setCurrentIndex(0)  # set current index

        button.setText("Active")
        button.setEnabled(False)

        if customizer:
            customizer.setEnabled(True)

    def activate_custom(self, customizer: QComboBox):
        settings["window_properties"]["theme_colors"] = customizer.currentText()

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        load_theme(self, settings["window_properties"]["theme"], settings["window_properties"]["theme_colors"])

    def change_app_theme(self):
        combo_val = self.app_theme_picker.currentText()

        theme_color = self.app_theme_customizer.currentText()
        settings["window_properties"]["theme_colors"] = self.app_theme_customizer.currentText()

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

        self.app_theme_customizer.blockSignals(True)
        self.app_theme_customizer.clear()
        self.app_theme_customizer.blockSignals(False)

        for pair in THEME_PAIRS:
            if pair[1] == settings["window_properties"]["theme"]:
                if "custom" in str(pair[0]).lower():
                    self.app_theme_customizer.addItems(pair[2])

        self.app_theme_customizer.blockSignals(True)
        self.app_theme_customizer.setCurrentText(theme_color)
        self.app_theme_customizer.blockSignals(False)

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
