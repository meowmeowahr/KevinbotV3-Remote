import re


def capitalize(string):
    return string[0].upper() + string[1:]


def extract_digits(string):
    return [int(s) for s in re.findall(r'\d+', string)]


def map_range(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


def convert_c_to_f(c):
    return (c * 9 / 5) + 32


def rstr(string, decimals=1):
    return str(round(float(string), decimals))


def limit(value, min_value, max_value):
    return max(min(value, max_value), min_value)

def load_theme(widget, themename="classic"):
    if themename == "classic":
        with open("theme.qss", 'r') as file:
            widget.setStyleSheet(file.read())
    elif themename == "qdarktheme":
        import qdarktheme
        widget.setStyleSheet(qdarktheme.load_stylesheet())
