from typing import Optional

from PyQt5.Qt import pyqtSignal, QObject

from UM.Application import Application
from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Util import parseBool

from cura.Machines.ContainerGroup import ContainerGroup
from cura.Machines.ContainerNode import ContainerNode


#
# Quality lookup tree structure:
#
#      <machine_definition_id>------|
#                |                  |
#          <variant_name>        <root_material_id>
#                |
#        <root_material_id>
#                |
#          <quality_type>
#                |
#            <quality_name>
#       + <quality_changes_name>
#


class QualityChangesGroup:
    __slots__ = ("name", "qc_for_global", "qc_for_extruders_dict")

    def __init__(self, name: str):
        self.name = name  # type: str
        self.qc_for_global = None  # type: Optional["QualityNode"]
        self.qc_for_extruders_dict = dict()  # <extruder_id> -> QualityNode

    def addMetadata(self, metadata: dict):
        extruder_id = metadata.get("extruder")
        if extruder_id is not None:
            self.qc_for_extruders_dict[extruder_id] = QualityNode(metadata)
        else:
            self.qc_for_global = QualityNode(metadata)

    def getContainerForGlobalStack(self) -> "InstanceContainer":
        return self.qc_for_global.getContainer()

    def getContainerForExtruderStack(self, extruder_definition_id: str) -> Optional["InstanceContainer"]:
        qc_node = self.qc_for_extruders_dict.get(extruder_definition_id)
        container = None
        if qc_node is not None:
            container = qc_node.getContainer()
        return container


class QualityGroup(ContainerGroup):

    def __init__(self, name: str, quality_type: str, parent = None):
        super().__init__(name, parent)
        self.quality_type = quality_type
        self.is_available = False


class QualityNode(ContainerNode):
    __slots__ = ("metadata", "container", "quality_type_map", "children_map")

    def __init__(self, metadata = None):
        super().__init__(metadata = metadata)
        self.quality_type_map = {}


    def addQualityMetadata(self, quality_type: str, metadata: dict):
        if quality_type not in self.quality_type_map:
            self.quality_type_map[quality_type] = QualityNode(metadata)

    def getQualityNode(self, quality_type: str):
        return self.quality_type_map.get(quality_type)

    def addQualityChangesMetadata(self, quality_type: str, metadata: dict):
        if quality_type not in self.quality_type_map:
            self.quality_type_map[quality_type] = QualityNode()
        quality_type_node = self.quality_type_map[quality_type]

        name = metadata["name"]
        if name not in quality_type_node.children_map:
            quality_type_node.children_map[name] = QualityChangesGroup(name)
        qc_group = quality_type_node.children_map[name]
        qc_group.addMetadata(metadata)


