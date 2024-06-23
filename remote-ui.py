#!/usr/bin/python

"""
The Kevinbot v3 Remote
By: Kevin Ahr
"""

import datetime
import time
import json
import platform
import sys
import traceback
from functools import partial

# noinspection PyUnresolvedReferences
import PyQt5  # useful for using debuggers

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWebEngineWidgets import *
from qtpy.QtWidgets import *
from qt_thread_updater import get_updater
from QCustomWidgets import (
    KBModalBar,
    KBMainWindow,
    QSuperDial,
    KBDevice,
    KBDebugDataEntry,
    Level,
    KBSkinSelector,
    KBDualColorPicker,
    KBHandshakeWidget,
)
import qtawesome as qta

import Joystick.Joystick as Joystick
import SlidingStackedWidget as SlidingStackedWidget
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
CURRENT_ARM_POS = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # two 5dof arms
HIGH_INSIDE_TEMP = 45

EYE_SKINS = {
    "Simple": (3, "icons/eye.svg"),
    "Metallic": (4, "icons/iris.png"),
    "Neon": (5, "icons/neon1.png"),
}
EYE_MOTIONS = {
    "Smooth": (1, "res/eye_motions/smooth.gif"),
    "Jump": (2, "res/eye_motions/const.gif"),
    "Manual": (3, "res/eye_motions/manual.svg"),
}
EYE_NEON_SKINS = {
    "Circle": ("neon1.png", "res/eye_skin_neon/neon1.png"),
    "Semicircle": ("neon2.png", "res/eye_skin_neon/neon2.png"),
    "Striped\nCircle": ("neon3.png", "res/eye_skin_neon/neon3.png"),
}

__version__ = "v1.0.0"
__author__ = "Kevin Ahr"

window = None
disable_batt_modal = False
disable_temp_modal = False
enabled = False
last_alive_message = datetime.datetime.now()

# load settings from file
with open("settings.json", "r") as f:
    settings = json.load(f)


