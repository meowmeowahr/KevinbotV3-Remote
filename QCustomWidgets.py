import enum
import os.path
import math

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import qtawesome as qta
import pyqtgraph as qtg

import strings

class QPushToolButton(QToolButton):
    def __init__(self, text: str = None):
        super().__init__()
        self.setText(text)


class QSpinner(QWidget):
    # noinspection PyArgumentList
    def __init__(self, text=None, icon_color=Qt.GlobalColor.white):
        super().__init__()

        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)

        if text:
            self.text = QLabel()
            self.text.setText(text)
            self.__layout.addWidget(self.text)

        self.spinbox = QSpinBox()
        self.spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinbox.setFixedHeight(32)
        self.__layout.addWidget(self.spinbox)

        self.add_button = QPushButton()
        self.add_button.setFixedSize(QSize(32, 32))
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.setIcon(qta.icon("fa5s.plus", color=icon_color))
        self.add_button.clicked.connect(self.spinbox.stepUp)
        self.__layout.addWidget(self.add_button)

        self.remove_button = QPushButton()
        self.remove_button.setFixedSize(QSize(32, 32))
        self.remove_button.setIconSize(QSize(24, 24))
        self.remove_button.setIcon(qta.icon("fa5s.minus", color=icon_color))
        self.remove_button.clicked.connect(self.spinbox.stepDown)
        self.__layout.addWidget(self.remove_button)

    def setMaximum(self, value: int):
        self.spinbox.setMaximum(value)

    def setMinimum(self, value: int):
        self.spinbox.setMinimum(value)

    def setValue(self, value: int):
        self.spinbox.setValue(value)

    def setSingleStep(self, value: int):
        self.spinbox.setSingleStep(value)

    def setSuffix(self, suffix: str):
        self.spinbox.setSuffix(suffix)


class QNamedLineEdit(QWidget):
    def __init__(self, text: str = ""):
        super().__init__()

        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)

        self.label = QLabel(text)
        self.__layout.addWidget(self.label)

        self.lineedit = QLineEdit()
        self.__layout.addWidget(self.lineedit)


class KBMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._windowify_action = QAction("Window Mode")
        self._windowify_action.triggered.connect(self._windowModeToggle)
        self._windowify_action.setCheckable(True)

        self._title_action = QAction("-- Dev Menu --")
        self._title_action.setEnabled(False)

        self._close_action = QAction("Quit")
        self._close_action.triggered.connect(self.close)

        self.setWindowIcon(QIcon(os.path.join(os.curdir, "icons/application-default-icon.svg")))
        self.setWindowTitle("Kevinbot Application")

    def _windowModeToggle(self):
        if self._windowify_action.isChecked():
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        self.show()

    def createDevTools(self):
        """ Create a right-click Debug Menu in app """
        self.centralWidget().setContextMenuPolicy(Qt.ActionsContextMenu)
        self.centralWidget().addAction(self._title_action)
        self.centralWidget().addAction(self._windowify_action)
        self.centralWidget().addAction(self._close_action)


