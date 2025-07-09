import math
import time
from pathlib import Path
import typing
import numpy as np

from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Math.Polygon import Polygon
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.FileHandler.ReadFileJob import ReadFileJob

from UM.Scene.SceneNode import SceneNode

from UM.Logger import Logger
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from cura.Settings.PerObjectContainerStack import PerObjectContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.SettingInstance import SettingInstance

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Math.AxisAlignedBox import AxisAlignedBox


from PyQt6.QtCore import QUrl

from typing import List, Dict, Optional

from UM.Mesh.ReadMeshJob import ReadMeshJob

if typing.TYPE_CHECKING:
    from UseDrywiseDryer import UseDrywiseDryer



class PurgeCubeSceneNode(CuraSceneNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drywise_script: UseDrywiseDryer | None = None

        self.prev_size: np.ndarray | None = None
        self.prev_orient: Quaternion | None = None
        self._current_volume: float = 1.0
        self._initial_size: np.ndarray | None = None

        self._size_bounds: np.ndarray | None = None
        self.transformationChanged.connect(self._on_transform)

        # Signals on adding an object
        # Signals when selecting an object
        # Signals when deselecting an object
        # Signals when selecting which extruder should print the object
        # extruder_manager.selectedObjectExtrudersChanged.connect(self.on_extruder_change)

        if (app := CuraApplication.getInstance()) is None:
            return
        root_node = app.getController().getScene().getRoot()
        root_node.childrenChanged.connect(self.verify_if_still_exists)

    def set_setting(self, key: str, value: typing.Any, property_name: str = 'value'):
        """ Sets per object slicing setting (or adds it if it is not there) """

        if not self.hasDecoration('getStack'):
            raise RuntimeError(f'{self} has no decoration `getStack`!')
        # A container stack that just contains `userChanges` which is a single InstanceContainer
        node_stack = typing.cast(PerObjectContainerStack, self.callDecoration('getStack'))
        user_changes = typing.cast(InstanceContainer, node_stack.userChanges)
        if not user_changes.hasProperty(key, property_name):
            app = CuraApplication.getInstance()
            stack = app.getGlobalContainerStack()
            if (definition := stack.getSettingDefinition(key)) is None:
                Logger.warning(f'No definition for the {key=}.')
                return
            # Adding a setting like this will make it visible to the user in the per-object settings.
            user_changes.addInstance(SettingInstance(definition, container=user_changes))
        user_changes.setProperty(key, property_name, value)

    def verify_if_still_exists(self, *args):
        """ Check if the user deleted this node. If so, then signal to the script to delete itself and this node """
        if (app := CuraApplication.getInstance()) is None:
            return
        root_node = app.getController().getScene().getRoot()

        for child in root_node.getChildren():
            if child is self:
                return
        root_node.childrenChanged.disconnect(self.verify_if_still_exists)
        self.drywise_script.unload()

    @property
    def size_bounds(self) -> np.ndarray:
        return self._size_bounds

    @size_bounds.setter
    def size_bounds(self, value: np.ndarray):
        if value.shape != (2, 3):
            raise ValueError('Incorrect shape of the size bounds of the purge cube')
        if self._size_bounds is not None and np.allclose(self._size_bounds, value):
            return
        self._size_bounds = value
        self._on_transform()

    @property
    def volume(self) -> float:
        """ Required volume of the purge model

        Can change when the user changes some script parameters, such as distance from drywise output to extruder.
        As a result, the script should be able to update the scale of the model.

        See the script paramters for more info on which parameters affect the final volume of the purge model.
        """
        return self._current_volume

    @volume.setter
    def volume(self, value: float):
        if np.isclose(value, self.volume):
            return
        self._current_volume = value
        xy_size_change = math.sqrt(value / self.volume)
        self.scale(Vector(xy_size_change, 1.0, xy_size_change), transform_space=SceneNode.TransformSpace.Local)

    @property
    def size(self) -> np.ndarray:
        if self._initial_size is None:
            bbox = self.getBoundingBox()
            self._initial_size = np.array([bbox.width, bbox.height, bbox.depth])
        return self._initial_size * self.getScale().getData()

    @size.setter
    def size(self, new_size: np.ndarray):
        if np.allclose(new_size, (current_size := self.size)):
            return
        # Scaling is done with respect to local coordinates and not the world coords, unlike with position and
        # orientation. The reason for this is that when scaling is
        self.scale(Vector(data=new_size/current_size), transform_space=SceneNode.TransformSpace.Local)

    @property
    def z_height(self) -> float:
        return self.getBoundingBox().height

    @z_height.setter
    def z_height(self, value: float):
        if np.isclose(value, self.z_height):
            return
        self.scale(Vector(1.0, value/self.z_height, 1.0), transform_space=SceneNode.TransformSpace.Local)

    def place_and_resize_at(self,
        pos: typing.Literal['left', 'right', 'top', 'bottom'], bed_offset: float = 5.0, min_width: float = 10.0
    ):
        global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        build_volume = (
            float(global_stack.getProperty('machine_width', 'value')) - 2*bed_offset,
            float(global_stack.getProperty('machine_depth', 'value')) - 2*bed_offset,
        )

        vol = self.volume
        # The height of the cube does not change
        height = self.z_height

        # As a rule, if the position is on left/right, then size of the cube extends along the Y axis as much as
        # possible before extending along the X axis
        is_along_Y = pos in ['left', 'right']
        area = vol / height
        length = min(area / min_width, build_volume[int(is_along_Y)])
        width = max(min_width, area / length)

        self.size = np.array([length, height, width])
        if is_along_Y:
            # Rotate 90 degrees cw if right and acw if left
            q = Quaternion()
            q.setByAngleAxis(angle=math.radians(90), axis=Vector(0, 1, 0))
            self.rotate(q, transform_space=SceneNode.TransformSpace.World)
        # By default, the positioning of the cube is in the center
        self.setPosition(Vector(
            x=0.0 if not is_along_Y else (build_volume[0]/2 - width) * (-1 if pos == 'left' else 1),
            z=0.0,
            y=0.0 if is_along_Y else (build_volume[0]/2 - width) * (-1 if pos == 'bottom' else 1),
        ), transform_space=SceneNode.TransformSpace.World)

    def _on_transform(self, *args):
        # Disconnect to prevent repeated firing if this method modifies transformations
        self.transformationChanged.disconnect(self._on_transform)

        self.prev_size = self.prev_size if self.prev_size is not None else self.size
        self.prev_orient = self.prev_orient if self.prev_orient is not None else self.getWorldOrientation()

        self._on_transform_forbid_xz_rotations()
        self._on_transform_maintain_size_bounds()
        self._on_transform_maintain_volume()

        self.prev_size = self.size
        self.prev_orient = self.getWorldOrientation()

        # Reconnect after corrections are applied
        self.transformationChanged.connect(self._on_transform)

    def _on_transform_maintain_volume(self, *args):
        """ Maintains required volume for the purge cube """

        size = self.size
        is_transformed = ~np.isclose(self.prev_size, size)
        if not np.any(is_transformed):
            return

        volume_change = np.prod(size) / self.volume
        if is_transformed[1] or (is_transformed[0] and is_transformed[2]):
            scale_change = np.sqrt(np.array([volume_change, 1.0, volume_change]))
        elif is_transformed[0]:
            scale_change = np.array([1.0, 1.0, volume_change])
        else:
            scale_change = np.array([volume_change, 1.0, 1.0])
        self.size = size / scale_change

    def _on_transform_maintain_size_bounds(self, *args):
        """
        Ensure that the object does not extend outside of the buildplate

        Notice that this does not protect against extending the object s.t. the adhesion area are either outside
        of the buildplate or placed on the non-printable area.
        """
        if self.size_bounds is None:
            return

        # `self.size` returns the size of the object in the local coordinate system, which is not
        # suitable for us, since the model can be rotated. As a result, it is best to compute the bbox
        # of the object on the buildplate and work with that.
        bbox = self.getBoundingBox()
        global_size = [bbox.width, bbox.height, bbox.depth]
        global_size_bounded = np.max(np.vstack((global_size, self.size_bounds[0, :])), axis=0)
        global_size_bounded = np.min(np.vstack((global_size_bounded, self.size_bounds[1, :])), axis=0)
        out_of_bounds = ~np.isclose(global_size_bounded, global_size)
        if not np.any(out_of_bounds):
            return

        # Since we are working with the bbox, we have to transform on the global coordinate system.
        Logger.debug(f'The purge cube was scaled to avoid being larger than the buildplate.')
        scaling_factor = np.where(out_of_bounds, global_size_bounded / global_size, 1.0)
        self.scale(Vector(data=scaling_factor), transform_space=SceneNode.TransformSpace.World)

    def _on_transform_forbid_xz_rotations(self, *args):
        orient = np.abs(self.getWorldOrientation().getData())
        if np.allclose(orient[[0, 2]], 0.0):
            return
        Logger.debug(f'Rotations of the purge cube not around the vertical Y-axis are forbidden. Reverting to previous state.')
        self.setOrientation(self.prev_orient, transform_space=SceneNode.TransformSpace.World)











    def addDecorator(self, decorator: SceneNodeDecorator) -> None:
        """ Modified in order to circumvent the type check that does not allow subclasses """

        if any(isinstance(dec, type(decorator)) for dec in self._decorators):
            Logger.log("w", "Unable to add the same decorator type (%s) to a SceneNode twice.", type(decorator))
            return
        try:
            decorator.setNode(self)
        except AttributeError:
            Logger.logException("e", "Unable to add decorator.")
            return
        self._decorators.append(decorator)
        self.decoratorsChanged.emit(self)

    def getDecorator(self, dec_type: type[SceneNodeDecorator]) -> Optional[SceneNodeDecorator]:
        """ Modified in order to circumvent the type check that does not allow subclasses """

        for decorator in self._decorators:
            if isinstance(decorator, dec_type):
                return decorator
        return None

    def removeDecorator(self, dec_type: type[SceneNodeDecorator]) -> None:
        """ Modified in order to circumvent the type check that does not allow subclasses """

        for decorator in self._decorators:
            if isinstance(decorator, dec_type):
                decorator.clear()
                self._decorators.remove(decorator)
                self.decoratorsChanged.emit(self)
                break

    # def _on_node_addition(self, *args):
    #     app = CuraApplication.getInstance()
    #     if app is None:
    #         return
    #
    #     root_node = app.getController().getScene().getRoot()
    #     children = root_node.getChildren()
    #
    #     idx_first_node = 0
    #     while not isinstance(children[idx_first_node], CuraSceneNode):
    #         idx_first_node += 1
    #         if idx_first_node >= len(children):
    #             return
    #     if children[idx_first_node] is self.node:
    #         return
    #
    #     idx_purge_cube = idx_first_node
    #     while children[idx_purge_cube] is not self.node:
    #         idx_purge_cube += 1
    #         if idx_purge_cube >= len(children):
    #             return
    #
    #     # Move the purge cube node to the last position
    #     root_node._children = [
    #         *children[:idx_first_node],
    #         self.node,
    #         *children[idx_first_node:idx_purge_cube],
    #         *children[idx_purge_cube + 1:],
    #     ]
    #     # root_node.childrenChanged.emit(root_node)
    #
    # def _enforce_print_order(self):
    #     app = CuraApplication.getInstance()
    #     if app is None or self.node is None:
    #         return
    #     if self.node.printOrder == 1:
    #         return
    #
    #     root_nodes = app.getController().getScene().getRoot()
    #     printing_nodes = [child for child in root_nodes.getChildren() if isinstance(child, CuraSceneNode)]
    #     for node in printing_nodes:
    #         if node.printOrder < self.node.printOrder:
    #             node.printOrder += 1
    #     self.node.printOrder = 1



class PurgeCubeConvexHullDecorator(ConvexHullDecorator):
    def __init__(self, nozzle_height: float = 2.0):
        super().__init__()

        self.nozzle_height = nozzle_height

    def getNode(self) -> PurgeCubeSceneNode | None:
        return self._node

    def _isSingularOneAtATimeNode(self) -> bool:
        """ Always printed as a whole, therefore a one-at-a-time node """
        return True

    def _getHeadAndFans(self):
        """ If the z_height of the node is small, allow placing other models much much closer to the `PurgeCube` """
        if self.getNode().z_height > self.nozzle_height:
            return super()._getHeadAndFans()
        # To simulate the nozzle. Even at that height the nozzle can hit the purge cube
        return Polygon.approximatedCircle(8.0 / 2)

    def _compute2DConvexHeadFull(self) -> Optional[Polygon]:
        convex_hull = self._compute2DConvexHull()
        convex_hull = self._add2DAdhesionMargin(convex_hull)
        if not convex_hull:
            return None
        head_hull = convex_hull.getMinkowskiHull(self._getHeadAndFans())
        if self._global_stack is not None \
            and self._global_stack.getProperty("print_sequence", "value") == "all_at_once":
            brim_hull = self._add2DAdhesionMargin(convex_hull)
            return head_hull.unionConvexHulls(brim_hull)
        return head_hull



def load_purge_cube(path: str, node_name: str = None) -> PurgeCubeSceneNode | None:
    """ Copy pasted from CuraApplication.readLocalFile

    Removed unnecessary lines since we know that we are loading an stl
    """
    file = QUrl(Path(__file__).parent.joinpath(path).as_uri())
    Logger.log("i", "Attempting to read file %s", file.toString())
    if not file.isValid():
        raise FileNotFoundError

    if (app := CuraApplication.getInstance()) is None:
        return None

    # No idea what isBlockSlicing decorator is, so I decided to just leave it as it is.
    scene = app.getController().getScene()
    for node in DepthFirstIterator(scene.getRoot()):
        if node.callDecoration("isBlockSlicing"):
            app.deleteAll()
            break

    f = file.toLocalFile()
    app._currently_loading_files.append(f)
    # Using UM.FileHandler.ReadFileJob instead of UM.Mesh.ReadMeshJob, because the latter tries to be smart and
    # auto-scales the model if it is too small. This is annoying, so I am not using it.
    job = ReadFileJob(filename=f, handler=app.getMeshFileHandler(), add_to_recent_files=False)
    job.start()

    # I do not really like callbacks that much. I wish cura used AsyncIO or at least Future or Promise, but no,
    # it uses callbacks. The way this is fine, since the model is just a cube with 8 vertices, so it is not very
    # computationally intensive (so it would not block the UI if this is the thread on which the UI runs).
    while not job.isFinished():
        if job.hasError():
            raise job.getError()
        time.sleep(0.1)

    result = job.getResult()
    if not isinstance(result, typing.Sequence) or len(result) <= 0:
        raise RuntimeError('Did not load any meshes for some reason...')

    # Code taken from CuraApplication._readMeshFinished where this code converts a SceneNode to
    # CuraSceneNode
    original_node = result[0]
    node = PurgeCubeSceneNode(name=node_name)
    node.setMeshData(original_node.getMeshData())
    node.source_mime_type = original_node.source_mime_type
    # Setting meshdata does not apply scaling.
    if original_node.getScale() != Vector(1.0, 1.0, 1.0):
        node.scale(original_node.getScale())

    # Ensure that the correct decorator is attached to this new node.
    if node.getDecorator(ConvexHullDecorator):
        node.removeDecorator(ConvexHullDecorator)
    node.addDecorator(PurgeCubeConvexHullDecorator())

    # Finish node creation using the default function
    job._result = [node]
    app._readMeshFinished(job)
    return node






# def _on_model_finish_loading(self, filename: str):
#     """ Find the `CuraSceneNode` that contains the purge cube that was loaded by cura
#
#     `CuraApplication.readLocalFile` loads the stl files in a separate worker thread. As a result, it does not
#     actually return the resulting node. So, after it finishes loading, we have to unironially find it. So,
#     all this method does is it finds to loaded node and saves its reference
#
#     """
#
#     if self.path != Path(filename):
#         return
#     app = CuraApplication.getInstance()
#     root_node = app.getController().getScene().getRoot()
#
#     candidate_nodes = [n for n in root_node.getChildren() if n.getName() == self.path.name]
#     if len(candidate_nodes) == 0:
#         raise RuntimeError('No purge cube node was found!')
#     elif len(candidate_nodes) == 1:
#         self.node = candidate_nodes[0]
#         assert isinstance(self.node, CuraSceneNode)
#     else:
#         raise NotImplementedError('Likely multiple purge cubes created by multiple scripts. We are not dealing with that for now')
#
#
#     def _getNozzle(chd: ConvexHullDecorator) -> Polygon:
#         if not chd._global_stack:
#             return Polygon()
#
#         polygon = Polygon.approximatedCircle(8.0/4)
#         return polygon
#
#     def decorator(chd: ConvexHullDecorator, func):
#         def wrapper(*args, **kwargs):
#             return chd._compute2DConvexHeadFull()
#         return wrapper
#
#     def decoratorMin(chd: ConvexHullDecorator, func):
#         def wrapper(*args, **kwargs):
#             if self.z_height > 2.0:
#                 return func()
#
#             return chd._compute2DConvexHeadFull()
#         return wrapper
#
#     def decoratorHeadAndFans(chd: ConvexHullDecorator, func):
#         def wrapper(*args, **kwargs):
#             if self.z_height > 2.0:
#                 return func()
#             polygon = Polygon.approximatedCircle(8.0/4)
#             offset_x = 0.0  # chd._getSettingProperty("machine_nozzle_offset_x", "value")
#             offset_y = 0.0  # chd._getSettingProperty("machine_nozzle_offset_y", "value")
#             return polygon.translate(-offset_x, -offset_y)
#         return wrapper
#
#
#     convex_hull_decor: ConvexHullDecorator | None = self.node.getDecorator(ConvexHullDecorator)
#     if convex_hull_decor is not None:
#         convex_hull_decor._isSingularOneAtATimeNode = lambda *args: True
#         convex_hull_decor._getHeadAndFans = decoratorHeadAndFans(convex_hull_decor, convex_hull_decor._getHeadAndFans)
#         convex_hull_decor.getConvexHullHeadFull = convex_hull_decor._compute2DConvexHeadFull
#         #convex_hull_decor._compute2DConvexHeadFull = decorator(convex_hull_decor, convex_hull_decor._compute2DConvexHeadFull)
#         #convex_hull_decor._compute2DConvexHeadMin = decoratorMin(convex_hull_decor, convex_hull_decor._compute2DConvexHeadMin)
#
#     app.fileCompleted.disconnect(self._on_model_finish_loading)  # No need to continue watching
#     self.node.transformationChanged.connect(self._on_transform)
#     root_node = app.getController().getScene().getRoot()
#     root_node.childrenChanged.connect(self._on_node_addition)
#     self._current_scale = self.node.getScale()
#
#     if self.on_load is not None:
#         self.on_load()


