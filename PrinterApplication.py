from Cura.Qt.QtApplication import QtApplication
from Cura.Scene.SceneObject import SceneObject

class PrinterApplication(QtApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        self._plugin_registry.loadPlugins({ "type": "StorageDevice" })
        self._plugin_registry.loadPlugins({ "type": "View" })
        self._plugin_registry.loadPlugins({ "type": "MeshHandler" })
        
        self.getController().setActiveView("MeshView")

        root = self.getController().getScene().getRoot()
        mesh = SceneObject()
        mesh.setMeshData(self.getMeshFileHandler().read("plugins/STLReader/simpleTestCube.stl",self.getStorageDevice('local')))
        root.addChild(mesh)

        self.setMainQml("printer/Printer.qml")
        self.initializeEngine()

        if self._engine.rootObjects:
            self.exec_()

    def registerObjects(self, engine):
        pass
