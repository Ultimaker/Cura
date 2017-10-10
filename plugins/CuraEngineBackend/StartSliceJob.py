# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from string import Formatter
from enum import IntEnum
import time

from UM.Job import Job
from UM.Application import Application
from UM.Logger import Logger

from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from UM.Settings.Validator import ValidatorState
from UM.Settings.SettingRelation import RelationType

from cura.OneAtATimeIterator import OneAtATimeIterator
from cura.Settings.ExtruderManager import ExtruderManager

class StartJobResult(IntEnum):
    Finished = 1
    Error = 2
    SettingError = 3
    NothingToSlice = 4
    MaterialIncompatible = 5
    BuildPlateError = 6


##  Formatter class that handles token expansion in start/end gcod
class GcodeStartEndFormatter(Formatter):
    def get_value(self, key, args, kwargs):  # [CodeStyle: get_value is an overridden function from the Formatter class]
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                Logger.log("w", "Unable to replace '%s' placeholder in start/end gcode", key)
                return "{" + key + "}"
        else:
            Logger.log("w", "Incorrectly formatted placeholder '%s' in start/end gcode", key)
            return "{" + str(key) + "}"


##  Job class that builds up the message of scene data to send to CuraEngine.
class StartSliceJob(Job):
    ##  Meshes that are sent to the engine regardless of being outside of the
    #   build volume.
    #
    #   If these settings are True for any mesh, the build volume is ignored.
    #   Note that Support Mesh is not in here because it actually generates
    #   g-code in the volume of the mesh.
    _not_printed_mesh_settings = {"anti_overhang_mesh", "infill_mesh", "cutting_mesh"}

    def __init__(self, slice_message):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._slice_message = slice_message
        self._is_cancelled = False

    def getSliceMessage(self):
        return self._slice_message

    ##  Check if a stack has any errors.
    ##  returns true if it has errors, false otherwise.
    def _checkStackForErrors(self, stack):
        if stack is None:
            return False

        for key in stack.getAllKeys():
            validation_state = stack.getProperty(key, "validationState")
            if validation_state in (ValidatorState.Exception, ValidatorState.MaximumError, ValidatorState.MinimumError):
                Logger.log("w", "Setting %s is not valid, but %s. Aborting slicing.", key, validation_state)
                return True
            Job.yieldThread()
        return False

    ##  Runs the job that initiates the slicing.
    def run(self):
        stack = Application.getInstance().getGlobalContainerStack()
        if not stack:
            self.setResult(StartJobResult.Error)
            return

        # Don't slice if there is a setting with an error value.
        if Application.getInstance().getMachineManager().stacksHaveErrors:
            self.setResult(StartJobResult.SettingError)
            return

        if Application.getInstance().getBuildVolume().hasErrors():
            self.setResult(StartJobResult.BuildPlateError)
            return

        for extruder_stack in ExtruderManager.getInstance().getMachineExtruders(stack.getId()):
            material = extruder_stack.findContainer({"type": "material"})
            if material:
                if material.getMetaDataEntry("compatible") == False:
                    self.setResult(StartJobResult.MaterialIncompatible)
                    return

        # Don't slice if there is a per object setting with an error value.
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is not SceneNode or not node.isSelectable():
                continue

            if self._checkStackForErrors(node.callDecoration("getStack")):
                self.setResult(StartJobResult.SettingError)
                return

        with self._scene.getSceneLock():
            # Remove old layer data.
            for node in DepthFirstIterator(self._scene.getRoot()):
                if node.callDecoration("getLayerData"):
                    node.getParent().removeChild(node)
                    break

            # Get the objects in their groups to print.
            object_groups = []
            if stack.getProperty("print_sequence", "value") == "one_at_a_time":
                for node in OneAtATimeIterator(self._scene.getRoot()):
                    temp_list = []

                    # Node can't be printed, so don't bother sending it.
                    if getattr(node, "_outside_buildarea", False):
                        continue

                    children = node.getAllChildren()
                    children.append(node)
                    for child_node in children:
                        if type(child_node) is SceneNode and child_node.getMeshData() and child_node.getMeshData().getVertices() is not None:
                            temp_list.append(child_node)

                    if temp_list:
                        object_groups.append(temp_list)
                    Job.yieldThread()
                if len(object_groups) == 0:
                    Logger.log("w", "No objects suitable for one at a time found, or no correct order found")
            else:
                temp_list = []
                for node in DepthFirstIterator(self._scene.getRoot()):
                    if type(node) is SceneNode and node.getMeshData() and node.getMeshData().getVertices() is not None:
                        if not getattr(node, "_outside_buildarea", False)\
                                or (node.callDecoration("getStack") and any(node.callDecoration("getStack").getProperty(setting, "value") for setting in self._not_printed_mesh_settings)):
                            temp_list.append(node)
                    Job.yieldThread()

                if temp_list:
                    object_groups.append(temp_list)

            # There are cases when there is nothing to slice. This can happen due to one at a time slicing not being
            # able to find a possible sequence or because there are no objects on the build plate (or they are outside
            # the build volume)
            if not object_groups:
                self.setResult(StartJobResult.NothingToSlice)
                return

            self._buildGlobalSettingsMessage(stack)
            self._buildGlobalInheritsStackMessage(stack)

            # Only add extruder stacks if there are multiple extruders
            # Single extruder machines only use the global stack to store setting values
            if stack.getProperty("machine_extruder_count", "value") > 1:
                for extruder_stack in ExtruderManager.getInstance().getMachineExtruders(stack.getId()):
                    self._buildExtruderMessage(extruder_stack)
            else:
                self._buildExtruderMessageFromGlobalStack(stack)

            for group in object_groups:
                group_message = self._slice_message.addRepeatedMessage("object_lists")
                if group[0].getParent().callDecoration("isGroup"):
                    self._handlePerObjectSettings(group[0].getParent(), group_message)
                for object in group:
                    mesh_data = object.getMeshData()
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

                    indices = mesh_data.getIndices()
                    if indices is not None:
                        flat_verts = numpy.take(verts, indices.flatten(), axis=0)
                    else:
                        flat_verts = numpy.array(verts)

                    obj.vertices = flat_verts

                    self._handlePerObjectSettings(object, obj)

                    Job.yieldThread()

        self.setResult(StartJobResult.Finished)

    def cancel(self):
        super().cancel()
        self._is_cancelled = True

    def isCancelled(self):
        return self._is_cancelled

    def _expandGcodeTokens(self, key, value, settings):
        try:
            # any setting can be used as a token
            fmt = GcodeStartEndFormatter()
            return str(fmt.format(value, **settings)).encode("utf-8")
        except:
            Logger.logException("w", "Unable to do token replacement on start/end gcode")
            return str(value).encode("utf-8")

    ##  Create extruder message from stack
    def _buildExtruderMessage(self, stack):
        message = self._slice_message.addRepeatedMessage("extruders")
        message.id = int(stack.getMetaDataEntry("position"))

        material_instance_container = stack.findContainer({"type": "material"})

        settings = {}
        for key in stack.getAllKeys():
            settings[key] = stack.getProperty(key, "value")
            Job.yieldThread()

        settings["print_bed_temperature"] = settings["material_bed_temperature"] #Renamed settings.
        settings["print_temperature"] = settings["material_print_temperature"]
        settings["time"] = time.strftime("%H:%M:%S") #Some extra settings.
        settings["date"] = time.strftime("%d-%m-%Y")
        settings["day"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][int(time.strftime("%w"))]

        for key, value in settings.items():
            # Do not send settings that are not settable_per_extruder.
            if not stack.getProperty(key, "settable_per_extruder"):
                continue
            setting = message.getMessage("settings").addRepeatedMessage("settings")
            setting.name = key
            if key == "material_guid" and material_instance_container:
                # Also send the material GUID. This is a setting in fdmprinter, but we have no interface for it.
                setting.value = str(material_instance_container.getMetaDataEntry("GUID", "")).encode("utf-8")
            elif key == "machine_extruder_start_code" or key == "machine_extruder_end_code":
                setting.value = self._expandGcodeTokens(key, value, settings)
            else:
                setting.value = str(stack.getProperty(key, "value")).encode("utf-8")
            Job.yieldThread()

    ##  Create extruder message from global stack
    def _buildExtruderMessageFromGlobalStack(self, stack):
        message = self._slice_message.addRepeatedMessage("extruders")

        for key in stack.getAllKeys():
            # Do not send settings that are not settable_per_extruder.
            if not stack.getProperty(key, "settable_per_extruder"):
                continue
            setting = message.getMessage("settings").addRepeatedMessage("settings")
            setting.name = key
            setting.value = str(stack.getProperty(key, "value")).encode("utf-8")
            Job.yieldThread()

    ##  Sends all global settings to the engine.
    #
    #   The settings are taken from the global stack. This does not include any
    #   per-extruder settings or per-object settings.
    def _buildGlobalSettingsMessage(self, stack):
        keys = stack.getAllKeys()
        settings = {}
        for key in keys:
            settings[key] = stack.getProperty(key, "value")
            Job.yieldThread()

        start_gcode = settings["machine_start_gcode"]
        #Pre-compute material material_bed_temp_prepend and material_print_temp_prepend
        bed_temperature_settings = {"material_bed_temperature", "material_bed_temperature_layer_0"}
        settings["material_bed_temp_prepend"] = all(("{" + setting + "}" not in start_gcode for setting in bed_temperature_settings))
        print_temperature_settings = {"material_print_temperature", "material_print_temperature_layer_0", "default_material_print_temperature", "material_initial_print_temperature", "material_final_print_temperature", "material_standby_temperature"}
        settings["material_print_temp_prepend"] = all(("{" + setting + "}" not in start_gcode for setting in print_temperature_settings))

        settings["print_bed_temperature"] = settings["material_bed_temperature"]
        settings["print_temperature"] = settings["material_print_temperature"]

        settings["time"] = time.strftime('%H:%M:%S')
        settings["date"] = time.strftime('%d-%m-%Y')
        settings["day"] = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][int(time.strftime('%w'))]

        for key, value in settings.items(): #Add all submessages for each individual setting.
            setting_message = self._slice_message.getMessage("global_settings").addRepeatedMessage("settings")
            setting_message.name = key
            if key == "machine_start_gcode" or key == "machine_end_gcode": #If it's a g-code message, use special formatting.
                setting_message.value = self._expandGcodeTokens(key, value, settings)
            else:
                setting_message.value = str(value).encode("utf-8")
            Job.yieldThread()

    ##  Sends for some settings which extruder they should fallback to if not
    #   set.
    #
    #   This is only set for settings that have the limit_to_extruder
    #   property.
    #
    #   \param stack The global stack with all settings, from which to read the
    #   limit_to_extruder property.
    def _buildGlobalInheritsStackMessage(self, stack):
        for key in stack.getAllKeys():
            extruder = int(round(float(stack.getProperty(key, "limit_to_extruder"))))
            if extruder >= 0: #Set to a specific extruder.
                setting_extruder = self._slice_message.addRepeatedMessage("limit_to_extruder")
                setting_extruder.name = key
                setting_extruder.extruder = extruder
            Job.yieldThread()

    ##  Check if a node has per object settings and ensure that they are set correctly in the message
    #   \param node \type{SceneNode} Node to check.
    #   \param message object_lists message to put the per object settings in
    def _handlePerObjectSettings(self, node, message):
        stack = node.callDecoration("getStack")

        # Check if the node has a stack attached to it and the stack has any settings in the top container.
        if not stack:
            return

        # Check all settings for relations, so we can also calculate the correct values for dependent settings.
        top_of_stack = stack.getTop()  # Cache for efficiency.
        changed_setting_keys = set(top_of_stack.getAllKeys())

        # Add all relations to changed settings as well.
        for key in top_of_stack.getAllKeys():
            instance = top_of_stack.getInstance(key)
            self._addRelations(changed_setting_keys, instance.definition.relations)
            Job.yieldThread()

        # Ensure that the engine is aware what the build extruder is.
        if stack.getProperty("machine_extruder_count", "value") > 1:
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

    ##  Recursive function to put all settings that require each other for value changes in a list
    #   \param relations_set \type{set} Set of keys (strings) of settings that are influenced
    #   \param relations list of relation objects that need to be checked.
    def _addRelations(self, relations_set, relations):
        for relation in filter(lambda r: r.role == "value" or r.role == "limit_to_extruder", relations):
            if relation.type == RelationType.RequiresTarget:
                continue

            relations_set.add(relation.target.key)
            self._addRelations(relations_set, relation.target.relations)
