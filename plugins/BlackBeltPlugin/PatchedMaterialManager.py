from cura.Machines.MaterialManager import MaterialManager
from UM.Logger import Logger
import uuid

from PyQt5.Qt import pyqtSlot

from cura.Machines.MaterialNode import MaterialNode
from cura.Machines.MaterialGroup import MaterialGroup
from cura.Machines.VariantType import VariantType

from typing import Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from UM.Settings.DefinitionContainer import DefinitionContainer

class PatchedMaterialManager(MaterialManager):
    #
    # Return a dict with all root material IDs (k) and ContainerNodes (v) that's suitable for the given setup.
    #
    # Copied verbatim from MaterialManager.getAvailableMaterials, with a minor patch to limit shown materials
    # if they are so specified in the machine definition
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

        ### START PATCH
        machine_limit_materials = machine_definition.getMetaDataEntry("limit_materials", False)
        ### END PATCH

        material_id_metadata_dict = dict()  # type: Dict[str, MaterialNode]
        for current_node in nodes_to_check:
            if current_node is None:
                continue

            # Only exclude the materials that are explicitly specified in the "exclude_materials" field.
            # Do not exclude other materials that are of the same type.
            for material_id, node in current_node.material_map.items():
                ### START PATCH
                if machine_limit_materials and node.getContainer().getId() == material_id:
                    # For the materials we want Cura creates a variant-specific InstanceContainer
                    # If the InstanceContainer is not variant-specific then we are not interested
                    continue
                ### END PATCH

                if material_id in machine_exclude_materials:
                    Logger.log("d", "Exclude material [%s] for machine [%s]",
                               material_id, machine_definition.getId())
                    continue

                if material_id not in material_id_metadata_dict:
                    material_id_metadata_dict[material_id] = node

        return material_id_metadata_dict

    #
    # Create a new material by cloning Generic PLA for the current material diameter and generate a new GUID.
    #
    # Copied verbatim from MaterialManager.createMaterial, with a minor patch to use the preferred material
    # as the template (instead of generic_pla)
    @pyqtSlot(result = str)
    def createMaterial(self) -> str:
        from UM.i18n import i18nCatalog
        catalog = i18nCatalog("cura")
        # Ensure all settings are saved.
        self._application.saveSettings()

        machine_manager = self._application.getMachineManager()
        extruder_stack = machine_manager.activeStack
        ### START PATCH
        machine_definition = self._application.getGlobalContainerStack().definition
        preferred_material = machine_definition.getMetaDataEntry("preferred_material")

        approximate_diameter = str(extruder_stack.approximateMaterialDiameter)
        root_material_id = preferred_material if preferred_material else "generic_pla"
        ### END PATCH
        root_material_id = self.getRootMaterialIDForDiameter(root_material_id, approximate_diameter)
        material_group = self.getMaterialGroup(root_material_id)
        if not material_group:
            return ""

        # Create a new ID & container to hold the data.
        new_id = self._container_registry.uniqueName("custom_material")
        new_metadata = {"name": catalog.i18nc("@label", "Custom Material"),
                        "brand": catalog.i18nc("@label", "Custom"),
                        "GUID": str(uuid.uuid4()),
                        }

        self.duplicateMaterial(material_group.root_material_node,
                               new_base_id = new_id,
                               new_metadata = new_metadata)
        return new_id
