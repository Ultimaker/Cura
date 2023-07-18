# Copyright (c) 2023 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import subprocess
from typing import Optional, List

from UM.Logger import Logger
from UM.PluginObject import PluginObject


class BackendPlugin(PluginObject):
    def __init__(self) -> None:
        super().__init__()
        self.__port: int = 0
        self._plugin_address: str = "127.0.0.1"
        self._plugin_command: Optional[List[str]] = None
        self._process = None
        self._is_running = False
        self._supported_slots: List[int] = []

    def getSupportedSlots(self) -> List[int]:
        return self._supported_slots

    def isRunning(self):
        return self._is_running

    def setPort(self, port: int) -> None:
        self.__port = port

    def getPort(self) -> int:
        return self.__port

    def getAddress(self) -> str:
        return self._plugin_address

    def _validatePluginCommand(self) -> list[str]:
        """
        Validate the plugin command and add the port parameter if it is missing.

        :return: A list of strings containing the validated plugin command.
        """
        if not self._plugin_command or "--port" in self._plugin_command:
            return self._plugin_command or []

        return self._plugin_command + ["--port=", str(self.__port)]

    def start(self) -> bool:
        """
        Starts the backend_plugin process.

        :return: True if the plugin process started successfully, False otherwise.
        """
        try:
            # STDIN needs to be None because we provide no input, but communicate via a local socket instead.
            # The NUL device sometimes doesn't exist on some computers.
            self._process = subprocess.Popen(self._validatePluginCommand(), stdin = None)
            self._is_running = True
            return True
        except PermissionError:
            Logger.log("e", f"Couldn't start backend_plugin [{self._plugin_id}]: No permission to execute process.")
        except FileNotFoundError:
            Logger.logException("e", f"Unable to find backend_plugin executable [{self._plugin_id}]")
        except BlockingIOError:
            Logger.logException("e", f"Couldn't start backend_plugin [{self._plugin_id}]: Resource is temporarily unavailable")
        except OSError as e:
            Logger.logException("e", f"Couldn't start backend_plugin [{self._plugin_id}]: Operating system is blocking it (antivirus?)")
        return False

    def stop(self) -> bool:
        if not self._process:
            self._is_running = False
            return True  # Nothing to stop

        try:
            self._process.terminate()
            return_code = self._process.wait()
            self._is_running = False
            Logger.log("d", f"Backend_plugin [{self._plugin_id}] was killed. Received return code {return_code}")
            return True
        except PermissionError:
            Logger.log("e", "Unable to kill running engine. Access is denied.")
            return False
