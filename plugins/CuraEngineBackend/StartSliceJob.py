#  Copyright (c) 2024 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.
import uuid

import os

import numpy
from string import Formatter
from enum import IntEnum
import time
from typing import Any, cast, Dict, List, Optional, Set, Tuple
import re
import pyArcus as Arcus  # For typing.
from PyQt6.QtCore import QCoreApplication

from UM.Job import Job
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.Settings.ContainerStack import ContainerStack #For typing.
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.Interfaces import ContainerInterface
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.SettingRelation import SettingRelation #For typing.

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Scene import Scene #For typing.
from UM.Settings.Validator import ValidatorState
from UM.Settings.SettingRelation import RelationType
from UM.Settings.SettingFunction import SettingFunction

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.OneAtATimeIterator import OneAtATimeIterator
from cura.Settings.ExtruderManager import ExtruderManager
from cura.CuraVersion import CuraVersion


NON_PRINTING_MESH_SETTINGS = ["anti_overhang_mesh", "infill_mesh", "cutting_mesh"]


class StartJobResult(IntEnum):
    Finished = 1
    Error = 2
    SettingError = 3
    NothingToSlice = 4
    MaterialIncompatible = 5
    BuildPlateError = 6
    ObjectSettingError = 7 #When an error occurs in per-object settings.
    ObjectsWithDisabledExtruder = 8


class GcodeStartEndFormatter(Formatter):
    # Formatter class that handles token expansion in start/end gcode
    # Example of a start/end gcode string:
    # ```
    # M104 S{material_print_temperature_layer_0, 0} ;pre-heat
    # M140 S{material_bed_temperature_layer_0} ;heat bed
    # M204 P{acceleration_print, 0} T{acceleration_travel, 0}
    # M205 X{jerk_print, 0}
    # ```
    # Any expression between curly braces will be evaluated and replaced with the result, using the
    # context of the provided default extruder. If no default extruder is provided, the global stack
    # will be used. Alternatively, if the expression is formatted as "{[expression], [extruder_nr]}",
    # then the expression will be evaluated with the extruder stack of the specified extruder_nr.

    _extruder_regex = re.compile(r"^\s*(?P<expression>.*)\s*,\s*(?P<extruder_nr_expr>.*)\s*$")

    def __init__(self, all_extruder_settings: Dict[str, Any], default_extruder_nr: int = -1) -> None:
        super().__init__()
        self._all_extruder_settings: Dict[str, Any] = all_extruder_settings
        self._default_extruder_nr: int = default_extruder_nr

    def get_field(self, field_name, args: [str], kwargs: dict) -> Tuple[str, str]:
        # get_field method parses all fields in the format-string and parses them individually to the get_value method.
        # e.g. for a string "Hello {foo.bar}" would the complete field "foo.bar" would be passed to get_field, and then
        # the individual parts "foo" and "bar" would be passed to get_value. This poses a problem for us, because  want
        # to parse the entire field as a single expression. To solve this, we override the get_field method and return
        # the entire field as the expression.
        return self.get_value(field_name, args, kwargs), field_name

    def get_value(self, expression: str, args: [str], kwargs: dict) -> str:

        # The following variables are not settings, but only become available after slicing.
        # when these variables are encountered, we return them as-is. They are replaced later
        # when the actual values are known.
        post_slice_data_variables = ["filament_cost", "print_time", "filament_amount", "filament_weight", "jobname"]
        if expression in post_slice_data_variables:
            return f"{{{expression}}}"

        extruder_nr = str(self._default_extruder_nr)

        # The settings may specify a specific extruder to use. This is done by
        # formatting the expression as "{expression}, {extruder_nr_expr}". If the
        # expression is formatted like this, we extract the extruder_nr and use
        # it to get the value from the correct extruder stack.
        match = self._extruder_regex.match(expression)
        if match:
            expression = match.group("expression")
            extruder_nr_expr = match.group("extruder_nr_expr")

            if extruder_nr_expr.isdigit():
                extruder_nr = extruder_nr_expr
            else:
                # We get the value of the extruder_nr_expr from `_all_extruder_settings` dictionary
                # rather than the global container stack. The `_all_extruder_settings["-1"]` is a
                # dict-representation of the global container stack, with additional properties such
                # as `initial_extruder_nr`. As users may enter such expressions we can't use the
                # global container stack.
                extruder_nr = str(self._all_extruder_settings["-1"].get(extruder_nr_expr, "-1"))

        if extruder_nr in self._all_extruder_settings:
            additional_variables = self._all_extruder_settings[extruder_nr].copy()
        else:
            Logger.warning(f"Extruder {extruder_nr} does not exist, using global settings")
            additional_variables = self._all_extruder_settings["-1"].copy()

        # Add the arguments and keyword arguments to the additional settings. These
        # are currently _not_ used, but they are added for consistency with the
        # base Formatter class.
        for key, value in enumerate(args):
            additional_variables[key] = value
        for key, value in kwargs.items():
            additional_variables[key] = value

        if extruder_nr == "-1":
            container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        else:
            container_stack = ExtruderManager.getInstance().getExtruderStack(extruder_nr)
            if not container_stack:
                Logger.warning(f"Extruder {extruder_nr} does not exist, using global settings")
                container_stack = CuraApplication.getInstance().getGlobalContainerStack()

        setting_function = SettingFunction(expression)
        value = setting_function(container_stack, additional_variables=additional_variables)

        return value


