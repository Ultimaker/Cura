from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Scene.Selection import Selection


class BuildPlateDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._build_plate_number = -1

    def setBuildPlateNumber(self, nr):
        self._build_plate_number = nr
        # self.getNode().childrenChanged.connect(self._onChildrenChanged)

    def getBuildPlateNumber(self):
        return self._build_plate_number

    # def setNode(self, node):
    #     super().setNode(node)
    #     self.getNode().childrenChanged.connect(self._onChildrenChanged)

    # def _onChildrenChanged(self, node):
    #     if not self.getNode().hasChildren():
    #         # A group that no longer has children may remove itself from the scene
    #         self._old_parent = self.getNode().getParent()
    #         self.getNode().setParent(None)
    #         Selection.remove(self.getNode())
    #     else:
    #         # A group that has removed itself from the scene because it had no children may add itself back to the scene when a child is added to it
    #         if not self.getNode().getParent() and self._old_parent:
    #             self.getNode().setParent(self._old_parent)
    #             self._old_parent = None

    def __deepcopy__(self, memo):
        return BuildPlateDecorator()
