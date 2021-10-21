# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
import os
from typing import List, Optional

from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from UM.Qt.QtApplication import QtApplication #For typing.
from UM.Logger import Logger


class SingleInstance:
    def __init__(self, application: QtApplication, files_to_open: Optional[List[str]]) -> None:
        self._application = application
        self._files_to_open = files_to_open

        self._single_instance_server = None

        self._application.getPreferences().addPreference("cura/single_instance_clear_before_load", True)

    # Starts a client that checks for a single instance server and sends the files that need to opened if the server
    # exists. Returns True if the single instance server is found, otherwise False.
    def startClient(self) -> bool:
        Logger.log("i", "Checking for the presence of an ready running Cura instance.")
        single_instance_socket = QLocalSocket(self._application)
        Logger.log("d", "Full single instance server name: %s", single_instance_socket.fullServerName())
        single_instance_socket.connectToServer("ultimaker-cura")
        single_instance_socket.waitForConnected(msecs = 3000)  # wait for 3 seconds

        if single_instance_socket.state() != QLocalSocket.ConnectedState:
            return False

        # We only send the files that need to be opened.
        if not self._files_to_open:
            Logger.log("i", "No file need to be opened, do nothing.")
            return True

        if single_instance_socket.state() == QLocalSocket.ConnectedState:
            Logger.log("i", "Connection has been made to the single-instance Cura socket.")

            # Protocol is one line of JSON terminated with a carriage return.
            # "command" field is required and holds the name of the command to execute.
            # Other fields depend on the command.

            if self._application.getPreferences().getValue("cura/single_instance_clear_before_load"):
                payload = {"command": "clear-all"}
                single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding = "ascii"))

            payload = {"command": "focus"}
            single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding = "ascii"))

            for filename in self._files_to_open:
                payload = {"command": "open", "filePath": os.path.abspath(filename)}
                single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding = "ascii"))

            payload = {"command": "close-connection"}
            single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding = "ascii"))

            single_instance_socket.flush()
            single_instance_socket.waitForDisconnected()
        return True

    def startServer(self) -> None:
        self._single_instance_server = QLocalServer()
        if self._single_instance_server:
            self._single_instance_server.newConnection.connect(self._onClientConnected)
            self._single_instance_server.listen("ultimaker-cura")
        else:
            Logger.log("e", "Single instance server was not created.")

    def _onClientConnected(self) -> None:
        Logger.log("i", "New connection received on our single-instance server")
        connection = None #type: Optional[QLocalSocket]
        if self._single_instance_server:
            connection = self._single_instance_server.nextPendingConnection()

        if connection is not None:
            connection.readyRead.connect(lambda c = connection: self.__readCommands(c))

    def __readCommands(self, connection: QLocalSocket) -> None:
        line = connection.readLine()
        while len(line) != 0:    # There is also a .canReadLine()
            try:
                payload = json.loads(str(line, encoding = "ascii").strip())
                command = payload["command"]

                # Command: Remove all models from the build plate.
                if command == "clear-all":
                    self._application.callLater(lambda: self._application.deleteAll())

                # Command: Load a model or project file
                elif command == "open":
                    self._application.callLater(lambda f = payload["filePath"]: self._application._openFile(f))

                # Command: Activate the window and bring it to the top.
                elif command == "focus":
                    # Operating systems these days prevent windows from moving around by themselves.
                    # 'alert' or flashing the icon in the taskbar is the best thing we do now.
                    main_window = self._application.getMainWindow()
                    if main_window is not None:
                        self._application.callLater(lambda: main_window.alert(0)) # type: ignore # I don't know why MyPy complains here

                # Command: Close the socket connection. We're done.
                elif command == "close-connection":
                    connection.close()

                else:
                    Logger.log("w", "Received an unrecognized command " + str(command))
            except json.decoder.JSONDecodeError as ex:
                Logger.log("w", "Unable to parse JSON command '%s': %s", line, repr(ex))
            line = connection.readLine()
