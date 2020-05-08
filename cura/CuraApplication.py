# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import sys
import time
from typing import cast, TYPE_CHECKING, Optional, Callable, List, Any, Dict

import numpy
from PyQt5.QtCore import QObject, QTimer, QUrl, pyqtSignal, pyqtProperty, QEvent, Q_ENUMS
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtQml import qmlRegisterUncreatableType, qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtWidgets import QMessageBox

import UM.Util
import cura.Settings.cura_empty_instance_containers
from UM.Application import Application
from UM.Decorators import override
from UM.FlameProfiler import pyqtSlot
from UM.Logger import Logger
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Mesh.ReadMeshJob import ReadMeshJob
from UM.Message import Message
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation
from UM.Platform import Platform
from UM.PluginError import PluginNotFoundError
from UM.Preferences import Preferences
from UM.Qt.QtApplication import QtApplication  # The class we're inheriting from.
from UM.Resources import Resources
from UM.Scene.Camera import Camera
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Scene.ToolHandle import ToolHandle
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.SettingDefinition import SettingDefinition, DefinitionPropertyType
from UM.Settings.SettingFunction import SettingFunction
from UM.Settings.Validator import Validator
from UM.View.SelectionPass import SelectionPass  # For typing.
from UM.Workspace.WorkspaceReader import WorkspaceReader
from UM.i18n import i18nCatalog
from cura import ApplicationMetadata
from cura.API import CuraAPI
from cura.Arranging.Arrange import Arrange
from cura.Arranging.ArrangeObjectsAllBuildPlatesJob import ArrangeObjectsAllBuildPlatesJob
from cura.Arranging.ArrangeObjectsJob import ArrangeObjectsJob
from cura.Arranging.ShapeArray import ShapeArray
from cura.Machines.MachineErrorChecker import MachineErrorChecker
from cura.Machines.Models.BuildPlateModel import BuildPlateModel
from cura.Machines.Models.CustomQualityProfilesDropDownMenuModel import CustomQualityProfilesDropDownMenuModel
from cura.Machines.Models.DiscoveredPrintersModel import DiscoveredPrintersModel
from cura.Machines.Models.DiscoveredCloudPrintersModel import DiscoveredCloudPrintersModel
from cura.Machines.Models.ExtrudersModel import ExtrudersModel
from cura.Machines.Models.FavoriteMaterialsModel import FavoriteMaterialsModel
from cura.Machines.Models.FirstStartMachineActionsModel import FirstStartMachineActionsModel
from cura.Machines.Models.GenericMaterialsModel import GenericMaterialsModel
from cura.Machines.Models.GlobalStacksModel import GlobalStacksModel
from cura.Machines.Models.IntentCategoryModel import IntentCategoryModel
from cura.Machines.Models.IntentModel import IntentModel
from cura.Machines.Models.MaterialBrandsModel import MaterialBrandsModel
from cura.Machines.Models.MaterialManagementModel import MaterialManagementModel
from cura.Machines.Models.MultiBuildPlateModel import MultiBuildPlateModel
from cura.Machines.Models.NozzleModel import NozzleModel
from cura.Machines.Models.QualityManagementModel import QualityManagementModel
from cura.Machines.Models.QualityProfilesDropDownMenuModel import QualityProfilesDropDownMenuModel
from cura.Machines.Models.QualitySettingsModel import QualitySettingsModel
from cura.Machines.Models.SettingVisibilityPresetsModel import SettingVisibilityPresetsModel
from cura.Machines.Models.UserChangesModel import UserChangesModel
from cura.Operations.SetParentOperation import SetParentOperation
from cura.PrinterOutput.NetworkMJPGImage import NetworkMJPGImage
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice
from cura.Scene import ZOffsetDecorator
from cura.Scene.BlockSlicingDecorator import BlockSlicingDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator
from cura.Scene.CuraSceneController import CuraSceneController
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Settings.ContainerManager import ContainerManager
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.CuraFormulaFunctions import CuraFormulaFunctions
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtruderStack import ExtruderStack
from cura.Settings.GlobalStack import GlobalStack
from cura.Settings.IntentManager import IntentManager
from cura.Settings.MachineManager import MachineManager
from cura.Settings.MachineNameValidator import MachineNameValidator
from cura.Settings.MaterialSettingsVisibilityHandler import MaterialSettingsVisibilityHandler
from cura.Settings.SettingInheritanceManager import SettingInheritanceManager
from cura.Settings.SidebarCustomMenuItemsModel import SidebarCustomMenuItemsModel
from cura.Settings.SimpleModeSettingsManager import SimpleModeSettingsManager
from cura.TaskManagement.OnExitCallbackManager import OnExitCallbackManager
from cura.UI import CuraSplashScreen, MachineActionManager, PrintInformation
from cura.UI.AddPrinterPagesModel import AddPrinterPagesModel
from cura.UI.MachineSettingsManager import MachineSettingsManager
from cura.UI.ObjectsModel import ObjectsModel
from cura.UI.RecommendedMode import RecommendedMode
from cura.UI.TextManager import TextManager
from cura.UI.WelcomePagesModel import WelcomePagesModel
from cura.UI.WhatsNewPagesModel import WhatsNewPagesModel
from cura.UltimakerCloud import UltimakerCloudAuthentication
from cura.Utils.NetworkingUtil import NetworkingUtil
from . import BuildVolume
from . import CameraAnimation
from . import CuraActions
from . import PlatformPhysics
from . import PrintJobPreviewImageProvider
from .AutoSave import AutoSave
from .SingleInstance import SingleInstance

if TYPE_CHECKING:
    from UM.Settings.EmptyInstanceContainer import EmptyInstanceContainer

numpy.seterr(all = "ignore")


