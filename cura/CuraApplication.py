# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from PyQt5.QtNetwork import QLocalServer
from PyQt5.QtNetwork import QLocalSocket

from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Matrix import Matrix
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
from UM.Message import Message
from UM.i18n import i18nCatalog

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation
from UM.Operations.TranslateOperation import TranslateOperation
from cura.SetParentOperation import SetParentOperation
from cura.SliceableObjectDecorator import SliceableObjectDecorator
from cura.BlockSlicingDecorator import BlockSlicingDecorator

from UM.Settings.SettingDefinition import SettingDefinition, DefinitionPropertyType
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingFunction import SettingFunction

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

from PyQt5.QtCore import QUrl, pyqtSignal, pyqtProperty, QEvent, Q_ENUMS
from UM.FlameProfiler import pyqtSlot
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtQml import qmlRegisterUncreatableType, qmlRegisterSingletonType, qmlRegisterType

import sys
import os.path
import numpy
import copy
import urllib.parse
import os
import argparse
import json

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
        SettingDefinition.addSupportedProperty("resolve", DefinitionPropertyType.Function, default = None, depends_on = "value")

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
                ("extruder_train", UM.Settings.ContainerStack.Version): (self.ResourceTypes.ExtruderStack, "application/x-uranium-extruderstack"),
                ("preferences", UM.Preferences.Version):               (Resources.Preferences, "application/x-uranium-preferences"),
                ("user", UM.Settings.InstanceContainer.Version):       (self.ResourceTypes.UserInstanceContainer, "application/x-uranium-instancecontainer")
            }
        )

        self._currently_loading_files = []
        self._non_sliceable_extensions = []

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

        with ContainerRegistry.getInstance().lockFile():
            ContainerRegistry.getInstance().load()

        Preferences.getInstance().addPreference("cura/active_mode", "simple")
        Preferences.getInstance().addPreference("cura/recent_files", "")
        Preferences.getInstance().addPreference("cura/categories_expanded", "")
        Preferences.getInstance().addPreference("cura/jobname_prefix", True)
        Preferences.getInstance().addPreference("view/center_on_select", False)
        Preferences.getInstance().addPreference("mesh/scale_to_fit", False)
        Preferences.getInstance().addPreference("mesh/scale_tiny_meshes", True)
        Preferences.getInstance().addPreference("cura/dialog_on_project_save", True)
        Preferences.getInstance().addPreference("cura/asked_dialog_on_project_save", False)

        Preferences.getInstance().addPreference("cura/currency", "€")
        Preferences.getInstance().addPreference("cura/material_settings", "{}")

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
                z_seam_x
                z_seam_y
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

    def setViewLegendItems(self, items):
        self.viewLegendItemsChanged.emit(items)

    viewLegendItemsChanged = pyqtSignal("QVariantList", arguments = ["items"])

    ##  Cura has multiple locations where instance containers need to be saved, so we need to handle this differently.
    #
    #   Note that the AutoSave plugin also calls this method.
    def saveSettings(self):
        if not self._started: # Do not do saving during application start
            return

        # Lock file for "more" atomically loading and saving to/from config dir.
        with ContainerRegistry.getInstance().lockFile():
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
                elif instance_type == "definition_changes":
                    path = Resources.getStoragePath(self.ResourceTypes.MachineStack, file_name)

                if path:
                    instance.setPath(path)
                    with SaveFile(path, "wt") as f:
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
            with SaveFile(path, "wt") as f:
                f.write(data)


    @pyqtSlot(str, result = QUrl)
    def getDefaultPath(self, key):
        default_path = Preferences.getInstance().getValue("local_file/%s" % key)
        return QUrl.fromLocalFile(default_path)

    @pyqtSlot(str, str)
    def setDefaultPath(self, key, default_path):
        Preferences.getInstance().setValue("local_file/%s" % key, QUrl(default_path).toLocalFile())

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

    @classmethod
    def addCommandLineOptions(self, parser):
        super().addCommandLineOptions(parser)
        parser.add_argument("file", nargs="*", help="Files to load after starting the application.")
        parser.add_argument("--single-instance", action="store_true", default=False)

    # Set up a local socket server which listener which coordinates single instances Curas and accepts commands.
    def _setUpSingleInstanceServer(self):
        if self.getCommandLineOption("single_instance", False):
            self.__single_instance_server = QLocalServer()
            self.__single_instance_server.newConnection.connect(self._singleInstanceServerNewConnection)
            self.__single_instance_server.listen("ultimaker-cura")

    def _singleInstanceServerNewConnection(self):
        Logger.log("i", "New connection recevied on our single-instance server")
        remote_cura_connection = self.__single_instance_server.nextPendingConnection()

        if remote_cura_connection is not None:
            def readCommands():
                line = remote_cura_connection.readLine()
                while len(line) != 0:    # There is also a .canReadLine()
                    try:
                        payload = json.loads(str(line, encoding="ASCII").strip())
                        command = payload["command"]

                        # Command: Remove all models from the build plate.
                        if command == "clear-all":
                            self.deleteAll()

                        # Command: Load a model file
                        elif command == "open":
                            self._openFile(payload["filePath"])
                            # WARNING ^ this method is async and we really should wait until
                            # the file load is complete before processing more commands.

                        # Command: Activate the window and bring it to the top.
                        elif command == "focus":
                            # Operating systems these days prevent windows from moving around by themselves.
                            # 'alert' or flashing the icon in the taskbar is the best thing we do now.
                            self.getMainWindow().alert(0)

                        else:
                            Logger.log("w", "Received an unrecognized command " + str(command))
                    except json.decoder.JSONDecodeError as ex:
                        Logger.log("w", "Unable to parse JSON command in _singleInstanceServerNewConnection(): " + repr(ex))
                    line = remote_cura_connection.readLine()

            remote_cura_connection.readyRead.connect(readCommands)
            remote_cura_connection.disconnected.connect(readCommands)    # Get any last commands before it is destroyed.

    ##  Perform any checks before creating the main application.
    #
    #   This should be called directly before creating an instance of CuraApplication.
    #   \returns \type{bool} True if the whole Cura app should continue running.
    @classmethod
    def preStartUp(cls):
        # Peek the arguments and look for the 'single-instance' flag.
        parser = argparse.ArgumentParser(prog="cura")  # pylint: disable=bad-whitespace
        CuraApplication.addCommandLineOptions(parser)
        parsed_command_line = vars(parser.parse_args())

        if "single_instance" in parsed_command_line and parsed_command_line["single_instance"]:
            Logger.log("i", "Checking for the presence of an ready running Cura instance.")
            single_instance_socket = QLocalSocket()
            single_instance_socket.connectToServer("ultimaker-cura")
            single_instance_socket.waitForConnected()
            if single_instance_socket.state() == QLocalSocket.ConnectedState:
                Logger.log("i", "Connection has been made to the single-instance Cura socket.")

                # Protocol is one line of JSON terminated with a carriage return.
                # "command" field is required and holds the name of the command to execute.
                # Other fields depend on the command.

                payload = {"command": "clear-all"}
                single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding="ASCII"))

                payload = {"command": "focus"}
                single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding="ASCII"))

                if len(parsed_command_line["file"]) != 0:
                    for filename in parsed_command_line["file"]:
                        payload = {"command": "open", "filePath": filename}
                        single_instance_socket.write(bytes(json.dumps(payload) + "\n", encoding="ASCII"))
                single_instance_socket.flush()
                single_instance_socket.close()
                return False
        return True

    def run(self):
        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Setting up scene..."))

        self._setUpSingleInstanceServer()

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
        qmlRegisterSingletonType(cura.Settings.ProfilesModel, "Cura", 1, 0, "ProfilesModel", cura.Settings.ProfilesModel.createProfilesModel)
        qmlRegisterType(cura.Settings.QualityAndUserProfilesModel, "Cura", 1, 0, "QualityAndUserProfilesModel")
        qmlRegisterType(cura.Settings.UserProfilesModel, "Cura", 1, 0, "UserProfilesModel")
        qmlRegisterType(cura.Settings.MaterialSettingsVisibilityHandler, "Cura", 1, 0, "MaterialSettingsVisibilityHandler")
        qmlRegisterType(cura.Settings.QualitySettingsModel, "Cura", 1, 0, "QualitySettingsModel")
        qmlRegisterType(cura.Settings.MachineNameValidator, "Cura", 1, 0, "MachineNameValidator")

        qmlRegisterSingletonType(cura.Settings.ContainerManager, "Cura", 1, 0, "ContainerManager", cura.Settings.ContainerManager.createContainerManager)

        # As of Qt5.7, it is necessary to get rid of any ".." in the path for the singleton to work.
        actions_url = QUrl.fromLocalFile(os.path.abspath(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles, "Actions.qml")))
        qmlRegisterSingletonType(actions_url, "Cura", 1, 0, "Actions")

        engine.rootContext().setContextProperty("ExtruderManager", cura.Settings.ExtruderManager.getInstance())

        for path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.QmlFiles):
            type_name = os.path.splitext(os.path.basename(path))[0]
            if type_name in ("Cura", "Actions"):
                continue

            qmlRegisterType(QUrl.fromLocalFile(path), "Cura", 1, 0, type_name)

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if self.getController().getActiveTool():
                # If the tool has been disabled by the new selection
                if not self.getController().getActiveTool().getEnabled():
                    # Default
                    self.getController().setActiveTool("TranslateTool")
            else:
                if self._previous_active_tool:
                    self.getController().setActiveTool(self._previous_active_tool)
                    if not self.getController().getActiveTool().getEnabled():
                        self.getController().setActiveTool("TranslateTool")
                    self._previous_active_tool = None
                else:
                    # Default
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
        is_block_slicing_node = False
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or (not node.getMeshData() and not node.callDecoration("getLayerData")):
                continue
            if node.callDecoration("isBlockSlicing"):
                is_block_slicing_node = True

            count += 1
            if not scene_bounding_box:
                scene_bounding_box = node.getBoundingBox()
            else:
                other_bb = node.getBoundingBox()
                if other_bb is not None:
                    scene_bounding_box = scene_bounding_box + node.getBoundingBox()

        print_information = self.getPrintInformation()
        if print_information:
            print_information.setPreSliced(is_block_slicing_node)

        if not scene_bounding_box:
            scene_bounding_box = AxisAlignedBox.Null

        if repr(self._scene_bounding_box) != repr(scene_bounding_box) and scene_bounding_box.isValid():
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

            op = GroupedOperation()
            for _ in range(count):
                new_node = copy.deepcopy(current_node)
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
            if not node.isSelectable():
                continue  # i.e. node with layer data
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
            if (not node.getMeshData() and not node.callDecoration("getLayerData")) and not node.callDecoration("isGroup"):
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
            if not node.isSelectable():
                continue  # i.e. node with layer data
            nodes.append(node)

        if nodes:
            op = GroupedOperation()
            for node in nodes:
                # Ensure that the object is above the build platform
                node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
                if node.getBoundingBox():
                    center_y = node.getWorldPosition().y - node.getBoundingBox().bottom
                else:
                    center_y = 0
                op.addOperation(SetTransformOperation(node, Vector(0, center_y, 0)))
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
            if not node.isSelectable():
                continue  # i.e. node with layer data
            nodes.append(node)

        if nodes:
            op = GroupedOperation()
            for node in nodes:
                # Ensure that the object is above the build platform
                node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
                if node.getBoundingBox():
                    center_y = node.getWorldPosition().y - node.getBoundingBox().bottom
                else:
                    center_y = 0
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

        meshes = [node.getMeshData() for node in group_node.getAllChildren() if node.getMeshData()]

        # Compute the center of the objects
        object_centers = []
        # Forget about the translation that the original objects have
        zero_translation = Matrix(data=numpy.zeros(3))
        for mesh, node in zip(meshes, group_node.getChildren()):
            transformation = node.getLocalTransformation()
            transformation.setTranslation(zero_translation)
            transformed_mesh = mesh.getTransformed(transformation)
            center = transformed_mesh.getCenterPosition()
            object_centers.append(center)
        if object_centers and len(object_centers) > 0:
            middle_x = sum([v.x for v in object_centers]) / len(object_centers)
            middle_y = sum([v.y for v in object_centers]) / len(object_centers)
            middle_z = sum([v.z for v in object_centers]) / len(object_centers)
            offset = Vector(middle_x, middle_y, middle_z)
        else:
            offset = Vector(0, 0, 0)

        # Move each node to the same position.
        for mesh, node in zip(meshes, group_node.getChildren()):
            transformation = node.getLocalTransformation()
            transformation.setTranslation(zero_translation)
            transformed_mesh = mesh.getTransformed(transformation)

            # Align the object around its zero position
            # and also apply the offset to center it inside the group.
            node.setPosition(-transformed_mesh.getZeroPosition() - offset)

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
        nodes = job.getResult()
        for node in nodes:
            if node is not None:
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
        mesh_data = job.getResult()[0].getMeshData()
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

    @pyqtSlot(QUrl)
    def readLocalFile(self, file):
        if not file.isValid():
            return

        scene = self.getController().getScene()

        for node in DepthFirstIterator(scene.getRoot()):
            if node.callDecoration("isBlockSlicing"):
                self.deleteAll()
                break

        f = file.toLocalFile()
        extension = os.path.splitext(f)[1]
        filename = os.path.basename(f)
        if len(self._currently_loading_files) > 0:
            # If a non-slicable file is already being loaded, we prevent loading of any further non-slicable files
            if extension.lower() in self._non_sliceable_extensions:
                message = Message(
                    self._i18n_catalog.i18nc("@info:status",
                                       "Only one G-code file can be loaded at a time. Skipped importing {0}",
                                       filename))
                message.show()
                return
            # If file being loaded is non-slicable file, then prevent loading of any other files
            extension = os.path.splitext(self._currently_loading_files[0])[1]
            if extension.lower() in self._non_sliceable_extensions:
                message = Message(
                    self._i18n_catalog.i18nc("@info:status",
                                       "Can't open any other file if G-code is loading. Skipped importing {0}",
                                       filename))
                message.show()
                return

        self._currently_loading_files.append(f)
        if extension in self._non_sliceable_extensions:
            self.deleteAll()

        job = ReadMeshJob(f)
        job.finished.connect(self._readMeshFinished)
        job.start()

    def _readMeshFinished(self, job):
        nodes = job.getResult()
        filename = job.getFileName()
        self._currently_loading_files.remove(filename)

        for node in nodes:
            node.setSelectable(True)
            node.setName(os.path.basename(filename))

            extension = os.path.splitext(filename)[1]
            if extension.lower() in self._non_sliceable_extensions:
                self.getController().setActiveView("LayerView")
                view = self.getController().getActiveView()
                view.resetLayerData()
                view.setLayer(9999999)
                view.calculateMaxLayers()

                block_slicing_decorator = BlockSlicingDecorator()
                node.addDecorator(block_slicing_decorator)
            else:
                sliceable_decorator = SliceableObjectDecorator()
                node.addDecorator(sliceable_decorator)

            scene = self.getController().getScene()

            op = AddSceneNodeOperation(node, scene.getRoot())
            op.push()

            scene.sceneChanged.emit(node)

    def addNonSliceableExtension(self, extension):
        self._non_sliceable_extensions.append(extension)
