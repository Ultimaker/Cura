from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

class ConvexHullDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._convex_hull = None
        self._convex_hull_node = None
        self._convex_hull_job = None
        
    def getConvexHull(self):
        return self._convex_hull
    
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
            
    