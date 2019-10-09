# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job  # For our background task of loading MachineNodes lazily.
from UM.JobQueue import JobQueue  # For our background task of loading MachineNodes lazily.
from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry  # To listen to containers being added.
from UM.Signal import Signal
import cura.CuraApplication  # Imported like this to prevent circular dependencies.
from cura.Machines.MachineNode import MachineNode
from cura.Settings.GlobalStack import GlobalStack  # To listen only to global stacks being added.

from typing import Dict, List, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from cura.Machines.QualityGroup import QualityGroup
    from cura.Machines.QualityChangesGroup import QualityChangesGroup


##  This class contains a look-up tree for which containers are available at
#   which stages of configuration.
#
#   The tree starts at the machine definitions. For every distinct definition
#   there will be one machine node here.
#
#   All of the fallbacks for material choices, quality choices, etc. should be
#   encoded in this tree. There must always be at least one child node (for
#   nodes that have children) but that child node may be a node representing the
#   empty instance container.
class ContainerTree:
    __instance = None

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = ContainerTree()
        return cls.__instance

    def __init__(self) -> None:
        self.machines = self.MachineNodeMap()  # Mapping from definition ID to machine nodes with lazy loading.
        self.materialsChanged = Signal()  # Emitted when any of the material nodes in the tree got changed.
        cura.CuraApplication.CuraApplication.getInstance().initializationFinished.connect(self._onStartupFinished)  # Start the background task to load more machine nodes after start-up is completed.

    ##  Get the quality groups available for the currently activated printer.
    #
    #   This contains all quality groups, enabled or disabled. To check whether
    #   the quality group can be activated, test for the
    #   ``QualityGroup.is_available`` property.
    #   \return For every quality type, one quality group.
    def getCurrentQualityGroups(self) -> Dict[str, "QualityGroup"]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return {}
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
        return self.machines[global_stack.definition.getId()].getQualityGroups(variant_names, material_bases, extruder_enabled)

    ##  Get the quality changes groups available for the currently activated
    #   printer.
    #
    #   This contains all quality changes groups, enabled or disabled. To check
    #   whether the quality changes group can be activated, test for the
    #   ``QualityChangesGroup.is_available`` property.
    #   \return A list of all quality changes groups.
    def getCurrentQualityChangesGroups(self) -> List["QualityChangesGroup"]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return []
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
        return self.machines[global_stack.definition.getId()].getQualityChangesGroups(variant_names, material_bases, extruder_enabled)

    ##  Builds the initial container tree.
    def _loadAll(self):
        Logger.log("i", "Building container tree.")
        start_time = time.time()
        all_stacks = ContainerRegistry.getInstance().findContainerStacks()
        for stack in all_stacks:
            if not isinstance(stack, GlobalStack):
                continue  # Only want to load global stacks. We don't need to create a tree for extruder definitions.
            _ = self.machines[stack.definition.getId()]  # TODO: Load this lazily.

        Logger.log("d", "Building the container tree took %s seconds",  time.time() - start_time)

    ##  Ran after completely starting up the application.
    def _onStartupFinished(self):
        JobQueue.getInstance().add(self.MachineNodeLoadJob(self))

    ##  For debugging purposes, visualise the entire container tree as it stands
    #   now.
    def _visualise_tree(self) -> str:
        lines = ["% CONTAINER TREE"]  # Start with array and then combine into string, for performance.
        for machine in self.machines.machines.values():
            lines.append("  # " + machine.container_id)
            for variant in machine.variants.values():
                lines.append("    * " + variant.container_id)
                for material in variant.materials.values():
                    lines.append("      + " + material.container_id)
                    for quality in material.qualities.values():
                        lines.append("        - " + quality.container_id)
                        for intent in quality.intents.values():
                            lines.append("          . " + intent.container_id)
        return "\n".join(lines)

    ##  Dictionary-like object that contains the machines.
    #
    #   This handles the lazy loading of MachineNodes.
    class MachineNodeMap:
        def __init__(self):
            self.machines = {}

        ##  Returns whether a printer with a certain definition ID exists. This
        #   is regardless of whether or not the printer is loaded yet.
        #   \param definition_id The definition to look for.
        #   \return Whether or not a printer definition exists with that name.
        def __contains__(self, definition_id: str) -> bool:
            return len(ContainerRegistry.getInstance().findInstanceContainersMetadata(id = definition_id)) == 0

        ##  Returns a machine node for the specified definition ID.
        #
        #   If the machine node wasn't loaded yet, this will load it lazily.
        #   \param definition_id The definition to look for.
        #   \return A machine node for that definition.
        def __getitem__(self, definition_id: str) -> MachineNode:
            if definition_id not in self.machines:
                print("-----------------------------------bluuuh", definition_id)
                start_time = time.time()
                self.machines[definition_id] = MachineNode(definition_id)
                self.machines[definition_id].materialsChanged.connect(ContainerTree.getInstance().materialsChanged)
                Logger.log("d", "Adding container tree for {definition_id} took {duration} seconds.".format(definition_id = definition_id, duration = time.time() - start_time))
            return self.machines[definition_id]

        ##  Returns whether we've already cached this definition's node.
        #   \param definition_id The definition that we may have cached.
        #   \return ``True`` if it's cached.
        def is_loaded(self, definition_id: str) -> bool:
            return definition_id in self.machines

    ##  Pre-loads all currently added printers as a background task so that
    #   switching printers in the interface is faster.
    class MachineNodeLoadJob(Job):
        ##  Creates a new background task.
        #   \param tree_root The container tree instance. This cannot be
        #   obtained through the singleton static function since the instance
        #   may not yet be constructed completely.
        def __init__(self, tree_root: "ContainerTree"):
            self.tree_root = tree_root
            super().__init__()

        ##  Starts the background task.
        #
        #   The ``JobQueue`` will schedule this on a different thread.
        def run(self) -> None:
            currently_added = ContainerRegistry.getInstance().findContainerStacks()  # Find all currently added global stacks.
            for stack in currently_added:
                time.sleep(0.5)
                if not isinstance(stack, GlobalStack):
                    continue
                definition_id = stack.definition.getId()
                if not self.tree_root.machines.is_loaded(definition_id):
                    _ = self.tree_root.machines[definition_id]