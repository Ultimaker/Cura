from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Preferences import Preferences
import threading

import subprocess

CMD_REQUEST_IDENTIFIER = 0x00100000;
CMD_IDENTIFIER_REPLY = 0x00100001;
CMD_REQUEST_VERSION = 0x00100002;
CMD_VERSION_REPLY = 0x00100003;

CMD_SETTING = 0x00100004;
CMD_MATRIX = 0x00300002;
CMD_OBJECT_COUNT = 0x00300003;
CMD_OBJECT_LIST = 0x00200000;
CMD_MESH_LIST = 0x00200001;
CMD_VERTEX_LIST = 0x00200002;
CMD_NORMAL_LIST = 0x00200003;
CMD_PROCESS_MESH = 0x00300000;

CMD_PROGRESS_REPORT = 0x00300001;
CMD_OBJECT_PRINT_TIME = 0x00300004;
CMD_OBJECT_PRINT_MATERIAL = 0x00300005;
CMD_LAYER_INFO = 0x00300007;
CMD_POLYGON = 0x00300006;

class CuraEngineBackend(Backend):
    def __init__(self):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        self._command_handlers[CMD_IDENTIFIER_REPLY] = self._identifierReply
        self._command_handlers[CMD_OBJECT_PRINT_TIME] = self._printTimeReply

    def startEngine(self):
        super().startEngine()

    def getEngineCommand(self):
        return [Preferences.getPreference("BackendLocation"), '--socket', str(self._socket_thread.getPort()), '--command-socket']

    def _onSceneChanged(self, source):
        if (type(source) is not SceneNode) or (source is self._scene.getRoot()):
            return

        objects = []
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                objects.append(node)

        self._socket_thread.sendCommand(CMD_OBJECT_COUNT, len(objects))

        for object in objects:
            print('sending object', object)
            self._socket_thread.sendCommand(CMD_OBJECT_LIST, 1)

            meshData = object.getMeshData()
            self._socket_thread.sendCommand(CMD_MESH_LIST, 1)
            self._socket_thread.sendCommand(CMD_VERTEX_LIST, meshData.getVerticesAsByteArray())

        self._socket_thread.sendCommand(CMD_PROCESS_MESH)

    def _identifierReply(self, data):
        print(data)

    def _printTimeReply(self, data):
        print(data)
