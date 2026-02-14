import sys
import unittest
from unittest.mock import MagicMock

# Import mock PyQt6
import mock_pyqt6

# Now import QMLCrawler
from QMLCrawler import QMLCrawler


class TestQMLCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = QMLCrawler()
        self.app = mock_pyqt6.QtWidgets.QApplication
        self.app.topLevelWidgets = MagicMock()

    def test_get_ui_tree_empty(self):
        self.app.topLevelWidgets.return_value = []
        tree = self.crawler.get_ui_tree()
        self.assertEqual(tree, {"root": []})

    def test_get_ui_tree_single_widget(self):
        widget = mock_pyqt6.QtWidgets.QWidget("TestWidget")
        widget._visible = True
        widget._enabled = True
        widget._geometry.x.return_value = 10
        widget._geometry.y.return_value = 20
        widget._geometry.width.return_value = 100
        widget._geometry.height.return_value = 50
        widget._text = "Hello"
        widget._windowTitle = "My Window"

        self.app.topLevelWidgets.return_value = [widget]

        tree = self.crawler.get_ui_tree()

        expected_node = {
            "type": "QWidget",
            "id": "TestWidget",
            "children": [],
            "visible": True,
            "enabled": True,
            "geometry": {"x": 10, "y": 20, "width": 100, "height": 50},
            "text": "Hello",
            "title": "My Window",
        }

        self.assertEqual(tree["root"][0], expected_node)

    def test_get_ui_tree_nested_widgets(self):
        parent = mock_pyqt6.QtWidgets.QWidget("Parent")
        child = mock_pyqt6.QtWidgets.QWidget("Child")
        parent._children = [child]

        self.app.topLevelWidgets.return_value = [parent]

        tree = self.crawler.get_ui_tree()

        self.assertEqual(len(tree["root"]), 1)
        self.assertEqual(tree["root"][0]["id"], "Parent")
        self.assertEqual(len(tree["root"][0]["children"]), 1)
        self.assertEqual(tree["root"][0]["children"][0]["id"], "Child")

    def test_get_ui_tree_qquickitem(self):
        item = mock_pyqt6.QtQuick.QQuickItem("QMLItem")
        item._visible = True
        item._enabled = False
        item._x = 5
        item._y = 5
        item._width = 200
        item._height = 200

        # QQuickItem is not a top level widget, so we wrap it in a QWidget
        container = mock_pyqt6.QtWidgets.QWidget("Container")
        container._children = [item]

        self.app.topLevelWidgets.return_value = [container]

        tree = self.crawler.get_ui_tree()

        qml_node = tree["root"][0]["children"][0]
        self.assertEqual(qml_node["type"], "QQuickItem")
        self.assertEqual(qml_node["id"], "QMLItem")
        self.assertEqual(qml_node["visible"], True)
        self.assertEqual(qml_node["enabled"], False)
        self.assertEqual(
            qml_node["geometry"], {"x": 5, "y": 5, "width": 200, "height": 200}
        )


if __name__ == "__main__":
    unittest.main()
