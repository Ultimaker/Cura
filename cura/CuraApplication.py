# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Resources import Resources
from UM.Scene.ToolHandle import ToolHandle
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.ReadMeshJob import ReadMeshJob
from UM.Logger import Logger
from UM.Preferences import Preferences
from UM.JobQueue import JobQueue
from UM.SaveFile import SaveFile
from UM.Scene.Selection import Selection
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Settings.Validator import Validator

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation
from UM.Operations.TranslateOperation import TranslateOperation
from cura.SetParentOperation import SetParentOperation

from UM.Settings.SettingDefinition import SettingDefinition, DefinitionPropertyType
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingFunction import SettingFunction

from UM.i18n import i18nCatalog

from . import PlatformPhysics
from . import BuildVolume
from . import CameraAnimation
from . import PrintInformation
from . import CuraActions
from . import ZOffsetDecorator
from . import CuraSplashScreen
from . import CameraImageProvider
from . import MachineActionManager

import cura.Settings

from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty, QEvent, Q_ENUMS
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtQml import qmlRegisterUncreatableType, qmlRegisterSingletonType, qmlRegisterType

from contextlib import contextmanager

import sys
import os.path
import numpy
import copy
import urllib
import os
import time

CONFIG_LOCK_FILENAME = "cura.lock"

##  Contextmanager to create a lock file and remove it afterwards.
@contextmanager
def lockFile(filename):
    try:
        with open(filename, 'w') as lock_file:
            lock_file.write("Lock file - Cura is currently writing")
    except:
        Logger.log("e", "Could not create lock file [%s]" % filename)
    yield
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except:
        Logger.log("e", "Could not delete lock file [%s]" % filename)


##  Wait for a lock file to disappear
#   the maximum allowable age is settable; if the file is too old, it will be ignored too
def waitFileDisappear(filename, max_age_seconds=10, msg=""):
    now = time.time()
    while os.path.exists(filename) and now < os.path.getmtime(filename) + max_age_seconds and now > os.path.getmtime(filename):
        if msg:
            Logger.log("d", msg)
        time.sleep(1)
        now = time.time()


numpy.seterr(all="ignore")

try:
    from cura.CuraVersion import CuraVersion, CuraBuildType
except ImportError:
    CuraVersion = "master"  # [CodeStyle: Reflecting imported value]
    CuraBuildType = ""

