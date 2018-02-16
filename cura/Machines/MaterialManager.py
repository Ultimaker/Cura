from collections import defaultdict, OrderedDict
from typing import Optional

from PyQt5.Qt import QTimer, QObject, pyqtSignal

from UM.Logger import Logger
from UM.Settings import ContainerRegistry

from cura.Machines.ContainerNode import ContainerNode


class MaterialGroup:
    __slots__ = ("name", "root_material_node", "derived_material_node_list")

    def __init__(self, name: str):
        self.name = name
        self.root_material_node = None
        self.derived_material_node_list = []

    def __str__(self) -> str:
        return "%s[%s]" % (self.__class__.__name__, self.name)


class MaterialNode(ContainerNode):
    __slots__ = ("material_map", "children_map")

    def __init__(self, metadata: Optional[dict] = None):
        super().__init__(metadata = metadata)
        self.material_map = {}
        self.children_map = {}


class MaterialManager(QObject):

    materialsUpdated = pyqtSignal()  # Emitted whenever the material lookup tables are updated.

    def __init__(self, container_registry, parent = None):
        super().__init__(parent)
        self._container_registry = container_registry  # type: ContainerRegistry

        self._fallback_materials_map = dict()  # material_type -> generic material metadata
        self._material_group_map = dict()  # root_material_id -> MaterialGroup
        self._diameter_machine_variant_material_map = dict()  # diameter -> dict(machine_definition_id -> MaterialNode)

        # We're using these two maps to convert between the specific diameter material id and the generic material id
        # because the generic material ids are used in qualities and definitions, while the specific diameter material is meant
        # i.e. generic_pla -> generic_pla_175
        self._material_diameter_map = defaultdict(dict)  # root_material_id -> diameter -> root_material_id for that diameter
        self._diameter_material_map = dict()  # material id including diameter (generic_pla_175) -> material root id (generic_pla)

        # This is used in Legacy UM3 send material function and the material management page.
        self._guid_material_groups_map = defaultdict(list)  # GUID -> a list of material_groups

        # The machine definition ID for the non-machine-specific materials.
        # This is used as the last fallback option if the given machine-specific material(s) cannot be found.
        self._default_machine_definition_id = "fdmprinter"
        self._default_approximate_diameter_for_quality_search = "3"

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(300)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._updateTables)

        self._container_registry.containerMetaDataChanged.connect(self._onContainerMetadataChanged)
        self._container_registry.containerAdded.connect(self._onContainerMetadataChanged)
        self._container_registry.containerRemoved.connect(self._onContainerMetadataChanged)

    def initialize(self):
        # Find all materials and put them in a matrix for quick search.
        material_metadata_list = self._container_registry.findContainersMetadata(type = "material")

        self._material_group_map = dict()

        # Map #1
        #    root_material_id -> MaterialGroup
        for material_metadata in material_metadata_list:
            material_id = material_metadata["id"]
            # We don't store empty material in the lookup tables
            if material_id == "empty_material":
                continue

            root_material_id = material_metadata.get("base_file")
            if root_material_id not in self._material_group_map:
                self._material_group_map[root_material_id] = MaterialGroup(root_material_id)
            group = self._material_group_map[root_material_id]

            # We only add root materials here
            if material_id == root_material_id:
                group.root_material_node = MaterialNode(material_metadata)
            else:
                new_node = MaterialNode(material_metadata)
                group.derived_material_node_list.append(new_node)
        self._material_group_map = OrderedDict(sorted(self._material_group_map.items(), key = lambda x: x[0]))

        # Map #1.5
        #    GUID -> material group list
        self._guid_material_groups_map = defaultdict(list)
        for root_material_id, material_group in self._material_group_map.items():
            guid = material_group.root_material_node.metadata["GUID"]
            self._guid_material_groups_map[guid].append(material_group)

        # Map #2
        # Lookup table for material type -> fallback material metadata
        grouped_by_type_dict = dict()
        for root_material_id, material_node in self._material_group_map.items():
            material_type = material_node.root_material_node.metadata["material"]
            if material_type not in grouped_by_type_dict:
                grouped_by_type_dict[material_type] = {"generic": None,
                                                       "others": []}
            brand = material_node.root_material_node.metadata["brand"]
            if brand.lower() == "generic":
                grouped_by_type_dict[material_type] = material_node.root_material_node.metadata
        self._fallback_materials_map = grouped_by_type_dict

        # Map #3
        # There can be multiple material profiles for the same material with different diameters, such as "generic_pla"
        # and "generic_pla_175". This is inconvenient when we do material-specific quality lookup because a quality can
        # be for either "generic_pla" or "generic_pla_175", but not both. This map helps to get the correct material ID
        # for quality search.
        self._material_diameter_map = defaultdict(dict)
        self._diameter_material_map = dict()

        # Group the material IDs by the same name, material, brand, and color but with different diameters.
        material_group_dict = dict()
        keys_to_fetch = ("name", "material", "brand", "color")
        for root_material_id, machine_node in self._material_group_map.items():
            root_material_metadata = machine_node.root_material_node.metadata

            key_data = []
            for key in keys_to_fetch:
                key_data.append(root_material_metadata.get(key))
            key_data = tuple(key_data)

            if key_data not in material_group_dict:
                material_group_dict[key_data] = dict()
            approximate_diameter = root_material_metadata.get("approximate_diameter")
            material_group_dict[key_data][approximate_diameter] = root_material_metadata["id"]

        # Map [root_material_id][diameter] -> root_material_id for this diameter
        for data_dict in material_group_dict.values():
            for root_material_id1 in data_dict.values():
                if root_material_id1 in self._material_diameter_map:
                    continue
                diameter_map = data_dict
                for root_material_id2 in data_dict.values():
                    self._material_diameter_map[root_material_id2] = diameter_map

            default_root_material_id = data_dict.get(self._default_approximate_diameter_for_quality_search)
            if default_root_material_id is None:
                default_root_material_id = list(data_dict.values())[0]  # no default diameter present, just take "the" only one
            for root_material_id in data_dict.values():
                self._diameter_material_map[root_material_id] = default_root_material_id

        # Map #4
        #    "machine" -> "variant_name" -> "root material ID" -> specific material InstanceContainer
        # Construct the "machine" -> "variant" -> "root material ID" -> specific material InstanceContainer
        self._diameter_machine_variant_material_map = dict()
        for material_metadata in material_metadata_list:
            # We don't store empty material in the lookup tables
            if material_metadata["id"] == "empty_material":
                continue

            root_material_id = material_metadata["base_file"]
            definition = material_metadata["definition"]
            approximate_diameter = material_metadata["approximate_diameter"]

            if approximate_diameter not in self._diameter_machine_variant_material_map:
                self._diameter_machine_variant_material_map[approximate_diameter] = {}

            machine_variant_material_map = self._diameter_machine_variant_material_map[approximate_diameter]
            if definition not in machine_variant_material_map:
                machine_variant_material_map[definition] = MaterialNode()

            machine_node = machine_variant_material_map[definition]
            variant_name = material_metadata.get("variant_name")
            if not variant_name:
                # if there is no variant, this material is for the machine, so put its metadata in the machine node.
                machine_node.material_map[root_material_id] = MaterialNode(material_metadata)
            else:
                # this material is variant-specific, so we save it in a variant-specific node under the
                # machine-specific node
                if variant_name not in machine_node.children_map:
                    machine_node.children_map[variant_name] = MaterialNode()

                variant_node = machine_node.children_map[variant_name]
                if root_material_id not in variant_node.material_map:
                    variant_node.material_map[root_material_id] = MaterialNode(material_metadata)
                else:
                    # Sanity check: make sure we don't have duplicated variant-specific materials for the same machine
                    raise RuntimeError("Found duplicate variant name [%s] for machine [%s] in material [%s]" %
                                       (variant_name, definition, material_metadata["id"]))

        self.materialsUpdated.emit()

    def _updateTables(self):
        self.initialize()

    def _onContainerMetadataChanged(self, container):
        self._onContainerChanged(container)

    def _onContainerChanged(self, container):
        container_type = container.getMetaDataEntry("type")
        if container_type != "material":
            return

        # TODO: update the cache table
        self._update_timer.start()

    def getMaterialGroup(self, root_material_id: str) -> Optional[MaterialGroup]:
        return self._material_group_map.get(root_material_id)

    def getRootMaterialIDForDiameter(self, root_material_id: str, approximate_diameter: str) -> str:
        return self._material_diameter_map.get(root_material_id).get(approximate_diameter, root_material_id)

    def getRootMaterialIDWithoutDiameter(self, root_material_id: str) -> str:
        return self._diameter_material_map.get(root_material_id)

    def getMaterialGroupListByGUID(self, guid: str) -> Optional[list]:
        return self._guid_material_groups_map.get(guid)

    #
    # Return a dict with all root material IDs (k) and ContainerNodes (v) that's suitable for the given setup.
    #
    def getAvailableMaterials(self, machine_definition_id: str, variant_name: Optional[str], diameter: float) -> dict:
        # round the diameter to get the approximate diameter
        rounded_diameter = str(round(diameter))
        if rounded_diameter not in self._diameter_machine_variant_material_map:
            Logger.log("i", "Cannot find materials with diameter [%s] (rounded to [%s])", diameter, rounded_diameter)
            return dict()

        # If there are variant materials, get the variant material
        machine_variant_material_map = self._diameter_machine_variant_material_map[rounded_diameter]
        machine_node = machine_variant_material_map.get(machine_definition_id)
        default_machine_node = machine_variant_material_map.get(self._default_machine_definition_id)
        variant_node = None
        if variant_name is not None and machine_node is not None:
            variant_node = machine_node.getChildNode(variant_name)

        nodes_to_check = [variant_node, machine_node, default_machine_node]

        # Fallback mechanism of finding materials:
        #  1. variant-specific material
        #  2. machine-specific material
        #  3. generic material (for fdmprinter)
        material_id_metadata_dict = dict()
        for node in nodes_to_check:
            if node is not None:
                material_id_metadata_dict = {mid: node for mid, node in variant_node.material_map.items()}
                break

        return material_id_metadata_dict

    #
    # Gets MaterialNode for the given extruder and machine with the given material name.
    # Returns None if:
    #  1. the given machine doesn't have materials;
    #  2. cannot find any material InstanceContainers with the given settings.
    #
    def getMaterialNode(self, machine_definition_id: str, variant_name: Optional[str], diameter: float, root_material_id: str) -> Optional["InstanceContainer"]:
        # round the diameter to get the approximate diameter
        rounded_diameter = str(round(diameter))
        if rounded_diameter not in self._diameter_machine_variant_material_map:
            Logger.log("i", "Cannot find materials with diameter [%s] (rounded to [%s]) for root material id [%s]",
                       diameter, rounded_diameter, root_material_id)
            return None

        # If there are variant materials, get the variant material
        machine_variant_material_map = self._diameter_machine_variant_material_map[rounded_diameter]
        machine_node = machine_variant_material_map.get(machine_definition_id)
        variant_node = None

        # Fallback for "fdmprinter" if the machine-specific materials cannot be found
        if machine_node is None:
            machine_node = machine_variant_material_map.get(self._default_machine_definition_id)
        if machine_node is not None and variant_name is not None:
            variant_node = machine_node.getChildNode(variant_name)

        # Fallback mechanism of finding materials:
        #  1. variant-specific material
        #  2. machine-specific material
        #  3. generic material (for fdmprinter)
        nodes_to_check = [variant_node, machine_node,
                          machine_variant_material_map.get(self._default_machine_definition_id)]

        material_node = None
        for node in nodes_to_check:
            if node is not None:
                material_node = node.material_map.get(root_material_id)
                if material_node:
                    break

        return material_node

    #
    # Used by QualityManager. Built-in quality profiles may be based on generic material IDs such as "generic_pla".
    # For materials such as ultimaker_pla_orange, no quality profiles may be found, so we should fall back to use
    # the generic material IDs to search for qualities.
    #
    # This function returns the generic root material ID for the given material type, where material types are "PLA",
    # "ABS", etc.
    #
    def getFallbackMaterialId(self, material_type: str) -> str:
        # For safety
        if material_type not in self._fallback_materials_map:
            raise RuntimeError("Material type [%s] is not in the fallback materials table." % material_type)
        fallback_material = self._fallback_materials_map[material_type]
        if fallback_material:
            return self.getRootMaterialIDWithoutDiameter(fallback_material["id"])
        else:
            return None
