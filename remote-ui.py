#!/usr/bin/python

# The GUI for the Kevinbot v3 Control using PyQt5

import datetime
import json
import platform
import sys
from functools import partial

# noinspection PyUnresolvedReferences
import PyQt5  # useful for using debuggers

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWebEngineWidgets import *
from qtpy.QtWidgets import *
from qt_thread_updater import get_updater
from QCustomWidgets import KBModalBar, KBMainWindow, QSuperDial
import qtawesome as qta

import Joystick.Joystick as Joystick
import SlidingStackedWidget as SlidingStackedWidget
from level import Level
import com
import strings
from colorpicker.colorpicker import ColorPicker
from palette import PaletteGrid, PALETTES
from utils import *

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True
DEVEL_OPTIONS = True

ENABLE_BATT2 = True
THEME_FILE = "theme.qss"
CURRENT_ARM_POS = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 2 5dof arms
HIGH_INSIDE_TEMP = 45

__version__ = "v1.0.0"
__author__ = "Kevin Ahr"

window = None
disable_batt_modal = False
disable_temp_modal = False
enabled = False

# load settings from file
with open("settings.json", "r") as f:
    settings = json.load(f)


def save_settings():
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)


# load stick size settings
if "joystick_size" in settings:
    JOYSTICK_SIZE = settings["joystick_size"]
else:
    settings["joystick_size"] = 80  # save default
    JOYSTICK_SIZE = settings["joystick_size"]
    save_settings()

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
    save_settings()

# load voltage warning settings
if "warning_voltage" in settings:
    warning_voltage = settings["warning_voltage"]
else:
    settings["warning_voltage"] = 10  # save default
    warning_voltage = settings["warning_voltage"]
    save_settings()

# load temp warning settings
if "motor_temp_warning" in settings:
    HIGH_MOTOR_TEMP = settings["motor_temp_warning"]
else:
    settings["motor_temp_warning"] = 50  # save default
    HIGH_MOTOR_TEMP = settings["motor_temp_warning"]
    save_settings()

# if windows
if platform.system() == "Windows":
    import ctypes

    # show icon in taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Kevinbot3 Remote")

try:
    remote_name = settings["name"]
except KeyError:
    remote_name = "KBOT_REMOTE"


