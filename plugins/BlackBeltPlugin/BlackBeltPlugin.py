from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BlackBeltPlugin")

from . import BuildVolumePatches

import math
import os.path

class BlackBeltPlugin(Extension):
    def __init__(self):
        super().__init__()
        plugin_path = os.path.dirname(os.path.abspath(__file__))

        self._application = Application.getInstance()

        self._build_volume_patches = None

        self._global_container_stack = None
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

        self._scene_root = self._application.getController().getScene().getRoot()
        self._scene_root.addDecorator(BlackBeltDecorator())
        self._application.getBackend().slicingStarted.connect(self._onSlicingStarted)

        self._application.engineCreatedSignal.connect(self._onEngineCreated)

    def _onGlobalContainerStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingValueChanged)
        self._global_container_stack = self._application.getGlobalContainerStack()
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingValueChanged)

            # HACK: Move blackbelt_settings to the top of the list of settings
            definition_container = self._global_container_stack.getBottom()
            if definition_container._definitions[len(definition_container._definitions) -1].key == "blackbelt_settings":
                definition_container._definitions.insert(0, definition_container._definitions.pop(len(definition_container._definitions) -1))

    def _onSlicingStarted(self):
        self._scene_root.callDecoration("calculateTransformData")

    def _onSettingValueChanged(self, key, property_name):
        if key in ["blackbelt_gantry_angle"] and property_name == "value":
            # Setting the gantry angle changes the build volume.
            # Force rebuilding the build volume by reloading the global container stack.
            # This is a bit of a hack, but it seems quick enough.
            self._application.globalContainerStackChanged.emit()

    def _onEngineCreated(self):
        # Apply patches
        self._build_volume_patches = BuildVolumePatches.BuildVolumePatches(self._application.getBuildVolume())

        # Fix preferences
        preferences = Preferences.getInstance()
        visible_settings = preferences.getValue("general/visible_settings")
        if not visible_settings:
            # Wait until the default visible settings have been set
            return

        visible_settings_changed = False
        for key in ["blackbelt_settings", "blackbelt_gantry_angle", "blackbelt_nozzle_size"]:
            if key not in visible_settings:
                visible_settings += ";%s" % key
                visible_settings_changed = True

        if not visible_settings_changed:
            return

        preferences.setValue("general/visible_settings", visible_settings)

        expanded_settings = preferences.getValue("cura/categories_expanded")
        if expanded_settings is None:
            expanded_settings = ""
        for key in ["blackbelt_settings"]:
            if key not in expanded_settings:
                expanded_settings += ";%s" % key
        preferences.setValue("cura/categories_expanded", expanded_settings)
        self._application.expandedCategoriesChanged.emit()

## Decorator for easy access to gantry angle and transform matrix.
class BlackBeltDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._gantry_angle = 0
        self._transform_matrix = Matrix()
        self._scene_front_offset = 0

    def calculateTransformData(self):
        global_stack = Application.getInstance().getGlobalContainerStack()

        self._scene_front_offset = 0
        gantry_angle = global_stack.getProperty("blackbelt_gantry_angle", "value")
        if not gantry_angle:
            self._gantry_angle = 0
            self._transform_matrix = Matrix()
            return
        self._gantry_angle = math.radians(float(gantry_angle))

        machine_depth = global_stack.getProperty("machine_depth", "value")

        matrix = Matrix()
        matrix.setColumn(1, [0, 1 / math.tan(self._gantry_angle), 1, (machine_depth / 2) * (2 - math.cos(self._gantry_angle))])
        matrix.setColumn(2, [0, - 1 / math.sin(self._gantry_angle), 0, machine_depth / 2])
        self._transform_matrix = matrix

        # The above magic transform matrix is composed as follows:
        """
        matrix_data = numpy.identity(4)
        matrix_data[2, 2] = 1/math.sin(self._gantry_angle)  # scale Z
        matrix_data[1, 2] = -1/math.tan(self._gantry_angle) # shear ZY
        matrix = Matrix(matrix_data)

        matrix_data = numpy.identity(4)
        # use front buildvolume face instead of bottom face
        matrix_data[1, 1] = 0
        matrix_data[1, 2] = 1
        matrix_data[2, 1] = -1
        matrix_data[2, 2] = 0
        axes_matrix = Matrix(matrix_data)

        matrix.multiply(axes_matrix)

        # bottom face has origin at the center, front face has origin at one side
        matrix.translate(Vector(0, - math.sin(self._gantry_angle) * machine_depth / 2, 0))
        # make sure objects are not transformed to be below the buildplate
        matrix.translate(Vector(0, 0, machine_depth))

        self._transform_matrix = matrix
        """

    def getGantryAngle(self):
        return self._gantry_angle

    def getTransformMatrix(self):
        return self._transform_matrix

    def setSceneFrontOffset(self, front_offset):
        self._scene_front_offset = front_offset

    def getSceneFrontOffset(self):
        return self._scene_front_offset