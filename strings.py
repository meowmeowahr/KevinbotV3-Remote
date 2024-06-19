# Strings used in the remote for Kevinbot v3
from typing import Final

WIN_TITLE: Final[str] = "Kevinbot3 Remote"

# -- Remote UI Arms -- #

ARM_PRESET_G: Final[str] = "Arm Presets"
ARM_PRESETS: Final[list[str]] = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
ARM_SET_PRESET: Final[str] = "Setup"

ARM_PRESET_EDIT_G: Final[str] = "Edit Presets"
PRESET_PICK: Final[str] = "Pick Preset"
ARM_PRESET_EDIT: Final[str] = "Editor"
ARM_PRESET_EDIT_L: Final[str] = "Left"
ARM_PRESET_EDIT_R: Final[str] = "Right"
CURRENT_ARM_PRESET: Final[str] = "Current Preset"

# -- Remote UI Leds -- #

LED_PRESET_G: Final[str] = "Appearance"
LED_HEAD: Final[str] = "Head LEDs"
LED_BODY: Final[str] = "Body LEDs"
LED_BASE: Final[str] = "Base LEDs"
LED_CAMERA: Final[str] = "Camera LEDs"
LED_EYE_CONFIG: Final[str] = "Eye Config"

# -- Remote UI Main -- #

MAIN_G: Final[str] = "Main"

# -- Remote UI Speech -- #

SPEECH_INPUT_H: Final[str] = "Speech Input"
SPEECH_BUTTON: Final[str] = "Speak"
SPEECH_SAVE: Final[str] = "Save"
SPEECH_ESPEAK: Final[str] = "eSpeak"
SPEECH_FESTIVAL: Final[str] = "Festival"

# -- Remote UI Camera -- #

CAMERA_G: Final[str] = "Camera"
CAMERA_LEDS_G: Final[str] = "Camera LED Brightness"

# -- Remote UI Led Effects -- #

HEAD_COLOR_G: Final[str] = "Head Color"
HEAD_EFFECTS_G: Final[str] = "Head Effects"
HEAD_SPEED_G: Final[str] = "Head Speed"

BODY_COLOR_G: Final[str] = "Body Color"
BODY_EFFECTS_G: Final[str] = "Body Effects"
BODY_SPEED_G: Final[str] = "Body Speed"

BASE_COLOR_G: Final[str] = "Base Color"
BASE_EFFECTS_G: Final[str] = "Base Effects"
BASE_SPEED_G: Final[str] = "Base Speed"

# -- Remote UI Eyes -- #

EYE_CONFIG_B_G: Final[str] = "Background Color"
EYE_CONFIG_P_G: Final[str] = "Pupil Color"
EYE_CONFIG_I_G: Final[str] = "Iris Color"
EYE_CONFIG_PS_G: Final[str] = "Pupil Size (%)"
EYE_CONFIG_IS_G: Final[str] = "Iris Size"
EYE_CONFIG_SP_G: Final[str] = "Motion Speed"
EYE_CONFIG_BR_G: Final[str] = "Backlight"

EYE_CONFIG_METAL_IS_T_G: Final[str] = "Iris Tint"

EYE_CONFIG_NEON_PALETTES: Final[str] = "Foreground Colors"

EYE_JOYSTICK: Final[str] = "Manual Position"

SAVE: Final[str] = "Save"
SAVE_SUCCESS: Final[str] = "Saved Successfully"
SAVE_ERROR: Final[str] = "Save Error"
SAVE_WARN_1: Final[str] = "Please Select a Preset before saving"

COM_REOPEN: Final[str] = "Kevinbot Services"
COM_REOPEN_DESC: Final[str] = "Kevinbot Com Service has Started"

ESTOP_TITLE: Final[str] = "E-Stop"
ESTOP: Final[str] = "Kevinbot is shutting down"

SHUTDOWN_MESSAGE: Final[str] = "Are you sure you want to shutdown the remote?"
SHUTDOWN_TITLE: Final[str] = "Shutdown"

ROBOT_VERSION: Final[str] = "Robot Version: "
REMOTE_VERSION: Final[str] = "Remote Version: "
BATT_VOLT1: Final[str] = "Battery #1 Voltage: {}"
BATT_VOLT2: Final[str] = "Battery #2 Voltage: {}"
BATT_LOW: Final[str] = "One or More Batteries are Low"

# -- Remote UI Volt Warning -- #

MODAL_CLOSE: Final[str] = "Ignore"
MODAL_SHUTDOWN: Final[str] = "Shutdown Robot"

# -- Remote UI Sensors -- #

SENSORS_G: Final[str] = "Sensors"
OUTSIDE_TEMP: Final[str] = "Outside Temp: {}"
OUTSIDE_HUMI: Final[str] = "Outside Humidity: {}%"
OUTSIDE_PRES: Final[str] = "Outside Pressure: {}hPa"

LEFT_TEMP: Final[str] = "Left Motor Temp: {}"
RIGHT_TEMP: Final[str] = "Right Motor Temp: {}"
INSIDE_TEMP: Final[str] = "Inside Temp: {}"
MOT_TEMP_HIGH: Final[str] = "One or More Motors are Overheating"

