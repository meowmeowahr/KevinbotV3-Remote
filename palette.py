from qtpy import QtCore, QtWidgets
from qtpy.QtCore import Signal as Signal

import haptics

haptics.init(21)

BLACK = "#000000"
RED = "#FF0000"
GREEN = "#00FF00"
BLUE = "#0000FF"
WHITE = "#FFFFFF"
CYAN = "#00FFFF"
MAGENTA = "#FF00FF"
YELLOW = "#FFFF00"
CHARTREUSE = "#7FFF00"
ORANGE = "#FF6000"
AQUAMARINE = "#7FFFD4"
PINK = "#FF5F5F"
TURQUOISE = "#3FE0C0"
INDIGO = "#3F007F"
VIOLET = "#BF7FBF"
MAROON = "#320010"
BROWN = "#0E0600"
CRIMSON = "#DC283C"
PURPLE = "#8C00FF"
DBLUE = "#0022FF"
GRAY = "#555555"

PALETTES = {
    # bokeh paired 12
    "paired12": [
        "#000000",
        "#a6cee3",
        "#1f78b4",
        "#b2df8a",
        "#33a02c",
        "#fb9a99",
        "#e31a1c",
        "#fdbf6f",
        "#ff7f00",
        "#cab2d6",
        "#6a3d9a",
        "#ffff99",
        "#b15928",
        "#ffffff",
    ],
    # d3 category 10
    "category10": [
        "#000000",
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#ffffff",
    ],
    # 17 undertones https://lospec.com/palette-list/17undertones
    "17undertones": [
        "#000000",
        "#141923",
        "#414168",
        "#3a7fa7",
        "#35e3e3",
        "#8fd970",
        "#5ebb49",
        "#458352",
        "#dcd37b",
        "#fffee5",
        "#ffd035",
        "#cc9245",
        "#a15c3e",
        "#a42f3b",
        "#f45b7a",
        "#c24998",
        "#81588d",
        "#bcb0c2",
        "#ffffff",
    ],
    # Kevinbot v3
    "kevinbot": [
        BLACK,
        RED,
        GREEN,
        BLUE,
        WHITE,
        CYAN,
        MAGENTA,
        YELLOW,
        CHARTREUSE,
        ORANGE,
        AQUAMARINE,
        PINK,
        TURQUOISE,
        INDIGO,
        VIOLET,
        MAROON,
        BROWN,
        CRIMSON,
        PURPLE,
        DBLUE,
        GRAY,
    ],
}


class _PaletteButton(haptics.HPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(26, 26))
        self.color = color
        self.setStyleSheet(
            "padding: 0px; background-color: "
            "qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 {0}, stop: 1 {0});".format(
                color
            )
        )


class _PaletteBase(QtWidgets.QWidget):
    selected = Signal(object)

    def _emit_color(self, color):
        self.selected.emit(color)


class _PaletteLinearBase(_PaletteBase):
    # noinspection PyUnresolvedReferences
    def __init__(self, colors, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(colors, str):
            if colors in PALETTES:
                colors = PALETTES[colors]

        palette = self.layoutvh()

        for c in colors:
            b = _PaletteButton(c)
            b.pressed.connect(lambda c=c: self._emit_color(c))
            palette.addWidget(b)

        self.setLayout(palette)


class PaletteHorizontal(_PaletteLinearBase):
    layoutvh = QtWidgets.QHBoxLayout


class PaletteVertical(_PaletteLinearBase):
    layoutvh = QtWidgets.QVBoxLayout


class PaletteGrid(_PaletteBase):

    def __init__(self, colors, n_columns=7, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(colors, str):
            if colors in PALETTES:
                colors = PALETTES[colors]

        palette = QtWidgets.QGridLayout()
        row, col = 0, 0

        for c in colors:
            b = _PaletteButton(c)
            b.pressed.connect(lambda c=c: self._emit_color(c))
            palette.addWidget(b, row, col)
            col += 1
            if col == n_columns:
                col = 0
                row += 1

        self.setLayout(palette)