class KBModalBar(QFrame):
    def __init__(self, parent, width=400, height=64, gap=16, centerText=True, opacity=90, bgColor=None):
        super(KBModalBar, self).__init__()

        self.gap = gap
        self.parent = parent

        self.setObjectName("Kevinbot3_RemoteUI_ModalBar")
        self.setFrameStyle(QFrame.Box)
        self.setFixedSize(QSize(width, height))
        self.setParent(parent)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(opacity / 100)  # 0 to 1 will cause the fade effect to kick in
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)

        self.move(int(parent.width() / 2 - self.width() / 2),
                  int(parent.height() - height - gap))

        if bgColor:
            self.setStyleSheet(f"background-color: {bgColor}")

        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)

        self.__icon = QLabel()
        self.__layout.addWidget(self.__icon)

        if centerText:
            self.__layout.addStretch()

        self.__labels_layout = QVBoxLayout()
        self.__layout.addLayout(self.__labels_layout)

        self.__name = QLabel()
        self.__labels_layout.addWidget(self.__name)

        self.__description = QLabel()
        self.__labels_layout.addWidget(self.__description)

        self.__layout.addStretch()

        self.hide()

    def setTitle(self, text):
        self.__name.setText(text)

    def setDescription(self, text):
        self.__description.setText(text)

    def setPixmap(self, pixmap):
        self.__icon.setPixmap(pixmap)

    def closeToast(self, closeSpeed = 750):
        self.__anim = QPropertyAnimation(self, b"pos")
        self.__anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.__anim.setEndValue(QPoint(int(self.parent.width() / 2 - self.width() / 2),
                                self.parent.height() + self.height() + 25))
        self.__anim.setDuration(closeSpeed)
        self.__anim.start()

        timer = QTimer()
        timer.singleShot(closeSpeed, self.deleteLater)

    def changeIndex(self, newIndex, moveSpeed = 750, easingCurve = QEasingCurve.OutCubic):
        self.posIndex = newIndex
        self.__anim = QPropertyAnimation(self, b"pos")
        self.__anim.setEasingCurve(easingCurve)
        self.__anim.setEndValue(QPoint(int(self.parent.width() / 2 - self.width() / 2),
                                     int(self.parent.height() - ((self.height() + self.gap) * newIndex))))
        self.__anim.setDuration(moveSpeed)
        self.__anim.start()

    def getIndex(self):
        return self.posIndex

    def popToast(self, pop_speed = 750, easing_curve = QEasingCurve.OutCubic, pos_index = 1):

        self.posIndex = pos_index

        self.move(int(self.parent.width() / 2 - self.width() / 2),
                 self.parent.height() + self.height())
        self.show()

        self.__anim = QPropertyAnimation(self, b"pos")
        self.__anim.setEasingCurve(easing_curve)
        self.__anim.setEndValue(QPoint(int(self.parent.width() / 2 - self.width() / 2),
                                       int(self.parent.height() - (self.height() + self.gap) * pos_index)))
        self.__anim.setDuration(pop_speed)
        self.__anim.start()


# https://github.com/Vampouille/superboucle/blob/master/superboucle/qsuperdial.py
class QSuperDial(QDial):
    """Overload QDial with correct stylesheet support
    QSuperDial support background-color and color stylesheet
    properties and do NOT add "shadow"
    QSuperDial draw ellipse if width and height are different
    """

    _degree270 = 1.5 * math.pi
    _degree225 = 1.25 * math.pi

    def __init__(self, knob_radius=5, knob_margin=5):
        super(QSuperDial, self).__init__()
        self.knobRadius = knob_radius
        self.knobMargin = knob_margin
        self.setRange(0, 100)

    def paintEvent(self, event):
        # From Peter, thanks !
        # http://thecodeinn.blogspot.fr/2015/02/customizing-qdials-in-qt-part-1.html

        painter = QPainter(self)

        # So that we can use the background color
        painter.setBackgroundMode(1)

        # Smooth out the circle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(painter.background())
        point_color = QColor(painter.pen().color())
        painter.setPen(QPen(Qt.NoPen))

        painter.drawEllipse(0, 0, self.width(), self.height())
        painter.setBrush(QBrush(point_color))

        ratio = self.value() / self.maximum()
        angle = ratio * self._degree270 - self._degree225
        rx = self.width() / 2
        ry = self.height() / 2

        # Add r to have (0,0) in the center of dial
        y = math.sin(angle) * (ry - self.knobRadius - self.knobMargin) + ry
        x = math.cos(angle) * (rx - self.knobRadius - self.knobMargin) + rx

        # Draw the ellipse
        painter.drawEllipse(QPointF(x, y),
                            self.knobRadius,
                            self.knobRadius)

