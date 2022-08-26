import string
from PyQt5.QtWidgets import QToolButton

class QPushToolButton(QToolButton):
    def __init__(self, text: str = None):
        super().__init__()
        self.setText(text)