from Cura.Qt.QtApplication import QtApplication
from Cura.Scene.SceneNode import SceneNode
from Cura.Scene.Camera import Camera
from Cura.Scene.Platform import Platform
from Cura.Math.Vector import Vector
from Cura.Math.Matrix import Matrix
from Cura.Resources import Resources

from Cura.Scene.BoxRenderer import BoxRenderer

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
        platform = Platform(root)

        mesh = SceneNode(platform)
        mesh.setMeshData(self.getMeshFileHandler().read(Resources.getPath(Resources.MeshesLocation, 'UltimakerRobot_support.stl'), self.getStorageDevice('local')))
        mesh.rotateByAngleAxis(45, Vector(0, 1, 0))
        mesh.translate(Vector(0, 10, 0))

        box = BoxRenderer(mesh.getBoundingBox(), root)

        try:
            self.getMachineSettings().loadValuesFromFile(Resources.getPath(Resources.SettingsLocation, 'ultimaker2.cfg'))
        except FileNotFoundError:
            pass

        self.getRenderer().setLightPosition(Vector(0, 150, 150))

        camera = Camera('3d', root)
        camera.translate(Vector(0, 150, 150))
        proj = Matrix()
        proj.setPerspective(45, 640/480, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0), Vector(0, 1, 0))

        camera = Camera('left', root)
        camera.translate(Vector(-150, 50, 0))
        proj = Matrix()
        proj.setOrtho(-200, 200, -200, 200, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.lookAt(Vector(0, 50, 0), Vector(0, 1, 0))
        camera.setLocked(True)

        camera = Camera('top', root)
        camera.translate(Vector(0, 150, 0))
        proj = Matrix()
        proj.setOrtho(-200, 200, -200, 200, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.lookAt(Vector(0, 0, 0), Vector(0, 0, -1))
        camera.setLocked(True)

        camera = Camera('front', root)
        camera.translate(Vector(0, 50, 150))
        proj = Matrix()
        proj.setOrtho(-200, 200, -200, 200, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.lookAt(Vector(0, 50, 0), Vector(0, 1, 0))
        camera.setLocked(True)

        self.getController().getScene().setActiveCamera('3d')

        self.setMainQml(os.path.dirname(__file__) + "/Printer.qml")
        self.initializeEngine()

        if self._engine.rootObjects:
            self.exec_()

        self.getMachineSettings().saveValuesToFile(Resources.getStoragePath(Resources.SettingsLocation, 'ultimaker2.cfg'))

    def registerObjects(self, engine):
        pass
