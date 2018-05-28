# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from string import Formatter
from enum import IntEnum
import time
import copy
import math
import re

from UM.Job import Job
from UM.Application import Application
from UM.Logger import Logger

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from UM.Settings.Validator import ValidatorState
from UM.Settings.SettingRelation import RelationType
from cura.Settings.CuraContainerStack import CuraContainerStack

from UM.Math.Vector import Vector
from UM.Mesh.MeshData import transformVertices
from UM.Mesh.MeshBuilder import MeshBuilder
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.ConvexHullNode import ConvexHullNode
from cura.OneAtATimeIterator import OneAtATimeIterator
from cura.Settings.ExtruderManager import ExtruderManager
from UM.Settings.ContainerRegistry import ContainerRegistry


NON_PRINTING_MESH_SETTINGS = ["anti_overhang_mesh", "infill_mesh", "cutting_mesh"]


class StartJobResult(IntEnum):
    Finished = 1
    Error = 2
    SettingError = 3
    NothingToSlice = 4
    MaterialIncompatible = 5
    BuildPlateError = 6
    ObjectSettingError = 7 #When an error occurs in per-object settings.


##  Formatter class that handles token expansion in start/end gcod
class GcodeStartEndFormatter(Formatter):
    def get_value(self, key, args, kwargs):  # [CodeStyle: get_value is an overridden function from the Formatter class]
        # The kwargs dictionary contains a dictionary for each stack (with a string of the extruder_nr as their key),
        # and a default_extruder_nr to use when no extruder_nr is specified

        if isinstance(key, str):
            try:
                extruder_nr = kwargs["default_extruder_nr"]
            except ValueError:
                extruder_nr = -1

            key_fragments = [fragment.strip() for fragment in key.split(',')]
            if len(key_fragments) == 2:
                try:
                    extruder_nr = int(key_fragments[1])
                except ValueError:
                    try:
                        extruder_nr = int(kwargs["-1"][key_fragments[1]]) # get extruder_nr values from the global stack
                    except (KeyError, ValueError):
                        # either the key does not exist, or the value is not an int
                        Logger.log("w", "Unable to determine stack nr '%s' for key '%s' in start/end g-code, using global stack", key_fragments[1], key_fragments[0])
            elif len(key_fragments) != 1:
                Logger.log("w", "Incorrectly formatted placeholder '%s' in start/end g-code", key)
                return "{" + str(key) + "}"

            key = key_fragments[0]
            try:
                return kwargs[str(extruder_nr)][key]
            except KeyError:
                Logger.log("w", "Unable to replace '%s' placeholder in start/end g-code", key)
                return "{" + key + "}"
        else:
            Logger.log("w", "Incorrectly formatted placeholder '%s' in start/end g-code", key)
            return "{" + str(key) + "}"


