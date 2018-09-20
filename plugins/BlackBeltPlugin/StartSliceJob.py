# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from string import Formatter
from enum import IntEnum
import time
from typing import Any, cast, Dict, List, Optional, Set
import copy
import math
import re
import Arcus #For typing.

from UM.Job import Job
from UM.Logger import Logger
from UM.Settings.ContainerStack import ContainerStack #For typing.
from UM.Settings.SettingRelation import SettingRelation #For typing.

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Scene import Scene #For typing.
from UM.Settings.Validator import ValidatorState
from UM.Settings.SettingRelation import RelationType
from cura.Settings.CuraContainerStack import CuraContainerStack

from cura.CuraApplication import CuraApplication

from UM.Math.Vector import Vector
from UM.Math.Polygon import Polygon
from UM.Mesh.MeshData import transformVertices
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.SceneNode import SceneNode
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.ConvexHullNode import ConvexHullNode
from cura.OneAtATimeIterator import OneAtATimeIterator
from cura.Settings.ExtruderManager import ExtruderManager
from UM.Settings.ContainerRegistry import ContainerRegistry

from .SupportMeshCreator import SupportMeshCreator

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


##  Formatter class that handles token expansion in start/end gcode
class GcodeStartEndFormatter(Formatter):
    def get_value(self, key: str, args: str, kwargs: dict, default_extruder_nr: str = "-1") -> str: #type: ignore # [CodeStyle: get_value is an overridden function from the Formatter class]
        # The kwargs dictionary contains a dictionary for each stack (with a string of the extruder_nr as their key),
        # and a default_extruder_nr to use when no extruder_nr is specified

        extruder_nr = int(default_extruder_nr)

        key_fragments = [fragment.strip() for fragment in key.split(",")]
        if len(key_fragments) == 2:
            try:
                extruder_nr = int(key_fragments[1])
            except ValueError:
                try:
                    extruder_nr = int(kwargs["-1"][key_fragments[1]]) # get extruder_nr values from the global stack #TODO: How can you ever provide the '-1' kwarg?
                except (KeyError, ValueError):
                    # either the key does not exist, or the value is not an int
                    Logger.log("w", "Unable to determine stack nr '%s' for key '%s' in start/end g-code, using global stack", key_fragments[1], key_fragments[0])
        elif len(key_fragments) != 1:
            Logger.log("w", "Incorrectly formatted placeholder '%s' in start/end g-code", key)
            return "{" + key + "}"

        key = key_fragments[0]
        try:
            return kwargs[str(extruder_nr)][key]
        except KeyError:
            Logger.log("w", "Unable to replace '%s' placeholder in start/end g-code", key)
            return "{" + key + "}"