# noinspection PyAttributeOutsideInit,PyArgumentList
class RemoteUI(KBMainWindow):
    # noinspection PyArgumentList
    def __init__(self):
        super(RemoteUI, self).__init__()

        self.setObjectName("Kevinbot3_RemoteUI")
        self.setWindowTitle(strings.WIN_TITLE)
        self.setWindowIcon(QIcon('icons/icon.svg'))

        # start coms
        com.init(callback=self.serial_callback)
        init_robot()

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setFixedSize(800, 480)

        # load theme
        try:
            load_theme(self, settings["window_properties"]["theme"], settings["window_properties"]["theme_colors"])
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        # vars
        self.modal_count = 0
        self.modals = []

        self.init_ui()

        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    @staticmethod
    def serial_callback(message):
        data = message["rf_data"].decode("utf-8")
        data = data.split("=", maxsplit=1)

        if data[0] == "batt_volts":
            if window is not None:
                volt1, volt2 = data[1].split(",")
                get_updater().call_latest(window.batt_volt1.setText, strings.BATT_VOLT1.format(float(volt1) / 10) + "V")
                get_updater().call_latest(window.battery1_label.setText, strings.BATT_VOLT1.format(float(volt1) / 10))

                if float(volt1) / 10 < warning_voltage:
                    get_updater().call_latest(window.battery1_label.setStyleSheet, "background-color: #df574d;")
                else:
                    get_updater().call_latest(window.battery1_label.setStyleSheet, "")

                if ENABLE_BATT2:
                    get_updater().call_latest(window.batt_volt2.setText,
                                              strings.BATT_VOLT2.format(float(volt2) / 10) + "V")
                    get_updater().call_latest(window.battery2_label.setText,
                                              strings.BATT_VOLT2.format(float(volt2) / 10))
                    if float(volt2) / 10 < warning_voltage:
                        get_updater().call_latest(window.battery2_label.setStyleSheet, "background-color: #df574d;")
                    else:
                        get_updater().call_latest(window.battery2_label.setStyleSheet, "")

                if not disable_batt_modal:
                    if float(volt1) / 10 < 11:
                        com.txmot([1500, 1500])
                        get_updater().call_latest(window.battModalText.setText, strings.BATT_LOW)
                        get_updater().call_latest(window.batt_modal.show)
                    elif float(volt2) / 10 < 11:
                        com.txmot([1500, 1500])
                        get_updater().call_latest(window.battModalText.setText, strings.BATT_LOW)
                        get_updater().call_latest(window.batt_modal.show)
        # bme280 sensor
        elif data[0] == "bme":
            if window is not None:
                get_updater().call_latest(window.outside_temp.setText,
                                          strings.OUTSIDE_TEMP.format(str(data[1].split(",")[0]) + "℃ (" + str(
                                              data[1].split(",")[1]) + "℉)"))
                get_updater().call_latest(window.outside_humi.setText,
                                          strings.OUTSIDE_HUMI.format(data[1].split(",")[2]))
                get_updater().call_latest(window.outside_hpa.setText,
                                          strings.OUTSIDE_PRES.format(data[1].split(",")[3]))
        # motor, body temps
        elif data[0] == "temps":
            if window is not None:
                get_updater().call_latest(window.left_temp.setText,
                                          strings.LEFT_TEMP.format(rstr(data[1].split(",")[0]) + "℃ (" +
                                                                   rstr(convert_c_to_f(
                                                                       float(data[1].split(",")[0]))) + "℉)"))
                get_updater().call_latest(window.right_temp.setText,
                                          strings.RIGHT_TEMP.format(rstr(data[1].split(",")[1]) + "℃ (" +
                                                                    rstr(convert_c_to_f(
                                                                        float(data[1].split(",")[1]))) + "℉)"))

                get_updater().call_latest(window.robot_temp.setText,
                                          strings.INSIDE_TEMP.format(rstr(data[1].split(",")[2]) + "℃ (" +
                                                                     rstr(convert_c_to_f(
                                                                         float(data[1].split(",")[2]))) + "℉)"))

                if float(data[1].split(",")[0]) > HIGH_MOTOR_TEMP:
                    get_updater().call_latest(window.left_temp.setStyleSheet, "background-color: #df574d;")
                    get_updater().call_latest(window.motor_stick.setDisabled, True)
                    if not disable_temp_modal:
                        com.txmot([1500, 1500])
                        get_updater().call_latest(window.motTempModalText.setText, strings.MOT_TEMP_HIGH)
                        get_updater().call_latest(window.motTemp_modal.show)
                else:
                    get_updater().call_latest(window.left_temp.setStyleSheet, "")

                if float(data[1].split(",")[1]) > HIGH_MOTOR_TEMP:
                    get_updater().call_latest(window.right_temp.setStyleSheet, "background-color: #df574d;")
                    get_updater().call_latest(window.motor_stick.setDisabled, True)
                    if not disable_temp_modal:
                        com.txmot([1500, 1500])
                        get_updater().call_latest(window.motTempModalText.setText, strings.MOT_TEMP_HIGH)
                        get_updater().call_latest(window.motTemp_modal.show)
                else:
                    get_updater().call_latest(window.right_temp.setStyleSheet, "")

                if float(data[1].split(",")[2]) > HIGH_INSIDE_TEMP:
                    get_updater().call_latest(window.robot_temp.setStyleSheet, "background-color: #df574d;")
                else:
                    get_updater().call_latest(window.robot_temp.setStyleSheet, "")
        elif data[0] == "angle":
            if window is not None:
                get_updater().call_latest(window.level.setAngle, int(data[1]))
                if int(data[1]) > 18:
                    get_updater().call_latest(window.level.label.setStyleSheet, "background-color: #df574d;")
                    get_updater().call_latest(window.level.setLineColor, QColor("#df574d"))
                elif int(data[1]) > 10:
                    get_updater().call_latest(window.level.label.setStyleSheet, "background-color: #eebc2a;")
                    get_updater().call_latest(window.level.setLineColor, QColor("#eebc2a"))
                else:
                    get_updater().call_latest(window.level.label.setStyleSheet, "")
                    get_updater().call_latest(window.level.setLineColor, Qt.white)
        # remote disable
        elif data[0] == "remote.disableui":
            if str(data[1]).lower() == "true":
                get_updater().call_latest(window.arm_group.setDisabled, True)
                get_updater().call_latest(window.led_group.setDisabled, True)
                get_updater().call_latest(window.mainGroup.setDisabled, True)

            else:
                get_updater().call_latest(window.arm_group.setDisabled, False)
                get_updater().call_latest(window.led_group.setDisabled, False)
                get_updater().call_latest(window.mainGroup.setDisabled, False)

    # noinspection PyUnresolvedReferences
    def init_ui(self):
        self.widget = SlidingStackedWidget.SlidingStackedWidget()
        self.setCentralWidget(self.widget)

        self.widget.setDirection(settings["window_properties"]["animation_dir"])
        self.widget.setSpeed(settings["window_properties"]["animation_speed"])

        self.mainWidget = QWidget()
        self.mainWidget.setObjectName("Kevinbot3_RemoteUI_MainWidget")

        self.cameraWidget = QWidget()
        self.cameraWidget.setObjectName("Kevinbot3_RemoteUI_CameraWidget")

        self.headColorWidget = QWidget()
        self.headColorWidget.setObjectName("Kevinbot3_RemoteUI_HeadColorWidget")

        self.bodyColorWidget = QWidget()
        self.bodyColorWidget.setObjectName("Kevinbot3_RemoteUI_BodyColorWidget")

        self.baseColorWidget = QWidget()
        self.baseColorWidget.setObjectName("Kevinbot3_RemoteUI_BaseColorWidget")

        self.armPresetsWidget = QWidget()
        self.armPresetsWidget.setObjectName("Kevinbot3_RemoteUI_ArmPresetsWidget")

        self.eyeConfigWidget = QWidget()
        self.eyeConfigWidget.setObjectName("Kevinbot3_RemoteUI_EyeConfigWidget")

        self.sensorsWidget = QWidget()
        self.sensorsWidget.setObjectName("Kevinbot3_RemoteUI_SensorsWidget")

        self.layout = QVBoxLayout()
        self.mainWidget.setLayout(self.layout)
        self.widget.addWidget(self.mainWidget)

        self.camera_layout = QVBoxLayout()
        self.cameraWidget.setLayout(self.camera_layout)
        self.widget.addWidget(self.cameraWidget)

        self.headColorLayout = QHBoxLayout()
        self.headColorWidget.setLayout(self.headColorLayout)
        self.widget.addWidget(self.headColorWidget)

        self.bodyColorLayout = QHBoxLayout()
        self.bodyColorWidget.setLayout(self.bodyColorLayout)
        self.widget.addWidget(self.bodyColorWidget)

        self.base_color_layout = QHBoxLayout()
        self.baseColorWidget.setLayout(self.base_color_layout)
        self.widget.addWidget(self.baseColorWidget)

        self.arm_presets_layout = QVBoxLayout()
        self.armPresetsWidget.setLayout(self.arm_presets_layout)
        self.widget.addWidget(self.armPresetsWidget)

        self.eyeConfigLayout = QHBoxLayout()
        self.eyeConfigWidget.setLayout(self.eyeConfigLayout)
        self.widget.addWidget(self.eyeConfigWidget)

        self.sensor_layout = QHBoxLayout()
        self.sensorsWidget.setLayout(self.sensor_layout)
        self.widget.addWidget(self.sensorsWidget)

        self.widget.setCurrentIndex(0)

        self.arm_group = QGroupBox(strings.ARM_PRESET_G)
        self.arm_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.layout.addWidget(self.arm_group)

        self.arm_layout = QHBoxLayout()
        self.arm_group.setLayout(self.arm_layout)

        # Modal

        self.ensurePolished()
        self.init_batt_modal()
        self.init_mot_temp_modal()

        # Arm Presets

        self.arm_preset1 = QPushButton(strings.ARM_PRESETS[0])
        self.arm_preset1.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset2 = QPushButton(strings.ARM_PRESETS[1])
        self.arm_preset2.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset3 = QPushButton(strings.ARM_PRESETS[2])
        self.arm_preset3.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset4 = QPushButton(strings.ARM_PRESETS[3])
        self.arm_preset4.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset5 = QPushButton(strings.ARM_PRESETS[4])
        self.arm_preset5.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset6 = QPushButton(strings.ARM_PRESETS[5])
        self.arm_preset6.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset7 = QPushButton(strings.ARM_PRESETS[6])
        self.arm_preset7.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset8 = QPushButton(strings.ARM_PRESETS[7])
        self.arm_preset8.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset9 = QPushButton(strings.ARM_PRESETS[8])
        self.arm_preset9.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_set_preset = QPushButton(strings.ARM_SET_PRESET)
        self.arm_set_preset.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.arm_preset1.setFixedSize(60, 50)
        self.arm_preset2.setFixedSize(60, 50)
        self.arm_preset3.setFixedSize(60, 50)
        self.arm_preset4.setFixedSize(60, 50)
        self.arm_preset5.setFixedSize(60, 50)
        self.arm_preset6.setFixedSize(60, 50)
        self.arm_preset7.setFixedSize(60, 50)
        self.arm_preset8.setFixedSize(60, 50)
        self.arm_preset9.setFixedSize(60, 50)
        self.arm_set_preset.setFixedSize(60, 50)

        self.arm_preset1.clicked.connect(lambda: self.arm_action(0))
        self.arm_preset2.clicked.connect(lambda: self.arm_action(1))
        self.arm_preset3.clicked.connect(lambda: self.arm_action(2))
        self.arm_preset4.clicked.connect(lambda: self.arm_action(3))
        self.arm_preset5.clicked.connect(lambda: self.arm_action(4))
        self.arm_preset6.clicked.connect(lambda: self.arm_action(5))
        self.arm_preset7.clicked.connect(lambda: self.arm_action(6))
        self.arm_preset8.clicked.connect(lambda: self.arm_action(7))
        self.arm_preset9.clicked.connect(lambda: self.arm_action(8))
        self.arm_set_preset.clicked.connect(self.arm_edit_action)

        self.arm_preset1.setShortcut("1")
        self.arm_preset2.setShortcut("2")
        self.arm_preset3.setShortcut("3")
        self.arm_preset4.setShortcut("4")
        self.arm_preset5.setShortcut("5")
        self.arm_preset6.setShortcut("6")
        self.arm_preset7.setShortcut("7")
        self.arm_preset8.setShortcut("8")
        self.arm_preset9.setShortcut("9")

        self.arm_layout.addWidget(self.arm_preset1)
        self.arm_layout.addWidget(self.arm_preset2)
        self.arm_layout.addWidget(self.arm_preset3)
        self.arm_layout.addWidget(self.arm_preset4)
        self.arm_layout.addWidget(self.arm_preset5)
        self.arm_layout.addWidget(self.arm_preset6)
        self.arm_layout.addWidget(self.arm_preset7)
        self.arm_layout.addWidget(self.arm_preset8)
        self.arm_layout.addWidget(self.arm_preset9)
        self.arm_layout.addWidget(self.arm_set_preset)

        # LED Options

        self.led_group = QGroupBox(strings.LED_PRESET_G)
        self.led_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.layout.addWidget(self.led_group)

        self.led_layout = QHBoxLayout()
        self.led_group.setLayout(self.led_layout)

        self.head_led = QPushButton(strings.LED_HEAD)
        self.head_led.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.head_led.clicked.connect(lambda: self.led_action(0))
        self.led_layout.addWidget(self.head_led)

        self.body_led = QPushButton(strings.LED_BODY)
        self.body_led.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.body_led.clicked.connect(lambda: self.led_action(1))
        self.led_layout.addWidget(self.body_led)

        self.camera_led = QPushButton(strings.LED_CAMERA)
        self.camera_led.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.camera_led.clicked.connect(self.camera_led_action)
        self.led_layout.addWidget(self.camera_led)

        self.base_led = QPushButton(strings.LED_BASE)
        self.base_led.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.base_led.clicked.connect(lambda: self.led_action(2))
        self.led_layout.addWidget(self.base_led)

        self.eyeConfig = QPushButton(strings.LED_EYE_CONFIG)
        self.eyeConfig.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.eyeConfig.clicked.connect(self.eye_config_action)
        self.led_layout.addWidget(self.eyeConfig)

        # LED Button Heights
        self.head_led.setFixedHeight(24)
        self.body_led.setFixedHeight(24)
        self.camera_led.setFixedHeight(24)
        self.base_led.setFixedHeight(24)
        self.eyeConfig.setFixedHeight(24)

        # DPad, Joystick, and Speech

        self.mainGroup = QGroupBox(strings.MAIN_G)
        self.mainGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.layout.addWidget(self.mainGroup)

        self.mainLayout = QHBoxLayout()
        self.mainGroup.setLayout(self.mainLayout)

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[2])):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        self.motor_stick = Joystick.Joystick(color=self.fg_color, sticky=False, max_distance=JOYSTICK_SIZE)
        self.motor_stick.setObjectName("Kevinbot3_RemoteUI_Joystick")
        self.motor_stick.posChanged.connect(self.motor_action)
        self.motor_stick.centerEvent.connect(com.txstop)
        self.motor_stick.setMinimumSize(180, 180)
        self.mainLayout.addWidget(self.motor_stick)

        self.mainLayout.addStretch()

        self.speechWidget = QWidget()
        self.speechWidget.setObjectName("Kevinbot3_RemoteUI_SpeechWidget")
        self.mainLayout.addWidget(self.speechWidget)

        self.speechGrid = QGridLayout()
        self.speechWidget.setLayout(self.speechGrid)

        self.enable_button = QPushButton("ENABLE")
        self.enable_button.setObjectName("Enable_Button")
        self.enable_button.setMinimumHeight(56)
        self.enable_button.clicked.connect(lambda: self.set_enabled(True))
        self.speechGrid.addWidget(self.enable_button, 0, 0)

        self.disable_button = QPushButton("DISABLE")
        self.disable_button.setObjectName("Disable_Button")
        self.disable_button.setMinimumHeight(56)
        self.disable_button.clicked.connect(lambda: self.set_enabled(False))
        self.speechGrid.addWidget(self.disable_button, 0, 1)

        self.speechInput = QLineEdit()
        self.speechInput.setObjectName("Kevinbot3_RemoteUI_SpeechInput")
        self.speechInput.setText(settings["speech"]["text"])
        self.speechInput.returnPressed.connect(lambda: com.txcv("no-pass.speech", self.speechInput.text()))
        self.speechInput.setPlaceholderText(strings.SPEECH_INPUT_H)

        self.speechGrid.addWidget(self.speechInput, 1, 0, 1, 2)

        self.speechButton = QPushButton(strings.SPEECH_BUTTON)
        self.speechButton.setObjectName("Kevinbot3_RemoteUI_SpeechButton")
        self.speechButton.clicked.connect(lambda: com.txcv("no-pass.speech", self.speechInput.text()))
        self.speechButton.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.speechGrid.addWidget(self.speechButton, 2, 0, 1, 1)

        self.speechSave = QPushButton(strings.SPEECH_SAVE)
        self.speechSave.setObjectName("Kevinbot3_RemoteUI_SpeechButton")
        self.speechSave.clicked.connect(lambda: self.save_speech(self.speechInput.text()))
        self.speechSave.setShortcut(QKeySequence("Ctrl+S"))
        self.speechGrid.addWidget(self.speechSave, 2, 1, 1, 1)

        self.espeakRadio = QRadioButton(strings.SPEECH_ESPEAK)
        self.espeakRadio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.espeakRadio.setChecked(True)
        self.espeakRadio.pressed.connect(lambda: com.txcv("no-pass.speech-engine", "espeak"))
        self.espeakRadio.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.speechGrid.addWidget(self.espeakRadio, 3, 0, 1, 1)

        self.festivalRadio = QRadioButton(strings.SPEECH_FESTIVAL)
        self.festivalRadio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.festivalRadio.pressed.connect(lambda: com.txcv("no-pass.speech-engine", "festival"))
        self.festivalRadio.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.speechGrid.addWidget(self.festivalRadio, 3, 1, 1, 1)

        self.speechWidget.setFixedHeight(self.speechWidget.sizeHint().height())
        self.speechWidget.setFixedWidth(self.speechWidget.sizeHint().width() + 100)

        self.mainLayout.addStretch()

        self.head_stick = Joystick.Joystick(color=self.fg_color, max_distance=JOYSTICK_SIZE)
        self.head_stick.setObjectName("Kevinbot3_RemoteUI_Joystick")
        self.head_stick.posChanged.connect(self.head_changed_action)
        self.head_stick.setMinimumSize(180, 180)
        self.mainLayout.addWidget(self.head_stick)

        # Camera Page

        # Camera WebEngine
        self.cameraGroup = QGroupBox(strings.CAMERA_G)
        self.cameraGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.camera_layout.addWidget(self.cameraGroup)

        self.camera_layout = QVBoxLayout()
        self.cameraGroup.setLayout(self.camera_layout)

        self.cameraWebView = QWebEngineView()
        self.cameraWebView.setObjectName("Kevinbot3_RemoteUI_CameraWebView")
        self.camera_layout.addWidget(self.cameraWebView)

        # navigate to the camera page
        self.cameraWebView.load(QUrl(settings["camera_url"]))

        # Camera Leds
        self.cameraLedsGroup = QGroupBox(strings.CAMERA_LEDS_G)
        self.cameraLedsGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.camera_layout.addWidget(self.cameraLedsGroup)

        self.cameraLedsLayout = QHBoxLayout()
        self.cameraLedsGroup.setLayout(self.cameraLedsLayout)

        self.cameraLedSlider = QSlider(Qt.Orientation.Horizontal)
        self.cameraLedSlider.setObjectName("Kevinbot3_RemoteUI_CameraLedSlider")
        self.cameraLedSlider.valueChanged.connect(self.camera_brightness_changed)
        self.cameraLedSlider.setRange(0, 255)
        self.cameraLedsLayout.addWidget(self.cameraLedSlider)

        # Head Color Page

        # Back Button
        self.headColorBack = QPushButton()
        self.headColorBack.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.headColorBack.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.headColorBack.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.headColorBack.setIconSize(QSize(32, 32))
        self.headColorBack.setFixedSize(QSize(36, 36))
        self.headColorBack.setFlat(True)
        self.headColorLayout.addWidget(self.headColorBack)

        # Head Colorpicker
        self.headColorGroup = QGroupBox(strings.HEAD_COLOR_G)
        self.headColorGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.headColorLayout.addWidget(self.headColorGroup)

        self.headColorLayoutP = QGridLayout()
        self.headColorGroup.setLayout(self.headColorLayoutP)

        self.headColorPicker = ColorPicker()
        self.headColorPicker.setObjectName("Kevinbot3_RemoteUI_HeadColorPicker")
        self.headColorPicker.colorChanged.connect(self.head_color1_changed)
        self.headColorPicker.setHex("000000")
        self.headColorLayoutP.addWidget(self.headColorPicker, 0, 0)

        # Head Colorpicker 2
        self.headColorPicker2 = ColorPicker()
        self.headColorPicker2.setObjectName("Kevinbot3_RemoteUI_HeadColorPicker")
        self.headColorPicker2.colorChanged.connect(self.head_color2_changed)
        self.headColorPicker2.setHex("000000")
        self.headColorLayoutP.addWidget(self.headColorPicker2, 1, 0)

        # Head Animation Speed
        self.headSpeedBox = QGroupBox(strings.HEAD_SPEED_G)
        self.headSpeedBox.setObjectName("Kevinbot3_RemoteUI_Group")
        self.headColorLayoutP.addWidget(self.headSpeedBox, 0, 1)

        self.headSpeedLayout = QVBoxLayout()
        self.headSpeedBox.setLayout(self.headSpeedLayout)

        self.headSpeed = QSlider(Qt.Orientation.Horizontal)
        self.headSpeed.setRange(100, 500)
        self.headSpeed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.headSpeed.valueChanged.connect(lambda x: com.txcv("head_update", map_range(x, 100, 500, 500, 100)))
        self.headSpeedLayout.addWidget(self.headSpeed)

        # Head Effects
        self.headEffectsGroup = QGroupBox(strings.HEAD_EFFECTS_G)
        self.headEffectsGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.headColorLayout.addWidget(self.headEffectsGroup)

        self.headEffectsLayout = QGridLayout()
        self.headEffectsGroup.setLayout(self.headEffectsLayout)

        for i in range(len(settings["head_effects"])):
            effect_button = QPushButton(capitalize(settings["head_effects"][i]))
            effect_button.setObjectName("Kevinbot3_RemoteUI_HeadEffectButton")
            self.headEffectsLayout.addWidget(effect_button, i // 2, i % 2)
            effect_button.clicked.connect(partial(self.head_effect_action, i))
            effect_button.setFixedSize(QSize(75, 50))

        # Body Color Page

        # Back Button
        self.bodyColorBack = QPushButton()
        self.bodyColorBack.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.bodyColorBack.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.bodyColorBack.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.bodyColorBack.setIconSize(QSize(32, 32))
        self.bodyColorBack.setFixedSize(QSize(36, 36))
        self.bodyColorBack.setFlat(True)
        self.bodyColorLayout.addWidget(self.bodyColorBack)

        # Body Color picker
        self.bodyColorGroup = QGroupBox(strings.BODY_COLOR_G)
        self.bodyColorGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.bodyColorLayout.addWidget(self.bodyColorGroup)

        self.bodyColorLayoutP = QGridLayout()
        self.bodyColorGroup.setLayout(self.bodyColorLayoutP)

        self.bodyColorPicker = ColorPicker()
        self.bodyColorPicker.setObjectName("Kevinbot3_RemoteUI_BodyColorPicker")
        self.bodyColorPicker.colorChanged.connect(self.body_color1_changed)
        self.bodyColorPicker.setHex("000000")
        self.bodyColorLayoutP.addWidget(self.bodyColorPicker, 0, 0)

        # Body Color picker 2
        self.bodyColorPicker2 = ColorPicker()
        self.bodyColorPicker2.setObjectName("Kevinbot3_RemoteUI_BodyColorPicker")
        self.bodyColorPicker2.colorChanged.connect(self.body_color2_changed)
        self.bodyColorPicker2.setHex("000000")
        self.bodyColorLayoutP.addWidget(self.bodyColorPicker2, 1, 0)

        # Body Animation Speed
        self.bodySpeedBox = QGroupBox(strings.BODY_SPEED_G)
        self.bodySpeedBox.setObjectName("Kevinbot3_RemoteUI_Group")
        self.bodyColorLayoutP.addWidget(self.bodySpeedBox, 0, 1)

        self.bodySpeedLayout = QVBoxLayout()
        self.bodySpeedBox.setLayout(self.bodySpeedLayout)

        self.bodySpeed = QSlider(Qt.Orientation.Horizontal)
        self.bodySpeed.setRange(100, 500)
        self.bodySpeed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.bodySpeed.valueChanged.connect(lambda x: com.txcv("body_update", map_range(x, 100, 500, 500, 100)))
        self.bodySpeedLayout.addWidget(self.bodySpeed)

        # Body Effects
        self.body_effects_group = QGroupBox(strings.BODY_EFFECTS_G)
        self.body_effects_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.bodyColorLayout.addWidget(self.body_effects_group)

        self.body_effects_layout = QGridLayout()
        self.body_effects_group.setLayout(self.body_effects_layout)

        for i in range(len(settings["body_effects"])):
            if "*" not in settings["body_effects"][i]:
                effect_button = QPushButton(capitalize(settings["body_effects"][i]))
                effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
                self.body_effects_layout.addWidget(effect_button, i // 2, i % 2)
                effect_button.clicked.connect(partial(self.body_effect_action, i))
                effect_button.setFixedSize(QSize(75, 50))
            elif "*c" in settings["body_effects"][i]:
                dt = datetime.datetime.now()
                if dt.day in range(20, 27) and dt.month == 12:
                    effect_button = QPushButton(capitalize(settings["body_effects"][i]))
                    effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButtonEgg")
                    effect_button.clicked.connect(partial(self.body_effect_action, i))
                    self.body_effects_layout.addWidget(effect_button, (i // 2) + 1, i % 2)

        self.body_bright_plus = QPushButton("Bright+")
        self.body_bright_plus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.body_bright_plus.clicked.connect(lambda: com.txstr("body_bright+"))
        self.body_bright_plus.setFixedSize(QSize(75, 50))
        self.body_effects_layout.addWidget(self.body_bright_plus, (len(settings["body_effects"]) // 2),
                                           (len(settings["body_effects"]) % 2) - 1)

        self.body_bright_minus = QPushButton("Bright-")
        self.body_bright_minus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.body_bright_minus.clicked.connect(lambda: com.txstr("body_bright-"))
        self.body_bright_minus.setFixedSize(QSize(75, 50))
        self.body_effects_layout.addWidget(self.body_bright_minus, len(settings["body_effects"]) // 2,
                                           len(settings["body_effects"]) % 2)

        # Base Color Page

        # Back Button
        self.base_color_back = QPushButton()
        self.base_color_back.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.base_color_back.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.base_color_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.base_color_back.setIconSize(QSize(32, 32))
        self.base_color_back.setFixedSize(QSize(36, 36))
        self.base_color_back.setFlat(True)
        self.base_color_layout.addWidget(self.base_color_back)

        # Base Color picker
        self.baseColorGroup = QGroupBox(strings.BASE_COLOR_G)
        self.baseColorGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.base_color_layout.addWidget(self.baseColorGroup)

        self.base_color_layout_p = QGridLayout()
        self.baseColorGroup.setLayout(self.base_color_layout_p)

        self.base_color_picker = ColorPicker()
        self.base_color_picker.setObjectName("Kevinbot3_RemoteUI_BodyColorPicker")
        self.base_color_picker.colorChanged.connect(self.base_color1_changed)
        self.base_color_picker.setHex("000000")
        self.base_color_layout_p.addWidget(self.base_color_picker, 0, 0)

        # Base Color picker 2
        self.base_color_picker_2 = ColorPicker()
        self.base_color_picker_2.setObjectName("Kevinbot3_RemoteUI_BodyColorPicker")
        self.base_color_picker_2.colorChanged.connect(self.base_color2_changed)
        self.base_color_picker_2.setHex("000000")
        self.base_color_layout_p.addWidget(self.base_color_picker_2, 1, 0)

        # Base Animation Speed
        self.base_speed_box = QGroupBox(strings.BASE_SPEED_G)
        self.base_speed_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.base_color_layout_p.addWidget(self.base_speed_box, 0, 1)
        self.base_speed_layout = QVBoxLayout()

        self.base_speed = QSlider(Qt.Orientation.Horizontal)
        self.base_speed.setRange(100, 500)
        self.base_speed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.base_speed.valueChanged.connect(lambda x: com.txcv("base_update", map_range(x, 100, 500, 500, 100)))
        self.base_speed_layout.addWidget(self.base_speed)
        self.base_speed_box.setLayout(self.base_speed_layout)

        # Base Effects
        self.base_effects_group = QGroupBox(strings.BASE_EFFECTS_G)
        self.base_effects_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.base_color_layout.addWidget(self.base_effects_group)

        self.base_effects_layout = QGridLayout()
        self.base_effects_group.setLayout(self.base_effects_layout)

        for i in range(len(settings["base_effects"])):
            if "*" not in settings["base_effects"][i]:
                effect_button = QPushButton(capitalize(settings["base_effects"][i]))
                effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
                self.base_effects_layout.addWidget(effect_button, i // 2, i % 2)
                effect_button.clicked.connect(partial(self.base_effect_action, i))
                effect_button.setFixedSize(QSize(75, 50))
            elif "*c" in settings["base_effects"][i]:
                dt = datetime.datetime.now()
                if dt.day in range(20, 27) and dt.month == 12:
                    effect_button = QPushButton(capitalize(settings["base_effects"][i]))
                    effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButtonEgg")
                    effect_button.clicked.connect(partial(self.base_effect_action, i))
                    self.base_effects_layout.addWidget(effect_button, (i // 2) + 1, i % 2)

        self.base_bright_plus = QPushButton("Bright+")
        self.base_bright_plus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.base_bright_plus.clicked.connect(lambda: com.txstr("base_bright+"))
        self.base_bright_plus.setFixedSize(QSize(75, 50))
        self.base_effects_layout.addWidget(self.base_bright_plus, (len(settings["base_effects"]) // 2),
                                           (len(settings["base_effects"]) % 2) - 1)

        self.base_bright_minus = QPushButton("Bright-")
        self.base_bright_minus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.base_bright_minus.clicked.connect(lambda: com.txstr("base_bright-"))
        self.base_bright_minus.setFixedSize(QSize(75, 50))
        self.base_effects_layout.addWidget(self.base_bright_minus, len(settings["base_effects"]) // 2,
                                           len(settings["base_effects"]) % 2)

        # Arm Preset Editor

        # Title
        self.arm_preset_title = QLabel(strings.ARM_PRESET_EDIT_G)
        self.arm_preset_title.setObjectName("Kevinbot3_RemoteUI_Title")
        self.arm_preset_title.setAlignment(Qt.AlignCenter)
        self.arm_preset_title.setMaximumHeight(self.arm_preset_title.sizeHint().height())
        self.arm_presets_layout.addWidget(self.arm_preset_title)

        # Pick Preset
        self.arm_preset_group = QGroupBox(strings.PRESET_PICK)
        self.arm_preset_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.arm_presets_layout.addWidget(self.arm_preset_group)

        self.arm_preset_layout = QHBoxLayout()
        self.arm_preset_group.setLayout(self.arm_preset_layout)

        # add arm preset buttons
        for i in range(len(settings["arm_prog"])):
            preset_button = QPushButton(strings.ARM_PRESETS[i])
            preset_button.setObjectName("Kevinbot3_RemoteUI_ArmButton")
            preset_button.setFixedSize(QSize(50, 50))
            preset_button.clicked.connect(partial(self.arm_preset_action, i))
            self.arm_preset_layout.addWidget(preset_button)

        # Editor
        self.arm_preset_editor = QGroupBox(strings.ARM_PRESET_EDIT)
        self.arm_preset_editor.setObjectName("Kevinbot3_RemoteUI_Group")
        self.arm_presets_layout.addWidget(self.arm_preset_editor)

        self.arm_preset_editor_layout = QVBoxLayout()
        self.arm_preset_editor.setLayout(self.arm_preset_editor_layout)

        # current arm preset
        self.arm_preset_label = QLabel(strings.CURRENT_ARM_PRESET + ": Unset")
        self.arm_preset_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.arm_preset_label.setAlignment(Qt.AlignCenter)
        self.arm_preset_label.setMaximumHeight(self.arm_preset_label.minimumSizeHint().height())
        self.arm_preset_editor_layout.addWidget(self.arm_preset_label)

        # stretch
        self.arm_preset_editor_layout.addStretch()

        # left group box
        self.arm_preset_editor_left = QGroupBox(strings.ARM_PRESET_EDIT_L)
        self.arm_preset_editor_left.setObjectName("Kevinbot3_RemoteUI_Group")
        self.arm_preset_editor_layout.addWidget(self.arm_preset_editor_left)
        self.arm_preset_editor_left_layout = QHBoxLayout()
        self.arm_preset_editor_left.setLayout(self.arm_preset_editor_left_layout)

        # right group box
        self.arm_preset_editor_right = QGroupBox(strings.ARM_PRESET_EDIT_R)
        self.arm_preset_editor_right.setObjectName("Kevinbot3_RemoteUI_Group")
        self.arm_preset_editor_layout.addWidget(self.arm_preset_editor_right)
        self.arm_preset_editor_right_layout = QHBoxLayout()
        self.arm_preset_editor_right.setLayout(self.arm_preset_editor_right_layout)

        # use knobs and a label per servo

        self.left_knobs = []
        self.right_knobs = []
        self.left_labels = []
        self.right_labels = []

        for i in range(settings["arm_dof"]):
            # layout
            layout = QVBoxLayout()
            self.arm_preset_editor_left_layout.addLayout(layout)
            # knob
            self.left_knobs.append(QSuperDial(knob_radius=8, knob_margin=7))
            self.left_knobs[i].setObjectName("Kevinbot3_RemoteUI_ArmKnob")
            self.left_knobs[i].setRange(settings["arm_min_max"][i][0], settings["arm_min_max"][i][1])
            self.left_knobs[i].setValue(settings["arm_prog"][0][i])
            self.left_knobs[i].setFixedSize(QSize(72, 72))

            layout.addWidget(self.left_knobs[i])
            # label
            self.left_labels.append(QLabel(str(settings["arm_prog"][0][i])))
            self.left_labels[i].setObjectName("Kevinbot3_RemoteUI_ArmLabel")
            self.left_labels[i].setAlignment(Qt.AlignCenter)
            self.left_labels[i].setFixedSize(QSize(72, 24))
            layout.addWidget(self.left_labels[i])

            self.left_knobs[i].valueChanged.connect(partial(self.arm_preset_left_changed, i))

        for i in range(settings["arm_dof"]):
            # layout
            layout = QVBoxLayout()
            self.arm_preset_editor_right_layout.addLayout(layout)
            # knob
            self.right_knobs.append(QSuperDial(knob_radius=8, knob_margin=7))
            self.right_knobs[i].setObjectName("Kevinbot3_RemoteUI_ArmKnob")
            self.right_knobs[i].setRange(settings["arm_min_max"][i + settings["arm_dof"]][0],
                                         settings["arm_min_max"][i + settings["arm_dof"]][1])
            self.right_knobs[i].setValue(settings["arm_prog"][0][i + settings["arm_dof"]])
            self.right_knobs[i].setFixedSize(QSize(72, 72))
            layout.addWidget(self.right_knobs[i])
            # label
            self.right_labels.append(QLabel(str(settings["arm_prog"][0][i + settings["arm_dof"]])))
            self.right_labels[i].setObjectName("Kevinbot3_RemoteUI_ArmLabel")
            self.right_labels[i].setAlignment(Qt.AlignCenter)
            self.right_labels[i].setFixedSize(QSize(72, 24))
            layout.addWidget(self.right_labels[i])

            self.right_knobs[i].valueChanged.connect(partial(self.arm_preset_right_changed, i))

        # stretch
        self.arm_preset_editor_layout.addStretch()

        # Back button and save button

        self.arm_bottom_layout = QHBoxLayout()
        self.arm_presets_layout.addLayout(self.arm_bottom_layout)

        self.arm_preset_back = QPushButton()
        self.arm_preset_back.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.arm_preset_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.arm_preset_back.setFixedSize(QSize(36, 36))
        self.arm_preset_back.setIconSize(QSize(32, 32))
        self.arm_preset_back.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.arm_preset_back.setFlat(True)
        self.arm_bottom_layout.addWidget(self.arm_preset_back)

        self.arm_preset_save = QPushButton(" " * 5 + strings.SAVE)
        self.arm_preset_save.setObjectName("Kevinbot3_RemoteUI_ArmButton")
        self.arm_preset_save.setFixedHeight(36)
        self.arm_preset_save.setIcon(qta.icon("fa5.save", color=self.fg_color))
        self.arm_preset_save.setIconSize(QSize(32, 32))
        self.arm_preset_save.clicked.connect(self.arm_preset_save_action)
        self.arm_bottom_layout.addWidget(self.arm_preset_save)

        # Eye Configurator

        self.eye_config_back = QPushButton()
        self.eye_config_back.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.eye_config_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.eye_config_back.setFixedSize(QSize(36, 36))
        self.eye_config_back.setIconSize(QSize(32, 32))
        self.eye_config_back.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.eye_config_back.setFlat(True)
        self.eyeConfigLayout.addWidget(self.eye_config_back)

        # group box
        self.eyeConfigGroup = QGroupBox(strings.EYE_CONFIG_G)
        self.eyeConfigGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigLayout.addWidget(self.eyeConfigGroup)
        self.eye_config_group_layout = QGridLayout()
        self.eyeConfigGroup.setLayout(self.eye_config_group_layout)

        # background group box
        self.eyeConfigBackground = QGroupBox(strings.EYE_CONFIG_B_G)
        self.eyeConfigBackground.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_group_layout.addWidget(self.eyeConfigBackground, 0, 0)
        self.eyeConfigBackgroundLayout = QHBoxLayout()
        self.eyeConfigBackground.setLayout(self.eyeConfigBackgroundLayout)

        # background image
        self.eyeConfigBackgroundImage = QLabel()
        self.eyeConfigBackgroundImage.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eyeConfigBackgroundImage.setPixmap(QPixmap("icons/eye-bg.svg"))
        self.eyeConfigBackgroundImage.setAlignment(Qt.AlignCenter)
        self.eyeConfigBackgroundLayout.addWidget(self.eyeConfigBackgroundImage)

        # palette
        self.eyeConfigPalette = PaletteGrid(colors=PALETTES['kevinbot'])
        self.eyeConfigPalette.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eyeConfigPalette.setFixedSize(self.eyeConfigPalette.sizeHint())
        self.eyeConfigPalette.selected.connect(self.eye_config_palette_selected)
        self.eyeConfigBackgroundLayout.addWidget(self.eyeConfigPalette)

        # pupil group box
        self.eye_config_pupil = QGroupBox(strings.EYE_CONFIG_P_G)
        self.eye_config_pupil.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_group_layout.addWidget(self.eye_config_pupil, 0, 1)
        self.eye_config_pupil_layout = QHBoxLayout()
        self.eye_config_pupil.setLayout(self.eye_config_pupil_layout)

        # pupil image
        self.eye_config_pupil_image = QLabel()
        self.eye_config_pupil_image.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eye_config_pupil_image.setPixmap(QPixmap("icons/eye-pupil.svg"))
        self.eye_config_pupil_image.setAlignment(Qt.AlignCenter)
        self.eye_config_pupil_layout.addWidget(self.eye_config_pupil_image)

        # pupil palette
        self.eye_config_palette_2 = PaletteGrid(colors=PALETTES['kevinbot'])
        self.eye_config_palette_2.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eye_config_palette_2.setFixedSize(self.eye_config_palette_2.sizeHint())
        self.eye_config_palette_2.selected.connect(self.eye_config_palette2_selected)
        self.eye_config_pupil_layout.addWidget(self.eye_config_palette_2)

        # iris group box
        self.eye_config_iris = QGroupBox(strings.EYE_CONFIG_I_G)
        self.eye_config_iris.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_group_layout.addWidget(self.eye_config_iris, 1, 0)
        self.eye_config_iris_layout = QHBoxLayout()
        self.eye_config_iris.setLayout(self.eye_config_iris_layout)

        # iris image
        self.eye_config_iris_image = QLabel()
        self.eye_config_iris_image.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eye_config_iris_image.setPixmap(QPixmap("icons/eye-iris.svg"))
        self.eye_config_iris_image.setAlignment(Qt.AlignCenter)
        self.eye_config_iris_layout.addWidget(self.eye_config_iris_image)

        # iris palette
        self.eye_config_palette_3 = PaletteGrid(colors=PALETTES['kevinbot'])
        self.eye_config_palette_3.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eye_config_palette_3.setFixedSize(self.eye_config_palette_3.sizeHint())
        self.eye_config_palette_3.selected.connect(self.eye_config_palette3_selected)
        self.eye_config_iris_layout.addWidget(self.eye_config_palette_3)

        # eye size group box
        self.eye_config_size = QGroupBox(strings.EYE_CONFIG_S_G)
        self.eye_config_size.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_group_layout.addWidget(self.eye_config_size, 1, 1)
        self.eye_config_size_layout = QHBoxLayout()
        self.eye_config_size.setLayout(self.eye_config_size_layout)

        # eye size image
        self.eye_config_size_image = QLabel()
        self.eye_config_size_image.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eye_config_size_image.setPixmap(QPixmap("icons/eye-size.svg"))
        self.eye_config_size_image.setAlignment(Qt.AlignCenter)
        self.eye_config_size_layout.addWidget(self.eye_config_size_image)

        # eye size slider
        self.eye_config_size_slider = QSlider(Qt.Horizontal)
        self.eye_config_size_slider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eye_config_size_slider.setMinimum(0)
        self.eye_config_size_slider.setMaximum(50)
        self.eye_config_size_slider.setValue(35)
        self.eye_config_size_slider.setTickPosition(QSlider.TicksBelow)
        self.eye_config_size_slider.setTickInterval(5)
        self.eye_config_size_slider.valueChanged.connect(self.eye_config_size_slider_value_changed)
        self.eye_config_size_layout.addWidget(self.eye_config_size_slider)

        # eye move speed group box
        self.eye_config_bright = QGroupBox(strings.EYE_CONFIG_SP_G)
        self.eye_config_bright.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_group_layout.addWidget(self.eye_config_bright, 2, 0)
        self.eye_config_speed_layout = QHBoxLayout()
        self.eye_config_bright.setLayout(self.eye_config_speed_layout)

        # eye speed slider
        self.eye_config_light_slider = QSlider(Qt.Horizontal)
        self.eye_config_light_slider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eye_config_light_slider.setMinimum(1)
        self.eye_config_light_slider.setMaximum(16)
        self.eye_config_light_slider.setValue(5)
        self.eye_config_light_slider.setTickPosition(QSlider.NoTicks)
        self.eye_config_light_slider.setTickInterval(1)
        self.eye_config_light_slider.valueChanged.connect(self.eye_config_speed_slider_value_changed)
        self.eye_config_speed_layout.addWidget(self.eye_config_light_slider)

        # eye brightness group box
        self.eye_config_bright = QGroupBox(strings.EYE_CONFIG_BR_G)
        self.eye_config_bright.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_group_layout.addWidget(self.eye_config_bright, 2, 1)
        self.eye_config_speed_layout = QHBoxLayout()
        self.eye_config_bright.setLayout(self.eye_config_speed_layout)

        # eye brightness slider
        self.eye_config_light_slider = QSlider(Qt.Horizontal)
        self.eye_config_light_slider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eye_config_light_slider.setMinimum(1)
        self.eye_config_light_slider.setMaximum(255)
        self.eye_config_light_slider.setValue(255)
        self.eye_config_light_slider.setTickPosition(QSlider.NoTicks)
        self.eye_config_light_slider.setTickInterval(1)
        self.eye_config_light_slider.valueChanged.connect(self.eye_config_bright_slider_value_changed)
        self.eye_config_speed_layout.addWidget(self.eye_config_light_slider)

        # Sensors
        self.sensors_back = QPushButton()
        self.sensors_back.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.sensors_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.sensors_back.setFixedSize(QSize(36, 36))
        self.sensors_back.setIconSize(QSize(32, 32))
        self.sensors_back.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.sensor_layout.addWidget(self.sensors_back)

        self.sensors_box = QGroupBox(strings.SENSORS_G)
        self.sensors_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.sensor_box_layout = QVBoxLayout()
        self.sensors_box.setLayout(self.sensor_box_layout)
        self.sensor_layout.addWidget(self.sensors_box)

        self.batt_layout = QHBoxLayout()
        self.bme_layout = QHBoxLayout()
        self.sensor_box_layout.addLayout(self.batt_layout)
        self.sensor_box_layout.addLayout(self.bme_layout)

        # Battery 1
        self.battery1_label = QLabel(strings.BATT_VOLT1.format("Not Installed / Unknown"))
        self.battery1_label.setFrameShape(QFrame.Shape.Box)
        self.battery1_label.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.battery1_label.setFixedHeight(32)
        self.battery1_label.setAlignment(Qt.AlignCenter)
        self.batt_layout.addWidget(self.battery1_label)

        # Battery 2
        self.battery2_label = QLabel(strings.BATT_VOLT2.format("Not Installed / Unknown"))
        self.battery2_label.setFrameShape(QFrame.Shape.Box)
        self.battery2_label.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.battery2_label.setFixedHeight(32)
        self.battery2_label.setAlignment(Qt.AlignCenter)
        self.batt_layout.addWidget(self.battery2_label)

        # Outside Temp
        self.outside_temp = QLabel(strings.OUTSIDE_TEMP.format("Unknown"))
        self.outside_temp.setFrameShape(QFrame.Shape.Box)
        self.outside_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.outside_temp.setFixedHeight(32)
        self.outside_temp.setAlignment(Qt.AlignCenter)
        self.bme_layout.addWidget(self.outside_temp)

        # Outside Humidity
        self.outside_humi = QLabel(strings.OUTSIDE_HUMI.format("Unknown"))
        self.outside_humi.setFrameShape(QFrame.Shape.Box)
        self.outside_humi.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.outside_humi.setFixedHeight(32)
        self.outside_humi.setAlignment(Qt.AlignCenter)
        self.bme_layout.addWidget(self.outside_humi)

        # Outside Pressure
        self.outside_hpa = QLabel(strings.OUTSIDE_PRES.format("Unknown"))
        self.outside_hpa.setFrameShape(QFrame.Shape.Box)
        self.outside_hpa.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.outside_hpa.setFixedHeight(32)
        self.outside_hpa.setAlignment(Qt.AlignCenter)
        self.bme_layout.addWidget(self.outside_hpa)

        self.motor_temp_layout = QHBoxLayout()
        self.sensor_box_layout.addLayout(self.motor_temp_layout)

        # Left
        self.left_temp = QLabel(strings.LEFT_TEMP.format("Unknown"))
        self.left_temp.setFrameShape(QFrame.Shape.Box)
        self.left_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.left_temp.setFixedHeight(32)
        self.left_temp.setAlignment(Qt.AlignCenter)
        self.motor_temp_layout.addWidget(self.left_temp)

        # Robot Temp
        self.robot_temp = QLabel(strings.INSIDE_TEMP.format("Unknown"))
        self.robot_temp.setFrameShape(QFrame.Shape.Box)
        self.robot_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.robot_temp.setFixedHeight(32)
        self.robot_temp.setAlignment(Qt.AlignCenter)
        self.motor_temp_layout.addWidget(self.robot_temp)

        # Right
        self.right_temp = QLabel(strings.RIGHT_TEMP.format("Unknown"))
        self.right_temp.setFrameShape(QFrame.Shape.Box)
        self.right_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.right_temp.setFixedHeight(32)
        self.right_temp.setAlignment(Qt.AlignCenter)
        self.motor_temp_layout.addWidget(self.right_temp)

        # Level
        self.level_layout = QHBoxLayout()
        self.sensor_box_layout.addLayout(self.level_layout)

        self.level = Level()
        self.level.label.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.level.setFixedSize(QSize(220, 260))
        self.level.setLineColor(self.fg_color)
        self.level.setLineWidth(16)
        self.level.setRobotColor(QColor(0, 34, 255))
        self.ensurePolished()
        self.level.setBackgroundColor(QColor(QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                                             QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                                             QColor(self.palette().color(QPalette.Window)).getRgb()[2]))
        self.level_layout.addWidget(self.level)

        self.sensor_box_layout.addStretch()

        # Page Flip 1
        self.page_flip_layout_1 = QHBoxLayout()
        self.layout.addLayout(self.page_flip_layout_1)

        self.page_flip_left = QPushButton()
        self.page_flip_left.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_left.clicked.connect(lambda: self.widget.slideInIdx(7))
        self.page_flip_left.setShortcut(QKeySequence(Qt.Key.Key_Comma))

        self.page_flip_right = QPushButton()
        self.page_flip_right.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_right.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.page_flip_right.setShortcut(QKeySequence(Qt.Key.Key_Period))

        self.shutdown = QPushButton()
        self.shutdown.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.shutdown.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.shutdown.setIconSize(QSize(32, 32))
        self.shutdown.clicked.connect(self.shutdown_action)
        self.shutdown.setFixedSize(QSize(36, 36))

        # icons
        self.page_flip_left.setIcon(qta.icon("fa5s.thermometer-half", color=self.fg_color))
        self.page_flip_right.setIcon(qta.icon("fa5s.camera", color=self.fg_color))

        # batt_volt1
        self.batt_volt1 = QLabel(strings.BATT_VOLT1.format("Unknown"))
        self.batt_volt1.setObjectName("Kevinbot3_RemoteUI_VoltageText")

        # batt_volt2
        self.batt_volt2 = QLabel(strings.BATT_VOLT2.format("Unknown"))
        self.batt_volt2.setObjectName("Kevinbot3_RemoteUI_VoltageText")

        # width/height
        self.page_flip_left.setFixedSize(36, 36)
        self.page_flip_right.setFixedSize(36, 36)
        self.page_flip_left.setIconSize(QSize(32, 32))
        self.page_flip_right.setIconSize(QSize(32, 32))

        self.page_flip_layout_1.addWidget(self.page_flip_left)
        self.page_flip_layout_1.addStretch()
        self.page_flip_layout_1.addWidget(self.batt_volt1)
        self.page_flip_layout_1.addStretch()
        self.page_flip_layout_1.addWidget(self.shutdown)
        self.page_flip_layout_1.addStretch()
        self.page_flip_layout_1.addWidget(self.batt_volt2)
        self.page_flip_layout_1.addStretch()
        self.page_flip_layout_1.addWidget(self.page_flip_right)

        # Page Flip 2
        self.page_flip_layout_2 = QHBoxLayout()
        self.camera_layout.addLayout(self.page_flip_layout_2)

        self.page_flip_left_2 = QPushButton()
        self.page_flip_left_2.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_left_2.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.page_flip_left_2.setShortcut(QKeySequence(Qt.Key.Key_Comma))

        self.refresh_camera = QPushButton()
        self.refresh_camera.clicked.connect(self.cameraWebView.reload)

        self.page_flip_right_2 = QPushButton()
        self.page_flip_right_2.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_left.setShortcut(QKeySequence(Qt.Key.Key_Period))
        self.page_flip_right_2.setDisabled(True)

        self.page_flip_left_2.setIcon(qta.icon("fa5.arrow-alt-circle-left", color=self.fg_color))
        self.refresh_camera.setIcon(qta.icon("fa5s.redo-alt", color=self.fg_color))
        self.page_flip_right_2.setIcon(qta.icon("fa5.arrow-alt-circle-right", color=self.fg_color))

        self.page_flip_left_2.setFixedSize(36, 36)
        self.refresh_camera.setFixedSize(36, 36)
        self.page_flip_right_2.setFixedSize(36, 36)
        self.page_flip_left_2.setIconSize(QSize(32, 32))
        self.refresh_camera.setIconSize(QSize(32, 32))
        self.page_flip_right_2.setIconSize(QSize(32, 32))

        self.page_flip_layout_2.addWidget(self.page_flip_left_2)
        self.page_flip_layout_2.addStretch()
        self.page_flip_layout_2.addWidget(self.refresh_camera)
        self.page_flip_layout_2.addStretch()
        self.page_flip_layout_2.addWidget(self.page_flip_right_2)

        # disable items on startup
        self.arm_set_preset.setEnabled(False)
        self.arm_preset1.setEnabled(False)
        self.arm_preset2.setEnabled(False)
        self.arm_preset3.setEnabled(False)
        self.arm_preset4.setEnabled(False)
        self.arm_preset5.setEnabled(False)
        self.arm_preset6.setEnabled(False)
        self.arm_preset7.setEnabled(False)
        self.arm_preset8.setEnabled(False)
        self.arm_preset9.setEnabled(False)

        self.motor_stick.setEnabled(False)
        self.head_stick.setEnabled(False)

        self.head_led.setEnabled(False)
        self.base_led.setEnabled(False)
        self.body_led.setEnabled(False)
        self.camera_led.setEnabled(False)

    def closeEvent(self, event):
        com.xb.halt()
        event.accept()

    # noinspection PyUnresolvedReferences
    def init_batt_modal(self):
        # a main_widget floating in the middle of the window
        self.batt_modal = QWidget(self)
        self.batt_modal.setFixedSize(QSize(400, 200))
        self.batt_modal.setObjectName("Kevinbot3_RemoteUI_Modal")
        self.batt_modal.setStyleSheet("#Kevinbot3_RemoteUI_Modal { border: 1px solid " + QColor(
            self.palette().color(QPalette.ColorRole.ButtonText)).name() + "; }")
        self.batt_modal.move(int(self.width() / 2 - self.batt_modal.width() / 2),
                             int(self.height() / 2 - self.batt_modal.height() / 2))
        self.batt_modal.hide()

        self.battModalMainLayout = QVBoxLayout()
        self.batt_modal.setLayout(self.battModalMainLayout)

        self.battModalLayout = QGridLayout()
        self.battModalMainLayout.addLayout(self.battModalLayout)

        self.battModalIcon = QLabel()
        self.battModalIcon.setPixmap(QPixmap("icons/ban.svg"))
        self.battModalIcon.setFixedSize(QSize(128, 128))
        self.battModalIcon.setScaledContents(True)
        self.battModalIcon.setObjectName("Kevinbot3_RemoteUI_ModalIcon")
        self.battModalLayout.addWidget(self.battModalIcon, 0, 0)

        self.battModalText = QLabel("Text not loaded")
        self.battModalText.setObjectName("Kevinbot3_RemoteUI_ModalText")
        self.battModalText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.battModalText.setWordWrap(True)
        self.battModalLayout.addWidget(self.battModalText, 0, 1)

        self.battModalButtonLayout = QHBoxLayout()
        self.battModalMainLayout.addLayout(self.battModalButtonLayout)

        self.battModalClose = QPushButton(strings.MODAL_CLOSE)
        self.battModalClose.setObjectName("Kevinbot3_RemoteUI_ModalButton")
        self.battModalClose.setFixedHeight(36)
        self.battModalClose.clicked.connect(lambda: self.slide_out_batt_modal(disable=True))
        self.battModalButtonLayout.addWidget(self.battModalClose)

        self.battModalShutdown = QPushButton(strings.MODAL_SHUTDOWN)
        self.battModalShutdown.setObjectName("Kevinbot3_RemoteUI_ModalButton")
        self.battModalShutdown.setFixedHeight(36)
        self.battModalShutdown.clicked.connect(self.shutdown_robot_modal_action)
        self.battModalButtonLayout.addWidget(self.battModalShutdown)

    # noinspection PyArgumentList,PyUnresolvedReferences
    def init_mot_temp_modal(self):
        # a main_widget floating in the middle of the window
        self.motTemp_modal = QWidget(self)
        self.motTemp_modal.setObjectName("Kevinbot3_RemoteUI_Modal")
        self.motTemp_modal.setStyleSheet("#Kevinbot3_RemoteUI_Modal { border: 1px solid " + QColor(
            self.palette().color(QPalette.ColorRole.ButtonText)).name() + "; }")
        self.motTemp_modal.setFixedSize(QSize(400, 200))
        self.motTemp_modal.move(int(self.width() / 2 - self.motTemp_modal.width() / 2),
                                int(self.height() / 2 - self.motTemp_modal.height() / 2))
        self.motTemp_modal.hide()

        self.motTempModalMainLayout = QVBoxLayout()
        self.motTemp_modal.setLayout(self.motTempModalMainLayout)

        self.motTempModalLayout = QGridLayout()
        self.motTempModalMainLayout.addLayout(self.motTempModalLayout)

        self.motTempModalIcon = QLabel()
        self.motTempModalIcon.setPixmap(QPixmap("icons/ban.svg"))
        self.motTempModalIcon.setFixedSize(QSize(128, 128))
        self.motTempModalIcon.setScaledContents(True)
        self.motTempModalIcon.setObjectName("Kevinbot3_RemoteUI_ModalIcon")
        self.motTempModalLayout.addWidget(self.motTempModalIcon, 0, 0)

        self.motTempModalText = QLabel("Text not loaded")
        self.motTempModalText.setObjectName("Kevinbot3_RemoteUI_ModalText")
        self.motTempModalText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motTempModalText.setWordWrap(True)
        self.motTempModalLayout.addWidget(self.motTempModalText, 0, 1)

        self.motTempModalButtonLayout = QHBoxLayout()
        self.motTempModalMainLayout.addLayout(self.motTempModalButtonLayout)

        self.motTempModalClose = QPushButton(strings.MODAL_CLOSE)
        self.motTempModalClose.setObjectName("Kevinbot3_RemoteUI_ModalButton")
        self.motTempModalClose.setFixedHeight(36)
        self.motTempModalClose.clicked.connect(lambda: self.slide_out_temp_modal(disable=True))
        self.motTempModalButtonLayout.addWidget(self.motTempModalClose)

        self.motTempModalShutdown = QPushButton(strings.MODAL_SHUTDOWN)
        self.motTempModalShutdown.setObjectName("Kevinbot3_RemoteUI_ModalButton")
        self.motTempModalShutdown.setFixedHeight(36)
        self.motTempModalShutdown.clicked.connect(self.shutdown_robot_modal_action)
        self.motTempModalButtonLayout.addWidget(self.motTempModalShutdown)

    def slide_out_batt_modal(self, disable=False):
        global disable_batt_modal
        if disable:
            disable_batt_modal = True
        # animate modal to slide to the top and then close
        self.anim = QPropertyAnimation(self.batt_modal, b"pos")
        self.anim.setEndValue(QPoint(int(self.batt_modal.pos().x()),
                                     int(self.batt_modal.pos().y() - self.batt_modal.height() -
                                         self.batt_modal.geometry().height() / 1.6)))
        self.anim.setEasingCurve(QEasingCurve.Type.OutSine)
        self.anim.setDuration(settings["window_properties"]["animation_speed"])
        # noinspection PyUnresolvedReferences
        self.anim.finished.connect(lambda: self.hide_batt_modal((not disable)))
        self.anim.start()

    def slide_out_temp_modal(self, disable=False):
        global disable_temp_modal
        if disable:
            disable_temp_modal = True
        # animate modal to slide to the top and then close
        self.anim = QPropertyAnimation(self.motTemp_modal, b"pos")
        self.anim.setEndValue(QPoint(int(self.motTemp_modal.pos().x()),
                                     int(self.motTemp_modal.pos().y() - self.motTemp_modal.height() -
                                         self.motTemp_modal.geometry().height() / 1.6)))
        self.anim.setEasingCurve(QEasingCurve.Type.OutSine)
        self.anim.setDuration(settings["window_properties"]["animation_speed"])
        # noinspection PyUnresolvedReferences
        self.anim.finished.connect(lambda: self.hide_temp_modal((not disable)))
        self.anim.start()

    def hide_batt_modal(self, end=False):
        global disable_batt_modal
        disable_batt_modal = True

        self.batt_modal.hide()
        self.batt_modal.move(int(self.width() / 2 - self.batt_modal.width() / 2),
                             int(self.height() / 2 - self.batt_modal.height() / 2))

        if end:
            self.close()
            sys.exit()

    def hide_temp_modal(self, end=False):
        global disable_temp_modal
        disable_temp_modal = True

        self.motTemp_modal.hide()
        self.motTemp_modal.move(int(self.width() / 2 - self.motTemp_modal.width() / 2),
                                int(self.height() / 2 - self.motTemp_modal.height() / 2))

        if end:
            self.close()
            sys.exit()

    def shutdown_robot_modal_action(self):
        com.txstr("no-pass.remote.status=disconnected")
        com.txshut()
        self.close()

    def camera_led_action(self):
        old_dir = self.widget.getDirection()
        self.widget.setDirection(Qt.Axis.YAxis)
        self.widget.slideInIdx(1)
        self.widget.setDirection(old_dir)

    def arm_edit_action(self):
        old_dir = self.widget.getDirection()
        self.widget.setDirection(Qt.Axis.YAxis)
        self.widget.slideInIdx(5)
        self.widget.setDirection(old_dir)

    @staticmethod
    def arm_action(index):
        global CURRENT_ARM_POS
        com.txcv("arms", settings["arm_prog"][index])
        CURRENT_ARM_POS = settings["arm_prog"][index]

    def led_action(self, index):
        self.widget.slideInIdx(2 + index)

    @staticmethod
    def head_effect_action(index):
        com.txcv("head_effect", settings["head_effects"][index])

    @staticmethod
    def body_effect_action(index):
        com.txcv("body_effect", settings["body_effects"][index].replace("*c", ""))

    @staticmethod
    def base_effect_action(index):
        com.txcv("base_effect", settings["base_effects"][index].replace("*c", ""))

    def eye_config_action(self):
        self.widget.slideInIdx(6)

    def head_color1_changed(self):
        com.txcv("head_color1", str(self.headColorPicker.getHex()).strip("#") + "00")

    def head_color2_changed(self):
        com.txcv("head_color2", str(self.headColorPicker2.getHex()).strip("#") + "00")

    def body_color1_changed(self):
        com.txcv("body_color1", str(self.bodyColorPicker.getHex()).strip("#") + "00")

    def body_color2_changed(self):
        com.txcv("body_color2", str(self.bodyColorPicker2.getHex()).strip("#") + "00")

    def base_color1_changed(self):
        com.txcv("base_color1", str(self.base_color_picker.getHex()).strip("#") + "00")

    def base_color2_changed(self):
        com.txcv("base_color2", str(self.base_color_picker_2.getHex()).strip("#") + "00")

    def camera_brightness_changed(self):
        com.txcv("cam_brightness", str(self.cameraLedSlider.value()))

    def arm_preset_action(self, index):
        global CURRENT_ARM_POS
        print("arm preset: " + str(index))
        com.txcv("arms", settings["arm_prog"][index])
        CURRENT_ARM_POS = settings["arm_prog"][index]

        # suppress events on knobs
        for i in range(len(settings["arm_prog"][index])):
            if i < settings["arm_dof"]:
                self.left_knobs[i].blockSignals(True)
            else:
                self.right_knobs[i - settings["arm_dof"]].blockSignals(True)

        # update knobs
        for i in range(len(settings["arm_prog"][index])):
            if i < settings["arm_dof"]:
                self.left_knobs[i].setValue(settings["arm_prog"][index][i])
            else:
                self.right_knobs[i - settings["arm_dof"]].setValue(settings["arm_prog"][index][i])

        # update labels
        for i in range(len(settings["arm_prog"][index])):
            if i < settings["arm_dof"]:
                self.left_labels[i].setText(str(settings["arm_prog"][index][i]))
            else:
                self.right_labels[i - settings["arm_dof"]].setText(str(settings["arm_prog"][index][i]))

        # allow events on knobs
        for i in range(len(settings["arm_prog"][index])):
            if i < settings["arm_dof"]:
                self.left_knobs[i].blockSignals(False)
            else:
                self.right_knobs[i - settings["arm_dof"]].blockSignals(False)

        # update label
        self.arm_preset_label.setText(strings.CURRENT_ARM_PRESET + ": {}".format(str(index + 1)))

    def arm_preset_left_changed(self, index):
        global CURRENT_ARM_POS
        self.left_labels[index].setText(str(self.left_knobs[index].value()))
        com.txcv("arms",
                 [self.left_knobs[i].value() for i in range(len(self.left_knobs))] + [self.right_knobs[i].value() for i
                                                                                      in range(len(self.right_knobs))])
        CURRENT_ARM_POS = [self.left_knobs[i].value() for i in range(len(self.left_knobs))] + [
            self.right_knobs[i].value() for i in range(len(self.right_knobs))]

    def arm_preset_right_changed(self, index):
        global CURRENT_ARM_POS
        self.right_labels[index].setText(str(self.right_knobs[index].value()))
        com.txcv("arms",
                 [self.left_knobs[i].value() for i in range(len(self.left_knobs))] + [self.right_knobs[i].value() for i
                                                                                      in range(len(self.right_knobs))])
        CURRENT_ARM_POS = [self.left_knobs[i].value() for i in range(len(self.left_knobs))] + [
            self.right_knobs[i].value() for i in range(len(self.right_knobs))]

    def arm_preset_save_action(self):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        if not extract_digits(self.arm_preset_label.text()):
            if self.modal_count < 6:
                modal_bar = KBModalBar(self)
                self.modals.append(modal_bar)
                self.modal_count += 1
                modal_bar.setTitle(strings.SAVE_ERROR)
                modal_bar.setDescription(strings.SAVE_WARN_1)
                modal_bar.setPixmap(qta.icon("fa5s.exclamation-triangle", color=self.fg_color).pixmap(36))

                modal_bar.popToast(popSpeed=500, posIndex=self.modal_count)

                modal_timeout = QTimer()
                modal_timeout.singleShot(1500, close_modal)
        else:
            if self.modal_count < 6:
                modal_bar = KBModalBar(self)
                self.modals.append(modal_bar)
                self.modal_count += 1
                modal_bar.setTitle(strings.SAVE_SUCCESS)
                modal_bar.setDescription("Speech Preset Saved")
                modal_bar.setPixmap(qta.icon("fa5.save", color=self.fg_color).pixmap(36))

                modal_bar.popToast(popSpeed=500, posIndex=self.modal_count)

                modal_timeout = QTimer()
                modal_timeout.singleShot(1500, close_modal)

            for i in range(len(settings["arm_prog"][extract_digits(self.arm_preset_label.text())[0] - 1])):
                if i < settings["arm_dof"]:
                    settings["arm_prog"][extract_digits(self.arm_preset_label.text())[0] - 1][i] = self.left_knobs[
                        i].value()
                else:
                    settings["arm_prog"][extract_digits(self.arm_preset_label.text())[0] - 1][i] = self.right_knobs[
                        i - settings["arm_dof"]].value()

            # dump json
            save_settings()

    def save_speech(self, text):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        settings["speech"]["text"] = text
        save_settings()

        # show modal
        if self.modal_count < 6:
            modal_bar = KBModalBar(self)
            self.modals.append(modal_bar)
            self.modal_count += 1
            modal_bar.setTitle(strings.SAVE_SUCCESS)
            modal_bar.setDescription("Speech Preset Saved")
            modal_bar.setPixmap(qta.icon("fa5.save", color=self.fg_color).pixmap(36))

            modal_bar.popToast(popSpeed=500, posIndex=self.modal_count)

            modal_timeout = QTimer()
            modal_timeout.singleShot(1500, close_modal)

    def set_speed(self, speed):
        self.speed = speed
        settings["speed"] = speed
        save_settings()

    def head_changed_action(self):
        com.txcv("head_x", map_range(self.head_stick.getXY()[0], 0, JOYSTICK_SIZE, 0, 60))
        com.txcv("head_y", map_range(self.head_stick.getXY()[1], 0, JOYSTICK_SIZE, 0, 60))

    def shutdown_action(self):
        self.close()
        app.quit()

    @staticmethod
    def eye_config_palette_selected(color):
        com.txcv("eye_bg_color", color.strip("#"))

    @staticmethod
    def eye_config_palette2_selected(color):
        com.txcv("pupil_color", color.strip("#"))

    @staticmethod
    def eye_config_palette3_selected(color):
        com.txcv("iris_color", color.strip("#"))

    @staticmethod
    def eye_config_size_slider_value_changed(value):
        com.txcv("eye_size", value)

    @staticmethod
    def eye_config_speed_slider_value_changed(value):
        com.txcv("eye_speed", value)

    @staticmethod
    def eye_config_bright_slider_value_changed(value):
        com.txcv("eye_brightness", value)

    def motor_action(self):
        if not ANALOG_STICK:
            x, y = self.motor_stick.getXY()
            y = -y

            direction = direction_lookup(x, 0, y, 0)[0]

            distance = round(math.dist((0, 0), (x, y)))

            if direction == "N":
                com.txmot((map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, settings["max_us"]),
                           map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, settings["max_us"])))
            elif direction == "S":
                com.txmot((map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, 2000 -
                                     (settings["max_us"] - 1000)),
                           map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, 2000 -
                                     (settings["max_us"] - 1000))))
            elif direction == "W":
                com.txmot((map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, 2000 -
                                     (settings["max_us"] - 1000)),
                           map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, settings["max_us"])))
            elif direction == "E":
                com.txmot((map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, settings["max_us"]),
                           map_range(distance, 0, self.motor_stick.getMaxDistance(), 1500, 2000 -
                                     (settings["max_us"] - 1000))))
        elif ANALOG_STICK:
            # EXPERIMENTAL ANALOG CONTROL

            # get values
            x, y = self.motor_stick.getXY()
            x, y = x / self.motor_stick.getMaxDistance(), y / self.motor_stick.getMaxDistance()

            theta = math.atan2(y, x)
            r = math.sqrt(x * x + y * y)

            if abs(x) > abs(y):
                max_r = abs(r / x)
            else:
                max_r = abs(r / y)

            magnitude = r / max_r

            turn_damping = 3.0
            left = magnitude * (math.sin(theta) + math.cos(theta) / turn_damping)
            right = magnitude * (math.sin(theta) - math.cos(theta) / turn_damping)

            us_change = abs(1000 - settings["max_us"])

            left = map_range_limit(left, -1, 1, 1000 + us_change, 2000 - us_change)
            right = map_range_limit(right, -1, 1, 1000 + us_change, 2000 - us_change)

            com.txmot((int(right), int(left)))

    def set_enabled(self, ena: bool):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        global enabled

        if not enabled == ena:
            # show modal
            if self.modal_count < 6:
                modal_bar = KBModalBar(self)
                self.modals.append(modal_bar)
                self.modal_count += 1
                modal_bar.setTitle(f"Robot {'Enabled' if ena else 'Disabled'}")
                modal_bar.setDescription(f"Kevinbot has been {'Enabled' if ena else 'Disabled'}")
                modal_bar.setPixmap(qta.icon("fa5s.power-off", color=self.fg_color).pixmap(36))

                modal_bar.popToast(popSpeed=500, posIndex=self.modal_count)

                modal_timeout = QTimer()
                modal_timeout.singleShot(1500, close_modal)

        enabled = ena

        self.arm_set_preset.setEnabled(enabled)
        self.arm_preset1.setEnabled(enabled)
        self.arm_preset2.setEnabled(enabled)
        self.arm_preset3.setEnabled(enabled)
        self.arm_preset4.setEnabled(enabled)
        self.arm_preset5.setEnabled(enabled)
        self.arm_preset6.setEnabled(enabled)
        self.arm_preset7.setEnabled(enabled)
        self.arm_preset8.setEnabled(enabled)
        self.arm_preset9.setEnabled(enabled)

        self.motor_stick.setEnabled(enabled)
        self.head_stick.setEnabled(enabled)

        self.head_led.setEnabled(enabled)
        self.base_led.setEnabled(enabled)
        self.body_led.setEnabled(enabled)
        self.camera_led.setEnabled(enabled)

        if not enabled:
            com.txcv("head_effect", "color1", delay=0.02)
            com.txcv("body_effect", "color1", delay=0.02)
            com.txcv("base_effect", "color1", delay=0.02)

        com.txcv("robot.disable", str(not enabled))


def init_robot():
    com.txcv("no-pass.remote.name", remote_name)
    try:
        com.txcv("no-pass.remote.version", open("version.txt", "r").read())
    except FileNotFoundError:
        com.txcv("no-pass.remote.version", "UNKNOWN")
    com.txcv("no-pass.remote.status", "connected")
    com.txcv("arms", CURRENT_ARM_POS, delay=0.02)
    com.txcv("no-pass.speech-engine", "espeak", delay=0.02)
    com.txcv("head_effect", "color1", delay=0.02)
    com.txcv("body_effect", "color1", delay=0.02)
    com.txcv("base_effect", "color1", delay=0.02)
    com.txcv("cam_brightness", 0, delay=0.02)
    com.txcv("eye_speed", 5, delay=0.02)
    com.txcv("eye_bg_color", "0022ff", delay=0.02)
    com.txcv("pupil_color", "000000", delay=0.02)
    com.txcv("iris_color", "ffffff", delay=0.02)
    com.txcv("robot.disable", "True", delay=0.02)
    com.txcv("eye_size", 35, delay=0.02)


if __name__ == '__main__':
    error = None
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Kevinbot Remote")
        app.setApplicationVersion(__version__)
        window = RemoteUI()
        ex = app.exec()
    # noinspection PyBroadException
    except Exception as e:
        com.txcv("no-pass.remote.status", "error")
        com.txcv("no-pass.remote.error", e)
        error = True
    finally:
        if not error:
            com.txcv("no-pass.remote.status", "disconnected")
