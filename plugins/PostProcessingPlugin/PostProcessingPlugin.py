# Copyright (c) 2015 Jaime van Kessel, Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger

import os.path
import pkgutil
import sys
import importlib.util

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


##  The post processing plugin is an Extension type plugin that enables pre-written scripts to post process generated
#   g-code files.
class PostProcessingPlugin(QObject, Extension):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.addMenuItem(i18n_catalog.i18n("Modify G-Code"), self.showPopup)
        self._view = None

        # Loaded scripts are all scripts that can be used
        self._loaded_scripts = {}
        self._script_labels = {}

        # Script list contains instances of scripts in loaded_scripts.
        # There can be duplicates, which will be executed in sequence.
        self._script_list = []
        self._selected_script_index = -1

        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.execute)

    selectedIndexChanged = pyqtSignal()
    @pyqtProperty("QVariant", notify = selectedIndexChanged)
    def selectedScriptDefinitionId(self):
        try:
            return self._script_list[self._selected_script_index].getDefinitionId()
        except:
            return ""

    @pyqtProperty("QVariant", notify=selectedIndexChanged)
    def selectedScriptStackId(self):
        try:
            return self._script_list[self._selected_script_index].getStackId()
        except:
            return ""

    ##  Execute all post-processing scripts on the gcode.
    def execute(self, output_device):
        scene = Application.getInstance().getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict")
        if not gcode_dict:
            return

        # get gcode list for the active build plate
        active_build_plate_id = Application.getInstance().getBuildPlateModel().activeBuildPlate
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
    def setSelectedScriptIndex(self, index):
        self._selected_script_index = index
        self.selectedIndexChanged.emit()

    @pyqtProperty(int, notify = selectedIndexChanged)
    def selectedScriptIndex(self):
        return self._selected_script_index

    @pyqtSlot(int, int)
    def moveScript(self, index, new_index):
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
    def removeScriptByIndex(self, index):
        self._script_list.pop(index)
        if len(self._script_list) - 1 < self._selected_script_index:
            self._selected_script_index = len(self._script_list) - 1
        self.scriptListChanged.emit()
        self.selectedIndexChanged.emit()  # Ensure that settings are updated
        self._propertyChanged()

    ##  Load all scripts from provided path.
    #   This should probably only be done on init.
    #   \param path Path to check for scripts.
    def loadAllScripts(self, path):
        scripts = pkgutil.iter_modules(path = [path])
        for loader, script_name, ispkg in scripts:
            # Iterate over all scripts.
            if script_name not in sys.modules:
                spec = importlib.util.spec_from_file_location(__name__ + "." + script_name, os.path.join(path, script_name + ".py"))
                loaded_script = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(loaded_script)
                sys.modules[script_name] = loaded_script

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
        self.loadedScriptListChanged.emit()

    loadedScriptListChanged = pyqtSignal()
    @pyqtProperty("QVariantList", notify = loadedScriptListChanged)
    def loadedScriptList(self):
        return sorted(list(self._loaded_scripts.keys()))

    @pyqtSlot(str, result = str)
    def getScriptLabelByKey(self, key):
        return self._script_labels[key]

    scriptListChanged = pyqtSignal()
    @pyqtProperty("QVariantList", notify = scriptListChanged)
    def scriptList(self):
        script_list = [script.getSettingData()["key"] for script in self._script_list]
        return script_list

    @pyqtSlot(str)
    def addScriptToList(self, key):
        Logger.log("d", "Adding script %s to list.", key)
        new_script = self._loaded_scripts[key]()
        self._script_list.append(new_script)
        self.setSelectedScriptIndex(len(self._script_list) - 1)
        self.scriptListChanged.emit()
        self._propertyChanged()

    ##  Creates the view used by show popup. The view is saved because of the fairly aggressive garbage collection.
    def _createView(self):
        Logger.log("d", "Creating post processing plugin view.")

        ## Load all scripts in the scripts folders
        for root in [PluginRegistry.getInstance().getPluginPath("PostProcessingPlugin"), Resources.getStoragePath(Resources.Preferences)]:
            try:
                path = os.path.join(root, "scripts")
                if not os.path.isdir(path):
                    try:
                        os.makedirs(path)
                    except OSError:
                        Logger.log("w", "Unable to create a folder for scripts: " + path)
                        continue

                self.loadAllScripts(path)
            except Exception as e:
                Logger.logException("e", "Exception occurred while loading post processing plugin: {error_msg}".format(error_msg = str(e)))

        # Create the plugin dialog component
        path = os.path.join(PluginRegistry.getInstance().getPluginPath("PostProcessingPlugin"), "PostProcessingPlugin.qml")
        self._view = Application.getInstance().createQmlComponent(path, {"manager": self})
        Logger.log("d", "Post processing view created.")

        # Create the save button component
        Application.getInstance().addAdditionalComponent("saveButton", self._view.findChild(QObject, "postProcessingSaveAreaButton"))

    ##  Show the (GUI) popup of the post processing plugin.
    def showPopup(self):
        if self._view is None:
            self._createView()
        self._view.show()

    ##  Property changed: trigger re-slice
    #   To do this we use the global container stack propertyChanged.
    #   Re-slicing is necessary for setting changes in this plugin, because the changes
    #   are applied only once per "fresh" gcode
    def _propertyChanged(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        global_container_stack.propertyChanged.emit("post_processing_plugin", "value")


