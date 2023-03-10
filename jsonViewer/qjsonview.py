"""
The view inheriting QTreeView for displaying QJsonModel
this view is strictly used to display and control dictionary-like,
hierarchical data structure.
With custom implementation of drag & drop, editing behavior

Reference:
https://doc.qt.io/qt-5/model-view-programming.html#mime-data
https://doc.qt.io/qt-5/qitemselectionmodel.html
https://stackoverflow.com/questions/10778936/qt-mousemoveevent-qtleftbutton
https://doc.qt.io/qt-5/qmouseevent.html#button
"""


import ast
from PyQt6 import QtWidgets, QtCore, QtGui
from .qjsonnode import QJsonNode


class ItemDelegate(QtWidgets.QItemDelegate):
    def sizeHint(self, option, index):
        if index.column() == 1:
            return QtCore.QSize(0, 32)
        return super().sizeHint(option, index)


class QJsonView(QtWidgets.QTreeView):
    dragStartPosition = None

    def __init__(self):
        """
        Initialization
        """
        super(QJsonView, self).__init__()

        self._clipBroad = ''

        # set flags
        self.setSortingEnabled(True)
        self.setExpandsOnDoubleClick(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.setItemDelegate(ItemDelegate())
        self.setAlternatingRowColors(True)
        self.customContextMenuRequested.connect(self.openContextMenu)

    def setModel(self, model):
        """
        Extend: set the current model and sort it

        :param model: QSortFilterProxyModel. model
        """
        super(QJsonView, self).setModel(model)
        self.model().sort(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.header().resizeSection(0, 170)

    def openContextMenu(self, position):
        """
        Custom: open context menu when right-clicking
        """
        index = self.indexAt(position)
        if not index.isValid():
            return
        self.contextMenu = QtWidgets.QMenu()
        self.contextMenu.addAction('Expand All', self.expandAll)
        self.contextMenu.addAction('Collapse All', self.collapseAll)
        self.contextMenu.exec(self.mapToGlobal(position))

    # helper methods

    def getSelectedIndices(self):
        """
        Custom: get source model indices of the selected item(s)

        :return: list of QModelIndex. selected indices
        """
        indices = self.selectionModel().selectedRows()
        return [self.model().mapToSource(index) for index in indices]

    def asDict(self, indices):
        """
        Custom: serialize specified model indices to dictionary

        :param indices: list of QModelIndex. root indices
        :return: dict. output dictionary
        """
        output = dict()
        if not indices:
            output = self.model().sourceModel().asDict()
        else:
            for index in indices:
                output.update(self.model().sourceModel().asDict(index))
        return output

    # overwrite drag and drop

    def mousePressEvent(self, event):
        """
        Override: record mouse click position
        """
        super(QJsonView, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.dragStartPosition = event.pos()

    def mouseMoveEvent(self, event):
        """
        Override: instantiate custom drag object when dragging with left-click
        """
        if not event.buttons():
            return

        if not event.buttons() == QtCore.Qt.LeftButton:
            return

        if (event.pos() - self.dragStartPosition).manhattanLength() \
                < QtWidgets.QApplication.startDragDistance():
            return

        if self.selectionModel().selectedRows():
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()

            selected = self.asDict(self.getSelectedIndices())
            mime_data.setText(str(selected))
            drag.setMimeData(mime_data)

            drag.exec_()

    def dragEnterEvent(self, event):
        """
        Override: allow dragging only for certain drag object
        """
        data = event.mimeData()
        if data.hasText():
            event.acceptProposedAction()

    # custom behavior
    def remove(self, indices):
        """
        Custom: remove node(s) of specified indices

        :param indices: QModelIndex. specified indices
        """
        for index in indices:
            current_node = index.internalPointer()
            position = current_node.row()

            # let the model know we are removing
            self.model().sourceModel().removeChild(position, index.parent())

    def add(self, text=None, index=QtCore.QModelIndex()):
        """
        Custom: add node(s) under the specified index

        :param text: str. input text for de-serialization
        :param index: QModelIndex. parent index
        """
        # populate items with a temp root
        root = QJsonNode.load(ast.literal_eval(text))

        self.model().sourceModel().addChildren(root.children, index)
        self.model().sort(0, QtCore.Qt.AscendingOrder)

    def clear(self):
        """
        Custom: clear the entire view
        """
        self.model().sourceModel().clear()

    def copy(self):
        """
        Custom: copy the selected indices by store the serialized value
        """
        selected = self.asDict(self.getSelectedIndices())
        self._clipBroad = str(selected)

    def paste(self, index):
        """
        Custom: paste to index by de-serialize clipboard value

        :param index: QModelIndex. target index
        """
        self.customAdd(self._clipBroad, index)
        self._clipBroad = ''
        
    def customAdd(self, text=None, index=QtCore.QModelIndex()):
        """
        Custom: add node(s) under the specified index using specified values

        :param text: str. input text for de-serialization
        :param index: QModelIndex. parent index
        """

        # test value
        if not text:
            text = "{'_newEntry0': [{'key0': 'value0','key1': 'value1'},{'key0': 'value2','key1': 'value3'}]}"
        self.add(text, index)
