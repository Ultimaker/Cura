# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty
from UM.FlameProfiler import pyqtSlot

from UM.Application import Application
from UM.Logger import Logger
from UM.Qt.Duration import Duration
from UM.Preferences import Preferences
from UM.Scene.SceneNode import SceneNode
from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Scene.CuraSceneNode import CuraSceneNode

from cura.Settings.ExtruderManager import ExtruderManager
from typing import Dict

import math
import os.path
import unicodedata
import json
import re #To create abbreviations for printer names.

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

##  A class for processing and calculating minimum, current and maximum print time as well as managing the job name
#
#   This class contains all the logic relating to calculation and slicing for the
#   time/quality slider concept. It is a rather tricky combination of event handling
#   and state management. The logic behind this is as follows:
#
#   - A scene change or setting change event happens.
#        We track what the source was of the change, either a scene change, a setting change, an active machine change or something else.
#   - This triggers a new slice with the current settings - this is the "current settings pass".
#   - When the slice is done, we update the current print time and material amount.
#   - If the source of the slice was not a Setting change, we start the second slice pass, the "low quality settings pass". Otherwise we stop here.
#   - When that is done, we update the minimum print time and start the final slice pass, the "Extra Fine settings pass".
#   - When the Extra Fine pass is done, we update the maximum print time.
#
#   This class also mangles the current machine name and the filename of the first loaded mesh into a job name.
#   This job name is requested by the JobSpecs qml file.
class PrintInformation(QObject):
    class SlicePass:
        CurrentSettings = 1
        LowQualitySettings = 2
        HighQualitySettings = 3

    class SliceReason:
        SceneChanged = 1
        SettingChanged = 2
        ActiveMachineChanged = 3
        Other = 4

    def __init__(self, parent = None):
        super().__init__(parent)

        self.initializeCuraMessagePrintTimeProperties()

        self._material_lengths = {}  # indexed by build plate number
        self._material_weights = {}
        self._material_costs = {}
        self._material_names = {}

        self._pre_sliced = False

        self._backend = Application.getInstance().getBackend()
        if self._backend:
            self._backend.printDurationMessage.connect(self._onPrintDurationMessage)
        Application.getInstance().getController().getScene().sceneChanged.connect(self._onSceneChanged)

        self._base_name = ""
        self._abbr_machine = ""
        self._job_name = ""
        self._project_name = ""
        self._active_build_plate = 0
        self._initVariablesWithBuildPlate(self._active_build_plate)

        Application.getInstance().globalContainerStackChanged.connect(self._updateJobName)
        Application.getInstance().fileLoaded.connect(self.setBaseName)
        Application.getInstance().getBuildPlateModel().activeBuildPlateChanged.connect(self._onActiveBuildPlateChanged)
        Application.getInstance().workspaceLoaded.connect(self.setProjectName)

        Preferences.getInstance().preferenceChanged.connect(self._onPreferencesChanged)

        self._active_material_container = None
        Application.getInstance().getMachineManager().activeMaterialChanged.connect(self._onActiveMaterialChanged)
        self._onActiveMaterialChanged()

        self._material_amounts = []

    # Crate cura message translations and using translation keys initialize empty time Duration object for total time
    # and time for each feature
    def initializeCuraMessagePrintTimeProperties(self):
        self._current_print_time = {}  # Duration(None, self)

        self._print_time_message_translations = {
            "inset_0": catalog.i18nc("@tooltip", "Outer Wall"),
            "inset_x": catalog.i18nc("@tooltip", "Inner Walls"),
            "skin": catalog.i18nc("@tooltip", "Skin"),
            "infill": catalog.i18nc("@tooltip", "Infill"),
            "support_infill": catalog.i18nc("@tooltip", "Support Infill"),
            "support_interface": catalog.i18nc("@tooltip", "Support Interface"),
            "support": catalog.i18nc("@tooltip", "Support"),
            "skirt": catalog.i18nc("@tooltip", "Skirt"),
            "travel": catalog.i18nc("@tooltip", "Travel"),
            "retract": catalog.i18nc("@tooltip", "Retractions"),
            "none": catalog.i18nc("@tooltip", "Other")
        }

        self._print_time_message_values = {}

    def _initPrintTimeMessageValues(self, build_plate_number):
        # Full fill message values using keys from _print_time_message_translations
        self._print_time_message_values[build_plate_number] = {}
        for key in self._print_time_message_translations.keys():
            self._print_time_message_values[build_plate_number][key] = Duration(None, self)

    def _initVariablesWithBuildPlate(self, build_plate_number):
        if build_plate_number not in self._print_time_message_values:
            self._initPrintTimeMessageValues(build_plate_number)
        if self._active_build_plate not in self._material_lengths:
            self._material_lengths[self._active_build_plate] = []
        if self._active_build_plate not in self._material_weights:
            self._material_weights[self._active_build_plate] = []
        if self._active_build_plate not in self._material_costs:
            self._material_costs[self._active_build_plate] = []
        if self._active_build_plate not in self._material_names:
            self._material_names[self._active_build_plate] = []
        if self._active_build_plate not in self._current_print_time:
            self._current_print_time[self._active_build_plate] = Duration(None, self)

    currentPrintTimeChanged = pyqtSignal()

    preSlicedChanged = pyqtSignal()

    @pyqtProperty(bool, notify=preSlicedChanged)
    def preSliced(self):
        return self._pre_sliced

    def setPreSliced(self, pre_sliced):
        self._pre_sliced = pre_sliced
        self.preSlicedChanged.emit()

    @pyqtProperty(Duration, notify = currentPrintTimeChanged)
    def currentPrintTime(self):
        return self._current_print_time[self._active_build_plate]

    materialLengthsChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = materialLengthsChanged)
    def materialLengths(self):
        return self._material_lengths[self._active_build_plate]

    materialWeightsChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = materialWeightsChanged)
    def materialWeights(self):
        return self._material_weights[self._active_build_plate]

    materialCostsChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = materialCostsChanged)
    def materialCosts(self):
        return self._material_costs[self._active_build_plate]

    materialNamesChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = materialNamesChanged)
    def materialNames(self):
        return self._material_names[self._active_build_plate]

    def printTimes(self):
        return self._print_time_message_values[self._active_build_plate]

    def _onPrintDurationMessage(self, build_plate_number, print_time: Dict[str, int], material_amounts: list):
        self._updateTotalPrintTimePerFeature(build_plate_number, print_time)
        self.currentPrintTimeChanged.emit()

        self._material_amounts = material_amounts
        self._calculateInformation(build_plate_number)

    def _updateTotalPrintTimePerFeature(self, build_plate_number, print_time: Dict[str, int]):
        total_estimated_time = 0

        if build_plate_number not in self._print_time_message_values:
            self._initPrintTimeMessageValues(build_plate_number)

        for feature, time in print_time.items():
            if time != time:  # Check for NaN. Engine can sometimes give us weird values.
                self._print_time_message_values[build_plate_number].get(feature).setDuration(0)
                Logger.log("w", "Received NaN for print duration message")
                continue

            total_estimated_time += time
            self._print_time_message_values[build_plate_number].get(feature).setDuration(time)

        if build_plate_number not in self._current_print_time:
            self._current_print_time[build_plate_number] = Duration(None, self)
        self._current_print_time[build_plate_number].setDuration(total_estimated_time)

    def _calculateInformation(self, build_plate_number):
        if Application.getInstance().getGlobalContainerStack() is None:
            return

        # Material amount is sent as an amount of mm^3, so calculate length from that
        radius = Application.getInstance().getGlobalContainerStack().getProperty("material_diameter", "value") / 2
        self._material_lengths[build_plate_number] = []
        self._material_weights[build_plate_number] = []
        self._material_costs[build_plate_number] = []
        self._material_names[build_plate_number] = []

        material_preference_values = json.loads(Preferences.getInstance().getValue("cura/material_settings"))

        extruder_stacks = list(ExtruderManager.getInstance().getMachineExtruders(Application.getInstance().getGlobalContainerStack().getId()))
        for index, amount in enumerate(self._material_amounts):
            ## Find the right extruder stack. As the list isn't sorted because it's a annoying generator, we do some
            #  list comprehension filtering to solve this for us.
            material = None
            if extruder_stacks:  # Multi extrusion machine
                extruder_stack = [extruder for extruder in extruder_stacks if extruder.getMetaDataEntry("position") == str(index)][0]
                density = extruder_stack.getMetaDataEntry("properties", {}).get("density", 0)
                material = extruder_stack.findContainer({"type": "material"})
            else:  # Machine with no extruder stacks
                density = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("properties", {}).get("density", 0)
                material = Application.getInstance().getGlobalContainerStack().findContainer({"type": "material"})

            weight = float(amount) * float(density) / 1000
            cost = 0
            material_name = catalog.i18nc("@label unknown material", "Unknown")
            if material:
                material_guid = material.getMetaDataEntry("GUID")
                material_name = material.getName()
                if material_guid in material_preference_values:
                    material_values = material_preference_values[material_guid]

                    weight_per_spool = float(material_values["spool_weight"] if material_values and "spool_weight" in material_values else 0)
                    cost_per_spool = float(material_values["spool_cost"] if material_values and "spool_cost" in material_values else 0)

                    if weight_per_spool != 0:
                        cost = cost_per_spool * weight / weight_per_spool
                    else:
                        cost = 0

            if radius != 0:
                length = round((amount / (math.pi * radius ** 2)) / 1000, 2)
            else:
                length = 0
            self._material_weights[build_plate_number].append(weight)
            self._material_lengths[build_plate_number].append(length)
            self._material_costs[build_plate_number].append(cost)
            self._material_names[build_plate_number].append(material_name)

        self.materialLengthsChanged.emit()
        self.materialWeightsChanged.emit()
        self.materialCostsChanged.emit()
        self.materialNamesChanged.emit()

    def _onPreferencesChanged(self, preference):
        if preference != "cura/material_settings":
            return

        for build_plate_number in range(Application.getInstance().getBuildPlateModel().maxBuildPlate + 1):
            self._calculateInformation(build_plate_number)

    def _onActiveMaterialChanged(self):
        if self._active_material_container:
            try:
                self._active_material_container.metaDataChanged.disconnect(self._onMaterialMetaDataChanged)
            except TypeError: #pyQtSignal gives a TypeError when disconnecting from something that is already disconnected.
                pass

        active_material_id = Application.getInstance().getMachineManager().activeMaterialId
        active_material_containers = ContainerRegistry.getInstance().findInstanceContainers(id = active_material_id)

        if active_material_containers:
            self._active_material_container = active_material_containers[0]
            self._active_material_container.metaDataChanged.connect(self._onMaterialMetaDataChanged)

    def _onActiveBuildPlateChanged(self):
        new_active_build_plate = Application.getInstance().getBuildPlateModel().activeBuildPlate
        if new_active_build_plate != self._active_build_plate:
            self._active_build_plate = new_active_build_plate

            self._initVariablesWithBuildPlate(self._active_build_plate)

            self.materialLengthsChanged.emit()
            self.materialWeightsChanged.emit()
            self.materialCostsChanged.emit()
            self.materialNamesChanged.emit()
            self.currentPrintTimeChanged.emit()

    def _onMaterialMetaDataChanged(self, *args, **kwargs):
        for build_plate_number in range(Application.getInstance().getBuildPlateModel().maxBuildPlate + 1):
            self._calculateInformation(build_plate_number)

    @pyqtSlot(str)
    def setJobName(self, name):
        self._job_name = name
        self.jobNameChanged.emit()

    jobNameChanged = pyqtSignal()

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    def _updateJobName(self):
        if self._base_name == "":
            self._job_name = ""
            self.jobNameChanged.emit()
            return

        base_name = self._stripAccents(self._base_name)
        self._setAbbreviatedMachineName()
        if self._pre_sliced:
            self._job_name = catalog.i18nc("@label", "Pre-sliced file {0}", base_name)
        elif Preferences.getInstance().getValue("cura/jobname_prefix"):
            # Don't add abbreviation if it already has the exact same abbreviation.
            if base_name.startswith(self._abbr_machine + "_"):
                self._job_name = base_name
            else:
                self._job_name = self._abbr_machine + "_" + base_name
        else:
            self._job_name = base_name

        self.jobNameChanged.emit()

    @pyqtProperty(str)
    def baseName(self):
        return self._base_name

    @pyqtSlot(str)
    def setProjectName(self, name):
        self.setBaseName(name, is_project_file = True)

    @pyqtSlot(str)
    def setBaseName(self, base_name, is_project_file = False):
        # Ensure that we don't use entire path but only filename
        name = os.path.basename(base_name)

        # when a file is opened using the terminal; the filename comes from _onFileLoaded and still contains its
        # extension. This cuts the extension off if necessary.
        name = os.path.splitext(name)[0]

        # if this is a profile file, always update the job name
        # name is "" when I first had some meshes and afterwards I deleted them so the naming should start again
        is_empty = name == ""
        if is_project_file or (is_empty or (self._base_name == "" and self._base_name != name)):
            # remove ".curaproject" suffix from (imported) the file name
            if name.endswith(".curaproject"):
                name = name[:name.rfind(".curaproject")]
            self._base_name = name
            self._updateJobName()


    ##  Created an acronymn-like abbreviated machine name from the currently active machine name
    #   Called each time the global stack is switched
    def _setAbbreviatedMachineName(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            self._abbr_machine = ""
            return
        active_machine_type_id = global_container_stack.definition.getId()

        abbr_machine = ""
        for word in re.findall(r"[\w']+", active_machine_type_id):
            if word.lower() == "ultimaker":
                abbr_machine += "UM"
            elif word.isdigit():
                abbr_machine += word
            else:
                stripped_word = self._stripAccents(word.upper())
                # - use only the first character if the word is too long (> 3 characters)
                # - use the whole word if it's not too long (<= 3 characters)
                if len(stripped_word) > 3:
                    stripped_word = stripped_word[0]
                abbr_machine += stripped_word

        self._abbr_machine = abbr_machine

    ##  Utility method that strips accents from characters (eg: â -> a)
    def _stripAccents(self, str):
        return ''.join(char for char in unicodedata.normalize('NFD', str) if unicodedata.category(char) != 'Mn')

    @pyqtSlot(result = "QVariantMap")
    def getFeaturePrintTimes(self):
        result = {}
        if self._active_build_plate not in self._print_time_message_values:
            self._initPrintTimeMessageValues(self._active_build_plate)
        for feature, time in self._print_time_message_values[self._active_build_plate].items():
            if feature in self._print_time_message_translations:
                result[self._print_time_message_translations[feature]] = time
            else:
                result[feature] = time
        return result

    # Simulate message with zero time duration
    def setToZeroPrintInformation(self, build_plate):

        # Construct the 0-time message
        temp_message = {}
        if build_plate not in self._print_time_message_values:
            self._print_time_message_values[build_plate] = {}
        for key in self._print_time_message_values[build_plate].keys():
            temp_message[key] = 0
        temp_material_amounts = [0]

        self._onPrintDurationMessage(build_plate, temp_message, temp_material_amounts)

    ##  Listen to scene changes to check if we need to reset the print information
    def _onSceneChanged(self, scene_node):

        # Ignore any changes that are not related to sliceable objects
        if not isinstance(scene_node, SceneNode)\
                or not scene_node.callDecoration("isSliceable")\
                or not scene_node.callDecoration("getBuildPlateNumber") == self._active_build_plate:
            return

        self.setToZeroPrintInformation(self._active_build_plate)
