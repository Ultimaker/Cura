# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from collections import defaultdict
import copy
import uuid
from typing import Dict, Optional, TYPE_CHECKING, Any, List, cast

from PyQt5.Qt import QTimer, QObject, pyqtSignal, pyqtSlot

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Decorators import deprecated
from UM.Logger import Logger
from UM.Settings.SettingFunction import SettingFunction
from UM.Util import parseBool
import cura.CuraApplication #Imported like this to prevent circular imports.
from cura.Machines.ContainerTree import ContainerTree
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

        # Material id including diameter (generic_pla_175) -> material root id (generic_pla)
        self._diameter_material_map = dict()  # type: Dict[str, str]

        # This is used in Legacy UM3 send material function and the material management page.
        # GUID -> a list of material_groups
        self._guid_material_groups_map = defaultdict(list)  # type: Dict[str, List[MaterialGroup]]

        self._favorites = set(cura.CuraApplication.CuraApplication.getInstance().getPreferences().getValue("cura/favorite_materials").split(";"))
        self.materialsUpdated.emit()

    def getMaterialGroup(self, root_material_id: str) -> Optional[MaterialGroup]:
        return self._material_group_map.get(root_material_id)

    def getRootMaterialIDForDiameter(self, root_material_id: str, approximate_diameter: str) -> str:
        original_material = CuraContainerRegistry.getInstance().findInstanceContainersMetadata(id=root_material_id)[0]
        if original_material["approximate_diameter"] == approximate_diameter:
            return root_material_id

        matching_materials = CuraContainerRegistry.getInstance().findInstanceContainersMetadata(type = "material", brand = original_material["brand"], definition = original_material["definition"], material = original_material["material"], color_name = original_material["color_name"])
        for material in matching_materials:
            if material["approximate_diameter"] == approximate_diameter:
                return material["id"]
        return root_material_id

    def getRootMaterialIDWithoutDiameter(self, root_material_id: str) -> str:
        return self._diameter_material_map.get(root_material_id, "")

    def getMaterialGroupListByGUID(self, guid: str) -> Optional[List[MaterialGroup]]:
        return self._guid_material_groups_map.get(guid)

    # Returns a dict of all material groups organized by root_material_id.
    def getAllMaterialGroups(self) -> Dict[str, "MaterialGroup"]:
        return self._material_group_map

    ##  Gives a dictionary of all root material IDs and their associated
    #   MaterialNodes from the ContainerTree that are available for the given
    #   printer and variant.
    def getAvailableMaterials(self, definition_id: str, nozzle_name: Optional[str]) -> Dict[str, MaterialNode]:
        return ContainerTree.getInstance().machines[definition_id].variants[nozzle_name].materials

    #
    # A convenience function to get available materials for the given machine with the extruder position.
    #
    def getAvailableMaterialsForMachineExtruder(self, machine: "GlobalStack",
                                                extruder_stack: "ExtruderStack") -> Dict[str, MaterialNode]:
        nozzle_name = None
        if extruder_stack.variant.getId() != "empty_variant":
            nozzle_name = extruder_stack.variant.getName()

        # Fetch the available materials (ContainerNode) for the current active machine and extruder setup.
        materials = self.getAvailableMaterials(machine.definition.getId(), nozzle_name)
        compatible_material_diameter = str(round(extruder_stack.getCompatibleMaterialDiameter()))
        result = {key: material for key, material in materials.items() if material.container.getMetaDataEntry("approximate_diameter") == compatible_material_diameter}
        return result

    #
    # Gets MaterialNode for the given extruder and machine with the given material name.
    # Returns None if:
    #  1. the given machine doesn't have materials;
    #  2. cannot find any material InstanceContainers with the given settings.
    #
    def getMaterialNode(self, machine_definition_id: str, nozzle_name: Optional[str],
                        buildplate_name: Optional[str], diameter: float, root_material_id: str) -> Optional["MaterialNode"]:
        container_tree = ContainerTree.getInstance()
        machine_node = container_tree.machines.get(machine_definition_id)
        if machine_node is None:
            Logger.log("w", "Could not find machine with definition %s in the container tree", machine_definition_id)
            return None

        variant_node = machine_node.variants.get(nozzle_name)
        if variant_node is None:
            Logger.log("w", "Could not find variant %s for machine with definition %s in the container tree", nozzle_name, machine_definition_id )
            return None

        material_node = variant_node.materials.get(root_material_id)

        if material_node is None:
            Logger.log("w", "Could not find material %s for machine with definition %s and variant %s in the container tree", root_material_id, machine_definition_id, nozzle_name)
            return None

        return material_node

    #
    # Gets MaterialNode for the given extruder and machine with the given material type.
    # Returns None if:
    #  1. the given machine doesn't have materials;
    #  2. cannot find any material InstanceContainers with the given settings.
    #
    def getMaterialNodeByType(self, global_stack: "GlobalStack", position: str, nozzle_name: str,
                              buildplate_name: Optional[str], material_guid: str) -> Optional["MaterialNode"]:
        machine_definition = global_stack.definition
        variant_name = global_stack.extruders[position].variant.getName()

        return self.getMaterialNode(machine_definition.getId(), variant_name, buildplate_name, 3, material_guid)

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
        container_registry = CuraContainerRegistry.getInstance()
        results = container_registry.findContainers(id=root_material_id)
        if not results:
            container_registry.addWrongContainerId(root_material_id)

        for result in results:
            container_registry.removeContainer(result.getMetaDataEntry("id", ""))

    @pyqtSlot("QVariant", result=bool)
    def canMaterialBeRemoved(self, material_node: "MaterialNode"):
        # Check if the material is active in any extruder train. In that case, the material shouldn't be removed!
        # In the future we might enable this again, but right now, it's causing a ton of issues if we do (since it
        # corrupts the configuration)
        root_material_id = material_node.getMetaDataEntry("base_file")
        ids_to_remove = [metadata.get("id", "") for metadata in CuraContainerRegistry.getInstance().findInstanceContainersMetadata(base_file=root_material_id)]

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
        containers = CuraContainerRegistry.getInstance().findInstanceContainers(id = root_material_id)
        containers[0].setName(name)

    @pyqtSlot("QVariant")
    def removeMaterial(self, material_node: "MaterialNode") -> None:
        root_material_id = material_node.getMetaDataEntry("base_file")
        if root_material_id is not None:
            self.removeMaterialByRootId(root_material_id)

    def duplicateMaterialByRootId(self, root_material_id,  new_base_id: Optional[str] = None, new_metadata: Dict[str, Any] = None) -> Optional[str]:
        container_registry = CuraContainerRegistry.getInstance()
        results = container_registry.findContainers(id=root_material_id)

        if not results:
            Logger.log("i", "Unable to duplicate the material with id %s, because it doesn't exist.", root_material_id)
            return None

        base_container = results[0]

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
        for container_to_copy in container_registry.findContainers(base_file=root_material_id):
            if container_to_copy.getId() == root_material_id:
                continue  # We already have that one, skip it
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
    # Creates a duplicate of a material, which has the same GUID and base_file metadata.
    # Returns the root material ID of the duplicated material if successful.
    #
    @pyqtSlot("QVariant", result = str)
    def duplicateMaterial(self, material_node: MaterialNode, new_base_id: Optional[str] = None, new_metadata: Dict[str, Any] = None) -> Optional[str]:
        root_material_id = cast(str, material_node.getMetaDataEntry("base_file", ""))
        return self.duplicateMaterialByRootId(root_material_id, new_base_id, new_metadata)

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

        # Create a new ID & container to hold the data.
        new_id = CuraContainerRegistry.getInstance().uniqueName("custom_material")
        new_metadata = {"name": catalog.i18nc("@label", "Custom Material"),
                        "brand": catalog.i18nc("@label", "Custom"),
                        "GUID": str(uuid.uuid4()),
                        }

        self.duplicateMaterialByRootId(root_material_id, new_base_id = new_id, new_metadata = new_metadata)
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
