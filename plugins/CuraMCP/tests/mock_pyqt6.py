import sys
from unittest.mock import MagicMock

# Mock PyQt6 modules
QtCore = MagicMock()
QtWidgets = MagicMock()
QtQuick = MagicMock()


# Mock QObject
class QObject:
    def __init__(self, name=""):
        self._name = name
        self._children = []

    def objectName(self):
        return self._name

    def children(self):
        return self._children

    def setChildren(self, children):
        self._children = children


QtCore.QObject = QObject
QtCore.QRect = MagicMock


# Mock QWidget
class QWidget(QObject):
    def __init__(self, name=""):
        super().__init__(name)
        self._visible = True
        self._enabled = True
        self._geometry = MagicMock()
        self._geometry.x.return_value = 0
        self._geometry.y.return_value = 0
        self._geometry.width.return_value = 100
        self._geometry.height.return_value = 100
        self._text = ""
        self._windowTitle = ""

    def isVisible(self):
        return self._visible

    def isEnabled(self):
        return self._enabled

    def geometry(self):
        return self._geometry

    def text(self):
        return self._text

    def windowTitle(self):
        return self._windowTitle


QtWidgets.QWidget = QWidget
QtWidgets.QApplication = MagicMock()


# Mock QQuickItem
class QQuickItem(QObject):
    def __init__(self, name=""):
        super().__init__(name)
        self._visible = True
        self._enabled = True
        self._x = 0
        self._y = 0
        self._width = 100
        self._height = 100
        self._contentItem = None

    def isVisible(self):
        return self._visible

    def isEnabled(self):
        return self._enabled

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height

    def contentItem(self):
        return self._contentItem


QtQuick.QQuickItem = QQuickItem

# Register mocks
sys.modules["PyQt6"] = MagicMock()
sys.modules["PyQt6.QtCore"] = QtCore
sys.modules["PyQt6.QtWidgets"] = QtWidgets
sys.modules["PyQt6.QtQuick"] = QtQuick

# Mock UM
UM = MagicMock()
UM.Extension = MagicMock
UM.Logger = MagicMock
sys.modules["UM"] = UM
sys.modules["UM.Extension"] = UM.Extension
sys.modules["UM.Logger"] = UM.Logger
