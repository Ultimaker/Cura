from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Preferences import Preferences


##  Keep track of all objects in the project
class ObjectsModel(ListModel):
    def __init__(self):
        super().__init__()

        Application.getInstance().getController().getScene().sceneChanged.connect(self._update)
        Preferences.getInstance().preferenceChanged.connect(self._update)

        self._build_plate_number = -1

    def setActiveBuildPlate(self, nr):
        self._build_plate_number = nr
        self._update()

    def _update(self, *args):
        nodes = []
        filter_current_build_plate = Preferences.getInstance().getValue("view/filter_current_build_plate")
        active_build_plate_number = self._build_plate_number
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if not issubclass(type(node), SceneNode) or (not node.getMeshData() and not node.callDecoration("getLayerData")):
                continue
            if not node.callDecoration("isSliceable"):
                continue
            node_build_plate_number = node.callDecoration("getBuildPlateNumber")
            if filter_current_build_plate and node_build_plate_number != active_build_plate_number:
                continue
            nodes.append({
                "name": node.getName(),
                "isSelected": Selection.isSelected(node),
                "isOutsideBuildArea": node.isOutsideBuildArea(),
                "buildPlateNumber": node_build_plate_number,
                "node": node
            })
        nodes = sorted(nodes, key=lambda n: n["name"])
        self.setItems(nodes)

        self.itemsChanged.emit()

    @staticmethod
    def createObjectsModel():
        return ObjectsModel()
