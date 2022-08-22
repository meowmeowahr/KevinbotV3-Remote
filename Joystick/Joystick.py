from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys
from enum import Enum


class Direction(Enum):
    Left = 0
    Right = 1
    Up = 2
    Down = 3


class Joystick(QWidget):

    posChanged = pyqtSignal()

    def __init__(self, parent=None, color=Qt.GlobalColor.black, sticky=True, maxDistance=60):
        super(Joystick, self).__init__(parent)
        self.color = color
        self.sticky = sticky
        self.setMinimumSize(100, 100)
        self.movingOffset = QPointF(0, 0)
        self.grabCenter = False
        self.__maxDistance = maxDistance

        self.__changedEvent = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bounds = QRectF(-self.__maxDistance, -self.__maxDistance, self.__maxDistance * 2, self.__maxDistance * 2).translated(self._center())
        painter.setPen(QPen(self.color, 4))
        painter.drawEllipse(bounds)
        painter.setBrush(self.color)
        painter.drawEllipse(self._centerEllipse())

    def _centerEllipse(self):
        if self.grabCenter:
            return QRectF(-20, -20, 40, 40).translated(self.movingOffset)
        return QRectF(-20, -20, 40, 40).translated(self._center())

    def _center(self):
        return QPointF(self.width()/2, self.height()/2)


    def _boundJoystick(self, point):
        limitLine = QLineF(self._center(), point)
        if (limitLine.length() > self.__maxDistance):
            limitLine.setLength(self.__maxDistance)
        return limitLine.p2()

    def joystickDirection(self):
        normVector = QLineF(self._center(), self.movingOffset)
        return (round(normVector.dx()), round(normVector.dy()))


    def mousePressEvent(self, ev):
        self.grabCenter = self._centerEllipse().contains(ev.pos())
        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, event):
        if self.sticky is False:
            self.movingOffset = QPointF(10, 0)
            self.grabCenter = False
        self.posChanged.emit()
        self.update()

    def mouseMoveEvent(self, event):
        if self.grabCenter:
            self.movingOffset = self._boundJoystick(event.pos())
            self.update()
        self.xyChanged()

    def getXY(self):
        return self.joystickDirection()

    def xyChanged(self):
        self.posChanged.emit()


if __name__ == '__main__':
    # Create main application window
    app = QApplication([])
    joystick = Joystick()
    joystick.show()
    sys.exit(app.exec_())