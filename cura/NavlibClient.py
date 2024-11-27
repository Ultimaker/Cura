import pynavlib.pynavlib_interface as pynav
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from cura.PickingPass import PickingPass
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from cura.Scene.OverlayNode import OverlayNode, SceneNode
from UM.Resources import Resources

class NavlibClient(pynav.NavlibNavigationModel):

    def __init__(self, scene, renderer) -> None:
        super().__init__(False, pynav.NavlibOptions.RowMajorOrder)
        self._scene = scene
        self._renderer = renderer
        self._pointer_pick = None
        self._was_pick = False
        self._hit_selection_only = False
        self._picking_pass = None
        self._pivot_node = OverlayNode(node=SceneNode(), image_path=Resources.getPath(Resources.Images, "cor.png"), size=2.5)

    def pick(self, x, y, check_selection = False, radius = 0.):

        if self._picking_pass is None or radius < 0.:
            return None

        step = 0.
        if radius == 0.:
            grid_resolution = 0
        else:
            grid_resolution = 5
            step = (2. * radius) / float(grid_resolution)

        min_depth = 99999.
        result_position = None

        for i in range(grid_resolution + 1):
            for j in range(grid_resolution + 1):

                coord_x = (x - radius) + i * step
                coord_y = (y - radius) + j * step
            
                picked_depth = self._picking_pass.getPickedDepth(coord_x, coord_y)
                max_depth = 16777.215

                if 0. < picked_depth < max_depth:

                    valid_hit = True
                    if check_selection:
                        selection_pass = self._renderer.getRenderPass("selection")
                        picked_object_id = selection_pass.getIdAtPosition(coord_x, coord_y)
                        picked_object = self._scene.findObject(picked_object_id)

                        from UM.Scene.Selection import Selection
                        valid_hit = Selection.isSelected(picked_object)

                    if not valid_hit and grid_resolution > 0.:
                        continue
                    elif not valid_hit and grid_resolution == 0.:
                        return None

                    if picked_depth < min_depth:
                        min_depth = picked_depth
                        result_position = self._picking_pass.getPickedPosition(coord_x, coord_y)
                
        return result_position
    
    def get_pointer_position(self)->pynav.NavlibVector:

        from UM.Qt.QtApplication import QtApplication
        main_window = QtApplication.getInstance().getMainWindow()

        x_n = 2. * main_window._mouse_x / self._scene.getActiveCamera().getViewportWidth() - 1.
        y_n = 2. * main_window._mouse_y / self._scene.getActiveCamera().getViewportHeight() - 1.

        if self.get_is_view_perspective():
            self._was_pick = True
            from cura.Utils.Threading import call_on_qt_thread
            wrapped_pick = call_on_qt_thread(self.pick)
            
            self._pointer_pick = wrapped_pick(x_n, y_n)

            return pynav.NavlibVector(0., 0., 0.)
        else:
            ray = self._scene.getActiveCamera().getRay(x_n, y_n)
            pointer_position = ray.origin + ray.direction

            return pynav.NavlibVector(pointer_position.x, pointer_position.y, pointer_position.z)

    def get_view_extents(self)->pynav.NavlibBox:

        view_width = self._scene.getActiveCamera().getViewportWidth()
        view_height = self._scene.getActiveCamera().getViewportHeight()
        horizontal_zoom = view_width * self._scene.getActiveCamera().getZoomFactor()
        vertical_zoom = view_height * self._scene.getActiveCamera().getZoomFactor()

        pt_min = pynav.NavlibVector(-view_width / 2 - horizontal_zoom, -view_height / 2 - vertical_zoom, -9001)
        pt_max = pynav.NavlibVector(view_width / 2 + horizontal_zoom, view_height / 2 + vertical_zoom, 9001)

        return pynav.NavlibBox(pt_min, pt_max)

    def get_view_frustum(self)->pynav.NavlibFrustum:

        projection_matrix = self._scene.getActiveCamera().getProjectionMatrix()
        half_height = 2. / projection_matrix.getData()[1,1]
        half_width = half_height * (projection_matrix.getData()[1,1] / projection_matrix.getData()[0,0])

        return pynav.NavlibFrustum(-half_width, half_width, -half_height, half_height, 1., 5000.)
    
    def get_is_view_perspective(self)->bool:
        return self._scene.getActiveCamera().isPerspective()

    def get_selection_extents(self)->pynav.NavlibBox:

        from UM.Scene.Selection import Selection
        bounding_box = Selection.getBoundingBox()

        if(bounding_box is not None) :
            pt_min = pynav.NavlibVector(bounding_box.minimum.x, bounding_box.minimum.y, bounding_box.minimum.z)
            pt_max = pynav.NavlibVector(bounding_box.maximum.x, bounding_box.maximum.y, bounding_box.maximum.z)
            return pynav.NavlibBox(pt_min, pt_max)

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
        
        result_bbox = AxisAlignedBox()
        build_volume_bbox = None

        for node in DepthFirstIterator(self._scene.getRoot()):
            node.setCalculateBoundingBox(True)
            if node.__class__.__qualname__ == "CuraSceneNode" :
                result_bbox = result_bbox + node.getBoundingBox()
            elif node.__class__.__qualname__ == "BuildVolume":
                build_volume_bbox = node.getBoundingBox()

        if not result_bbox.isValid():
            result_bbox = build_volume_bbox

        if result_bbox is not None:
            pt_min = pynav.NavlibVector(result_bbox.minimum.x, result_bbox.minimum.y, result_bbox.minimum.z)
            pt_max = pynav.NavlibVector(result_bbox.maximum.x, result_bbox.maximum.y, result_bbox.maximum.z)
            self._scene_center = result_bbox.center
            self._scene_radius = (result_bbox.maximum - self._scene_center).length()
            return pynav.NavlibBox(pt_min, pt_max)
        
    def get_pivot_position(self)->pynav.NavlibVector:
        return pynav.NavlibVector()
    
    def get_hit_look_at(self)->pynav.NavlibVector:
        
        if self._was_pick and self._pointer_pick is not None:
            return pynav.NavlibVector(self._pointer_pick.x, self._pointer_pick.y, self._pointer_pick.z)
        elif self._was_pick and self._pointer_pick is None:
            return None

        from cura.Utils.Threading import call_on_qt_thread
        wrapped_pick = call_on_qt_thread(self.pick)
        picked_position = wrapped_pick(0, 0, self._hit_selection_only, 0.5)

        if picked_position is not None:
            return pynav.NavlibVector(picked_position.x, picked_position.y, picked_position.z)
    
    def get_units_to_meters(self)->float:
        return 0.05
    
    def is_user_pivot(self)->bool:
        return False
    
    def set_camera_matrix(self, matrix : pynav.NavlibMatrix):

        # !!!!!!
        # Hit testing in Orthographic view is not reliable
        # Picking starts in camera position, not on near plane
        # which results in wrong depth values (visible geometry
        # cannot be picked properly) - Workaround needed (camera position offset)
        # !!!!!! 
        if not self.get_is_view_perspective():
            affine = matrix._matrix
            direction = Vector(-affine[0][2], -affine[1][2], -affine[2][2])
            distance = self._scene_center - Vector(affine[0][3], affine[1][3], affine[2][3])

            cos_value = direction.dot(distance.normalized())

            offset = 0.

            if (distance.length() < self._scene_radius) and (cos_value > 0.):
                offset = self._scene_radius
            elif (distance.length() < self._scene_radius) and (cos_value < 0.):
                offset = 2. * self._scene_radius
            elif (distance.length() > self._scene_radius) and (cos_value < 0.):
                offset = 2. * distance.length()

            matrix._matrix[0][3] = matrix._matrix[0][3] - offset * direction.x
            matrix._matrix[1][3] = matrix._matrix[1][3] - offset * direction.y
            matrix._matrix[2][3] = matrix._matrix[2][3] - offset * direction.z    

        transformation = Matrix(data = matrix._matrix)
        self._scene.getActiveCamera().setTransformation(transformation)

        active_camera = self._scene.getActiveCamera()
        if active_camera.isPerspective():
            camera_position = active_camera.getWorldPosition()
            dist = (camera_position - self._pivot_node.getWorldPosition()).length()
            scale = dist / 400.
        else:
            view_width = active_camera.getViewportWidth()
            current_size = view_width + (2. * active_camera.getZoomFactor() * view_width)
            scale = current_size / view_width * 5.

        self._pivot_node.scale(scale)

    def set_view_extents(self, extents: pynav.NavlibBox):
        view_width = self._scene.getActiveCamera().getViewportWidth()
        new_zoom = (extents._min._x + view_width / 2.) / - view_width
        self._scene.getActiveCamera().setZoomFactor(new_zoom)

    def set_hit_selection_only(self, onlySelection : bool):
        self._hit_selection_only = onlySelection

    def set_motion_flag(self, motion : bool):
        if motion:
            width = self._scene.getActiveCamera().getViewportWidth()
            height = self._scene.getActiveCamera().getViewportHeight()
            self._picking_pass = PickingPass(width, height)
            self._renderer.addRenderPass(self._picking_pass)
        else:
            self._was_pick = False
            self._renderer.removeRenderPass(self._picking_pass)
    
    def set_pivot_position(self, position):
        self._pivot_node._target_node.setPosition(position=Vector(position._x, position._y, position._z), transform_space = SceneNode.TransformSpace.World)
    
    def set_pivot_visible(self, visible):
        if visible:
            self._scene.getRoot().addChild(self._pivot_node)
        else:
            self._scene.getRoot().removeChild(self._pivot_node)
        
