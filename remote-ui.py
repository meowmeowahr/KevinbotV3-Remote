#!/usr/bin/python

# The GUI for the Kevinbot v3 Control using PyQt5

import datetime
import json
import platform
import sys
import threading
import time
from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from QCustomWidgets import KBModalBar
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
HIGH_MOTOR_TEMP = 50
HIGH_INSIDE_TEMP = 45

ROBOT_VERSION = "Unknown"
ENABLED = True

__version__ = "v1.0.0"
__author__ = "Kevin Ahr"

window = None
disable_batt_modal = False
disable_temp_modal = False

# load settings from file
with open("settings.json", "r") as f:
    settings = json.load(f)

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

# load voltage warning settings
if "warning_voltage" in settings:
    warning_voltage = settings["warning_voltage"]
else:
    settings["warning_voltage"] = 10  # save default
    warning_voltage = settings["warning_voltage"]
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=2)

# if windows
if platform.system() == "Windows":
    import ctypes

    # show icon in taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Kevinbot3 Remote")

try:
    remote_name = settings["name"]
except KeyError:
    remote_name = "KBOT_REMOTE"


def rx_data():
    time.sleep(1)  # wait for window to open

    global ENABLED
    global ROBOT_VERSION
    global window
    global disable_batt_modal
    while True:
        data = com.xb.wait_read_frame()

        try:
            data = data['rf_data'].decode('utf-8').strip().split("=")
        except KeyError:
            continue

        print("Received: " + str(data))

        # older battery data format
        if data[0] == "batt_volt1":
            if window is not None:
                window.batt_volt1.setText(strings.BATT_VOLT1.format(int(data[1]) / 10) + "V")
                window.battery1_label.setText(strings.BATT_VOLT1.format(int(data[1]) / 10))

                if int(data[1]) / 10 < warning_voltage:
                    window.battery1_label.setStyleSheet("background-color: #df574d;")
                else:
                    window.battery1_label.setStyleSheet("")

                if not disable_batt_modal:
                    if int(data[1]) / 10 < warning_voltage:
                        com.txmot([1500, 1500])
                        window.battModalText.setText(strings.BATT_LOW)
                        window.batt_modal.show()
        elif data[0] == "batt_volt2" and ENABLE_BATT2:
            if window is not None:
                window.batt_volt2.setText(strings.BATT_VOLT2.format(float(volt2) / 10) + "V")
                window.battery2_label.setText(strings.BATT_VOLT2.format(int(data[1]) / 10))

                if int(data[1]) / 10 < warning_voltage:
                    window.battery2_label.setStyleSheet("background-color: #df574d;")
                else:
                    window.battery2_label.setStyleSheet("")

                if not disable_batt_modal:
                    if int(data[1]) / 10 < warning_voltage:
                        com.txmot([1500, 1500])
                        window.battModalText.setText(strings.BATT_LOW)
                        window.batt_modal.show()
        # newer battery data format
        elif data[0] == "batt_volts":
            if window is not None:
                volt1, volt2 = data[1].split(",")
                window.batt_volt1.setText(strings.BATT_VOLT1.format(float(volt1) / 10) + "V")
                window.battery1_label.setText(strings.BATT_VOLT1.format(float(volt1) / 10))

                if float(volt1) / 10 < warning_voltage:
                    window.battery1_label.setStyleSheet("background-color: #df574d;")
                else:
                    window.battery1_label.setStyleSheet("")

                if ENABLE_BATT2:
                    window.batt_volt2.setText(strings.BATT_VOLT2.format(float(volt2) / 10) + "V")
                    window.battery2_label.setText(strings.BATT_VOLT2.format(float(volt2) / 10))
                    if float(volt2) / 10 < warning_voltage:
                        window.battery2_label.setStyleSheet("background-color: #df574d;")
                    else:
                        window.battery2_label.setStyleSheet("")

                if not disable_batt_modal:
                    if float(volt1) / 10 < 11:
                        com.txmot([1500, 1500])
                        window.battModalText.setText(strings.BATT_LOW)
                        window.batt_modal.show()
                    elif float(volt2) / 10 < 11:
                        com.txmot([1500, 1500])
                        window.battModalText.setText(strings.BATT_LOW)
                        window.batt_modal.show()
        # bme280 sensor
        elif data[0] == "bme":
            if window is not None:
                try:
                    window.outside_temp.setText(strings.OUTSIDE_TEMP.format(str(data[1].split(",")[0])
                                                                            + "℃ (" + str(
                        data[1].split(",")[1]) + "℉)"))
                    window.outside_humi.setText(strings.OUTSIDE_HUMI.format(data[1].split(",")[2]))
                    window.outside_hpa.setText(strings.OUTSIDE_PRES.format(data[1].split(",")[3]))
                except RuntimeError:
                    # user quit out  of program
                    pass
        # motor, body temps
        elif data[0] == "temps":
            if window is not None:
                try:
                    window.left_temp.setText(strings.LEFT_TEMP.format(rstr(data[1].split(",")[0]) + "℃ (" +
                                                                      rstr(convert_c_to_f(
                                                                          float(data[1].split(",")[0])))
                                                                      + "℉)"))
                    window.right_temp.setText(strings.RIGHT_TEMP.format(rstr(data[1].split(",")[1]) + "℃ (" +
                                                                        rstr(convert_c_to_f(
                                                                            float(data[1].split(",")[1])))
                                                                        + "℉)"))

                    window.robot_temp.setText(strings.INSIDE_TEMP.format(rstr(data[1].split(",")[2]) + "℃ (" +
                                                                         rstr(convert_c_to_f(
                                                                             float(data[1].split(",")[2])))
                                                                         + "℉)"))

                    if float(data[1].split(",")[0]) > HIGH_MOTOR_TEMP:
                        window.left_temp.setStyleSheet("background-color: #df574d;")
                        window.motor_stick.setDisabled(True)
                        if not disable_temp_modal:
                            com.txmot([1500, 1500])
                            window.motTempModalText.setText(strings.MOT_TEMP_HIGH)
                            window.motTemp_modal.show()
                    else:
                        window.left_temp.setStyleSheet("")

                    if float(data[1].split(",")[1]) > HIGH_MOTOR_TEMP:
                        window.right_temp.setStyleSheet("background-color: #df574d;")
                        window.motor_stick.setDisabled(True)
                        if not disable_temp_modal:
                            com.txmot([1500, 1500])
                            window.motTempModalText.setText(strings.MOT_TEMP_HIGH)
                            window.motTemp_modal.show()
                    else:
                        window.right_temp.setStyleSheet("")

                    if float(data[1].split(",")[2]) > HIGH_INSIDE_TEMP:
                        window.robot_temp.setStyleSheet("background-color: #df574d;")
                    else:
                        window.robot_temp.setStyleSheet("")

                except RuntimeError:
                    # user quit out  of program
                    pass
        elif data[0] == "angle":
            if window is not None:
                window.level.setAngle(int(data[1]))
                if int(data[1]) > 18:
                    window.level.label.setStyleSheet("background-color: #df574d;")
                    window.level.setLineColor(QColor("#df574d"))
                elif int(data[1]) > 10:
                    window.level.label.setStyleSheet("background-color: #eebc2a;")
                    window.level.setLineColor(QColor("#eebc2a"))
                else:
                    window.level.label.setStyleSheet("")
                    window.level.setLineColor(Qt.white)
        # remote disable
        elif data[0] == "remote.disableui":
            if str(data[1]).lower() == "true":
                window.armGroup.setDisabled(True)
                window.ledGroup.setDisabled(True)
                window.mainGroup.setDisabled(True)
                
            else:
                window.armGroup.setDisabled(False)
                window.ledGroup.setDisabled(False)
                window.mainGroup.setDisabled(False)

        if not ENABLED:
            break


