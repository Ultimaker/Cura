# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant  # For communicating data and events to Qt.
from UM.FlameProfiler import pyqtSlot

import cura.CuraApplication # To get the global container stack to find the current machine.
from cura.Settings.GlobalStack import GlobalStack
from UM.Logger import Logger
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Settings.ContainerRegistry import ContainerRegistry  # Finding containers by ID.
from UM.Settings.ContainerStack import ContainerStack

from typing import Any, cast, Dict, List, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from cura.Settings.ExtruderStack import ExtruderStack


##  Manages all existing extruder stacks.
#
#   This keeps a list of extruder stacks for each machine.
class ExtruderManager(QObject):

    ##  Registers listeners and such to listen to changes to the extruders.
    def __init__(self, parent = None):
        if ExtruderManager.__instance is not None:
            raise RuntimeError("Try to create singleton '%s' more than once" % self.__class__.__name__)
        ExtruderManager.__instance = self

        super().__init__(parent)

        self._application = cura.CuraApplication.CuraApplication.getInstance()

        # Per machine, a dictionary of extruder container stack IDs. Only for separately defined extruders.
        self._extruder_trains = {}  # type: Dict[str, Dict[str, "ExtruderStack"]]
        self._active_extruder_index = -1  # Indicates the index of the active extruder stack. -1 means no active extruder stack

        # TODO; I have no idea why this is a union of ID's and extruder stacks. This needs to be fixed at some point.
        self._selected_object_extruders = []  # type: List[Union[str, "ExtruderStack"]]

        self._addCurrentMachineExtruders()

        Selection.selectionChanged.connect(self.resetSelectedObjectExtruders)

    ##  Signal to notify other components when the list of extruders for a machine definition changes.
    extrudersChanged = pyqtSignal(QVariant)

    ##  Notify when the user switches the currently active extruder.
    activeExtruderChanged = pyqtSignal()

    ##  Gets the unique identifier of the currently active extruder stack.
    #
    #   The currently active extruder stack is the stack that is currently being
    #   edited.
    #
    #   \return The unique ID of the currently active extruder stack.
    @pyqtProperty(str, notify = activeExtruderChanged)
    def activeExtruderStackId(self) -> Optional[str]:
        if not self._application.getGlobalContainerStack():
            return None  # No active machine, so no active extruder.
        try:
            return self._extruder_trains[self._application.getGlobalContainerStack().getId()][str(self.activeExtruderIndex)].getId()
        except KeyError:  # Extruder index could be -1 if the global tab is selected, or the entry doesn't exist if the machine definition is wrong.
            return None

    ##  Gets a dict with the extruder stack ids with the extruder number as the key.
    @pyqtProperty("QVariantMap", notify = extrudersChanged)
    def extruderIds(self) -> Dict[str, str]:
        extruder_stack_ids = {}  # type: Dict[str, str]

        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            extruder_stack_ids = {position: extruder.id for position, extruder in global_container_stack.extruders.items()}

        return extruder_stack_ids

    ##  Changes the active extruder by index.
    #
    #   \param index The index of the new active extruder.
    @pyqtSlot(int)
    def setActiveExtruderIndex(self, index: int) -> None:
        if self._active_extruder_index != index:
            self._active_extruder_index = index
            self.activeExtruderChanged.emit()

    @pyqtProperty(int, notify = activeExtruderChanged)
    def activeExtruderIndex(self) -> int:
        return self._active_extruder_index

    ##  Gets the extruder name of an extruder of the currently active machine.
    #
    #   \param index The index of the extruder whose name to get.
    @pyqtSlot(int, result = str)
    def getExtruderName(self, index: int) -> str:
        try:
            return self.getActiveExtruderStacks()[index].getName()
        except IndexError:
            return ""

    ## Emitted whenever the selectedObjectExtruders property changes.
    selectedObjectExtrudersChanged = pyqtSignal()

    ##  Provides a list of extruder IDs used by the current selected objects.
    @pyqtProperty("QVariantList", notify = selectedObjectExtrudersChanged)
    def selectedObjectExtruders(self) -> List[Union[str, "ExtruderStack"]]:
        if not self._selected_object_extruders:
            object_extruders = set()

            # First, build a list of the actual selected objects (including children of groups, excluding group nodes)
            selected_nodes = []  # type: List["SceneNode"]
            for node in Selection.getAllSelectedObjects():
                if node.callDecoration("isGroup"):
                    for grouped_node in BreadthFirstIterator(node): #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
                        if grouped_node.callDecoration("isGroup"):
                            continue

                        selected_nodes.append(grouped_node)
                else:
                    selected_nodes.append(node)

            # Then, figure out which nodes are used by those selected nodes.
            current_extruder_trains = self.getActiveExtruderStacks()
            for node in selected_nodes:
                extruder = node.callDecoration("getActiveExtruder")
                if extruder:
                    object_extruders.add(extruder)
                elif current_extruder_trains:
                    object_extruders.add(current_extruder_trains[0].getId())

            self._selected_object_extruders = list(object_extruders)  # type: List[Union[str, "ExtruderStack"]]

        return self._selected_object_extruders

    ##  Reset the internal list used for the selectedObjectExtruders property
    #
    #   This will trigger a recalculation of the extruders used for the
    #   selection.
    def resetSelectedObjectExtruders(self) -> None:
        self._selected_object_extruders = []  # type: List[Union[str, "ExtruderStack"]]
        self.selectedObjectExtrudersChanged.emit()

    @pyqtSlot(result = QObject)
    def getActiveExtruderStack(self) -> Optional["ExtruderStack"]:
        return self.getExtruderStack(self.activeExtruderIndex)

    ##  Get an extruder stack by index
    def getExtruderStack(self, index) -> Optional["ExtruderStack"]:
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            if global_container_stack.getId() in self._extruder_trains:
                if str(index) in self._extruder_trains[global_container_stack.getId()]:
                    return self._extruder_trains[global_container_stack.getId()][str(index)]
        return None

    def registerExtruder(self, extruder_train: "ExtruderStack", machine_id: str) -> None:
        changed = False

        if machine_id not in self._extruder_trains:
            self._extruder_trains[machine_id] = {}
            changed = True

        # do not register if an extruder has already been registered at the position on this machine
        if any(item.getId() == extruder_train.getId() for item in self._extruder_trains[machine_id].values()):
            Logger.log("w", "Extruder [%s] has already been registered on machine [%s], not doing anything",
                       extruder_train.getId(), machine_id)
            return

        if extruder_train:
            self._extruder_trains[machine_id][extruder_train.getMetaDataEntry("position")] = extruder_train
            changed = True
        if changed:
            self.extrudersChanged.emit(machine_id)

    ##  Gets a property of a setting for all extruders.
    #
    #   \param setting_key  \type{str} The setting to get the property of.
    #   \param property  \type{str} The property to get.
    #   \return \type{List} the list of results
    def getAllExtruderSettings(self, setting_key: str, prop: str) -> List:
        result = []

        for extruder_stack in self.getActiveExtruderStacks():
            result.append(extruder_stack.getProperty(setting_key, prop))

        return result

    def extruderValueWithDefault(self, value: str) -> str:
        machine_manager = self._application.getMachineManager()
        if value == "-1":
            return machine_manager.defaultExtruderPosition
        else:
            return value

    ##  Gets the extruder stacks that are actually being used at the moment.
    #
    #   An extruder stack is being used if it is the extruder to print any mesh
    #   with, or if it is the support infill extruder, the support interface
    #   extruder, or the bed adhesion extruder.
    #
    #   If there are no extruders, this returns the global stack as a singleton
    #   list.
    #
    #   \return A list of extruder stacks.
    def getUsedExtruderStacks(self) -> List["ContainerStack"]:
        global_stack = self._application.getGlobalContainerStack()
        container_registry = ContainerRegistry.getInstance()

        used_extruder_stack_ids = set()

        # Get the extruders of all meshes in the scene
        support_enabled = False
        support_bottom_enabled = False
        support_roof_enabled = False

        scene_root = self._application.getController().getScene().getRoot()

        # If no extruders are registered in the extruder manager yet, return an empty array
        if len(self.extruderIds) == 0:
            return []

        # Get the extruders of all printable meshes in the scene
        meshes = [node for node in DepthFirstIterator(scene_root) if isinstance(node, SceneNode) and node.isSelectable()] #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
        for mesh in meshes:
            extruder_stack_id = mesh.callDecoration("getActiveExtruder")
            if not extruder_stack_id:
                # No per-object settings for this node
                extruder_stack_id = self.extruderIds["0"]
            used_extruder_stack_ids.add(extruder_stack_id)

            # Get whether any of them use support.
            stack_to_use = mesh.callDecoration("getStack")  # if there is a per-mesh stack, we use it
            if not stack_to_use:
                # if there is no per-mesh stack, we use the build extruder for this mesh
                stack_to_use = container_registry.findContainerStacks(id = extruder_stack_id)[0]

            support_enabled |= stack_to_use.getProperty("support_enable", "value")
            support_bottom_enabled |= stack_to_use.getProperty("support_bottom_enable", "value")
            support_roof_enabled |= stack_to_use.getProperty("support_roof_enable", "value")

            # Check limit to extruders
            limit_to_extruder_feature_list = ["wall_0_extruder_nr",
                                              "wall_x_extruder_nr",
                                              "roofing_extruder_nr",
                                              "top_bottom_extruder_nr",
                                              "infill_extruder_nr",
                                              ]
            for extruder_nr_feature_name in limit_to_extruder_feature_list:
                extruder_nr = int(global_stack.getProperty(extruder_nr_feature_name, "value"))
                if extruder_nr == -1:
                    continue
                used_extruder_stack_ids.add(self.extruderIds[str(extruder_nr)])

        # Check support extruders
        if support_enabled:
            used_extruder_stack_ids.add(self.extruderIds[self.extruderValueWithDefault(str(global_stack.getProperty("support_infill_extruder_nr", "value")))])
            used_extruder_stack_ids.add(self.extruderIds[self.extruderValueWithDefault(str(global_stack.getProperty("support_extruder_nr_layer_0", "value")))])
            if support_bottom_enabled:
                used_extruder_stack_ids.add(self.extruderIds[self.extruderValueWithDefault(str(global_stack.getProperty("support_bottom_extruder_nr", "value")))])
            if support_roof_enabled:
                used_extruder_stack_ids.add(self.extruderIds[self.extruderValueWithDefault(str(global_stack.getProperty("support_roof_extruder_nr", "value")))])

        # The platform adhesion extruder. Not used if using none.
        if global_stack.getProperty("adhesion_type", "value") != "none" or (
                global_stack.getProperty("prime_tower_brim_enable", "value") and
                global_stack.getProperty("adhesion_type", "value") != 'raft'):
            extruder_str_nr = str(global_stack.getProperty("adhesion_extruder_nr", "value"))
            if extruder_str_nr == "-1":
                extruder_str_nr = self._application.getMachineManager().defaultExtruderPosition
            used_extruder_stack_ids.add(self.extruderIds[extruder_str_nr])

        try:
            return [container_registry.findContainerStacks(id = stack_id)[0] for stack_id in used_extruder_stack_ids]
        except IndexError:  # One or more of the extruders was not found.
            Logger.log("e", "Unable to find one or more of the extruders in %s", used_extruder_stack_ids)
            return []

    ##  Removes the container stack and user profile for the extruders for a specific machine.
    #
    #   \param machine_id The machine to remove the extruders for.
    def removeMachineExtruders(self, machine_id: str) -> None:
        for extruder in self.getMachineExtruders(machine_id):
            ContainerRegistry.getInstance().removeContainer(extruder.userChanges.getId())
            ContainerRegistry.getInstance().removeContainer(extruder.getId())
        if machine_id in self._extruder_trains:
            del self._extruder_trains[machine_id]

    ##  Returns extruders for a specific machine.
    #
    #   \param machine_id The machine to get the extruders of.
    def getMachineExtruders(self, machine_id: str) -> List["ExtruderStack"]:
        if machine_id not in self._extruder_trains:
            return []
        return [self._extruder_trains[machine_id][name] for name in self._extruder_trains[machine_id]]

    ##  Returns the list of active extruder stacks, taking into account the machine extruder count.
    #
    #   \return \type{List[ContainerStack]} a list of
    def getActiveExtruderStacks(self) -> List["ExtruderStack"]:
        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return []
        return global_stack.extruderList

    def _globalContainerStackChanged(self) -> None:
        # If the global container changed, the machine changed and might have extruders that were not registered yet
        self._addCurrentMachineExtruders()

        self.resetSelectedObjectExtruders()

    ##  Adds the extruders of the currently active machine.
    def _addCurrentMachineExtruders(self) -> None:
        global_stack = self._application.getGlobalContainerStack()
        extruders_changed = False

        if global_stack:
            container_registry = ContainerRegistry.getInstance()
            global_stack_id = global_stack.getId()

            # Gets the extruder trains that we just created as well as any that still existed.
            extruder_trains = container_registry.findContainerStacks(type = "extruder_train", machine = global_stack_id)

            # Make sure the extruder trains for the new machine can be placed in the set of sets
            if global_stack_id not in self._extruder_trains:
                self._extruder_trains[global_stack_id] = {}
                extruders_changed = True

            # Register the extruder trains by position
            for extruder_train in extruder_trains:
                extruder_position = extruder_train.getMetaDataEntry("position")
                self._extruder_trains[global_stack_id][extruder_position] = extruder_train

                # regardless of what the next stack is, we have to set it again, because of signal routing. ???
                extruder_train.setParent(global_stack)
                extruder_train.setNextStack(global_stack)
                extruders_changed = True

            self.fixSingleExtrusionMachineExtruderDefinition(global_stack)
            if extruders_changed:
                self.extrudersChanged.emit(global_stack_id)
                self.setActiveExtruderIndex(0)
                self.activeExtruderChanged.emit()

    # After 3.4, all single-extrusion machines have their own extruder definition files instead of reusing
    # "fdmextruder". We need to check a machine here so its extruder definition is correct according to this.
    def fixSingleExtrusionMachineExtruderDefinition(self, global_stack: "GlobalStack") -> None:
        container_registry = ContainerRegistry.getInstance()
        expected_extruder_definition_0_id = global_stack.getMetaDataEntry("machine_extruder_trains")["0"]
        extruder_stack_0 = global_stack.extruders.get("0")
        # At this point, extruder stacks for this machine may not have been loaded yet. In this case, need to look in
        # the container registry as well.
        if not global_stack.extruders:
            extruder_trains = container_registry.findContainerStacks(type = "extruder_train",
                                                                     machine = global_stack.getId())
            if extruder_trains:
                for extruder in extruder_trains:
                    if extruder.getMetaDataEntry("position") == "0":
                        extruder_stack_0 = extruder
                        break

        if extruder_stack_0 is None:
            Logger.log("i", "No extruder stack for global stack [%s], create one", global_stack.getId())
            # Single extrusion machine without an ExtruderStack, create it
            from cura.Settings.CuraStackBuilder import CuraStackBuilder
            CuraStackBuilder.createExtruderStackWithDefaultSetup(global_stack, 0)

        elif extruder_stack_0.definition.getId() != expected_extruder_definition_0_id:
            Logger.log("e", "Single extruder printer [{printer}] expected extruder [{expected}], but got [{got}]. I'm making it [{expected}].".format(
                printer = global_stack.getId(), expected = expected_extruder_definition_0_id, got = extruder_stack_0.definition.getId()))
            extruder_definition = container_registry.findDefinitionContainers(id = expected_extruder_definition_0_id)[0]
            extruder_stack_0.definition = extruder_definition

    ##  Get all extruder values for a certain setting.
    #
    #   This is exposed to qml for display purposes
    #
    #   \param key The key of the setting to retrieve values for.
    #
    #   \return String representing the extruder values
    @pyqtSlot(str, result="QVariant")
    def getInstanceExtruderValues(self, key: str) -> List:
        return self._application.getCuraFormulaFunctions().getValuesInAllExtruders(key)

    ##  Get the resolve value or value for a given key
    #
    #   This is the effective value for a given key, it is used for values in the global stack.
    #   This is exposed to SettingFunction to use in value functions.
    #   \param key The key of the setting to get the value of.
    #
    #   \return The effective value
    @staticmethod
    def getResolveOrValue(key: str) -> Any:
        global_stack = cast(GlobalStack, cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack())
        resolved_value = global_stack.getProperty(key, "value")

        return resolved_value

    __instance = None   # type: ExtruderManager

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "ExtruderManager":
        return cls.__instance