class StartSliceJob(Job):
    """Job class that builds up the message of scene data to send to CuraEngine."""

    def __init__(self, slice_message: Arcus.PythonMessage) -> None:
        super().__init__()

        self._scene: Scene = CuraApplication.getInstance().getController().getScene()
        self._slice_message: Arcus.PythonMessage = slice_message
        self._is_cancelled: bool = False
        self._build_plate_number: Optional[int] = None

        # cache for all setting values from all stacks (global & extruder) for the current machine
        self._all_extruders_settings: Optional[Dict[str, Any]] = None

    def getSliceMessage(self) -> Arcus.PythonMessage:
        return self._slice_message

    def setBuildPlate(self, build_plate_number: int) -> None:
        self._build_plate_number = build_plate_number

    def _checkStackForErrors(self, stack: ContainerStack) -> bool:
        """Check if a stack has any errors."""

        """returns true if it has errors, false otherwise."""

        top_of_stack = cast(InstanceContainer, stack.getTop())  # Cache for efficiency.
        changed_setting_keys = top_of_stack.getAllKeys()

        # Add all relations to changed settings as well.
        for key in top_of_stack.getAllKeys():
            instance = top_of_stack.getInstance(key)
            if instance is None:
                continue
            self._addRelations(changed_setting_keys, instance.definition.relations)
            Job.yieldThread()

        for changed_setting_key in changed_setting_keys:
            if not stack.getProperty(changed_setting_key, "enabled"):
                continue

            validation_state = stack.getProperty(changed_setting_key, "validationState")

            if validation_state is None:
                definition = cast(SettingDefinition, stack.getSettingDefinition(changed_setting_key))
                validator_type = SettingDefinition.getValidatorForType(definition.type)
                if validator_type:
                    validator = validator_type(changed_setting_key)
                    validation_state = validator(stack)
            if validation_state in (
            ValidatorState.Exception, ValidatorState.MaximumError, ValidatorState.MinimumError, ValidatorState.Invalid):
                Logger.log("w", "Setting %s is not valid, but %s. Aborting slicing.", changed_setting_key, validation_state)
                return True
            Job.yieldThread()

        return False

    def run(self) -> None:
        """Runs the job that initiates the slicing."""

        if self._build_plate_number is None:
            self.setResult(StartJobResult.Error)
            return

        stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not stack:
            self.setResult(StartJobResult.Error)
            return

        # Don't slice if there is a setting with an error value.
        if CuraApplication.getInstance().getMachineManager().stacksHaveErrors:
            self.setResult(StartJobResult.SettingError)
            return

        if CuraApplication.getInstance().getBuildVolume().hasErrors():
            self.setResult(StartJobResult.BuildPlateError)
            return

        # Wait for error checker to be done.
        while CuraApplication.getInstance().getMachineErrorChecker().needToWaitForResult:
            time.sleep(0.1)

        if CuraApplication.getInstance().getMachineErrorChecker().hasError:
            self.setResult(StartJobResult.SettingError)
            return

        # Don't slice if the buildplate or the nozzle type is incompatible with the materials
        if not CuraApplication.getInstance().getMachineManager().variantBuildplateCompatible and \
                not CuraApplication.getInstance().getMachineManager().variantBuildplateUsable:
            self.setResult(StartJobResult.MaterialIncompatible)
            return

        for extruder_stack in stack.extruderList:
            material = extruder_stack.findContainer({"type": "material"})
            if not extruder_stack.isEnabled:
                continue
            if material:
                if material.getMetaDataEntry("compatible") == False:
                    self.setResult(StartJobResult.MaterialIncompatible)
                    return

        # Don't slice if there is a per object setting with an error value.
        for node in DepthFirstIterator(self._scene.getRoot()):
            if not isinstance(node, CuraSceneNode) or not node.isSelectable():
                continue

            if self._checkStackForErrors(node.callDecoration("getStack")):
                self.setResult(StartJobResult.ObjectSettingError)
                return

        # Remove old layer data.
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("getLayerData") and node.callDecoration("getBuildPlateNumber") == self._build_plate_number:
                # Since we walk through all nodes in the scene, they always have a parent.
                cast(SceneNode, node.getParent()).removeChild(node)
                break

        # Get the objects in their groups to print.
        object_groups = []
        if stack.getProperty("print_sequence", "value") == "one_at_a_time":
            modifier_mesh_nodes = []

            for node in DepthFirstIterator(self._scene.getRoot()):
                build_plate_number = node.callDecoration("getBuildPlateNumber")
                if node.callDecoration("isNonPrintingMesh") and build_plate_number == self._build_plate_number:
                    modifier_mesh_nodes.append(node)

            for node in OneAtATimeIterator(self._scene.getRoot()):
                temp_list = []

                # Filter on current build plate
                build_plate_number = node.callDecoration("getBuildPlateNumber")
                if build_plate_number is not None and build_plate_number != self._build_plate_number:
                    continue

                children = node.getAllChildren()
                children.append(node)
                for child_node in children:
                    mesh_data = child_node.getMeshData()
                    if mesh_data and mesh_data.getVertices() is not None:
                        temp_list.append(child_node)

                if temp_list:
                    object_groups.append(temp_list + modifier_mesh_nodes)
                Job.yieldThread()
            if len(object_groups) == 0:
                Logger.log("w", "No objects suitable for one at a time found, or no correct order found")
        else:
            temp_list = []
            has_printing_mesh = False
            for node in DepthFirstIterator(self._scene.getRoot()):
                mesh_data = node.getMeshData()
                if node.callDecoration("isSliceable") and mesh_data and mesh_data.getVertices() is not None:
                    is_non_printing_mesh = bool(node.callDecoration("isNonPrintingMesh"))

                    # Find a reason not to add the node
                    if node.callDecoration("getBuildPlateNumber") != self._build_plate_number:
                        continue
                    if getattr(node, "_outside_buildarea", False) and not is_non_printing_mesh:
                        continue

                    temp_list.append(node)
                    if not is_non_printing_mesh:
                        has_printing_mesh = True

                Job.yieldThread()

            # If the list doesn't have any model with suitable settings then clean the list
            # otherwise CuraEngine will crash
            if not has_printing_mesh:
                temp_list.clear()

            if temp_list:
                object_groups.append(temp_list)

        global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            return
        extruders_enabled = [stack.isEnabled for stack in global_stack.extruderList]
        filtered_object_groups = []
        has_model_with_disabled_extruders = False
        associated_disabled_extruders = set()
        for group in object_groups:
            stack = global_stack
            skip_group = False
            for node in group:
                # Only check if the printing extruder is enabled for printing meshes
                is_non_printing_mesh = node.callDecoration("evaluateIsNonPrintingMesh")
                extruder_position = int(node.callDecoration("getActiveExtruderPosition"))
                if not is_non_printing_mesh and not extruders_enabled[extruder_position]:
                    skip_group = True
                    has_model_with_disabled_extruders = True
                    associated_disabled_extruders.add(extruder_position)
            if not skip_group:
                filtered_object_groups.append(group)

        if has_model_with_disabled_extruders:
            self.setResult(StartJobResult.ObjectsWithDisabledExtruder)
            associated_disabled_extruders = {p + 1 for p in associated_disabled_extruders}
            self.setMessage(", ".join(map(str, sorted(associated_disabled_extruders))))
            return

        # There are cases when there is nothing to slice. This can happen due to one at a time slicing not being
        # able to find a possible sequence or because there are no objects on the build plate (or they are outside
        # the build volume)
        if not filtered_object_groups:
            self.setResult(StartJobResult.NothingToSlice)
            return

        self._buildGlobalSettingsMessage(stack)
        self._buildGlobalInheritsStackMessage(stack)

        user_id = uuid.getnode()  # On all of Cura's supported platforms, this returns the MAC address which is pseudonymical information (!= anonymous).
        user_id %= 2 ** 16  # So to make it anonymous, apply a bitmask selecting only the last 16 bits. This prevents it from being traceable to a specific user but still gives somewhat of an idea of whether it's just the same user hitting the same crash over and over again, or if it's widespread.
        self._slice_message.sentry_id = f"{user_id}"
        self._slice_message.cura_version = CuraVersion

        # Add the project name to the message if the user allows for non-anonymous crash data collection.
        account = CuraApplication.getInstance().getCuraAPI().account
        if account and account.isLoggedIn and not CuraApplication.getInstance().getPreferences().getValue("info/anonymous_engine_crash_report"):
            self._slice_message.project_name = CuraApplication.getInstance().getPrintInformation().baseName
            self._slice_message.user_name = account.userName

        # Build messages for extruder stacks
        for extruder_stack in global_stack.extruderList:
            self._buildExtruderMessage(extruder_stack)

        for plugin in CuraApplication.getInstance().getBackendPlugins():
            if not plugin.usePlugin():
                continue
            for slot in plugin.getSupportedSlots():
                # Right now we just send the message for every slot that we support. A single plugin can support
                # multiple slots
                # In the future the frontend will need to decide what slots that a plugin actually supports should
                # also be used. For instance, if you have two plugins and each of them support a_generate and b_generate
                # only one of each can actually be used (eg; plugin 1 does both, plugin 1 does a_generate and 2 does
                # b_generate, etc).
                plugin_message = self._slice_message.addRepeatedMessage("engine_plugins")
                plugin_message.id = slot
                plugin_message.address = plugin.getAddress()
                plugin_message.port = plugin.getPort()
                plugin_message.plugin_name = plugin.getPluginId()
                plugin_message.plugin_version = plugin.getVersion()

        for group in filtered_object_groups:
            group_message = self._slice_message.addRepeatedMessage("object_lists")
            parent = group[0].getParent()
            if parent is not None and parent.callDecoration("isGroup"):
                self._handlePerObjectSettings(cast(CuraSceneNode, parent), group_message)

            for object in group:
                mesh_data = object.getMeshData()
                if mesh_data is None:
                    continue
                rot_scale = object.getWorldTransformation().getTransposed().getData()[0:3, 0:3]
                translate = object.getWorldTransformation().getData()[:3, 3]

                # This effectively performs a limited form of MeshData.getTransformed that ignores normals.
                verts = mesh_data.getVertices()
                verts = verts.dot(rot_scale)
                verts += translate

                # Convert from Y up axes to Z up axes. Equals a 90 degree rotation.
                verts[:, [1, 2]] = verts[:, [2, 1]]
                verts[:, 1] *= -1

                obj = group_message.addRepeatedMessage("objects")
                obj.id = id(object)
                obj.name = object.getName()
                indices = mesh_data.getIndices()
                if indices is not None:
                    flat_verts = numpy.take(verts, indices.flatten(), axis=0)
                else:
                    flat_verts = numpy.array(verts)

                obj.vertices = flat_verts

                self._handlePerObjectSettings(cast(CuraSceneNode, object), obj)

                Job.yieldThread()

        self.setResult(StartJobResult.Finished)

    def cancel(self) -> None:
        super().cancel()
        self._is_cancelled = True

    def isCancelled(self) -> bool:
        return self._is_cancelled

    def setIsCancelled(self, value: bool):
        self._is_cancelled = value

    def _buildReplacementTokens(self, stack: ContainerStack) -> Dict[str, Any]:
        """Creates a dictionary of tokens to replace in g-code pieces.

        This indicates what should be replaced in the start and end g-codes.
        :param stack: The stack to get the settings from to replace the tokens with.
        :return: A dictionary of replacement tokens to the values they should be replaced with.
        """

        result = {}
        for key in stack.getAllKeys():
            result[key] = stack.getProperty(key, "value")
            Job.yieldThread()

        # Material identification in addition to non-human-readable GUID
        result["material_id"] = stack.material.getMetaDataEntry("base_file", "")
        result["material_type"] = stack.material.getMetaDataEntry("material", "")
        result["material_name"] = stack.material.getMetaDataEntry("name", "")
        result["material_brand"] = stack.material.getMetaDataEntry("brand", "")

        result["quality_name"] = stack.quality.getMetaDataEntry("name", "")
        result["quality_changes_name"] = stack.qualityChanges.getMetaDataEntry("name")

        # Renamed settings.
        result["print_bed_temperature"] = result["material_bed_temperature"]
        result["print_temperature"] = result["material_print_temperature"]
        result["travel_speed"] = result["speed_travel"]

        #Some extra settings.
        result["time"] = time.strftime("%H:%M:%S")
        result["date"] = time.strftime("%d-%m-%Y")
        result["day"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][int(time.strftime("%w"))]
        result["initial_extruder_nr"] = CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr()

        return result

    def _cacheAllExtruderSettings(self):
        global_stack = cast(ContainerStack, CuraApplication.getInstance().getGlobalContainerStack())

        # NB: keys must be strings for the string formatter
        self._all_extruders_settings = {
            "-1": self._buildReplacementTokens(global_stack)
        }
        QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
        for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
            extruder_nr = extruder_stack.getProperty("extruder_nr", "value")
            self._all_extruders_settings[str(extruder_nr)] = self._buildReplacementTokens(extruder_stack)
            QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

    def _expandGcodeTokens(self, value: str, default_extruder_nr: int = -1) -> str:
        """Replace setting tokens in a piece of g-code.

        :param value: A piece of g-code to replace tokens in.
        :param default_extruder_nr: Stack nr to use when no stack nr is specified, defaults to the global stack
        """
        if not self._all_extruders_settings:
            self._cacheAllExtruderSettings()

        try:
            # Get "replacement-keys" for the extruders. In the formatter the settings stack is used to get the
            # replacement values for the setting-keys. However, the values for `material_id`, `material_type`,
            # etc are not in the settings stack.
            fmt = GcodeStartEndFormatter(self._all_extruders_settings, default_extruder_nr=default_extruder_nr)
            return str(fmt.format(value))
        except:
            Logger.logException("w", "Unable to do token replacement on start/end g-code")
            return str(value)

    def _buildExtruderMessage(self, stack: ContainerStack) -> None:
        """Create extruder message from stack"""

        message = self._slice_message.addRepeatedMessage("extruders")
        message.id = int(stack.getMetaDataEntry("position"))
        if not self._all_extruders_settings:
            self._cacheAllExtruderSettings()

        if self._all_extruders_settings is None:
            return

        extruder_nr = stack.getProperty("extruder_nr", "value")
        settings = self._all_extruders_settings[str(extruder_nr)].copy()

        # Also send the material GUID. This is a setting in fdmprinter, but we have no interface for it.
        settings["material_guid"] = stack.material.getMetaDataEntry("GUID", "")

        # Replace the setting tokens in start and end g-code.
        extruder_nr = stack.getProperty("extruder_nr", "value")
        settings["machine_extruder_start_code"] = self._expandGcodeTokens(settings["machine_extruder_start_code"], extruder_nr)
        settings["machine_extruder_end_code"] = self._expandGcodeTokens(settings["machine_extruder_end_code"], extruder_nr)

        global_definition = cast(ContainerInterface, cast(ContainerStack, stack.getNextStack()).getBottom())
        own_definition = cast(ContainerInterface, stack.getBottom())

        for key, value in settings.items():
            # Do not send settings that are not settable_per_extruder.
            # Since these can only be set in definition files, we only have to ask there.
            if not global_definition.getProperty(key, "settable_per_extruder") and \
                    not own_definition.getProperty(key, "settable_per_extruder"):
                    continue
            setting = message.getMessage("settings").addRepeatedMessage("settings")
            setting.name = key
            setting.value = str(value).encode("utf-8")
            Job.yieldThread()

    def _buildGlobalSettingsMessage(self, stack: ContainerStack) -> None:
        """Sends all global settings to the engine.

        The settings are taken from the global stack. This does not include any
        per-extruder settings or per-object settings.
        """

        if not self._all_extruders_settings:
            self._cacheAllExtruderSettings()

        if self._all_extruders_settings is None:
            return

        settings = self._all_extruders_settings["-1"].copy()

        # Pre-compute material material_bed_temp_prepend and material_print_temp_prepend
        start_gcode = settings["machine_start_gcode"]
        # Remove all the comments from the start g-code
        start_gcode = re.sub(r";.+?(\n|$)", "\n", start_gcode)
        bed_temperature_settings = ["material_bed_temperature", "material_bed_temperature_layer_0"]
        pattern = r"\{(%s)(,\s?\w+)?\}" % "|".join(bed_temperature_settings) # match {setting} as well as {setting, extruder_nr}
        settings["material_bed_temp_prepend"] = re.search(pattern, start_gcode) == None
        print_temperature_settings = ["material_print_temperature", "material_print_temperature_layer_0", "default_material_print_temperature", "material_initial_print_temperature", "material_final_print_temperature", "material_standby_temperature", "print_temperature"]
        pattern = r"\{(%s)(,\s?\w+)?\}" % "|".join(print_temperature_settings) # match {setting} as well as {setting, extruder_nr}
        settings["material_print_temp_prepend"] = re.search(pattern, start_gcode) is None

        # Replace the setting tokens in start and end g-code.
        # Use values from the first used extruder by default so we get the expected temperatures
        initial_extruder_nr = CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr()
        settings["machine_start_gcode"] = self._expandGcodeTokens(settings["machine_start_gcode"], initial_extruder_nr)
        settings["machine_end_gcode"] = self._expandGcodeTokens(settings["machine_end_gcode"], initial_extruder_nr)

        # Manually add 'nozzle offsetting', since that is a metadata-entry instead for some reason.
        # NOTE: This probably needs to be an actual setting at some point.
        settings["nozzle_offsetting_for_disallowed_areas"] = CuraApplication.getInstance().getGlobalContainerStack().getMetaDataEntry("nozzle_offsetting_for_disallowed_areas", True)

        # Add all sub-messages for each individual setting.
        for key, value in settings.items():
            setting_message = self._slice_message.getMessage("global_settings").addRepeatedMessage("settings")
            setting_message.name = key
            setting_message.value = str(value).encode("utf-8")
            Job.yieldThread()

    def _buildGlobalInheritsStackMessage(self, stack: ContainerStack) -> None:
        """Sends for some settings which extruder they should fallback to if not set.

        This is only set for settings that have the limit_to_extruder
        property.

        :param stack: The global stack with all settings, from which to read the
            limit_to_extruder property.
        """

        for key in stack.getAllKeys():
            extruder_position = int(round(float(stack.getProperty(key, "limit_to_extruder"))))
            if extruder_position >= 0:  # Set to a specific extruder.
                setting_extruder = self._slice_message.addRepeatedMessage("limit_to_extruder")
                setting_extruder.name = key
                setting_extruder.extruder = extruder_position
            Job.yieldThread()

    def _handlePerObjectSettings(self, node: CuraSceneNode, message: Arcus.PythonMessage):
        """Check if a node has per object settings and ensure that they are set correctly in the message

        :param node: Node to check.
        :param message: object_lists message to put the per object settings in
        """

        stack = node.callDecoration("getStack")

        # Check if the node has a stack attached to it and the stack has any settings in the top container.
        if not stack:
            return

        # Check all settings for relations, so we can also calculate the correct values for dependent settings.
        top_of_stack = stack.getTop()  # Cache for efficiency.
        changed_setting_keys = top_of_stack.getAllKeys()

        # Add all relations to changed settings as well.
        for key in top_of_stack.getAllKeys():
            instance = top_of_stack.getInstance(key)
            self._addRelations(changed_setting_keys, instance.definition.relations)
            Job.yieldThread()

        # Ensure that the engine is aware what the build extruder is.
        changed_setting_keys.add("extruder_nr")

        # Get values for all changed settings
        for key in changed_setting_keys:
            setting = message.addRepeatedMessage("settings")
            setting.name = key
            extruder = int(round(float(stack.getProperty(key, "limit_to_extruder"))))

            # Check if limited to a specific extruder, but not overridden by per-object settings.
            if extruder >= 0 and key not in changed_setting_keys:
                limited_stack = ExtruderManager.getInstance().getActiveExtruderStacks()[extruder]
            else:
                limited_stack = stack

            setting.value = str(limited_stack.getProperty(key, "value")).encode("utf-8")

            Job.yieldThread()

    def _addRelations(self, relations_set: Set[str], relations: List[SettingRelation]):
        """Recursive function to put all settings that require each other for value changes in a list

        :param relations_set: Set of keys of settings that are influenced
        :param relations: list of relation objects that need to be checked.
        """

        for relation in filter(lambda r: r.role == "value" or r.role == "limit_to_extruder", relations):
            if relation.type == RelationType.RequiresTarget:
                continue

            relations_set.add(relation.target.key)
            self._addRelations(relations_set, relation.target.relations)
