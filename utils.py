import re
import math
import statistics
from shutil import which
# noinspection PyPackageRequirements
from PyQt5.QtCore import QFile, QTextStream


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


def load_theme(widget, theme="classic", theme_style="default"):
    if theme == "classic":
        with open("theme.qss", 'r') as file:
            widget.setStyleSheet(file.read())
    elif theme == "qdarktheme":
        import qdarktheme
        if theme_style.lower() == "default":
            widget.setStyleSheet(qdarktheme.load_stylesheet())
        elif theme_style.lower() == "purple":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#d970d5"}))
        elif theme_style.lower() == "green":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#56bba4"}))
        elif theme_style.lower() == "orange":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#ffa348"}))
        elif theme_style.lower() == "teal":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#56bbca"}))
        elif theme_style.lower() == "red":
            widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#e65c4d"}))
        else:
            widget.setStyleSheet(qdarktheme.load_stylesheet())
    elif theme == "highcontrast":
        import qdarktheme
        widget.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#ffffff", 
                                                                       "background": "#000000",
                                                                       "border": "#ffffff",
                                                                       "input.background": "#000000",
                                                                       "foreground": "#efefef",
                                                                       "foreground>icon": "#ffffff",
                                                                       "scrollbarSlider.background": "#757575"}))

    elif theme == "qdarktheme_light":
        import qdarktheme
        widget.setStyleSheet(qdarktheme.load_stylesheet(theme="light"))
    elif theme == "breeze_dark":
        # noinspection PyUnresolvedReferences
        import breeze_resources
        file = QFile(":/dark/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        widget.setStyleSheet(stream.readAll())
    elif theme == "breeze_light":
        # noinspection PyUnresolvedReferences
        import breeze_resources
        file = QFile(":/light/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        widget.setStyleSheet(stream.readAll())


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
