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

from typing import Dict, List, Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from cura.Machines.QualityGroup import QualityGroup
    from cura.Machines.QualityChangesGroup import QualityChangesGroup
    from UM.Settings.ContainerStack import ContainerStack


class ContainerTree:
    """This class contains a look-up tree for which containers are available at which stages of configuration.
    
    The tree starts at the machine definitions. For every distinct definition there will be one machine node here.
    
    All of the fallbacks for material choices, quality choices, etc. should be encoded in this tree. There must
    always be at least one child node (for nodes that have children) but that child node may be a node representing
    the empty instance container.
    """

    __instance = None  # type: Optional["ContainerTree"]

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = ContainerTree()
        return cls.__instance

    def __init__(self) -> None:
        self.machines = self._MachineNodeMap()  # Mapping from definition ID to machine nodes with lazy loading.
        self.materialsChanged = Signal()  # Emitted when any of the material nodes in the tree got changed.
        cura.CuraApplication.CuraApplication.getInstance().initializationFinished.connect(self._onStartupFinished)  # Start the background task to load more machine nodes after start-up is completed.

    def getCurrentQualityGroups(self) -> Dict[str, "QualityGroup"]:
        """Get the quality groups available for the currently activated printer.
        
        This contains all quality groups, enabled or disabled. To check whether the quality group can be activated,
        test for the ``QualityGroup.is_available`` property.

        :return: For every quality type, one quality group.
        """

        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return {}
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
        return self.machines[global_stack.definition.getId()].getQualityGroups(variant_names, material_bases, extruder_enabled)

    def getCurrentQualityChangesGroups(self) -> List["QualityChangesGroup"]:
        """Get the quality changes groups available for the currently activated printer.
        
        This contains all quality changes groups, enabled or disabled. To check whether the quality changes group can
        be activated, test for the ``QualityChangesGroup.is_available`` property.

        :return: A list of all quality changes groups.
        """

        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return []
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
        return self.machines[global_stack.definition.getId()].getQualityChangesGroups(variant_names, material_bases, extruder_enabled)

    def _onStartupFinished(self) -> None:
        """Ran after completely starting up the application."""

        currently_added = ContainerRegistry.getInstance().findContainerStacks()  # Find all currently added global stacks.
        JobQueue.getInstance().add(self._MachineNodeLoadJob(self, currently_added))

    class _MachineNodeMap:
        """Dictionary-like object that contains the machines.
        
        This handles the lazy loading of MachineNodes.
        """

        def __init__(self) -> None:
            self._machines = {}  # type: Dict[str, MachineNode]

        def __contains__(self, definition_id: str) -> bool:
            """Returns whether a printer with a certain definition ID exists.

            This is regardless of whether or not the printer is loaded yet.

            :param definition_id: The definition to look for.

            :return: Whether or not a printer definition exists with that name.
            """

            return len(ContainerRegistry.getInstance().findContainersMetadata(id = definition_id)) > 0

        def __getitem__(self, definition_id: str) -> MachineNode:
            """Returns a machine node for the specified definition ID.
            
            If the machine node wasn't loaded yet, this will load it lazily.

            :param definition_id: The definition to look for.

            :return: A machine node for that definition.
            """

            if definition_id not in self._machines:
                start_time = time.time()
                self._machines[definition_id] = MachineNode(definition_id)
                self._machines[definition_id].materialsChanged.connect(ContainerTree.getInstance().materialsChanged)
                Logger.log("d", "Adding container tree for {definition_id} took {duration} seconds.".format(definition_id = definition_id, duration = time.time() - start_time))
            return self._machines[definition_id]

        def get(self, definition_id: str, default: Optional[MachineNode] = None) -> Optional[MachineNode]:
            """Gets a machine node for the specified definition ID, with default.
            
            The default is returned if there is no definition with the specified ID. If the machine node wasn't
            loaded yet, this will load it lazily.

            :param definition_id: The definition to look for.
            :param default: The machine node to return if there is no machine with that definition (can be ``None``
            optionally or if not provided).

            :return: A machine node for that definition, or the default if there is no definition with the provided
            definition_id.
            """

            if definition_id not in self:
                return default
            return self[definition_id]

        def is_loaded(self, definition_id: str) -> bool:
            """Returns whether we've already cached this definition's node.
            
            :param definition_id: The definition that we may have cached.

            :return: ``True`` if it's cached.
            """

            return definition_id in self._machines

    class _MachineNodeLoadJob(Job):
        """Pre-loads all currently added printers as a background task so that switching printers in the interface is
        faster.
        """

        def __init__(self, tree_root: "ContainerTree", container_stacks: List["ContainerStack"]) -> None:
            """Creates a new background task.
            
            :param tree_root: The container tree instance. This cannot be obtained through the singleton static
            function since the instance may not yet be constructed completely.
            :param container_stacks: All of the stacks to pre-load the container trees for. This needs to be provided
            from here because the stacks need to be constructed on the main thread because they are QObject.
            """

            self.tree_root = tree_root
            self.container_stacks = container_stacks
            super().__init__()

        def run(self) -> None:
            """Starts the background task.
            
            The ``JobQueue`` will schedule this on a different thread.
            """

            for stack in self.container_stacks:  # Load all currently-added containers.
                if not isinstance(stack, GlobalStack):
                    continue
                # Allow a thread switch after every container.
                # Experimentally, sleep(0) didn't allow switching. sleep(0.1) or sleep(0.2) neither.
                # We're in no hurry though. Half a second is fine.
                time.sleep(0.5)
                definition_id = stack.definition.getId()
                if not self.tree_root.machines.is_loaded(definition_id):
                    _ = self.tree_root.machines[definition_id]