class QualityManager(QObject):

    def __init__(self, container_registry, parent = None):
        super().__init__(parent)

        self._material_manager = Application.getInstance()._material_manager

        self._container_registry = container_registry
        self._empty_quality_container = self._container_registry.findInstanceContainers(id = "empty_quality")[0]
        #self._empty_quality_changes_container = self._container_registry.findInstanceContainers(id = "empty_quality_changes")[0]

        self._machine_variant_material_quality_type_to_quality_dict = {}  # for quality lookup
        self._machine_quality_type_to_quality_changes_dict = {}  # for quality_changes lookup

        self._default_machine_definition_id = "fdmprinter"

    def initialize(self):
        # Initialize the lookup tree for quality profiles with following structure:
        # <machine> -> <variant> -> <material>
        #           -> <material>
        quality_metadata_list = self._container_registry.findContainersMetadata(type = "quality")
        for metadata in quality_metadata_list:
            if metadata["id"] == "empty_quality":
                continue

            definition_id = metadata["definition"]
            quality_type = metadata["quality_type"]

            root_material_id = metadata.get("material")
            variant_name = metadata.get("variant")
            is_global_quality = metadata.get("global_quality", False)
            is_global_quality = is_global_quality or (root_material_id is None and variant_name is None)

            # Sanity check: material+variant and is_global_quality cannot be present at the same time
            if is_global_quality and (root_material_id or variant_name):
                raise RuntimeError("Quality profile [%s] contains invalid data: it is a global quality but contains 'material' and 'nozzle' info." % metadata["id"])

            if definition_id not in self._machine_variant_material_quality_type_to_quality_dict:
                self._machine_variant_material_quality_type_to_quality_dict[definition_id] = QualityNode()
            machine_node = self._machine_variant_material_quality_type_to_quality_dict[definition_id]

            if is_global_quality:
                # For global qualities, save data in the machine node
                machine_node.addQualityMetadata(quality_type, metadata)
                continue

            if variant_name is not None:
                # If variant_name is specified in the quality/quality_changes profile, check if material is specified,
                # too.
                if variant_name not in machine_node.children_map:
                    machine_node.children_map[variant_name] = QualityNode()
                variant_node = machine_node.children_map[variant_name]

                if root_material_id is None:
                    # If only variant_name is specified but material is not, add the quality/quality_changes metadata
                    # into the current variant node.
                    variant_node.addQualityMetadata(quality_type, metadata)
                else:
                    # If only variant_name and material are both specified, go one level deeper: create a material node
                    # under the current variant node, and then add the quality/quality_changes metadata into the
                    # material node.
                    if root_material_id not in variant_node.children_map:
                        variant_node.children_map[root_material_id] = QualityNode()
                    material_node = variant_node.children_map[root_material_id]

                    material_node.addQualityMetadata(quality_type, metadata)

            else:
                # If variant_name is not specified, check if material is specified.
                if root_material_id is not None:
                    if root_material_id not in machine_node.children_map:
                        machine_node.children_map[root_material_id] = QualityNode()
                    material_node = machine_node.children_map[root_material_id]

                    material_node.addQualityMetadata(quality_type, metadata)

        # Initialize the lookup tree for quality_changes profiles with following structure:
        # <machine> -> <quality_type> -> <name>
        quality_changes_metadata_list = self._container_registry.findContainersMetadata(type = "quality_changes")
        for metadata in quality_changes_metadata_list:
            if metadata["id"] == "empty_quality_changes":
                continue

            machine_definition_id = metadata["definition"]
            quality_type = metadata["quality_type"]

            if machine_definition_id not in self._machine_quality_type_to_quality_changes_dict:
                self._machine_quality_type_to_quality_changes_dict[machine_definition_id] = QualityNode()
            machine_node = self._machine_quality_type_to_quality_changes_dict[machine_definition_id]

            machine_node.addQualityChangesMetadata(quality_type, metadata)

    def getQualityGroups(self, machine: "GlobalStack") -> dict:
        # TODO: How to make this simpler, including the fallbacks.
        # Get machine definition ID
        machine_definition_id = self._default_machine_definition_id
        if parseBool(machine.getMetaDataEntry("has_machine_quality", False)):
            machine_definition_id = machine.getMetaDataEntry("quality_definition")
            if machine_definition_id is None:
                machine_definition_id = machine.definition.getId()

        machine_node = self._machine_variant_material_quality_type_to_quality_dict.get(machine_definition_id)
        if not machine_node:
            Logger.log("e", "Cannot find node for machine def [%s] in quality lookup table", machine_definition_id)

        # iterate over all quality_types in the machine node
        quality_group_dict = {}
        for quality_type, quality_node in machine_node.quality_type_map.items():
            quality_group = QualityGroup(quality_node.metadata["name"], quality_type)
            quality_group.node_for_global = quality_node

            quality_group_dict[quality_type] = quality_group

        # Iterate over all extruders
        for position, extruder in machine.extruders.items():
            variant_name = None
            if extruder.variant.getId() != "empty_variant":
                variant_name = extruder.variant.getName()

            # This is a list of root material IDs to use for searching for suitable quality profiles.
            # The root material IDs in this list are in prioritized order.
            root_material_id_list = []
            has_material = False  # flag indicating whether this extruder has a material assigned
            if extruder.material.getId() != "empty_material":
                has_material = True
                root_material_id = extruder.material.getMetaDataEntry("base_file")
                root_material_id_list.append(root_material_id)

                # Also try to get the fallback material
                material_type = extruder.material.getMetaDataEntry("material")
                fallback_root_material_metadata = self._material_manager.getFallbackMaterialForType(material_type)
                if fallback_root_material_metadata:
                    root_material_id_list.append(fallback_root_material_metadata["id"])

            variant_node = None
            material_node = None

            if variant_name:
                # In this case, we have both a specific variant and a specific material
                variant_node = machine_node.getChildNode(variant_name)
                if not variant_node:
                    continue
                if has_material:
                    for root_material_id in root_material_id_list:
                        material_node = variant_node.getChildNode(root_material_id)
                        if material_node:
                            break
                    if not material_node:
                        # No suitable quality found: not supported
                        Logger.log("d", "Cannot find quality with machine [%s], variant name [%s], and materials [%s].",
                                   machine_definition_id, variant_name, ", ".join(root_material_id_list))
                        continue
            else:
                # In this case, we only have a specific material but NOT a variant
                if has_material:
                    for root_material_id in root_material_id_list:
                        material_node = machine_node.getChildNode(root_material_id)
                        if material_node:
                            break
                    if not material_node:
                        # No suitable quality found: not supported
                        Logger.log("d", "Cannot find quality with machine [%s], variant name [%s], and materials [%s].",
                                   machine_definition_id, variant_name, ", ".join(root_material_id_list))
                        continue

            node_to_check = material_node
            if not node_to_check:
                node_to_check = variant_node
            if not node_to_check:
                node_to_check = machine_node

            for quality_type, quality_node in node_to_check.quality_type_map.items():
                if quality_type not in quality_group_dict:
                    quality_group = QualityGroup(quality_node.metadata["name"], quality_type)
                    quality_group_dict[quality_type] = quality_group

                quality_group = quality_group_dict[quality_type]

                quality_group.nodes_for_extruders[position] = quality_node

        used_extruders = set()
        # TODO: This will change after the Machine refactoring
        for i in range(machine.getProperty("machine_extruder_count", "value")):
            used_extruders.add(str(i))

        # Update the "is_available" flag for each quality group.
        for quality_group in quality_group_dict.values():
            is_available = True
            if quality_group.node_for_global is None:
                is_available = False
            if is_available:
                for position in used_extruders:
                    if position not in quality_group.nodes_for_extruders:
                        is_available = False
                        break

            quality_group.is_available = is_available

        return quality_group_dict


    def getQuality(self, quality_type: str, machine: "GlobalStack"):
        # Get machine definition ID
        machine_definition_id = self._default_machine_definition_id
        if parseBool(machine.getMetaDataEntry("has_machine_quality", False)):
            machine_definition_id = machine.getMetaDataEntry("quality_definition")
            if machine_definition_id is None:
                machine_definition_id = machine.definition.getId()

        machine_quality = self.getQualityContainer(quality_type, machine_definition_id)
        extruder_quality_dict = {}
        for position, extruder in machine.extruders.items():
            variant = extruder.variant
            material = extruder.material

            variant_name = variant.getName()
            if variant.getId() == "empty_variant":
                variant_name = None
            root_material_id = material.getMetaDataEntry("base_file")
            if material.getId() == "empty_material":
                root_material_id = None

            extruder_quality = self.getQualityContainer(quality_type, machine_definition_id,
                                                        variant_name, root_material_id)
            extruder_quality_dict[position] = extruder_quality

        # TODO: return as a group
        return machine_quality, extruder_quality_dict

    def getQualityContainer(self, quality_type: str, machine_definition_id: dict,
                            variant_name: Optional[str] = None,
                            root_material_id: Optional[str] = None) -> "InstanceContainer":
        assert machine_definition_id is not None
        assert quality_type is not None

        # If the specified quality cannot be found, empty_quality will be returned.
        container = self._empty_quality_container

        machine_node = self._machine_variant_material_quality_type_to_quality_dict.get(machine_definition_id)
        variant_node = None
        material_node = None
        if machine_node is not None:
            if variant_name is not None:
                variant_node = machine_node.getChildNode(variant_name)
                if variant_node is not None:
                    if root_material_id is not None:
                        material_node = variant_node.getChildNode(root_material_id)
            elif root_material_id is not None:
                material_node = machine_node.getChildNode(root_material_id)

        nodes_to_try = [material_node, variant_node, machine_node]
        if machine_definition_id != self._default_machine_definition_id:
            default_machine_node = self._machine_variant_material_quality_type_to_quality_dict.get(self._default_machine_definition_id)
            nodes_to_try.append(default_machine_node)

        for node in nodes_to_try:
            if node is None:
                continue
            quality_node = node.getQualityNode(quality_type)
            if quality_node is None:
                continue

            container = quality_node.getContainer()
            break

        return container