##  Job class that builds up the message of scene data to send to CuraEngine.
class StartSliceJob(Job):
    def __init__(self, slice_message):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._slice_message = slice_message
        self._is_cancelled = False
        self._build_plate_number = None

        self._all_extruders_settings = None # cache for all setting values from all stacks (global & extruder) for the current machine

    def getSliceMessage(self):
        return self._slice_message

    def setBuildPlate(self, build_plate_number):
        self._build_plate_number = build_plate_number

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
        if self._build_plate_number is None:
            self.setResult(StartJobResult.Error)
            return

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

        # Don't slice if the buildplate or the nozzle type is incompatible with the materials
        if not Application.getInstance().getMachineManager().variantBuildplateCompatible and \
                not Application.getInstance().getMachineManager().variantBuildplateUsable:
            self.setResult(StartJobResult.MaterialIncompatible)
            return

        for position, extruder_stack in stack.extruders.items():
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

        with self._scene.getSceneLock():
            # Remove old layer data.
            for node in DepthFirstIterator(self._scene.getRoot()):
                if node.callDecoration("getLayerData") and node.callDecoration("getBuildPlateNumber") == self._build_plate_number:
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

                    # Filter on current build plate
                    build_plate_number = node.callDecoration("getBuildPlateNumber")
                    if build_plate_number is not None and build_plate_number != self._build_plate_number:
                        continue

                    children = node.getAllChildren()
                    children.append(node)
                    for child_node in children:
                        if child_node.getMeshData() and child_node.getMeshData().getVertices() is not None:
                            temp_list.append(child_node)

                    if temp_list:
                        object_groups.append(temp_list)
                    Job.yieldThread()
                if len(object_groups) == 0:
                    Logger.log("w", "No objects suitable for one at a time found, or no correct order found")
            else:
                temp_list = []
                has_printing_mesh = False
                # print convex hull nodes as "faux-raft"
                print_convex_hulls = stack.getProperty("blackbelt_raft", "value")
                for node in DepthFirstIterator(self._scene.getRoot()):
                    slice_node = (print_convex_hulls and type(node) is ConvexHullNode) or node.callDecoration("isSliceable")
                    if slice_node and node.getMeshData() and node.getMeshData().getVertices() is not None:
                        per_object_stack = node.callDecoration("getStack")
                        is_non_printing_mesh = False
                        if per_object_stack:
                            is_non_printing_mesh = any(per_object_stack.getProperty(key, "value") for key in NON_PRINTING_MESH_SETTINGS)

                        # Find a reason not to add the node
                        if node.callDecoration("getBuildPlateNumber") != self._build_plate_number and type(node) is not ConvexHullNode:
                            # NB: ConvexHullNodes get none of the usual decorators, so skip checking for them
                            continue
                        if getattr(node, "_outside_buildarea", False) and not is_non_printing_mesh:
                            continue

                        temp_list.append(node)
                        if not is_non_printing_mesh:
                            has_printing_mesh = True

                    Job.yieldThread()

                #If the list doesn't have any model with suitable settings then clean the list
                # otherwise CuraEngine will crash
                if not has_printing_mesh:
                    temp_list.clear()

                if temp_list:
                    object_groups.append(temp_list)

            extruders_enabled = {position: stack.isEnabled for position, stack in Application.getInstance().getGlobalContainerStack().extruders.items()}
            filtered_object_groups = []
            for group in object_groups:
                stack = Application.getInstance().getGlobalContainerStack()
                skip_group = False
                for node in group:
                    # ConvexHullNodes get none of the usual decorators. If it made it here, it is meant to be printed
                    if type(node) is not ConvexHullNode and not extruders_enabled[node.callDecoration("getActiveExtruderPosition")]:
                        skip_group = True
                        break
                if not skip_group:
                    filtered_object_groups.append(group)

            # There are cases when there is nothing to slice. This can happen due to one at a time slicing not being
            # able to find a possible sequence or because there are no objects on the build plate (or they are outside
            # the build volume)
            if not filtered_object_groups:
                self.setResult(StartJobResult.NothingToSlice)
                return

            container_registry = ContainerRegistry.getInstance()
            stack_id = stack.getId()

            # Adapt layer_height and material_flow for a slanted gantry
            gantry_angle = self._scene.getRoot().callDecoration("getGantryAngle")
            if gantry_angle: # not 0 or None
                # Act on a copy of the stack, so these changes don't cause a reslice
                _stack = CuraContainerStack(stack_id + "_temp")
                index = 0
                for container in stack.getContainers():
                    if container_registry.isReadOnly(container.getId()):
                        _stack.replaceContainer(index, container)
                    else:
                        _stack.replaceContainer(index, copy.deepcopy(container))
                    index = index + 1
                stack = _stack

                # Make sure CuraEngine does not create any supports
                # support_enable is set in the frontend so support options are settable,
                # but CuraEngine support structures don't work for slanted gantry
                stack.setProperty("support_enable", "value", False)
                # Make sure CuraEngine does not create a raft (we create one manually)
                # Adhsion type is used in the frontend to show the raft in the viewport
                stack.setProperty("adhesion_type", "value", "none")

                # HOTFIX: make sure the bed temperature is taken from the extruder stack
                extruder_stack = ExtruderManager.getInstance().getMachineExtruders(stack_id)[0]
                stack.setProperty("material_bed_temperature", "value", extruder_stack.getProperty("material_bed_temperature", "value"))

                for key in ["layer_height", "layer_height_0"]:
                    current_value = stack.getProperty(key, "value")
                    stack.setProperty(key, "value", current_value / math.sin(gantry_angle))
                for key in ["material_flow", "prime_tower_flow", "spaghetti_flow"]:
                    current_value = stack.getProperty(key, "value")
                    stack.setProperty(key, "value", current_value * math.sin(gantry_angle))

            self._buildGlobalSettingsMessage(stack)
            self._buildGlobalInheritsStackMessage(stack)

            # Build messages for extruder stacks
            for extruder_stack in ExtruderManager.getInstance().getMachineExtruders(stack.getId()):
                if gantry_angle: # not 0 or None
                    # Act on a copy of the stack, so these changes don't cause a reslice
                    _extruder_stack = CuraContainerStack(extruder_stack.getId() + "_temp")
                    index = 0
                    for container in extruder_stack.getContainers():
                        if container_registry.isReadOnly(container.getId()):
                            _extruder_stack.replaceContainer(index, container)
                        else:
                            _extruder_stack.replaceContainer(index, copy.deepcopy(container))
                        index = index + 1
                    extruder_stack = _extruder_stack
                    extruder_stack.setNextStack(stack)
                    for key in ["material_flow", "prime_tower_flow", "spaghetti_flow"]:
                        current_value = extruder_stack.getProperty(key, "value")
                        if current_value:
                            extruder_stack.setProperty(key, "value", current_value * math.sin(gantry_angle))
                self._buildExtruderMessage(extruder_stack)

            belt_layer_mesh_data = {}
            if gantry_angle: # not 0 or None
                # Add a modifier mesh to all printable meshes touching the belt
                for group in filtered_object_groups:
                    added_meshes = []
                    for object in group:

                        is_non_printing_mesh = False
                        per_object_stack = object.callDecoration("getStack")
                        if per_object_stack:
                            is_non_printing_mesh = any(per_object_stack.getProperty(key, "value") for key in NON_PRINTING_MESH_SETTINGS)

                        # ConvexHullNodes get none of the usual decorators. If it made it here, it is meant to be printed
                        if not is_non_printing_mesh and not object.getName().startswith("beltLayerModifierMesh") and type(node) is not ConvexHullNode:
                            extruder_stack_index = object.callDecoration("getActiveExtruderPosition")
                            if not extruder_stack_index:
                                extruder_stack_index = 0
                            extruder_stack = ExtruderManager.getInstance().getMachineExtruders(Application.getInstance().getGlobalContainerStack().getId())[int(extruder_stack_index)]

                            belt_wall_enabled = extruder_stack.getProperty("blackbelt_belt_wall_enabled", "value")
                            belt_wall_speed = extruder_stack.getProperty("blackbelt_belt_wall_speed", "value")
                            belt_wall_flow = extruder_stack.getProperty("blackbelt_belt_wall_flow", "value")
                            wall_line_width = extruder_stack.getProperty("wall_line_width_0", "value")

                            if per_object_stack:
                                belt_wall_enabled = per_object_stack.getProperty("blackbelt_belt_wall_enabled", "value")
                                belt_wall_speed = per_object_stack.getProperty("blackbelt_belt_wall_speed", "value")
                                belt_wall_flow = per_object_stack.getProperty("blackbelt_belt_wall_flow", "value")
                                wall_line_width = per_object_stack.getProperty("wall_line_width_0", "value")

                            if not belt_wall_enabled:
                                continue

                            aabb = object.getBoundingBox()
                            if aabb.bottom <= 0:
                                height = wall_line_width * math.sin(gantry_angle)
                                center = Vector(aabb.center.x, height/2, aabb.center.z)

                                mb = MeshBuilder()

                                mb.addCube(
                                    width = aabb.width,
                                    height = height,
                                    depth = aabb.depth,
                                    center = center
                                )

                                new_node = CuraSceneNode(parent = self._scene.getRoot())
                                new_node.setMeshData(mb.build())
                                node_name = "beltLayerModifierMesh" + hex(id(new_node))
                                new_node.setName(node_name)
                                belt_layer_mesh_data[node_name] = {
                                    "blackbelt_belt_wall_speed": belt_wall_speed,
                                    "blackbelt_belt_wall_flow" : belt_wall_flow * math.sin(gantry_angle)
                                }

                                # Note: adding a SettingOverrideDecorator here causes a slicing loop
                                added_meshes.append(new_node)
                    if added_meshes:
                        group += added_meshes

            transform_matrix = self._scene.getRoot().callDecoration("getTransformMatrix")
            front_offset = None

            raft_thickness = 0
            raft_gap = 0
            hull_scale = 1.0
            raft_speed = None
            raft_flow = 1.0

            if stack.getProperty("blackbelt_raft", "value"):
                raft_thickness = stack.getProperty("blackbelt_raft_thickness", "value")
                raft_gap = stack.getProperty("blackbelt_raft_gap", "value")
                hull_scale = raft_thickness / (raft_thickness + raft_gap)
                raft_speed = stack.getProperty("blackbelt_raft_speed", "value")
                if gantry_angle:
                    raft_flow = stack.getProperty("blackbelt_raft_flow", "value") * math.sin(gantry_angle)

            for group in filtered_object_groups:
                group_message = self._slice_message.addRepeatedMessage("object_lists")
                if group[0].getParent() is not None and group[0].getParent().callDecoration("isGroup"):
                    self._handlePerObjectSettings(group[0].getParent(), group_message)
                for object in group:
                    mesh_data = object.getMeshData()
                    rot_scale = object.getWorldTransformation().getTransposed().getData()[0:3, 0:3]
                    translate = object.getWorldTransformation().getData()[:3, 3]
                    # offset all objects if rafts are enabled, or they end up under the belt
                    # air gap is applied here to vertically offset objects from the raft
                    translate[1] = translate[1] + raft_thickness
                    if type(object) is not ConvexHullNode:
                        translate[1] = translate[1] + raft_gap - (raft_gap / 2)

                    # This effectively performs a limited form of MeshData.getTransformed that ignores normals.
                    verts = mesh_data.getVertices()
                    if type(object) is ConvexHullNode:
                        verts = verts * numpy.array([1, hull_scale, 1], numpy.float32)
                    verts = verts.dot(rot_scale)
                    verts += translate

                    if transform_matrix:
                        verts = transformVertices(verts, transform_matrix)

                        is_non_printing_mesh = object.getName() in belt_layer_mesh_data
                        per_object_stack = object.callDecoration("getStack")
                        if per_object_stack:
                            is_non_printing_mesh = any(per_object_stack.getProperty(key, "value") for key in NON_PRINTING_MESH_SETTINGS)

                        if not is_non_printing_mesh:
                            _front_offset = verts[:, 1].min()
                            if front_offset is None or _front_offset < front_offset:
                                front_offset = _front_offset

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

                    if type(object) is ConvexHullNode:
                        for (key, value) in {
                            "wall_line_count": 99999999,
                            "speed_wall_0": raft_speed,
                            "speed_wall_x": raft_speed,
                            "material_flow": raft_flow
                        }.items():
                            setting = obj.addRepeatedMessage("settings")
                            setting.name = key
                            setting.value = str(value).encode("utf-8")

                    if object.getName() in belt_layer_mesh_data:
                        data = belt_layer_mesh_data[object.getName()]
                        for (key, value) in {
                            "cutting_mesh": "True",
                            "wall_line_count": 1,
                            "magic_mesh_surface_mode": "normal",
                            "speed_wall_0": data["blackbelt_belt_wall_speed"],
                            "speed_wall_x": data["blackbelt_belt_wall_speed"],
                            "material_flow": data["blackbelt_belt_wall_flow"]
                        }.items():
                            setting = obj.addRepeatedMessage("settings")
                            setting.name = key
                            setting.value = str(value).encode("utf-8")

                    self._handlePerObjectSettings(object, obj)

                    Job.yieldThread()

                # Store the front-most coordinate of the scene so the scene can be moved back into place post slicing
                # TODO: this should be handled per mesh-group instead of per scene
                # One-at-a-time printing should be disabled for slanted gantry printers for now
                self._scene.getRoot().callDecoration("setSceneFrontOffset", front_offset)

        self.setResult(StartJobResult.Finished)

    def cancel(self):
        super().cancel()
        self._is_cancelled = True

    def isCancelled(self):
        return self._is_cancelled

    ##  Creates a dictionary of tokens to replace in g-code pieces.
    #
    #   This indicates what should be replaced in the start and end g-codes.
    #   \param stack The stack to get the settings from to replace the tokens
    #   with.
    #   \return A dictionary of replacement tokens to the values they should be
    #   replaced with.
    def _buildReplacementTokens(self, stack) -> dict:
        default_extruder_position = int(Application.getInstance().getMachineManager().defaultExtruderPosition)
        result = {}
        for key in stack.getAllKeys():
            setting_type = stack.definition.getProperty(key, "type")
            value = stack.getProperty(key, "value")
            if setting_type == "extruder" and value == -1:
                # replace with the default value
                value = default_extruder_position
            result[key] = value
            Job.yieldThread()

        result["print_bed_temperature"] = result["material_bed_temperature"] # Renamed settings.
        result["print_temperature"] = result["material_print_temperature"]
        result["time"] = time.strftime("%H:%M:%S") #Some extra settings.
        result["date"] = time.strftime("%d-%m-%Y")
        result["day"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][int(time.strftime("%w"))]

        initial_extruder_stack = Application.getInstance().getExtruderManager().getUsedExtruderStacks()[0]
        initial_extruder_nr = initial_extruder_stack.getProperty("extruder_nr", "value")
        result["initial_extruder_nr"] = initial_extruder_nr

        return result

    ##  Replace setting tokens in a piece of g-code.
    #   \param value A piece of g-code to replace tokens in.
    #   \param default_extruder_nr Stack nr to use when no stack nr is specified, defaults to the global stack
    def _expandGcodeTokens(self, value: str, default_extruder_nr: int = -1):
        if not self._all_extruders_settings:
            global_stack = Application.getInstance().getGlobalContainerStack()

            # NB: keys must be strings for the string formatter
            self._all_extruders_settings = {
                "-1": self._buildReplacementTokens(global_stack)
            }

            for extruder_stack in ExtruderManager.getInstance().getMachineExtruders(global_stack.getId()):
                extruder_nr = extruder_stack.getProperty("extruder_nr", "value")
                self._all_extruders_settings[str(extruder_nr)] = self._buildReplacementTokens(extruder_stack)

        try:
            # any setting can be used as a token
            fmt = GcodeStartEndFormatter()
            settings = self._all_extruders_settings.copy()
            settings["default_extruder_nr"] = default_extruder_nr
            return str(fmt.format(value, **settings))
        except:
            Logger.logException("w", "Unable to do token replacement on start/end g-code")
            return str(value)

    ##  Create extruder message from stack
    def _buildExtruderMessage(self, stack):
        message = self._slice_message.addRepeatedMessage("extruders")
        message.id = int(stack.getMetaDataEntry("position"))

        settings = self._buildReplacementTokens(stack)

        # Also send the material GUID. This is a setting in fdmprinter, but we have no interface for it.
        settings["material_guid"] = stack.material.getMetaDataEntry("GUID", "")

        # Replace the setting tokens in start and end g-code.
        extruder_nr = stack.getProperty("extruder_nr", "value")
        settings["machine_extruder_start_code"] = self._expandGcodeTokens(settings["machine_extruder_start_code"], extruder_nr)
        settings["machine_extruder_end_code"] = self._expandGcodeTokens(settings["machine_extruder_end_code"], extruder_nr)

        for key, value in settings.items():
            # Do not send settings that are not settable_per_extruder.
            if not stack.getProperty(key, "settable_per_extruder"):
                continue
            setting = message.getMessage("settings").addRepeatedMessage("settings")
            setting.name = key
            setting.value = str(value).encode("utf-8")
            Job.yieldThread()

    ##  Sends all global settings to the engine.
    #
    #   The settings are taken from the global stack. This does not include any
    #   per-extruder settings or per-object settings.
    def _buildGlobalSettingsMessage(self, stack):
        settings = self._buildReplacementTokens(stack)

        # Pre-compute material material_bed_temp_prepend and material_print_temp_prepend
        start_gcode = settings["machine_start_gcode"]
        bed_temperature_settings = ["material_bed_temperature", "material_bed_temperature_layer_0"]
        pattern = r"\{(%s)(,\s?\w+)?\}" % "|".join(bed_temperature_settings) # match {setting} as well as {setting, extruder_nr}
        settings["material_bed_temp_prepend"] = re.search(pattern, start_gcode) == None
        print_temperature_settings = ["material_print_temperature", "material_print_temperature_layer_0", "default_material_print_temperature", "material_initial_print_temperature", "material_final_print_temperature", "material_standby_temperature"]
        pattern = r"\{(%s)(,\s?\w+)?\}" % "|".join(print_temperature_settings) # match {setting} as well as {setting, extruder_nr}
        settings["material_print_temp_prepend"] = re.search(pattern, start_gcode) == None

        # Replace the setting tokens in start and end g-code.
        # Use values from the first used extruder by default so we get the expected temperatures
        initial_extruder_stack = Application.getInstance().getExtruderManager().getUsedExtruderStacks()[0]
        initial_extruder_nr = initial_extruder_stack.getProperty("extruder_nr", "value")

        settings["machine_start_gcode"] = self._expandGcodeTokens(settings["machine_start_gcode"], initial_extruder_nr)
        settings["machine_end_gcode"] = self._expandGcodeTokens(settings["machine_end_gcode"], initial_extruder_nr)

        # Add all sub-messages for each individual setting.
        for key, value in settings.items():
            setting_message = self._slice_message.getMessage("global_settings").addRepeatedMessage("settings")
            setting_message.name = key
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
            extruder_position = int(round(float(stack.getProperty(key, "limit_to_extruder"))))
            if extruder_position >= 0:  # Set to a specific extruder.
                setting_extruder = self._slice_message.addRepeatedMessage("limit_to_extruder")
                setting_extruder.name = key
                setting_extruder.extruder = extruder_position
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