def save_settings():
    with open("settings.json", "w") as file:
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
        self.setWindowIcon(QIcon("icons/icon.svg"))

        # start coms
        com.init(callback=self.serial_callback)
        init_robot()

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setFixedSize(800, 480)

        # load theme
        try:
            load_theme(
                self,
                settings["window_properties"]["theme"],
                settings["window_properties"]["theme_colors"],
            )
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        # vars
        self.modal_count = 0
        self.modals = []
        self.full_mesh = []
        self.full_mesh_last_part = 0
        self.eye_skin = 3
        self.eye_neon_left_color = "#ffffff"
        self.eye_neon_right_color = "#ffffff"

        self.init_ui()

        com.txcv("eye.get_settings", True)

        if settings["dev_mode"]:
            self.createDevTools()

        try:
            remote_version = open("version.txt", "r").read()
        except FileNotFoundError:
            remote_version = "UNKNOWN"
        com.txcv("core.remotes.add", f"{remote_name}|{remote_version}|kevinbot.remote")

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def serial_callback(self, message):
        # noinspection PyBroadException
        try:
            if not "rf_data" in message:
                # TODO: Add a more permanant solution for the 0x74 error
                # 0x74 = Message to long
                print(f"Status message", message)
                return

            data = message["rf_data"].decode("utf-8").strip("\r\n")
            data = data.split("=", maxsplit=1)

            print(data)
            if data[0] == "handshake.end" and data[1] == remote_name:
                get_updater().call_latest(window.widget.setCurrentIndex, 1)
            elif data[0] == "bms.voltages":
                if window is not None:
                    volt1, volt2 = data[1].split(",")
                    get_updater().call_latest(
                        window.batt_volt1.setText,
                        strings.BATT_VOLT1.format(float(volt1) / 10) + "V",
                    )
                    get_updater().call_latest(
                        window.battery1_label.setText,
                        strings.BATT_VOLT1.format(float(volt1) / 10),
                    )

                    if float(volt1) / 10 < warning_voltage:
                        get_updater().call_latest(
                            window.battery1_label.setStyleSheet,
                            "background-color: #df574d;",
                        )
                    else:
                        get_updater().call_latest(
                            window.battery1_label.setStyleSheet, ""
                        )

                    if ENABLE_BATT2:
                        get_updater().call_latest(
                            window.batt_volt2.setText,
                            strings.BATT_VOLT2.format(float(volt2) / 10) + "V",
                        )
                        get_updater().call_latest(
                            window.battery2_label.setText,
                            strings.BATT_VOLT2.format(float(volt2) / 10),
                        )
                        if float(volt2) / 10 < warning_voltage:
                            get_updater().call_latest(
                                window.battery2_label.setStyleSheet,
                                "background-color: #df574d;",
                            )
                        else:
                            get_updater().call_latest(
                                window.battery2_label.setStyleSheet, ""
                            )

                    if not disable_batt_modal:
                        if float(volt1) / 10 < 11:
                            print(enabled)
                            if enabled:
                                get_updater().call_latest(window.request_enabled, False)
                            get_updater().call_latest(
                                window.battModalText.setText, strings.BATT_LOW
                            )
                            get_updater().call_latest(window.batt_modal.show)
                        elif float(volt2) / 10 < 11:
                            if enabled:
                                get_updater().call_latest(window.request_enabled, False)
                            get_updater().call_latest(
                                window.battModalText.setText, strings.BATT_LOW
                            )
                            get_updater().call_latest(window.batt_modal.show)
            # bme280 sensor
            elif data[0] == "bme":
                if window is not None:
                    get_updater().call_latest(
                        window.outside_temp.setText,
                        strings.OUTSIDE_TEMP.format(
                            str(data[1].split(",")[0])
                            + "℃ ("
                            + str(data[1].split(",")[1])
                            + "℉)"
                        ),
                    )
                    get_updater().call_latest(
                        window.outside_humi.setText,
                        strings.OUTSIDE_HUMI.format(data[1].split(",")[2]),
                    )
                    get_updater().call_latest(
                        window.outside_hpa.setText,
                        strings.OUTSIDE_PRES.format(data[1].split(",")[3]),
                    )
            # motor, body temps
            elif data[0] == "temps":
                if window is not None:
                    get_updater().call_latest(
                        window.left_temp.setText,
                        strings.LEFT_TEMP.format(
                            rstr(data[1].split(",")[0])
                            + "℃ ("
                            + rstr(convert_c_to_f(float(data[1].split(",")[0])))
                            + "℉)"
                        ),
                    )
                    get_updater().call_latest(
                        window.right_temp.setText,
                        strings.RIGHT_TEMP.format(
                            rstr(data[1].split(",")[1])
                            + "℃ ("
                            + rstr(convert_c_to_f(float(data[1].split(",")[1])))
                            + "℉)"
                        ),
                    )

                    get_updater().call_latest(
                        window.robot_temp.setText,
                        strings.INSIDE_TEMP.format(
                            rstr(data[1].split(",")[2])
                            + "℃ ("
                            + rstr(convert_c_to_f(float(data[1].split(",")[2])))
                            + "℉)"
                        ),
                    )

                    if float(data[1].split(",")[0]) > HIGH_MOTOR_TEMP:
                        get_updater().call_latest(
                            window.left_temp.setStyleSheet, "background-color: #df574d;"
                        )
                        get_updater().call_latest(window.motor_stick.setDisabled, True)
                        if not disable_temp_modal:
                            com.txmot([1500, 1500])
                            get_updater().call_latest(
                                window.motTempModalText.setText, strings.MOT_TEMP_HIGH
                            )
                            get_updater().call_latest(window.motTemp_modal.show)
                    else:
                        get_updater().call_latest(window.left_temp.setStyleSheet, "")

                    if float(data[1].split(",")[1]) > HIGH_MOTOR_TEMP:
                        get_updater().call_latest(
                            window.right_temp.setStyleSheet,
                            "background-color: #df574d;",
                        )
                        get_updater().call_latest(window.motor_stick.setDisabled, True)
                        if not disable_temp_modal:
                            com.txmot([1500, 1500])
                            get_updater().call_latest(
                                window.motTempModalText.setText, strings.MOT_TEMP_HIGH
                            )
                            get_updater().call_latest(window.motTemp_modal.show)
                    else:
                        get_updater().call_latest(window.right_temp.setStyleSheet, "")

                    if float(data[1].split(",")[2]) > HIGH_INSIDE_TEMP:
                        get_updater().call_latest(
                            window.robot_temp.setStyleSheet,
                            "background-color: #df574d;",
                        )
                    else:
                        get_updater().call_latest(window.robot_temp.setStyleSheet, "")
            # yaw, pitch, roll
            elif data[0] == "imu":
                roll, pitch, yaw = data[1].split(",")
                if window is not None:
                    get_updater().call_latest(
                        window.level.setAngles, (float(roll), float(pitch), float(yaw))
                    )
                    if abs(float(roll)) > 18:
                        get_updater().call_latest(
                            window.level.setLineColor, QColor("#df574d")
                        )
                    elif abs(float(roll)) > 10:
                        get_updater().call_latest(
                            window.level.setLineColor, QColor("#eebc2a")
                        )
                    else:
                        get_updater().call_latest(window.level.setLineColor, Qt.white)
            # core alive message
            elif data[0] == "core.uptime":
                if window:
                    delta = datetime.timedelta(seconds=int(data[1]))
                    get_updater().call_latest(
                        self.debug_uptime.setText,
                        strings.CORE_UPTIME.format(delta, data[1] + "s"),
                    )
            # sys uptime
            elif data[0] == "os_uptime":
                if window:
                    delta = datetime.timedelta(seconds=int(data[1]))
                    get_updater().call_latest(
                        self.debug_sys_uptime.setText,
                        strings.SYS_UPTIME.format(delta, data[1] + "s"),
                    )
            # remote disable
            elif data[0] == "remote.disableui":
                if str(data[1]).lower() == "true":
                    get_updater().call_latest(window.arm_group.setDisabled, True)
                    get_updater().call_latest(window.led_group.setDisabled, True)
                    get_updater().call_latest(window.main_group.setDisabled, True)

                    if settings["window_properties"]["ui_style"] == "modern":
                        get_updater().call_latest(
                            window.bottom_base_led_button.setDisabled, True
                        )
                        get_updater().call_latest(
                            window.bottom_body_led_button.setDisabled, True
                        )
                        get_updater().call_latest(
                            window.bottom_head_led_button.setDisabled, True
                        )
                        get_updater().call_latest(
                            window.bottom_eye_button.setDisabled, True
                        )

                else:
                    get_updater().call_latest(window.arm_group.setDisabled, False)
                    get_updater().call_latest(window.led_group.setDisabled, False)
                    get_updater().call_latest(window.main_group.setDisabled, False)

                    if settings["window_properties"]["ui_style"] == "modern":
                        get_updater().call_latest(
                            window.bottom_base_led_button.setDisabled, False
                        )
                        get_updater().call_latest(
                            window.bottom_body_led_button.setDisabled, False
                        )
                        get_updater().call_latest(
                            window.bottom_head_led_button.setDisabled, False
                        )
                        get_updater().call_latest(
                            window.bottom_eye_button.setDisabled, False
                        )
            # old remote enable
            elif data[0] == "core.enabled":
                while not window:
                    time.sleep(0.02)

                get_updater().call_latest(window.set_enabled, data[1].lower() == "true")
            elif data[0] == "core.enablefailed":
                get_updater().call_latest(window.show_enabled_fail, int(data[1]))
            elif data[0] == "core.speech-engine":
                while not window:
                    time.sleep(0.02)

                if data[1] == "festival":
                    get_updater().call_latest(window.festival_radio.blockSignals, True)
                    get_updater().call_latest(window.festival_radio.setChecked, True)
                    get_updater().call_latest(window.festival_radio.blockSignals, False)
                else:
                    get_updater().call_latest(window.espeak_radio.blockSignals, True)
                    get_updater().call_latest(window.espeak_radio.setChecked, True)
                    get_updater().call_latest(window.espeak_radio.blockSignals, False)
            elif data == ["core.service.init", "kevinbot.com"]:
                get_updater().call_latest(window.pop_com_service_modal)
                try:
                    remote_version = open("version.txt", "r").read()
                except FileNotFoundError:
                    remote_version = "UNKNOWN"
                com.txcv(
                    "core.remotes.add",
                    f"{remote_name}|{remote_version}|kevinbot.remote",
                )
            elif data[0].startswith("core.full_mesh"):
                cmd_part = data[0].split(":")[1]
                cmd_parts = data[0].split(":")[2]

                self.full_mesh.insert(int(cmd_part), data[1])

                if int(cmd_parts) == int(cmd_part):
                    get_updater().call_latest(
                        window.add_mesh_devices, "".join(self.full_mesh)
                    )
                    self.full_mesh = []
            elif data[0] == "core.ping":
                src_dest = data[1].split(",", maxsplit=1)
                get_updater().call_latest(window.ping, src_dest[0])
            elif data[0] == "eye_settings.states.page":
                if window:
                    get_updater().call_latest(
                        self.eye_config_stack.setCurrentIndex, int(data[1]) - 3
                    )
            elif data[0] == "eye_settings.skins.simple.iris_size":
                if window:
                    get_updater().call_latest(
                        self.eye_simple_iris_size_slider.blockSignals, True
                    )
                    get_updater().call_latest(
                        self.eye_simple_iris_size_slider.setValue, int(data[1])
                    )
                    get_updater().call_latest(
                        self.eye_simple_iris_size_slider.blockSignals, False
                    )
            elif data[0] == "eye_settings.skins.simple.pupil_size":
                if window:
                    get_updater().call_latest(
                        self.eye_simple_pupil_size_slider.blockSignals, True
                    )
                    get_updater().call_latest(
                        self.eye_simple_pupil_size_slider.setValue, int(data[1])
                    )
                    get_updater().call_latest(
                        self.eye_simple_pupil_size_slider.blockSignals, False
                    )
            elif data[0] == "eye_settings.skins.neon.fg_color_start":
                if window:
                    self.eye_neon_left_color = data[1].strip('"')
            elif data[0] == "eye_settings.skins.neon.fg_color_end":
                if window:
                    self.eye_neon_right_color = data[1].strip('"')
            elif (
                data[0] == "eye_settings.display.backlight"
                or data[0] == "eye.set_backlight"
            ):
                if window:
                    get_updater().call_latest(
                        self.eye_config_light_slider.blockSignals, True
                    )
                    get_updater().call_latest(
                        self.eye_config_light_slider.setValue, int(data[1])
                    )
                    get_updater().call_latest(
                        self.eye_config_light_slider.blockSignals, False
                    )
            elif data[0] == "eye_settings.motions.speed" or data[0] == "eye.set_speed":
                if window:
                    get_updater().call_latest(
                        self.eye_config_speed_slider.setValue, int(data[1])
                    )
            elif data[0] == "eye_settings.states.motion" or data[0] == "eye.set_motion":
                if window:
                    if data[1] == "3":
                        get_updater().call_latest(
                            self.eye_joystick_group.setEnabled, True
                        )
                        get_updater().call_latest(
                            self.eye_joystick.setColor, self.fg_color
                        )
                    else:
                        get_updater().call_latest(
                            self.eye_joystick_group.setEnabled, False
                        )
                        get_updater().call_latest(
                            self.eye_joystick.setColor, QColor("#9E9E9E")
                        )

        except Exception:
            traceback.print_exc()

    # noinspection PyUnresolvedReferences
    def init_ui(self):
        self.widget = SlidingStackedWidget.SlidingStackedWidget()
        self.setCentralWidget(self.widget)

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

        self.widget.setDirection(settings["window_properties"]["animation_dir"])
        self.widget.setSpeed(settings["window_properties"]["animation_speed"])

        self.connect_widget = KBHandshakeWidget(QColor(self.fg_color))
        self.connect_widget.setObjectName("Kevinbot3_RemoteUI_HandshakeWidget")

        self.main_widget = QWidget()
        self.main_widget.setObjectName("Kevinbot3_RemoteUI_MainWidget")

        self.camera_widget = QWidget()
        self.camera_widget.setObjectName("Kevinbot3_RemoteUI_CameraWidget")

        self.head_color_widget = QWidget()
        self.head_color_widget.setObjectName("Kevinbot3_RemoteUI_HeadColorWidget")

        self.body_color_widget = QWidget()
        self.body_color_widget.setObjectName("Kevinbot3_RemoteUI_BodyColorWidget")

        self.base_color_widget = QWidget()
        self.base_color_widget.setObjectName("Kevinbot3_RemoteUI_BaseColorWidget")

        self.arm_presets_widget = QWidget()
        self.arm_presets_widget.setObjectName("Kevinbot3_RemoteUI_ArmPresetsWidget")

        self.eye_config_widget = QWidget()
        self.eye_config_widget.setObjectName("Kevinbot3_RemoteUI_EyeConfigWidget")

        self.sensors_widget = QWidget()
        self.sensors_widget.setObjectName("Kevinbot3_RemoteUI_SensorsWidget")

        self.debug_widget = QWidget()
        self.debug_widget.setObjectName("Kevinbot3_RemoteUI_DebugWidget")

        self.mesh_widget = QWidget()
        self.mesh_widget.setObjectName("Kevinbot3_RemoteUI_MeshWidget")

        self.widget.addWidget(self.connect_widget)

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        self.widget.addWidget(self.main_widget)

        self.camera_layout = QVBoxLayout()
        self.camera_widget.setLayout(self.camera_layout)
        self.widget.addWidget(self.camera_widget)

        self.head_color_layout = QHBoxLayout()
        self.head_color_widget.setLayout(self.head_color_layout)
        self.widget.addWidget(self.head_color_widget)

        self.body_color_layout = QHBoxLayout()
        self.body_color_widget.setLayout(self.body_color_layout)
        self.widget.addWidget(self.body_color_widget)

        self.base_color_layout = QHBoxLayout()
        self.base_color_widget.setLayout(self.base_color_layout)
        self.widget.addWidget(self.base_color_widget)

        self.arm_presets_layout = QVBoxLayout()
        self.arm_presets_widget.setLayout(self.arm_presets_layout)
        self.widget.addWidget(self.arm_presets_widget)

        self.eye_config_layout = QHBoxLayout()
        self.eye_config_layout.setContentsMargins(2, 2, 2, 2)
        self.eye_config_widget.setLayout(self.eye_config_layout)
        self.widget.addWidget(self.eye_config_widget)

        self.sensor_layout = QHBoxLayout()
        self.sensors_widget.setLayout(self.sensor_layout)
        self.widget.addWidget(self.sensors_widget)

        self.mesh_layout = QHBoxLayout()
        self.mesh_widget.setLayout(self.mesh_layout)
        self.widget.addWidget(self.mesh_widget)

        self.debug_layout = QHBoxLayout()
        self.debug_widget.setLayout(self.debug_layout)
        self.widget.addWidget(self.debug_widget)

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

        if settings["window_properties"]["ui_style"] == "classic":
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

        self.eye_config = QPushButton(strings.LED_EYE_CONFIG)
        self.eye_config.setObjectName("Kevinbot3_RemoteUI_LedButton")
        self.eye_config.clicked.connect(self.eye_config_action)
        self.led_layout.addWidget(self.eye_config)

        # LED Button Heights
        self.head_led.setFixedHeight(24)
        self.body_led.setFixedHeight(24)
        self.camera_led.setFixedHeight(24)
        self.base_led.setFixedHeight(24)
        self.eye_config.setFixedHeight(24)

        # Joysticks and Speech

        self.main_group = QGroupBox(strings.MAIN_G)
        self.main_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.layout.addWidget(self.main_group)

        self.main_layout = QHBoxLayout()
        self.main_group.setLayout(self.main_layout)

        self.motor_stick = Joystick.Joystick(
            color=self.fg_color, sticky=False, max_distance=JOYSTICK_SIZE
        )
        self.motor_stick.setObjectName("Kevinbot3_RemoteUI_Joystick")
        self.motor_stick.posChanged.connect(self.motor_action)
        self.motor_stick.centerEvent.connect(com.txstop)
        self.motor_stick.setMinimumSize(180, 180)
        self.main_layout.addWidget(self.motor_stick)

        self.main_layout.addStretch()

        self.speech_widget = QWidget()
        self.speech_widget = QWidget()
        self.speech_widget.setObjectName("Kevinbot3_RemoteUI_SpeechWidget")
        self.main_layout.addWidget(self.speech_widget)

        self.speech_grid = QGridLayout()
        self.speech_widget.setLayout(self.speech_grid)

        self.e_stop = QPushButton("E-STOP")
        self.e_stop.setObjectName("E_Stop")
        self.e_stop.setShortcut(Qt.Key.Key_Space)
        self.e_stop.setMinimumHeight(64)
        self.e_stop.pressed.connect(self.e_stop_action)
        self.speech_grid.addWidget(self.e_stop, 0, 0, 1, 2)

        self.enable_button = QPushButton("ENABLE")
        self.enable_button.setObjectName("Enable_Button")
        self.enable_button.setMinimumHeight(42)
        self.enable_button.clicked.connect(lambda: self.request_enabled(True))
        self.speech_grid.addWidget(self.enable_button, 1, 0)

        self.disable_button = QPushButton("DISABLE")
        self.disable_button.setObjectName("Disable_Button")
        self.disable_button.setMinimumHeight(42)
        self.disable_button.clicked.connect(lambda: self.request_enabled(False))
        self.speech_grid.addWidget(self.disable_button, 1, 1)

        self.speech_input = QLineEdit()
        self.speech_input.setObjectName("Kevinbot3_RemoteUI_SpeechInput")
        self.speech_input.setText(settings["speech"]["text"])
        self.speech_input.returnPressed.connect(
            lambda: com.txcv("core.speech", self.speech_input.text())
        )
        self.speech_input.setPlaceholderText(strings.SPEECH_INPUT_H)
        self.speech_grid.addWidget(self.speech_input, 2, 0, 1, 2)

        self.speech_button = QPushButton(strings.SPEECH_BUTTON)
        self.speech_button.setObjectName("Kevinbot3_RemoteUI_SpeechButton")
        self.speech_button.clicked.connect(
            lambda: com.txcv("core.speech", self.speech_input.text())
        )
        self.speech_button.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.speech_grid.addWidget(self.speech_button, 3, 0)

        self.speech_save = QPushButton(strings.SPEECH_SAVE)
        self.speech_save.setObjectName("Kevinbot3_RemoteUI_SpeechButton")
        self.speech_save.clicked.connect(
            lambda: self.save_speech(self.speech_input.text())
        )
        self.speech_save.setShortcut(QKeySequence("Ctrl+S"))
        self.speech_grid.addWidget(self.speech_save, 3, 1)

        self.espeak_radio = QRadioButton(strings.SPEECH_ESPEAK)
        self.espeak_radio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.espeak_radio.setChecked(True)
        self.espeak_radio.pressed.connect(
            lambda: com.txcv("core.speech-engine", "espeak")
        )
        self.espeak_radio.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.speech_grid.addWidget(self.espeak_radio, 4, 0)

        self.festival_radio = QRadioButton(strings.SPEECH_FESTIVAL)
        self.festival_radio.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.festival_radio.pressed.connect(
            lambda: com.txcv("core.speech-engine", "festival")
        )
        self.festival_radio.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.speech_grid.addWidget(self.festival_radio, 4, 1)

        self.speech_widget.setFixedHeight(self.speech_widget.sizeHint().height())
        self.speech_widget.setFixedWidth(self.speech_widget.sizeHint().width() + 100)

        self.main_layout.addStretch()

        self.head_stick = Joystick.Joystick(
            color=self.fg_color, max_distance=JOYSTICK_SIZE
        )
        self.head_stick.setObjectName("Kevinbot3_RemoteUI_Joystick")
        self.head_stick.posChanged.connect(self.head_changed_action)
        self.head_stick.setMinimumSize(180, 180)
        self.main_layout.addWidget(self.head_stick)

        # Camera Page

        # Camera WebEngine
        self.camera_group = QGroupBox(strings.CAMERA_G)
        self.camera_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.camera_layout.addWidget(self.camera_group)

        self.camera_layout = QVBoxLayout()
        self.camera_group.setLayout(self.camera_layout)

        self.camera_web_view = QWebEngineView()
        self.camera_web_view.setObjectName("Kevinbot3_RemoteUI_CameraWebView")
        self.camera_layout.addWidget(self.camera_web_view)

        # navigate to the camera page
        self.camera_web_view.load(QUrl(settings["camera_url"]))

        # Camera Leds
        self.camera_leds_group = QGroupBox(strings.CAMERA_LEDS_G)
        self.camera_leds_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.camera_layout.addWidget(self.camera_leds_group)

        self.camera_leds_layout = QHBoxLayout()
        self.camera_leds_group.setLayout(self.camera_leds_layout)

        self.camera_led_slider = QSlider(Qt.Orientation.Horizontal)
        self.camera_led_slider.setObjectName("Kevinbot3_RemoteUI_CameraLedSlider")
        self.camera_led_slider.valueChanged.connect(self.camera_brightness_changed)
        self.camera_led_slider.setRange(0, 255)
        self.camera_leds_layout.addWidget(self.camera_led_slider)

        # Head Color Page

        # Back Button
        self.head_color_back = QPushButton()
        self.head_color_back.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.head_color_back.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.head_color_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.head_color_back.setIconSize(QSize(32, 32))
        self.head_color_back.setFixedSize(QSize(36, 36))
        self.head_color_back.setFlat(True)
        self.head_color_layout.addWidget(self.head_color_back)

        # Head Colorpicker
        self.head_color_group = QGroupBox(strings.HEAD_COLOR_G)
        self.head_color_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.head_color_layout.addWidget(self.head_color_group)

        self.head_color_layout_p = QGridLayout()
        self.head_color_group.setLayout(self.head_color_layout_p)

        self.head_color_picker = ColorPicker()
        self.head_color_picker.setObjectName("Kevinbot3_RemoteUI_HeadColorPicker")
        self.head_color_picker.colorChanged.connect(self.head_color1_changed)
        self.head_color_picker.setHex("000000")
        self.head_color_layout_p.addWidget(self.head_color_picker, 0, 0)

        # Head Colorpicker 2
        self.head_color_picker_2 = ColorPicker()
        self.head_color_picker_2.setObjectName("Kevinbot3_RemoteUI_HeadColorPicker")
        self.head_color_picker_2.colorChanged.connect(self.head_color2_changed)
        self.head_color_picker_2.setHex("000000")
        self.head_color_layout_p.addWidget(self.head_color_picker_2, 1, 0)

        self.head_right_layout = QVBoxLayout()
        self.head_color_layout.addLayout(self.head_right_layout)

        # Head Animation Speed
        self.head_speed_box = QGroupBox(strings.HEAD_SPEED_G)
        self.head_speed_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.head_right_layout.addWidget(self.head_speed_box)

        self.head_speed_layout = QVBoxLayout()
        self.head_speed_box.setLayout(self.head_speed_layout)

        self.head_speed = QSlider(Qt.Orientation.Horizontal)
        self.head_speed.setRange(100, 500)
        self.head_speed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.head_speed.valueChanged.connect(
            lambda x: com.txcv("head_update", map_range(x, 100, 500, 500, 100))
        )
        self.head_speed_layout.addWidget(self.head_speed)

        # Head Effects
        self.head_effects_group = QGroupBox(strings.HEAD_EFFECTS_G)
        self.head_effects_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.head_right_layout.addWidget(self.head_effects_group)

        self.head_effects_layout = QGridLayout()
        self.head_effects_group.setLayout(self.head_effects_layout)

        for i in range(len(settings["head_effects"])):
            effect_button = QPushButton(capitalize(settings["head_effects"][i]))
            effect_button.setObjectName("Kevinbot3_RemoteUI_HeadEffectButton")
            self.head_effects_layout.addWidget(effect_button, i // 3, i % 3)
            effect_button.clicked.connect(partial(self.head_effect_action, i))
            effect_button.setFixedSize(QSize(75, 50))

        # Body Color Page

        # Back Button
        self.body_color_back = QPushButton()
        self.body_color_back.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.body_color_back.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.body_color_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.body_color_back.setIconSize(QSize(32, 32))
        self.body_color_back.setFixedSize(QSize(36, 36))
        self.body_color_back.setFlat(True)
        self.body_color_layout.addWidget(self.body_color_back)

        # Body Color picker
        self.body_color_group = QGroupBox(strings.BODY_COLOR_G)
        self.body_color_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.body_color_layout.addWidget(self.body_color_group)

        self.bodyColorLayoutP = QGridLayout()
        self.body_color_group.setLayout(self.bodyColorLayoutP)

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

        self.body_right_layout = QVBoxLayout()
        self.body_color_layout.addLayout(self.body_right_layout)

        # Body Animation Speed
        self.bodySpeedBox = QGroupBox(strings.BODY_SPEED_G)
        self.bodySpeedBox.setObjectName("Kevinbot3_RemoteUI_Group")
        self.body_right_layout.addWidget(self.bodySpeedBox)

        self.bodySpeedLayout = QVBoxLayout()
        self.bodySpeedBox.setLayout(self.bodySpeedLayout)

        self.bodySpeed = QSlider(Qt.Orientation.Horizontal)
        self.bodySpeed.setRange(100, 500)
        self.bodySpeed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.bodySpeed.valueChanged.connect(
            lambda x: com.txcv("body_update", map_range(x, 100, 500, 500, 100))
        )
        self.bodySpeedLayout.addWidget(self.bodySpeed)

        # Body Effects
        self.body_effects_group = QGroupBox(strings.BODY_EFFECTS_G)
        self.body_effects_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.body_right_layout.addWidget(self.body_effects_group)

        self.body_effects_layout = QGridLayout()
        self.body_effects_group.setLayout(self.body_effects_layout)

        for i in range(len(settings["body_effects"])):
            effect_button = QPushButton(capitalize(settings["body_effects"][i]))
            effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
            self.body_effects_layout.addWidget(effect_button, i // 4, i % 4)
            effect_button.clicked.connect(partial(self.body_effect_action, i))
            effect_button.setFixedSize(QSize(75, 50))

        self.body_bright_plus = QPushButton("Bright+")
        self.body_bright_plus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.body_bright_plus.clicked.connect(lambda: com.txstr("body_bright+"))
        self.body_bright_plus.setFixedSize(QSize(75, 50))
        self.body_effects_layout.addWidget(
            self.body_bright_plus,
            (len(settings["body_effects"]) // 4),
            (len(settings["body_effects"]) % 4),
        )

        self.body_bright_minus = QPushButton("Bright-")
        self.body_bright_minus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.body_bright_minus.clicked.connect(lambda: com.txstr("body_bright-"))
        self.body_bright_minus.setFixedSize(QSize(75, 50))
        self.body_effects_layout.addWidget(
            self.body_bright_minus,
            len(settings["body_effects"]) // 4,
            len(settings["body_effects"]) % 4 + 1,
        )

        # Base Color Page

        # Back Button
        self.base_color_back = QPushButton()
        self.base_color_back.setObjectName("Kevinbot3_RemoteUI_BackButton")
        self.base_color_back.clicked.connect(lambda: self.widget.slideInIdx(1))
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

        self.base_right_layout = QVBoxLayout()
        self.base_color_layout.addLayout(self.base_right_layout)

        # Base Animation Speed
        self.base_speed_box = QGroupBox(strings.BASE_SPEED_G)
        self.base_speed_box.setObjectName("Kevinbot3_RemoteUI_Group")
        self.base_right_layout.addWidget(self.base_speed_box)
        self.base_speed_layout = QVBoxLayout()

        self.base_speed = QSlider(Qt.Orientation.Horizontal)
        self.base_speed.setRange(100, 500)
        self.base_speed.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.base_speed.valueChanged.connect(
            lambda x: com.txcv("base_update", map_range(x, 100, 500, 500, 100))
        )
        self.base_speed_layout.addWidget(self.base_speed)
        self.base_speed_box.setLayout(self.base_speed_layout)

        # Base Effects
        self.base_effects_group = QGroupBox(strings.BASE_EFFECTS_G)
        self.base_effects_group.setObjectName("Kevinbot3_RemoteUI_Group")
        self.base_right_layout.addWidget(self.base_effects_group)

        self.base_effects_layout = QGridLayout()
        self.base_effects_group.setLayout(self.base_effects_layout)

        for i in range(len(settings["base_effects"])):
            effect_button = QPushButton(capitalize(settings["base_effects"][i]))
            effect_button.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
            self.base_effects_layout.addWidget(effect_button, i // 4, i % 4)
            effect_button.clicked.connect(partial(self.base_effect_action, i))
            effect_button.setFixedSize(QSize(75, 50))

        self.base_bright_plus = QPushButton("Bright+")
        self.base_bright_plus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.base_bright_plus.clicked.connect(lambda: com.txstr("base_bright+"))
        self.base_bright_plus.setFixedSize(QSize(75, 50))
        self.base_effects_layout.addWidget(
            self.base_bright_plus,
            (len(settings["base_effects"]) // 4),
            (len(settings["base_effects"]) % 4),
        )

        self.base_bright_minus = QPushButton("Bright-")
        self.base_bright_minus.setObjectName("Kevinbot3_RemoteUI_BodyEffectButton")
        self.base_bright_minus.clicked.connect(lambda: com.txstr("base_bright-"))
        self.base_bright_minus.setFixedSize(QSize(75, 50))
        self.base_effects_layout.addWidget(
            self.base_bright_minus,
            len(settings["base_effects"]) // 4,
            len(settings["base_effects"]) % 4 + 1,
        )

        # Arm Preset Editor

        # Title
        self.arm_preset_title = QLabel(strings.ARM_PRESET_EDIT_G)
        self.arm_preset_title.setObjectName("Kevinbot3_RemoteUI_Title")
        self.arm_preset_title.setAlignment(Qt.AlignCenter)
        self.arm_preset_title.setMaximumHeight(
            self.arm_preset_title.sizeHint().height()
        )
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
        self.arm_preset_label.setMaximumHeight(
            self.arm_preset_label.minimumSizeHint().height()
        )
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
            self.left_knobs[i].setRange(
                settings["arm_min_max"][i][0], settings["arm_min_max"][i][1]
            )
            self.left_knobs[i].setValue(settings["arm_prog"][0][i])
            self.left_knobs[i].setFixedSize(QSize(72, 72))

            layout.addWidget(self.left_knobs[i])
            # label
            self.left_labels.append(QLabel(str(settings["arm_prog"][0][i])))
            self.left_labels[i].setObjectName("Kevinbot3_RemoteUI_ArmLabel")
            self.left_labels[i].setAlignment(Qt.AlignCenter)
            self.left_labels[i].setFixedSize(QSize(72, 24))
            layout.addWidget(self.left_labels[i])

            self.left_knobs[i].valueChanged.connect(
                partial(self.arm_preset_left_changed, i)
            )

        for i in range(settings["arm_dof"]):
            # layout
            layout = QVBoxLayout()
            self.arm_preset_editor_right_layout.addLayout(layout)
            # knob
            self.right_knobs.append(QSuperDial(knob_radius=8, knob_margin=7))
            self.right_knobs[i].setObjectName("Kevinbot3_RemoteUI_ArmKnob")
            self.right_knobs[i].setRange(
                settings["arm_min_max"][i + settings["arm_dof"]][0],
                settings["arm_min_max"][i + settings["arm_dof"]][1],
            )
            self.right_knobs[i].setValue(
                settings["arm_prog"][0][i + settings["arm_dof"]]
            )
            self.right_knobs[i].setFixedSize(QSize(72, 72))
            layout.addWidget(self.right_knobs[i])
            # label
            self.right_labels.append(
                QLabel(str(settings["arm_prog"][0][i + settings["arm_dof"]]))
            )
            self.right_labels[i].setObjectName("Kevinbot3_RemoteUI_ArmLabel")
            self.right_labels[i].setAlignment(Qt.AlignCenter)
            self.right_labels[i].setFixedSize(QSize(72, 24))
            layout.addWidget(self.right_labels[i])

            self.right_knobs[i].valueChanged.connect(
                partial(self.arm_preset_right_changed, i)
            )

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
        self.arm_preset_back.clicked.connect(lambda: self.widget.slideInIdx(1))
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
        self.eye_config_back.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.eye_config_back.setFlat(True)
        self.eye_config_layout.addWidget(self.eye_config_back)

        self.eye_config_tabs = QTabWidget()
        self.eye_config_layout.addWidget(self.eye_config_tabs)

        self.eye_config_skins_layout = QVBoxLayout()
        self.eye_config_skins_widget = QWidget()
        self.eye_config_skins_widget.setLayout(self.eye_config_skins_layout)

        self.eye_config_tabs.addTab(self.eye_config_skins_widget, strings.SKINS)

        self.eye_config_properties_layout = QVBoxLayout()
        self.eye_config_properties_widget = QWidget()
        self.eye_config_properties_widget.setLayout(self.eye_config_properties_layout)

        self.eye_config_tabs.addTab(
            self.eye_config_properties_widget, strings.PROPERTIES
        )

        # Eye Skin Select
        self.eye_skin_selector = KBSkinSelector()
        self.eye_skin_selector.setStyleSheet(
            "border-top: none; "
            "border-left: none; "
            "border-right: none; "
            "border-radius: 0px;"
        )
        self.eye_skin_selector.addSkins(EYE_SKINS, self.eye_set_state)
        self.eye_config_skins_layout.addWidget(self.eye_skin_selector)

        self.eye_config_stack = QStackedWidget()
        self.eye_config_skins_layout.addWidget(self.eye_config_stack)

        # Simple Skin
        self.eye_simple_layout = QGridLayout()
        self.eye_simple_layout.setContentsMargins(0, 0, 0, 0)
        self.eye_simple_widget = QWidget()
        self.eye_simple_widget.setLayout(self.eye_simple_layout)
        self.eye_config_stack.insertWidget(0, self.eye_simple_widget)

        # background group box
        self.eye_simple_background = QGroupBox(strings.EYE_CONFIG_B_G)
        self.eye_simple_background.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_simple_layout.addWidget(self.eye_simple_background, 0, 0)
        self.eye_simple_background_layout = QHBoxLayout()
        self.eye_simple_background.setLayout(self.eye_simple_background_layout)

        # background image
        self.eye_simple_background_image = QLabel()
        self.eye_simple_background_image.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigImage"
        )
        self.eye_simple_background_image.setPixmap(
            QPixmap("icons/eye-bg.svg").scaledToWidth(
                96, Qt.TransformationMode.SmoothTransformation
            )
        )
        self.eye_simple_background_image.setAlignment(Qt.AlignCenter)
        self.eye_simple_background_layout.addWidget(self.eye_simple_background_image)

        # palette
        self.eye_simple_bg_palette = PaletteGrid(colors=PALETTES["kevinbot"])
        self.eye_simple_bg_palette.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eye_simple_bg_palette.setFixedSize(self.eye_simple_bg_palette.sizeHint())
        self.eye_simple_bg_palette.selected.connect(self.eye_config_simple_bg_selected)
        self.eye_simple_background_layout.addWidget(self.eye_simple_bg_palette)

        # pupil group box
        self.eye_simple_pupil_color = QGroupBox(strings.EYE_CONFIG_P_G)
        self.eye_simple_pupil_color.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_simple_layout.addWidget(self.eye_simple_pupil_color, 0, 1)
        self.eye_simple_pupil_color_layout = QHBoxLayout()
        self.eye_simple_pupil_color.setLayout(self.eye_simple_pupil_color_layout)

        # pupil image
        self.eye_simple_pupil_color_image = QLabel()
        self.eye_simple_pupil_color_image.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigImage"
        )
        self.eye_simple_pupil_color_image.setPixmap(
            QPixmap("icons/eye-pupil.svg").scaledToWidth(
                96, Qt.TransformationMode.SmoothTransformation
            )
        )
        self.eye_simple_pupil_color_image.setAlignment(Qt.AlignCenter)
        self.eye_simple_pupil_color_layout.addWidget(self.eye_simple_pupil_color_image)

        # pupil palette
        self.eye_simple_pupil_palette = PaletteGrid(colors=PALETTES["kevinbot"])
        self.eye_simple_pupil_palette.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigPalette"
        )
        self.eye_simple_pupil_palette.setFixedSize(
            self.eye_simple_pupil_palette.sizeHint()
        )
        self.eye_simple_pupil_palette.selected.connect(
            self.eye_config_simple_pupil_selected
        )
        self.eye_simple_pupil_color_layout.addWidget(self.eye_simple_pupil_palette)

        # iris group box
        self.eye_simple_iris = QGroupBox(strings.EYE_CONFIG_I_G)
        self.eye_simple_iris.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_simple_layout.addWidget(self.eye_simple_iris, 1, 0, 2, 1)
        self.eye_simple_iris_layout = QHBoxLayout()
        self.eye_simple_iris.setLayout(self.eye_simple_iris_layout)

        # iris image
        self.eye_simple_iris_image = QLabel()
        self.eye_simple_iris_image.setObjectName("Kevinbot3_RemoteUI_EyeConfigImage")
        self.eye_simple_iris_image.setPixmap(
            QPixmap("icons/eye-iris.svg").scaledToWidth(
                96, Qt.TransformationMode.SmoothTransformation
            )
        )
        self.eye_simple_iris_image.setAlignment(Qt.AlignCenter)
        self.eye_simple_iris_layout.addWidget(self.eye_simple_iris_image)

        # iris palette
        self.eye_simple_iris_palette = PaletteGrid(colors=PALETTES["kevinbot"])
        self.eye_simple_iris_palette.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigPalette"
        )
        self.eye_simple_iris_palette.setFixedSize(
            self.eye_simple_iris_palette.sizeHint()
        )
        self.eye_simple_iris_palette.selected.connect(
            self.eye_config_simple_iris_selected
        )
        self.eye_simple_iris_layout.addWidget(self.eye_simple_iris_palette)

        # pupil size group box
        self.eye_simple_pupil_size = QGroupBox(strings.EYE_CONFIG_PS_G)
        self.eye_simple_pupil_size.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_simple_layout.addWidget(self.eye_simple_pupil_size, 1, 1)
        self.eye_simple_pupil_size_layout = QHBoxLayout()
        self.eye_simple_pupil_size.setLayout(self.eye_simple_pupil_size_layout)

        # pupil size slider
        self.eye_simple_pupil_size_slider = QSlider(Qt.Horizontal)
        self.eye_simple_pupil_size_slider.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigSlider"
        )
        self.eye_simple_pupil_size_slider.setMinimum(0)
        self.eye_simple_pupil_size_slider.setMaximum(100)
        self.eye_simple_pupil_size_slider.setValue(35)
        self.eye_simple_pupil_size_slider.setTickPosition(QSlider.TicksBelow)
        self.eye_simple_pupil_size_slider.setTickInterval(5)
        self.eye_simple_pupil_size_slider.valueChanged.connect(
            self.eye_config_pupil_size_slider_value_changed
        )
        self.eye_simple_pupil_size_layout.addWidget(self.eye_simple_pupil_size_slider)

        # iris size group box
        self.eye_simple_iris_size = QGroupBox(strings.EYE_CONFIG_IS_G)
        self.eye_simple_iris_size.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_simple_layout.addWidget(self.eye_simple_iris_size, 2, 1)
        self.eye_simple_iris_size_layout = QHBoxLayout()
        self.eye_simple_iris_size.setLayout(self.eye_simple_iris_size_layout)

        # iris size slider
        self.eye_simple_iris_size_slider = QSlider(Qt.Horizontal)
        self.eye_simple_iris_size_slider.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigSlider"
        )
        self.eye_simple_iris_size_slider.setMinimum(0)
        self.eye_simple_iris_size_slider.setMaximum(150)
        self.eye_simple_iris_size_slider.setValue(35)
        self.eye_simple_iris_size_slider.setTickPosition(QSlider.TicksBelow)
        self.eye_simple_iris_size_slider.setTickInterval(5)
        self.eye_simple_iris_size_slider.valueChanged.connect(
            self.eye_config_iris_size_slider_value_changed
        )
        self.eye_simple_iris_size_layout.addWidget(self.eye_simple_iris_size_slider)

        # Metal Skin
        self.eye_metal_layout = QGridLayout()
        self.eye_metal_layout.setContentsMargins(0, 0, 0, 0)
        self.eye_metal_widget = QWidget()
        self.eye_metal_widget.setLayout(self.eye_metal_layout)
        self.eye_config_stack.insertWidget(1, self.eye_metal_widget)

        # iris tint group box
        self.eye_metal_iris_tint = QGroupBox(strings.EYE_CONFIG_METAL_IS_T_G)
        self.eye_metal_iris_tint.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_metal_layout.addWidget(self.eye_metal_iris_tint, 0, 0, 1, 2)
        self.eye_metal_iris_tint_layout = QVBoxLayout()
        self.eye_metal_iris_tint.setLayout(self.eye_metal_iris_tint_layout)

        # iris tint slider
        self.eye_metal_iris_tint_slider = QSlider(Qt.Horizontal)
        self.eye_metal_iris_tint_slider.setObjectName(
            "Kevinbot3_RemoteUI_EyeConfigSlider"
        )
        self.eye_metal_iris_tint_slider.setMinimum(0)
        self.eye_metal_iris_tint_slider.setMaximum(255)
        self.eye_metal_iris_tint_slider.setValue(35)
        self.eye_metal_iris_tint_slider.setTickPosition(QSlider.TicksBelow)
        self.eye_metal_iris_tint_slider.setTickInterval(5)
        self.eye_metal_iris_tint_slider.valueChanged.connect(
            self.eye_config_metal_tint_changed
        )
        self.eye_metal_iris_tint_layout.addWidget(self.eye_metal_iris_tint_slider)

        self.eye_metal_iris_tint_image = QLabel()
        self.eye_metal_iris_tint_image.setPixmap(QPixmap("res/misc/hues.png"))
        self.eye_metal_iris_tint_image.setScaledContents(True)
        self.eye_metal_iris_tint_image.setFixedHeight(24)
        self.eye_metal_iris_tint_layout.addWidget(self.eye_metal_iris_tint_image)

        # Neon Skin
        self.eye_neon_layout = QGridLayout()
        self.eye_neon_layout.setContentsMargins(0, 0, 0, 0)
        self.eye_neon_widget = QWidget()
        self.eye_neon_widget.setLayout(self.eye_neon_layout)
        self.eye_config_stack.insertWidget(2, self.eye_neon_widget)

        self.eye_neon_selector = KBSkinSelector(direction=QBoxLayout.Direction.Down)
        self.eye_neon_selector.setStyleSheet("margin: 8px;")
        self.eye_neon_selector.setContentsMargins(0, 0, 0, 0)
        self.eye_neon_selector.addSkins(EYE_NEON_SKINS, self.eye_set_neon_style, 84, 88)
        self.eye_neon_selector.setFixedWidth(124)
        self.eye_neon_layout.addWidget(self.eye_neon_selector, 0, 3, 3, 1)

        self.eye_neon_fg_color_picker = KBDualColorPicker(
            self.palette(), strings.EYE_CONFIG_NEON_PALETTES
        )
        self.eye_neon_fg_color_picker.palette_a.selected.connect(
            self.eye_neon_left_changed
        )
        self.eye_neon_fg_color_picker.palette_b.selected.connect(
            self.eye_neon_right_changed
        )
        self.eye_neon_fg_color_picker.swap.clicked.connect(self.eye_neon_swap_colors)
        self.eye_neon_fg_color_picker.arrow_a.clicked.connect(self.eye_neon_copy_rtl)
        self.eye_neon_fg_color_picker.arrow_b.clicked.connect(self.eye_neon_copy_ltr)
        self.eye_neon_layout.addWidget(self.eye_neon_fg_color_picker, 0, 0, 1, 2)

        # background group box
        self.eye_neon_background = QGroupBox(strings.EYE_CONFIG_B_G)
        self.eye_neon_background.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_neon_layout.addWidget(self.eye_neon_background, 1, 0)
        self.eye_neon_background_layout = QHBoxLayout()
        self.eye_neon_background_layout.setContentsMargins(0, 2, 0, 2)
        self.eye_neon_background.setLayout(self.eye_neon_background_layout)

        self.eye_neon_bg_palette = PaletteGrid(colors=PALETTES["kevinbot"])
        self.eye_neon_bg_palette.setObjectName("Kevinbot3_RemoteUI_EyeConfigPalette")
        self.eye_neon_bg_palette.setFixedSize(self.eye_neon_bg_palette.sizeHint())
        self.eye_neon_bg_palette.selected.connect(self.eye_config_neon_bg_selected)
        self.eye_neon_background_layout.addWidget(self.eye_neon_bg_palette)

        # Eye Props

        self.eye_config_bottom_layout = QHBoxLayout()
        self.eye_config_properties_layout.addLayout(self.eye_config_bottom_layout)

        # eye motions
        self.eye_config_motions = KBSkinSelector()
        self.eye_config_motions.addSkins(
            EYE_MOTIONS,
            self.eye_config_motion_selected,
            button_height=96,
            icon_size=QSize(128, 128),
        )
        self.eye_config_properties_layout.addWidget(self.eye_config_motions)

        # eye joystick
        self.eye_joystick_group = QGroupBox(strings.EYE_JOYSTICK)
        self.eye_config_properties_layout.addWidget(self.eye_joystick_group)
        self.eye_joystick_layout = QHBoxLayout()
        self.eye_joystick_group.setLayout(self.eye_joystick_layout)

        self.eye_joystick = Joystick.Joystick(
            sticky=True, color=self.fg_color, max_distance=80
        )
        self.eye_joystick.setFixedSize(QSize(180, 180))
        self.eye_joystick.posChanged.connect(self.eye_pos_changed)
        self.eye_joystick_layout.addWidget(self.eye_joystick)

        # eye move speed group box
        self.eye_config_bright = QGroupBox(strings.EYE_CONFIG_SP_G)
        self.eye_config_bright.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_bottom_layout.addWidget(self.eye_config_bright)
        self.eye_config_speed_layout = QHBoxLayout()
        self.eye_config_bright.setLayout(self.eye_config_speed_layout)

        # eye speed slider
        self.eye_config_speed_slider = QSlider(Qt.Horizontal)
        self.eye_config_speed_slider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eye_config_speed_slider.setMinimum(1)
        self.eye_config_speed_slider.setMaximum(100)
        self.eye_config_speed_slider.setValue(50)
        self.eye_config_speed_slider.setTickPosition(QSlider.NoTicks)
        self.eye_config_speed_slider.setTickInterval(1)
        self.eye_config_speed_slider.valueChanged.connect(
            self.eye_config_speed_slider_value_changed
        )
        self.eye_config_speed_layout.addWidget(self.eye_config_speed_slider)

        # eye brightness group box
        self.eye_config_bright = QGroupBox(strings.EYE_CONFIG_BR_G)
        self.eye_config_bright.setObjectName("Kevinbot3_RemoteUI_Group")
        self.eye_config_bottom_layout.addWidget(self.eye_config_bright)
        self.eye_config_speed_layout = QHBoxLayout()
        self.eye_config_bright.setLayout(self.eye_config_speed_layout)

        # eye brightness slider
        self.eye_config_light_slider = QSlider(Qt.Horizontal)
        self.eye_config_light_slider.setObjectName("Kevinbot3_RemoteUI_EyeConfigSlider")
        self.eye_config_light_slider.setMinimum(1)
        self.eye_config_light_slider.setMaximum(100)
        self.eye_config_light_slider.setValue(100)
        self.eye_config_light_slider.setTickPosition(QSlider.NoTicks)
        self.eye_config_light_slider.setTickInterval(1)
        self.eye_config_light_slider.valueChanged.connect(
            self.eye_config_bright_slider_value_changed
        )
        self.eye_config_speed_layout.addWidget(self.eye_config_light_slider)

        # Sensors
        self.sensors_back = QPushButton()
        self.sensors_back.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.sensors_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.sensors_back.setFixedSize(QSize(36, 36))
        self.sensors_back.setIconSize(QSize(32, 32))
        self.sensors_back.clicked.connect(lambda: self.widget.slideInIdx(1))
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
        self.battery1_label = QLabel(
            strings.BATT_VOLT1.format("Not Installed / Unknown")
        )
        self.battery1_label.setFrameShape(QFrame.Shape.Box)
        self.battery1_label.setObjectName("Kevinbot3_RemoteUI_SensorData")
        self.battery1_label.setFixedHeight(32)
        self.battery1_label.setAlignment(Qt.AlignCenter)
        self.batt_layout.addWidget(self.battery1_label)

        # Battery 2
        self.battery2_label = QLabel(
            strings.BATT_VOLT2.format("Not Installed / Unknown")
        )
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

        self.level = Level(self.palette())
        self.level.setFixedSize(QSize(500, 320))
        self.level.setLineColor(self.fg_color)
        self.level.setLineWidth(16)
        self.level.setRobotColor(QColor(0, 34, 255))
        self.level.setBackgroundColor(
            QColor(
                QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                QColor(self.palette().color(QPalette.Window)).getRgb()[2],
            )
        )
        self.level_layout.addWidget(self.level)

        self.sensor_box_layout.addStretch()

        # Mesh
        self.mesh_back = QPushButton()
        self.mesh_back.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.mesh_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.mesh_back.setFixedSize(QSize(36, 36))
        self.mesh_back.setIconSize(QSize(32, 32))
        self.mesh_back.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.mesh_layout.addWidget(self.mesh_back)

        self.mesh_inner_layout = QVBoxLayout()
        self.mesh_layout.addLayout(self.mesh_inner_layout)

        self.connected_devices = QLabel(
            strings.CONNECTED_DEVICES.format(strings.UNKNOWN)
        )
        self.connected_devices.setStyleSheet("font-family: Roboto; font-size: 16px;")
        self.connected_devices.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mesh_inner_layout.addWidget(self.connected_devices)

        self.devices_scroll = QScrollArea()
        self.devices_layout = QVBoxLayout()
        self.devices_widget = QWidget()
        self.devices_widget.setLayout(self.devices_layout)
        self.mesh_inner_layout.addWidget(self.devices_scroll)

        self.devices_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.devices_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.devices_scroll.setWidgetResizable(True)
        QScroller.grabGesture(
            self.devices_scroll, QScroller.LeftMouseButtonGesture
        )  # enable single-touch scroll
        self.devices_scroll.setWidget(self.devices_widget)

        self.devices_refresh = QPushButton(strings.REFRESH)
        self.devices_refresh.clicked.connect(self.refresh_mesh)
        self.mesh_inner_layout.addWidget(self.devices_refresh)

        # Debug
        self.debug_back = QPushButton()
        self.debug_back.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.debug_back.setIcon(qta.icon("fa5s.caret-left", color=self.fg_color))
        self.debug_back.setFixedSize(QSize(36, 36))
        self.debug_back.setIconSize(QSize(32, 32))
        self.debug_back.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.debug_layout.addWidget(self.debug_back)

        self.debug_inner_layout = QVBoxLayout()
        self.debug_layout.addLayout(self.debug_inner_layout)

        self.debug_title = QLabel(strings.DEBUG_TITLE)
        self.debug_title.setStyleSheet("font-family: Roboto; font-size: 16px;")
        self.debug_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.debug_inner_layout.addWidget(self.debug_title)

        self.debug_scroll = QScrollArea()
        self.debug_scroll_layout = QVBoxLayout()
        self.debug_scroll_widget = QWidget()
        self.debug_scroll_widget.setLayout(self.debug_scroll_layout)
        self.debug_inner_layout.addWidget(self.debug_scroll)

        self.debug_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.debug_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.debug_scroll.setWidgetResizable(True)
        QScroller.grabGesture(
            self.debug_scroll, QScroller.LeftMouseButtonGesture
        )  # enable single-touch scroll
        self.debug_scroll.setWidget(self.debug_scroll_widget)

        self.debug_uptime = KBDebugDataEntry()
        self.debug_uptime.setText(
            strings.CORE_UPTIME.format(strings.UNKNOWN, strings.UNKNOWN)
        )
        self.debug_uptime.setIcon(qta.icon("mdi.timer", color="#00BCD4"))
        self.debug_scroll_layout.addWidget(self.debug_uptime)

        self.debug_sys_uptime = KBDebugDataEntry()
        self.debug_sys_uptime.setText(
            strings.SYS_UPTIME.format(strings.UNKNOWN, strings.UNKNOWN)
        )
        self.debug_sys_uptime.setIcon(qta.icon("mdi.timer", color="#F44336"))
        self.debug_scroll_layout.addWidget(self.debug_sys_uptime)

        # Page Flip 1
        self.page_flip_layout_1 = QHBoxLayout()
        self.layout.addLayout(self.page_flip_layout_1)

        self.page_flip_left = QPushButton()
        self.page_flip_left.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_left.clicked.connect(lambda: self.widget.slideInIdx(8))
        self.page_flip_left.setShortcut(QKeySequence(Qt.Key.Key_Comma))

        self.page_flip_mesh = QPushButton()
        self.page_flip_mesh.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_mesh.clicked.connect(lambda: self.widget.slideInIdx(9))

        self.page_flip_debug = QPushButton()
        self.page_flip_debug.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_debug.clicked.connect(lambda: self.widget.slideInIdx(10))

        self.page_flip_right = QPushButton()
        self.page_flip_right.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_right.clicked.connect(lambda: self.widget.slideInIdx(2))
        self.page_flip_right.setShortcut(QKeySequence(Qt.Key.Key_Period))

        self.shutdown = QPushButton()
        self.shutdown.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.shutdown.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.shutdown.setIconSize(QSize(32, 32))
        self.shutdown.clicked.connect(self.shutdown_action)
        self.shutdown.setFixedSize(QSize(36, 36))

        # icons
        self.page_flip_left.setIcon(
            qta.icon("fa5s.thermometer-half", color=self.fg_color)
        )
        self.page_flip_mesh.setIcon(
            qta.icon("fa5s.project-diagram", color=self.fg_color)
        )
        self.page_flip_debug.setIcon(
            qta.icon(
                "fa5s.bug",
                color=(
                    self.fg_color
                    if settings["window_properties"]["ui_style"] == "classic"
                    else "#4CAF50"
                ),
            )
        )
        self.page_flip_right.setIcon(qta.icon("fa5s.camera", color=self.fg_color))

        # batts
        self.bottom_batt_layout = QVBoxLayout()

        # batt_volt1
        self.batt_volt1 = QLabel(strings.BATT_VOLT1.format("Unknown"))

        # batt_volt2
        self.batt_volt2 = QLabel(strings.BATT_VOLT2.format("Unknown"))

        # width/height
        self.page_flip_left.setFixedSize(36, 36)
        self.page_flip_mesh.setFixedSize(36, 36)
        self.page_flip_debug.setFixedSize(36, 36)
        self.page_flip_right.setFixedSize(36, 36)
        self.page_flip_left.setIconSize(QSize(32, 32))
        self.page_flip_mesh.setIconSize(QSize(24, 24))
        self.page_flip_debug.setIconSize(QSize(24, 24))
        self.page_flip_right.setIconSize(QSize(32, 32))

        if settings["window_properties"]["ui_style"] == "classic":
            self.page_flip_layout_1.addWidget(self.page_flip_left)
            self.page_flip_layout_1.addWidget(self.page_flip_mesh)
            self.page_flip_layout_1.addWidget(self.page_flip_debug)
            self.page_flip_layout_1.addStretch()
            self.page_flip_layout_1.addWidget(self.batt_volt1)
            self.page_flip_layout_1.addStretch()
            self.page_flip_layout_1.addWidget(self.shutdown)
            self.page_flip_layout_1.addStretch()
            if ENABLE_BATT2:
                self.page_flip_layout_1.addWidget(self.batt_volt2)
                self.page_flip_layout_1.addStretch()
            self.page_flip_layout_1.addWidget(self.page_flip_right)
        elif settings["window_properties"]["ui_style"] == "modern":
            self.bottom_batt_layout.addWidget(self.batt_volt1)
            if ENABLE_BATT2:
                self.bottom_batt_layout.addWidget(self.batt_volt2)

            self.page_flip_layout_1.addWidget(self.page_flip_left)
            self.page_flip_layout_1.addWidget(self.page_flip_mesh)
            self.page_flip_layout_1.addWidget(self.page_flip_debug)
            self.page_flip_layout_1.addStretch()
            self.page_flip_layout_1.addLayout(self.bottom_batt_layout)
            self.page_flip_layout_1.addStretch()
            self.page_flip_layout_1.addWidget(
                self.shutdown, alignment=Qt.AlignmentFlag.AlignVCenter
            )
            self.page_flip_layout_1.addStretch()

            self.bottom_head_led_button = QPushButton()
            self.bottom_head_led_button.setFixedSize(QSize(36, 36))
            self.bottom_head_led_button.setIconSize(QSize(32, 32))
            self.bottom_head_led_button.setIcon(
                qta.icon("ph.number-circle-one-fill", color="#ff2a2a")
            )
            self.bottom_head_led_button.clicked.connect(lambda: self.led_action(0))
            self.page_flip_layout_1.addWidget(self.bottom_head_led_button)

            self.bottom_body_led_button = QPushButton()
            self.bottom_body_led_button.setFixedSize(QSize(36, 36))
            self.bottom_body_led_button.setIconSize(QSize(32, 32))
            self.bottom_body_led_button.setIcon(
                qta.icon("ph.number-circle-two-fill", color="#5fd35f")
            )
            self.bottom_body_led_button.clicked.connect(lambda: self.led_action(1))
            self.page_flip_layout_1.addWidget(self.bottom_body_led_button)

            self.bottom_base_led_button = QPushButton()
            self.bottom_base_led_button.setFixedSize(QSize(36, 36))
            self.bottom_base_led_button.setIconSize(QSize(32, 32))
            self.bottom_base_led_button.setIcon(
                qta.icon("ph.number-circle-three-fill", color="#2a7fff")
            )
            self.bottom_base_led_button.clicked.connect(lambda: self.led_action(2))
            self.page_flip_layout_1.addWidget(self.bottom_base_led_button)

            self.bottom_eye_button = QPushButton()
            self.bottom_eye_button.setFixedSize(QSize(36, 36))
            self.bottom_eye_button.setIconSize(QSize(32, 32))
            self.bottom_eye_button.setIcon(qta.icon("fa5s.eye", color="#ff7fff"))
            self.bottom_eye_button.clicked.connect(self.eye_config_action)
            self.page_flip_layout_1.addWidget(self.bottom_eye_button)

            self.page_flip_layout_1.addWidget(self.page_flip_right)

        # Page Flip 2
        self.page_flip_layout_2 = QHBoxLayout()
        self.camera_layout.addLayout(self.page_flip_layout_2)

        self.page_flip_left_2 = QPushButton()
        self.page_flip_left_2.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_left_2.clicked.connect(lambda: self.widget.slideInIdx(1))
        self.page_flip_left_2.setShortcut(QKeySequence(Qt.Key.Key_Comma))

        self.refresh_camera = QPushButton()
        self.refresh_camera.clicked.connect(self.camera_web_view.reload)

        self.page_flip_right_2 = QPushButton()
        self.page_flip_right_2.setObjectName("Kevinbot3_RemoteUI_PageFlipButton")
        self.page_flip_left.setShortcut(QKeySequence(Qt.Key.Key_Period))
        self.page_flip_right_2.setDisabled(True)

        self.page_flip_left_2.setIcon(
            qta.icon("fa5.arrow-alt-circle-left", color=self.fg_color)
        )
        self.refresh_camera.setIcon(qta.icon("fa5s.redo-alt", color=self.fg_color))
        self.page_flip_right_2.setIcon(
            qta.icon("fa5.arrow-alt-circle-right", color=self.fg_color)
        )

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

        if settings["window_properties"]["ui_style"] == "modren":
            self.bottom_base_led_button.setEnabled(False)
            self.bottom_body_led_button.setEnabled(False)
            self.bottom_head_led_button.setEnabled(False)
            self.bottom_eye_button.setEnabled(False)

    def closeEvent(self, event):
        if com.ser:
            com.xb.halt()

        event.accept()

    # noinspection PyUnresolvedReferences
    def init_batt_modal(self):
        # a main widget floating in the middle of the window
        self.batt_modal = QWidget(self)
        self.batt_modal.setFixedSize(QSize(400, 200))
        self.batt_modal.setObjectName("Kevinbot3_RemoteUI_Modal")
        self.batt_modal.setStyleSheet(
            "#Kevinbot3_RemoteUI_Modal { border: 1px solid "
            + QColor(self.palette().color(QPalette.ColorRole.ButtonText)).name()
            + "; }"
        )
        self.batt_modal.move(
            int(self.width() / 2 - self.batt_modal.width() / 2),
            int(self.height() / 2 - self.batt_modal.height() / 2),
        )
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
        self.battModalClose.clicked.connect(
            lambda: self.slide_out_batt_modal(disable=True)
        )
        self.battModalButtonLayout.addWidget(self.battModalClose)

        self.battModalShutdown = QPushButton(strings.MODAL_SHUTDOWN)
        self.battModalShutdown.setObjectName("Kevinbot3_RemoteUI_ModalButton")
        self.battModalShutdown.setFixedHeight(36)
        self.battModalShutdown.clicked.connect(self.shutdown_robot_modal_action)
        self.battModalButtonLayout.addWidget(self.battModalShutdown)

    # noinspection PyArgumentList,PyUnresolvedReferences
    def init_mot_temp_modal(self):
        # a main widget floating in the middle of the window
        self.motTemp_modal = QWidget(self)
        self.motTemp_modal.setObjectName("Kevinbot3_RemoteUI_Modal")
        self.motTemp_modal.setStyleSheet(
            "#Kevinbot3_RemoteUI_Modal { border: 1px solid "
            + QColor(self.palette().color(QPalette.ColorRole.ButtonText)).name()
            + "; }"
        )
        self.motTemp_modal.setFixedSize(QSize(400, 200))
        self.motTemp_modal.move(
            int(self.width() / 2 - self.motTemp_modal.width() / 2),
            int(self.height() / 2 - self.motTemp_modal.height() / 2),
        )
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
        self.motTempModalClose.clicked.connect(
            lambda: self.slide_out_temp_modal(disable=True)
        )
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
        self.anim.setEndValue(
            QPoint(
                int(self.batt_modal.pos().x()),
                int(
                    self.batt_modal.pos().y()
                    - self.batt_modal.height()
                    - self.batt_modal.geometry().height() / 1.6
                ),
            )
        )
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
        self.anim.setEndValue(
            QPoint(
                int(self.motTemp_modal.pos().x()),
                int(
                    self.motTemp_modal.pos().y()
                    - self.motTemp_modal.height()
                    - self.motTemp_modal.geometry().height() / 1.6
                ),
            )
        )
        self.anim.setEasingCurve(QEasingCurve.Type.OutSine)
        self.anim.setDuration(settings["window_properties"]["animation_speed"])
        # noinspection PyUnresolvedReferences
        self.anim.finished.connect(lambda: self.hide_temp_modal((not disable)))
        self.anim.start()

    def hide_batt_modal(self, end=False):
        global disable_batt_modal
        disable_batt_modal = True

        self.batt_modal.hide()
        self.batt_modal.move(
            int(self.width() / 2 - self.batt_modal.width() / 2),
            int(self.height() / 2 - self.batt_modal.height() / 2),
        )

        if end:
            self.close()
            sys.exit()

    def hide_temp_modal(self, end=False):
        global disable_temp_modal
        disable_temp_modal = True

        self.motTemp_modal.hide()
        self.motTemp_modal.move(
            int(self.width() / 2 - self.motTemp_modal.width() / 2),
            int(self.height() / 2 - self.motTemp_modal.height() / 2),
        )

        if end:
            self.close()
            sys.exit()

    def shutdown_robot_modal_action(self):
        com.txstr("core.remote.status=disconnected")
        com.tx_e_stop()
        self.close()

    def camera_led_action(self):
        old_dir = self.widget.getDirection()
        self.widget.setDirection(Qt.Axis.YAxis)
        self.widget.slideInIdx(2)
        self.widget.setDirection(old_dir)

    def arm_edit_action(self):
        old_dir = self.widget.getDirection()
        self.widget.setDirection(Qt.Axis.YAxis)
        self.widget.slideInIdx(6)
        self.widget.setDirection(old_dir)

    @staticmethod
    def arm_action(index):
        global CURRENT_ARM_POS
        com.txcv("arms", settings["arm_prog"][index])
        CURRENT_ARM_POS = settings["arm_prog"][index]

    def led_action(self, index):
        self.widget.slideInIdx(3 + index)

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
        self.widget.slideInIdx(7)

    def head_color1_changed(self):
        com.txcv("head_color1", str(self.head_color_picker.getHex()).strip("#") + "00")

    def head_color2_changed(self):
        com.txcv(
            "head_color2", str(self.head_color_picker_2.getHex()).strip("#") + "00"
        )

    def body_color1_changed(self):
        com.txcv("body_color1", str(self.bodyColorPicker.getHex()).strip("#") + "00")

    def body_color2_changed(self):
        com.txcv("body_color2", str(self.bodyColorPicker2.getHex()).strip("#") + "00")

    def base_color1_changed(self):
        com.txcv("base_color1", str(self.base_color_picker.getHex()).strip("#") + "00")

    def base_color2_changed(self):
        com.txcv(
            "base_color2", str(self.base_color_picker_2.getHex()).strip("#") + "00"
        )

    def camera_brightness_changed(self):
        com.txcv("cam_brightness", str(self.camera_led_slider.value()))

    def arm_preset_action(self, index):
        global CURRENT_ARM_POS
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
                self.right_knobs[i - settings["arm_dof"]].setValue(
                    settings["arm_prog"][index][i]
                )

        # update labels
        for i in range(len(settings["arm_prog"][index])):
            if i < settings["arm_dof"]:
                self.left_labels[i].setText(str(settings["arm_prog"][index][i]))
            else:
                self.right_labels[i - settings["arm_dof"]].setText(
                    str(settings["arm_prog"][index][i])
                )

        # allow events on knobs
        for i in range(len(settings["arm_prog"][index])):
            if i < settings["arm_dof"]:
                self.left_knobs[i].blockSignals(False)
            else:
                self.right_knobs[i - settings["arm_dof"]].blockSignals(False)

        # update label
        self.arm_preset_label.setText(
            strings.CURRENT_ARM_PRESET + ": {}".format(str(index + 1))
        )

    def arm_preset_left_changed(self, index):
        global CURRENT_ARM_POS
        self.left_labels[index].setText(str(self.left_knobs[index].value()))
        com.txcv(
            "arms",
            [self.left_knobs[i].value() for i in range(len(self.left_knobs))]
            + [self.right_knobs[i].value() for i in range(len(self.right_knobs))],
        )
        CURRENT_ARM_POS = [
            self.left_knobs[i].value() for i in range(len(self.left_knobs))
        ] + [self.right_knobs[i].value() for i in range(len(self.right_knobs))]

    def arm_preset_right_changed(self, index):
        global CURRENT_ARM_POS
        self.right_labels[index].setText(str(self.right_knobs[index].value()))
        com.txcv(
            "arms",
            [self.left_knobs[i].value() for i in range(len(self.left_knobs))]
            + [self.right_knobs[i].value() for i in range(len(self.right_knobs))],
        )
        CURRENT_ARM_POS = [
            self.left_knobs[i].value() for i in range(len(self.left_knobs))
        ] + [self.right_knobs[i].value() for i in range(len(self.right_knobs))]

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
                modal_bar.setPixmap(
                    qta.icon("fa5s.exclamation-triangle", color=self.fg_color).pixmap(
                        36
                    )
                )

                modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

                modal_timeout = QTimer()
                modal_timeout.singleShot(1500, close_modal)
        else:
            if self.modal_count < 6:
                modal_bar = KBModalBar(self)
                self.modals.append(modal_bar)
                self.modal_count += 1
                modal_bar.setTitle(strings.SAVE_SUCCESS)
                modal_bar.setDescription("Speech Preset Saved")
                modal_bar.setPixmap(
                    qta.icon("fa5.save", color=self.fg_color).pixmap(36)
                )

                modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

                modal_timeout = QTimer()
                modal_timeout.singleShot(1500, close_modal)

            for i in range(
                len(
                    settings["arm_prog"][
                        extract_digits(self.arm_preset_label.text())[0] - 1
                    ]
                )
            ):
                if i < settings["arm_dof"]:
                    settings["arm_prog"][
                        extract_digits(self.arm_preset_label.text())[0] - 1
                    ][i] = self.left_knobs[i].value()
                else:
                    settings["arm_prog"][
                        extract_digits(self.arm_preset_label.text())[0] - 1
                    ][i] = self.right_knobs[i - settings["arm_dof"]].value()

            # dump json
            save_settings()

    def pop_com_service_modal(self):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        if self.modal_count < 6:
            modal_bar = KBModalBar(self)
            self.modals.append(modal_bar)
            self.modal_count += 1
            modal_bar.setTitle(strings.COM_REOPEN)
            modal_bar.setDescription(strings.COM_REOPEN_DESC)
            modal_bar.setPixmap(qta.icon("fa5s.cogs", color=self.fg_color).pixmap(36))

            modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

            modal_timeout = QTimer()
            modal_timeout.singleShot(1500, close_modal)

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

            modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

            modal_timeout = QTimer()
            modal_timeout.singleShot(1500, close_modal)

    def set_speed(self, speed):
        self.speed = speed
        settings["speed"] = speed
        save_settings()

    def head_changed_action(self):
        com.txcv(
            "head_x", map_range(self.head_stick.getXY()[0], 0, JOYSTICK_SIZE, 0, 60)
        )
        com.txcv(
            "head_y", map_range(self.head_stick.getXY()[1], 0, JOYSTICK_SIZE, 0, 60)
        )

    def shutdown_action(self):
        self.close()
        app.quit()

    def eye_set_state(self, state: int):
        com.txcv("eye.set_state", state)
        self.eye_config_stack.setCurrentIndex(state - 3)

    @staticmethod
    def eye_config_simple_bg_selected(color):
        com.txstr(f"eye.set_skin_option=simple:bg_color:{color}")

    @staticmethod
    def eye_config_simple_pupil_selected(color):
        com.txstr(f"eye.set_skin_option=simple:pupil_color:{color}")

    @staticmethod
    def eye_config_simple_iris_selected(color):
        com.txstr(f"eye.set_skin_option=simple:iris_color:{color}")

    def eye_config_pupil_size_slider_value_changed(self, value):
        com.txstr(
            f"eye.set_skin_option=simple:pupil_size:{self.eye_simple_iris_size_slider.value() * value // 100}"
        )

    def eye_config_iris_size_slider_value_changed(self, value):
        com.txstr(f"eye.set_skin_option=simple:iris_size:{value}")
        com.txstr(
            f"eye.set_skin_option=simple:pupil_size:{value * self.eye_simple_pupil_size_slider.value() // 100}"
        )

    @staticmethod
    def eye_config_speed_slider_value_changed(value):
        com.txcv("eye.set_speed", value)

    @staticmethod
    def eye_config_bright_slider_value_changed(value):
        com.txcv("eye.set_backlight", value)

    @staticmethod
    def eye_config_metal_tint_changed(value):
        com.txstr(f"eye.set_skin_option=metal:tint:{value}")

    @staticmethod
    def eye_set_neon_style(value):
        com.txstr(f"eye.set_skin_option=neon:style:{value}")

    def eye_neon_left_changed(self, value):
        self.eye_neon_left_color = value
        com.txstr(f"eye.set_skin_option=neon:fg_color_start:{self.eye_neon_left_color}")
        com.txstr(f"eye.set_skin_option=neon:fg_color_end:{self.eye_neon_right_color}")

    def eye_neon_right_changed(self, value):
        self.eye_neon_right_color = value
        com.txstr(f"eye.set_skin_option=neon:fg_color_start:{self.eye_neon_left_color}")
        com.txstr(f"eye.set_skin_option=neon:fg_color_end:{self.eye_neon_right_color}")

    def eye_neon_swap_colors(self):
        self.eye_neon_left_color, self.eye_neon_right_color = (
            self.eye_neon_right_color,
            self.eye_neon_left_color,
        )
        com.txstr(f"eye.set_skin_option=neon:fg_color_start:{self.eye_neon_left_color}")
        com.txstr(f"eye.set_skin_option=neon:fg_color_end:{self.eye_neon_right_color}")

    def eye_neon_copy_ltr(self):
        self.eye_neon_right_color = self.eye_neon_left_color
        com.txstr(f"eye.set_skin_option=neon:fg_color_start:{self.eye_neon_left_color}")
        com.txstr(f"eye.set_skin_option=neon:fg_color_end:{self.eye_neon_right_color}")

    def eye_neon_copy_rtl(self):
        self.eye_neon_left_color = self.eye_neon_right_color
        com.txstr(f"eye.set_skin_option=neon:fg_color_start:{self.eye_neon_left_color}")
        com.txstr(f"eye.set_skin_option=neon:fg_color_end:{self.eye_neon_right_color}")

    @staticmethod
    def eye_config_neon_bg_selected(value):
        com.txstr(f"eye.set_skin_option=neon:bg_color:{value}")

    def eye_pos_changed(self):
        pos = self.eye_joystick.getXY()
        pos = (map_range(pos[0], -80, 80, 0, 240), map_range(pos[1], -80, 80, 0, 240))
        com.txcv("eye.set_position", ",".join(str(x) for x in pos))

    def eye_config_motion_selected(self, motion):
        com.txcv("eye.set_motion", motion)

        if motion == 3:
            self.eye_joystick_group.setEnabled(True)
            self.eye_joystick.setColor(self.fg_color)
        else:
            self.eye_joystick_group.setEnabled(False)
            self.eye_joystick.setColor(QColor("#9E9E9E"))

    def motor_action(self):
        if not ANALOG_STICK:
            x, y = self.motor_stick.getXY()
            y = -y

            direction = direction_lookup(x, 0, y, 0)[0]

            distance = round(math.dist((0, 0), (x, y)))

            if direction == "N":
                com.txmot(
                    (
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            settings["max_us"],
                        ),
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            settings["max_us"],
                        ),
                    )
                )
            elif direction == "S":
                com.txmot(
                    (
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            2000 - (settings["max_us"] - 1000),
                        ),
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            2000 - (settings["max_us"] - 1000),
                        ),
                    )
                )
            elif direction == "W":
                com.txmot(
                    (
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            2000 - (settings["max_us"] - 1000),
                        ),
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            settings["max_us"],
                        ),
                    )
                )
            elif direction == "E":
                com.txmot(
                    (
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            settings["max_us"],
                        ),
                        map_range(
                            distance,
                            0,
                            self.motor_stick.getMaxDistance(),
                            1500,
                            2000 - (settings["max_us"] - 1000),
                        ),
                    )
                )
        elif ANALOG_STICK:
            # EXPERIMENTAL ANALOG CONTROL

            # get values
            x, y = self.motor_stick.getXY()
            if x == 0 and y == 0:
                com.txmot((1500, 1500))
                return

            x, y = (
                x / self.motor_stick.getMaxDistance(),
                y / self.motor_stick.getMaxDistance(),
            )

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

    def show_enabled_fail(self, ena: int):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        modal_bar = KBModalBar(self)
        self.modals.append(modal_bar)
        self.modal_count += 1
        modal_bar.setTitle("Enable action failed")
        modal_bar.setDescription(
            f"Attempt to set enabled state to {int(ena)}"
        )
        modal_bar.setPixmap(
            qta.icon("fa5s.power-off", color="#F44336").pixmap(36)
        )

        modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

        modal_timeout = QTimer()
        modal_timeout.singleShot(4000, close_modal)


    def set_enabled(self, ena: bool):
        global enabled

        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        if not enabled == ena:
            if self.modal_count < 6:
                modal_bar = KBModalBar(self)
                self.modals.append(modal_bar)
                self.modal_count += 1
                modal_bar.setTitle(f"Robot {'Enabled' if ena else 'Disabled'}")
                modal_bar.setDescription(
                    f"Kevinbot has been {'Enabled' if ena else 'Disabled'}"
                )
                modal_bar.setPixmap(
                    qta.icon("fa5s.power-off", color=self.fg_color).pixmap(36)
                )

                modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

                modal_timeout = QTimer()
                modal_timeout.singleShot(1500, close_modal)
        enabled = ena

        if window:
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
            self.camera_leds_group.setEnabled(enabled)

            if settings["window_properties"]["ui_style"] == "modern":
                self.bottom_base_led_button.setEnabled(enabled)
                self.bottom_body_led_button.setEnabled(enabled)
                self.bottom_head_led_button.setEnabled(enabled)
                self.bottom_eye_button.setEnabled(enabled)


    @staticmethod
    def request_enabled(ena: bool):
        com.txcv("request.enabled", str(ena))

    def e_stop_action(self):
        """EMERGENCY STOP CODE"""

        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        com.tx_e_stop()

        # show modal
        if self.modal_count < 6:
            modal_bar = KBModalBar(self)
            self.modals.append(modal_bar)
            self.modal_count += 1
            modal_bar.setTitle(strings.ESTOP_TITLE)
            modal_bar.setDescription(strings.ESTOP)
            modal_bar.setPixmap(
                qta.icon("fa5s.exclamation-circle", color="#E53935").pixmap(36)
            )

            modal_bar.popToast(pop_speed=80, pos_index=self.modal_count)

            modal_timeout = QTimer()
            modal_timeout.singleShot(2000, close_modal)

    def refresh_mesh(self):
        com.txstr("core.remotes.get_full")

    def add_mesh_devices(self, items):
        items = items.split(",")
        self.connected_devices.setText(strings.CONNECTED_DEVICES.format(len(items)))

        for i in reversed(range(self.devices_layout.count())):
            self.devices_layout.itemAt(i).widget().setParent(None)

        objects = []
        for count, item in enumerate(items):
            objects.append(KBDevice())
            if item.split("|")[2] == "kevinbot.remote":
                objects[count].setDeviceName(strings.DEVICE_REMOTE)
                objects[count].setIcon(KBDevice.IconType.Remote)
            elif item.split("|")[2] == "kevinbot.kevinbot":
                objects[count].setDeviceName(strings.DEVICE_ROBOT)
                objects[count].setIcon(KBDevice.IconType.Robot)
            objects[count].setDeviceNickName(
                strings.DEVICE_NICKNAME.format(item.split("|")[0])
            )
            if item.split("|")[0] == remote_name:
                objects[count].ping.clicked.connect(partial(lambda: self.ping("self")))
            else:
                objects[count].ping.clicked.connect(
                    partial(self.send_ping, item.split("|")[0])
                )
            self.devices_layout.addWidget(objects[count])

    def ping(self, transmitter):
        def close_modal():
            # close this modal, move other modals
            modal_bar.closeToast()
            self.modal_count -= 1

            self.modals.remove(modal_bar)

            for modal in self.modals:
                modal.changeIndex(modal.getIndex() - 1, moveSpeed=600)

        # show modal
        if self.modal_count < 6:
            modal_bar = KBModalBar(self)
            self.modals.append(modal_bar)
            self.modal_count += 1
            modal_bar.setTitle(strings.PING_TITLE)
            modal_bar.setDescription(strings.PING_DESC.format(transmitter))
            modal_bar.setPixmap(
                qta.icon("fa5s.exclamation-circle", color="#29B6F6").pixmap(36)
            )

            modal_bar.popToast(pop_speed=500, pos_index=self.modal_count)

            modal_timeout = QTimer()
            modal_timeout.singleShot(3000, close_modal)

    def send_ping(self, source):
        com.txcv("core.ping", f"{source},{remote_name}")


