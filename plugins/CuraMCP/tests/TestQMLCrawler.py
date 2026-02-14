import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock PyQt6
mock_pyqt_core = MagicMock()
mock_pyqt_widgets = MagicMock()
mock_pyqt_quick = MagicMock()

sys.modules["PyQt6"] = MagicMock()
sys.modules["PyQt6.QtCore"] = mock_pyqt_core
sys.modules["PyQt6.QtWidgets"] = mock_pyqt_widgets
sys.modules["PyQt6.QtQuick"] = mock_pyqt_quick


# Mock QObject and QWidget for type checking
class MockQObject:
    def __init__(self, name=""):
        self._objectName = name
        self._children = []
        self._visible = True
        self._enabled = True

    def objectName(self):
        return self._objectName

    def children(self):
        return self._children

    def isVisible(self):
        return self._visible

    def isEnabled(self):
        return self._enabled

    def setVisible(self, visible):
        self._visible = visible


class MockQWidget(MockQObject):
    def geometry(self):
        return MagicMock(
            x=lambda: 0, y=lambda: 0, width=lambda: 100, height=lambda: 100
        )


class MockQQuickItem(MockQObject):
    def x(self):
        return 0

    def y(self):
        return 0

    def width(self):
        return 100

    def height(self):
        return 100


mock_pyqt_core.QObject = MockQObject
mock_pyqt_widgets.QWidget = MockQWidget
mock_pyqt_widgets.QApplication = MagicMock()
mock_pyqt_quick.QQuickItem = MockQQuickItem

# Add plugin path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from QMLCrawler import QMLCrawler


class TestQMLCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = QMLCrawler()

        # Setup a mock UI tree
        self.root = MockQWidget("root")
        self.child1 = MockQWidget("child1")
        self.child2 = MockQQuickItem("child2")
        self.grandchild = MockQWidget("grandchild")

        self.root._children = [self.child1, self.child2]
        self.child2._children = [self.grandchild]

        # Mock QApplication.topLevelWidgets
        mock_pyqt_widgets.QApplication.topLevelWidgets.return_value = [self.root]

    def test_find_element_found(self):
        # Setup a mock UI tree
        root = MockQWidget("root")
        child1 = MockQWidget("child1")
        child2 = MockQQuickItem("child2")
        grandchild = MockQWidget("grandchild")

        root._children = [child1, child2]
        child2._children = [grandchild]

        # Mock QApplication.topLevelWidgets
        mock_pyqt_widgets.QApplication.topLevelWidgets.return_value = [root]

        element = self.crawler.find_element("grandchild")
        self.assertIsNotNone(element)
        self.assertEqual(element.objectName(), "grandchild")

    def test_find_element_not_found(self):
        # Setup a mock UI tree
        root = MockQWidget("root")

        # Mock QApplication.topLevelWidgets
        mock_pyqt_widgets.QApplication.topLevelWidgets.return_value = [root]

        element = self.crawler.find_element("non_existent")
        self.assertIsNone(element)


if __name__ == "__main__":
    unittest.main()