class SliderProxyStyle(QProxyStyle):
    # noinspection PyMethodOverriding
    def pixelMetric(self, metric, option, widget):
        if metric == QStyle.PM_SliderThickness:
            return 25
        elif metric == QStyle.PM_SliderLength:
            return 22
        return super().pixelMetric(metric, option, widget)


# noinspection PyAttributeOutsideInit,PyArgumentList
class RemoteUI(QMainWindow):
    # noinspection PyArgumentList
    def __init__(self, parent=None):
        super(RemoteUI, self).__init__(parent)

        self.setObjectName("Kevinbot3_RemoteUI")
        self.setWindowTitle(strings.WIN_TITLE)
        self.setWindowIcon(QIcon('icons/icon.svg'))

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

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    # noinspection PyArgumentList,PyUnresolvedReferences
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

        self.cameraLayout = QVBoxLayout()
        self.cameraWidget.setLayout(self.cameraLayout)
        self.widget.addWidget(self.cameraWidget)

        self.headColorLayout = QHBoxLayout()
        self.headColorWidget.setLayout(self.headColorLayout)
        self.widget.addWidget(self.headColorWidget)

        self.bodyColorLayout = QHBoxLayout()
        self.bodyColorWidget.setLayout(self.bodyColorLayout)
        self.widget.addWidget(self.bodyColorWidget)

        self.baseColorLayout = QHBoxLayout()
        self.baseColorWidget.setLayout(self.baseColorLayout)
        self.widget.addWidget(self.baseColorWidget)

        self.armPresetsLayout = QVBoxLayout()
        self.armPresetsWidget.setLayout(self.armPresetsLayout)
        self.widget.addWidget(self.armPresetsWidget)

        self.eyeConfigLayout = QHBoxLayout()
        self.eyeConfigWidget.setLayout(self.eyeConfigLayout)
        self.widget.addWidget(self.eyeConfigWidget)

        self.sensorLayout = QHBoxLayout()
        self.sensorsWidget.setLayout(self.sensorLayout)
        self.widget.addWidget(self.sensorsWidget)

        self.widget.setCurrentIndex(0)

        self.armGroup = QGroupBox(strings.ARM_PRESET_G)
        self.armGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.layout.addWidget(self.armGroup)

        self.armLayout = QHBoxLayout()
        self.armGroup.setLayout(self.armLayout)

        # Modal

        self.ensurePolished()
        self.init_modal()
        self.init_batt_modal()
        self.init_mot_temp_modal()

        # Arm Presets

        self.armPreset1 = QPushButton(strings.ARM_PRESETS[0])
        self.armPreset1.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset2 = QPushButton(strings.ARM_PRESETS[1])
        self.armPreset2.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset3 = QPushButton(strings.ARM_PRESETS[2])
        self.armPreset3.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset4 = QPushButton(strings.ARM_PRESETS[3])
        self.armPreset4.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset5 = QPushButton(strings.ARM_PRESETS[4])
        self.armPreset5.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset6 = QPushButton(strings.ARM_PRESETS[5])
        self.armPreset6.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset7 = QPushButton(strings.ARM_PRESETS[6])
        self.armPreset7.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset8 = QPushButton(strings.ARM_PRESETS[7])
        self.armPreset8.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset9 = QPushButton(strings.ARM_PRESETS[8])
        self.armPreset9.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armSetPreset = QPushButton(strings.ARM_SET_PRESET)
        self.armSetPreset.setObjectName("Kevinbot3_RemoteUI_ArmButton")

        self.armPreset1.setFixedSize(60, 50)
        self.armPreset2.setFixedSize(60, 50)
        self.armPreset3.setFixedSize(60, 50)
        self.armPreset4.setFixedSize(60, 50)
        self.armPreset5.setFixedSize(60, 50)
        self.armPreset6.setFixedSize(60, 50)
        self.armPreset7.setFixedSize(60, 50)
        self.armPreset8.setFixedSize(60, 50)
        self.armPreset9.setFixedSize(60, 50)
        self.armSetPreset.setFixedSize(60, 50)

        self.armPreset1.clicked.connect(lambda: self.arm_action(0))
        self.armPreset2.clicked.connect(lambda: self.arm_action(1))
        self.armPreset3.clicked.connect(lambda: self.arm_action(2))
        self.armPreset4.clicked.connect(lambda: self.arm_action(3))
        self.armPreset5.clicked.connect(lambda: self.arm_action(4))
        self.armPreset6.clicked.connect(lambda: self.arm_action(5))
        self.armPreset7.clicked.connect(lambda: self.arm_action(6))
        self.armPreset8.clicked.connect(lambda: self.arm_action(7))
        self.armPreset9.clicked.connect(lambda: self.arm_action(8))
        self.armSetPreset.clicked.connect(self.arm_edit_action)

        self.armPreset1.setShortcut("1")
        self.armPreset2.setShortcut("2")
        self.armPreset3.setShortcut("3")
        self.armPreset4.setShortcut("4")
        self.armPreset5.setShortcut("5")
        self.armPreset6.setShortcut("6")
        self.armPreset7.setShortcut("7")
        self.armPreset8.setShortcut("8")
        self.armPreset9.setShortcut("9")

        self.armLayout.addWidget(self.armPreset1)
        self.armLayout.addWidget(self.armPreset2)
        self.armLayout.addWidget(self.armPreset3)
        self.armLayout.addWidget(self.armPreset4)
        self.armLayout.addWidget(self.armPreset5)
        self.armLayout.addWidget(self.armPreset6)
        self.armLayout.addWidget(self.armPreset7)
        self.armLayout.addWidget(self.armPreset8)
        self.armLayout.addWidget(self.armPreset9)
        self.armLayout.addWidget(self.armSetPreset)

        # LED Options

        self.ledGroup = QGroupBox(strings.LED_PRESET_G)
        self.ledGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.layout.addWidget(self.ledGroup)

        self.ledLayout = QHBoxLayout()
        self.ledGroup.setLayout(self.ledLayout)

        self.headLED = QPushButton(strings.LED_HEAD)
        self.headLED.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.headLED.clicked.connect(lambda: self.led_action(0))
        self.ledLayout.addWidget(self.headLED)

        self.bodyLED = QPushButton(strings.LED_BODY)
        self.bodyLED.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.bodyLED.clicked.connect(lambda: self.led_action(1))
        self.ledLayout.addWidget(self.bodyLED)

        self.cameraLED = QPushButton(strings.LED_CAMERA)
        self.cameraLED.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.cameraLED.clicked.connect(self.camera_led_action)
        self.ledLayout.addWidget(self.cameraLED)

        self.baseLED = QPushButton(strings.LED_BASE)
        self.baseLED.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.baseLED.clicked.connect(lambda: self.led_action(2))
        self.ledLayout.addWidget(self.baseLED)

        self.eyeConfig = QPushButton(strings.LED_EYE_CONFIG)
        self.eyeConfig.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.eyeConfig.clicked.connect(self.eye_config_action)
        self.ledLayout.addWidget(self.eyeConfig)

        # LED Button Heights
        self.headLED.setFixedHeight(24)
        self.bodyLED.setFixedHeight(24)
        self.cameraLED.setFixedHeight(24)
        self.baseLED.setFixedHeight(24)
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

        self.speechInput = QLineEdit()
        self.speechInput.setObjectName("Kevinbot3_RemoteUI_SpeechInput")
        self.speechInput.setText(settings["speech"]["text"])
        self.speechInput.returnPressed.connect(lambda: com.txcv("no-pass.speech", self.speechInput.text()))
        self.speechInput.setPlaceholderText(strings.SPEECH_INPUT_H)

        self.speechGrid.addWidget(self.speechInput, 0, 0, 1, 2)

        self.speechButton = QPushButton(strings.SPEECH_BUTTON)
        self.speechButton.setObjectName("Kevinbot3_RemoteUI_SpeechButton")
        self.speechButton.clicked.connect(lambda: com.txcv("no-pass.speech", self.speechInput.text()))
        self.speechButton.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.speechGrid.addWidget(self.speechButton, 1, 0, 1, 1)

        self.speechSave = QPushButton(strings.SPEECH_SAVE)
        self.speechSave.setObjectName("Kevinbot3_RemoteUI_SpeechButton")
        self.speechSave.clicked.connect(lambda: self.save_speech(self.speechInput.text()))
        self.speechSave.setShortcut(QKeySequence("Ctrl+S"))
        self.speechGrid.addWidget(self.speechSave, 1, 1, 1, 1)

        self.espeakRadio = QRadioButton(strings.SPEECH_ESPEAK)
        self.espeakRadio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.espeakRadio.setChecked(True)
        self.espeakRadio.pressed.connect(lambda: com.txcv("no-pass.speech-engine", "espeak"))
        self.espeakRadio.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.speechGrid.addWidget(self.espeakRadio, 2, 0, 1, 1)

        self.festivalRadio = QRadioButton(strings.SPEECH_FESTIVAL)
        self.festivalRadio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.festivalRadio.pressed.connect(lambda: com.txcv("no-pass.speech-engine", "festival"))
        self.festivalRadio.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.speechGrid.addWidget(self.festivalRadio, 2, 1, 1, 1)

        self.speechWidget.setFixedHeight(self.speechWidget.sizeHint().height())
        self.speechWidget.setFixedWidth(self.speechWidget.sizeHint().width() + 100)

        self.mainLayout.addStretch()

        self.joystick = Joystick.Joystick(color=self.fg_color, max_distance=JOYSTICK_SIZE)
        self.joystick.setObjectName("Kevinbot3_RemoteUI_Joystick")
        self.joystick.posChanged.connect(self.head_changed_action)
        self.joystick.setMinimumSize(180, 180)
        self.mainLayout.addWidget(self.joystick)

        # Camera Page

        # Camera WebEngine
        self.cameraGroup = QGroupBox(strings.CAMERA_G)
        self.cameraGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.cameraLayout.addWidget(self.cameraGroup)

        self.cameraLayout = QVBoxLayout()
        self.cameraGroup.setLayout(self.cameraLayout)

        self.cameraWebView = QWebEngineView()
        self.cameraWebView.setObjectName("Kevinbot3_RemoteUI_CameraWebView")
        self.cameraLayout.addWidget(self.cameraWebView)

        # navigate to the camera page
        self.cameraWebView.load(QUrl(settings["camera_url"]))

        # Camera Leds
        self.cameraLedsGroup = QGroupBox(strings.CAMERA_LEDS_G)
        self.cameraLedsGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.cameraLayout.addWidget(self.cameraLedsGroup)

        self.cameraLedsLayout = QHBoxLayout()
        self.cameraLedsGroup.setLayout(self.cameraLedsLayout)

        self.cameraLedSlider = QSlider(Qt.Orientation.Horizontal)
        self.cameraLedSlider.setObjectName("Kevinbot3_RemoteUI_CameraLedSlider")
        slider_style = SliderProxyStyle(self.cameraLedSlider.style())
        self.cameraLedSlider.setStyle(slider_style)
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
        self.bodyEffectsGroup = QGroupBox(strings.BODY_EFFECTS_G)
        self.bodyEffectsGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.bodyColorLayout.addWidget(self.bodyEffectsGroup)

        self.bodyEffectsLayout = QGridLayout()
        self.bodyEffectsGroup.setLayout(self.bodyEffectsLayout)

        for i in range(len(settings["body_effects"])):
            if "*" not in settings["body_effects"][i]:
                effect_button = QPushButton(capitalize(settings["body_effects"][i]))
                effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
                self.bodyEffectsLayout.addWidget(effect_button, i // 2, i % 2)
                effect_button.clicked.connect(partial(self.body_effect_action, i))
                effect_button.setFixedSize(QSize(75, 50))
            elif "*c" in settings["body_effects"][i]:
                dt = datetime.datetime.now()
                if dt.day in range(20, 27) and dt.month == 12:
                    effect_button = QPushButton(capitalize(settings["body_effects"][i]))
                    effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButtonEgg")
                    effect_button.clicked.connect(partial(self.body_effect_action, i))
                    self.bodyEffectsLayout.addWidget(effect_button, (i // 2) + 1, i % 2)

        self.bodyBrightPlus = QPushButton("Bright+")
        self.bodyBrightPlus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.bodyBrightPlus.clicked.connect(lambda: com.txstr("body_bright+"))
        self.bodyBrightPlus.setFixedSize(QSize(75, 50))
        self.bodyEffectsLayout.addWidget(self.bodyBrightPlus, (len(settings["body_effects"]) // 2),
                                         (len(settings["body_effects"]) % 2) - 1)

        self.bodyBrightMinus = QPushButton("Bright-")
        self.bodyBrightMinus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.bodyBrightMinus.clicked.connect(lambda: com.txstr("body_bright-"))
        self.bodyBrightMinus.setFixedSize(QSize(75, 50))
        self.bodyEffectsLayout.addWidget(self.bodyBrightMinus, len(settings["body_effects"]) // 2,
                                         len(settings["body_effects"]) % 2)

        # Base Color Page

        # Back Button
        self.baseColorBack = QPushButton()
        self.baseColorBack.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.baseColorBack.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.baseColorBack.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.baseColorBack.setIconSize(QSize(32, 32))
        self.baseColorBack.setFixedSize(QSize(36, 36))
        self.baseColorBack.setFlat(True)
        self.baseColorLayout.addWidget(self.baseColorBack)

        # Base Color picker
        self.baseColorGroup = QGroupBox(strings.BASE_COLOR_G)
        self.baseColorGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.baseColorLayout.addWidget(self.baseColorGroup)

        self.baseColorLayoutP = QGridLayout()
        self.baseColorGroup.setLayout(self.baseColorLayoutP)

        self.baseColorPicker = ColorPicker()
        self.baseColorPicker.setObjectName("Kevinbot3_RemoteUI_BodyColorPicker")
        self.baseColorPicker.colorChanged.connect(self.base_color1_changed)
        self.baseColorPicker.setHex("000000")
        self.baseColorLayoutP.addWidget(self.baseColorPicker, 0, 0)

        # Base Color picker 2
        self.baseColorPicker2 = ColorPicker()
        self.baseColorPicker2.setObjectName("Kevinbot3_RemoteUI_BodyColorPicker")
        self.baseColorPicker2.colorChanged.connect(self.base_color2_changed)
        self.baseColorPicker2.setHex("000000")
        self.baseColorLayoutP.addWidget(self.baseColorPicker2, 1, 0)

        # Base Animation Speed
        self.baseSpeedBox = QGroupBox(strings.BASE_SPEED_G)
        self.baseSpeedBox.setObjectName("Kevinbot3_RemoteUI_Group")
        self.baseColorLayoutP.addWidget(self.baseSpeedBox, 0, 1)
        self.baseSpeedLayout = QVBoxLayout()

        self.baseSpeed = QSlider(Qt.Orientation.Horizontal)
        self.baseSpeed.setRange(100, 500)
        self.baseSpeed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.baseSpeed.valueChanged.connect(lambda x: com.txcv("base_update", map_range(x, 100, 500, 500, 100)))
        self.baseSpeedLayout.addWidget(self.baseSpeed)
        self.baseSpeedBox.setLayout(self.baseSpeedLayout)

        # Base Effects
        self.baseEffectsGroup = QGroupBox(strings.BASE_EFFECTS_G)
        self.baseEffectsGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.baseColorLayout.addWidget(self.baseEffectsGroup)

        self.baseEffectsLayout = QGridLayout()
        self.baseEffectsGroup.setLayout(self.baseEffectsLayout)

        for i in range(len(settings["base_effects"])):
            if "*" not in settings["base_effects"][i]:
                effect_button = QPushButton(capitalize(settings["base_effects"][i]))
                effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
                self.baseEffectsLayout.addWidget(effect_button, i // 2, i % 2)
                effect_button.clicked.connect(partial(self.base_effect_action, i))
                effect_button.setFixedSize(QSize(75, 50))
            elif "*c" in settings["base_effects"][i]:
                dt = datetime.datetime.now()
                if dt.day in range(20, 27) and dt.month == 12:
                    effect_button = QPushButton(capitalize(settings["base_effects"][i]))
                    effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButtonEgg")
                    effect_button.clicked.connect(partial(self.base_effect_action, i))
                    self.baseEffectsLayout.addWidget(effect_button, (i // 2) + 1, i % 2)

        self.baseBrightPlus = QPushButton("Bright+")
        self.baseBrightPlus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.baseBrightPlus.clicked.connect(lambda: com.txstr("base_bright+"))
        self.baseBrightPlus.setFixedSize(QSize(75, 50))
        self.baseEffectsLayout.addWidget(self.baseBrightPlus, (len(settings["base_effects"]) // 2),
                                         (len(settings["base_effects"]) % 2) - 1)

        self.baseBrightMinus = QPushButton("Bright-")
        self.baseBrightMinus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.baseBrightMinus.clicked.connect(lambda: com.txstr("base_bright-"))
        self.baseBrightMinus.setFixedSize(QSize(75, 50))
        self.baseEffectsLayout.addWidget(self.baseBrightMinus, len(settings["base_effects"]) // 2,
                                         len(settings["base_effects"]) % 2)

        # Arm Preset Editor

        # Title
        self.armPresetTitle = QLabel(strings.ARM_PRESET_EDIT_G)
        self.armPresetTitle.setObjectName("Kevinbot3_RemoteUI_Title")
        self.armPresetTitle.setAlignment(Qt.AlignCenter)
        self.armPresetTitle.setMaximumHeight(self.armPresetTitle.sizeHint().height())
        self.armPresetsLayout.addWidget(self.armPresetTitle)

        # Pick Preset
        self.armPresetGroup = QGroupBox(strings.PRESET_PICK)
        self.armPresetGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.armPresetsLayout.addWidget(self.armPresetGroup)

        self.armPresetLayout = QHBoxLayout()
        self.armPresetGroup.setLayout(self.armPresetLayout)

        # add arm preset buttons
        for i in range(len(settings["arm_prog"])):
            preset_button = QPushButton(strings.ARM_PRESETS[i])
            preset_button.setObjectName("Kevinbot3_RemoteUI_ArmButton")
            preset_button.setFixedSize(QSize(50, 50))
            preset_button.clicked.connect(partial(self.arm_preset_action, i))
            self.armPresetLayout.addWidget(preset_button)

        # Editor
        self.armPresetEditor = QGroupBox(strings.ARM_PRESET_EDIT)
        self.armPresetEditor.setObjectName("Kevinbot3_RemoteUI_Group")
        self.armPresetsLayout.addWidget(self.armPresetEditor)

        self.armPresetEditorLayout = QVBoxLayout()
        self.armPresetEditor.setLayout(self.armPresetEditorLayout)

        # current arm preset
        self.armPresetLabel = QLabel(strings.CURRENT_ARM_PRESET + ": Unset")
        self.armPresetLabel.setObjectName("Kevinbot3_RemoteUI_Label")
        self.armPresetLabel.setAlignment(Qt.AlignCenter)
        self.armPresetLabel.setMaximumHeight(self.armPresetLabel.minimumSizeHint().height())
        self.armPresetEditorLayout.addWidget(self.armPresetLabel)

        # stretch
        self.armPresetEditorLayout.addStretch()

        # left group box
        self.armPresetEditorLeft = QGroupBox(strings.ARM_PRESET_EDIT_L)
        self.armPresetEditorLeft.setObjectName("Kevinbot3_RemoteUI_Group")
        self.armPresetEditorLayout.addWidget(self.armPresetEditorLeft)
        self.armPresetEditorLeftLayout = QHBoxLayout()
        self.armPresetEditorLeft.setLayout(self.armPresetEditorLeftLayout)

        # right group box
        self.armPresetEditorRight = QGroupBox(strings.ARM_PRESET_EDIT_R)
        self.armPresetEditorRight.setObjectName("Kevinbot3_RemoteUI_Group")
        self.armPresetEditorLayout.addWidget(self.armPresetEditorRight)
        self.armPresetEditorRightLayout = QHBoxLayout()
        self.armPresetEditorRight.setLayout(self.armPresetEditorRightLayout)

        # use knobs and a label per servo

        self.left_knobs = []
        self.right_knobs = []
        self.left_labels = []
        self.right_labels = []

        for i in range(settings["arm_dof"]):
            # layout
            layout = QVBoxLayout()
            self.armPresetEditorLeftLayout.addLayout(layout)
            # knob
            self.left_knobs.append(QDial())
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
            self.armPresetEditorRightLayout.addLayout(layout)
            # knob
            self.right_knobs.append(QDial())
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
        self.armPresetEditorLayout.addStretch()

        # Back button and save button

        self.armBottomLayout = QHBoxLayout()
        self.armPresetsLayout.addLayout(self.armBottomLayout)

        self.armPresetBack = QPushButton()
        self.armPresetBack.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.armPresetBack.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.armPresetBack.setFixedSize(QSize(36, 36))
        self.armPresetBack.setIconSize(QSize(32, 32))
        self.armPresetBack.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.armBottomLayout.addWidget(self.armPresetBack)

        self.armPresetSave = QPushButton("    " + strings.SAVE)
        self.armPresetSave.setObjectName("Kevinbot3_RemoteUI_ArmButton")
        self.armPresetSave.setFixedHeight(36)
        self.armPresetSave.setIcon(qta.icon("fa5.save", color=self.fg_color))
        self.armPresetSave.setIconSize(QSize(32, 32))
        self.armPresetSave.clicked.connect(self.arm_preset_save_action)
        self.armBottomLayout.addWidget(self.armPresetSave)

        # Eye Configurator

        self.eyeConfigBack = QPushButton()
        self.eyeConfigBack.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.eyeConfigBack.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.eyeConfigBack.setFixedSize(QSize(36, 36))
        self.eyeConfigBack.setIconSize(QSize(32, 32))
        self.eyeConfigBack.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.eyeConfigLayout.addWidget(self.eyeConfigBack)

        # group box
        self.eyeConfigGroup = QGroupBox(strings.EYE_CONFIG_G)
        self.eyeConfigGroup.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigLayout.addWidget(self.eyeConfigGroup)
        self.eyeConfigGroupLayout = QGridLayout()
        self.eyeConfigGroup.setLayout(self.eyeConfigGroupLayout)

        # background group box
        self.eyeConfigBackground = QGroupBox(strings.EYE_CONFIG_B_G)
        self.eyeConfigBackground.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigGroupLayout.addWidget(self.eyeConfigBackground, 0, 0)
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
        self.eyeConfigPupil = QGroupBox(strings.EYE_CONFIG_P_G)
        self.eyeConfigPupil.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigGroupLayout.addWidget(self.eyeConfigPupil, 0, 1)
        self.eyeConfigPupilLayout = QHBoxLayout()
        self.eyeConfigPupil.setLayout(self.eyeConfigPupilLayout)

        # pupil image
        self.eyeConfigPupilImage = QLabel()
        self.eyeConfigPupilImage.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eyeConfigPupilImage.setPixmap(QPixmap("icons/eye-pupil.svg"))
        self.eyeConfigPupilImage.setAlignment(Qt.AlignCenter)
        self.eyeConfigPupilLayout.addWidget(self.eyeConfigPupilImage)

        # pupil palette
        self.eyeConfigPalette2 = PaletteGrid(colors=PALETTES['kevinbot'])
        self.eyeConfigPalette2.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eyeConfigPalette2.setFixedSize(self.eyeConfigPalette2.sizeHint())
        self.eyeConfigPalette2.selected.connect(self.eye_config_palette2_selected)
        self.eyeConfigPupilLayout.addWidget(self.eyeConfigPalette2)

        # iris group box
        self.eyeConfigIris = QGroupBox(strings.EYE_CONFIG_I_G)
        self.eyeConfigIris.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigGroupLayout.addWidget(self.eyeConfigIris, 1, 0)
        self.eyeConfigIrisLayout = QHBoxLayout()
        self.eyeConfigIris.setLayout(self.eyeConfigIrisLayout)

        # iris image
        self.eyeConfigIrisImage = QLabel()
        self.eyeConfigIrisImage.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eyeConfigIrisImage.setPixmap(QPixmap("icons/eye-iris.svg"))
        self.eyeConfigIrisImage.setAlignment(Qt.AlignCenter)
        self.eyeConfigIrisLayout.addWidget(self.eyeConfigIrisImage)

        # iris palette
        self.eyeConfigPalette3 = PaletteGrid(colors=PALETTES['kevinbot'])
        self.eyeConfigPalette3.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eyeConfigPalette3.setFixedSize(self.eyeConfigPalette3.sizeHint())
        self.eyeConfigPalette3.selected.connect(self.eye_config_palette3_selected)
        self.eyeConfigIrisLayout.addWidget(self.eyeConfigPalette3)

        # eye size group box
        self.eyeConfigSize = QGroupBox(strings.EYE_CONFIG_S_G)
        self.eyeConfigSize.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigGroupLayout.addWidget(self.eyeConfigSize, 1, 1)
        self.eyeConfigSizeLayout = QHBoxLayout()
        self.eyeConfigSize.setLayout(self.eyeConfigSizeLayout)

        # eye size image
        self.eyeConfigSizeImage = QLabel()
        self.eyeConfigSizeImage.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eyeConfigSizeImage.setPixmap(QPixmap("icons/eye-size.svg"))
        self.eyeConfigSizeImage.setAlignment(Qt.AlignCenter)
        self.eyeConfigSizeLayout.addWidget(self.eyeConfigSizeImage)

        # eye size slider
        self.eyeConfigSizeSlider = QSlider(Qt.Horizontal)
        self.eyeConfigSizeSlider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eyeConfigSizeSlider.setMinimum(0)
        self.eyeConfigSizeSlider.setMaximum(50)
        self.eyeConfigSizeSlider.setValue(35)
        self.eyeConfigSizeSlider.setTickPosition(QSlider.TicksBelow)
        self.eyeConfigSizeSlider.setTickInterval(5)
        self.eyeConfigSizeSlider.valueChanged.connect(self.eye_config_size_slider_value_changed)
        self.eyeConfigSizeLayout.addWidget(self.eyeConfigSizeSlider)

        # eye move speed group box
        self.eyeConfigBright = QGroupBox(strings.EYE_CONFIG_SP_G)
        self.eyeConfigBright.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigGroupLayout.addWidget(self.eyeConfigBright, 2, 0)
        self.eyeConfigSpeedLayout = QHBoxLayout()
        self.eyeConfigBright.setLayout(self.eyeConfigSpeedLayout)

        # eye speed slider
        self.eyeConfigBrightSlider = QSlider(Qt.Horizontal)
        self.eyeConfigBrightSlider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eyeConfigBrightSlider.setMinimum(1)
        self.eyeConfigBrightSlider.setMaximum(16)
        self.eyeConfigBrightSlider.setValue(5)
        self.eyeConfigBrightSlider.setTickPosition(QSlider.NoTicks)
        self.eyeConfigBrightSlider.setTickInterval(1)
        self.eyeConfigBrightSlider.valueChanged.connect(self.eye_config_speed_slider_value_changed)
        self.eyeConfigSpeedLayout.addWidget(self.eyeConfigBrightSlider)

        # eye brightness group box
        self.eyeConfigBright = QGroupBox(strings.EYE_CONFIG_BR_G)
        self.eyeConfigBright.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eyeConfigGroupLayout.addWidget(self.eyeConfigBright, 2, 1)
        self.eyeConfigSpeedLayout = QHBoxLayout()
        self.eyeConfigBright.setLayout(self.eyeConfigSpeedLayout)

        # eye brightness slider
        self.eyeConfigBrightSlider = QSlider(Qt.Horizontal)
        self.eyeConfigBrightSlider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eyeConfigBrightSlider.setMinimum(1)
        self.eyeConfigBrightSlider.setMaximum(255)
        self.eyeConfigBrightSlider.setValue(255)
        self.eyeConfigBrightSlider.setTickPosition(QSlider.NoTicks)
        self.eyeConfigBrightSlider.setTickInterval(1)
        self.eyeConfigBrightSlider.valueChanged.connect(self.eye_config_bright_slider_value_changed)
        self.eyeConfigSpeedLayout.addWidget(self.eyeConfigBrightSlider)

        # Sensors
        self.sensorsBack = QPushButton()
        self.sensorsBack.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.sensorsBack.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.sensorsBack.setFixedSize(QSize(36, 36))
        self.sensorsBack.setIconSize(QSize(32, 32))
        self.sensorsBack.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.sensorLayout.addWidget(self.sensorsBack)

        self.sensorsBox = QGroupBox(strings.SENSORS_G)
        self.sensorsBox.setObjectName("Kevinbot3_RemoteUI_Group")
        self.sensorBoxLayout = QVBoxLayout()
        self.sensorsBox.setLayout(self.sensorBoxLayout)
        self.sensorLayout.addWidget(self.sensorsBox)

        self.battLayout = QHBoxLayout()
        self.bmeLayout = QHBoxLayout()
        self.sensorBoxLayout.addLayout(self.battLayout)
        self.sensorBoxLayout.addLayout(self.bmeLayout)

        # Battery 1
        self.battery1_label = QLabel(strings.BATT_VOLT1.format("Not Installed / Unknown"))
        self.battery1_label.setFrameShape(QFrame.Shape.Box)
        self.battery1_label.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.battery1_label.setFixedHeight(32)
        self.battery1_label.setAlignment(Qt.AlignCenter)
        self.battLayout.addWidget(self.battery1_label)

        # Battery 2
        self.battery2_label = QLabel(strings.BATT_VOLT2.format("Not Installed / Unknown"))
        self.battery2_label.setFrameShape(QFrame.Shape.Box)
        self.battery2_label.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.battery2_label.setFixedHeight(32)
        self.battery2_label.setAlignment(Qt.AlignCenter)
        self.battLayout.addWidget(self.battery2_label)

        # Outside Temp
        self.outside_temp = QLabel(strings.OUTSIDE_TEMP.format("Unknown"))
        self.outside_temp.setFrameShape(QFrame.Shape.Box)
        self.outside_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.outside_temp.setFixedHeight(32)
        self.outside_temp.setAlignment(Qt.AlignCenter)
        self.bmeLayout.addWidget(self.outside_temp)

        # Outside Humidity
        self.outside_humi = QLabel(strings.OUTSIDE_HUMI.format("Unknown"))
        self.outside_humi.setFrameShape(QFrame.Shape.Box)
        self.outside_humi.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.outside_humi.setFixedHeight(32)
        self.outside_humi.setAlignment(Qt.AlignCenter)
        self.bmeLayout.addWidget(self.outside_humi)

        # Outside Pressure
        self.outside_hpa = QLabel(strings.OUTSIDE_PRES.format("Unknown"))
        self.outside_hpa.setFrameShape(QFrame.Shape.Box)
        self.outside_hpa.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.outside_hpa.setFixedHeight(32)
        self.outside_hpa.setAlignment(Qt.AlignCenter)
        self.bmeLayout.addWidget(self.outside_hpa)

        self.motorTempLayout = QHBoxLayout()
        self.sensorBoxLayout.addLayout(self.motorTempLayout)

        # Left
        self.left_temp = QLabel(strings.LEFT_TEMP.format("Unknown"))
        self.left_temp.setFrameShape(QFrame.Shape.Box)
        self.left_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.left_temp.setFixedHeight(32)
        self.left_temp.setAlignment(Qt.AlignCenter)
        self.motorTempLayout.addWidget(self.left_temp)

        # Robot Temp
        self.robot_temp = QLabel(strings.INSIDE_TEMP.format("Unknown"))
        self.robot_temp.setFrameShape(QFrame.Shape.Box)
        self.robot_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.robot_temp.setFixedHeight(32)
        self.robot_temp.setAlignment(Qt.AlignCenter)
        self.motorTempLayout.addWidget(self.robot_temp)

        # Right
        self.right_temp = QLabel(strings.RIGHT_TEMP.format("Unknown"))
        self.right_temp.setFrameShape(QFrame.Shape.Box)
        self.right_temp.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.right_temp.setFixedHeight(32)
        self.right_temp.setAlignment(Qt.AlignCenter)
        self.motorTempLayout.addWidget(self.right_temp)

        # Level
        self.level_layout = QHBoxLayout()
        self.sensorBoxLayout.addLayout(self.level_layout)

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

        self.sensorBoxLayout.addStretch()

        # Page Flip 1
        self.pageFlipLayout1 = QHBoxLayout()
        self.layout.addLayout(self.pageFlipLayout1)

        self.pageFlipLeft = QPushButton()
        self.pageFlipLeft.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.pageFlipLeft.clicked.connect(lambda: self.widget.slideInIdx(7))
        self.pageFlipLeft.setShortcut(QKeySequence(Qt.Key.Key_Comma))

        self.pageFlipRight = QPushButton()
        self.pageFlipRight.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.pageFlipRight.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.pageFlipRight.setShortcut(QKeySequence(Qt.Key.Key_Period))

        self.shutdown = QPushButton()
        self.shutdown.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.shutdown.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.shutdown.setIconSize(QSize(32, 32))
        self.shutdown.clicked.connect(self.shutdown_action)
        self.shutdown.setFixedSize(QSize(36, 36))

        # icons
        self.pageFlipLeft.setIcon(qta.icon("fa5s.thermometer-half", color=self.fg_color))
        self.pageFlipRight.setIcon(qta.icon("fa5s.camera", color=self.fg_color))

        # batt_volt1
        self.batt_volt1 = QLabel(strings.BATT_VOLT1.format("Unknown"))
        self.batt_volt1.setObjectName("Kevinbot3_RemoteUI_VoltageText")

        # batt_volt2
        self.batt_volt2 = QLabel(strings.BATT_VOLT2.format("Unknown"))
        self.batt_volt2.setObjectName("Kevinbot3_RemoteUI_VoltageText")

        # width/height
        self.pageFlipLeft.setFixedSize(36, 36)
        self.pageFlipRight.setFixedSize(36, 36)
        self.pageFlipLeft.setIconSize(QSize(32, 32))
        self.pageFlipRight.setIconSize(QSize(32, 32))

        self.aboutButton = QPushButton()
        self.aboutButton.setObjectName("Kevinbot3_RemoteUI_AboutButton")
        self.aboutButton.clicked.connect(self.about_action)
        self.aboutButton.setIcon(qta.icon("fa5s.info-circle", color=self.fg_color))
        self.aboutButton.setIconSize(QSize(32, 32))
        self.aboutButton.setFixedSize(QSize(36, 36))
        self.pageFlipLayout1.addWidget(self.pageFlipLeft)
        self.pageFlipLayout1.addStretch()
        self.pageFlipLayout1.addWidget(self.batt_volt1)
        self.pageFlipLayout1.addStretch()
        self.pageFlipLayout1.addWidget(self.shutdown)
        self.pageFlipLayout1.addStretch()
        self.pageFlipLayout1.addWidget(self.batt_volt2)
        self.pageFlipLayout1.addStretch()
        self.pageFlipLayout1.addWidget(self.pageFlipRight)

        # Page Flip 2
        self.pageFlipLayout2 = QHBoxLayout()
        self.cameraLayout.addLayout(self.pageFlipLayout2)

        self.pageFlipLeft2 = QPushButton()
        self.pageFlipLeft2.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.pageFlipLeft2.clicked.connect(lambda: self.widget.slideInIdx(0))
        self.pageFlipLeft2.setShortcut(QKeySequence(Qt.Key.Key_Comma))

        self.refreshCamera = QPushButton()
        self.refreshCamera.clicked.connect(self.cameraWebView.reload)

        self.pageFlipRight2 = QPushButton()
        self.pageFlipRight2.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.pageFlipLeft.setShortcut(QKeySequence(Qt.Key.Key_Period))
        self.pageFlipRight2.setDisabled(True)

        self.pageFlipLeft2.setIcon(qta.icon("fa5.arrow-alt-circle-left", color=self.fg_color))
        self.refreshCamera.setIcon(qta.icon("fa5s.redo-alt", color=self.fg_color))
        self.pageFlipRight2.setIcon(qta.icon("fa5.arrow-alt-circle-right", color=self.fg_color))

        self.pageFlipLeft2.setFixedSize(36, 36)
        self.refreshCamera.setFixedSize(36, 36)
        self.pageFlipRight2.setFixedSize(36, 36)
        self.pageFlipLeft2.setIconSize(QSize(32, 32))
        self.refreshCamera.setIconSize(QSize(32, 32))
        self.pageFlipRight2.setIconSize(QSize(32, 32))

        self.pageFlipLayout2.addWidget(self.pageFlipLeft2)
        self.pageFlipLayout2.addStretch()
        self.pageFlipLayout2.addWidget(self.refreshCamera)
        self.pageFlipLayout2.addStretch()
        self.pageFlipLayout2.addWidget(self.pageFlipRight2)

    def closeEvent(self, event):
        global ENABLED
        ENABLED = False
        com.xb.halt()
        event.accept()

    def init_modal(self):
        # a main_widget floating in the middle of the window
        self.modal = QWidget(self)
        self.modal.setObjectName("Kevinbot3_RemoteUI_Modal")
        self.modal.setStyleSheet("#Kevinbot3_RemoteUI_Modal { border: 1px solid " + QColor(
            self.palette().color(QPalette.ColorRole.ButtonText)).name() + "; }")
        self.modal.setFixedSize(QSize(400, 200))
        self.modal.move(int(self.width() / 2 - self.modal.width() / 2),
                        int(self.height() / 2 - self.modal.height() / 2))
        self.modal.hide()

        self.modalLayout = QGridLayout()
        self.modal.setLayout(self.modalLayout)

        self.modalIcon = QLabel()
        self.modalIcon.setPixmap(QPixmap("icons/check-circle.svg"))
        self.modalIcon.setFixedSize(QSize(128, 128))
        self.modalIcon.setScaledContents(True)
        self.modalIcon.setObjectName("Kevinbot3_RemoteUI_ModalIcon")
        self.modalLayout.addWidget(self.modalIcon, 0, 0, 1, 2)

        self.modalText = QLabel(strings.SAVE_SUCCESS)
        self.modalText.setObjectName("Kevinbot3_RemoteUI_ModalText")
        self.modalText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modalText.setWordWrap(True)
        self.modalLayout.addWidget(self.modalText, 0, 1, 1, 2)

    # noinspection PyArgumentList,PyUnresolvedReferences
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
        self.battModalShutdown.clicked.connect(lambda: self.shutdown_robot_modal_action(self.slide_out_batt_modal()))
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
        self.motTempModalShutdown.clicked.connect(lambda: self.shutdown_robot_modal_action(self.slide_out_temp_modal()))
        self.motTempModalButtonLayout.addWidget(self.motTempModalShutdown)

    def slide_out_modal(self):
        # animate modal to slide to the top and then close
        self.anim = QPropertyAnimation(self.modal, b"pos")
        self.anim.setEndValue(QPoint(int(self.modal.pos().x()),
                                     int(self.modal.pos().y() - self.modal.height() -
                                         self.modal.geometry().height() / 1.6)))
        self.anim.setEasingCurve(QEasingCurve.Type.OutSine)
        self.anim.setDuration(settings["window_properties"]["animation_speed"])
        self.anim.finished.connect(self.hide_modal)
        self.anim.start()

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
        self.anim.finished.connect(lambda: self.hide_temp_modal((not disable)))
        self.anim.start()

    def hide_modal(self):
        self.modal.hide()
        self.modal.move(int(self.width() / 2 - self.modal.width() / 2),
                        int(self.height() / 2 - self.modal.height() / 2))

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

    def shutdown_robot_modal_action(self, modal):
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
        com.txcv("base_color1", str(self.baseColorPicker.getHex()).strip("#") + "00")

    def base_color2_changed(self):
        com.txcv("base_color2", str(self.baseColorPicker2.getHex()).strip("#") + "00")

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
        self.armPresetLabel.setText(strings.CURRENT_ARM_PRESET + ": {}".format(str(index + 1)))

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
        if not extract_digits(self.armPresetLabel.text()):
            # animate self.armPresetLabel to shake using QPropertyAnimation
            self.anim = QPropertyAnimation(self.widget, b"pos")
            self.anim.setEndValue(QPoint(self.widget.pos().x() + 100, self.widget.pos().y()))
            self.anim.setEasingCurve(QEasingCurve.Type.Linear)
            self.anim.setDuration(settings["window_properties"]["error_animation_speed"])
            self.anim_2 = QPropertyAnimation(self.widget, b"pos")
            self.anim_2.setEndValue(QPoint(self.widget.pos().x() - 100, self.widget.pos().y()))
            self.anim_2.setDuration(settings["window_properties"]["error_animation_speed"])
            self.anim_3 = QPropertyAnimation(self.widget, b"pos")
            self.anim_3.setEndValue(QPoint(0, 0))
            self.anim_3.setDuration(settings["window_properties"]["error_animation_speed"])
            self.anim_group = QSequentialAnimationGroup()
            self.anim_group.addAnimation(self.anim)
            self.anim_group.addAnimation(self.anim_2)
            self.anim_group.addAnimation(self.anim_3)
            self.anim_group.start()
        else:
            self.modal.show()
            # noinspection PyTypeChecker
            QTimer.singleShot(1000, self.slide_out_modal)
            for i in range(len(settings["arm_prog"][extract_digits(self.armPresetLabel.text())[0] - 1])):
                if i < settings["arm_dof"]:
                    settings["arm_prog"][extract_digits(self.armPresetLabel.text())[0] - 1][i] = self.left_knobs[
                        i].value()
                else:
                    settings["arm_prog"][extract_digits(self.armPresetLabel.text())[0] - 1][i] = self.right_knobs[
                        i - settings["arm_dof"]].value()

            # dump json
            with open('settings.json', 'w') as file:
                json.dump(settings, file, indent=2)

    def save_speech(self, text):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed = 600)

        settings["speech"]["text"] = text
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=2)

        # show modal
        if self.modal_count < 6:
            modal_bar = KBModalBar(self)
            self.modals.append(modal_bar)
            self.modal_count += 1
            modal_bar.setTitle(strings.SAVE_SUCCESS)
            modal_bar.setDescription("Speech Preset Saved")
            modal_bar.setPixmap(qta.icon("fa5.save", color=self.fg_color).pixmap(36))

            modal_bar.popToast(popSpeed = 500, posIndex = self.modal_count)
            
            modal_timeout = QTimer()
            modal_timeout.singleShot(1500, close_modal)

    def about_action(self):
        pass

    def set_speed(self, speed):
        self.speed = speed
        settings["speed"] = speed
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=4)

    def head_changed_action(self):
        com.txcv("head_x", map_range(self.joystick.getXY()[0], 0, JOYSTICK_SIZE, 0, 60))
        com.txcv("head_y", map_range(self.joystick.getXY()[1], 0, JOYSTICK_SIZE, 0, 60))

    def shutdown_action(self):
        self.close()

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
    com.txcv("eye_size", 35, delay=0.02)


if __name__ == '__main__':
    error = None
    try:
        com.init()
        rx_thread = threading.Thread(target=rx_data, daemon=True)
        rx_thread.start()
        init_robot()
        app = QApplication(sys.argv)
        app.setApplicationName("Kevinbot Remote")
        app.setApplicationVersion(__version__)
        window = RemoteUI()
        ex = app.exec()
    #except Exception as e:
    #    com.txcv("no-pass.remote.status", "error")
    #    com.txcv("no-pass.remote.error", e)
    #    error = True
    finally:
        if not error:
            com.txcv("no-pass.remote.status", "disconnected")
    sys.exit()
