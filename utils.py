import os
import re
import math
import statistics
import threading
from shutil import which
# noinspection PyPackageRequirements
from qtpy.QtCore import QFile, QTextStream
from qtpy.QtWidgets import QWidget


def capitalize(string):
    return string[0].upper() + string[1:]


def extract_digits(string):
    return [int(s) for s in re.findall(r'\d+', string)]


def map_range(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


def map_range_limit(x, in_min, in_max, out_min, out_max):
    if x > in_max:
        x = in_max
    elif x < in_min:
        x = in_min

    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


def convert_c_to_f(c):
    return (c * 9 / 5) + 32


def rstr(string, decimals=1):
    return str(round(float(string), decimals))


def limit(value, min_value, max_value):
    return max(min(value, max_value), min_value)


def detect_dark(rgb):
    average = statistics.mean(rgb)
    if average > 127:
        return False
    else:
        return True


def load_theme(widget: QWidget, theme="classic", theme_style="default"):
    if theme == "classic":
        with open("theme.qss", 'r') as file:
            widget.setStyleSheet(file.read())
    elif theme == "qdarktheme":
        import qdarktheme
        if theme_style.lower() == "default":
            widget.setStyleSheet(qdarktheme.load_stylesheet())
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #8ab4f7;"
                                 "color: #202124;"
                                 "}")
        elif theme_style.lower() == "purple":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#d970d5"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #d970d5;"
                                 "color: #202124;"
                                 "}")
        elif theme_style.lower() == "green":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#56bb74"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #56bb74;"
                                 "color: #202124;"
                                 "}")
        elif theme_style.lower() == "orange":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#ffa348"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #ffa348;"
                                 "color: #202124;"
                                 "}")
        elif theme_style.lower() == "teal":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#56bbca"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #56bbca;"
                                 "color: #202124;"
                                 "}")
        elif theme_style.lower() == "red":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#e65c4d"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #e65c4d;"
                                 "color: #202124;"
                                 "}")
        elif theme_style.lower() == "white":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#ffffff"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #ffffff;"
                                 "color: #202124;"
                                 "}")
        else:
            widget.setStyleSheet(qdarktheme.load_stylesheet())
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #8ab4f7;"
                                 "color: #202124;"
                                 "}")
    elif theme == "qdarktheme_kbot":
        import qdarktheme
        widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"background": "#111114", "primary": "#afbfcf",
                                                                       "primary>button.activeBackground": "#333348",
                                                                       "primary>button.hoverBackground": "222238"}))
        # add extra stylesheets
        widget.setStyleSheet(widget.styleSheet() +
                             "QDial{"
                             "background-color: #263f66;"
                             "color: #afbfcf;"
                             "}"
                             "#Enable_Button{"
                             "background-color: #e65c4d;"
                             "color: #080808;"
                             "font-size: 18px;"
                             "font-family: Roboto;"
                             "font-weight: bold;"
                             "}"
                             "#Disable_Button{"
                             "background-color: #56bb74;"
                             "color: #080808;"
                             "font-size: 18px;"
                             "font-family: Roboto;"
                             "font-weight: bold;"
                             "}"
                             "#E_Stop{"
                             "background-color: #fbc02d;"
                             "color: #080808;"
                             "font-size: 24px;"
                             "font-family: Roboto;"
                             "font-weight: bold;"
                             "}"
                             )
    elif theme == "highcontrast":
        import qdarktheme
        if theme_style.lower() == "default":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#ffffff",
                                                                           "background": "#000000",
                                                                           "border": "#ffffff",
                                                                           "input.background": "#000000",
                                                                           "foreground": "#efefef",
                                                                           "foreground>icon": "#ffffff",
                                                                           "scrollbarSlider.background": "#757575"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #ffffff;"
                                 "color: #000000;"
                                 "}")
        elif theme_style.lower() == "light":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#000000",
                                                                           "background": "#ffffff",
                                                                           "border": "#000000",
                                                                           "input.background": "#ffffff",
                                                                           "foreground": "#010101",
                                                                           "foreground>icon": "#000000",
                                                                           "scrollbarSlider.background": "#8a8a8a"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #ffffff;"
                                 "}")
    elif theme == "qdarktheme_light":
        import qdarktheme
        if theme_style.lower() == "default":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light"))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #4990ed;"
                                 "}")
        elif theme_style.lower() == "purple":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light", custom_colors={"primary": "#a63da3"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #a63da3;"
                                 "}")
        elif theme_style.lower() == "green":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light", custom_colors={"primary": "#349952"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #349952;"
                                 "}")
        elif theme_style.lower() == "orange":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light", custom_colors={"primary": "#dd8126"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #dd8126;"
                                 "}")
        elif theme_style.lower() == "teal":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light", custom_colors={"primary": "#3499a8"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #3499a8;"
                                 "}")
        elif theme_style.lower() == "red":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light", custom_colors={"primary": "#c43a2b"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #c43a2b;"
                                 "color: #f8f9fa;"
                                 "}")
        elif theme_style.lower() == "black":
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light", custom_colors={"primary": "#000000"}))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #f8f9fa;"
                                 "}")
        else:
            widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light"))
            # add extra stylesheets
            widget.setStyleSheet(widget.styleSheet() +
                                 "QDial{"
                                 "background-color: #000000;"
                                 "color: #4990ed;"
                                 "}")
    elif theme == "breeze_dark":
        # noinspection PyUnresolvedReferences
        import breeze_resources
        file = QFile(":/dark/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        widget.setStyleSheet(stream.readAll())
        # add extra stylesheets
        widget.setStyleSheet(widget.styleSheet() +
                             "QDial{"
                             "background-color: #58d3ff;"
                             "color: #1d2023;"
                             "}")
    elif theme == "breeze_light":
        # noinspection PyUnresolvedReferences
        import breeze_resources
        file = QFile(":/light/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        widget.setStyleSheet(stream.readAll())
        # add extra stylesheets
        widget.setStyleSheet(widget.styleSheet() +
                             "QDial{"
                             "background-color: #272b2f;"
                             "color: #eff0f1;"
                             "}")
    else:
        widget.setStyleSheet("")


def direction_lookup(destination_x, origin_x, destination_y, origin_y):
    delta_x = destination_x - origin_x
    delta_y = destination_y - origin_y

    degrees_temp = math.atan2(delta_x, delta_y)/math.pi*180
    
    if degrees_temp < 0:
        degrees_final = 360 + degrees_temp
    else:
        degrees_final = degrees_temp
    compass_brackets = ["N", "E", "S", "W", "N"]
    compass_lookup = round(degrees_final / 90)
    return compass_brackets[compass_lookup], degrees_final


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is not None


def is_pi():
    try:
        if "Raspberry" in open("/sys/firmware/devicetree/base/model", "r").readline():
            return True
        else:
            return False
    except IOError:
        return False


def is_using_venv():
    """Check if a virtual environment is being used"""
    return os.path.isdir(os.path.join(os.path.curdir, "venv"))


def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


class AppLauncher:
    def __init__(self):
        super().__init__()
        self.__done = None
        self.__thread = None
        self.__script = None

    def launch(self):
        self.__thread = threading.Thread(target=self.__launch_thread)
        self.__thread.start()

    def set_script(self, script, launch=False):
        self.__script = script

        if launch:
            self.launch()

    def set_finnished(self, func):
        self.__done = func

    def __launch_thread(self):
        os.system(self.__script)
        if self.__done:
            self.__done()
