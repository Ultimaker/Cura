# Copyright (c) 2018 Jaime van Kessel, Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

import configparser  # The script lists are stored in metadata as serialised config files.
import importlib.util
import io  # To allow configparser to write to a string.
import os.path
import pkgutil
import sys
from typing import Dict, Type, TYPE_CHECKING, List, Optional, cast

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Trust import Trust
from UM.i18n import i18nCatalog
from cura import ApplicationMetadata
from cura.CuraApplication import CuraApplication

i18n_catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from .Script import Script


##  The post processing plugin is an Extension type plugin that enables pre-written scripts to post process generated
#   g-code files.
class PostProcessingPlugin(QObject, Extension):
    def __init__(self, parent = None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self.setMenuName(i18n_catalog.i18nc("@item:inmenu", "Post Processing"))
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Modify G-Code"), self.showPopup)
        self._view = None

        # Loaded scripts are all scripts that can be used
        self._loaded_scripts = {}  # type: Dict[str, Type[Script]]
        self._script_labels = {}  # type: Dict[str, str]

        # Script list contains instances of scripts in loaded_scripts.
        # There can be duplicates, which will be executed in sequence.
        self._script_list = []  # type: List[Script]
        self._selected_script_index = -1
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        if self._global_container_stack:
            self._global_container_stack.metaDataChanged.connect(self._restoreScriptInforFromMetadata)

        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.execute)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)  # When the current printer changes, update the list of scripts.
        CuraApplication.getInstance().mainWindowChanged.connect(self._createView)  # When the main window is created, create the view so that we can display the post-processing icon if necessary.

    selectedIndexChanged = pyqtSignal()

    @pyqtProperty(str, notify = selectedIndexChanged)
    def selectedScriptDefinitionId(self) -> Optional[str]:
        try:
            return self._script_list[self._selected_script_index].getDefinitionId()
        except IndexError:
            return ""

    @pyqtProperty(str, notify=selectedIndexChanged)
    def selectedScriptStackId(self) -> Optional[str]:
        try:
            return self._script_list[self._selected_script_index].getStackId()
        except IndexError:
            return ""

    ##  Execute all post-processing scripts on the gcode.
    def execute(self, output_device) -> None:
        scene = Application.getInstance().getController().getScene()
        # If the scene does not have a gcode, do nothing
        if not hasattr(scene, "gcode_dict"):
            return
        gcode_dict = getattr(scene, "gcode_dict")
        if not gcode_dict:
            return

        # get gcode list for the active build plate
        active_build_plate_id = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        gcode_list = gcode_dict[active_build_plate_id]
        if not gcode_list:
            return

        if ";POSTPROCESSED" not in gcode_list[0]:
            for script in self._script_list:
                try:
                    gcode_list = script.execute(gcode_list)
                except Exception:
                    Logger.logException("e", "Exception in post-processing script.")
            if len(self._script_list):  # Add comment to g-code if any changes were made.
                gcode_list[0] += ";POSTPROCESSED\n"
            gcode_dict[active_build_plate_id] = gcode_list
            setattr(scene, "gcode_dict", gcode_dict)
        else:
            Logger.log("e", "Already post processed")

    @pyqtSlot(int)
    def setSelectedScriptIndex(self, index: int) -> None:
        if self._selected_script_index != index:
            self._selected_script_index = index
            self.selectedIndexChanged.emit()

    @pyqtProperty(int, notify = selectedIndexChanged)
    def selectedScriptIndex(self) -> int:
        return self._selected_script_index

    @pyqtSlot(int, int)
    def moveScript(self, index: int, new_index: int) -> None:
        if new_index < 0 or new_index > len(self._script_list) - 1:
            return  # nothing needs to be done
        else:
            # Magical switch code.
            self._script_list[new_index], self._script_list[index] = self._script_list[index], self._script_list[new_index]
            self.scriptListChanged.emit()
            self.selectedIndexChanged.emit() #Ensure that settings are updated
            self._propertyChanged()

    ##  Remove a script from the active script list by index.
    @pyqtSlot(int)
    def removeScriptByIndex(self, index: int) -> None:
        self._script_list.pop(index)
        if len(self._script_list) - 1 < self._selected_script_index:
            self._selected_script_index = len(self._script_list) - 1
        self.scriptListChanged.emit()
        self.selectedIndexChanged.emit()  # Ensure that settings are updated
        self._propertyChanged()

    ##  Load all scripts from all paths where scripts can be found.
    #
    #   This should probably only be done on init.
    def loadAllScripts(self) -> None:
        if self._loaded_scripts: # Already loaded.
            return

        # The PostProcessingPlugin path is for built-in scripts.
        # The Resources path is where the user should store custom scripts.
        # The Preferences path is legacy, where the user may previously have stored scripts.
        for root in [PluginRegistry.getInstance().getPluginPath("PostProcessingPlugin"), Resources.getStoragePath(Resources.Resources), Resources.getStoragePath(Resources.Preferences)]:
            if root is None:
                continue
            path = os.path.join(root, "scripts")
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except OSError:
                    Logger.log("w", "Unable to create a folder for scripts: " + path)
                    continue

            self.loadScripts(path)

    ##  Load all scripts from provided path.
    #   This should probably only be done on init.
    #   \param path Path to check for scripts.
    def loadScripts(self, path: str) -> None:
        ## Load all scripts in the scripts folders
        scripts = pkgutil.iter_modules(path = [path])
        for loader, script_name, ispkg in scripts:
            # Iterate over all scripts.
            if script_name not in sys.modules:
                try:
                    file_path = os.path.join(path, script_name + ".py")
                    if not self._isScriptAllowed(file_path):
                        Logger.warning("Skipped loading post-processing script {}: not trusted".format(file_path))
                        continue

                    spec = importlib.util.spec_from_file_location(__name__ + "." + script_name,
                                                                  file_path)
                    loaded_script = importlib.util.module_from_spec(spec)
                    if spec.loader is None:
                        continue
                    spec.loader.exec_module(loaded_script)  # type: ignore
                    sys.modules[script_name] = loaded_script #TODO: This could be a security risk. Overwrite any module with a user-provided name?

                    loaded_class = getattr(loaded_script, script_name)
                    temp_object = loaded_class()
                    Logger.log("d", "Begin loading of script: %s", script_name)
                    try:
                        setting_data = temp_object.getSettingData()
                        if "name" in setting_data and "key" in setting_data:
                            self._script_labels[setting_data["key"]] = setting_data["name"]
                            self._loaded_scripts[setting_data["key"]] = loaded_class
                        else:
                            Logger.log("w", "Script %s.py has no name or key", script_name)
                            self._script_labels[script_name] = script_name
                            self._loaded_scripts[script_name] = loaded_class
                    except AttributeError:
                        Logger.log("e", "Script %s.py is not a recognised script type. Ensure it inherits Script", script_name)
                    except NotImplementedError:
                        Logger.log("e", "Script %s.py has no implemented settings", script_name)
                except Exception as e:
                    Logger.logException("e", "Exception occurred while loading post processing plugin: {error_msg}".format(error_msg = str(e)))

    loadedScriptListChanged = pyqtSignal()
    @pyqtProperty("QVariantList", notify = loadedScriptListChanged)
    def loadedScriptList(self) -> List[str]:
        return sorted(list(self._loaded_scripts.keys()))

    @pyqtSlot(str, result = str)
    def getScriptLabelByKey(self, key: str) -> Optional[str]:
        return self._script_labels.get(key)

    scriptListChanged = pyqtSignal()
    @pyqtProperty("QStringList", notify = scriptListChanged)
    def scriptList(self) -> List[str]:
        script_list = [script.getSettingData()["key"] for script in self._script_list]
        return script_list

    @pyqtSlot(str)
    def addScriptToList(self, key: str) -> None:
        Logger.log("d", "Adding script %s to list.", key)
        new_script = self._loaded_scripts[key]()
        new_script.initialize()
        self._script_list.append(new_script)
        self.setSelectedScriptIndex(len(self._script_list) - 1)
        self.scriptListChanged.emit()
        self._propertyChanged()

    def _restoreScriptInforFromMetadata(self):
        self.loadAllScripts()
        new_stack = self._global_container_stack
        if new_stack is None:
            return
        self._script_list.clear()
        if not new_stack.getMetaDataEntry("post_processing_scripts"):  # Missing or empty.
            self.scriptListChanged.emit()  # Even emit this if it didn't change. We want it to write the empty list to the stack's metadata.
            self.setSelectedScriptIndex(-1)
            return

        self._script_list.clear()
        scripts_list_strs = new_stack.getMetaDataEntry("post_processing_scripts")
        for script_str in scripts_list_strs.split(
                "\n"):  # Encoded config files should never contain three newlines in a row. At most 2, just before section headers.
            if not script_str:  # There were no scripts in this one (or a corrupt file caused more than 3 consecutive newlines here).
                continue
            script_str = script_str.replace(r"\\\n", "\n").replace(r"\\\\", "\\\\")  # Unescape escape sequences.
            script_parser = configparser.ConfigParser(interpolation=None)
            script_parser.optionxform = str  # type: ignore  # Don't transform the setting keys as they are case-sensitive.
            script_parser.read_string(script_str)
            for script_name, settings in script_parser.items():  # There should only be one, really! Otherwise we can't guarantee the order or allow multiple uses of the same script.
                if script_name == "DEFAULT":  # ConfigParser always has a DEFAULT section, but we don't fill it. Ignore this one.
                    continue
                if script_name not in self._loaded_scripts:  # Don't know this post-processing plug-in.
                    Logger.log("e",
                               "Unknown post-processing script {script_name} was encountered in this global stack.".format(
                                   script_name=script_name))
                    continue
                new_script = self._loaded_scripts[script_name]()
                new_script.initialize()
                for setting_key, setting_value in settings.items():  # Put all setting values into the script.
                    if new_script._instance is not None:
                        new_script._instance.setProperty(setting_key, "value", setting_value)
                self._script_list.append(new_script)

        self.setSelectedScriptIndex(0)
        # Ensure that we always force an update (otherwise the fields don't update correctly!)
        self.selectedIndexChanged.emit()
        self.scriptListChanged.emit()
        self._propertyChanged()

    ##  When the global container stack is changed, swap out the list of active
    #   scripts.
    def _onGlobalContainerStackChanged(self) -> None:
        if self._global_container_stack:
            self._global_container_stack.metaDataChanged.disconnect(self._restoreScriptInforFromMetadata)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.metaDataChanged.connect(self._restoreScriptInforFromMetadata)
        self._restoreScriptInforFromMetadata()

    @pyqtSlot()
    def writeScriptsToStack(self) -> None:
        script_list_strs = []  # type: List[str]
        for script in self._script_list:
            parser = configparser.ConfigParser(interpolation = None)  # We'll encode the script as a config with one section. The section header is the key and its values are the settings.
            parser.optionxform = str  # type: ignore # Don't transform the setting keys as they are case-sensitive.
            script_name = script.getSettingData()["key"]
            parser.add_section(script_name)
            for key in script.getSettingData()["settings"]:
                value = script.getSettingValueByKey(key)
                parser[script_name][key] = str(value)
            serialized = io.StringIO()  # ConfigParser can only write to streams. Fine.
            parser.write(serialized)
            serialized.seek(0)
            script_str = serialized.read()
            script_str = script_str.replace("\\\\", r"\\\\").replace("\n", r"\\\n")  # Escape newlines because configparser sees those as section delimiters.
            script_list_strs.append(script_str)

        script_list_string = "\n".join(script_list_strs)  # ConfigParser should never output three newlines in a row when serialised, so it's a safe delimiter.

        if self._global_container_stack is None:
            return

        # Ensure we don't get triggered by our own write.
        self._global_container_stack.metaDataChanged.disconnect(self._restoreScriptInforFromMetadata)

        if "post_processing_scripts" not in self._global_container_stack.getMetaData():
            self._global_container_stack.setMetaDataEntry("post_processing_scripts", "")

        self._global_container_stack.setMetaDataEntry("post_processing_scripts", script_list_string)
        # We do want to listen to other events.
        self._global_container_stack.metaDataChanged.connect(self._restoreScriptInforFromMetadata)

    ##  Creates the view used by show popup. The view is saved because of the fairly aggressive garbage collection.
    def _createView(self) -> None:
        Logger.log("d", "Creating post processing plugin view.")

        self.loadAllScripts()

        # Create the plugin dialog component
        path = os.path.join(cast(str, PluginRegistry.getInstance().getPluginPath("PostProcessingPlugin")), "PostProcessingPlugin.qml")
        self._view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        if self._view is None:
            Logger.log("e", "Not creating PostProcessing button near save button because the QML component failed to be created.")
            return
        Logger.log("d", "Post processing view created.")

        # Create the save button component
        CuraApplication.getInstance().addAdditionalComponent("saveButton", self._view.findChild(QObject, "postProcessingSaveAreaButton"))

    ##  Show the (GUI) popup of the post processing plugin.
    def showPopup(self) -> None:
        if self._view is None:
            self._createView()
            if self._view is None:
                Logger.log("e", "Not creating PostProcessing window since the QML component failed to be created.")
                return
        self._view.show()

    ##  Property changed: trigger re-slice
    #   To do this we use the global container stack propertyChanged.
    #   Re-slicing is necessary for setting changes in this plugin, because the changes
    #   are applied only once per "fresh" gcode
    def _propertyChanged(self) -> None:
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is not None:
            global_container_stack.propertyChanged.emit("post_processing_plugin", "value")

    @staticmethod
    def _isScriptAllowed(file_path: str) -> bool:
        """Checks whether the given file is allowed to be loaded"""
        if not ApplicationMetadata.IsEnterpriseVersion:
            # No signature needed
            return True

        if os.path.split(file_path)[0] == os.path.join(
                PluginRegistry.getInstance().getPluginPath("PostProcessingPlugin"),
                "scripts"):
            # Bundled scripts are trusted.
            return True

        trust_instance = Trust.getInstanceOrNone()
        if trust_instance is not None and Trust.signatureFileExistsFor(file_path):
            if trust_instance.signedFileCheck(file_path):
                return True

        return False  # Default verdict should be False, being the most secure fallback


