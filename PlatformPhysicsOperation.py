from UM.Operations.Operation import Operation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.TranslateOperation import TranslateOperation

##  A specialised operation designed specifically to modify the previous operation.
class PlatformPhysicsOperation(Operation):
    def __init__(self, node, translation):
        super().__init__()
        self._node = node
        self._translation = translation

    def undo(self):
        pass

    def redo(self):
        pass

    def mergeWith(self, other):
        if type(other) is AddSceneNodeOperation:
            other._node.translate(self._translation)
            return other
        elif type(other) is TranslateOperation:
            other._translation += self._translation
            return other
        else:
            return False