def init_robot():
    com.txcv("arms", CURRENT_ARM_POS, delay=0.02)
    com.txcv("core.speech-engine", "espeak", delay=0.02)
    com.txcv("head_effect", "color1", delay=0.02)
    com.txcv("body_effect", "color1", delay=0.02)
    com.txcv("base_effect", "color1", delay=0.02)
    com.txcv("cam_brightness", 0, delay=0.02)


if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            import ctypes

            # show icon in the taskbar
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Kevinbot3 Remote"
            )

        if not os.path.exists(os.path.join(os.curdir, "mpu_graph_images")):
            os.mkdir(os.path.join(os.curdir, "mpu_graph_images"))

        app = QApplication(sys.argv)
        app.setApplicationName("Kevinbot Remote")
        app.setApplicationVersion(__version__)

        # Font
        QFontDatabase.addApplicationFont(
            os.path.join(os.curdir, "res/fonts/Roboto-Regular.ttf")
        )
        QFontDatabase.addApplicationFont(
            os.path.join(os.curdir, "res/fonts/Roboto-Medium.ttf")
        )
        QFontDatabase.addApplicationFont(
            os.path.join(os.curdir, "res/fonts/Roboto-Bold.ttf")
        )
        QFontDatabase.addApplicationFont(
            os.path.join(os.curdir, "res/fonts/Lato-Regular.ttf")
        )
        QFontDatabase.addApplicationFont(
            os.path.join(os.curdir, "res/fonts/Lato-Bold.ttf")
        )

        window = RemoteUI()
        ex = app.exec()
    finally:
        try:
            remote_version = open("version.txt", "r").read()
        except FileNotFoundError:
            remote_version = "UNKNOWN"
        com.txcv(
            "core.remotes.remove", f"{remote_name}|{remote_version}|kevinbot.remote"
        )