class CuraApplication(QtApplication):
    # SettingVersion represents the set of settings available in the machine/extruder definitions.
    # You need to make sure that this version number needs to be increased if there is any non-backwards-compatible
    # changes of the settings.
    SettingVersion = 13

    Created = False

    class ResourceTypes:
        QmlFiles = Resources.UserType + 1
        Firmware = Resources.UserType + 2
        QualityInstanceContainer = Resources.UserType + 3
        QualityChangesInstanceContainer = Resources.UserType + 4
        MaterialInstanceContainer = Resources.UserType + 5
        VariantInstanceContainer = Resources.UserType + 6
        UserInstanceContainer = Resources.UserType + 7
        MachineStack = Resources.UserType + 8
        ExtruderStack = Resources.UserType + 9
        DefinitionChangesContainer = Resources.UserType + 10
        SettingVisibilityPreset = Resources.UserType + 11
        IntentInstanceContainer = Resources.UserType + 12

    Q_ENUMS(ResourceTypes)

    def __init__(self, *args, **kwargs):
        super().__init__(name = ApplicationMetadata.CuraAppName,
                         app_display_name = ApplicationMetadata.CuraAppDisplayName,
                         version = ApplicationMetadata.CuraVersion,
                         api_version = ApplicationMetadata.CuraSDKVersion,
                         build_type = ApplicationMetadata.CuraBuildType,
                         is_debug_mode = ApplicationMetadata.CuraDebugMode,
                         tray_icon_name = "cura-icon-32.png",
                         **kwargs)

        self.default_theme = "cura-light"

        self.change_log_url = "https://ultimaker.com/ultimaker-cura-latest-features"

        self._boot_loading_time = time.time()

        self._on_exit_callback_manager = OnExitCallbackManager(self)

        # Variables set from CLI
        self._files_to_open = []
        self._use_single_instance = False

        self._single_instance = None

        self._cura_formula_functions = None  # type: Optional[CuraFormulaFunctions]

        self._machine_action_manager = None  # type: Optional[MachineActionManager.MachineActionManager]

        self.empty_container = None  # type: EmptyInstanceContainer
        self.empty_definition_changes_container = None  # type: EmptyInstanceContainer
        self.empty_variant_container = None  # type: EmptyInstanceContainer
        self.empty_intent_container = None  # type: EmptyInstanceContainer 
        self.empty_material_container = None  # type: EmptyInstanceContainer
        self.empty_quality_container = None  # type: EmptyInstanceContainer
        self.empty_quality_changes_container = None  # type: EmptyInstanceContainer

        self._material_manager = None
        self._machine_manager = None
        self._extruder_manager = None
        self._container_manager = None

        self._object_manager = None
        self._extruders_model = None
        self._extruders_model_with_optional = None
        self._build_plate_model = None
        self._multi_build_plate_model = None
        self._setting_visibility_presets_model = None
        self._setting_inheritance_manager = None
        self._simple_mode_settings_manager = None
        self._cura_scene_controller = None
        self._machine_error_checker = None

        self._machine_settings_manager = MachineSettingsManager(self, parent = self)
        self._material_management_model = None
        self._quality_management_model = None

        self._discovered_printer_model = DiscoveredPrintersModel(self, parent = self)
        self._discovered_cloud_printers_model = DiscoveredCloudPrintersModel(self, parent = self)
        self._first_start_machine_actions_model = None
        self._welcome_pages_model = WelcomePagesModel(self, parent = self)
        self._add_printer_pages_model = AddPrinterPagesModel(self, parent = self)
        self._whats_new_pages_model = WhatsNewPagesModel(self, parent = self)
        self._text_manager = TextManager(parent = self)

        self._quality_profile_drop_down_menu_model = None
        self._custom_quality_profile_drop_down_menu_model = None
        self._cura_API = CuraAPI(self)

        self._physics = None
        self._volume = None
        self._output_devices = {}
        self._print_information = None
        self._previous_active_tool = None
        self._platform_activity = False
        self._scene_bounding_box = AxisAlignedBox.Null

        self._center_after_select = False
        self._camera_animation = None
        self._cura_actions = None
        self.started = False

        self._message_box_callback = None
        self._message_box_callback_arguments = []
        self._i18n_catalog = None

        self._currently_loading_files = []
        self._non_sliceable_extensions = []
        self._additional_components = {}  # Components to add to certain areas in the interface

        self._open_file_queue = []  # A list of files to open (after the application has started)

        self._update_platform_activity_timer = None

        self._sidebar_custom_menu_items = []  # type: list # Keeps list of custom menu items for the side bar

        self._plugins_loaded = False

        # Backups
        self._auto_save = None  # type: Optional[AutoSave]
        self._enable_save = True

        self._container_registry_class = CuraContainerRegistry
        # Redefined here in order to please the typing.
        self._container_registry = None # type: CuraContainerRegistry
        from cura.CuraPackageManager import CuraPackageManager
        self._package_manager_class = CuraPackageManager

    @pyqtProperty(str, constant=True)
    def ultimakerCloudApiRootUrl(self) -> str:
        return UltimakerCloudAuthentication.CuraCloudAPIRoot

    @pyqtProperty(str, constant = True)
    def ultimakerCloudAccountRootUrl(self) -> str:
        return UltimakerCloudAuthentication.CuraCloudAccountAPIRoot

    def addCommandLineOptions(self):
        """Adds command line options to the command line parser.

        This should be called after the application is created and before the pre-start.
        """

        super().addCommandLineOptions()
        self._cli_parser.add_argument("--help", "-h",
                                      action = "store_true",
                                      default = False,
                                      help = "Show this help message and exit.")
        self._cli_parser.add_argument("--single-instance",
                                      dest = "single_instance",
                                      action = "store_true",
                                      default = False)
        # >> For debugging
        # Trigger an early crash, i.e. a crash that happens before the application enters its event loop.
        self._cli_parser.add_argument("--trigger-early-crash",
                                      dest = "trigger_early_crash",
                                      action = "store_true",
                                      default = False,
                                      help = "FOR TESTING ONLY. Trigger an early crash to show the crash dialog.")
        self._cli_parser.add_argument("file", nargs = "*", help = "Files to load after starting the application.")

    def getContainerRegistry(self) -> "CuraContainerRegistry":
        return self._container_registry

    def parseCliOptions(self):
        super().parseCliOptions()

        if self._cli_args.help:
            self._cli_parser.print_help()
            sys.exit(0)

        self._use_single_instance = self._cli_args.single_instance
        # FOR TESTING ONLY
        if self._cli_args.trigger_early_crash:
            assert not "This crash is triggered by the trigger_early_crash command line argument."

        for filename in self._cli_args.file:
            self._files_to_open.append(os.path.abspath(filename))

    def initialize(self) -> None:
        self.__addExpectedResourceDirsAndSearchPaths()  # Must be added before init of super

        super().initialize()

        self.__sendCommandToSingleInstance()
        self._initializeSettingDefinitions()
        self._initializeSettingFunctions()
        self.__addAllResourcesAndContainerResources()
        self.__addAllEmptyContainers()
        self.__setLatestResouceVersionsForVersionUpgrade()

        self._machine_action_manager = MachineActionManager.MachineActionManager(self)
        self._machine_action_manager.initialize()

    def __sendCommandToSingleInstance(self):
        self._single_instance = SingleInstance(self, self._files_to_open)

        # If we use single instance, try to connect to the single instance server, send commands, and then exit.
        # If we cannot find an existing single instance server, this is the only instance, so just keep going.
        if self._use_single_instance:
            if self._single_instance.startClient():
                Logger.log("i", "Single instance commands were sent, exiting")
                sys.exit(0)

    def __addExpectedResourceDirsAndSearchPaths(self):
        """Adds expected directory names and search paths for Resources."""

        # this list of dir names will be used by UM to detect an old cura directory
        for dir_name in ["extruders", "machine_instances", "materials", "plugins", "quality", "quality_changes", "user", "variants", "intent"]:
            Resources.addExpectedDirNameInData(dir_name)

        app_root = os.path.abspath(os.path.join(os.path.dirname(sys.executable)))
        Resources.addSearchPath(os.path.join(app_root, "share", "cura", "resources"))

        Resources.addSearchPath(os.path.join(self._app_install_dir, "share", "cura", "resources"))
        if not hasattr(sys, "frozen"):
            resource_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "resources")
            Resources.addSearchPath(resource_path)

    @classmethod
    def _initializeSettingDefinitions(cls):
        # Need to do this before ContainerRegistry tries to load the machines
        SettingDefinition.addSupportedProperty("settable_per_mesh", DefinitionPropertyType.Any, default=True,
                                               read_only=True)
        SettingDefinition.addSupportedProperty("settable_per_extruder", DefinitionPropertyType.Any, default=True,
                                               read_only=True)
        # this setting can be changed for each group in one-at-a-time mode
        SettingDefinition.addSupportedProperty("settable_per_meshgroup", DefinitionPropertyType.Any, default=True,
                                               read_only=True)
        SettingDefinition.addSupportedProperty("settable_globally", DefinitionPropertyType.Any, default=True,
                                               read_only=True)

        # From which stack the setting would inherit if not defined per object (handled in the engine)
        # AND for settings which are not settable_per_mesh:
        # which extruder is the only extruder this setting is obtained from
        SettingDefinition.addSupportedProperty("limit_to_extruder", DefinitionPropertyType.Function, default="-1",
                                               depends_on="value")

        # For settings which are not settable_per_mesh and not settable_per_extruder:
        # A function which determines the glabel/meshgroup value by looking at the values of the setting in all (used) extruders
        SettingDefinition.addSupportedProperty("resolve", DefinitionPropertyType.Function, default=None,
                                               depends_on="value")

        SettingDefinition.addSettingType("extruder", None, str, Validator)
        SettingDefinition.addSettingType("optional_extruder", None, str, None)
        SettingDefinition.addSettingType("[int]", None, str, None)


    def _initializeSettingFunctions(self):
        """Adds custom property types, settings types, and extra operators (functions).

        Whom need to be registered in SettingDefinition and SettingFunction.
        """

        self._cura_formula_functions = CuraFormulaFunctions(self)

        SettingFunction.registerOperator("extruderValue", self._cura_formula_functions.getValueInExtruder)
        SettingFunction.registerOperator("extruderValues", self._cura_formula_functions.getValuesInAllExtruders)
        SettingFunction.registerOperator("resolveOrValue", self._cura_formula_functions.getResolveOrValue)
        SettingFunction.registerOperator("defaultExtruderPosition", self._cura_formula_functions.getDefaultExtruderPosition)
        SettingFunction.registerOperator("valueFromContainer", self._cura_formula_functions.getValueFromContainerAtIndex)
        SettingFunction.registerOperator("extruderValueFromContainer", self._cura_formula_functions.getValueFromContainerAtIndexInExtruder)

    def __addAllResourcesAndContainerResources(self) -> None:
        """Adds all resources and container related resources."""

        Resources.addStorageType(self.ResourceTypes.QualityInstanceContainer, "quality")
        Resources.addStorageType(self.ResourceTypes.QualityChangesInstanceContainer, "quality_changes")
        Resources.addStorageType(self.ResourceTypes.VariantInstanceContainer, "variants")
        Resources.addStorageType(self.ResourceTypes.MaterialInstanceContainer, "materials")
        Resources.addStorageType(self.ResourceTypes.UserInstanceContainer, "user")
        Resources.addStorageType(self.ResourceTypes.ExtruderStack, "extruders")
        Resources.addStorageType(self.ResourceTypes.MachineStack, "machine_instances")
        Resources.addStorageType(self.ResourceTypes.DefinitionChangesContainer, "definition_changes")
        Resources.addStorageType(self.ResourceTypes.SettingVisibilityPreset, "setting_visibility")
        Resources.addStorageType(self.ResourceTypes.IntentInstanceContainer, "intent")

        self._container_registry.addResourceType(self.ResourceTypes.QualityInstanceContainer, "quality")
        self._container_registry.addResourceType(self.ResourceTypes.QualityChangesInstanceContainer, "quality_changes")
        self._container_registry.addResourceType(self.ResourceTypes.VariantInstanceContainer, "variant")
        self._container_registry.addResourceType(self.ResourceTypes.MaterialInstanceContainer, "material")
        self._container_registry.addResourceType(self.ResourceTypes.UserInstanceContainer, "user")
        self._container_registry.addResourceType(self.ResourceTypes.ExtruderStack, "extruder_train")
        self._container_registry.addResourceType(self.ResourceTypes.MachineStack, "machine")
        self._container_registry.addResourceType(self.ResourceTypes.DefinitionChangesContainer, "definition_changes")
        self._container_registry.addResourceType(self.ResourceTypes.IntentInstanceContainer, "intent")

        Resources.addType(self.ResourceTypes.QmlFiles, "qml")
        Resources.addType(self.ResourceTypes.Firmware, "firmware")

    def __addAllEmptyContainers(self) -> None:
        """Adds all empty containers."""

        # Add empty variant, material and quality containers.
        # Since they are empty, they should never be serialized and instead just programmatically created.
        # We need them to simplify the switching between materials.
        self.empty_container = cura.Settings.cura_empty_instance_containers.empty_container

        self._container_registry.addContainer(
            cura.Settings.cura_empty_instance_containers.empty_definition_changes_container)
        self.empty_definition_changes_container = cura.Settings.cura_empty_instance_containers.empty_definition_changes_container

        self._container_registry.addContainer(cura.Settings.cura_empty_instance_containers.empty_variant_container)
        self.empty_variant_container = cura.Settings.cura_empty_instance_containers.empty_variant_container

        self._container_registry.addContainer(cura.Settings.cura_empty_instance_containers.empty_intent_container)
        self.empty_intent_container = cura.Settings.cura_empty_instance_containers.empty_intent_container

        self._container_registry.addContainer(cura.Settings.cura_empty_instance_containers.empty_material_container)
        self.empty_material_container = cura.Settings.cura_empty_instance_containers.empty_material_container

        self._container_registry.addContainer(cura.Settings.cura_empty_instance_containers.empty_quality_container)
        self.empty_quality_container = cura.Settings.cura_empty_instance_containers.empty_quality_container

        self._container_registry.addContainer(cura.Settings.cura_empty_instance_containers.empty_quality_changes_container)
        self.empty_quality_changes_container = cura.Settings.cura_empty_instance_containers.empty_quality_changes_container

    def __setLatestResouceVersionsForVersionUpgrade(self):
        """Initializes the version upgrade manager with by providing the paths for each resource type and the latest
        versions. """

        self._version_upgrade_manager.setCurrentVersions(
            {
                ("quality", InstanceContainer.Version * 1000000 + self.SettingVersion):             (self.ResourceTypes.QualityInstanceContainer, "application/x-uranium-instancecontainer"),
                ("quality_changes", InstanceContainer.Version * 1000000 + self.SettingVersion):     (self.ResourceTypes.QualityChangesInstanceContainer, "application/x-uranium-instancecontainer"),
                ("intent", InstanceContainer.Version * 1000000 + self.SettingVersion):              (self.ResourceTypes.IntentInstanceContainer, "application/x-uranium-instancecontainer"),
                ("machine_stack", GlobalStack.Version * 1000000 + self.SettingVersion):             (self.ResourceTypes.MachineStack, "application/x-cura-globalstack"),
                ("extruder_train", ExtruderStack.Version * 1000000 + self.SettingVersion):          (self.ResourceTypes.ExtruderStack, "application/x-cura-extruderstack"),
                ("preferences", Preferences.Version * 1000000 + self.SettingVersion):               (Resources.Preferences, "application/x-uranium-preferences"),
                ("user", InstanceContainer.Version * 1000000 + self.SettingVersion):                (self.ResourceTypes.UserInstanceContainer, "application/x-uranium-instancecontainer"),
                ("definition_changes", InstanceContainer.Version * 1000000 + self.SettingVersion):  (self.ResourceTypes.DefinitionChangesContainer, "application/x-uranium-instancecontainer"),
                ("variant", InstanceContainer.Version * 1000000 + self.SettingVersion):             (self.ResourceTypes.VariantInstanceContainer, "application/x-uranium-instancecontainer"),
            }
        )

    def startSplashWindowPhase(self) -> None:
        """Runs preparations that needs to be done before the starting process."""

        super().startSplashWindowPhase()

        if not self.getIsHeadLess():
            self.setWindowIcon(QIcon(Resources.getPath(Resources.Images, "cura-icon.png")))

        self.setRequiredPlugins([
            # Misc.:
            "ConsoleLogger", #You want to be able to read the log if something goes wrong.
            "CuraEngineBackend", #Cura is useless without this one since you can't slice.
            "FileLogger", #You want to be able to read the log if something goes wrong.
            "XmlMaterialProfile", #Cura crashes without this one.
            "Toolbox", #This contains the interface to enable/disable plug-ins, so if you disable it you can't enable it back.
            "PrepareStage", #Cura is useless without this one since you can't load models.
            "PreviewStage", #This shows the list of the plugin views that are installed in Cura.
            "MonitorStage", #Major part of Cura's functionality.
            "LocalFileOutputDevice", #Major part of Cura's functionality.
            "LocalContainerProvider", #Cura is useless without any profiles or setting definitions.

            # Views:
            "SimpleView", #Dependency of SolidView.
            "SolidView", #Displays models. Cura is useless without it.

            # Readers & Writers:
            "GCodeWriter", #Cura is useless if it can't write its output.
            "STLReader", #Most common model format, so disabling this makes Cura 90% useless.
            "3MFWriter", #Required for writing project files.

            # Tools:
            "CameraTool", #Needed to see the scene. Cura is useless without it.
            "SelectionTool", #Dependency of the rest of the tools.
            "TranslateTool", #You'll need this for almost every print.
        ])
        self._i18n_catalog = i18nCatalog("cura")

        self._update_platform_activity_timer = QTimer()
        self._update_platform_activity_timer.setInterval(500)
        self._update_platform_activity_timer.setSingleShot(True)
        self._update_platform_activity_timer.timeout.connect(self.updatePlatformActivity)

        self.getController().getScene().sceneChanged.connect(self.updatePlatformActivityDelayed)
        self.getController().toolOperationStopped.connect(self._onToolOperationStopped)
        self.getController().contextMenuRequested.connect(self._onContextMenuRequested)
        self.getCuraSceneController().activeBuildPlateChanged.connect(self.updatePlatformActivityDelayed)

        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Loading machines..."))

        self._container_registry.allMetadataLoaded.connect(ContainerRegistry.getInstance)

        with self._container_registry.lockFile():
            self._container_registry.loadAllMetadata()

        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Setting up preferences..."))
        # Set the setting version for Preferences
        preferences = self.getPreferences()
        preferences.addPreference("metadata/setting_version", 0)
        preferences.setValue("metadata/setting_version", self.SettingVersion)  # Don't make it equal to the default so that the setting version always gets written to the file.

        preferences.addPreference("cura/active_mode", "simple")

        preferences.addPreference("cura/categories_expanded", "")
        preferences.addPreference("cura/jobname_prefix", True)
        preferences.addPreference("cura/select_models_on_load", False)
        preferences.addPreference("view/center_on_select", False)
        preferences.addPreference("mesh/scale_to_fit", False)
        preferences.addPreference("mesh/scale_tiny_meshes", True)
        preferences.addPreference("cura/dialog_on_project_save", True)
        preferences.addPreference("cura/asked_dialog_on_project_save", False)
        preferences.addPreference("cura/choice_on_profile_override", "always_ask")
        preferences.addPreference("cura/choice_on_open_project", "always_ask")
        preferences.addPreference("cura/use_multi_build_plate", False)
        preferences.addPreference("cura/show_list_of_objects", False)
        preferences.addPreference("view/settings_list_height", 400)
        preferences.addPreference("view/settings_visible", False)
        preferences.addPreference("view/settings_xpos", 0)
        preferences.addPreference("view/settings_ypos", 56)
        preferences.addPreference("view/colorscheme_xpos", 0)
        preferences.addPreference("view/colorscheme_ypos", 56)
        preferences.addPreference("cura/currency", "€")
        preferences.addPreference("cura/material_settings", "{}")

        preferences.addPreference("view/invert_zoom", False)
        preferences.addPreference("view/filter_current_build_plate", False)
        preferences.addPreference("cura/sidebar_collapsed", False)

        preferences.addPreference("cura/favorite_materials", "")
        preferences.addPreference("cura/expanded_brands", "")
        preferences.addPreference("cura/expanded_types", "")

        preferences.addPreference("general/accepted_user_agreement", False)

        for key in [
            "dialog_load_path",  # dialog_save_path is in LocalFileOutputDevicePlugin
            "dialog_profile_path",
            "dialog_material_path"]:

            preferences.addPreference("local_file/%s" % key, os.path.expanduser("~/"))

        preferences.setDefault("local_file/last_used_type", "text/x-gcode")

        self.applicationShuttingDown.connect(self.saveSettings)
        self.engineCreatedSignal.connect(self._onEngineCreated)

        self.getCuraSceneController().setActiveBuildPlate(0)  # Initialize

        CuraApplication.Created = True

    def _onEngineCreated(self):
        self._qml_engine.addImageProvider("print_job_preview", PrintJobPreviewImageProvider.PrintJobPreviewImageProvider())

    @pyqtProperty(bool)
    def needToShowUserAgreement(self) -> bool:
        return not UM.Util.parseBool(self.getPreferences().getValue("general/accepted_user_agreement"))

    @pyqtSlot(bool)
    def setNeedToShowUserAgreement(self, set_value: bool = True) -> None:
        self.getPreferences().setValue("general/accepted_user_agreement", str(not set_value))

    @pyqtSlot(str, str)
    def writeToLog(self, severity: str, message: str) -> None:
        Logger.log(severity, message)

    # DO NOT call this function to close the application, use checkAndExitApplication() instead which will perform
    # pre-exit checks such as checking for in-progress USB printing, etc.
    # Except for the 'Decline and close' in the 'User Agreement'-step in the Welcome-pages, that should be a hard exit.
    @pyqtSlot()
    def closeApplication(self) -> None:
        Logger.log("i", "Close application")
        main_window = self.getMainWindow()
        if main_window is not None:
            main_window.close()
        else:
            self.exit(0)

    # This function first performs all upon-exit checks such as USB printing that is in progress.
    # Use this to close the application.
    @pyqtSlot()
    def checkAndExitApplication(self) -> None:
        self._on_exit_callback_manager.resetCurrentState()
        self._on_exit_callback_manager.triggerNextCallback()

    @pyqtSlot(result = bool)
    def getIsAllChecksPassed(self) -> bool:
        return self._on_exit_callback_manager.getIsAllChecksPassed()

    def getOnExitCallbackManager(self) -> "OnExitCallbackManager":
        return self._on_exit_callback_manager

    def triggerNextExitCheck(self) -> None:
        self._on_exit_callback_manager.triggerNextCallback()

    showConfirmExitDialog = pyqtSignal(str, arguments = ["message"])

    def setConfirmExitDialogCallback(self, callback: Callable) -> None:
        self._confirm_exit_dialog_callback = callback

    @pyqtSlot(bool)
    def callConfirmExitDialogCallback(self, yes_or_no: bool) -> None:
        self._confirm_exit_dialog_callback(yes_or_no)

    showPreferencesWindow = pyqtSignal()
    """Signal to connect preferences action in QML"""

    @pyqtSlot()
    def showPreferences(self) -> None:
        """Show the preferences window"""

        self.showPreferencesWindow.emit()

    # This is called by drag-and-dropping curapackage files.
    @pyqtSlot(QUrl)
    def installPackageViaDragAndDrop(self, file_url: str) -> Optional[str]:
        filename = QUrl(file_url).toLocalFile()
        return self._package_manager.installPackage(filename)

    @override(Application)
    def getGlobalContainerStack(self) -> Optional["GlobalStack"]:
        return self._global_container_stack

    @override(Application)
    def setGlobalContainerStack(self, stack: "GlobalStack") -> None:
        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Initializing Active Machine..."))
        super().setGlobalContainerStack(stack)

    showMessageBox = pyqtSignal(str,str, str, str, int, int,
                                arguments = ["title", "text", "informativeText", "detailedText","buttons", "icon"])
    """A reusable dialogbox"""

    def messageBox(self, title, text,
                   informativeText = "",
                   detailedText = "",
                   buttons = QMessageBox.Ok,
                   icon = QMessageBox.NoIcon,
                   callback = None,
                   callback_arguments = []
                   ):
        self._message_box_callback = callback
        self._message_box_callback_arguments = callback_arguments
        self.showMessageBox.emit(title, text, informativeText, detailedText, buttons, icon)

    showDiscardOrKeepProfileChanges = pyqtSignal()

    def discardOrKeepProfileChanges(self) -> bool:
        has_user_interaction = False
        choice = self.getPreferences().getValue("cura/choice_on_profile_override")
        if choice == "always_discard":
            # don't show dialog and DISCARD the profile
            self.discardOrKeepProfileChangesClosed("discard")
        elif choice == "always_keep":
            # don't show dialog and KEEP the profile
            self.discardOrKeepProfileChangesClosed("keep")
        elif not self._is_headless:
            # ALWAYS ask whether to keep or discard the profile
            self.showDiscardOrKeepProfileChanges.emit()
            has_user_interaction = True
        return has_user_interaction

    @pyqtSlot(str)
    def discardOrKeepProfileChangesClosed(self, option: str) -> None:
        global_stack = self.getGlobalContainerStack()
        if option == "discard":
            for extruder in global_stack.extruderList:
                extruder.userChanges.clear()
            global_stack.userChanges.clear()

        # if the user decided to keep settings then the user settings should be re-calculated and validated for errors
        # before slicing. To ensure that slicer uses right settings values
        elif option == "keep":
            for extruder in global_stack.extruderList:
                extruder.userChanges.update()
            global_stack.userChanges.update()

    @pyqtSlot(int)
    def messageBoxClosed(self, button):
        if self._message_box_callback:
            self._message_box_callback(button, *self._message_box_callback_arguments)
            self._message_box_callback = None
            self._message_box_callback_arguments = []

    def enableSave(self, enable: bool):
        self._enable_save = enable

    # Cura has multiple locations where instance containers need to be saved, so we need to handle this differently.
    def saveSettings(self) -> None:
        if not self.started or not self._enable_save:
            # Do not do saving during application start or when data should not be saved on quit.
            return
        ContainerRegistry.getInstance().saveDirtyContainers()
        self.savePreferences()

    def saveStack(self, stack):
        if not self._enable_save:
            return
        ContainerRegistry.getInstance().saveContainer(stack)

    @pyqtSlot(str, result = QUrl)
    def getDefaultPath(self, key):
        default_path = self.getPreferences().getValue("local_file/%s" % key)
        return QUrl.fromLocalFile(default_path)

    @pyqtSlot(str, str)
    def setDefaultPath(self, key, default_path):
        self.getPreferences().setValue("local_file/%s" % key, QUrl(default_path).toLocalFile())

    def _loadPlugins(self) -> None:
        """Handle loading of all plugin types (and the backend explicitly)
        
        :py:class:`Uranium.UM.PluginRegistry`
        """

        self._plugin_registry.setCheckIfTrusted(ApplicationMetadata.IsEnterpriseVersion)

        self._plugin_registry.addType("profile_reader", self._addProfileReader)
        self._plugin_registry.addType("profile_writer", self._addProfileWriter)

        if Platform.isLinux():
            lib_suffixes = {"", "64", "32", "x32"}  # A few common ones on different distributions.
        else:
            lib_suffixes = {""}
        for suffix in lib_suffixes:
            self._plugin_registry.addPluginLocation(os.path.join(QtApplication.getInstallPrefix(), "lib" + suffix, "cura"))
        if not hasattr(sys, "frozen"):
            self._plugin_registry.addPluginLocation(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "plugins"))
            self._plugin_registry.loadPlugin("ConsoleLogger")
            self._plugin_registry.loadPlugin("CuraEngineBackend")

        self._plugin_registry.loadPlugins()

        if self.getBackend() is None:
            raise RuntimeError("Could not load the backend plugin!")

        self._plugins_loaded = True

    def _setLoadingHint(self, hint: str):
        """Set a short, user-friendly hint about current loading status.
        
        The way this message is displayed depends on application state
        """

        if self.started:
            Logger.info(hint)
        else:
            self.showSplashMessage(hint)

    def run(self):
        super().run()

        Logger.log("i", "Initializing machine error checker")
        self._machine_error_checker = MachineErrorChecker(self)
        self._machine_error_checker.initialize()
        self.processEvents()

        Logger.log("i", "Initializing machine manager")
        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Initializing machine manager..."))
        self.getMachineManager()
        self.processEvents()

        Logger.log("i", "Initializing container manager")
        self._container_manager = ContainerManager(self)
        self.processEvents()

        # Check if we should run as single instance or not. If so, set up a local socket server which listener which
        # coordinates multiple Cura instances and accepts commands.
        if self._use_single_instance:
            self.__setUpSingleInstanceServer()

        # Setup scene and build volume
        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Initializing build volume..."))
        root = self.getController().getScene().getRoot()
        self._volume = BuildVolume.BuildVolume(self, root)
        Arrange.build_volume = self._volume

        # initialize info objects
        self._print_information = PrintInformation.PrintInformation(self)
        self._cura_actions = CuraActions.CuraActions(self)
        self.processEvents()
        # Initialize setting visibility presets model.
        self._setting_visibility_presets_model = SettingVisibilityPresetsModel(self.getPreferences(), parent = self)

        # Initialize Cura API
        self._cura_API.initialize()
        self.processEvents()
        self._output_device_manager.start()
        self._welcome_pages_model.initialize()
        self._add_printer_pages_model.initialize()
        self._whats_new_pages_model.initialize()

        # Detect in which mode to run and execute that mode
        if self._is_headless:
            self.runWithoutGUI()
        else:
            self.runWithGUI()

        self.started = True
        self.initializationFinished.emit()
        Logger.log("d", "Booting Cura took %s seconds", time.time() - self._boot_loading_time)

        # For now use a timer to postpone some things that need to be done after the application and GUI are
        # initialized, for example opening files because they may show dialogs which can be closed due to incomplete
        # GUI initialization.
        self._post_start_timer = QTimer(self)
        self._post_start_timer.setInterval(1000)
        self._post_start_timer.setSingleShot(True)
        self._post_start_timer.timeout.connect(self._onPostStart)
        self._post_start_timer.start()

        self._auto_save = AutoSave(self)
        self._auto_save.initialize()

        self.exec_()

    def __setUpSingleInstanceServer(self):
        if self._use_single_instance:
            self._single_instance.startServer()

    def _onPostStart(self):
        for file_name in self._files_to_open:
            self.callLater(self._openFile, file_name)
        for file_name in self._open_file_queue:  # Open all the files that were queued up while plug-ins were loading.
            self.callLater(self._openFile, file_name)

    initializationFinished = pyqtSignal()

    def runWithoutGUI(self):
        """Run Cura without GUI elements and interaction (server mode)."""

        self.closeSplash()

    def runWithGUI(self):
        """Run Cura with GUI (desktop mode)."""

        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Setting up scene..."))

        controller = self.getController()

        t = controller.getTool("TranslateTool")
        if t:
            t.setEnabledAxis([ToolHandle.XAxis, ToolHandle.YAxis, ToolHandle.ZAxis])

        Selection.selectionChanged.connect(self.onSelectionChanged)

        # Set default background color for scene
        self.getRenderer().setBackgroundColor(QColor(245, 245, 245))
        self.processEvents()
        # Initialize platform physics
        self._physics = PlatformPhysics.PlatformPhysics(controller, self._volume)

        # Initialize camera
        root = controller.getScene().getRoot()
        camera = Camera("3d", root)
        diagonal = self.getBuildVolume().getDiagonalSize()
        if diagonal < 1: #No printer added yet. Set a default camera distance for normal-sized printers.
            diagonal = 375
        camera.setPosition(Vector(-80, 250, 700) * diagonal / 375)
        camera.lookAt(Vector(0, 0, 0))
        controller.getScene().setActiveCamera("3d")

        # Initialize camera tool
        camera_tool = controller.getTool("CameraTool")
        camera_tool.setOrigin(Vector(0, 100, 0))
        camera_tool.setZoomRange(0.1, 2000)

        # Initialize camera animations
        self._camera_animation = CameraAnimation.CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool("CameraTool"))

        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Loading interface..."))

        # Initialize QML engine
        self.setMainQml(Resources.getPath(self.ResourceTypes.QmlFiles, "Cura.qml"))
        self._qml_import_paths.append(Resources.getPath(self.ResourceTypes.QmlFiles))
        self._setLoadingHint(self._i18n_catalog.i18nc("@info:progress", "Initializing engine..."))
        self.initializeEngine()

        # Initialize UI state
        controller.setActiveStage("PrepareStage")
        controller.setActiveView("SolidView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        # Hide the splash screen
        self.closeSplash()

    @pyqtSlot(result = QObject)
    def getDiscoveredPrintersModel(self, *args) -> "DiscoveredPrintersModel":
        return self._discovered_printer_model

    @pyqtSlot(result=QObject)
    def getDiscoveredCloudPrintersModel(self, *args) -> "DiscoveredCloudPrintersModel":
        return self._discovered_cloud_printers_model

    @pyqtSlot(result = QObject)
    def getFirstStartMachineActionsModel(self, *args) -> "FirstStartMachineActionsModel":
        if self._first_start_machine_actions_model is None:
            self._first_start_machine_actions_model = FirstStartMachineActionsModel(self, parent = self)
            if self.started:
                self._first_start_machine_actions_model.initialize()
        return self._first_start_machine_actions_model

    @pyqtSlot(result = QObject)
    def getSettingVisibilityPresetsModel(self, *args) -> SettingVisibilityPresetsModel:
        return self._setting_visibility_presets_model

    @pyqtSlot(result = QObject)
    def getWelcomePagesModel(self, *args) -> "WelcomePagesModel":
        return self._welcome_pages_model

    @pyqtSlot(result = QObject)
    def getAddPrinterPagesModel(self, *args) -> "AddPrinterPagesModel":
        return self._add_printer_pages_model

    @pyqtSlot(result = QObject)
    def getWhatsNewPagesModel(self, *args) -> "WhatsNewPagesModel":
        return self._whats_new_pages_model

    @pyqtSlot(result = QObject)
    def getMachineSettingsManager(self, *args) -> "MachineSettingsManager":
        return self._machine_settings_manager

    @pyqtSlot(result = QObject)
    def getTextManager(self, *args) -> "TextManager":
        return self._text_manager

    def getCuraFormulaFunctions(self, *args) -> "CuraFormulaFunctions":
        if self._cura_formula_functions is None:
            self._cura_formula_functions = CuraFormulaFunctions(self)
        return self._cura_formula_functions

    def getMachineErrorChecker(self, *args) -> MachineErrorChecker:
        return self._machine_error_checker

    def getMachineManager(self, *args) -> MachineManager:
        if self._machine_manager is None:
            self._machine_manager = MachineManager(self, parent = self)
        return self._machine_manager

    def getExtruderManager(self, *args) -> ExtruderManager:
        if self._extruder_manager is None:
            self._extruder_manager = ExtruderManager()
        return self._extruder_manager

    def getIntentManager(self, *args) -> IntentManager:
        return IntentManager.getInstance()

    def getObjectsModel(self, *args):
        if self._object_manager is None:
            self._object_manager = ObjectsModel(self)
        return self._object_manager

    @pyqtSlot(result = QObject)
    def getExtrudersModel(self, *args) -> "ExtrudersModel":
        if self._extruders_model is None:
            self._extruders_model = ExtrudersModel(self)
        return self._extruders_model

    @pyqtSlot(result = QObject)
    def getExtrudersModelWithOptional(self, *args) -> "ExtrudersModel":
        if self._extruders_model_with_optional is None:
            self._extruders_model_with_optional = ExtrudersModel(self)
            self._extruders_model_with_optional.setAddOptionalExtruder(True)
        return self._extruders_model_with_optional

    @pyqtSlot(result = QObject)
    def getMultiBuildPlateModel(self, *args) -> MultiBuildPlateModel:
        if self._multi_build_plate_model is None:
            self._multi_build_plate_model = MultiBuildPlateModel(self)
        return self._multi_build_plate_model

    @pyqtSlot(result = QObject)
    def getBuildPlateModel(self, *args) -> BuildPlateModel:
        if self._build_plate_model is None:
            self._build_plate_model = BuildPlateModel(self)
        return self._build_plate_model

    def getCuraSceneController(self, *args) -> CuraSceneController:
        if self._cura_scene_controller is None:
            self._cura_scene_controller = CuraSceneController.createCuraSceneController()
        return self._cura_scene_controller

    def getSettingInheritanceManager(self, *args) -> SettingInheritanceManager:
        if self._setting_inheritance_manager is None:
            self._setting_inheritance_manager = SettingInheritanceManager.createSettingInheritanceManager()
        return self._setting_inheritance_manager

    def getMachineActionManager(self, *args: Any) -> MachineActionManager.MachineActionManager:
        """Get the machine action manager
        
        We ignore any *args given to this, as we also register the machine manager as qml singleton.
        It wants to give this function an engine and script engine, but we don't care about that.
        """

        return cast(MachineActionManager.MachineActionManager, self._machine_action_manager)

    @pyqtSlot(result = QObject)
    def getMaterialManagementModel(self) -> MaterialManagementModel:
        if not self._material_management_model:
            self._material_management_model = MaterialManagementModel(parent = self)
        return self._material_management_model

    @pyqtSlot(result = QObject)
    def getQualityManagementModel(self) -> QualityManagementModel:
        if not self._quality_management_model:
            self._quality_management_model = QualityManagementModel(parent = self)
        return self._quality_management_model

    def getSimpleModeSettingsManager(self, *args):
        if self._simple_mode_settings_manager is None:
            self._simple_mode_settings_manager = SimpleModeSettingsManager()
        return self._simple_mode_settings_manager

    def event(self, event):
        """Handle Qt events"""

        if event.type() == QEvent.FileOpen:
            if self._plugins_loaded:
                self._openFile(event.file())
            else:
                self._open_file_queue.append(event.file())

        return super().event(event)

    def getAutoSave(self) -> Optional[AutoSave]:
        return self._auto_save

    def getPrintInformation(self):
        """Get print information (duration / material used)"""

        return self._print_information

    def getQualityProfilesDropDownMenuModel(self, *args, **kwargs):
        if self._quality_profile_drop_down_menu_model is None:
            self._quality_profile_drop_down_menu_model = QualityProfilesDropDownMenuModel(self)
        return self._quality_profile_drop_down_menu_model

    def getCustomQualityProfilesDropDownMenuModel(self, *args, **kwargs):
        if self._custom_quality_profile_drop_down_menu_model is None:
            self._custom_quality_profile_drop_down_menu_model = CustomQualityProfilesDropDownMenuModel(self)
        return self._custom_quality_profile_drop_down_menu_model

    def getCuraAPI(self, *args, **kwargs) -> "CuraAPI":
        return self._cura_API

    def registerObjects(self, engine):
        """Registers objects for the QML engine to use.
        
        :param engine: The QML engine.
        """

        super().registerObjects(engine)

        # global contexts
        self.processEvents()
        engine.rootContext().setContextProperty("Printer", self)
        engine.rootContext().setContextProperty("CuraApplication", self)
        engine.rootContext().setContextProperty("PrintInformation", self._print_information)
        engine.rootContext().setContextProperty("CuraActions", self._cura_actions)
        engine.rootContext().setContextProperty("CuraSDKVersion", ApplicationMetadata.CuraSDKVersion)

        self.processEvents()
        qmlRegisterUncreatableType(CuraApplication, "Cura", 1, 0, "ResourceTypes", "Just an Enum type")

        self.processEvents()
        qmlRegisterSingletonType(CuraSceneController, "Cura", 1, 0, "SceneController", self.getCuraSceneController)
        qmlRegisterSingletonType(ExtruderManager, "Cura", 1, 0, "ExtruderManager", self.getExtruderManager)
        qmlRegisterSingletonType(MachineManager, "Cura", 1, 0, "MachineManager", self.getMachineManager)
        qmlRegisterSingletonType(IntentManager, "Cura", 1, 6, "IntentManager", self.getIntentManager)
        qmlRegisterSingletonType(SettingInheritanceManager, "Cura", 1, 0, "SettingInheritanceManager", self.getSettingInheritanceManager)
        qmlRegisterSingletonType(SimpleModeSettingsManager, "Cura", 1, 0, "SimpleModeSettingsManager", self.getSimpleModeSettingsManager)
        qmlRegisterSingletonType(MachineActionManager.MachineActionManager, "Cura", 1, 0, "MachineActionManager", self.getMachineActionManager)

        self.processEvents()
        qmlRegisterType(NetworkingUtil, "Cura", 1, 5, "NetworkingUtil")
        qmlRegisterType(WelcomePagesModel, "Cura", 1, 0, "WelcomePagesModel")
        qmlRegisterType(WhatsNewPagesModel, "Cura", 1, 0, "WhatsNewPagesModel")
        qmlRegisterType(AddPrinterPagesModel, "Cura", 1, 0, "AddPrinterPagesModel")
        qmlRegisterType(TextManager, "Cura", 1, 0, "TextManager")
        qmlRegisterType(RecommendedMode, "Cura", 1, 0, "RecommendedMode")

        self.processEvents()
        qmlRegisterType(NetworkMJPGImage, "Cura", 1, 0, "NetworkMJPGImage")
        qmlRegisterType(ObjectsModel, "Cura", 1, 0, "ObjectsModel")
        qmlRegisterType(BuildPlateModel, "Cura", 1, 0, "BuildPlateModel")
        qmlRegisterType(MultiBuildPlateModel, "Cura", 1, 0, "MultiBuildPlateModel")
        qmlRegisterType(InstanceContainer, "Cura", 1, 0, "InstanceContainer")
        qmlRegisterType(ExtrudersModel, "Cura", 1, 0, "ExtrudersModel")
        qmlRegisterType(GlobalStacksModel, "Cura", 1, 0, "GlobalStacksModel")

        self.processEvents()
        qmlRegisterType(FavoriteMaterialsModel, "Cura", 1, 0, "FavoriteMaterialsModel")
        qmlRegisterType(GenericMaterialsModel, "Cura", 1, 0, "GenericMaterialsModel")
        qmlRegisterType(MaterialBrandsModel, "Cura", 1, 0, "MaterialBrandsModel")
        qmlRegisterSingletonType(QualityManagementModel, "Cura", 1, 0, "QualityManagementModel", self.getQualityManagementModel)
        qmlRegisterSingletonType(MaterialManagementModel, "Cura", 1, 5, "MaterialManagementModel", self.getMaterialManagementModel)

        self.processEvents()
        qmlRegisterType(DiscoveredPrintersModel, "Cura", 1, 0, "DiscoveredPrintersModel")
        qmlRegisterType(DiscoveredCloudPrintersModel, "Cura", 1, 7, "DiscoveredCloudPrintersModel")
        qmlRegisterSingletonType(QualityProfilesDropDownMenuModel, "Cura", 1, 0,
                                 "QualityProfilesDropDownMenuModel", self.getQualityProfilesDropDownMenuModel)
        qmlRegisterSingletonType(CustomQualityProfilesDropDownMenuModel, "Cura", 1, 0,
                                 "CustomQualityProfilesDropDownMenuModel", self.getCustomQualityProfilesDropDownMenuModel)
        qmlRegisterType(NozzleModel, "Cura", 1, 0, "NozzleModel")
        qmlRegisterType(IntentModel, "Cura", 1, 6, "IntentModel")
        qmlRegisterType(IntentCategoryModel, "Cura", 1, 6, "IntentCategoryModel")

        self.processEvents()
        qmlRegisterType(MaterialSettingsVisibilityHandler, "Cura", 1, 0, "MaterialSettingsVisibilityHandler")
        qmlRegisterType(SettingVisibilityPresetsModel, "Cura", 1, 0, "SettingVisibilityPresetsModel")
        qmlRegisterType(QualitySettingsModel, "Cura", 1, 0, "QualitySettingsModel")
        qmlRegisterType(FirstStartMachineActionsModel, "Cura", 1, 0, "FirstStartMachineActionsModel")
        qmlRegisterType(MachineNameValidator, "Cura", 1, 0, "MachineNameValidator")
        qmlRegisterType(UserChangesModel, "Cura", 1, 0, "UserChangesModel")
        qmlRegisterSingletonType(ContainerManager, "Cura", 1, 0, "ContainerManager", ContainerManager.getInstance)
        qmlRegisterType(SidebarCustomMenuItemsModel, "Cura", 1, 0, "SidebarCustomMenuItemsModel")

        qmlRegisterType(PrinterOutputDevice, "Cura", 1, 0, "PrinterOutputDevice")

        from cura.API import CuraAPI
        qmlRegisterSingletonType(CuraAPI, "Cura", 1, 1, "API", self.getCuraAPI)

        # As of Qt5.7, it is necessary to get rid of any ".." in the path for the singleton to work.
        actions_url = QUrl.fromLocalFile(os.path.abspath(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles, "Actions.qml")))
        qmlRegisterSingletonType(actions_url, "Cura", 1, 0, "Actions")

        for path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.QmlFiles):
            type_name = os.path.splitext(os.path.basename(path))[0]
            if type_name in ("Cura", "Actions"):
                continue

            # Ignore anything that is not a QML file.
            if not path.endswith(".qml"):
                continue

            qmlRegisterType(QUrl.fromLocalFile(path), "Cura", 1, 0, type_name)
            self.processEvents()

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

            if self.getPreferences().getValue("view/center_on_select"):
                self._center_after_select = True
        else:
            if self.getController().getActiveTool():
                self._previous_active_tool = self.getController().getActiveTool().getPluginId()
                self.getController().setActiveTool(None)

    def _onToolOperationStopped(self, event):
        if self._center_after_select and Selection.getSelectedObject(0) is not None:
            self._center_after_select = False
            self._camera_animation.setStart(self.getController().getTool("CameraTool").getOrigin())
            self._camera_animation.setTarget(Selection.getSelectedObject(0).getWorldPosition())
            self._camera_animation.start()

    activityChanged = pyqtSignal()
    sceneBoundingBoxChanged = pyqtSignal()

    @pyqtProperty(bool, notify = activityChanged)
    def platformActivity(self):
        return self._platform_activity

    @pyqtProperty(str, notify = sceneBoundingBoxChanged)
    def getSceneBoundingBoxString(self):
        return self._i18n_catalog.i18nc("@info 'width', 'depth' and 'height' are variable names that must NOT be translated; just translate the format of ##x##x## mm.", "%(width).1f x %(depth).1f x %(height).1f mm") % {'width' : self._scene_bounding_box.width.item(), 'depth': self._scene_bounding_box.depth.item(), 'height' : self._scene_bounding_box.height.item()}

    def updatePlatformActivityDelayed(self, node = None):
        if node is not None and (node.getMeshData() is not None or node.callDecoration("getLayerData")):
            self._update_platform_activity_timer.start()

    def updatePlatformActivity(self, node = None):
        """Update scene bounding box for current build plate"""

        count = 0
        scene_bounding_box = None
        is_block_slicing_node = False
        active_build_plate = self.getMultiBuildPlateModel().activeBuildPlate

        print_information = self.getPrintInformation()
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if (
                not issubclass(type(node), CuraSceneNode) or
                (not node.getMeshData() and not node.callDecoration("getLayerData")) or
                (node.callDecoration("getBuildPlateNumber") != active_build_plate)):

                continue
            if node.callDecoration("isBlockSlicing"):
                is_block_slicing_node = True

            count += 1

            # After clicking the Undo button, if the build plate empty the project name needs to be set
            if print_information.baseName == '':
                print_information.setBaseName(node.getName())

            if not scene_bounding_box:
                scene_bounding_box = node.getBoundingBox()
            else:
                other_bb = node.getBoundingBox()
                if other_bb is not None:
                    scene_bounding_box = scene_bounding_box + node.getBoundingBox()


        if print_information:
            print_information.setPreSliced(is_block_slicing_node)

        if not scene_bounding_box:
            scene_bounding_box = AxisAlignedBox.Null

        if repr(self._scene_bounding_box) != repr(scene_bounding_box):
            self._scene_bounding_box = scene_bounding_box
            self.sceneBoundingBoxChanged.emit()

        self._platform_activity = True if count > 0 else False
        self.activityChanged.emit()

    @pyqtSlot()
    def selectAll(self):
        """Select all nodes containing mesh data in the scene."""

        if not self.getController().getToolsEnabled():
            return

        Selection.clear()
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup") or node.getParent().callDecoration("isSliceable"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            if not node.isSelectable():
                continue  # i.e. node with layer data
            if not node.callDecoration("isSliceable") and not node.callDecoration("isGroup"):
                continue  # i.e. node with layer data

            Selection.add(node)

    @pyqtSlot()
    def resetAllTranslation(self):
        """Reset all translation on nodes with mesh data."""

        Logger.log("i", "Resetting all scene translations")
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
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

    @pyqtSlot()
    def resetAll(self):
        """Reset all transformations on nodes with mesh data."""

        Logger.log("i", "Resetting all scene transformations")
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            if not node.callDecoration("isSliceable") and not node.callDecoration("isGroup"):
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

    @pyqtSlot()
    def arrangeObjectsToAllBuildPlates(self) -> None:
        """Arrange all objects."""

        nodes_to_arrange = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
                continue

            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.

            parent_node = node.getParent()
            if parent_node and parent_node.callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is reset)

            if not node.callDecoration("isSliceable") and not node.callDecoration("isGroup"):
                continue  # i.e. node with layer data

            bounding_box = node.getBoundingBox()
            # Skip nodes that are too big
            if bounding_box is None or bounding_box.width < self._volume.getBoundingBox().width or bounding_box.depth < self._volume.getBoundingBox().depth:
                nodes_to_arrange.append(node)
        job = ArrangeObjectsAllBuildPlatesJob(nodes_to_arrange)
        job.start()
        self.getCuraSceneController().setActiveBuildPlate(0)  # Select first build plate

    # Single build plate
    @pyqtSlot()
    def arrangeAll(self) -> None:
        nodes_to_arrange = []
        active_build_plate = self.getMultiBuildPlateModel().activeBuildPlate
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
                continue

            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.

            parent_node = node.getParent()
            if parent_node and parent_node.callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)

            if not node.isSelectable():
                continue  # i.e. node with layer data

            if not node.callDecoration("isSliceable") and not node.callDecoration("isGroup"):
                continue  # i.e. node with layer data

            if node.callDecoration("getBuildPlateNumber") == active_build_plate:
                # Skip nodes that are too big
                bounding_box = node.getBoundingBox()
                if bounding_box is None or bounding_box.width < self._volume.getBoundingBox().width or bounding_box.depth < self._volume.getBoundingBox().depth:
                    nodes_to_arrange.append(node)
        self.arrange(nodes_to_arrange, fixed_nodes = [])

    def arrange(self, nodes: List[SceneNode], fixed_nodes: List[SceneNode]) -> None:
        """Arrange a set of nodes given a set of fixed nodes
        
        :param nodes: nodes that we have to place
        :param fixed_nodes: nodes that are placed in the arranger before finding spots for nodes
        """

        min_offset = self.getBuildVolume().getEdgeDisallowedSize() + 2  # Allow for some rounding errors
        job = ArrangeObjectsJob(nodes, fixed_nodes, min_offset = max(min_offset, 8))
        job.start()

    @pyqtSlot()
    def reloadAll(self) -> None:
        """Reload all mesh data on the screen from file."""

        Logger.log("i", "Reloading all loaded mesh data.")
        nodes = []
        has_merged_nodes = False
        gcode_filename = None  # type: Optional[str]
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            # Objects loaded from Gcode should also be included.
            gcode_filename = node.callDecoration("getGcodeFileName")
            if gcode_filename is not None:
                break

            if not isinstance(node, CuraSceneNode) or not node.getMeshData():
                if node.getName() == "MergedMesh":
                    has_merged_nodes = True
                continue

            nodes.append(node)

        # We can open only one gcode file at the same time. If the current view has a gcode file open, just reopen it
        # for reloading.
        if gcode_filename:
            self._openFile(gcode_filename)

        if not nodes:
            return

        objects_in_filename = {}  # type: Dict[str, List[CuraSceneNode]]
        for node in nodes:
            mesh_data = node.getMeshData()
            if mesh_data:
                file_name = mesh_data.getFileName()
                if file_name:
                    if file_name not in objects_in_filename:
                        objects_in_filename[file_name] = []
                    if file_name in objects_in_filename:
                        objects_in_filename[file_name].append(node)
                else:
                    Logger.log("w", "Unable to reload data because we don't have a filename.")

        for file_name, nodes in objects_in_filename.items():
            for node in nodes:
                job = ReadMeshJob(file_name)
                job._node = node  # type: ignore
                job.finished.connect(self._reloadMeshFinished)
                if has_merged_nodes:
                    job.finished.connect(self.updateOriginOfMergedMeshes)

                job.start()

    @pyqtSlot("QStringList")
    def setExpandedCategories(self, categories: List[str]) -> None:
        categories = list(set(categories))
        categories.sort()
        joined = ";".join(categories)
        if joined != self.getPreferences().getValue("cura/categories_expanded"):
            self.getPreferences().setValue("cura/categories_expanded", joined)
            self.expandedCategoriesChanged.emit()

    expandedCategoriesChanged = pyqtSignal()

    @pyqtProperty("QStringList", notify = expandedCategoriesChanged)
    def expandedCategories(self) -> List[str]:
        return self.getPreferences().getValue("cura/categories_expanded").split(";")

    @pyqtSlot()
    def mergeSelected(self):
        self.groupSelected()
        try:
            group_node = Selection.getAllSelectedObjects()[0]
        except Exception as e:
            Logger.log("e", "mergeSelected: Exception: %s", e)
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
            if center is not None:
                object_centers.append(center)

        if object_centers:
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
        group_node.setName("MergedMesh")  # add a specific name to distinguish this node


    def updateOriginOfMergedMeshes(self, _):
        """Updates origin position of all merged meshes"""

        group_nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if isinstance(node, CuraSceneNode) and node.getName() == "MergedMesh":

                # Checking by name might be not enough, the merged mesh should has "GroupDecorator" decorator
                for decorator in node.getDecorators():
                    if isinstance(decorator, GroupDecorator):
                        group_nodes.append(node)
                        break

        for group_node in group_nodes:
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
                if center is not None:
                    object_centers.append(center)

            if object_centers:
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
    def groupSelected(self) -> None:
        # Create a group-node
        group_node = CuraSceneNode()
        group_decorator = GroupDecorator()
        group_node.addDecorator(group_decorator)
        group_node.addDecorator(ConvexHullDecorator())
        group_node.addDecorator(BuildPlateDecorator(self.getMultiBuildPlateModel().activeBuildPlate))
        group_node.setParent(self.getController().getScene().getRoot())
        group_node.setSelectable(True)
        center = Selection.getSelectionCenter()
        group_node.setPosition(center)
        group_node.setCenterPosition(center)

        # Remove nodes that are directly parented to another selected node from the selection so they remain parented
        selected_nodes = Selection.getAllSelectedObjects().copy()
        for node in selected_nodes:
            parent = node.getParent()
            if parent is not None and parent in selected_nodes and not parent.callDecoration("isGroup"):
                Selection.remove(node)

        # Move selected nodes into the group-node
        Selection.applyOperation(SetParentOperation, group_node)

        # Deselect individual nodes and select the group-node instead
        for node in group_node.getChildren():
            Selection.remove(node)
        Selection.add(group_node)

    @pyqtSlot()
    def ungroupSelected(self) -> None:
        selected_objects = Selection.getAllSelectedObjects().copy()
        for node in selected_objects:
            if node.callDecoration("isGroup"):
                op = GroupedOperation()

                group_parent = node.getParent()
                children = node.getChildren().copy()
                for child in children:
                    # Ungroup only 1 level deep
                    if child.getParent() != node:
                        continue

                    # Set the parent of the children to the parent of the group-node
                    op.addOperation(SetParentOperation(child, group_parent))

                    # Add all individual nodes to the selection
                    Selection.add(child)

                op.push()
                # Note: The group removes itself from the scene once all its children have left it,
                # see GroupDecorator._onChildrenChanged

    def _createSplashScreen(self) -> Optional[CuraSplashScreen.CuraSplashScreen]:
        if self._is_headless:
            return None
        return CuraSplashScreen.CuraSplashScreen()

    def _onActiveMachineChanged(self):
        pass

    fileLoaded = pyqtSignal(str)
    fileCompleted = pyqtSignal(str)

    def _reloadMeshFinished(self, job) -> None:
        """
        Function called whenever a ReadMeshJob finishes in the background. It reloads a specific node object in the
        scene from its source file. The function gets all the nodes that exist in the file through the job result, and
        then finds the scene node that it wants to refresh by its object id. Each job refreshes only one node.

        :param job: The :py:class:`Uranium.UM.ReadMeshJob.ReadMeshJob` running in the background that reads all the
        meshes in a file
        """

        job_result = job.getResult()  # nodes that exist inside the file read by this job
        if len(job_result) == 0:
            Logger.log("e", "Reloading the mesh failed.")
            return
        object_found = False
        mesh_data = None
        # Find the node to be refreshed based on its id
        for job_result_node in job_result:
            if job_result_node.getId() == job._node.getId():
                mesh_data = job_result_node.getMeshData()
                object_found = True
                break
        if not object_found:
            Logger.warning("The object with id {} no longer exists! Keeping the old version in the scene.".format(job_result_node.getId()))
            return
        if not mesh_data:
            Logger.log("w", "Could not find a mesh in reloaded node.")
            return
        job._node.setMeshData(mesh_data)

    def _openFile(self, filename):
        self.readLocalFile(QUrl.fromLocalFile(filename))

    def _addProfileReader(self, profile_reader):
        # TODO: Add the profile reader to the list of plug-ins that can be used when importing profiles.
        pass

    def _addProfileWriter(self, profile_writer):
        pass

    @pyqtSlot("QSize")
    def setMinimumWindowSize(self, size):
        main_window = self.getMainWindow()
        if main_window:
            main_window.setMinimumSize(size)

    def getBuildVolume(self):
        return self._volume

    additionalComponentsChanged = pyqtSignal(str, arguments = ["areaId"])

    @pyqtProperty("QVariantMap", notify = additionalComponentsChanged)
    def additionalComponents(self):
        return self._additional_components

    @pyqtSlot(str, "QVariant")
    def addAdditionalComponent(self, area_id: str, component):
        """Add a component to a list of components to be reparented to another area in the GUI.
        
        The actual reparenting is done by the area itself.
        :param area_id: dentifying name of the area to which the component should be reparented
        :param (QQuickComponent) component: The component that should be reparented
        """

        if area_id not in self._additional_components:
            self._additional_components[area_id] = []
        self._additional_components[area_id].append(component)

        self.additionalComponentsChanged.emit(area_id)

    @pyqtSlot(str)
    def log(self, msg):
        Logger.log("d", msg)

    openProjectFile = pyqtSignal(QUrl, arguments = ["project_file"])  # Emitted when a project file is about to open.

    @pyqtSlot(QUrl, str)
    @pyqtSlot(QUrl)
    def readLocalFile(self, file: QUrl, project_mode: Optional[str] = None):
        """Open a local file
        
        :param project_mode: How to handle project files. Either None(default): Follow user preference, "open_as_model"
         or "open_as_project". This parameter is only considered if the file is a project file.
        """

        if not file.isValid():
            return

        scene = self.getController().getScene()

        for node in DepthFirstIterator(scene.getRoot()):
            if node.callDecoration("isBlockSlicing"):
                self.deleteAll()
                break

        is_project_file = self.checkIsValidProjectFile(file)

        if project_mode is None:
            project_mode = self.getPreferences().getValue("cura/choice_on_open_project")

        if is_project_file and project_mode == "open_as_project":
            # open as project immediately without presenting a dialog
            workspace_handler = self.getWorkspaceFileHandler()
            workspace_handler.readLocalFile(file)
            return

        if is_project_file and project_mode == "always_ask":
            # present a dialog asking to open as project or import models
            self.callLater(self.openProjectFile.emit, file)
            return

        # Either the file is a model file or we want to load only models from project. Continue to load models.

        if self.getPreferences().getValue("cura/select_models_on_load"):
            Selection.clear()

        f = file.toLocalFile()
        extension = os.path.splitext(f)[1]
        extension = extension.lower()
        filename = os.path.basename(f)
        if self._currently_loading_files:
            # If a non-slicable file is already being loaded, we prevent loading of any further non-slicable files
            if extension in self._non_sliceable_extensions:
                message = Message(
                    self._i18n_catalog.i18nc("@info:status",
                                       "Only one G-code file can be loaded at a time. Skipped importing {0}",
                                       filename), title = self._i18n_catalog.i18nc("@info:title", "Warning"))
                message.show()
                return
            # If file being loaded is non-slicable file, then prevent loading of any other files
            extension = os.path.splitext(self._currently_loading_files[0])[1]
            extension = extension.lower()
            if extension in self._non_sliceable_extensions:
                message = Message(
                    self._i18n_catalog.i18nc("@info:status",
                                       "Can't open any other file if G-code is loading. Skipped importing {0}",
                                       filename), title = self._i18n_catalog.i18nc("@info:title", "Error"))
                message.show()
                return

        self._currently_loading_files.append(f)
        if extension in self._non_sliceable_extensions:
            self.deleteAll(only_selectable = False)

        job = ReadMeshJob(f)
        job.finished.connect(self._readMeshFinished)
        job.start()

    def _readMeshFinished(self, job):
        global_container_stack = self.getGlobalContainerStack()
        if not global_container_stack:
            Logger.log("w", "Can't load meshes before a printer is added.")
            return

        nodes = job.getResult()
        file_name = job.getFileName()
        file_name_lower = file_name.lower()
        file_extension = file_name_lower.split(".")[-1]
        self._currently_loading_files.remove(file_name)

        self.fileLoaded.emit(file_name)
        target_build_plate = self.getMultiBuildPlateModel().activeBuildPlate

        root = self.getController().getScene().getRoot()
        fixed_nodes = []
        for node_ in DepthFirstIterator(root):
            if node_.callDecoration("isSliceable") and node_.callDecoration("getBuildPlateNumber") == target_build_plate:
                fixed_nodes.append(node_)
        machine_width = global_container_stack.getProperty("machine_width", "value")
        machine_depth = global_container_stack.getProperty("machine_depth", "value")
        arranger = Arrange.create(x = machine_width, y = machine_depth, fixed_nodes = fixed_nodes)
        min_offset = 8
        default_extruder_position = self.getMachineManager().defaultExtruderPosition
        default_extruder_id = self._global_container_stack.extruderList[int(default_extruder_position)].getId()

        select_models_on_load = self.getPreferences().getValue("cura/select_models_on_load")

        for original_node in nodes:

            # Create a CuraSceneNode just if the original node is not that type
            if isinstance(original_node, CuraSceneNode):
                node = original_node
            else:
                node = CuraSceneNode()
                node.setMeshData(original_node.getMeshData())

                #Setting meshdata does not apply scaling.
                if(original_node.getScale() != Vector(1.0, 1.0, 1.0)):
                    node.scale(original_node.getScale())

            node.setSelectable(True)
            node.setName(os.path.basename(file_name))
            self.getBuildVolume().checkBoundsAndUpdate(node)

            is_non_sliceable = "." + file_extension in self._non_sliceable_extensions

            if is_non_sliceable:
                # Need to switch first to the preview stage and then to layer view
                self.callLater(lambda: (self.getController().setActiveStage("PreviewStage"),
                                        self.getController().setActiveView("SimulationView")))

                block_slicing_decorator = BlockSlicingDecorator()
                node.addDecorator(block_slicing_decorator)
            else:
                sliceable_decorator = SliceableObjectDecorator()
                node.addDecorator(sliceable_decorator)

            scene = self.getController().getScene()

            # If there is no convex hull for the node, start calculating it and continue.
            if not node.getDecorator(ConvexHullDecorator):
                node.addDecorator(ConvexHullDecorator())
            for child in node.getAllChildren():
                if not child.getDecorator(ConvexHullDecorator):
                    child.addDecorator(ConvexHullDecorator())

            if file_extension != "3mf":
                if node.callDecoration("isSliceable"):
                    # Only check position if it's not already blatantly obvious that it won't fit.
                    if node.getBoundingBox() is None or self._volume.getBoundingBox() is None or node.getBoundingBox().width < self._volume.getBoundingBox().width or node.getBoundingBox().depth < self._volume.getBoundingBox().depth:
                        # Find node location
                        offset_shape_arr, hull_shape_arr = ShapeArray.fromNode(node, min_offset = min_offset)

                        # If a model is to small then it will not contain any points
                        if offset_shape_arr is None and hull_shape_arr is None:
                            Message(self._i18n_catalog.i18nc("@info:status", "The selected model was too small to load."),
                                    title = self._i18n_catalog.i18nc("@info:title", "Warning")).show()
                            return

                        # Step is for skipping tests to make it a lot faster. it also makes the outcome somewhat rougher
                        arranger.findNodePlacement(node, offset_shape_arr, hull_shape_arr, step = 10)

            # This node is deep copied from some other node which already has a BuildPlateDecorator, but the deepcopy
            # of BuildPlateDecorator produces one that's associated with build plate -1. So, here we need to check if
            # the BuildPlateDecorator exists or not and always set the correct build plate number.
            build_plate_decorator = node.getDecorator(BuildPlateDecorator)
            if build_plate_decorator is None:
                build_plate_decorator = BuildPlateDecorator(target_build_plate)
                node.addDecorator(build_plate_decorator)
            build_plate_decorator.setBuildPlateNumber(target_build_plate)

            operation = AddSceneNodeOperation(node, scene.getRoot())
            operation.push()

            node.callDecoration("setActiveExtruder", default_extruder_id)
            scene.sceneChanged.emit(node)

            if select_models_on_load:
                Selection.add(node)

        self.fileCompleted.emit(file_name)

    def addNonSliceableExtension(self, extension):
        self._non_sliceable_extensions.append(extension)

    @pyqtSlot(str, result=bool)
    def checkIsValidProjectFile(self, file_url):
        """Checks if the given file URL is a valid project file. """

        file_path = QUrl(file_url).toLocalFile()
        workspace_reader = self.getWorkspaceFileHandler().getReaderForFile(file_path)
        if workspace_reader is None:
            return False  # non-project files won't get a reader
        try:
            result = workspace_reader.preRead(file_path, show_dialog=False)
            return result == WorkspaceReader.PreReadResult.accepted
        except Exception:
            Logger.logException("e", "Could not check file %s", file_url)
            return False

    def _onContextMenuRequested(self, x: float, y: float) -> None:
        # Ensure we select the object if we request a context menu over an object without having a selection.
        if Selection.hasSelection():
            return
        selection_pass = cast(SelectionPass, self.getRenderer().getRenderPass("selection"))
        if not selection_pass:  # If you right-click before the rendering has been initialised there might not be a selection pass yet.
            print("--------------ding! Got the crash.")
            return
        node = self.getController().getScene().findObject(selection_pass.getIdAtPosition(x, y))
        if not node:
            return
        parent = node.getParent()
        while parent and parent.callDecoration("isGroup"):
            node = parent
            parent = node.getParent()

        Selection.add(node)

    @pyqtSlot()
    def showMoreInformationDialogForAnonymousDataCollection(self):
        try:
            slice_info = self._plugin_registry.getPluginObject("SliceInfoPlugin")
            slice_info.showMoreInfoDialog()
        except PluginNotFoundError:
            Logger.log("w", "Plugin SliceInfo was not found, so not able to show the info dialog.")

    def addSidebarCustomMenuItem(self, menu_item: dict) -> None:
        self._sidebar_custom_menu_items.append(menu_item)

    def getSidebarCustomMenuItems(self) -> list:
        return self._sidebar_custom_menu_items

    @pyqtSlot(result = bool)
    def shouldShowWelcomeDialog(self) -> bool:
        # Only show the complete flow if there is no printer yet.
        return self._machine_manager.activeMachine is None

    @pyqtSlot(result = bool)
    def shouldShowWhatsNewDialog(self) -> bool:
        has_active_machine = self._machine_manager.activeMachine is not None
        has_app_just_upgraded = self.hasJustUpdatedFromOldVersion()

        # Only show the what's new dialog if there's no machine and we have just upgraded
        show_whatsnew_only = has_active_machine and has_app_just_upgraded
        return show_whatsnew_only

    @pyqtSlot(result = int)
    def appWidth(self) -> int:
        main_window = QtApplication.getInstance().getMainWindow()
        if main_window:
            return main_window.width()
        return 0

    @pyqtSlot(result = int)
    def appHeight(self) -> int:
        main_window = QtApplication.getInstance().getMainWindow()
        if main_window:
            return main_window.height()
        return 0

    @pyqtSlot()
    def deleteAll(self, only_selectable: bool = True) -> None:
        super().deleteAll(only_selectable = only_selectable)

        # Also remove nodes with LayerData
        self._removeNodesWithLayerData(only_selectable = only_selectable)

    def _removeNodesWithLayerData(self, only_selectable: bool = True) -> None:
        Logger.log("i", "Clearing scene")
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
                continue
            if not node.isEnabled():
                continue
            if (not node.getMeshData() and not node.callDecoration("getLayerData")) and not node.callDecoration("isGroup"):
                continue  # Node that doesnt have a mesh and is not a group.
            if only_selectable and not node.isSelectable():
                continue  # Only remove nodes that are selectable.
            if not node.callDecoration("isSliceable") and not node.callDecoration("getLayerData") and not node.callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)
        if nodes:
            from UM.Operations.GroupedOperation import GroupedOperation
            op = GroupedOperation()

            for node in nodes:
                from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
                op.addOperation(RemoveSceneNodeOperation(node))

                # Reset the print information
                self.getController().getScene().sceneChanged.emit(node)

            op.push()
            from UM.Scene.Selection import Selection
            Selection.clear()

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "CuraApplication":
        return cast(CuraApplication, super().getInstance(**kwargs))
