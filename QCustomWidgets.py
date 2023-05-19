import enum
import os.path
import math

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import qtawesome as qta

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

        # Use background color
        painter.setBrush(painter.background())

        # Store color from stylesheet, pen will be overriden
        point_color = QColor(painter.pen().color())

        # No border
        painter.setPen(QPen(Qt.NoPen))

        # Draw first circle
        painter.drawEllipse(0, 0, self.width(), self.height())

        # Reset color to point_color from stylesheet
        painter.setBrush(QBrush(point_color))

        # Get ratio between current value and maximum to calculate angle
        ratio = self.value() / self.maximum()

        # The maximum amount of degrees is 270, offset by 225
        angle = ratio * self._degree270 - self._degree225

        # Radius of background circle
        rx = self.width() / 2
        ry = self.height() / 2

        # Add r to have (0,0) in center of dial
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