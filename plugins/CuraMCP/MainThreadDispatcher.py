from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import threading
from UM.Logger import Logger


class MainThreadDispatcher(QObject):
    """
    Dispatcher to execute actions on the main Qt thread from background threads.
    """

    perform_action_signal = pyqtSignal(str, dict, object)

    def __init__(self):
        super().__init__()
        self.perform_action_signal.connect(self._perform_action)
        self._lock = threading.Lock()

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

    @pyqtSlot(str, dict, object)
    def _perform_action(self, action: str, args: dict, context: tuple):
        """
        Slot executed on the main thread.
        """
        event, result_container = context
        try:
            if action == "log":
                Logger.log("i", f"[MCP] {args.get('msg', '')}")
                result_container["result"] = True
            else:
                Logger.log("w", f"[MCP] Unknown action: {action}")
                result_container["error"] = ValueError(f"Unknown action: {action}")
        except Exception as e:
            Logger.log("e", f"[MCP] Error executing action {action}: {e}")
            result_container["error"] = e
        finally:
            event.set()
