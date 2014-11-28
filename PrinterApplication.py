from Cura.Qt.QtApplication import QtApplication
from Cura.Scene.SceneNode import SceneNode
from Cura.Scene.Camera import Camera
from Cura.Math.Vector import Vector

import os.path

class PrinterApplication(QtApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        self._plugin_registry.loadPlugins({ "type": "Logger"})
        self._plugin_registry.loadPlugins({ "type": "StorageDevice" })
        self._plugin_registry.loadPlugins({ "type": "View" })
        self._plugin_registry.loadPlugins({ "type": "MeshHandler" })
        self._plugin_registry.loadPlugins({ "type": "Tool" })
        
        self.getController().setActiveView("MeshView")

        root = self.getController().getScene().getRoot()
        mesh = SceneNode(root)
        mesh.setMeshData(self.getMeshFileHandler().read("plugins/FileHandlers/STLReader/simpleTestCube.stl",self.getStorageDevice('local')))

        camera = Camera('3d', root)
        camera.translate(Vector(0, 5, 5))
        camera.rotateByAngleAxis(45, Vector(1, 0, 0))

        camera = Camera('left', root)
        camera.translate(Vector(5, 0, 0))
        camera.rotateByAngleAxis(-90, Vector(0, 1, 0))
        camera.setLocked(True)

        self.getController().getScene().setActiveCamera('3d')

        self.log('i',"Application started")

        self.setMainQml(os.path.dirname(__file__) + "/Printer.qml")
        self.initializeEngine()

        if self._engine.rootObjects:
            self.exec_()

    def registerObjects(self, engine):
        pass