class KBDevice(QWidget):
    class IconType(enum.Enum):
        Remote = 0
        Robot = 1
    def __init__(self):
        super(KBDevice, self).__init__()

        self.__root_layout = QVBoxLayout()
        self.setLayout(self.__root_layout)

        self.__layout = QHBoxLayout()
        self.__root_layout.addLayout(self.__layout)

        self.__icon = QLabel()
        self.__layout.addWidget(self.__icon)

        self.__layout.addStretch()

        self.__device_nickname = QLabel()
        self.__device_nickname.setStyleSheet("font-family: Roboto; font-size: 14px;")
        self.__layout.addWidget(self.__device_nickname)

        self.__layout.addStretch()

        self.__device_type = QLabel()
        self.__device_type.setStyleSheet("font-family: Roboto; font-size: 14px;")
        self.__layout.addWidget(self.__device_type)

        self.__layout.addStretch()

        self.ping = QPushButton(strings.PING.upper())
        self.ping.setStyleSheet("font-family: Roboto; font-size: 16px;")
        self.ping.setFixedSize(QSize(84, 48))
        self.__layout.addWidget(self.ping)

        self.__line = QFrame()
        self.__line.setFrameShape(QFrame.Shape.HLine)
        self.__root_layout.addWidget(self.__line)

    def setIcon(self, icon: IconType):
        if icon == self.IconType.Remote:
            self.__icon.setPixmap(QPixmap("icons/remote-hardware-128.svg"))
        elif icon == self.IconType.Robot:
            self.__icon.setPixmap(QPixmap("icons/icon-meshview.svg"))

    def setDeviceName(self, name: str):
        self.__device_type.setText(name)

    def setDeviceNickName(self, name: str):
        self.__device_nickname.setText(name)

class KBDebugDataEntry(QWidget):
    def __init__(self):
        super(KBDebugDataEntry, self).__init__()

        self.setObjectName("Kevinbot3_Widget_KBDebugDataEntry")

        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)

        self.__icon = QLabel()
        self.__layout.addWidget(self.__icon)

        self.__data = QLabel()
        self.__data.setObjectName("Kevinbot3_Widget_KBDebugDataEntry_Data")
        self.__layout.addWidget(self.__data)

        self.__layout.addStretch()

    def setText(self, text: str):
        self.__data.setText(text)
    def setIcon(self, icon: QIcon, size: QSize = QSize(36, 36)):
        self.__icon.setPixmap(icon.pixmap(size))


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
                         QPointF(self.height() / 2 + math.cos(math.radians(self.angle)) * self.height() / 2 - 5,
                                 self.height() / 2 + math.sin(math.radians(self.angle)) * self.height() / 2))

        painter.drawLine(QPointF(self.height() / 2, self.height() / 2),
                         QPointF(self.height() / 2 - math.cos(math.radians(self.angle)) * self.height() / 2 + 5,
                                 self.height() / 2 - math.sin(math.radians(self.angle)) * self.height() / 2))

        # line 20px out of the angle line
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
    def __init__(self, palette, parent=None):
        super(Level, self).__init__(parent)

        self.levelText = "Angle: {}°"

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._top_layout = QHBoxLayout()
        self._layout.addLayout(self._top_layout)

        self._level = LevelWidget(self)
        self._level.setFixedSize(QSize(200, 200))
        self._top_layout.addWidget(self._level)

        qtg.setConfigOption("antialias", True)

        self.graph = qtg.PlotWidget()
        self.graph.plotItem.setMenuEnabled(False)
        self.graph.plotItem.setMouseEnabled(False, False)
        self._top_layout.addWidget(self.graph)

        color = palette.color(QPalette.Window)
        self.graph.setBackground(color)

        self.x = list(range(100))
        self.y = [0 for _ in range(100)]

        pen = qtg.mkPen(color="#F44336")
        self.data_line = self.graph.plot(self.x, self.y, pen=pen)

        self.label = QLabel()
        self.label.setFixedHeight(32)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(self.levelText.format(self._level.angle))
        self._layout.addWidget(self.label)

    def setAngle(self, angle):
        self._level.setAngle(angle)
        self.label.setText(self.levelText.format(angle))

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(angle)  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.

    def setLineColor(self, color):
        self._level.setLineColor(color)

    def setRobotColor(self, color):
        self._level.setRobotColor(color)

    def setLineWidth(self, width):
        self._level.setLineWidth(width)

    def setBackgroundColor(self, color):
        self._level.setBackgroundColor(color)
