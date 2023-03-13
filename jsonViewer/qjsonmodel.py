"""
The model class used for populating the QJsonView,
and providing functionalities to manipulate QJsonNode objects within the model
"""


from qtpy import QtCore, QtGui
from .qjsonnode import QJsonNode
import os
import platform

FILE_ICON = QtGui.QIcon("icons/file.svg")
FOLDER_ICON = QtGui.QIcon("icons/folder.svg")
NUMBER_ICON = QtGui.QIcon("icons/number.svg")
STRING_ICON = QtGui.QIcon("icons/string.svg")
URL_ICON = QtGui.QIcon("icons/link.svg")
BOOL_ICON = QtGui.QIcon("icons/bool.svg")
BLANK_ICON = QtGui.QIcon()


class QJsonModel(QtCore.QAbstractItemModel):
    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1

    def __init__(self, root, parent=None):
        """
        Initialization

        :param root: QJsonNode. root node of the model, it is hidden
        """
        super(QJsonModel, self).__init__(parent)
        self._rootNode = root

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Override
        """
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        return parentNode.childCount

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Override
        """
        return 2

    def data(self, index, role):
        """
        Override
        """
        node = self.getNode(index)

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return node.key
            elif index.column() == 1:
                return node.value

        elif role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return node.key
            elif index.column() == 1:
                return node.value

        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0:
                return node.icon
            elif index.column() == 1:
                if isinstance(node.value, bool):
                    return node.boolIcon
                elif isinstance(node.value, int):
                    return node.integerIcon
                elif isinstance(node.value, str) and node.value.startswith("http"):
                    return node.urlIcon
                elif isinstance(node.value, str) and not node.value == "":
                    return node.stringIcon

                if not platform.system() == "Windows":
                    if isinstance(node.value, str) and os.path.isdir(str(node.value).replace("$USER",
                                                                                               os.environ["USER"])):
                        return node.folderIcon
                    elif isinstance(node.value, str) and os.path.isfile(str(node.value).replace("$USER",
                                                                                                os.environ["USER"])):
                        return node.fileIcon

        elif role == QJsonModel.sortRole:
            return node.key

        elif role == QJsonModel.filterRole:
            return node.key

        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(-1, 32)

    def setData(self, index, value, role):
        """
        Override
        """
        node = self.getNode(index)

        if role == QtCore.Qt.EditRole:
            if index.column() == 0:
                node.key = value
                self.dataChanged.emit(index, index)
                return True

            if index.column() == 1:
                node.value = value
                self.dataChanged.emit(index, index)
                return True

        return False

    def headerData(self, section, orientation, role):
        """
        Override
        """
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Key"
            elif section == 1:
                return "Value"

    def flags(self, index):
        """
        Override
        """
        flags = super(QJsonModel, self).flags(index)
        if index.column() == 0:
            return (QtCore.Qt.ItemFlag.NoItemFlags
                    | QtCore.Qt.ItemIsDragEnabled
                    | QtCore.Qt.ItemIsDropEnabled
                    | flags)
        else:
            return (QtCore.Qt.ItemFlag.ItemIsEditable
                    | QtCore.Qt.ItemIsDragEnabled
                    | QtCore.Qt.ItemIsDropEnabled
                    | flags)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        """
        Override
        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parentNode = self.getNode(parent)
        currentNode = parentNode.child(row)
        if currentNode:
            return self.createIndex(row, column, currentNode)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        """
        Override
        """
        currentNode = self.getNode(index)
        parentNode = currentNode.parent

        if parentNode == self._rootNode:
            return QtCore.QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    def addChildren(self, children, parent=QtCore.QModelIndex()):
        """
        Custom: add children QJsonNode to the specified index
        """
        self.beginInsertRows(parent, 0, len(children) - 1)

        if parent == QtCore.QModelIndex():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        for child in children:
            parentNode.addChild(child)

        self.endInsertRows()
        return True

    def removeChild(self, position, parent=QtCore.QModelIndex()):
        """
        Custom: remove child of position for the specified index
        """
        self.beginRemoveRows(parent, position, position)

        if parent == QtCore.QModelIndex():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        parentNode.removeChild(position)

        self.endRemoveRows()
        return True

    def clear(self):
        """
        Custom: clear the model data
        """
        self.beginResetModel()
        self._rootNode = QJsonNode()
        self.endResetModel()
        return True

    def getNode(self, index):
        """
        Custom: get QJsonNode from model index

        :param index: QModelIndex. specified index
        """
        if index.isValid():
            current_node = index.internalPointer()
            current_node.icon = BLANK_ICON
            current_node.integerIcon = NUMBER_ICON
            current_node.urlIcon = URL_ICON
            current_node.folderIcon = FOLDER_ICON
            current_node.fileIcon = FILE_ICON
            current_node.stringIcon = STRING_ICON
            current_node.boolIcon = BOOL_ICON
            if current_node:
                return current_node
        return self._rootNode

    def asDict(self, index=QtCore.QModelIndex()):
        """
        Custom: serialize specified index to dictionary
        if no index is specified, the whole model will be serialized
        but will not include the root key (as it's supposed to be hidden)

        :param index: QModelIndex. specified index
        :return: dict. output dictionary
        """
        node = self.getNode(index)
        if node == self._rootNode:
            return list(node.asDict().values())[0]

        return node.asDict()
