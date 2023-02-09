import os.path

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class QPushToolButton(QToolButton):
    def __init__(self, text: str = None):
        super().__init__()
        self.setText(text)


class QSpinner(QWidget):
    # noinspection PyArgumentList
    def __init__(self, text=None):
        super().__init__()

        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)

        if text:
            self.text = QLabel()
            self.text.setText(text)
            self.__layout.addWidget(self.text)

        self.spinbox = QSpinBox()
        self.spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinbox.setFixedHeight(32)
        self.__layout.addWidget(self.spinbox)

        self.add_button = QPushButton()
        self.add_button.setFixedSize(QSize(32, 32))
        self.add_button.setIconSize(QSize(32, 32))
        self.add_button.setIcon(QIcon("icons/add.svg"))
        self.add_button.clicked.connect(self.spinbox.stepUp)
        self.__layout.addWidget(self.add_button)

        self.remove_button = QPushButton()
        self.remove_button.setFixedSize(QSize(32, 32))
        self.remove_button.setIconSize(QSize(32, 32))
        self.remove_button.setIcon(QIcon("icons/subtract.svg"))
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
        self.centralWidget().addAction(self._windowify_action)


class KBModalBar(QFrame):
    def __init__(self, parent, width = 400, height = 64, gap = 16, centerText = True, opacity = 90, bgColor = None):
        super().__init__()

        self.gap = gap
        self.parent = parent

        self.setObjectName("Kevinbot3_RemoteUI_ModalBar")
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(QSize(width, height))
        self.setParent(parent)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(opacity / 100) #0 to 1 will cause the fade effect to kick in
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

    def popToast(self, popSpeed = 750, easingCurve = QEasingCurve.OutCubic, posIndex = 1):

        self.posIndex = posIndex

        self.move(int(self.parent.width() / 2 - self.width() / 2),
                 self.parent.height() + self.height())
        self.show()

        self.__anim = QPropertyAnimation(self, b"pos")
        self.__anim.setEasingCurve(easingCurve)
        self.__anim.setEndValue(QPoint(int(self.parent.width() / 2 - self.width() / 2),
                                     int(self.parent.height() - (self.height() + self.gap) * posIndex)))
        self.__anim.setDuration(popSpeed)
        self.__anim.start()