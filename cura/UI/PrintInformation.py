# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
import math
import os
import unicodedata
from typing import Dict, List, Optional, TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QTimer

from UM.Logger import Logger
from UM.Qt.Duration import Duration
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeTypeNotFoundError

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication

catalog = i18nCatalog("cura")


class PrintInformation(QObject):
    """A class for processing and the print times per build plate as well as managing the job name

    This class also mangles the current machine name and the filename of the first loaded mesh into a job name.
    This job name is requested by the JobSpecs qml file.
    """


    UNTITLED_JOB_NAME = "Untitled"

    def __init__(self, application: "CuraApplication", parent = None) -> None:
        super().__init__(parent)
        self._application = application

        self.initializeCuraMessagePrintTimeProperties()

        # Indexed by build plate number
        self._material_lengths = {}  # type: Dict[int, List[float]]
        self._material_weights = {}  # type: Dict[int, List[float]]
        self._material_costs = {}   # type: Dict[int, List[float]]
        self._material_names = {}  # type: Dict[int, List[str]]

        self._pre_sliced = False

        self._backend = self._application.getBackend()
        if self._backend:
            self._backend.printDurationMessage.connect(self._onPrintDurationMessage)

        self._application.getController().getScene().sceneChanged.connect(self._onSceneChangedDelayed)

        self._change_timer = QTimer()
        self._change_timer.setInterval(100)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._onSceneChanged)

        self._is_user_specified_job_name = False
        self._base_name = ""
        self._abbr_machine = ""
        self._job_name = ""
        self._active_build_plate = 0
        self._initVariablesByBuildPlate(self._active_build_plate)

        self._multi_build_plate_model = self._application.getMultiBuildPlateModel()

        self._application.globalContainerStackChanged.connect(self._updateJobName)
        self._application.globalContainerStackChanged.connect(self.setToZeroPrintInformation)
        self._application.fileLoaded.connect(self.setBaseName)
        self._application.workspaceLoaded.connect(self.setProjectName)
        self._application.getMachineManager().rootMaterialChanged.connect(self._onActiveMaterialsChanged)
        self._application.getInstance().getPreferences().preferenceChanged.connect(self._onPreferencesChanged)

        self._multi_build_plate_model.activeBuildPlateChanged.connect(self._onActiveBuildPlateChanged)
        self._material_amounts = []  # type: List[float]
        self._onActiveMaterialsChanged()

    def initializeCuraMessagePrintTimeProperties(self) -> None:
        self._current_print_time = {}  # type: Dict[int, Duration]

        self._print_time_message_translations = {
            "inset_0": catalog.i18nc("@tooltip", "Outer Wall"),
            "inset_x": catalog.i18nc("@tooltip", "Inner Walls"),
            "skin": catalog.i18nc("@tooltip", "Skin"),
            "infill": catalog.i18nc("@tooltip", "Infill"),
            "support_infill": catalog.i18nc("@tooltip", "Support Infill"),
            "support_interface": catalog.i18nc("@tooltip", "Support Interface"),
            "support": catalog.i18nc("@tooltip", "Support"),
            "skirt": catalog.i18nc("@tooltip", "Skirt"),
            "prime_tower": catalog.i18nc("@tooltip", "Prime Tower"),
            "travel": catalog.i18nc("@tooltip", "Travel"),
            "retract": catalog.i18nc("@tooltip", "Retractions"),
            "none": catalog.i18nc("@tooltip", "Other")
        }

        self._print_times_per_feature = {}  # type: Dict[int, Dict[str, Duration]]

    def _initPrintTimesPerFeature(self, build_plate_number: int) -> None:
        # Full fill message values using keys from _print_time_message_translations
        self._print_times_per_feature[build_plate_number] = {}
        for key in self._print_time_message_translations.keys():
            self._print_times_per_feature[build_plate_number][key] = Duration(None, self)

    def _initVariablesByBuildPlate(self, build_plate_number: int) -> None:
        if build_plate_number not in self._print_times_per_feature:
            self._initPrintTimesPerFeature(build_plate_number)
        if self._active_build_plate not in self._material_lengths:
            self._material_lengths[self._active_build_plate] = []
        if self._active_build_plate not in self._material_weights:
            self._material_weights[self._active_build_plate] = []
        if self._active_build_plate not in self._material_costs:
            self._material_costs[self._active_build_plate] = []
        if self._active_build_plate not in self._material_names:
            self._material_names[self._active_build_plate] = []
        if self._active_build_plate not in self._current_print_time:
            self._current_print_time[self._active_build_plate] = Duration(parent = self)

    currentPrintTimeChanged = pyqtSignal()

    preSlicedChanged = pyqtSignal()

    @pyqtProperty(bool, notify=preSlicedChanged)
    def preSliced(self) -> bool:
        return self._pre_sliced

    def setPreSliced(self, pre_sliced: bool) -> None:
        if self._pre_sliced != pre_sliced:
            self._pre_sliced = pre_sliced
            self._updateJobName()
            self.preSlicedChanged.emit()

    @pyqtProperty(Duration, notify = currentPrintTimeChanged)
    def currentPrintTime(self) -> Duration:
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

    #   Get all print times (by feature) of the active buildplate.
    def printTimes(self) -> Dict[str, Duration]:
        return self._print_times_per_feature[self._active_build_plate]

    def _onPrintDurationMessage(self, build_plate_number: int, print_times_per_feature: Dict[str, int], material_amounts: List[float]) -> None:
        self._updateTotalPrintTimePerFeature(build_plate_number, print_times_per_feature)
        self.currentPrintTimeChanged.emit()

        self._material_amounts = material_amounts
        self._calculateInformation(build_plate_number)

    def _updateTotalPrintTimePerFeature(self, build_plate_number: int, print_times_per_feature: Dict[str, int]) -> None:
        total_estimated_time = 0

        if build_plate_number not in self._print_times_per_feature:
            self._initPrintTimesPerFeature(build_plate_number)

        for feature, time in print_times_per_feature.items():
            if feature not in self._print_times_per_feature[build_plate_number]:
                self._print_times_per_feature[build_plate_number][feature] = Duration(parent=self)
            duration = self._print_times_per_feature[build_plate_number][feature]

            if time != time:  # Check for NaN. Engine can sometimes give us weird values.
                duration.setDuration(0)
                Logger.log("w", "Received NaN for print duration message")
                continue

            total_estimated_time += time
            duration.setDuration(time)

        if build_plate_number not in self._current_print_time:
            self._current_print_time[build_plate_number] = Duration(None, self)
        self._current_print_time[build_plate_number].setDuration(total_estimated_time)

    def _calculateInformation(self, build_plate_number: int) -> None:
        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None:
            return

        self._material_lengths[build_plate_number] = []
        self._material_weights[build_plate_number] = []
        self._material_costs[build_plate_number] = []
        self._material_names[build_plate_number] = []

        material_preference_values = json.loads(self._application.getInstance().getPreferences().getValue("cura/material_settings"))

        for index, extruder_stack in enumerate(global_stack.extruderList):
            if index >= len(self._material_amounts):
                continue
            amount = self._material_amounts[index]
            # Find the right extruder stack. As the list isn't sorted because it's a annoying generator, we do some
            # list comprehension filtering to solve this for us.
            density = extruder_stack.getMetaDataEntry("properties", {}).get("density", 0)
            material = extruder_stack.material
            radius = extruder_stack.getProperty("material_diameter", "value") / 2

            weight = float(amount) * float(density) / 1000
            cost = 0.

            material_guid = material.getMetaDataEntry("GUID")
            material_name = material.getName()

            if material_guid in material_preference_values:
                material_values = material_preference_values[material_guid]

                if material_values and "spool_weight" in material_values:
                    weight_per_spool = float(material_values["spool_weight"])
                else:
                    weight_per_spool = float(extruder_stack.getMetaDataEntry("properties", {}).get("weight", 0))

                cost_per_spool = float(material_values["spool_cost"] if material_values and "spool_cost" in material_values else 0)

                if weight_per_spool != 0:
                    cost = cost_per_spool * weight / weight_per_spool
                else:
                    cost = 0

            # Material amount is sent as an amount of mm^3, so calculate length from that
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

    def _onPreferencesChanged(self, preference: str) -> None:
        if preference == "cura/job_name_template":
            self._updateJobName()
        elif preference == "cura/material_settings":
            for build_plate_number in range(self._multi_build_plate_model.maxBuildPlate + 1):
                self._calculateInformation(build_plate_number)

    def _onActiveBuildPlateChanged(self) -> None:
        new_active_build_plate = self._multi_build_plate_model.activeBuildPlate
        if new_active_build_plate != self._active_build_plate:
            self._active_build_plate = new_active_build_plate
            self._updateJobName()

            self._initVariablesByBuildPlate(self._active_build_plate)

            self.materialLengthsChanged.emit()
            self.materialWeightsChanged.emit()
            self.materialCostsChanged.emit()
            self.materialNamesChanged.emit()
            self.currentPrintTimeChanged.emit()

    def _onActiveMaterialsChanged(self, *args, **kwargs) -> None:
        for build_plate_number in range(self._multi_build_plate_model.maxBuildPlate + 1):
            self._calculateInformation(build_plate_number)

    # Manual override of job name should also set the base name so that when the printer prefix is updated, it the
    # prefix can be added to the manually added name, not the old base name
    @pyqtSlot(str, bool)
    def setJobName(self, name: str, is_user_specified_job_name = False) -> None:
        self._is_user_specified_job_name = is_user_specified_job_name
        self._job_name = name
        self._base_name = name.replace(self._abbr_machine + "_", "")
        if name == "":
            self._is_user_specified_job_name = False
        self.jobNameChanged.emit()

    jobNameChanged = pyqtSignal()

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    def _updateJobName(self) -> None:
        if self._base_name == "":
            self._job_name = self.UNTITLED_JOB_NAME
            self._is_user_specified_job_name = False
            self.jobNameChanged.emit()
            return

        base_name = self._stripAccents(self._base_name)
        self._defineAbbreviatedMachineName()

        # Only update the job name when it's not user-specified.
        if not self._is_user_specified_job_name:
            if not self._pre_sliced:
                self._job_name = self.parseTemplate()
            else:
                self._job_name = base_name

        # In case there are several buildplates, a suffix is attached
        if self._multi_build_plate_model.maxBuildPlate > 0:
            connector = "_#"
            suffix = connector + str(self._active_build_plate + 1)
            if connector in self._job_name:
                self._job_name = self._job_name.split(connector)[0] # get the real name
            if self._active_build_plate != 0:
                self._job_name += suffix

        self.jobNameChanged.emit()

    @pyqtSlot(str)
    def setProjectName(self, name: str) -> None:
        self.setBaseName(name, is_project_file = True)

    baseNameChanged = pyqtSignal()

    def setBaseName(self, base_name: str, is_project_file: bool = False) -> None:
        self._is_user_specified_job_name = False

        # Ensure that we don't use entire path but only filename
        name = os.path.basename(base_name)

        # when a file is opened using the terminal; the filename comes from _onFileLoaded and still contains its
        # extension. This cuts the extension off if necessary.
        check_name = os.path.splitext(name)[0]
        filename_parts = os.path.basename(base_name).split(".")

        # If it's a gcode, also always update the job name
        is_gcode = False
        if len(filename_parts) > 1:
            # Only check the extension(s)
            is_gcode = "gcode" in filename_parts[1:]

        # if this is a profile file, always update the job name
        # name is "" when I first had some meshes and afterwards I deleted them so the naming should start again
        is_empty = check_name == ""
        if is_gcode or is_project_file or (is_empty or (self._base_name == "" and self._base_name != check_name)):
            # Only take the file name part, Note : file name might have 'dot' in name as well

            data = ""
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(name)
                data = mime_type.stripExtension(name)
            except MimeTypeNotFoundError:
                Logger.log("w", "Unsupported Mime Type Database file extension %s", name)

            if data is not None and check_name is not None:
                self._base_name = data
            else:
                self._base_name = ""

            # Strip the old "curaproject" extension from the name
            OLD_CURA_PROJECT_EXT = ".curaproject"
            if self._base_name.lower().endswith(OLD_CURA_PROJECT_EXT):
                self._base_name = self._base_name[:len(self._base_name) - len(OLD_CURA_PROJECT_EXT)]

            # CURA-5896 Try to strip extra extensions with an infinite amount of ".curaproject.3mf".
            OLD_CURA_PROJECT_3MF_EXT = ".curaproject.3mf"
            while self._base_name.lower().endswith(OLD_CURA_PROJECT_3MF_EXT):
                self._base_name = self._base_name[:len(self._base_name) - len(OLD_CURA_PROJECT_3MF_EXT)]

            self._updateJobName()

    @pyqtProperty(str, fset = setBaseName, notify = baseNameChanged)
    def baseName(self):
        return self._base_name

    def _defineAbbreviatedMachineName(self) -> None:
        """Created an acronym-like abbreviated machine name from the currently active machine name.

        Called each time the global stack is switched.
        """

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            self._abbr_machine = ""
            return
        active_machine_type_name = global_container_stack.definition.getName()

        self._abbr_machine = self._application.getMachineManager().getAbbreviatedMachineName(active_machine_type_name)

    def _stripAccents(self, to_strip: str) -> str:
        """Utility method that strips accents from characters (eg: â -> a)"""

        return ''.join(char for char in unicodedata.normalize('NFD', to_strip) if unicodedata.category(char) != 'Mn')

    @pyqtSlot(result = "QVariantMap")
    def getFeaturePrintTimes(self) -> Dict[str, Duration]:
        result = {}
        if self._active_build_plate not in self._print_times_per_feature:
            self._initPrintTimesPerFeature(self._active_build_plate)
        for feature, time in self._print_times_per_feature[self._active_build_plate].items():
            if feature in self._print_time_message_translations:
                result[self._print_time_message_translations[feature]] = time
            else:
                result[feature] = time
        return result

    # Simulate message with zero time duration
    def setToZeroPrintInformation(self, build_plate: Optional[int] = None) -> None:
        if build_plate is None:
            build_plate = self._active_build_plate

        # Construct the 0-time message
        temp_message = {}
        if build_plate not in self._print_times_per_feature:
            self._print_times_per_feature[build_plate] = {}
        for key in self._print_times_per_feature[build_plate].keys():
            temp_message[key] = 0
        temp_material_amounts = [0.]

        self._onPrintDurationMessage(build_plate, temp_message, temp_material_amounts)

    def _onSceneChangedDelayed(self, scene_node: SceneNode) -> None:
        # Ignore any changes that are not related to sliceable objects
        if not isinstance(scene_node, SceneNode) \
                or not scene_node.callDecoration("isSliceable") \
                or not scene_node.callDecoration("getBuildPlateNumber") == self._active_build_plate:
            return
        self._change_timer.start()

    def _onSceneChanged(self) -> None:
        """Listen to scene changes to check if we need to reset the print information"""

        self.setToZeroPrintInformation(self._active_build_plate)

    def parseTemplate(self) -> str:
        """Generate a print job name from the job name template

        The template is a user preference: "cura/job_name_template"
        """
        template = self._application.getInstance().getPreferences().getValue("cura/job_name_template")
        output = template

        output = output.replace("{machine_name_short}", self._abbr_machine)

        if "{machine_name}" in template:
            global_container_stack = self._application.getGlobalContainerStack()
            active_machine_type_name = global_container_stack.definition.getName() \
                if global_container_stack \
                else "no_machine"

            active_machine_type_name = active_machine_type_name.replace(" ", "_")
            output = output.replace("{machine_name}", active_machine_type_name)

        if "{project_name}" in template:
            base_name = self._stripAccents(self._base_name)
            output = output.replace("{project_name}", base_name)

        return output
