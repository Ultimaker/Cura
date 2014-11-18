from Cura.Qt.QtApplication import QtApplication
from Cura.Scene.SceneObject import SceneObject
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
        self.getController().setActiveTool("TransformTool")

        root = self.getController().getScene().getRoot()
        mesh = SceneObject(root)
        mesh.setMeshData(self.getMeshFileHandler().read("plugins/FileHandlers/STLReader/simpleTestCube.stl",self.getStorageDevice('local')))

        camera = Camera(root)
        camera.translate(Vector(0, 0, 5))
        self.getController().getScene().setActiveCamera(camera)

        self.log('i',"Application started")

        self.setMainQml(os.path.dirname(__file__) + "/Printer.qml")
        self.initializeEngine()

        if self._engine.rootObjects:
            self.exec_()

    def registerObjects(self, engine):
        pass
