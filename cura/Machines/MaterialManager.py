# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from collections import defaultdict, OrderedDict
import copy
import uuid
from typing import Dict, Optional, TYPE_CHECKING, Any, Set, List, cast, Tuple

from PyQt5.Qt import QTimer, QObject, pyqtSignal, pyqtSlot

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Decorators import deprecated
from UM.Logger import Logger
from UM.Settings.SettingFunction import SettingFunction
from UM.Util import parseBool
import cura.CuraApplication #Imported like this to prevent circular imports.
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry

from .MaterialNode import MaterialNode
from .MaterialGroup import MaterialGroup
from .VariantType import VariantType

if TYPE_CHECKING:
    from UM.Settings.DefinitionContainer import DefinitionContainer
    from UM.Settings.InstanceContainer import InstanceContainer
    from cura.Settings.GlobalStack import GlobalStack
    from cura.Settings.ExtruderStack import ExtruderStack


#
# MaterialManager maintains a number of maps and trees for material lookup.
# The models GUI and QML use are now only dependent on the MaterialManager. That means as long as the data in
# MaterialManager gets updated correctly, the GUI models should be updated correctly too, and the same goes for GUI.
#
# For now, updating the lookup maps and trees here is very simple: we discard the old data completely and recreate them
# again. This means the update is exactly the same as initialization. There are performance concerns about this approach
# but so far the creation of the tables and maps is very fast and there is no noticeable slowness, we keep it like this
# because it's simple.
#
class MaterialManager(QObject):
    __instance = None

    @classmethod
    @deprecated("Use the ContainerTree structure instead.", since = "4.3")
    def getInstance(cls) -> "MaterialManager":
        if cls.__instance is None:
            cls.__instance = MaterialManager()
        return cls.__instance

    materialsUpdated = pyqtSignal()  # Emitted whenever the material lookup tables are updated.
    favoritesUpdated = pyqtSignal()  # Emitted whenever the favorites are changed

    def __init__(self, parent = None):
        super().__init__(parent)
        # Material_type -> generic material metadata
        self._fallback_materials_map = dict()  # type: Dict[str, Dict[str, Any]]

        # Root_material_id -> MaterialGroup
        self._material_group_map = dict()  # type: Dict[str, MaterialGroup]

        # Approximate diameter str
        self._diameter_machine_nozzle_buildplate_material_map = dict()  # type: Dict[str, Dict[str, MaterialNode]]

        # We're using these two maps to convert between the specific diameter material id and the generic material id
        # because the generic material ids are used in qualities and definitions, while the specific diameter material is meant
        # i.e. generic_pla -> generic_pla_175
        # root_material_id -> approximate diameter str -> root_material_id for that diameter
        self._material_diameter_map = defaultdict(dict)  # type: Dict[str, Dict[str, str]]

        # Material id including diameter (generic_pla_175) -> material root id (generic_pla)
        self._diameter_material_map = dict()  # type: Dict[str, str]

        # This is used in Legacy UM3 send material function and the material management page.
        # GUID -> a list of material_groups
        self._guid_material_groups_map = defaultdict(list)  # type: Dict[str, List[MaterialGroup]]

        # The machine definition ID for the non-machine-specific materials.
        # This is used as the last fallback option if the given machine-specific material(s) cannot be found.
        self._default_machine_definition_id = "fdmprinter"
        self._default_approximate_diameter_for_quality_search = "3"

        self._favorites = set(cura.CuraApplication.CuraApplication.getInstance().getPreferences().getValue("cura/favorite_materials").split(";"))
        self.materialsUpdated.emit()

    def __addMaterialMetadataIntoLookupTree(self, material_metadata: Dict[str, Any]) -> None:
        material_id = material_metadata["id"]

        # We don't store empty material in the lookup tables
        if material_id == "empty_material":
            return

        root_material_id = material_metadata["base_file"]
        definition = material_metadata["definition"]
        approximate_diameter = str(material_metadata["approximate_diameter"])

        if approximate_diameter not in self._diameter_machine_nozzle_buildplate_material_map:
            self._diameter_machine_nozzle_buildplate_material_map[approximate_diameter] = {}

        machine_nozzle_buildplate_material_map = self._diameter_machine_nozzle_buildplate_material_map[
            approximate_diameter]
        if definition not in machine_nozzle_buildplate_material_map:
            machine_nozzle_buildplate_material_map[definition] = MaterialNode()

        # This is a list of information regarding the intermediate nodes:
        #    nozzle -> buildplate
        nozzle_name = material_metadata.get("variant_name")
        buildplate_name = material_metadata.get("buildplate_name")
        intermediate_node_info_list = [(nozzle_name, VariantType.NOZZLE),
                                       (buildplate_name, VariantType.BUILD_PLATE),
                                       ]

        variant_manager = cura.CuraApplication.CuraApplication.getInstance().getVariantManager()

        machine_node = machine_nozzle_buildplate_material_map[definition]
        current_node = machine_node
        current_intermediate_node_info_idx = 0
        error_message = None  # type: Optional[str]
        while current_intermediate_node_info_idx < len(intermediate_node_info_list):
            variant_name, variant_type = intermediate_node_info_list[current_intermediate_node_info_idx]
            if variant_name is not None:
                # The new material has a specific variant, so it needs to be added to that specific branch in the tree.
                variant = variant_manager.getVariantNode(definition, variant_name, variant_type)
                if variant is None:
                    error_message = "Material {id} contains a variant {name} that does not exist.".format(
                        id = material_metadata["id"], name = variant_name)
                    break

                # Update the current node to advance to a more specific branch
                if variant_name not in current_node.children_map:
                    current_node.children_map[variant_name] = MaterialNode()
                current_node = current_node.children_map[variant_name]

            current_intermediate_node_info_idx += 1

        if error_message is not None:
            Logger.log("e", "%s It will not be added into the material lookup tree.", error_message)
            CuraContainerRegistry.getInstance().addWrongContainerId(material_metadata["id"])
            return

        # Add the material to the current tree node, which is the deepest (the most specific) branch we can find.
        # Sanity check: Make sure that there is no duplicated materials.
        if root_material_id in current_node.material_map:
            Logger.log("e", "Duplicated material [%s] with root ID [%s]. It has already been added.",
                       material_id, root_material_id)
            ConfigurationErrorMessage.getInstance().addFaultyContainers(root_material_id)
            return

        current_node.material_map[root_material_id] = MaterialNode(material_metadata)

    def getMaterialGroup(self, root_material_id: str) -> Optional[MaterialGroup]:
        return self._material_group_map.get(root_material_id)

    def getRootMaterialIDForDiameter(self, root_material_id: str, approximate_diameter: str) -> str:
        return self._material_diameter_map.get(root_material_id, {}).get(approximate_diameter, root_material_id)

    def getRootMaterialIDWithoutDiameter(self, root_material_id: str) -> str:
        return self._diameter_material_map.get(root_material_id, "")

    def getMaterialGroupListByGUID(self, guid: str) -> Optional[List[MaterialGroup]]:
        return self._guid_material_groups_map.get(guid)

    # Returns a dict of all material groups organized by root_material_id.
    def getAllMaterialGroups(self) -> Dict[str, "MaterialGroup"]:
        return self._material_group_map

    #
    # Return a dict with all root material IDs (k) and ContainerNodes (v) that's suitable for the given setup.
    #
    def getAvailableMaterials(self, machine_definition: "DefinitionContainer", nozzle_name: Optional[str],
                              buildplate_name: Optional[str], diameter: float) -> Dict[str, MaterialNode]:
        # round the diameter to get the approximate diameter
        rounded_diameter = str(round(diameter))
        if rounded_diameter not in self._diameter_machine_nozzle_buildplate_material_map:
            Logger.log("i", "Cannot find materials with diameter [%s] (rounded to [%s])", diameter, rounded_diameter)
            return dict()

        machine_definition_id = machine_definition.getId()

        # If there are nozzle-and-or-buildplate materials, get the nozzle-and-or-buildplate material
        machine_nozzle_buildplate_material_map = self._diameter_machine_nozzle_buildplate_material_map[rounded_diameter]
        machine_node = machine_nozzle_buildplate_material_map.get(machine_definition_id)
        default_machine_node = machine_nozzle_buildplate_material_map.get(self._default_machine_definition_id)
        nozzle_node = None
        buildplate_node = None
        if nozzle_name is not None and machine_node is not None:
            nozzle_node = machine_node.getChildNode(nozzle_name)
            # Get buildplate node if possible
            if nozzle_node is not None and buildplate_name is not None:
                buildplate_node = nozzle_node.getChildNode(buildplate_name)

        nodes_to_check = [buildplate_node, nozzle_node, machine_node, default_machine_node]
        # Fallback mechanism of finding materials:
        #  1. buildplate-specific material
        #  2. nozzle-specific material
        #  3. machine-specific material
        #  4. generic material (for fdmprinter)
        machine_exclude_materials = machine_definition.getMetaDataEntry("exclude_materials", [])

        material_id_metadata_dict = dict()  # type: Dict[str, MaterialNode]
        excluded_materials = set()
        for current_node in nodes_to_check:
            if current_node is None:
                continue

            # Only exclude the materials that are explicitly specified in the "exclude_materials" field.
            # Do not exclude other materials that are of the same type.
            for material_id, node in current_node.material_map.items():
                if material_id in machine_exclude_materials:
                    excluded_materials.add(material_id)
                    continue

                if material_id not in material_id_metadata_dict:
                    material_id_metadata_dict[material_id] = node

        if excluded_materials:
            Logger.log("d", "Exclude materials {excluded_materials} for machine {machine_definition_id}".format(excluded_materials = ", ".join(excluded_materials), machine_definition_id = machine_definition_id))

        return material_id_metadata_dict

    #
    # A convenience function to get available materials for the given machine with the extruder position.
    #
    def getAvailableMaterialsForMachineExtruder(self, machine: "GlobalStack",
                                                extruder_stack: "ExtruderStack") -> Optional[Dict[str, MaterialNode]]:
        buildplate_name = machine.getBuildplateName()
        nozzle_name = None
        if extruder_stack.variant.getId() != "empty_variant":
            nozzle_name = extruder_stack.variant.getName()
        diameter = extruder_stack.getApproximateMaterialDiameter()

        # Fetch the available materials (ContainerNode) for the current active machine and extruder setup.
        return self.getAvailableMaterials(machine.definition, nozzle_name, buildplate_name, diameter)

    #
    # Gets MaterialNode for the given extruder and machine with the given material name.
    # Returns None if:
    #  1. the given machine doesn't have materials;
    #  2. cannot find any material InstanceContainers with the given settings.
    #
    def getMaterialNode(self, machine_definition_id: str, nozzle_name: Optional[str],
                        buildplate_name: Optional[str], diameter: float, root_material_id: str) -> Optional["MaterialNode"]:
        # round the diameter to get the approximate diameter
        rounded_diameter = str(round(diameter))
        if rounded_diameter not in self._diameter_machine_nozzle_buildplate_material_map:
            Logger.log("i", "Cannot find materials with diameter [%s] (rounded to [%s]) for root material id [%s]",
                       diameter, rounded_diameter, root_material_id)
            return None

        # If there are nozzle materials, get the nozzle-specific material
        machine_nozzle_buildplate_material_map = self._diameter_machine_nozzle_buildplate_material_map[rounded_diameter]  # type: Dict[str, MaterialNode]
        machine_node = machine_nozzle_buildplate_material_map.get(machine_definition_id)
        nozzle_node = None
        buildplate_node = None

        # Fallback for "fdmprinter" if the machine-specific materials cannot be found
        if machine_node is None:
            machine_node = machine_nozzle_buildplate_material_map.get(self._default_machine_definition_id)
        if machine_node is not None and nozzle_name is not None:
            nozzle_node = machine_node.getChildNode(nozzle_name)
        if nozzle_node is not None and buildplate_name is not None:
            buildplate_node = nozzle_node.getChildNode(buildplate_name)

        # Fallback mechanism of finding materials:
        #  1. buildplate-specific material
        #  2. nozzle-specific material
        #  3. machine-specific material
        #  4. generic material (for fdmprinter)
        nodes_to_check = [buildplate_node, nozzle_node, machine_node,
                          machine_nozzle_buildplate_material_map.get(self._default_machine_definition_id)]

        material_node = None
        for node in nodes_to_check:
            if node is not None:
                material_node = node.material_map.get(root_material_id)
                if material_node:
                    break

        return material_node

    #
    # Gets MaterialNode for the given extruder and machine with the given material type.
    # Returns None if:
    #  1. the given machine doesn't have materials;
    #  2. cannot find any material InstanceContainers with the given settings.
    #
    def getMaterialNodeByType(self, global_stack: "GlobalStack", position: str, nozzle_name: str,
                              buildplate_name: Optional[str], material_guid: str) -> Optional["MaterialNode"]:
        node = None
        machine_definition = global_stack.definition
        extruder_definition = global_stack.extruders[position].definition
        if parseBool(machine_definition.getMetaDataEntry("has_materials", False)):
            material_diameter = extruder_definition.getProperty("material_diameter", "value")
            if isinstance(material_diameter, SettingFunction):
                material_diameter = material_diameter(global_stack)

            # Look at the guid to material dictionary
            root_material_id = None
            for material_group in self._guid_material_groups_map[material_guid]:
                root_material_id = cast(str, material_group.root_material_node.getMetaDataEntry("id", ""))
                break

            if not root_material_id:
                Logger.log("i", "Cannot find materials with guid [%s] ", material_guid)
                return None

            node = self.getMaterialNode(machine_definition.getId(), nozzle_name, buildplate_name,
                                        material_diameter, root_material_id)
        return node

    #   There are 2 ways to get fallback materials;
    #   - A fallback by type (@sa getFallbackMaterialIdByMaterialType), which adds the generic version of this material
    #   - A fallback by GUID; If a material has been duplicated, it should also check if the original materials do have
    #       a GUID. This should only be done if the material itself does not have a quality just yet.
    def getFallBackMaterialIdsByMaterial(self, material: "InstanceContainer") -> List[str]:
        results = []  # type: List[str]

        material_groups = self.getMaterialGroupListByGUID(material.getMetaDataEntry("GUID"))
        for material_group in material_groups:  # type: ignore
            if material_group.name != material.getId():
                # If the material in the group is read only, put it at the front of the list (since that is the most
                # likely one to get a result)
                if material_group.is_read_only:
                    results.insert(0, material_group.name)
                else:
                    results.append(material_group.name)

        fallback = self.getFallbackMaterialIdByMaterialType(material.getMetaDataEntry("material"))
        if fallback is not None:
            results.append(fallback)
        return results

    #
    # Used by QualityManager. Built-in quality profiles may be based on generic material IDs such as "generic_pla".
    # For materials such as ultimaker_pla_orange, no quality profiles may be found, so we should fall back to use
    # the generic material IDs to search for qualities.
    #
    # An example would be, suppose we have machine with preferred material set to "filo3d_pla" (1.75mm), but its
    # extruders only use 2.85mm materials, then we won't be able to find the preferred material for this machine.
    # A fallback would be to fetch a generic material of the same type "PLA" as "filo3d_pla", and in this case it will
    # be "generic_pla". This function is intended to get a generic fallback material for the given material type.
    #
    # This function returns the generic root material ID for the given material type, where material types are "PLA",
    # "ABS", etc.
    #
    def getFallbackMaterialIdByMaterialType(self, material_type: str) -> Optional[str]:
        # For safety
        if material_type not in self._fallback_materials_map:
            Logger.log("w", "The material type [%s] does not have a fallback material" % material_type)
            return None
        fallback_material = self._fallback_materials_map[material_type]
        if fallback_material:
            return self.getRootMaterialIDWithoutDiameter(fallback_material["id"])
        else:
            return None

    ##  Get default material for given global stack, extruder position and extruder nozzle name
    #   you can provide the extruder_definition and then the position is ignored (useful when building up global stack in CuraStackBuilder)
    def getDefaultMaterial(self, global_stack: "GlobalStack", position: str, nozzle_name: Optional[str],
                           extruder_definition: Optional["DefinitionContainer"] = None) -> Optional["MaterialNode"]:
        node = None

        buildplate_name = global_stack.getBuildplateName()
        machine_definition = global_stack.definition

        # The extruder-compatible material diameter in the extruder definition may not be the correct value because
        # the user can change it in the definition_changes container.
        if extruder_definition is None:
            extruder_stack_or_definition = global_stack.extruders[position]
            is_extruder_stack = True
        else:
            extruder_stack_or_definition = extruder_definition
            is_extruder_stack = False

        if extruder_stack_or_definition and parseBool(global_stack.getMetaDataEntry("has_materials", False)):
            if is_extruder_stack:
                material_diameter = extruder_stack_or_definition.getCompatibleMaterialDiameter()
            else:
                material_diameter = extruder_stack_or_definition.getProperty("material_diameter", "value")

            if isinstance(material_diameter, SettingFunction):
                material_diameter = material_diameter(global_stack)
            approximate_material_diameter = str(round(material_diameter))
            root_material_id = machine_definition.getMetaDataEntry("preferred_material")
            root_material_id = self.getRootMaterialIDForDiameter(root_material_id, approximate_material_diameter)
            node = self.getMaterialNode(machine_definition.getId(), nozzle_name, buildplate_name,
                                        material_diameter, root_material_id)
        return node

    def removeMaterialByRootId(self, root_material_id: str):
        material_group = self.getMaterialGroup(root_material_id)
        if not material_group:
            Logger.log("i", "Unable to remove the material with id %s, because it doesn't exist.", root_material_id)
            return

        container_registry = CuraContainerRegistry.getInstance()
        nodes_to_remove = [material_group.root_material_node] + material_group.derived_material_node_list
        # Sort all nodes with respect to the container ID lengths in the ascending order so the base material container
        # will be the first one to be removed. We need to do this to ensure that all containers get loaded & deleted.
        nodes_to_remove = sorted(nodes_to_remove, key = lambda x: len(x.getMetaDataEntry("id", "")))
        # Try to load all containers first. If there is any faulty ones, they will be put into the faulty container
        # list, so removeContainer() can ignore those ones.
        for node in nodes_to_remove:
            container_id = node.getMetaDataEntry("id", "")
            results = container_registry.findContainers(id = container_id)
            if not results:
                container_registry.addWrongContainerId(container_id)
        for node in nodes_to_remove:
            container_registry.removeContainer(node.getMetaDataEntry("id", ""))

    #
    # Methods for GUI
    #
    @pyqtSlot("QVariant", result=bool)
    def canMaterialBeRemoved(self, material_node: "MaterialNode"):
        # Check if the material is active in any extruder train. In that case, the material shouldn't be removed!
        # In the future we might enable this again, but right now, it's causing a ton of issues if we do (since it
        # corrupts the configuration)
        root_material_id = material_node.getMetaDataEntry("base_file")
        material_group = self.getMaterialGroup(root_material_id)
        if not material_group:
            return False

        nodes_to_remove = [material_group.root_material_node] + material_group.derived_material_node_list
        ids_to_remove = [node.getMetaDataEntry("id", "") for node in nodes_to_remove]

        for extruder_stack in CuraContainerRegistry.getInstance().findContainerStacks(type = "extruder_train"):
            if extruder_stack.material.getId() in ids_to_remove:
                return False
        return True

    @pyqtSlot("QVariant", str)
    def setMaterialName(self, material_node: "MaterialNode", name: str) -> None:
        root_material_id = material_node.getMetaDataEntry("base_file")
        if root_material_id is None:
            return
        if CuraContainerRegistry.getInstance().isReadOnly(root_material_id):
            Logger.log("w", "Cannot set name of read-only container %s.", root_material_id)
            return

        material_group = self.getMaterialGroup(root_material_id)
        if material_group:
            container = material_group.root_material_node.getContainer()
            if container:
                container.setName(name)

    #
    # Removes the given material.
    #
    @pyqtSlot("QVariant")
    def removeMaterial(self, material_node: "MaterialNode") -> None:
        root_material_id = material_node.getMetaDataEntry("base_file")
        if root_material_id is not None:
            self.removeMaterialByRootId(root_material_id)

    #
    # Creates a duplicate of a material, which has the same GUID and base_file metadata.
    # Returns the root material ID of the duplicated material if successful.
    #
    @pyqtSlot("QVariant", result = str)
    def duplicateMaterial(self, material_node: MaterialNode, new_base_id: Optional[str] = None, new_metadata: Dict[str, Any] = None) -> Optional[str]:
        root_material_id = cast(str, material_node.getMetaDataEntry("base_file", ""))

        material_group = self.getMaterialGroup(root_material_id)
        if not material_group:
            Logger.log("i", "Unable to duplicate the material with id %s, because it doesn't exist.", root_material_id)
            return None

        base_container = material_group.root_material_node.getContainer()
        if not base_container:
            return None

        # Ensure all settings are saved.
        cura.CuraApplication.CuraApplication.getInstance().saveSettings()

        # Create a new ID & container to hold the data.
        new_containers = []
        container_registry = CuraContainerRegistry.getInstance()
        if new_base_id is None:
            new_base_id = container_registry.uniqueName(base_container.getId())
        new_base_container = copy.deepcopy(base_container)
        new_base_container.getMetaData()["id"] = new_base_id
        new_base_container.getMetaData()["base_file"] = new_base_id
        if new_metadata is not None:
            for key, value in new_metadata.items():
                new_base_container.getMetaData()[key] = value
        new_containers.append(new_base_container)

        # Clone all of them.
        for node in material_group.derived_material_node_list:
            container_to_copy = node.getContainer()
            if not container_to_copy:
                continue
            # Create unique IDs for every clone.
            new_id = new_base_id
            if container_to_copy.getMetaDataEntry("definition") != "fdmprinter":
                new_id += "_" + container_to_copy.getMetaDataEntry("definition")
                if container_to_copy.getMetaDataEntry("variant_name"):
                    nozzle_name = container_to_copy.getMetaDataEntry("variant_name")
                    new_id += "_" + nozzle_name.replace(" ", "_")

            new_container = copy.deepcopy(container_to_copy)
            new_container.getMetaData()["id"] = new_id
            new_container.getMetaData()["base_file"] = new_base_id
            if new_metadata is not None:
                for key, value in new_metadata.items():
                    new_container.getMetaData()[key] = value

            new_containers.append(new_container)

        for container_to_add in new_containers:
            container_to_add.setDirty(True)
            container_registry.addContainer(container_to_add)

        # if the duplicated material was favorite then the new material should also be added to favorite.
        if root_material_id in self.getFavorites():
            self.addFavorite(new_base_id)

        return new_base_id

    #
    # Create a new material by cloning Generic PLA for the current material diameter and generate a new GUID.
    # Returns the ID of the newly created material.
    @pyqtSlot(result = str)
    def createMaterial(self) -> str:
        from UM.i18n import i18nCatalog
        catalog = i18nCatalog("cura")
        # Ensure all settings are saved.
        application = cura.CuraApplication.CuraApplication.getInstance()
        application.saveSettings()

        machine_manager = application.getMachineManager()
        extruder_stack = machine_manager.activeStack

        machine_definition = application.getGlobalContainerStack().definition
        root_material_id = machine_definition.getMetaDataEntry("preferred_material", default = "generic_pla")

        approximate_diameter = str(extruder_stack.approximateMaterialDiameter)
        root_material_id = self.getRootMaterialIDForDiameter(root_material_id, approximate_diameter)
        material_group = self.getMaterialGroup(root_material_id)

        if not material_group:  # This should never happen
            Logger.log("w", "Cannot get the material group of %s.", root_material_id)
            return ""

        # Create a new ID & container to hold the data.
        new_id = CuraContainerRegistry.getInstance().uniqueName("custom_material")
        new_metadata = {"name": catalog.i18nc("@label", "Custom Material"),
                        "brand": catalog.i18nc("@label", "Custom"),
                        "GUID": str(uuid.uuid4()),
                        }

        self.duplicateMaterial(material_group.root_material_node,
                               new_base_id = new_id,
                               new_metadata = new_metadata)
        return new_id

    @pyqtSlot(str)
    def addFavorite(self, root_material_id: str) -> None:
        self._favorites.add(root_material_id)
        self.materialsUpdated.emit()

        # Ensure all settings are saved.
        cura.CuraApplication.CuraApplication.getInstance().getPreferences().setValue("cura/favorite_materials", ";".join(list(self._favorites)))
        cura.CuraApplication.CuraApplication.getInstance().saveSettings()

    @pyqtSlot(str)
    def removeFavorite(self, root_material_id: str) -> None:
        try:
            self._favorites.remove(root_material_id)
        except KeyError:
            Logger.log("w", "Could not delete material %s from favorites as it was already deleted", root_material_id)
            return
        self.materialsUpdated.emit()

        # Ensure all settings are saved.
        cura.CuraApplication.CuraApplication.getInstance().getPreferences().setValue("cura/favorite_materials", ";".join(list(self._favorites)))
        cura.CuraApplication.CuraApplication.getInstance().saveSettings()

    @pyqtSlot()
    def getFavorites(self):
        return self._favorites
