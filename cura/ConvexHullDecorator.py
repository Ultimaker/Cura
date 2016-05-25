from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Application import Application


##  The convex hull decorator is a scene node decorator that adds the convex hull functionality to a scene node.
#   If a scene node has a convex hull decorator, it will have a shadow in which other objects can not be printed.
class ConvexHullDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._convex_hull = None

        # In case of printing all at once this is the same as the convex hull.
        # For one at the time this is the area without the head.
        self._convex_hull_boundary = None 

        # In case of printing all at once this is the same as the convex hull.
        # For one at the time this is area with intersection of mirrored head
        self._convex_hull_head = None

        # In case of printing all at once this is the same as the convex hull.
        # For one at the time this is area with intersection of full head
        self._convex_hull_head_full = None

        self._convex_hull_node = None
        self._convex_hull_job = None

        # Keep track of the previous parent so we can clear its convex hull when the object is reparented
        self._parent_node = None

        self._profile = None
        #Application.getInstance().getMachineManager().activeProfileChanged.connect(self._onActiveProfileChanged)
        #Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onActiveMachineInstanceChanged)
        #self._onActiveProfileChanged()

    def setNode(self, node):
        super().setNode(node)
        self._parent_node = node.getParent()
        node.parentChanged.connect(self._onParentChanged)

    ## Force that a new (empty) object is created upon copy.
    def __deepcopy__(self, memo):
        copy = ConvexHullDecorator()
        return copy

    ##  Get the unmodified convex hull of the node
    def getConvexHull(self):
        return self._convex_hull

    ##  Get the convex hull of the node with the full head size
    def getConvexHullHeadFull(self):
        if not self._convex_hull_head_full:
            return self.getConvexHull()
        return self._convex_hull_head_full

    ##  Get convex hull of the object + head size
    #   In case of printing all at once this is the same as the convex hull.
    #   For one at the time this is area with intersection of mirrored head
    def getConvexHullHead(self):
        if not self._convex_hull_head:
            return self.getConvexHull()
        return self._convex_hull_head

    ##  Get convex hull of the node
    #   In case of printing all at once this is the same as the convex hull.
    #   For one at the time this is the area without the head.
    def getConvexHullBoundary(self):
        if not self._convex_hull_boundary:
            return self.getConvexHull()
        return self._convex_hull_boundary

    def setConvexHullBoundary(self, hull):
        self._convex_hull_boundary = hull

    def setConvexHullHeadFull(self, hull):
        self._convex_hull_head_full = hull

    def setConvexHullHead(self, hull):
        self._convex_hull_head = hull

    def setConvexHull(self, hull):
        self._convex_hull = hull
        if not hull and self._convex_hull_node:
            self._convex_hull_node.setParent(None)
            self._convex_hull_node = None

    def getConvexHullJob(self):
        return self._convex_hull_job

    def setConvexHullJob(self, job):
        self._convex_hull_job = job

    def getConvexHullNode(self):
        return self._convex_hull_node

    def setConvexHullNode(self, node):
        self._convex_hull_node = node

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._onSettingValueChanged)

        self._profile = Application.getInstance().getMachineManager().getWorkingProfile()

        if self._profile:
            self._profile.settingValueChanged.connect(self._onSettingValueChanged)

    def _onActiveMachineInstanceChanged(self):
        if self._convex_hull_job:
            self._convex_hull_job.cancel()
        self.setConvexHull(None)

    def _onSettingValueChanged(self, setting):
        if setting == "print_sequence":
            if self._convex_hull_job:
                self._convex_hull_job.cancel()
            self.setConvexHull(None)

    def _onParentChanged(self, node):
        # Force updating the convex hull of the parent group if the object is in a group
        if self._parent_node and self._parent_node.callDecoration("isGroup"):
            self._parent_node.callDecoration("setConvexHull", None)
        self._parent_node = self.getNode().getParent()
