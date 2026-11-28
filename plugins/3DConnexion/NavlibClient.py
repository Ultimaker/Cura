# Copyright (c) 2025 3Dconnexion, UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import platform # Added
import logging # Added

from typing import Optional
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from cura.PickingPass import PickingPass
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Scene import Scene
from UM.Resources import Resources
from UM.Tool import Tool
from UM.View.Renderer import Renderer
from .OverlayNode import OverlayNode
from .LinuxSpacenavClient import LinuxSpacenavClient, SPNAV_EVENT_MOTION, SPNAV_EVENT_BUTTON # Added

import pynavlib.pynavlib_interface as pynav

logger = logging.getLogger(__name__) # Added


class NavlibClient(pynav.NavlibNavigationModel, Tool):

    def __init__(self, scene: Scene, renderer: Renderer) -> None:
        self._platform_system = platform.system()
        self._linux_spacenav_client: Optional[LinuxSpacenavClient] = None
        self._scene = scene
        self._renderer = renderer
        self._pointer_pick = None # Retain for pick()
        self._was_pick = False # Retain for pick() / get_hit_look_at()
        self._hit_selection_only = False # Retain for pick() / get_hit_look_at()
        self._picking_pass = None # Retain for pick() / set_motion_flag()
        # Pivot node might be useful on Linux too, initialize it.
        self._pivot_node = OverlayNode(node=SceneNode(), image_path=Resources.getPath(Resources.Images, "cor.png"), size=2.5)
        self._scene_center = Vector() # Used in set_camera_matrix, ensure it exists
        self._scene_radius = 1.0    # Used in set_camera_matrix, ensure it exists


        if self._platform_system == "Linux":
            # Tool.__init__(self) # Explicitly NOT calling Tool.__init__ for Linux as per current subtask
            logger.info("Attempting to initialize LinuxSpacenavClient for Linux platform.")
            # Essential scene/renderer setup, even if not a full Tool
            # self._scene = scene # Already assigned above
            # self._renderer = renderer # Already assigned above
            try:
                self._linux_spacenav_client = LinuxSpacenavClient()
                if self._linux_spacenav_client.available:
                    if not self._linux_spacenav_client.open():
                        logger.warning("Failed to open connection via LinuxSpacenavClient.")
                        self._linux_spacenav_client = None
                    else:
                        logger.info("LinuxSpacenavClient initialized and opened successfully.")
                        # self.enable_navigation(True) # This is a pynavlib call, handle equivalent in set_motion_flag
                else:
                    logger.warning("LinuxSpacenavClient is not available (library not found or functions missing).")
                    self._linux_spacenav_client = None
            except Exception as e:
                logger.error(f"Exception during LinuxSpacenavClient initialization: {e}")
                self._linux_spacenav_client = None
        else:
            pynav.NavlibNavigationModel.__init__(self, False, pynav.NavlibOptions.RowMajorOrder)
            Tool.__init__(self)
            self.put_profile_hint("UltiMaker Cura")
            self.enable_navigation(True)

    def event(self, event):
        if self._platform_system == "Linux" and self._linux_spacenav_client:
            self._update_linux_events()
            # For Linux, we might not want to call super().event() if it's Tool's base event,
            # unless specific Tool event handling is desired independent of spacenav.
            # For now, let's assume spacenav events are primary for this tool on Linux.
            return True # Indicate event was handled
        
        # Original event handling for non-Linux or if Linux client failed
        if hasattr(super(), "event"): # pynav.NavlibNavigationModel does not have event, Tool does.
             return super().event(event) # Call Tool.event
        return False


    def _update_linux_events(self):
        if not self._linux_spacenav_client:
            return

        while True:
            event_data = self._linux_spacenav_client.poll_event()
            if event_data is None:
                break # No more events

            if event_data.type == SPNAV_EVENT_MOTION:
                logger.info(f"Linux Motion Event: t({event_data.motion.x}, {event_data.motion.y}, {event_data.motion.z}) "
                            f"r({event_data.motion.rx}, {event_data.motion.ry}, {event_data.motion.rz})")
                
                # Placeholder: Construct a simple transformation matrix
                # This needs significant refinement for actual camera control.
                # Scaling factors are arbitrary for now.
                scale_t = 0.01 
                scale_r = 0.001

                # Create a new matrix for delta transformation
                delta_matrix = Matrix()
                # Apply translation (Todo: map to camera coordinates correctly)
                delta_matrix.translate(Vector(event_data.motion.x * scale_t, 
                                              -event_data.motion.y * scale_t, # Inverting Y for typical screen coords
                                              event_data.motion.z * scale_t))
                
                # Apply rotations (Todo: map to camera axes correctly)
                # For now, just using some fixed axes for rotation demonstration.
                # These rotations should be composed correctly.
                # rx -> pitch, ry -> yaw, rz -> roll (example mapping)
                if abs(event_data.motion.rx) > 10 : # Some threshold
                    delta_matrix.rotateByAngle(Vector(1,0,0), event_data.motion.rx * scale_r)
                if abs(event_data.motion.ry) > 10:
                    delta_matrix.rotateByAngle(Vector(0,1,0), event_data.motion.ry * scale_r)
                if abs(event_data.motion.rz) > 10:
                    delta_matrix.rotateByAngle(Vector(0,0,1), event_data.motion.rz * scale_r)

                current_cam_matrix = self._scene.getActiveCamera().getLocalTransformation()
                new_cam_matrix = current_cam_matrix.multiply(delta_matrix) # Apply delta
                
                self.set_camera_matrix(new_cam_matrix)

            elif event_data.type == SPNAV_EVENT_BUTTON:
                logger.info(f"Linux Button Event: press={event_data.button.press}, bnum={event_data.button.bnum}")


    def pick(self, x: float, y: float, check_selection: bool = False, radius: float = 0.) -> Optional[Vector]:

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

    def get_pointer_position(self) -> Optional["pynav.NavlibVector"]: # Adjusted return type for Linux
        if self._platform_system == "Linux":
            # Not directly applicable or available from libspnav.
            # Could potentially use mouse position if needed for some hybrid mode.
            logger.debug("get_pointer_position called on Linux, returning None.")
            return None

        from UM.Qt.QtApplication import QtApplication
        main_window = QtApplication.getInstance().getMainWindow()

        x_n = 2. * main_window._mouse_x / main_window.width() - 1.
        y_n = 2. * main_window._mouse_y / main_window.height() - 1.

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

    def get_view_extents(self) -> Optional["pynav.NavlibBox"]: # Adjusted return type for Linux
        if self._platform_system == "Linux":
            logger.debug("get_view_extents called on Linux, returning None (pynav.NavlibBox specific).")
            # Could return a dict if some generic extent info is needed
            return None

        view_width = self._scene.getActiveCamera().getViewportWidth()
        view_height = self._scene.getActiveCamera().getViewportHeight()
        horizontal_zoom = view_width * self._scene.getActiveCamera().getZoomFactor()
        vertical_zoom = view_height * self._scene.getActiveCamera().getZoomFactor()

        pt_min = pynav.NavlibVector(-view_width / 2 - horizontal_zoom, -view_height / 2 - vertical_zoom, -9001)
        pt_max = pynav.NavlibVector(view_width / 2 + horizontal_zoom, view_height / 2 + vertical_zoom, 9001)

        return pynav.NavlibBox(pt_min, pt_max)

    def get_view_frustum(self) -> Optional["pynav.NavlibFrustum"]: # Adjusted return type for Linux
        if self._platform_system == "Linux":
            logger.debug("get_view_frustum called on Linux, returning None (pynav.NavlibFrustum specific).")
            return None

        projection_matrix = self._scene.getActiveCamera().getProjectionMatrix()
        half_height = 2. / projection_matrix.getData()[1,1]
        half_width = half_height * (projection_matrix.getData()[1,1] / projection_matrix.getData()[0,0])

        return pynav.NavlibFrustum(-half_width, half_width, -half_height, half_height, 1., 5000.)

    def get_is_view_perspective(self) -> bool:
        # This method can be common if _scene and getActiveCamera() are available.
        return self._scene.getActiveCamera().isPerspective()

    def get_selection_extents(self) -> Optional["pynav.NavlibBox"]: # Adjusted return type for Linux
        if self._platform_system == "Linux":
            logger.debug("get_selection_extents called on Linux, returning None (pynav.NavlibBox specific).")
            # Could try to implement similar logic to below and return a dict if needed.
            return None

        from UM.Scene.Selection import Selection
        bounding_box = Selection.getBoundingBox()

        if(bounding_box is not None) :
            pt_min = pynav.NavlibVector(bounding_box.minimum.x, bounding_box.minimum.y, bounding_box.minimum.z)
            pt_max = pynav.NavlibVector(bounding_box.maximum.x, bounding_box.maximum.y, bounding_box.maximum.z)
            return pynav.NavlibBox(pt_min, pt_max)

    def get_selection_transform(self) -> Optional["pynav.NavlibMatrix"]: # Adjusted return type for Linux
        if self._platform_system == "Linux":
            logger.debug("get_selection_transform called on Linux, returning None (pynav.NavlibMatrix specific).")
            return None # No direct equivalent from libspnav
        return pynav.NavlibMatrix()

    def get_is_selection_empty(self) -> bool:
        # This method can be common if Selection is accessible.
        from UM.Scene.Selection import Selection
        return not Selection.hasSelection()

    def get_pivot_visible(self) -> bool:
        if self._platform_system == "Linux":
            # If we want to use the pivot node on Linux, this needs proper implementation
            return self._pivot_node.isEnabled() # Assuming OverlayNode has isEnabled or similar
        return False # Original behavior for non-Linux for now

    def get_camera_matrix(self) -> "pynav.NavlibMatrix" or Matrix: # Adjusted return type
        if self._platform_system == "Linux":
            # Return UM.Math.Matrix directly for Linux
            return self._scene.getActiveCamera().getLocalTransformation()

        transformation = self._scene.getActiveCamera().getLocalTransformation()

        return pynav.NavlibMatrix([[transformation.at(0, 0), transformation.at(0, 1), transformation.at(0, 2), transformation.at(0, 3)],
                                   [transformation.at(1, 0), transformation.at(1, 1), transformation.at(1, 2), transformation.at(1, 3)],
                                   [transformation.at(2, 0), transformation.at(2, 1), transformation.at(2, 2), transformation.at(2, 3)],
                                   [transformation.at(3, 0), transformation.at(3, 1), transformation.at(3, 2), transformation.at(3, 3)]])

    def get_coordinate_system(self) -> Optional["pynav.NavlibMatrix"]: # Adjusted
        if self._platform_system == "Linux":
            logger.debug("get_coordinate_system called on Linux, returning None.")
            return None
        return pynav.NavlibMatrix()

    def get_front_view(self) -> Optional["pynav.NavlibMatrix"]: # Adjusted
        if self._platform_system == "Linux":
            logger.debug("get_front_view called on Linux, returning None.")
            return None
        return pynav.NavlibMatrix()

    def get_model_extents(self) -> Optional["pynav.NavlibBox"]: # Adjusted
        if self._platform_system == "Linux":
            # Could implement the logic below and return a dict {min: [x,y,z], max: [x,y,z]}
            logger.debug("get_model_extents called on Linux, returning None (pynav.NavlibBox specific).")
            return None

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

    def get_pivot_position(self) -> Optional["pynav.NavlibVector"]: # Adjusted
        if self._platform_system == "Linux":
            # If using pivot node: return Vector(self._pivot_node.getPosition().x, ...)
            logger.debug("get_pivot_position called on Linux, returning None.")
            return None
        return pynav.NavlibVector()

    def get_hit_look_at(self) -> Optional["pynav.NavlibVector"]: # Adjusted
        if self._platform_system == "Linux":
            logger.debug("get_hit_look_at called on Linux, returning None (relies on picking).")
            return None

        if self._was_pick and self._pointer_pick is not None:
            return pynav.NavlibVector(self._pointer_pick.x, self._pointer_pick.y, self._pointer_pick.z)
        elif self._was_pick and self._pointer_pick is None:
            return None

        from cura.Utils.Threading import call_on_qt_thread
        wrapped_pick = call_on_qt_thread(self.pick)
        picked_position = wrapped_pick(0, 0, self._hit_selection_only, 0.5)

        if picked_position is not None:
            return pynav.NavlibVector(picked_position.x, picked_position.y, picked_position.z)

    def get_units_to_meters(self) -> float:
        if self._platform_system == "Linux":
            # This value might need to be configurable or determined differently.
            # For now, returning a default.
            return 0.05
        return 0.05

    def is_user_pivot(self) -> bool:
        if self._platform_system == "Linux":
            # If pivot control is added for Linux, this needs actual implementation
            return False
        return False

    def set_camera_matrix(self, matrix : "pynav.NavlibMatrix" or Matrix) -> None:
        if self._platform_system == "Linux":
            if not isinstance(matrix, Matrix):
                logger.error("set_camera_matrix on Linux called with incorrect matrix type.")
                return
            # Directly set the transformation for the active camera
            self._scene.getActiveCamera().setTransformation(matrix)
            # TODO: Consider if pivot node scaling is needed here for Linux
            # The logic below for pivot scaling might be reusable if self._pivot_node is active.
            # For now, keeping it simple.
            return

        # Original non-Linux logic:
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

    def set_view_extents(self, extents: "pynav.NavlibBox") -> None:
        if self._platform_system == "Linux":
            logger.debug("set_view_extents called on Linux. No-op for now.")
            # If needed, would have to interpret extents (possibly a dict) and set zoom.
            return

        view_width = self._scene.getActiveCamera().getViewportWidth()
        new_zoom = (extents._min._x + view_width / 2.) / - view_width
        self._scene.getActiveCamera().setZoomFactor(new_zoom)

    def set_hit_selection_only(self, onlySelection : bool) -> None:
        # This can be common logic.
        self._hit_selection_only = onlySelection

    def set_motion_flag(self, motion : bool) -> None:
        if self._platform_system == "Linux":
            if self._linux_spacenav_client and self._linux_spacenav_client.available:
                if motion:
                    logger.info("set_motion_flag(True) called on Linux. Ensuring Spacenav is open.")
                    if self._linux_spacenav_client.open():
                        logger.info("LinuxSpacenavClient is open.")
                    else:
                        logger.warning("Failed to open LinuxSpacenavClient on set_motion_flag(True).")
                else:
                    logger.info("set_motion_flag(False) called on Linux. Closing Spacenav.")
                    self._linux_spacenav_client.close() # close() in client logs success/failure
            elif motion: # motion is True, but client is not available/initialized
                logger.warning("set_motion_flag(True) called on Linux, but Spacenav client is not available.")
            # Since Tool.__init__ is not called on Linux, picking pass management is not relevant here.
            return

        # Original non-Linux logic:
        if motion:
            if self._picking_pass is None: # Ensure picking pass is only added once
                width = self._scene.getActiveCamera().getViewportWidth()
                height = self._scene.getActiveCamera().getViewportHeight()
                if width > 0 and height > 0:
                    self._picking_pass = PickingPass(width, height)
                    self._renderer.addRenderPass(self._picking_pass)
                else:
                    logger.warning("Cannot create PickingPass, viewport dimensions are invalid.")
        else:
            self._was_pick = False
            if self._picking_pass is not None:
                self._renderer.removeRenderPass(self._picking_pass)
                self._picking_pass = None # Explicitly set to None after removal


    def set_pivot_position(self, position) -> None: # `position` is pynav.NavlibVector or UM.Math.Vector
        if self._platform_system == "Linux":
            if isinstance(position, Vector): # Assuming position might be UM.Math.Vector for Linux
                self._pivot_node._target_node.setPosition(position=position, transform_space = SceneNode.TransformSpace.World)
                logger.debug(f"Set pivot position on Linux to {position}")
            else:
                logger.warning("set_pivot_position on Linux called with unexpected type.")
            return

        self._pivot_node._target_node.setPosition(position=Vector(position._x, position._y, position._z), transform_space = SceneNode.TransformSpace.World)

    def set_pivot_visible(self, visible) -> None:
        # This logic can be common if _scene and _pivot_node are available.
        if visible:
            if self._pivot_node not in self._scene.getRoot().getChildren():
                 self._scene.getRoot().addChild(self._pivot_node)
        else:
            if self._pivot_node in self._scene.getRoot().getChildren():
                 self._scene.getRoot().removeChild(self._pivot_node)

# Ensure logging is configured if this file is run standalone (e.g. for type checking)
# This is more of a library class, so direct execution isn't typical.
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info("NavlibClient.py - basic structure for type checking or direct import.")
