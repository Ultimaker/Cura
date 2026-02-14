from PyQt6.QtCore import QObject, QRect
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtQuick import QQuickItem
from typing import Dict, Any, List, Optional


class QMLCrawler:
    """
    Crawls the QML/Qt object hierarchy to build a DOM-like structure.
    """

    def find_element(self, element_id: str) -> Optional[QObject]:
        """
        Finds a QObject by its objectName.
        """
        for widget in QApplication.topLevelWidgets():
            found = self._find_in_object(widget, element_id)
            if found:
                return found
        return None

    def _find_in_object(self, obj: QObject, element_id: str) -> Optional[QObject]:
        """
        Recursively searches for an object with the given objectName.
        """
        if obj.objectName() == element_id:
            return obj

        children = obj.children()
        for child in children:
            found = self._find_in_object(child, element_id)
            if found:
                return found

        # Special handling for QQuickWindow content item
        if hasattr(obj, "contentItem"):
            content_item = obj.contentItem()
            if content_item:
                found = self._find_in_object(content_item, element_id)
                if found:
                    return found

        return None

    def get_ui_tree(self) -> Dict[str, Any]:
        """
        Returns the full UI tree starting from top-level widgets.
        """
        tree = []
        for widget in QApplication.topLevelWidgets():
            if widget.isVisible():
                tree.append(self._crawl_object(widget))
        return {"root": tree}

    def _crawl_object(self, obj: QObject) -> Dict[str, Any]:
        """
        Recursively crawls a QObject (QWidget or QQuickItem).
        """
        node = {"type": type(obj).__name__, "id": obj.objectName(), "children": []}

        # Geometry and Visibility
        if isinstance(obj, QWidget):
            node["visible"] = obj.isVisible()
            node["enabled"] = obj.isEnabled()
            geo = obj.geometry()
            node["geometry"] = {
                "x": geo.x(),
                "y": geo.y(),
                "width": geo.width(),
                "height": geo.height(),
            }
            # Text properties
            if hasattr(obj, "text"):
                node["text"] = obj.text()
            if hasattr(obj, "windowTitle"):
                node["title"] = obj.windowTitle()

        elif isinstance(obj, QQuickItem):
            node["visible"] = obj.isVisible()
            node["enabled"] = obj.isEnabled()
            node["geometry"] = {
                "x": obj.x(),
                "y": obj.y(),
                "width": obj.width(),
                "height": obj.height(),
            }
            # QML specific properties can be added here
            # e.g. attached properties, or specific QML types

        # Recursion
        children = obj.children()
        for child in children:
            # Filter out some internal objects if needed
            if isinstance(child, (QWidget, QQuickItem)):
                node["children"].append(self._crawl_object(child))

        # Special handling for QQuickWindow content item
        if hasattr(obj, "contentItem"):
            content_item = obj.contentItem()
            if content_item:
                node["children"].append(self._crawl_object(content_item))

        return node