##  Job class that builds up the message of scene data to send to CuraEngine.
class StartSliceJob(Job):
    def __init__(self, slice_message: Arcus.PythonMessage) -> None:
        super().__init__()

        self._scene = CuraApplication.getInstance().getController().getScene() #type: Scene
        self._slice_message = slice_message #type: Arcus.PythonMessage
        self._is_cancelled = False #type: bool
        self._build_plate_number = None #type: Optional[int]

        self._all_extruders_settings = None #type: Optional[Dict[str, Any]] # cache for all setting values from all stacks (global & extruder) for the current machine

    def getSliceMessage(self) -> Arcus.PythonMessage:
        return self._slice_message

    def setBuildPlate(self, build_plate_number: int) -> None:
        self._build_plate_number = build_plate_number

    ##  Check if a stack has any errors.
    ##  returns true if it has errors, false otherwise.
    def _checkStackForErrors(self, stack: ContainerStack) -> bool:
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
    def run(self) -> None:
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

        # Don't slice if the buildplate or the nozzle type is incompatible with the materials
        if not CuraApplication.getInstance().getMachineManager().variantBuildplateCompatible and \
                not CuraApplication.getInstance().getMachineManager().variantBuildplateUsable:
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
        for node in DepthFirstIterator(self._scene.getRoot()): #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
            if not isinstance(node, CuraSceneNode) or not node.isSelectable():
                continue

            if self._checkStackForErrors(node.callDecoration("getStack")):
                self.setResult(StartJobResult.ObjectSettingError)
                return

        with self._scene.getSceneLock():
            # Remove old layer data.
            for node in DepthFirstIterator(self._scene.getRoot()): #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
                if node.callDecoration("getLayerData") and node.callDecoration("getBuildPlateNumber") == self._build_plate_number:
                    node.getParent().removeChild(node)
                    break

            global_enable_support = stack.getProperty("support_enable", "value")

            # Get the objects in their groups to print.
            object_groups = []
            if stack.getProperty("print_sequence", "value") == "one_at_a_time":
                # note that one_at_a_time printing is disabled on belt printers due to collission risk
                for node in OneAtATimeIterator(self._scene.getRoot()): #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
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

            global_stack = CuraApplication.getInstance().getGlobalContainerStack()
            if not global_stack:
                return
            extruders_enabled = {position: stack.isEnabled for position, stack in global_stack.extruders.items()}
            filtered_object_groups = []
            has_model_with_disabled_extruders = False
            associated_disabled_extruders = set()
            for group in object_groups:
                stack = global_stack
                skip_group = False
                for node in group:
                    # Only check if the printing extruder is enabled for printing meshes
                    is_non_printing_mesh = node.callDecoration("evaluateIsNonPrintingMesh")
                    extruder_position = node.callDecoration("getActiveExtruderPosition")
                    if not is_non_printing_mesh and not extruders_enabled[extruder_position]:
                        skip_group = True
                        has_model_with_disabled_extruders = True
                        associated_disabled_extruders.add(extruder_position)
                if not skip_group:
                    filtered_object_groups.append(group)

            if has_model_with_disabled_extruders:
                self.setResult(StartJobResult.ObjectsWithDisabledExtruder)
                associated_disabled_extruders = {str(c) for c in sorted([int(p) + 1 for p in associated_disabled_extruders])}
                self.setMessage(", ".join(associated_disabled_extruders))
                return

            # There are cases when there is nothing to slice. This can happen due to one at a time slicing not being
            # able to find a possible sequence or because there are no objects on the build plate (or they are outside
            # the build volume)
            if not filtered_object_groups:
                self.setResult(StartJobResult.NothingToSlice)
                return

            container_registry = ContainerRegistry.getInstance()
            stack_id = stack.getId()

            global_blackbelt_support_gantry_angle_bias = 0

            # Adapt layer_height and material_flow for a slanted gantry
            gantry_angle = self._scene.getRoot().callDecoration("getGantryAngle")
            if gantry_angle: # not 0 or None
                global_blackbelt_support_gantry_angle_bias = stack.getProperty("blackbelt_support_gantry_angle_bias", "value")
                if global_blackbelt_support_gantry_angle_bias is None:
                    global_blackbelt_support_gantry_angle_bias = 0

                # Act on a copy of the stack, so these changes don't cause a reslice
                _stack = CuraContainerStack(stack_id + "_temp")
                for index, container in enumerate(stack.getContainers()):
                    if container_registry.isReadOnly(container.getId()):
                        _stack.replaceContainer(index, container)
                    else:
                        _stack.replaceContainer(index, copy.deepcopy(container))
                stack = _stack

                # Make sure CuraEngine does not create any supports
                # support_enable is set in the frontend so support options are settable,
                # but CuraEngine support structures don't work for slanted gantry
                stack.setProperty("support_enable", "value", False)
                # Make sure CuraEngine does not create a raft (we create one manually)
                # Adhesion type is used in the frontend to show the raft in the viewport
                stack.setProperty("adhesion_type", "value", "none")

                for key in ["layer_height", "layer_height_0"]:
                    current_value = stack.getProperty(key, "value")
                    stack.setProperty(key, "value", current_value / math.sin(gantry_angle))

            self._buildGlobalSettingsMessage(stack)
            self._buildGlobalInheritsStackMessage(stack)

            # Build messages for extruder stacks
            for position, extruder_stack in enumerate(ExtruderManager.getInstance().getActiveExtruderStacks()):
                if gantry_angle: # not 0 or None
                    # Act on a copy of the stack, so these changes don't cause a reslice
                    _extruder_stack = CuraContainerStack(extruder_stack.getId() + "_temp")
                    for index, container in enumerate(extruder_stack.getContainers()):
                        if container_registry.isReadOnly(container.getId()):
                            _extruder_stack.replaceContainer(index, container)
                        else:
                            _extruder_stack.replaceContainer(index, copy.deepcopy(container))
                    extruder_stack = _extruder_stack
                    extruder_stack.setNextStack(stack)
                    for key in ["material_flow", "prime_tower_flow", "spaghetti_flow"]:
                        if extruder_stack.hasProperty(key, "value"):
                            current_value = extruder_stack.getProperty(key, "value")
                            extruder_stack.setProperty(key, "value", current_value * math.sin(gantry_angle))
                self._buildExtruderMessage(extruder_stack)

            bottom_cutting_meshes = []
            raft_meshes = []
            support_meshes = []
            if gantry_angle: # not 0 or None
                for group in filtered_object_groups:
                    added_meshes = []
                    for object in group:

                        is_non_printing_mesh = False
                        per_object_stack = object.callDecoration("getStack")

                        # ConvexHullNodes get none of the usual decorators. If it made it here, it is meant to be printed
                        if type(object) is ConvexHullNode:
                            raft_thickness = stack.getProperty("blackbelt_raft_thickness", "value")
                            raft_margin = stack.getProperty("blackbelt_raft_margin", "value")

                            mb = MeshBuilder()
                            hull_polygon = object.getHull()
                            if raft_margin > 0:
                                hull_polygon = hull_polygon.getMinkowskiHull(Polygon.approximatedCircle(raft_margin))
                            mb.addConvexPolygonExtrusion(hull_polygon.getPoints()[::-1], 0, raft_thickness)

                            new_node = self._addMeshFromBuilder(mb, "raftMesh")
                            added_meshes.append(new_node)
                            raft_meshes.append(new_node.getName())

                        elif not is_non_printing_mesh:
                            # add support mesh if needed
                            blackbelt_support_gantry_angle_bias = None
                            if per_object_stack:
                                is_non_printing_mesh = any(per_object_stack.getProperty(key, "value") for key in NON_PRINTING_MESH_SETTINGS)

                                node_enable_support = per_object_stack.getProperty("support_enable", "value")
                                add_support_mesh = node_enable_support if node_enable_support is not None else global_enable_support
                                blackbelt_support_gantry_angle_bias = per_object_stack.getProperty("blackbelt_support_gantry_angle_bias", "value")
                            else:
                                add_support_mesh = global_enable_support

                            if add_support_mesh:
                                if blackbelt_support_gantry_angle_bias is None:
                                    blackbelt_support_gantry_angle_bias = global_blackbelt_support_gantry_angle_bias
                                biased_down_angle = math.radians(blackbelt_support_gantry_angle_bias)
                                support_mesh_data = SupportMeshCreator(
                                    down_vector=numpy.array([0, -math.cos(math.radians(biased_down_angle)), -math.sin(biased_down_angle)]),
                                    bottom_cut_off=stack.getProperty("wall_line_width_0", "value") / 2
                                ).createSupportMeshForNode(object)
                                if support_mesh_data:
                                    new_node = self._addMeshFromData(support_mesh_data, "generatedSupportMesh")
                                    added_meshes.append(new_node)
                                    support_meshes.append(new_node.getName())

                            # check if the bottom needs to be cut off
                            aabb = object.getBoundingBox()

                            if aabb.bottom < 0:
                                # mesh extends below the belt; add a cutting mesh to cut off the part below the bottom
                                height = -aabb.bottom
                                center = Vector(aabb.center.x, -height/2, aabb.center.z)

                                mb = MeshBuilder()
                                mb.addCube(
                                    width = aabb.width,
                                    height = height,
                                    depth = aabb.depth,
                                    center = center
                                )

                                new_node = self._addMeshFromBuilder(mb, "bottomCuttingMesh")
                                added_meshes.append(new_node)
                                bottom_cutting_meshes.append(new_node.getName())

                    if added_meshes:
                        group += added_meshes

            transform_matrix = self._scene.getRoot().callDecoration("getTransformMatrix")
            front_offset = None

            raft_offset = 0
            raft_speed = None
            raft_flow = 1.0

            if stack.getProperty("blackbelt_raft", "value"):
                raft_offset = stack.getProperty("blackbelt_raft_thickness", "value") + stack.getProperty("blackbelt_raft_gap", "value")
                raft_speed = stack.getProperty("blackbelt_raft_speed", "value")
                raft_flow = stack.getProperty("blackbelt_raft_flow", "value") * math.sin(gantry_angle)

            for group in filtered_object_groups:
                group_message = self._slice_message.addRepeatedMessage("object_lists")
                if group[0].getParent() is not None and group[0].getParent().callDecoration("isGroup"):
                    self._handlePerObjectSettings(group[0].getParent(), group_message)
                for object in group:
                    if type(object) is ConvexHullNode:
                        continue

                    mesh_data = object.getMeshData()
                    rot_scale = object.getWorldTransformation().getTransposed().getData()[0:3, 0:3]
                    translate = object.getWorldTransformation().getData()[:3, 3]
                    # offset all non-raft objects if rafts are enabled
                    # air gap is applied here to vertically offset objects from the raft
                    if object.getName() not in raft_meshes:
                        translate[1] = translate[1] + raft_offset

                    # This effectively performs a limited form of MeshData.getTransformed that ignores normals.
                    verts = mesh_data.getVertices()
                    verts = verts.dot(rot_scale)
                    verts += translate

                    if transform_matrix:
                        verts = transformVertices(verts, transform_matrix)

                        is_non_printing_mesh = object.getName() in bottom_cutting_meshes or object.getName() in raft_meshes
                        if not is_non_printing_mesh:
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

                    if object.getName() in raft_meshes:
                        self._addSettingsMessage(obj, {
                            "wall_line_count": 99999999,
                            "speed_wall_0": raft_speed,
                            "speed_wall_x": raft_speed,
                            "material_flow": raft_flow
                        })

                    elif object.getName() in support_meshes:
                        self._addSettingsMessage(obj, {
                            "support_mesh": "True",
                            "support_mesh_drop_down": "False"
                        })

                    elif object.getName() in bottom_cutting_meshes:
                        self._addSettingsMessage(obj, {
                            "cutting_mesh": True,
                            "wall_line_count": 0,
                            "top_layers": 0,
                            "bottom_layers": 0,
                            "infill_line_distance": 0
                        })

                    else:
                        self._handlePerObjectSettings(object, obj)
                        Job.yieldThread()

                # Store the front-most coordinate of the scene so the scene can be moved back into place post slicing
                # TODO: this should be handled per mesh-group instead of per scene
                # One-at-a-time printing should be disabled for slanted gantry printers for now
                self._scene.getRoot().callDecoration("setSceneFrontOffset", front_offset)

        self.setResult(StartJobResult.Finished)

    def _addMeshFromBuilder(self, mesh_builder, base_name = "") -> SceneNode:
        return self._addMeshFromData(mesh_builder.build(), base_name)

    def _addMeshFromData(self, mesh_data, base_name = "") -> SceneNode:
        new_node = SceneNode()
        new_node.setMeshData(mesh_data)
        node_name = base_name + hex(id(new_node))
        new_node.setName(node_name)

        return new_node

    def _addSettingsMessage(self, obj, settings):
        for (key, value) in settings.items():
            setting = obj.addRepeatedMessage("settings")
            setting.name = key
            setting.value = str(value).encode("utf-8")
            Job.yieldThread()

    def cancel(self) -> None:
        super().cancel()
        self._is_cancelled = True

    def isCancelled(self) -> bool:
        return self._is_cancelled

    def setIsCancelled(self, value: bool) -> None:
        self._is_cancelled = value

    ##  Creates a dictionary of tokens to replace in g-code pieces.
    #
    #   This indicates what should be replaced in the start and end g-codes.
    #   \param stack The stack to get the settings from to replace the tokens
    #   with.
    #   \return A dictionary of replacement tokens to the values they should be
    #   replaced with.
    def _buildReplacementTokens(self, stack: ContainerStack) -> Dict[str, Any]:
        result = {}
        for key in stack.getAllKeys():
            value = stack.getProperty(key, "value")
            result[key] = value
            Job.yieldThread()

        result["print_bed_temperature"] = result["material_bed_temperature"] # Renamed settings.
        result["print_temperature"] = result["material_print_temperature"]
        result["time"] = time.strftime("%H:%M:%S") #Some extra settings.
        result["date"] = time.strftime("%d-%m-%Y")
        result["day"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][int(time.strftime("%w"))]

        initial_extruder_stack = CuraApplication.getInstance().getExtruderManager().getUsedExtruderStacks()[0]
        initial_extruder_nr = initial_extruder_stack.getProperty("extruder_nr", "value")
        result["initial_extruder_nr"] = initial_extruder_nr

        return result

    ##  Replace setting tokens in a piece of g-code.
    #   \param value A piece of g-code to replace tokens in.
    #   \param default_extruder_nr Stack nr to use when no stack nr is specified, defaults to the global stack
    def _expandGcodeTokens(self, value: str, default_extruder_nr: int = -1) -> str:
        if not self._all_extruders_settings:
            global_stack = cast(ContainerStack, CuraApplication.getInstance().getGlobalContainerStack())

            # NB: keys must be strings for the string formatter
            self._all_extruders_settings = {
                "-1": self._buildReplacementTokens(global_stack)
            }

            for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
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
    def _buildExtruderMessage(self, stack: ContainerStack) -> None:
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
    def _buildGlobalSettingsMessage(self, stack: ContainerStack) -> None:
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
        initial_extruder_stack = CuraApplication.getInstance().getExtruderManager().getUsedExtruderStacks()[0]
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
    def _buildGlobalInheritsStackMessage(self, stack: ContainerStack) -> None:
        for key in stack.getAllKeys():
            extruder_position = int(round(float(stack.getProperty(key, "limit_to_extruder"))))
            if extruder_position >= 0:  # Set to a specific extruder.
                setting_extruder = self._slice_message.addRepeatedMessage("limit_to_extruder")
                setting_extruder.name = key
                setting_extruder.extruder = extruder_position
            Job.yieldThread()

    ##  Check if a node has per object settings and ensure that they are set correctly in the message
    #   \param node Node to check.
    #   \param message object_lists message to put the per object settings in
    def _handlePerObjectSettings(self, node: CuraSceneNode, message: Arcus.PythonMessage):
        stack = node.callDecoration("getStack")

        # Check if the node has a stack attached to it and the stack has any settings in the top container.
        if not stack:
            return

        # Check all settings for relations, so we can also calculate the correct values for dependent settings.
        top_of_stack = stack.getTop()  # Cache for efficiency.
        changed_setting_keys = top_of_stack.getAllKeys()

        # Remove support_enable for belt-printers
        if self._scene.getRoot().callDecoration("getGantryAngle"):
            try:
                changed_setting_keys.remove("support_enable")
            except KeyError:
                pass

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
    #   \param relations_set Set of keys of settings that are influenced
    #   \param relations list of relation objects that need to be checked.
    def _addRelations(self, relations_set: Set[str], relations: List[SettingRelation]):
        for relation in filter(lambda r: r.role == "value" or r.role == "limit_to_extruder", relations):
            if relation.type == RelationType.RequiresTarget:
                continue

            relations_set.add(relation.target.key)
            self._addRelations(relations_set, relation.target.relations)

