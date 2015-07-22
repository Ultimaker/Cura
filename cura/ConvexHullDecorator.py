from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Application import Application

class ConvexHullDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._convex_hull = None
        
        # In case of printing all at once this is the same as the convex hull. For one at the time this is the area without the head.
        self._convex_hull_boundary = None 
        
        # In case of printing all at once this is the same as the convex hull. For one at the time this is area with full head
        self._convex_hull_head = None
        
        self._convex_hull_node = None
        self._convex_hull_job = None
        settings = Application.getInstance().getActiveMachine()
        print_sequence_setting = settings.getSettingByKey("print_sequence")
        if print_sequence_setting:
            print_sequence_setting.valueChanged.connect(self._onPrintSequenceSettingChanged)
            
    def _onPrintSequenceSettingChanged(self, setting):
        if self._convex_hull_job:
            self._convex_hull_job.cancel()
        self.setConvexHull(None)
        if self._convex_hull_node:
            self._convex_hull_node.setParent(None)
            self._convex_hull_node = None
    
    def getConvexHull(self):
        return self._convex_hull
    
    def getConvexHullHead(self):
        if not self._convex_hull_head:
            return self.getConvexHull()
        return self._convex_hull_head
    
    def getConvexHullBoundary(self):
        if not self._convex_hull_boundary:
            return self.getConvexHull()
        return self._convex_hull_boundary
    
    def setConvexHullBoundary(self, hull):
        self._convex_hull_boundary = hull
        
    def setConvexHullHead(self, hull):
        self._convex_hull_head = hull
    
    def setConvexHull(self, hull):
        self._convex_hull = hull
    
    def getConvexHullJob(self):
        return self._convex_hull_job
    
    def setConvexHullJob(self, job):
        self._convex_hull_job = job
    
    def getConvexHullNode(self):
        return self._convex_hull_node
    
    def setConvexHullNode(self, node):
        self._convex_hull_node = node
            
    