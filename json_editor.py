"""
This is the main window to launch the editor
The whole UI mainly divided by two part:
1. Browser(json) on the left
2. Model(table) on the right


References:
This JSON Editor Tool highly relies on packages: QJsonModel, jsonViewer,
which provide classes and methods to display and control dictionary-like,
hierarchical data structure.
QJsonModel: https://github.com/dridk/QJsonModel.git
jsonViewer: https://github.com/leixingyu/jsonEditor.git
"""

import json
import os
import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *

from jsonViewer.qjsonmodel import QJsonModel
from jsonViewer.qjsonnode import QJsonNode
from jsonViewer.qjsonview import QJsonView

from syntax import JsonHighlighter, STYLE_1, STYLE_1_QSS

# Set UI file
MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.join(MODULE_PATH, 'ui', 'jsonEditor.ui')

# Default JSON file
with open("settings.json", "r") as f:
    START_SETTINGS = json.load(f)


class JSONEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Kevinbot3_RemoteUI_JSONEdit")


class Editor(QSplitter):
    def __init__(self):
        super(Editor, self).__init__()

        self.setMinimumSize(400, 190)

        self.ui_view_edit = JSONEditor()
        self.ui_view_edit.setStyleSheet(STYLE_1_QSS)
        self.highlight = JsonHighlighter(self.ui_view_edit.document(), STYLE_1)
        self.ui_view_edit.setReadOnly(True)
        self.addWidget(self.ui_view_edit)

        self.ui_tree_view = QJsonView()
        self.ui_tree_view.setAnimated(True)
        self.ui_tree_view.setIndentation(20)
        self.ui_tree_view.dataChanged = lambda a, b, c: self.updateBrowser()
        self.ui_tree_view.setObjectName("Kevinbot3_JsonEditor_TreeView")
        self.addWidget(self.ui_tree_view)

        # make the first column 200px wide
        self.ui_tree_view.setColumnWidth(0, 400)

        # Load settings
        root = QJsonNode.load(START_SETTINGS)
        self._model = QJsonModel(root, self)

        # Proxy model
        self._proxyModel = QtCore.QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self._model)
        self._proxyModel.setDynamicSortFilter(False)
        self._proxyModel.setSortRole(QJsonModel.sortRole)
        self._proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._proxyModel.setFilterRole(QJsonModel.filterRole)
        self._proxyModel.setFilterKeyColumn(0)

        # Json Viewer
        self.ui_tree_view.setModel(self._proxyModel)
        self.updateBrowser()
        self.filePath = ['', '']

    # Save file
    def saveFile(self):
        # ask for confirmation
        reply = QMessageBox.question(self, 'Confirmation', "Are you sure to save settings.json?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.filePath = "settings.json"
            file = open(self.filePath, 'w')
            file.write(self.ui_view_edit.toPlainText())
            file.close()

    # Collapse
    def collapseAll(self):
        self.ui_tree_view.collapseAll()

    # Expand
    def expandAll(self):
        self.ui_tree_view.expandAll()

    # Update the Browser on the left
    def updateBrowser(self):
        self.ui_view_edit.clear()
        output = self.ui_tree_view.asDict(None)
        json_dict = json.dumps(output, indent=3, sort_keys=True)
        self.ui_view_edit.setPlainText(str(json_dict))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Editor()
    window.show()
    sys.exit(app.exec_())
