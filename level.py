# A level widget for PyQt5
# A circle with a line in the middle
# You can change the angle of the line using "setAngle()"

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import math


class LevelWidget(QWidget):
    # noinspection PyArgumentList
    def __init__(self, parent=None):
        super(LevelWidget, self).__init__(parent)
        self.setMinimumSize(160, 160)

        self.angle = 0
        self._lineColor = Qt.black
        self._robotColor = Qt.blue
        self._lineWidth = 16
        self._levelText = "Angle: {}"

        if parent is not None:
            self._backgroundColor = Qt.GlobalColor.transparent
        else:
            self._backgroundColor = Qt.white

    def setAngle(self, angle):
        self.angle = angle
        self.update()

    def setLineColor(self, color):
        self._lineColor = color
        self.update()

    def setRobotColor(self, color):
        self._robotColor = color
        self.update()

    def setLineWidth(self, width):
        """
        Set the line width of the level widget.

        :type width: int, float
        """
        self._lineWidth = width
        self.update()

    def setBackgroundColor(self, color):
        self._backgroundColor = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self._lineColor, self._lineWidth))

        painter.drawLine(QPointF(self.height() / 2, self.height() / 2),
                         QPointF(self.height() / 2 + math.cos(math.radians(self.angle)) * self.height() / 2 - 12,
                                 self.height() / 2 + math.sin(math.radians(self.angle)) * self.height() / 2))

        painter.drawLine(QPointF(self.height() / 2, self.height() / 2),
                         QPointF(self.height() / 2 - math.cos(math.radians(self.angle)) * self.height() / 2 + 12,
                                 self.height() / 2 - math.sin(math.radians(self.angle)) * self.height() / 2))

        # line 20px out  of the angle line
        painter.setPen(QPen(self._robotColor, self._lineWidth))
        painter.drawLine(QPointF(self.height() / 2, self.height() / 2),
                         QPointF(self.height() / 2 + math.cos(math.radians(self.angle - 90)) * 20,
                                 self.height() / 2 + math.sin(math.radians(self.angle - 90)) * 20))

        painter.setPen(QPen(self._backgroundColor, 30))
        painter.drawEllipse(QRect(0, 0, self.height(), self.height()))

        painter.setPen(QPen(self._lineColor, self._lineWidth / 2.5))
        painter.drawEllipse(QRect(4, 4, self.height() - 8, self.height() - 8))
        painter.setPen(QPen(Qt.black, 16))


class Level(QWidget):
    # noinspection PyArgumentList
    def __init__(self, parent=None):
        super(Level, self).__init__(parent)

        self.levelText = "Angle: {}°"

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self._level = LevelWidget(self)
        self._layout.addWidget(self._level)

        self.label = QLabel()
        self.label.setFixedHeight(32)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(self.levelText.format(self._level.angle))
        self._layout.addWidget(self.label)

    def setAngle(self, angle):
        self._level.setAngle(angle)
        self.label.setText(self.levelText.format(angle))

    def setLineColor(self, color):
        self._level.setLineColor(color)

    def setRobotColor(self, color):
        self._level.setRobotColor(color)

    def setLineWidth(self, width):
        self._level.setLineWidth(width)

    def setBackgroundColor(self, color):
        self._level.setBackgroundColor(color)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # noinspection PyArgumentList
    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)
    level = Level()
    # noinspection PyArgumentList
    layout.addWidget(level)
    spinbox = QSpinBox()
    spinbox.setRange(0, 360)
    spinbox.setValue(0)
    # noinspection PyUnresolvedReferences
    spinbox.valueChanged.connect(level.setAngle)
    # noinspection PyArgumentList
    layout.addWidget(spinbox)
    window.show()
    sys.exit(app.exec_())
