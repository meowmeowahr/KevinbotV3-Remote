import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import *
from utils import load_theme


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        load_theme(self, "qdarktheme_kbot")

        self.setWindowTitle("Theme Preview")
        self.setObjectName("Kevinbot3_RemoteUI")

        palette = self.palette()
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight,
                         palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText,
                         palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText))
        self.setPalette(palette)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.button = QPushButton("Button")
        self.layout.addWidget(self.button, 0, 0)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setObjectName("Kevinbot3_RemoteUI_Slider")
        self.layout.addWidget(self.slider, 0, 1)

        self.check_box = QCheckBox("CheckBox")
        self.layout.addWidget(self.check_box, 1, 0)

        self.radio = QRadioButton("Radio")
        self.layout.addWidget(self.radio, 1, 1)

        self.combo = QComboBox()
        self.combo.setObjectName("Kevinbot3_RemoteUI_Combo")
        self.layout.addWidget(self.combo, 2, 0)

        self.progress = QProgressBar()
        self.progress.setValue(50)
        self.progress.setTextVisible(False)
        self.layout.addWidget(self.progress, 2, 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    QApplication.setStyle(QStyleFactory().create('Fusion'))
    window.show()
    app.exec()
