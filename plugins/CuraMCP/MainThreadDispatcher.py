from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QMetaObject, Qt
import threading
from typing import List, Optional, Dict, Any

from UM.Logger import Logger
from UM.Math.Vector import Vector
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

try:
    from cura.CuraApplication import CuraApplication
except ImportError:
    CuraApplication = None

try:
    from .QMLCrawler import QMLCrawler
except ImportError:
    from QMLCrawler import QMLCrawler

try:
    from PyQt6.QtTest import QTest
except ImportError:
    QTest = None


class MainThreadDispatcher(QObject):
    """
    Dispatcher to execute actions on the main Qt thread from background threads.
    """

    perform_action_signal = pyqtSignal(str, dict, object)

    def __init__(self):
        super().__init__()
        self.perform_action_signal.connect(self._perform_action)
        self._lock = threading.Lock()
        self._crawler = QMLCrawler()

    def dispatch(self, action: str, args: dict = None):
        """
        Dispatch an action to the main thread and wait for the result.
        """
        if args is None:
            args = {}

        event = threading.Event()
        result_container = {"result": None, "error": None}

        # We pass the event and result container to the slot
        self.perform_action_signal.emit(action, args, (event, result_container))

        # Wait for the action to complete
        event.wait()

        if result_container["error"]:
            raise result_container["error"]

        return result_container["result"]

    def _get_camera(self):
        if not CuraApplication:
            return None
        return (
            CuraApplication.getInstance().getController().getScene().getActiveCamera()
        )

    def _find_node_by_id(self, node_id: str):
        if not CuraApplication:
            return None
        scene = CuraApplication.getInstance().getController().getScene()
        # Try to find node by ID (assuming string ID)
        # Note: SceneNode IDs in UM are usually strings.
        # We can iterate if findNode doesn't exist or we need specific logic.
        # Let's try to use a simple iterator for now as it's safer than guessing API.
        for node in DepthFirstIterator(scene.getRoot()):
            if node.getId() == node_id:  # Assuming getId() exists, which is standard
                return node
            # Also check name if ID doesn't match, sometimes users mean name
            if node.getName() == node_id:
                return node
        return None

    @pyqtSlot(str, dict, object)
    def _perform_action(self, action: str, args: dict, context: tuple):
        """
        Slot executed on the main thread.
        """
        event, result_container = context
        try:
            app = CuraApplication.getInstance() if CuraApplication else None

            if action == "log":
                Logger.log("i", f"[MCP] {args.get('msg', '')}")
                result_container["result"] = True

            # --- Camera Actions ---
            elif action == "camera_home":
                if app:
                    # Use CuraActions logic
                    scene = app.getController().getScene()
                    camera = scene.getActiveCamera()
                    if camera:
                        diagonal_size = app.getBuildVolume().getDiagonalSize()
                        camera.setPosition(Vector(-80, 250, 700) * diagonal_size / 375)
                        camera.setPerspective(True)
                        camera.lookAt(Vector(0, 0, 0))
                        result_container["result"] = True
                    else:
                        result_container["error"] = RuntimeError("No active camera")
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            elif action == "camera_set_view":
                view = args.get("view", "iso").lower()
                if app:
                    scene = app.getController().getScene()
                    camera = scene.getActiveCamera()
                    if camera:
                        # Basic view implementation
                        # Assuming origin (0,0,0) is center of build plate or close to it
                        # We might need to adjust based on build volume size
                        bbox = app.getBuildVolume().getBoundingBox()
                        center = bbox.center if bbox else Vector(0, 0, 0)
                        size = (
                            bbox.size if bbox else Vector(200, 200, 200)
                        )  # Default fallback
                        dist = max(size.x, size.y, size.z) * 2.0

                        if view == "top":
                            camera.setPosition(center + Vector(0, dist, 0))
                            camera.lookAt(center)
                        elif view == "bottom":
                            camera.setPosition(center + Vector(0, -dist, 0))
                            camera.lookAt(center)
                        elif view == "front":
                            camera.setPosition(center + Vector(0, 0, dist))
                            camera.lookAt(center)
                        elif view == "back":
                            camera.setPosition(center + Vector(0, 0, -dist))
                            camera.lookAt(center)
                        elif view == "right":
                            camera.setPosition(center + Vector(dist, 0, 0))
                            camera.lookAt(center)
                        elif view == "left":
                            camera.setPosition(center + Vector(-dist, 0, 0))
                            camera.lookAt(center)
                        elif view == "iso":
                            # Similar to home but maybe strictly isometric angle
                            camera.setPosition(center + Vector(dist, dist, dist))
                            camera.lookAt(center)
                        else:
                            result_container["error"] = ValueError(
                                f"Unknown view: {view}"
                            )

                        if not result_container["error"]:
                            result_container["result"] = True
                    else:
                        result_container["error"] = RuntimeError("No active camera")
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            elif action == "camera_look_at":
                x = args.get("x", 0.0)
                y = args.get("y", 0.0)
                z = args.get("z", 0.0)
                if app:
                    camera = self._get_camera()
                    if camera:
                        camera.lookAt(Vector(x, y, z))
                        result_container["result"] = True
                    else:
                        result_container["error"] = RuntimeError("No active camera")
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            # --- Tool Actions ---
            elif action == "tool_set_active":
                tool_id = args.get("tool_id")
                if app:
                    app.getController().setActiveTool(tool_id)
                    result_container["result"] = True
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            elif action == "tool_get_active":
                if app:
                    tool = app.getController().getActiveTool()
                    result_container["result"] = tool.getPluginId() if tool else None
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            # --- Selection Actions ---
            elif action == "selection_get":
                if app:
                    nodes = Selection.getAllSelectedObjects()
                    # Return list of IDs or names
                    result_container["result"] = [
                        {"id": node.getId(), "name": node.getName()} for node in nodes
                    ]
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            elif action == "selection_clear":
                if app:
                    Selection.clear()
                    result_container["result"] = True
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            elif action == "selection_set":
                node_ids = args.get("node_ids", [])
                if app:
                    Selection.clear()
                    for node_id in node_ids:
                        node = self._find_node_by_id(node_id)
                        if node:
                            Selection.add(node)
                    result_container["result"] = True
                else:
                    result_container["error"] = RuntimeError(
                        "CuraApplication not available"
                    )

            # --- Existing Actions ---
            elif action == "get_ui_tree":
                result_container["result"] = self._crawler.get_ui_tree()
            elif action == "click":
                element_id = args.get("id")
                obj = self._crawler.find_element(element_id)
                if obj:
                    if QTest:
                        QTest.mouseClick(obj, Qt.MouseButton.LeftButton)
                        result_container["result"] = True
                    else:
                        Logger.log("w", "[MCP] QTest not available for click action")
                        result_container["error"] = RuntimeError("QTest not available")
                else:
                    result_container["error"] = ValueError(
                        f"Element not found: {element_id}"
                    )
            elif action == "set_value":
                element_id = args.get("id")
                value = args.get("value")
                obj = self._crawler.find_element(element_id)
                if obj:
                    prop_name = args.get("property", "text")
                    obj.setProperty(prop_name, value)
                    result_container["result"] = True
                else:
                    result_container["error"] = ValueError(
                        f"Element not found: {element_id}"
                    )
            elif action == "invoke_action":
                element_id = args.get("id")
                method_name = args.get("action")
                obj = self._crawler.find_element(element_id)
                if obj:
                    QMetaObject.invokeMethod(obj, method_name)
                    result_container["result"] = True
                else:
                    result_container["error"] = ValueError(
                        f"Element not found: {element_id}"
                    )
            else:
                Logger.log("w", f"[MCP] Unknown action: {action}")
                result_container["error"] = ValueError(f"Unknown action: {action}")
        except Exception as e:
            Logger.log("e", f"[MCP] Error executing action {action}: {e}")
            result_container["error"] = e
        finally:
            event.set()
