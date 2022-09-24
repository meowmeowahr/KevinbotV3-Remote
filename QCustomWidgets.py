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
        self.__layout.addWidget(self.spinbox)

        self.add_button = QPushButton()
        self.add_button.setFixedSize(QSize(32, 28))
        self.add_button.setIconSize(QSize(32, 28))
        self.add_button.setIcon(QIcon("icons/add.svg"))
        self.add_button.clicked.connect(self.spinbox.stepUp)
        self.__layout.addWidget(self.add_button)

        self.remove_button = QPushButton()
        self.remove_button.setFixedSize(QSize(32, 28))
        self.remove_button.setIconSize(QSize(32, 28))
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