X_LENGTH: Final[str] = "X-Axis Length"

# -- Remote UI Mesh -- #

CONNECTED_DEVICES: Final[str] = "Connected Devices: {0}"

DEVICE_REMOTE: Final[str] = "Type\nKevinbot Remote"
DEVICE_ROBOT: Final[str] = "Type\nKevinbot v3"

DEVICE_NICKNAME: Final[str] = "Unique ID\n{0}"

PING_TITLE: Final[str] = "Ping!"
PING_DESC: Final[str] = "Ping from {0}"

# -- Remote UI Debug -- #

DEBUG_TITLE: Final[str] = "Debug Data"

CORE_UPTIME: Final[str] = "Core Uptime: {0} ({1})"
SYS_UPTIME: Final[str] = "System Uptime: {0} ({1})"

# -- Settings -- #

SETTINGS_SCREEN_BR_G: Final[str] = "Screen Brightness"
SETTINGS_RUN_THEME_G: Final[str] = "Runner Theme"
SETTINGS_APP_THEME_G: Final[str] = "App Theme"
SETTINGS_ANIM_G: Final[str] = "Animations"
SETTINGS_XSC_G: Final[str] = "Screensaver"
SETTINGS_SPEED_G: Final[str] = "Robot Speed"
SETTINGS_CAM_URL_G: Final[str] = "Camera URL"
SETTINGS_HOMEPAGE_G: Final[str] = "Homepage"
SETTINGS_REMOTE_G: Final[str] = "Remote"

SETTINGS_ADV_G: Final[str] = "Advanced Settings"
SETTINGS_ADV_WARNING: Final[str] = (
    "WARNING: Changing some of these settings may damage your remote or robot."
)

SETTINGS_DISPLAY_OPT: Final[str] = "Display and Theme Settings"
SETTINGS_ROBOT_OPT: Final[str] = "Robot Settings"
SETTINGS_REMOTE_OPT: Final[str] = "Remote Settings"
SETTINGS_BROWSER_OPT: Final[str] = "Browser Settings"
SETTINGS_ADVANCED_OPT: Final[str] = "Advanced Settings"

SETTINGS_APP_THEMES: Final[str] = "App Theme Gallery"
SETTINGS_RUNNER_THEMES: Final[str] = "Runner Theme Gallery"

SETTINGS_XSC_PREVIEW_B: Final[str] = "Preview Screensaver"
SETTINGS_VALIDATE_URL_B: Final[str] = "Validate URL"
SETTINGS_CUSTOMIZER_B: Final[str] = "Customizer"

SETTINGS_XSC_TIME_S: Final[str] = "Screen Timeout: "
SETTINGS_XSC_TIME_SUF: Final[str] = " minutes"

SETTINGS_MAX_US_L: Final[str] = "Max µS:"
SETTINGS_NICKNAME_L: Final[str] = "Unique Identifier:"
SETTINGS_NICKNAME_DESC: Final[str] = (
    "The Unique ID is the identifier for this remote.\nIt must be unique and not used on any other remote.\nIt must also not contain special characters."
)
SETTINGS_STICK_SIZE_L: Final[str] = "Joystick Size:"
SETTINGS_STICK_MODE_L: Final[str] = "Joystick Mode:"
SETTINGS_UI_MODE_L: Final[str] = "UI Style"

SETTINGS_TICK_FLAT: Final[str] = "Flat"
SETTINGS_TICK_ENABLE: Final[str] = "Enable"

SETTINGS_RAD_SMALL: Final[str] = "Small"
SETTINGS_RAD_LARGE: Final[str] = "Large"
SETTINGS_RAD_X_LARGE: Final[str] = "X-Large"
SETTINGS_RAD_DIGITAL: Final[str] = "Digital"
SETTINGS_RAD_ANALOG: Final[str] = "Analog"
SETTINGS_RAD_CLASSIC: Final[str] = "Classic"
SETTINGS_RAD_MODERN: Final[str] = "Modern"

SETTINGS_MSG_VALID_URL: Final[str] = "URL is Valid"
SETTINGS_MSG_INVALID_URL: Final[str] = "URL is Invalid"
SETTINGS_WIN_URL_VALIDATOR: Final[str] = "URL Validator"

SETTINGS_ANIM_SPEED: Final[str] = "Animation Speed"

# -- ImView -- #

IMVIEW_GRAPH_A: Final[str] = "Gyro Graph Images"
IMVIEW_TIME: Final[str] = "Timestamp: {0}"

# -- Misc -- #

FILE_M: Final[str] = "File"
EXIT_A: Final[str] = "Exit"
CLEAR: Final[str] = "Clear"
PING: Final[str] = "Ping"
KICK: Final[str] = "Kick"
REFRESH: Final[str] = "Refresh"
UNKNOWN: Final[str] = "Unknown"
DEV_OFF: Final[str] = "Dev Options Disabled"
SKINS: Final[str] = "Skins"
PROPERTIES: Final[str] = "Properties"
