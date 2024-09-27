import pynavlib.pynavlib_interface as pynav
from UM.Math.Matrix import Matrix
from cura.PickingPass import PickingPass

class NavlibClient(pynav.NavlibNavigationModel):

    def __init__(self, scene, renderer) -> None:
        super().__init__(True, pynav.NavlibOptions.RowMajorOrder)
        self._scene = scene
        self._renderer = renderer
        self._pointer_pick = None
        self._was_pick = False
        self._hit_selection_only = False
        self._picking_pass = None

    def pick(self, x, y):
        if self._picking_pass is None:
            return None, None

        picked_depth = self._picking_pass.getPickedDepth(x, y)

        max_depth = 16777.215

        if 0. < picked_depth < max_depth:
            selection_pass = self._renderer.getRenderPass("selection")
            picked_object_id = selection_pass.getIdAtPosition(x, y)
            return self._picking_pass.getPickedPosition(x, y), picked_object_id
        
        return None, None
    
    def get_pointer_position(self)->pynav.NavlibVector:

        from UM.Qt.QtApplication import QtApplication
        mw = QtApplication.getInstance().getMainWindow()

        x_n = 2. * mw._mouse_x / self._scene.getActiveCamera().getViewportWidth() - 1.
        y_n = 2. * mw._mouse_y / self._scene.getActiveCamera().getViewportHeight() - 1.

        if self.get_is_view_perspective():
            self._was_pick = True
            from cura.Utils.Threading import call_on_qt_thread
            wrapped_pick = call_on_qt_thread(self.pick)
            
            self._pointer_pick, id = wrapped_pick(x_n, y_n)

            return pynav.NavlibVector(0., 0., 0.)
        else:
            ray = self._scene.getActiveCamera().getRay(x_n, y_n)
            pointer_position = ray.origin + ray.direction

            return pynav.NavlibVector(pointer_position.x, pointer_position.y, pointer_position.z)

    def get_view_extents(self)->pynav.NavlibBox:
        projectionMatrix = self._scene.getActiveCamera().getProjectionMatrix()
        
        pt_min = pynav.NavlibVector(projectionMatrix._left, projectionMatrix._bottom, projectionMatrix._near)
        pt_max = pynav.NavlibVector(projectionMatrix._right, projectionMatrix._top, projectionMatrix._far)

        return pynav.NavlibBox(pt_min, pt_max)

    def get_view_frustum(self)->pynav.NavlibFrustum:

        projectionMatrix = self._scene.getActiveCamera().getProjectionMatrix()
        halfHeight = 2. / projectionMatrix.getData()[1,1]
        halfWidth = halfHeight * (projectionMatrix.getData()[1,1] / projectionMatrix.getData()[0,0])

        return pynav.NavlibFrustum(-halfWidth, halfWidth, -halfHeight, halfHeight, projectionMatrix._near, 100. * projectionMatrix._far)
    
    def get_is_view_perspective(self)->bool:
        return self._scene.getActiveCamera().isPerspective()
    
    def get_selection_extents(self)->pynav.NavlibBox:

        from UM.Scene.Selection import Selection
        bounding_box = Selection.getBoundingBox()

        if(bounding_box is not None) :
            pt_min = pynav.NavlibVector(bounding_box.minimum.x, bounding_box.minimum.y, bounding_box.minimum.z)
            pt_max = pynav.NavlibVector(bounding_box.maximum.x, bounding_box.maximum.y, bounding_box.maximum.z)
            return pynav.NavlibBox(pt_min, pt_max)
        pass
    
    def get_selection_transform(self)->pynav.NavlibMatrix:
        return pynav.NavlibMatrix()
    
    def get_is_selection_empty(self)->bool:
        from UM.Scene.Selection import Selection
        return not Selection.hasSelection()
    
    def get_pivot_visible(self)->bool:
        return False
    
    def get_camera_matrix(self)->pynav.NavlibMatrix:

        transformation = self._scene.getActiveCamera().getLocalTransformation()
        
        return pynav.NavlibMatrix([[transformation.at(0, 0), transformation.at(0, 1), transformation.at(0, 2), transformation.at(0, 3)],
                                   [transformation.at(1, 0), transformation.at(1, 1), transformation.at(1, 2), transformation.at(1, 3)],
                                   [transformation.at(2, 0), transformation.at(2, 1), transformation.at(2, 2), transformation.at(2, 3)],
                                   [transformation.at(3, 0), transformation.at(3, 1), transformation.at(3, 2), transformation.at(3, 3)]])

    def get_coordinate_system(self)->pynav.NavlibMatrix:
        return pynav.NavlibMatrix()
    
    def get_front_view(self)->pynav.NavlibMatrix:
        return pynav.NavlibMatrix()
    
    def get_model_extents(self)->pynav.NavlibBox:

        # Why does running getCalculateBoundingBox on scene
        # root always takes into accont all of the objects, no matter
        # of their __calculate_aabb settings?
        from UM.Scene.SceneNode import SceneNode

        objectsTreeRoot = SceneNode()
        objectsTreeRoot.setCalculateBoundingBox(True)

        for node in self._scene.getRoot().getChildren() :
            if node.__class__.__qualname__ == "CuraSceneNode" :
                objectsTreeRoot.addChild(node)

        for node in objectsTreeRoot.getAllChildren():
            node.setCalculateBoundingBox(True)

        if objectsTreeRoot.getAllChildren().__len__() > 0 :
            boundingBox = objectsTreeRoot.getBoundingBox()
        else :
            self._scene.getRoot().setCalculateBoundingBox(True)
            boundingBox = self._scene.getRoot().getBoundingBox()

        if boundingBox is not None:
            pt_min = pynav.NavlibVector(boundingBox.minimum.x, boundingBox.minimum.y, boundingBox.minimum.z)
            pt_max = pynav.NavlibVector(boundingBox.maximum.x, boundingBox.maximum.y, boundingBox.maximum.z)
            return pynav.NavlibBox(pt_min, pt_max)
        
    def get_pivot_position(self)->pynav.NavlibVector:
        return pynav.NavlibVector()
    
    def get_hit_look_at(self)->pynav.NavlibVector:
        
        # !!!!!!
        # Hit testing in Orthographic view is not reliable
        # Picking starts in camera position, not on near plane
        # which results in wrong depth values (visible geometry
        # cannot be picked properly)
        # !!!!!! 

        if self._was_pick and self._pointer_pick is not None:
            return pynav.NavlibVector(self._pointer_pick.x, self._pointer_pick.y, self._pointer_pick.z)
        elif self._was_pick and self._pointer_pick is None:
            return None

        from cura.Utils.Threading import call_on_qt_thread
        
        # Iterate over the grid of given aperture to find
        # the depth- wise closest position 

        wrapped_pick = call_on_qt_thread(self.pick)
        picked_position, picked_object_id = wrapped_pick(0, 0)

        if self._hit_selection_only:
            picked_object = self._scene.findObject(picked_object_id)
            from UM.Scene.Selection import Selection
            if not Selection.isSelected(picked_object):
                return None

        # Return the closest point

        if picked_position is not None:
            return pynav.NavlibVector(picked_position.x, picked_position.y, picked_position.z)
        
        pass
    
    def get_units_to_meters(self)->float:
        return 0.05
    
    def is_user_pivot(self)->bool:
        return False
    
    def set_camera_matrix(self, matrix : pynav.NavlibMatrix):
        transformation = Matrix(data = matrix._matrix)
        self._scene.getActiveCamera().setTransformation(transformation)

    def set_view_extents(self, extents: pynav.NavlibBox):
        self._scene.getActiveCamera().getProjectionMatrix().setOrtho(extents._min._x, extents._max._x, 
                                                                     extents._min._y, extents._max._y, 
                                                                     extents._min._z, extents._max._z)

    def set_hit_selection_only(self, onlySelection : bool):
        self._hit_selection_only = onlySelection
        pass

    def set_active_command(self, commandId : str):
        pass

    def set_motion_flag(self, motion : bool):
        if motion:
            width = self._scene.getActiveCamera().getViewportWidth()
            height = self._scene.getActiveCamera().getViewportHeight()
            self._picking_pass = PickingPass(width, height)
            self._renderer.addRenderPass(self._picking_pass)
        else:
            self._was_pick = False
            self._renderer.removeRenderPass(self._picking_pass)
            