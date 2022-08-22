# A D-Pad main_widget for PyQt5

from tracemalloc import stop
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class DPad(QWidget):
    def __init__(self, parent=None, size=50, dark=False, stop_button=False, icons=True):
        super(DPad, self).__init__(parent)

        self.stop_button = stop_button

        # object name
        self.setObjectName("Kevinbot3_DPad")

        # layout
        self.root_layout = QVBoxLayout()
        self.layout = QGridLayout()
        self.root_layout.addLayout(self.layout)
        self.radio_layout = QHBoxLayout()
        self.root_layout.addLayout(self.radio_layout)
        self.setLayout(self.root_layout)

        # create the buttons
        self.up = QPushButton('Up')
        self.down = QPushButton('Down')
        self.left = QPushButton('Left')
        self.right = QPushButton('Right')
        if stop_button:
            self.stop = QPushButton('Stop')

        # object names
        self.up.setObjectName("Kevinbot3_DPad_Button")
        self.down.setObjectName("Kevinbot3_DPad_Button")
        self.left.setObjectName("Kevinbot3_DPad_Button")
        self.right.setObjectName("Kevinbot3_DPad_Button")
        if stop_button:
            self.stop.setObjectName("Kevinbot3_DPad_Button")

        # square the buttons
        self.up.setFixedSize(size, size)
        self.down.setFixedSize(size, size)
        self.left.setFixedSize(size, size)
        self.right.setFixedSize(size, size)
        if stop_button:
            self.stop.setFixedSize(size, size)

        # add the icons
        if icons:
            if dark:
                self.up.setIcon(QIcon('icons/caret-up-dark.svg'))
                self.down.setIcon(QIcon('icons/caret-down-dark.svg'))
                self.left.setIcon(QIcon('icons/caret-left-dark.svg'))
                self.right.setIcon(QIcon('icons/caret-right-dark.svg'))
                if stop_button:
                    self.stop.setIcon(QIcon('icons/stop-dark.svg'))
            else:
                self.up.setIcon(QIcon('icons/caret-up.svg'))
                self.down.setIcon(QIcon('icons/caret-down.svg'))
                self.left.setIcon(QIcon('icons/caret-left.svg'))
                self.right.setIcon(QIcon('icons/caret-right.svg'))
                if stop_button:
                    self.stop.setIcon(QIcon('icons/stop.svg'))

            # hide the text
            self.up.setText('')
            self.down.setText('')
            self.left.setText('')
            self.right.setText('')
            if stop_button:
                self.stop.setText('')

        # icon size
        self.up.setIconSize(QSize(size-5, size-5))
        self.down.setIconSize(QSize(size-5, size-5))
        self.left.setIconSize(QSize(size-5, size-5))
        self.right.setIconSize(QSize(size-5, size-5))
        if stop_button:
            self.stop.setIconSize(QSize(size-10, size-10))

        # add the buttons to the layout
        self.layout.addWidget(self.up, 0, 1)
        self.layout.addWidget(self.down, 2, 1)
        self.layout.addWidget(self.left, 1, 0)
        self.layout.addWidget(self.right, 1, 2)       
        if stop_button:
            self.layout.addWidget(self.stop, 1, 1)

        # slow, med, fast radio buttons
        self.slow = QRadioButton('S')
        self.med = QRadioButton('M')
        self.fast = QRadioButton('F')

        # object names
        self.slow.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.med.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")
        self.fast.setObjectName("Kevinbot3_RemoteUI_SpeechRadio")

        # add the buttons to the layout
        self.radio_layout.addWidget(self.slow)
        self.radio_layout.addWidget(self.med)
        self.radio_layout.addWidget(self.fast)

    def addButtonPressActions(self, up, down, left, right, stop=None):
        self.up.pressed.connect(up)
        self.down.pressed.connect(down)
        self.left.pressed.connect(left)
        self.right.pressed.connect(right)
        if self.stop_button:
            self.stop.pressed.connect(stop)
    
    def addButtonReleaseActions(self, up, down, left, right, stop=None):
        self.up.released.connect(up)
        self.down.released.connect(down)
        self.left.released.connect(left)
        self.right.released.connect(right)
        if self.stop_button:
            self.stop.released.connect(stop)

    def addSpeedRadioActions(self, slow, med, fast):
        self.slow.toggled.connect(slow)
        self.med.toggled.connect(med)
        self.fast.toggled.connect(fast)

    def addRadioShortcuts(self, s, m, f):
        self.slow.setShortcut(s)
        self.med.setShortcut(m)
        self.fast.setShortcut(f)

    def toggleRadioWithName(self, name):
        if name == 'S':
            self.slow.toggle()
        elif name == 'M':
            self.med.toggle()
        elif name == 'F':
            self.fast.toggle()

    def setKeyboardShortcuts(self, up, down, left, right, stop=None):
        self.up.setShortcut(up)
        self.down.setShortcut(down)
        self.left.setShortcut(left)
        self.right.setShortcut(right)
        if self.stop_button:
            self.stop.setShortcut(stop)


# test
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    dpad = DPad(stop_button=True)
    dpad.show()
    dpad.addButtonPressActions(lambda: print('up'), lambda: print('down'), lambda: print('left'),
                               lambda: print('right'), lambda: print('stop'))
    dpad.addButtonReleaseActions(lambda: print('up released'), lambda: print('down released'),
                                 lambda: print('left released'), lambda: print('right released'),
                                 lambda: print('stop released'))
    dpad.setKeyboardShortcuts(Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Space)
    sys.exit(app.exec_())