class CuraApplication(QtApplication):
    class ResourceTypes:
        QmlFiles = Resources.UserType + 1
        Firmware = Resources.UserType + 2
        QualityInstanceContainer = Resources.UserType + 3
        MaterialInstanceContainer = Resources.UserType + 4
        VariantInstanceContainer = Resources.UserType + 5
        UserInstanceContainer = Resources.UserType + 6
        MachineStack = Resources.UserType + 7
        ExtruderStack = Resources.UserType + 8

    Q_ENUMS(ResourceTypes)

    def __init__(self):
        Resources.addSearchPath(os.path.join(QtApplication.getInstallPrefix(), "share", "cura", "resources"))
        if not hasattr(sys, "frozen"):
            Resources.addSearchPath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "resources"))

        self._open_file_queue = []  # Files to open when plug-ins are loaded.

        # Need to do this before ContainerRegistry tries to load the machines
        SettingDefinition.addSupportedProperty("settable_per_mesh", DefinitionPropertyType.Any, default = True, read_only = True)
        SettingDefinition.addSupportedProperty("settable_per_extruder", DefinitionPropertyType.Any, default = True, read_only = True)
        # this setting can be changed for each group in one-at-a-time mode
        SettingDefinition.addSupportedProperty("settable_per_meshgroup", DefinitionPropertyType.Any, default = True, read_only = True)
        SettingDefinition.addSupportedProperty("settable_globally", DefinitionPropertyType.Any, default = True, read_only = True)

        # From which stack the setting would inherit if not defined per object (handled in the engine)
        # AND for settings which are not settable_per_mesh:
        # which extruder is the only extruder this setting is obtained from
        SettingDefinition.addSupportedProperty("limit_to_extruder", DefinitionPropertyType.Function, default = "-1")

        # For settings which are not settable_per_mesh and not settable_per_extruder:
        # A function which determines the glabel/meshgroup value by looking at the values of the setting in all (used) extruders
        SettingDefinition.addSupportedProperty("resolve", DefinitionPropertyType.Function, default = None)

        SettingDefinition.addSettingType("extruder", None, str, Validator)

        SettingFunction.registerOperator("extruderValues", cura.Settings.ExtruderManager.getExtruderValues)
        SettingFunction.registerOperator("extruderValue", cura.Settings.ExtruderManager.getExtruderValue)
        SettingFunction.registerOperator("resolveOrValue", cura.Settings.ExtruderManager.getResolveOrValue)

        ## Add the 4 types of profiles to storage.
        Resources.addStorageType(self.ResourceTypes.QualityInstanceContainer, "quality")
        Resources.addStorageType(self.ResourceTypes.VariantInstanceContainer, "variants")
        Resources.addStorageType(self.ResourceTypes.MaterialInstanceContainer, "materials")
        Resources.addStorageType(self.ResourceTypes.UserInstanceContainer, "user")
        Resources.addStorageType(self.ResourceTypes.ExtruderStack, "extruders")
        Resources.addStorageType(self.ResourceTypes.MachineStack, "machine_instances")

        ContainerRegistry.getInstance().addResourceType(self.ResourceTypes.QualityInstanceContainer)
        ContainerRegistry.getInstance().addResourceType(self.ResourceTypes.VariantInstanceContainer)
        ContainerRegistry.getInstance().addResourceType(self.ResourceTypes.MaterialInstanceContainer)
        ContainerRegistry.getInstance().addResourceType(self.ResourceTypes.UserInstanceContainer)
        ContainerRegistry.getInstance().addResourceType(self.ResourceTypes.ExtruderStack)
        ContainerRegistry.getInstance().addResourceType(self.ResourceTypes.MachineStack)

        ##  Initialise the version upgrade manager with Cura's storage paths.
        import UM.VersionUpgradeManager #Needs to be here to prevent circular dependencies.
        UM.VersionUpgradeManager.VersionUpgradeManager.getInstance().setCurrentVersions(
            {
                ("quality", UM.Settings.InstanceContainer.Version):    (self.ResourceTypes.QualityInstanceContainer, "application/x-uranium-instancecontainer"),
                ("machine_stack", UM.Settings.ContainerStack.Version): (self.ResourceTypes.MachineStack, "application/x-uranium-containerstack"),
                ("preferences", UM.Preferences.Version):               (Resources.Preferences, "application/x-uranium-preferences"),
                ("user", UM.Settings.InstanceContainer.Version):       (self.ResourceTypes.UserInstanceContainer, "application/x-uranium-instancecontainer")
            }
        )

        self._machine_action_manager = MachineActionManager.MachineActionManager()
        self._machine_manager = None    # This is initialized on demand.
        self._setting_inheritance_manager = None

        self._additional_components = {} # Components to add to certain areas in the interface

        super().__init__(name = "cura", version = CuraVersion, buildtype = CuraBuildType)

        self.setWindowIcon(QIcon(Resources.getPath(Resources.Images, "cura-icon.png")))

        self.setRequiredPlugins([
            "CuraEngineBackend",
            "MeshView",
            "LayerView",
            "STLReader",
            "SelectionTool",
            "CameraTool",
            "GCodeWriter",
            "LocalFileOutputDevice"
        ])
        self._physics = None
        self._volume = None
        self._output_devices = {}
        self._print_information = None
        self._previous_active_tool = None
        self._platform_activity = False
        self._scene_bounding_box = AxisAlignedBox.Null

        self._job_name = None
        self._center_after_select = False
        self._camera_animation = None
        self._cura_actions = None
        self._started = False

        self._message_box_callback = None
        self._message_box_callback_arguments = []

        self._i18n_catalog = i18nCatalog("cura")

        self.getController().getScene().sceneChanged.connect(self.updatePlatformActivity)
        self.getController().toolOperationStopped.connect(self._onToolOperationStopped)

        Resources.addType(self.ResourceTypes.QmlFiles, "qml")
        Resources.addType(self.ResourceTypes.Firmware, "firmware")

        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Loading machines..."))

        # Add empty variant, material and quality containers.
        # Since they are empty, they should never be serialized and instead just programmatically created.
        # We need them to simplify the switching between materials.
        empty_container = ContainerRegistry.getInstance().getEmptyInstanceContainer()
        empty_variant_container = copy.deepcopy(empty_container)
        empty_variant_container._id = "empty_variant"
        empty_variant_container.addMetaDataEntry("type", "variant")
        ContainerRegistry.getInstance().addContainer(empty_variant_container)
        empty_material_container = copy.deepcopy(empty_container)
        empty_material_container._id = "empty_material"
        empty_material_container.addMetaDataEntry("type", "material")
        ContainerRegistry.getInstance().addContainer(empty_material_container)
        empty_quality_container = copy.deepcopy(empty_container)
        empty_quality_container._id = "empty_quality"
        empty_quality_container.setName("Not supported")
        empty_quality_container.addMetaDataEntry("quality_type", "normal")
        empty_quality_container.addMetaDataEntry("type", "quality")
        ContainerRegistry.getInstance().addContainer(empty_quality_container)
        empty_quality_changes_container = copy.deepcopy(empty_container)
        empty_quality_changes_container._id = "empty_quality_changes"
        empty_quality_changes_container.addMetaDataEntry("type", "quality_changes")
        ContainerRegistry.getInstance().addContainer(empty_quality_changes_container)

        # Set the filename to create if cura is writing in the config dir.
        self._config_lock_filename = os.path.join(Resources.getConfigStoragePath(), CONFIG_LOCK_FILENAME)
        self.waitConfigLockFile()
        ContainerRegistry.getInstance().load()

        Preferences.getInstance().addPreference("cura/active_mode", "simple")
        Preferences.getInstance().addPreference("cura/recent_files", "")
        Preferences.getInstance().addPreference("cura/categories_expanded", "")
        Preferences.getInstance().addPreference("cura/jobname_prefix", True)
        Preferences.getInstance().addPreference("view/center_on_select", True)
        Preferences.getInstance().addPreference("mesh/scale_to_fit", True)
        Preferences.getInstance().addPreference("mesh/scale_tiny_meshes", True)

        for key in [
            "dialog_load_path",  # dialog_save_path is in LocalFileOutputDevicePlugin
            "dialog_profile_path",
            "dialog_material_path"]:

            Preferences.getInstance().addPreference("local_file/%s" % key, os.path.expanduser("~/"))

        Preferences.getInstance().setDefault("local_file/last_used_type", "text/x-gcode")

        Preferences.getInstance().setDefault("general/visible_settings", """
            machine_settings
                resolution
                layer_height
            shell
                wall_thickness
                top_bottom_thickness
            infill
                infill_sparse_density
            material
                material_print_temperature
                material_bed_temperature
                material_diameter
                material_flow
                retraction_enable
            speed
                speed_print
                speed_travel
                acceleration_print
                acceleration_travel
                jerk_print
                jerk_travel
            travel
            cooling
                cool_fan_enabled
            support
                support_enable
                support_extruder_nr
                support_type
                support_interface_density
            platform_adhesion
                adhesion_type
                adhesion_extruder_nr
                brim_width
                raft_airgap
                layer_0_z_overlap
                raft_surface_layers
            dual
                prime_tower_enable
                prime_tower_size
                prime_tower_position_x
                prime_tower_position_y
            meshfix
            blackmagic
                print_sequence
                infill_mesh
            experimental
        """.replace("\n", ";").replace(" ", ""))

        JobQueue.getInstance().jobFinished.connect(self._onJobFinished)

        self.applicationShuttingDown.connect(self.saveSettings)
        self.engineCreatedSignal.connect(self._onEngineCreated)
        self._recent_files = []
        files = Preferences.getInstance().getValue("cura/recent_files").split(";")
        for f in files:
            if not os.path.isfile(f):
                continue

            self._recent_files.append(QUrl.fromLocalFile(f))

    ## Lock file check: if (another) Cura is writing in the Config dir.
    #  one may not be able to read a valid set of files while writing. Not entirely fool-proof,
    #  but works when you start Cura shortly after shutting down.
    def waitConfigLockFile(self):
        waitFileDisappear(self._config_lock_filename, max_age_seconds=10, msg="Waiting for Cura to finish writing in the config dir...")

    def _onEngineCreated(self):
        self._engine.addImageProvider("camera", CameraImageProvider.CameraImageProvider())

    ## A reusable dialogbox
    #
    showMessageBox = pyqtSignal(str, str, str, str, int, int, arguments = ["title", "text", "informativeText", "detailedText", "buttons", "icon"])
    def messageBox(self, title, text, informativeText = "", detailedText = "", buttons = QMessageBox.Ok, icon = QMessageBox.NoIcon, callback = None, callback_arguments = []):
        self._message_box_callback = callback
        self._message_box_callback_arguments = callback_arguments
        self.showMessageBox.emit(title, text, informativeText, detailedText, buttons, icon)

    @pyqtSlot(int)
    def messageBoxClosed(self, button):
        if self._message_box_callback:
            self._message_box_callback(button, *self._message_box_callback_arguments)
            self._message_box_callback = None
            self._message_box_callback_arguments = []

    showPrintMonitor = pyqtSignal(bool, arguments = ["show"])

    ##  Cura has multiple locations where instance containers need to be saved, so we need to handle this differently.
    #
    #   Note that the AutoSave plugin also calls this method.
    def saveSettings(self):
        if not self._started: # Do not do saving during application start
            return

        self.waitConfigLockFile()

        # When starting Cura, we check for the lockFile which is created and deleted here
        with lockFile(self._config_lock_filename):

            for instance in ContainerRegistry.getInstance().findInstanceContainers():
                if not instance.isDirty():
                    continue

                try:
                    data = instance.serialize()
                except NotImplementedError:
                    continue
                except Exception:
                    Logger.logException("e", "An exception occurred when serializing container %s", instance.getId())
                    continue

                mime_type = ContainerRegistry.getMimeTypeForContainer(type(instance))
                file_name = urllib.parse.quote_plus(instance.getId()) + "." + mime_type.preferredSuffix
                instance_type = instance.getMetaDataEntry("type")
                path = None
                if instance_type == "material":
                    path = Resources.getStoragePath(self.ResourceTypes.MaterialInstanceContainer, file_name)
                elif instance_type == "quality" or instance_type == "quality_changes":
                    path = Resources.getStoragePath(self.ResourceTypes.QualityInstanceContainer, file_name)
                elif instance_type == "user":
                    path = Resources.getStoragePath(self.ResourceTypes.UserInstanceContainer, file_name)
                elif instance_type == "variant":
                    path = Resources.getStoragePath(self.ResourceTypes.VariantInstanceContainer, file_name)

                if path:
                    instance.setPath(path)
                    with SaveFile(path, "wt", -1, "utf-8") as f:
                        f.write(data)

            for stack in ContainerRegistry.getInstance().findContainerStacks():
                self.saveStack(stack)

    def saveStack(self, stack):
        if not stack.isDirty():
            return
        try:
            data = stack.serialize()
        except NotImplementedError:
            return
        except Exception:
            Logger.logException("e", "An exception occurred when serializing container %s", stack.getId())
            return

        mime_type = ContainerRegistry.getMimeTypeForContainer(type(stack))
        file_name = urllib.parse.quote_plus(stack.getId()) + "." + mime_type.preferredSuffix
        stack_type = stack.getMetaDataEntry("type", None)
        path = None
        if not stack_type or stack_type == "machine":
            path = Resources.getStoragePath(self.ResourceTypes.MachineStack, file_name)
        elif stack_type == "extruder_train":
            path = Resources.getStoragePath(self.ResourceTypes.ExtruderStack, file_name)
        if path:
            stack.setPath(path)
            with SaveFile(path, "wt", -1, "utf-8") as f:
                f.write(data)


    @pyqtSlot(str, result = QUrl)
    def getDefaultPath(self, key):
        default_path = Preferences.getInstance().getValue("local_file/%s" % key)
        return QUrl.fromLocalFile(default_path)

    @pyqtSlot(str, str)
    def setDefaultPath(self, key, default_path):
        Preferences.getInstance().setValue("local_file/%s" % key, default_path)

    ##  Handle loading of all plugin types (and the backend explicitly)
    #   \sa PluginRegistery
    def _loadPlugins(self):
        self._plugin_registry.addType("profile_reader", self._addProfileReader)
        self._plugin_registry.addType("profile_writer", self._addProfileWriter)
        self._plugin_registry.addPluginLocation(os.path.join(QtApplication.getInstallPrefix(), "lib", "cura"))
        if not hasattr(sys, "frozen"):
            self._plugin_registry.addPluginLocation(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "plugins"))
            self._plugin_registry.loadPlugin("ConsoleLogger")
            self._plugin_registry.loadPlugin("CuraEngineBackend")

        self._plugin_registry.loadPlugins()

        if self.getBackend() == None:
            raise RuntimeError("Could not load the backend plugin!")

        self._plugins_loaded = True

    def addCommandLineOptions(self, parser):
        super().addCommandLineOptions(parser)
        parser.add_argument("file", nargs="*", help="Files to load after starting the application.")
        parser.add_argument("--debug", dest="debug-mode", action="store_true", default=False, help="Enable detailed crash reports.")

    def run(self):
        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Setting up scene..."))

        controller = self.getController()

        controller.setActiveView("SolidView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool("TranslateTool")
        if t:
            t.setEnabledAxis([ToolHandle.XAxis, ToolHandle.YAxis,ToolHandle.ZAxis])

        Selection.selectionChanged.connect(self.onSelectionChanged)

        root = controller.getScene().getRoot()

        # The platform is a child of BuildVolume
        self._volume = BuildVolume.BuildVolume(root)

        self.getRenderer().setBackgroundColor(QColor(245, 245, 245))

        self._physics = PlatformPhysics.PlatformPhysics(controller, self._volume)

        camera = Camera("3d", root)
        camera.setPosition(Vector(-80, 250, 700))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))
        controller.getScene().setActiveCamera("3d")

        self.getController().getTool("CameraTool").setOrigin(Vector(0, 100, 0))

        self._camera_animation = CameraAnimation.CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool("CameraTool"))

        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Loading interface..."))

        # Initialise extruder so as to listen to global container stack changes before the first global container stack is set.
        cura.Settings.ExtruderManager.getInstance()
        qmlRegisterSingletonType(cura.Settings.MachineManager, "Cura", 1, 0, "MachineManager", self.getMachineManager)
        qmlRegisterSingletonType(cura.Settings.SettingInheritanceManager, "Cura", 1, 0, "SettingInheritanceManager", self.getSettingInheritanceManager)
        qmlRegisterSingletonType(MachineActionManager.MachineActionManager, "Cura", 1, 0, "MachineActionManager", self.getMachineActionManager)
        self.setMainQml(Resources.getPath(self.ResourceTypes.QmlFiles, "Cura.qml"))
        self._qml_import_paths.append(Resources.getPath(self.ResourceTypes.QmlFiles))
        self.initializeEngine()

        if self._engine.rootObjects:
            self.closeSplash()

            for file in self.getCommandLineOption("file", []):
                self._openFile(file)
            for file_name in self._open_file_queue: #Open all the files that were queued up while plug-ins were loading.
                self._openFile(file_name)

            self._started = True

            self.exec_()

    def getMachineManager(self, *args):
        if self._machine_manager is None:
            self._machine_manager = cura.Settings.MachineManager.createMachineManager()
        return self._machine_manager

    def getSettingInheritanceManager(self, *args):
        if self._setting_inheritance_manager is None:
            self._setting_inheritance_manager = cura.Settings.SettingInheritanceManager.createSettingInheritanceManager()
        return self._setting_inheritance_manager

    ##  Get the machine action manager
    #   We ignore any *args given to this, as we also register the machine manager as qml singleton.
    #   It wants to give this function an engine and script engine, but we don't care about that.
    def getMachineActionManager(self, *args):
        return self._machine_action_manager

    ##   Handle Qt events
    def event(self, event):
        if event.type() == QEvent.FileOpen:
            if self._plugins_loaded:
                self._openFile(event.file())
            else:
                self._open_file_queue.append(event.file())

        return super().event(event)

    ##  Get print information (duration / material used)
    def getPrintInformation(self):
        return self._print_information

    ##  Registers objects for the QML engine to use.
    #
    #   \param engine The QML engine.
    def registerObjects(self, engine):
        engine.rootContext().setContextProperty("Printer", self)
        engine.rootContext().setContextProperty("CuraApplication", self)
        self._print_information = PrintInformation.PrintInformation()
        engine.rootContext().setContextProperty("PrintInformation", self._print_information)
        self._cura_actions = CuraActions.CuraActions(self)
        engine.rootContext().setContextProperty("CuraActions", self._cura_actions)

        qmlRegisterUncreatableType(CuraApplication, "Cura", 1, 0, "ResourceTypes", "Just an Enum type")

        qmlRegisterType(cura.Settings.ExtrudersModel, "Cura", 1, 0, "ExtrudersModel")

        qmlRegisterType(cura.Settings.ContainerSettingsModel, "Cura", 1, 0, "ContainerSettingsModel")
        qmlRegisterType(cura.Settings.ProfilesModel, "Cura", 1, 0, "ProfilesModel")
        qmlRegisterType(cura.Settings.QualityAndUserProfilesModel, "Cura", 1, 0, "QualityAndUserProfilesModel")
        qmlRegisterType(cura.Settings.UserProfilesModel, "Cura", 1, 0, "UserProfilesModel")
        qmlRegisterType(cura.Settings.MaterialSettingsVisibilityHandler, "Cura", 1, 0, "MaterialSettingsVisibilityHandler")
        qmlRegisterType(cura.Settings.QualitySettingsModel, "Cura", 1, 0, "QualitySettingsModel")

        qmlRegisterSingletonType(cura.Settings.ContainerManager, "Cura", 1, 0, "ContainerManager", cura.Settings.ContainerManager.createContainerManager)

        qmlRegisterSingletonType(QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles, "Actions.qml")), "Cura", 1, 0, "Actions")

        engine.rootContext().setContextProperty("ExtruderManager", cura.Settings.ExtruderManager.getInstance())

        for path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.QmlFiles):
            type_name = os.path.splitext(os.path.basename(path))[0]
            if type_name in ("Cura", "Actions"):
                continue

            qmlRegisterType(QUrl.fromLocalFile(path), "Cura", 1, 0, type_name)

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                if self._previous_active_tool:
                    self.getController().setActiveTool(self._previous_active_tool)
                    self._previous_active_tool = None
                else:
                    self.getController().setActiveTool("TranslateTool")
            if Preferences.getInstance().getValue("view/center_on_select"):
                self._center_after_select = True
        else:
            if self.getController().getActiveTool():
                self._previous_active_tool = self.getController().getActiveTool().getPluginId()
                self.getController().setActiveTool(None)

    def _onToolOperationStopped(self, event):
        if self._center_after_select:
            self._center_after_select = False
            self._camera_animation.setStart(self.getController().getTool("CameraTool").getOrigin())
            self._camera_animation.setTarget(Selection.getSelectedObject(0).getWorldPosition())
            self._camera_animation.start()

    requestAddPrinter = pyqtSignal()
    activityChanged = pyqtSignal()
    sceneBoundingBoxChanged = pyqtSignal()

    @pyqtProperty(bool, notify = activityChanged)
    def getPlatformActivity(self):
        return self._platform_activity

    @pyqtProperty(str, notify = sceneBoundingBoxChanged)
    def getSceneBoundingBoxString(self):
        return self._i18n_catalog.i18nc("@info", "%(width).1f x %(depth).1f x %(height).1f mm") % {'width' : self._scene_bounding_box.width.item(), 'depth': self._scene_bounding_box.depth.item(), 'height' : self._scene_bounding_box.height.item()}

    def updatePlatformActivity(self, node = None):
        count = 0
        scene_bounding_box = None
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            count += 1
            if not scene_bounding_box:
                scene_bounding_box = node.getBoundingBox()
            else:
                other_bb = node.getBoundingBox()
                if other_bb is not None:
                    scene_bounding_box = scene_bounding_box + node.getBoundingBox()

        if not scene_bounding_box:
            scene_bounding_box = AxisAlignedBox.Null

        if repr(self._scene_bounding_box) != repr(scene_bounding_box):
            self._scene_bounding_box = scene_bounding_box
            self.sceneBoundingBoxChanged.emit()

        self._platform_activity = True if count > 0 else False
        self.activityChanged.emit()

    # Remove all selected objects from the scene.
    @pyqtSlot()
    def deleteSelection(self):
        if not self.getController().getToolsEnabled():
            return
        removed_group_nodes = []
        op = GroupedOperation()
        nodes = Selection.getAllSelectedObjects()
        for node in nodes:
            op.addOperation(RemoveSceneNodeOperation(node))
            group_node = node.getParent()
            if group_node and group_node.callDecoration("isGroup") and group_node not in removed_group_nodes:
                remaining_nodes_in_group = list(set(group_node.getChildren()) - set(nodes))
                if len(remaining_nodes_in_group) == 1:
                    removed_group_nodes.append(group_node)
                    op.addOperation(SetParentOperation(remaining_nodes_in_group[0], group_node.getParent()))
                    op.addOperation(RemoveSceneNodeOperation(group_node))
        op.push()

    ##  Remove an object from the scene.
    #   Note that this only removes an object if it is selected.
    @pyqtSlot("quint64")
    def deleteObject(self, object_id):
        if not self.getController().getToolsEnabled():
            return

        node = self.getController().getScene().findObject(object_id)

        if not node and object_id != 0:  # Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if node:
            op = GroupedOperation()
            op.addOperation(RemoveSceneNodeOperation(node))

            group_node = node.getParent()
            if group_node:
                # Note that at this point the node has not yet been deleted
                if len(group_node.getChildren()) <= 2 and group_node.callDecoration("isGroup"):
                    op.addOperation(SetParentOperation(group_node.getChildren()[0], group_node.getParent()))
                    op.addOperation(RemoveSceneNodeOperation(group_node))

            op.push()

    ##  Create a number of copies of existing object.
    @pyqtSlot("quint64", int)
    def multiplyObject(self, object_id, count):
        node = self.getController().getScene().findObject(object_id)

        if not node and object_id != 0:  # Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if node:
            current_node = node
            # Find the topmost group
            while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
                current_node = current_node.getParent()

            new_node = copy.deepcopy(current_node)

            op = GroupedOperation()
            for _ in range(count):
                op.addOperation(AddSceneNodeOperation(new_node, current_node.getParent()))
            op.push()

    ##  Center object on platform.
    @pyqtSlot("quint64")
    def centerObject(self, object_id):
        node = self.getController().getScene().findObject(object_id)
        if not node and object_id != 0:  # Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if not node:
            return

        if node.getParent() and node.getParent().callDecoration("isGroup"):
            node = node.getParent()

        if node:
            op = SetTransformOperation(node, Vector())
            op.push()

    ##  Select all nodes containing mesh data in the scene.
    @pyqtSlot()
    def selectAll(self):
        if not self.getController().getToolsEnabled():
            return

        Selection.clear()
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            Selection.add(node)

    ##  Delete all nodes containing mesh data in the scene.
    @pyqtSlot()
    def deleteAll(self):
        Logger.log("i", "Clearing scene")
        if not self.getController().getToolsEnabled():
            return

        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)
        if nodes:
            op = GroupedOperation()

            for node in nodes:
                op.addOperation(RemoveSceneNodeOperation(node))

            op.push()
            Selection.clear()

    ## Reset all translation on nodes with mesh data. 
    @pyqtSlot()
    def resetAllTranslation(self):
        Logger.log("i", "Resetting all scene translations")
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)

        if nodes:
            op = GroupedOperation()
            for node in nodes:
                # Ensure that the object is above the build platform
                node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
                op.addOperation(SetTransformOperation(node, Vector(0, node.getWorldPosition().y - node.getBoundingBox().bottom, 0)))
            op.push()

    ## Reset all transformations on nodes with mesh data.
    @pyqtSlot()
    def resetAll(self):
        Logger.log("i", "Resetting all scene transformations")
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)

        if nodes:
            op = GroupedOperation()
            for node in nodes:
                # Ensure that the object is above the build platform
                node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
                center_y = 0
                if node.callDecoration("isGroup"):
                    center_y = node.getWorldPosition().y - node.getBoundingBox().bottom
                else:
                    center_y = node.getMeshData().getCenterPosition().y
                op.addOperation(SetTransformOperation(node, Vector(0, center_y, 0), Quaternion(), Vector(1, 1, 1)))
            op.push()

    ##  Reload all mesh data on the screen from file.
    @pyqtSlot()
    def reloadAll(self):
        Logger.log("i", "Reloading all loaded mesh data.")
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            nodes.append(node)

        if not nodes:
            return

        for node in nodes:
            file_name = node.getMeshData().getFileName()
            if file_name:
                job = ReadMeshJob(file_name)
                job._node = node
                job.finished.connect(self._reloadMeshFinished)
                job.start()
            else:
                Logger.log("w", "Unable to reload data because we don't have a filename.")
    
    ##  Get logging data of the backend engine
    #   \returns \type{string} Logging data
    @pyqtSlot(result = str)
    def getEngineLog(self):
        log = ""

        for entry in self.getBackend().getLog():
            log += entry.decode()

        return log

    recentFilesChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = recentFilesChanged)
    def recentFiles(self):
        return self._recent_files

    @pyqtSlot("QStringList")
    def setExpandedCategories(self, categories):
        categories = list(set(categories))
        categories.sort()
        joined = ";".join(categories)
        if joined != Preferences.getInstance().getValue("cura/categories_expanded"):
            Preferences.getInstance().setValue("cura/categories_expanded", joined)
            self.expandedCategoriesChanged.emit()

    expandedCategoriesChanged = pyqtSignal()

    @pyqtProperty("QStringList", notify = expandedCategoriesChanged)
    def expandedCategories(self):
        return Preferences.getInstance().getValue("cura/categories_expanded").split(";")

    @pyqtSlot()
    def mergeSelected(self):
        self.groupSelected()
        try:
            group_node = Selection.getAllSelectedObjects()[0]
        except Exception as e:
            Logger.log("d", "mergeSelected: Exception:", e)
            return

        # Compute the center of the objects when their origins are aligned.
        object_centers = [node.getMeshData().getCenterPosition().scale(node.getScale()) for node in group_node.getChildren() if node.getMeshData()]
        if object_centers and len(object_centers) > 0:
            middle_x = sum([v.x for v in object_centers]) / len(object_centers)
            middle_y = sum([v.y for v in object_centers]) / len(object_centers)
            middle_z = sum([v.z for v in object_centers]) / len(object_centers)
            offset = Vector(middle_x, middle_y, middle_z)
        else:
            offset = Vector(0, 0, 0)

        # Move each node to the same position.
        for center, node in zip(object_centers, group_node.getChildren()):
            # Align the object and also apply the offset to center it inside the group.
            node.setPosition(center - offset)

        # Use the previously found center of the group bounding box as the new location of the group
        group_node.setPosition(group_node.getBoundingBox().center)

    @pyqtSlot()
    def groupSelected(self):
        # Create a group-node
        group_node = SceneNode()
        group_decorator = GroupDecorator()
        group_node.addDecorator(group_decorator)
        group_node.setParent(self.getController().getScene().getRoot())
        group_node.setSelectable(True)
        center = Selection.getSelectionCenter()
        group_node.setPosition(center)
        group_node.setCenterPosition(center)

        # Move selected nodes into the group-node
        Selection.applyOperation(SetParentOperation, group_node)

        # Deselect individual nodes and select the group-node instead
        for node in group_node.getChildren():
            Selection.remove(node)
        Selection.add(group_node)

    @pyqtSlot()
    def ungroupSelected(self):
        selected_objects = Selection.getAllSelectedObjects().copy()
        for node in selected_objects:
            if node.callDecoration("isGroup"):
                op = GroupedOperation()

                group_parent = node.getParent()
                children = node.getChildren().copy()
                for child in children:
                    # Set the parent of the children to the parent of the group-node
                    op.addOperation(SetParentOperation(child, group_parent))

                    # Add all individual nodes to the selection
                    Selection.add(child)

                op.push()
                # Note: The group removes itself from the scene once all its children have left it,
                # see GroupDecorator._onChildrenChanged

    def _createSplashScreen(self):
        return CuraSplashScreen.CuraSplashScreen()

    def _onActiveMachineChanged(self):
        pass

    fileLoaded = pyqtSignal(str)

    def _onFileLoaded(self, job):
        node = job.getResult()
        if node != None:
            self.fileLoaded.emit(job.getFileName())
            node.setSelectable(True)
            node.setName(os.path.basename(job.getFileName()))
            op = AddSceneNodeOperation(node, self.getController().getScene().getRoot())
            op.push()

            self.getController().getScene().sceneChanged.emit(node) #Force scene change.

    def _onJobFinished(self, job):
        if type(job) is not ReadMeshJob or not job.getResult():
            return

        f = QUrl.fromLocalFile(job.getFileName())
        if f in self._recent_files:
            self._recent_files.remove(f)

        self._recent_files.insert(0, f)
        if len(self._recent_files) > 10:
            del self._recent_files[10]

        pref = ""
        for path in self._recent_files:
            pref += path.toLocalFile() + ";"

        Preferences.getInstance().setValue("cura/recent_files", pref)
        self.recentFilesChanged.emit()

    def _reloadMeshFinished(self, job):
        # TODO; This needs to be fixed properly. We now make the assumption that we only load a single mesh!
        mesh_data = job.getResult().getMeshData()
        if mesh_data:
            job._node.setMeshData(mesh_data)
        else:
            Logger.log("w", "Could not find a mesh in reloaded node.")

    def _openFile(self, file):
        job = ReadMeshJob(os.path.abspath(file))
        job.finished.connect(self._onFileLoaded)
        job.start()

    def _addProfileReader(self, profile_reader):
        # TODO: Add the profile reader to the list of plug-ins that can be used when importing profiles.
        pass

    def _addProfileWriter(self, profile_writer):
        pass

    @pyqtSlot("QSize")
    def setMinimumWindowSize(self, size):
        self.getMainWindow().setMinimumSize(size)

    def getBuildVolume(self):
        return self._volume

    additionalComponentsChanged = pyqtSignal(str, arguments = ["areaId"])

    @pyqtProperty("QVariantMap", notify = additionalComponentsChanged)
    def additionalComponents(self):
        return self._additional_components

    ##  Add a component to a list of components to be reparented to another area in the GUI.
    #   The actual reparenting is done by the area itself.
    #   \param area_id \type{str} Identifying name of the area to which the component should be reparented
    #   \param component \type{QQuickComponent} The component that should be reparented
    @pyqtSlot(str, "QVariant")
    def addAdditionalComponent(self, area_id, component):
        if area_id not in self._additional_components:
            self._additional_components[area_id] = []
        self._additional_components[area_id].append(component)

        self.additionalComponentsChanged.emit(area_id)

    @pyqtSlot(str)
    def log(self, msg):
        Logger.log("d", msg)
