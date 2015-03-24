from UM.Operations.Operation import Operation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.GroupedOperation import GroupedOperation

##  A specialised operation designed specifically to modify the previous operation.
class PlatformPhysicsOperation(Operation):
    def __init__(self, node, translation):
        super().__init__()
        self._node = node
        self._transform = node.getLocalTransformation()
        self._position = node.getPosition() + translation
        self._always_merge = True

    def undo(self):
        self._node.setLocalTransformation(self._transform)

    def redo(self):
        self._node.setPosition(self._position)

    def mergeWith(self, other):
        group = GroupedOperation()

        group.addOperation(self)
        group.addOperation(other)

        return group

    def __repr__(self):
        return 'PlatformPhysicsOperation(t = {0})'.format(self._position)
