# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
import io
import json #To parse the product-to-id mapping file.
import os.path #To find the product-to-id mapping.
import sys
from typing import Any, Dict, List, Optional, Tuple, cast, Set, Union
import xml.etree.ElementTree as ET

from UM.Resources import Resources
from UM.Logger import Logger
import UM.Dictionary
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.ConfigurationErrorMessage import ConfigurationErrorMessage

from cura.CuraApplication import CuraApplication
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.VariantType import VariantType

try:
    from .XmlMaterialValidator import XmlMaterialValidator
except (ImportError, SystemError):
    import XmlMaterialValidator  # type: ignore  # This fixes the tests not being able to import.


##  Handles serializing and deserializing material containers from an XML file
class XmlMaterialProfile(InstanceContainer):
    CurrentFdmMaterialVersion = "1.3"
    Version = 1

    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)
        self._inherited_files = []

    ##  Translates the version number in the XML files to the setting_version
    #   metadata entry.
    #
    #   Since the two may increment independently we need a way to say which
    #   versions of the XML specification are compatible with our setting data
    #   version numbers.
    #
    #   \param xml_version: The version number found in an XML file.
    #   \return The corresponding setting_version.
    @staticmethod
    def xmlVersionToSettingVersion(xml_version: str) -> int:
        if xml_version == "1.3":
            return CuraApplication.SettingVersion
        return 0  # Older than 1.3.

    def getInheritedFiles(self):
        return self._inherited_files

    ##  Overridden from InstanceContainer
    #   set the meta data for all machine / variant combinations
    #
    #   The "apply_to_all" flag indicates whether this piece of metadata should be applied to all material containers
    #   or just this specific container.
    #   For example, when you change the material name, you want to apply it to all its derived containers, but for
    #   some specific settings, they should only be applied to a machine/variant-specific container.
    #
    def setMetaDataEntry(self, key, value, apply_to_all = True):
        registry = ContainerRegistry.getInstance()
        if registry.isReadOnly(self.getId()):
            Logger.log("w", "Can't change metadata {key} of material {material_id} because it's read-only.".format(key = key, material_id = self.getId()))
            return

        # Some metadata such as diameter should also be instantiated to be a setting. Go though all values for the
        # "properties" field and apply the new values to SettingInstances as well.
        new_setting_values_dict = {}
        if key == "properties":
            for k, v in value.items():
                if k in self.__material_properties_setting_map:
                    new_setting_values_dict[self.__material_properties_setting_map[k]] = v

        if not apply_to_all:  # Historical: If you only want to modify THIS container. We only used that to prevent recursion but with the below code that's no longer necessary.
            # CURA-6920: This is an optimization, but it also fixes the problem that you can only set metadata for a
            # material container that can be found in the container registry.
            container_query = [self]
        else:
            container_query = registry.findContainers(base_file = self.getMetaDataEntry("base_file"))

        for container in container_query:
            if key not in container.getMetaData() or container.getMetaData()[key] != value:
                container.getMetaData()[key] = value
                container.setDirty(True)
                container.metaDataChanged.emit(container)
            for k, v in new_setting_values_dict.items():
                self.setProperty(k, "value", v)

    ##  Overridden from InstanceContainer, similar to setMetaDataEntry.
    #   without this function the setName would only set the name of the specific nozzle / material / machine combination container
    #   The function is a bit tricky. It will not set the name of all containers if it has the correct name itself.
    def setName(self, new_name):
        registry = ContainerRegistry.getInstance()
        if registry.isReadOnly(self.getId()):
            return

        # Not only is this faster, it also prevents a major loop that causes a stack overflow.
        if self.getName() == new_name:
            return

        super().setName(new_name)

        basefile = self.getMetaDataEntry("base_file", self.getId())  # if basefile is self.getId, this is a basefile.
        # Update the basefile as well, this is actually what we're trying to do
        # Update all containers that share GUID and basefile
        containers = registry.findInstanceContainers(base_file = basefile)
        for container in containers:
            container.setName(new_name)

    ##  Overridden from InstanceContainer, to set dirty to base file as well.
    def setDirty(self, dirty):
        super().setDirty(dirty)
        base_file = self.getMetaDataEntry("base_file", None)
        registry = ContainerRegistry.getInstance()
        if base_file is not None and base_file != self.getId() and not registry.isReadOnly(base_file):
            containers = registry.findContainers(id = base_file)
            if containers:
                containers[0].setDirty(dirty)

    ##  Overridden from InstanceContainer
    # base file: common settings + supported machines
    # machine / variant combination: only changes for itself.
    def serialize(self, ignored_metadata_keys: Optional[Set[str]] = None):
        registry = ContainerRegistry.getInstance()

        base_file = self.getMetaDataEntry("base_file", "")
        if base_file and self.getId() != base_file:
            # Since we create an instance of XmlMaterialProfile for each machine and nozzle in the profile,
            # we should only serialize the "base" material definition, since that can then take care of
            # serializing the machine/nozzle specific profiles.
            raise NotImplementedError("Ignoring serializing non-root XML materials, the data is contained in the base material")

        builder = ET.TreeBuilder()

        root = builder.start("fdmmaterial",
                             {"xmlns": "http://www.ultimaker.com/material",
                              "xmlns:cura": "http://www.ultimaker.com/cura",
                              "version": self.CurrentFdmMaterialVersion})

        ## Begin Metadata Block
        builder.start("metadata") # type: ignore

        metadata = copy.deepcopy(self.getMetaData())
        # setting_version is derived from the "version" tag in the schema, so don't serialize it into a file
        if ignored_metadata_keys is None:
            ignored_metadata_keys = set()
        ignored_metadata_keys |= {"setting_version", "definition", "status", "variant", "type", "base_file", "approximate_diameter", "id", "container_type", "name", "compatible"}
        # remove the keys that we want to ignore in the metadata
        for key in ignored_metadata_keys:
            if key in metadata:
                del metadata[key]
        properties = metadata.pop("properties", {})

        ## Begin Name Block
        builder.start("name") # type: ignore

        builder.start("brand") # type: ignore
        builder.data(metadata.pop("brand", ""))
        builder.end("brand")

        builder.start("material") # type: ignore
        builder.data(metadata.pop("material", ""))
        builder.end("material")

        builder.start("color") # type: ignore
        builder.data(metadata.pop("color_name", ""))
        builder.end("color")

        builder.start("label") # type: ignore
        builder.data(self.getName())
        builder.end("label")

        builder.end("name")
        ## End Name Block

        for key, value in metadata.items():
            key_to_use = key
            if key in self._metadata_tags_that_have_cura_namespace:
                key_to_use = "cura:" + key_to_use
            builder.start(key_to_use) # type: ignore
            if value is not None: #Nones get handled well by the builder.
                #Otherwise the builder always expects a string.
                #Deserialize expects the stringified version.
                value = str(value)
            builder.data(value)
            builder.end(key_to_use)

        builder.end("metadata")
        ## End Metadata Block

        ## Begin Properties Block
        builder.start("properties") # type: ignore

        for key, value in properties.items():
            builder.start(key) # type: ignore
            builder.data(value)
            builder.end(key)

        builder.end("properties")
        ## End Properties Block

        ## Begin Settings Block
        builder.start("settings") # type: ignore

        if self.getMetaDataEntry("definition") == "fdmprinter":
            for instance in self.findInstances():
                self._addSettingElement(builder, instance)

        machine_container_map = {}  # type: Dict[str, InstanceContainer]
        machine_variant_map = {}  # type: Dict[str, Dict[str, Any]]

        root_material_id = self.getMetaDataEntry("base_file")  # if basefile is self.getId, this is a basefile.
        all_containers = registry.findInstanceContainers(base_file = root_material_id)

        for container in all_containers:
            definition_id = container.getMetaDataEntry("definition")
            if definition_id == "fdmprinter":
                continue

            if definition_id not in machine_container_map:
                machine_container_map[definition_id] = container

            if definition_id not in machine_variant_map:
                machine_variant_map[definition_id] = {}

            variant_name = container.getMetaDataEntry("variant_name")
            if not variant_name:
                machine_container_map[definition_id] = container
                continue

            variant_dict = {"variant_type": container.getMetaDataEntry("hardware_type", "nozzle"),
                            "material_container": container}
            machine_variant_map[definition_id][variant_name] = variant_dict

        # Map machine human-readable names to IDs
        product_id_map = self.getProductIdMap()

        for definition_id, container in machine_container_map.items():
            definition_id = container.getMetaDataEntry("definition")
            definition_metadata = registry.findDefinitionContainersMetadata(id = definition_id)[0]

            product = definition_id
            for product_name, product_id_list in product_id_map.items():
                if definition_id in product_id_list:
                    product = product_name
                    break

            builder.start("machine") # type: ignore
            builder.start("machine_identifier", {
                "manufacturer": container.getMetaDataEntry("machine_manufacturer",
                                                           definition_metadata.get("manufacturer", "Unknown")),
                "product":  product
            })
            builder.end("machine_identifier")

            for instance in container.findInstances():
                if self.getMetaDataEntry("definition") == "fdmprinter" and self.getInstance(instance.definition.key) and self.getProperty(instance.definition.key, "value") == instance.value:
                    # If the settings match that of the base profile, just skip since we inherit the base profile.
                    continue

                self._addSettingElement(builder, instance)

            # Find all hotend sub-profiles corresponding to this material and machine and add them to this profile.
            buildplate_dict = {} # type: Dict[str, Any]
            for variant_name, variant_dict in machine_variant_map[definition_id].items():
                variant_type = VariantType(variant_dict["variant_type"])
                if variant_type == VariantType.NOZZLE:
                    # The hotend identifier is not the containers name, but its "name".
                    builder.start("hotend", {"id": variant_name})

                    # Compatible is a special case, as it's added as a meta data entry (instead of an instance).
                    material_container = variant_dict["material_container"]
                    compatible = material_container.getMetaDataEntry("compatible")
                    if compatible is not None:
                        builder.start("setting", {"key": "hardware compatible"})
                        if compatible:
                            builder.data("yes")
                        else:
                            builder.data("no")
                        builder.end("setting")

                    for instance in material_container.findInstances():
                        if container.getInstance(instance.definition.key) and container.getProperty(instance.definition.key, "value") == instance.value:
                            # If the settings match that of the machine profile, just skip since we inherit the machine profile.
                            continue

                        self._addSettingElement(builder, instance)

                    if material_container.getMetaDataEntry("buildplate_compatible") and not buildplate_dict:
                        buildplate_dict["buildplate_compatible"] = material_container.getMetaDataEntry("buildplate_compatible")
                        buildplate_dict["buildplate_recommended"] = material_container.getMetaDataEntry("buildplate_recommended")
                        buildplate_dict["material_container"] = material_container

                    builder.end("hotend")

            if buildplate_dict:
                for variant_name in buildplate_dict["buildplate_compatible"]:
                    builder.start("buildplate", {"id": variant_name})

                    material_container = buildplate_dict["material_container"]
                    buildplate_compatible_dict = material_container.getMetaDataEntry("buildplate_compatible")
                    buildplate_recommended_dict = material_container.getMetaDataEntry("buildplate_recommended")
                    if buildplate_compatible_dict:
                        compatible = buildplate_compatible_dict[variant_name]
                        recommended = buildplate_recommended_dict[variant_name]

                        builder.start("setting", {"key": "hardware compatible"})
                        builder.data("yes" if compatible else "no")
                        builder.end("setting")

                        builder.start("setting", {"key": "hardware recommended"})
                        builder.data("yes" if recommended else "no")
                        builder.end("setting")

                    builder.end("buildplate")

            builder.end("machine")

        builder.end("settings")
        ## End Settings Block

        builder.end("fdmmaterial")

        root = builder.close()
        _indent(root)
        stream = io.BytesIO()
        tree = ET.ElementTree(root)
        # this makes sure that the XML header states encoding="utf-8"
        tree.write(stream, encoding = "utf-8", xml_declaration = True)

        return stream.getvalue().decode("utf-8")

    # Recursively resolve loading inherited files
    def _resolveInheritance(self, file_name):
        xml = self._loadFile(file_name)

        inherits = xml.find("./um:inherits", self.__namespaces)
        if inherits is not None:
            inherited = self._resolveInheritance(inherits.text)
            xml = self._mergeXML(inherited, xml)

        return xml

    def _loadFile(self, file_name):
        path = Resources.getPath(CuraApplication.getInstance().ResourceTypes.MaterialInstanceContainer, file_name + ".xml.fdm_material")

        with open(path, encoding = "utf-8") as f:
            contents = f.read()

        self._inherited_files.append(path)
        return ET.fromstring(contents)

    # The XML material profile can have specific settings for machines.
    # Some machines share profiles, so they are only created once.
    # This function duplicates those elements so that each machine tag only has one identifier.
    def _expandMachinesXML(self, element):
        settings_element = element.find("./um:settings", self.__namespaces)
        machines = settings_element.iterfind("./um:machine", self.__namespaces)
        machines_to_add = []
        machines_to_remove = []
        for machine in machines:
            identifiers = list(machine.iterfind("./um:machine_identifier", self.__namespaces))
            has_multiple_identifiers = len(identifiers) > 1
            if has_multiple_identifiers:
                # Multiple identifiers found. We need to create a new machine element and copy all it's settings there.
                for identifier in identifiers:
                    new_machine = copy.deepcopy(machine)
                    # Create list of identifiers that need to be removed from the copied element.
                    other_identifiers = [self._createKey(other_identifier) for other_identifier in identifiers if other_identifier is not identifier]
                    # As we can only remove by exact object reference, we need to look through the identifiers of copied machine.
                    new_machine_identifiers = list(new_machine.iterfind("./um:machine_identifier", self.__namespaces))
                    for new_machine_identifier in new_machine_identifiers:
                        key = self._createKey(new_machine_identifier)
                        # Key was in identifiers to remove, so this element needs to be purged
                        if key in other_identifiers:
                            new_machine.remove(new_machine_identifier)
                    machines_to_add.append(new_machine)
                machines_to_remove.append(machine)
            else:
                pass  # Machine only has one identifier. Nothing to do.
        # Remove & add all required machines.
        for machine_to_remove in machines_to_remove:
            settings_element.remove(machine_to_remove)
        for machine_to_add in machines_to_add:
            settings_element.append(machine_to_add)
        return element

    def _mergeXML(self, first, second):
        result = copy.deepcopy(first)
        self._combineElement(self._expandMachinesXML(result), self._expandMachinesXML(second))
        return result

    @staticmethod
    def _createKey(element):
        key = element.tag.split("}")[-1]
        if "key" in element.attrib:
            key += " key:" + element.attrib["key"]
        if "manufacturer" in element.attrib:
            key += " manufacturer:" + element.attrib["manufacturer"]
        if "product" in element.attrib:
            key += " product:" + element.attrib["product"]
        if key == "machine":
            for item in element:
                if "machine_identifier" in item.tag:
                    key += " " + item.attrib["product"]
        return key

    # Recursively merges XML elements. Updates either the text or children if another element is found in first.
    # If it does not exist, copies it from second.
    @staticmethod
    def _combineElement(first, second):
        # Create a mapping from tag name to element.
        mapping = {}
        for element in first:
            key = XmlMaterialProfile._createKey(element)
            mapping[key] = element
        for element in second:
            key = XmlMaterialProfile._createKey(element)
            if len(element):  # Check if element has children.
                try:
                    if "setting" in element.tag and not "settings" in element.tag:
                        # Setting can have points in it. In that case, delete all values and override them.
                        for child in list(mapping[key]):
                            mapping[key].remove(child)
                        for child in element:
                            mapping[key].append(child)
                    else:
                        XmlMaterialProfile._combineElement(mapping[key], element)  # Multiple elements, handle those.
                except KeyError:
                    mapping[key] = element
                    first.append(element)
            else:
                try:
                    mapping[key].text = element.text
                except KeyError:  # Not in the mapping, so simply add it
                    mapping[key] = element
                    first.append(element)

    def clearData(self):
        self._metadata = {
            "id": self.getId(),
            "name": ""
        }
        self._definition = None
        self._instances = {}
        self._read_only = False
        self._dirty = False
        self._path = ""

    @classmethod
    def getConfigurationTypeFromSerialized(cls, serialized: str) -> Optional[str]:
        return "materials"

    @classmethod
    def getVersionFromSerialized(cls, serialized: str) -> Optional[int]:
        data = ET.fromstring(serialized)

        version = XmlMaterialProfile.Version
        # get setting version
        if "version" in data.attrib:
            setting_version = cls.xmlVersionToSettingVersion(data.attrib["version"])
        else:
            setting_version = cls.xmlVersionToSettingVersion("1.2")

        return version * 1000000 + setting_version

    ##  Overridden from InstanceContainer
    def deserialize(self, serialized, file_name = None):
        containers_to_add = []
        # update the serialized data first
        from UM.Settings.Interfaces import ContainerInterface
        serialized = ContainerInterface.deserialize(self, serialized, file_name)

        try:
            data = ET.fromstring(serialized)
        except:
            Logger.logException("e", "An exception occurred while parsing the material profile")
            return

        # Reset previous metadata
        old_id = self.getId()
        self.clearData() # Ensure any previous data is gone.
        meta_data = {}
        meta_data["type"] = "material"
        meta_data["base_file"] = self.getId()
        meta_data["status"] = "unknown"  # TODO: Add material verification
        meta_data["id"] = old_id
        meta_data["container_type"] = XmlMaterialProfile

        common_setting_values = {}

        inherits = data.find("./um:inherits", self.__namespaces)
        if inherits is not None:
            inherited = self._resolveInheritance(inherits.text)
            data = self._mergeXML(inherited, data)

        # set setting_version in metadata
        if "version" in data.attrib:
            meta_data["setting_version"] = self.xmlVersionToSettingVersion(data.attrib["version"])
        else:
            meta_data["setting_version"] = self.xmlVersionToSettingVersion("1.2") #1.2 and lower didn't have that version number there yet.

        meta_data["name"] = "Unknown Material" #In case the name tag is missing.
        for entry in data.iterfind("./um:metadata/*", self.__namespaces):
            tag_name = _tag_without_namespace(entry)

            if tag_name == "name":
                brand = entry.find("./um:brand", self.__namespaces)
                material = entry.find("./um:material", self.__namespaces)
                color = entry.find("./um:color", self.__namespaces)
                label = entry.find("./um:label", self.__namespaces)

                if label is not None and label.text is not None:
                    meta_data["name"] = label.text
                else:
                    meta_data["name"] = self._profile_name(material.text, color.text)

                meta_data["brand"] = brand.text if brand.text is not None else "Unknown Brand"
                meta_data["material"] = material.text if material.text is not None else "Unknown Type"
                meta_data["color_name"] = color.text if color.text is not None else "Unknown Color"
                continue

            # setting_version is derived from the "version" tag in the schema earlier, so don't set it here
            if tag_name == "setting_version":
                continue

            meta_data[tag_name] = entry.text

            if tag_name in self.__material_metadata_setting_map:
                common_setting_values[self.__material_metadata_setting_map[tag_name]] = entry.text

        if "description" not in meta_data:
            meta_data["description"] = ""

        if "adhesion_info" not in meta_data:
            meta_data["adhesion_info"] = ""

        validation_message = XmlMaterialValidator.validateMaterialMetaData(meta_data)
        if validation_message is not None:
            ConfigurationErrorMessage.getInstance().addFaultyContainers(self.getId())
            Logger.log("e", "Not a valid material profile: {message}".format(message = validation_message))
            return

        property_values = {}
        properties = data.iterfind("./um:properties/*", self.__namespaces)
        for entry in properties:
            tag_name = _tag_without_namespace(entry)
            property_values[tag_name] = entry.text

            if tag_name in self.__material_properties_setting_map:
                common_setting_values[self.__material_properties_setting_map[tag_name]] = entry.text

        meta_data["approximate_diameter"] = str(round(float(property_values.get("diameter", 2.85)))) # In mm
        meta_data["properties"] = property_values
        meta_data["definition"] = "fdmprinter"

        common_compatibility = True
        settings = data.iterfind("./um:settings/um:setting", self.__namespaces)
        for entry in settings:
            key = entry.get("key")
            if key in self.__material_settings_setting_map:
                if key == "processing temperature graph": #This setting has no setting text but subtags.
                    graph_nodes = entry.iterfind("./um:point", self.__namespaces)
                    graph_points = []
                    for graph_node in graph_nodes:
                        flow = float(graph_node.get("flow"))
                        temperature = float(graph_node.get("temperature"))
                        graph_points.append([flow, temperature])
                    common_setting_values[self.__material_settings_setting_map[key]] = str(graph_points)
                else:
                    common_setting_values[self.__material_settings_setting_map[key]] = entry.text
            elif key in self.__unmapped_settings:
                if key == "hardware compatible":
                    common_compatibility = self._parseCompatibleValue(entry.text)

        # Add namespaced Cura-specific settings
        settings = data.iterfind("./um:settings/cura:setting", self.__namespaces)
        for entry in settings:
            value = entry.text
            if value.lower() == "yes":
                value = True
            elif value.lower() == "no":
                value = False
            key = entry.get("key")
            common_setting_values[key] = value

        self._cached_values = common_setting_values # from InstanceContainer ancestor

        meta_data["compatible"] = common_compatibility
        self.setMetaData(meta_data)
        self._dirty = False

        # Map machine human-readable names to IDs
        product_id_map = self.getProductIdMap()

        machines = data.iterfind("./um:settings/um:machine", self.__namespaces)
        for machine in machines:
            machine_compatibility = common_compatibility
            machine_setting_values = {}
            settings = machine.iterfind("./um:setting", self.__namespaces)
            for entry in settings:
                key = entry.get("key")
                if key in self.__material_settings_setting_map:
                    if key == "processing temperature graph": #This setting has no setting text but subtags.
                        graph_nodes = entry.iterfind("./um:point", self.__namespaces)
                        graph_points = []
                        for graph_node in graph_nodes:
                            flow = float(graph_node.get("flow"))
                            temperature = float(graph_node.get("temperature"))
                            graph_points.append([flow, temperature])
                        machine_setting_values[self.__material_settings_setting_map[key]] = str(graph_points)
                    else:
                        machine_setting_values[self.__material_settings_setting_map[key]] = entry.text
                elif key in self.__unmapped_settings:
                    if key == "hardware compatible":
                        machine_compatibility = self._parseCompatibleValue(entry.text)
                else:
                    Logger.log("d", "Unsupported material setting %s", key)

            # Add namespaced Cura-specific settings
            settings = machine.iterfind("./cura:setting", self.__namespaces)
            for entry in settings:
                value = entry.text
                if value.lower() == "yes":
                    value = True
                elif value.lower() == "no":
                    value = False
                key = entry.get("key")
                machine_setting_values[key] = value

            cached_machine_setting_properties = common_setting_values.copy()
            cached_machine_setting_properties.update(machine_setting_values)

            identifiers = machine.iterfind("./um:machine_identifier", self.__namespaces)
            for identifier in identifiers:
                machine_id_list = product_id_map.get(identifier.get("product"), [])
                if not machine_id_list:
                    machine_id_list = self.getPossibleDefinitionIDsFromName(identifier.get("product"))

                for machine_id in machine_id_list:
                    definitions = ContainerRegistry.getInstance().findDefinitionContainersMetadata(id = machine_id)
                    if not definitions:
                        continue

                    definition = definitions[0]

                    machine_manufacturer = identifier.get("manufacturer", definition.get("manufacturer", "Unknown")) #If the XML material doesn't specify a manufacturer, use the one in the actual printer definition.

                    # Always create the instance of the material even if it is not compatible, otherwise it will never
                    # show as incompatible if the material profile doesn't define hotends in the machine - CURA-5444
                    new_material_id = self.getId() + "_" + machine_id

                    # The child or derived material container may already exist. This can happen when a material in a
                    # project file and the a material in Cura have the same ID.
                    # In the case if a derived material already exists, override that material container because if
                    # the data in the parent material has been changed, the derived ones should be updated too.
                    if ContainerRegistry.getInstance().isLoaded(new_material_id):
                        new_material = ContainerRegistry.getInstance().findContainers(id = new_material_id)[0]
                        is_new_material = False
                    else:
                        new_material = XmlMaterialProfile(new_material_id)
                        is_new_material = True

                    new_material.setMetaData(copy.deepcopy(self.getMetaData()))
                    new_material.getMetaData()["id"] = new_material_id
                    new_material.getMetaData()["name"] = self.getName()
                    new_material.setDefinition(machine_id)
                    # Don't use setMetadata, as that overrides it for all materials with same base file
                    new_material.getMetaData()["compatible"] = machine_compatibility
                    new_material.getMetaData()["machine_manufacturer"] = machine_manufacturer
                    new_material.getMetaData()["definition"] = machine_id

                    new_material.setCachedValues(cached_machine_setting_properties)

                    new_material._dirty = False

                    if is_new_material:
                        containers_to_add.append(new_material)

                    hotends = machine.iterfind("./um:hotend", self.__namespaces)
                    for hotend in hotends:
                        # The "id" field for hotends in material profiles is actually name
                        hotend_name = hotend.get("id")
                        if hotend_name is None:
                            continue

                        hotend_mapped_settings, hotend_unmapped_settings = self._getSettingsDictForNode(hotend)
                        hotend_compatibility = hotend_unmapped_settings.get("hardware compatible", machine_compatibility)

                        # Generate container ID for the hotend-specific material container
                        new_hotend_specific_material_id = self.getId() + "_" + machine_id + "_" + hotend_name.replace(" ", "_")

                        # Same as machine compatibility, keep the derived material containers consistent with the parent material
                        if ContainerRegistry.getInstance().isLoaded(new_hotend_specific_material_id):
                            new_hotend_material = ContainerRegistry.getInstance().findContainers(id = new_hotend_specific_material_id)[0]
                            is_new_material = False
                        else:
                            new_hotend_material = XmlMaterialProfile(new_hotend_specific_material_id)
                            is_new_material = True

                        new_hotend_material.setMetaData(copy.deepcopy(self.getMetaData()))
                        new_hotend_material.getMetaData()["id"] = new_hotend_specific_material_id
                        new_hotend_material.getMetaData()["name"] = self.getName()
                        new_hotend_material.getMetaData()["variant_name"] = hotend_name
                        new_hotend_material.setDefinition(machine_id)
                        # Don't use setMetadata, as that overrides it for all materials with same base file
                        new_hotend_material.getMetaData()["compatible"] = hotend_compatibility
                        new_hotend_material.getMetaData()["machine_manufacturer"] = machine_manufacturer
                        new_hotend_material.getMetaData()["definition"] = machine_id

                        cached_hotend_setting_properties = cached_machine_setting_properties.copy()
                        cached_hotend_setting_properties.update(hotend_mapped_settings)

                        new_hotend_material.setCachedValues(cached_hotend_setting_properties)

                        new_hotend_material._dirty = False

                        if is_new_material:
                            containers_to_add.append(new_hotend_material)

                    # there is only one ID for a machine. Once we have reached here, it means we have already found
                    # a workable ID for that machine, so there is no need to continue
                    break

        for container_to_add in containers_to_add:
            ContainerRegistry.getInstance().addContainer(container_to_add)

    @classmethod
    def _getSettingsDictForNode(cls, node) -> Tuple[Dict[str,  Any], Dict[str, Any]]:
        node_mapped_settings_dict = dict()  # type: Dict[str, Any]
        node_unmapped_settings_dict = dict()  # type: Dict[str, Any]

        # Fetch settings in the "um" namespace
        um_settings = node.iterfind("./um:setting", cls.__namespaces)
        for um_setting_entry in um_settings:
            setting_key = um_setting_entry.get("key")

            # Mapped settings
            if setting_key in cls.__material_settings_setting_map:
                if setting_key == "processing temperature graph":  # This setting has no setting text but subtags.
                    graph_nodes = um_setting_entry.iterfind("./um:point", cls.__namespaces)
                    graph_points = []
                    for graph_node in graph_nodes:
                        flow = float(graph_node.get("flow"))
                        temperature = float(graph_node.get("temperature"))
                        graph_points.append([flow, temperature])
                    node_mapped_settings_dict[cls.__material_settings_setting_map[setting_key]] = str(
                        graph_points)
                else:
                    node_mapped_settings_dict[cls.__material_settings_setting_map[setting_key]] = um_setting_entry.text

            # Unmapped settings
            elif setting_key in cls.__unmapped_settings:
                if setting_key in ("hardware compatible", "hardware recommended"):
                    node_unmapped_settings_dict[setting_key] = cls._parseCompatibleValue(um_setting_entry.text)

            # Unknown settings
            else:
                Logger.log("w", "Unsupported material setting %s", setting_key)

        # Fetch settings in the "cura" namespace
        cura_settings = node.iterfind("./cura:setting", cls.__namespaces)
        for cura_setting_entry in cura_settings:
            value = cura_setting_entry.text
            if value.lower() == "yes":
                value = True
            elif value.lower() == "no":
                value = False
            key = cura_setting_entry.get("key")

            # Cura settings are all mapped
            node_mapped_settings_dict[key] = value

        return node_mapped_settings_dict, node_unmapped_settings_dict

    @classmethod
    def deserializeMetadata(cls, serialized: str, container_id: str) -> List[Dict[str, Any]]:
        result_metadata = [] #All the metadata that we found except the base (because the base is returned).

        #Update the serialized data to the latest version.
        serialized = cls._updateSerialized(serialized)

        base_metadata = {
            "type": "material",
            "status": "unknown", #TODO: Add material verification.
            "container_type": XmlMaterialProfile,
            "id": container_id,
            "base_file": container_id
        }

        try:
            data = ET.fromstring(serialized)
        except:
            Logger.logException("e", "An exception occurred while parsing the material profile")
            return []

        #TODO: Implement the <inherits> tag. It's unused at the moment though.

        if "version" in data.attrib:
            base_metadata["setting_version"] = cls.xmlVersionToSettingVersion(data.attrib["version"])
        else:
            base_metadata["setting_version"] = cls.xmlVersionToSettingVersion("1.2") #1.2 and lower didn't have that version number there yet.

        for entry in data.iterfind("./um:metadata/*", cls.__namespaces):
            tag_name = _tag_without_namespace(entry)

            if tag_name == "name":
                brand = entry.find("./um:brand", cls.__namespaces)
                material = entry.find("./um:material", cls.__namespaces)
                color = entry.find("./um:color", cls.__namespaces)
                label = entry.find("./um:label", cls.__namespaces)

                if label is not None and label.text is not None:
                    base_metadata["name"] = label.text
                else:
                    if material is not None and color is not None:
                        base_metadata["name"] = cls._profile_name(material.text, color.text)
                    else:
                        base_metadata["name"] = "Unknown Material"

                base_metadata["brand"] = brand.text if brand is not None and brand.text is not None else "Unknown Brand"
                base_metadata["material"] = material.text if material is not None and material.text is not None else "Unknown Type"
                base_metadata["color_name"] = color.text if color is not None and color.text is not None else "Unknown Color"
                continue

            #Setting_version is derived from the "version" tag in the schema earlier, so don't set it here.
            if tag_name == "setting_version":
                continue

            base_metadata[tag_name] = entry.text

        if "description" not in base_metadata:
            base_metadata["description"] = ""
        if "adhesion_info" not in base_metadata:
            base_metadata["adhesion_info"] = ""

        property_values = {}
        properties = data.iterfind("./um:properties/*", cls.__namespaces)
        for entry in properties:
            tag_name = _tag_without_namespace(entry)
            property_values[tag_name] = entry.text

        base_metadata["approximate_diameter"] = str(round(float(cast(float, property_values.get("diameter", 2.85))))) # In mm
        base_metadata["properties"] = property_values
        base_metadata["definition"] = "fdmprinter"

        compatible_entries = data.iterfind("./um:settings/um:setting[@key='hardware compatible']", cls.__namespaces)
        try:
            common_compatibility = cls._parseCompatibleValue(next(compatible_entries).text) # type: ignore
        except StopIteration: #No 'hardware compatible' setting.
            common_compatibility = True
        base_metadata["compatible"] = common_compatibility
        result_metadata.append(base_metadata)

        # Map machine human-readable names to IDs
        product_id_map = cls.getProductIdMap()

        for machine in data.iterfind("./um:settings/um:machine", cls.__namespaces):
            machine_compatibility = common_compatibility
            for entry in machine.iterfind("./um:setting[@key='hardware compatible']", cls.__namespaces):
                if entry.text is not None:
                    machine_compatibility = cls._parseCompatibleValue(entry.text)

            for identifier in machine.iterfind("./um:machine_identifier", cls.__namespaces):
                machine_id_list = product_id_map.get(identifier.get("product", ""), [])
                if not machine_id_list:
                    machine_id_list = cls.getPossibleDefinitionIDsFromName(identifier.get("product"))

                for machine_id in machine_id_list:
                    definition_metadatas = ContainerRegistry.getInstance().findDefinitionContainersMetadata(id = machine_id)
                    if not definition_metadatas:
                        continue

                    definition_metadata = definition_metadatas[0]

                    machine_manufacturer = identifier.get("manufacturer", definition_metadata.get("manufacturer", "Unknown")) #If the XML material doesn't specify a manufacturer, use the one in the actual printer definition.

                    # Always create the instance of the material even if it is not compatible, otherwise it will never
                    # show as incompatible if the material profile doesn't define hotends in the machine - CURA-5444
                    new_material_id = container_id + "_" + machine_id

                    # Do not look for existing container/container metadata with the same ID although they may exist.
                    # In project loading and perhaps some other places, we only want to get information (metadata)
                    # from a file without changing the current state of the system. If we overwrite the existing
                    # metadata here, deserializeMetadata() will not be safe for retrieving information.
                    new_material_metadata = {}

                    new_material_metadata.update(base_metadata)
                    new_material_metadata["id"] = new_material_id
                    new_material_metadata["compatible"] = machine_compatibility
                    new_material_metadata["machine_manufacturer"] = machine_manufacturer
                    new_material_metadata["definition"] = machine_id

                    result_metadata.append(new_material_metadata)

                    buildplates = machine.iterfind("./um:buildplate", cls.__namespaces)
                    buildplate_map = {}  # type: Dict[str, Dict[str, bool]]
                    buildplate_map["buildplate_compatible"] = {}
                    buildplate_map["buildplate_recommended"] = {}
                    for buildplate in buildplates:
                        buildplate_id = buildplate.get("id")
                        if buildplate_id is None:
                            continue

                        variant_metadata = ContainerRegistry.getInstance().findInstanceContainersMetadata(id = buildplate_id)
                        if not variant_metadata:
                            # It is not really properly defined what "ID" is so also search for variants by name.
                            variant_metadata = ContainerRegistry.getInstance().findInstanceContainersMetadata(definition = machine_id, name = buildplate_id)

                        if not variant_metadata:
                            continue

                        settings = buildplate.iterfind("./um:setting", cls.__namespaces)
                        buildplate_compatibility = True
                        buildplate_recommended = True
                        for entry in settings:
                            key = entry.get("key")
                            if entry.text is not None:
                                if key == "hardware compatible":
                                    buildplate_compatibility = cls._parseCompatibleValue(entry.text)
                                elif key == "hardware recommended":
                                    buildplate_recommended = cls._parseCompatibleValue(entry.text)

                        buildplate_map["buildplate_compatible"][buildplate_id] = buildplate_compatibility
                        buildplate_map["buildplate_recommended"][buildplate_id] = buildplate_recommended

                    for hotend in machine.iterfind("./um:hotend", cls.__namespaces):
                        hotend_name = hotend.get("id")
                        if hotend_name is None:
                            continue

                        hotend_compatibility = machine_compatibility
                        for entry in hotend.iterfind("./um:setting[@key='hardware compatible']", cls.__namespaces):
                            if entry.text is not None:
                                hotend_compatibility = cls._parseCompatibleValue(entry.text)

                        new_hotend_specific_material_id = container_id + "_" + machine_id + "_" + hotend_name.replace(" ", "_")

                        # Same as above, do not overwrite existing metadata.
                        new_hotend_material_metadata = {}

                        new_hotend_material_metadata.update(base_metadata)
                        new_hotend_material_metadata["variant_name"] = hotend_name
                        new_hotend_material_metadata["compatible"] = hotend_compatibility
                        new_hotend_material_metadata["machine_manufacturer"] = machine_manufacturer
                        new_hotend_material_metadata["id"] = new_hotend_specific_material_id
                        new_hotend_material_metadata["definition"] = machine_id
                        if buildplate_map["buildplate_compatible"]:
                            new_hotend_material_metadata["buildplate_compatible"] = buildplate_map["buildplate_compatible"]
                            new_hotend_material_metadata["buildplate_recommended"] = buildplate_map["buildplate_recommended"]

                        result_metadata.append(new_hotend_material_metadata)

                        #
                        # Buildplates in Hotends
                        #
                        buildplates = hotend.iterfind("./um:buildplate", cls.__namespaces)
                        for buildplate in buildplates:
                            # The "id" field for buildplate in material profiles is actually name
                            buildplate_name = buildplate.get("id")
                            if buildplate_name is None:
                                continue

                            buildplate_mapped_settings, buildplate_unmapped_settings = cls._getSettingsDictForNode(buildplate)
                            buildplate_compatibility = buildplate_unmapped_settings.get("hardware compatible",
                                                                                        buildplate_map["buildplate_compatible"])
                            buildplate_recommended = buildplate_unmapped_settings.get("hardware recommended",
                                                                                      buildplate_map["buildplate_recommended"])

                            # Generate container ID for the hotend-and-buildplate-specific material container
                            new_hotend_and_buildplate_specific_material_id = new_hotend_specific_material_id + "_" + buildplate_name.replace(
                                " ", "_")

                            new_hotend_and_buildplate_material_metadata = {}
                            new_hotend_and_buildplate_material_metadata.update(new_hotend_material_metadata)
                            new_hotend_and_buildplate_material_metadata["id"] = new_hotend_and_buildplate_specific_material_id
                            new_hotend_and_buildplate_material_metadata["buildplate_name"] = buildplate_name
                            new_hotend_and_buildplate_material_metadata["compatible"] = buildplate_compatibility
                            new_hotend_and_buildplate_material_metadata["buildplate_compatible"] = buildplate_compatibility
                            new_hotend_and_buildplate_material_metadata["buildplate_recommended"] = buildplate_recommended

                            result_metadata.append(new_hotend_and_buildplate_material_metadata)

                    # there is only one ID for a machine. Once we have reached here, it means we have already found
                    # a workable ID for that machine, so there is no need to continue
                    break

        return result_metadata

    def _addSettingElement(self, builder, instance):
        key = instance.definition.key
        if key in self.__material_settings_setting_map.values():
            # Setting has a key in the standard namespace
            key = UM.Dictionary.findKey(self.__material_settings_setting_map, instance.definition.key)
            tag_name = "setting"

            if key == "processing temperature graph": #The Processing Temperature Graph has its own little structure that we need to implement separately.
                builder.start(tag_name, {"key": key})
                graph_str = str(instance.value)
                graph = graph_str.replace("[", "").replace("]", "").split(", ") #Crude parsing of this list: Flatten the list by removing all brackets, then split on ", ". Safe to eval attacks though!
                graph = [graph[i:i + 2] for i in range(0, len(graph) - 1, 2)] #Convert to 2D array.
                for point in graph:
                    builder.start("point", {"flow": point[0], "temperature": point[1]})
                    builder.end("point")
                builder.end(tag_name)
                return

        elif key not in self.__material_properties_setting_map.values() and key not in self.__material_metadata_setting_map.values():
            # Setting is not in the standard namespace, and not a material property (eg diameter) or metadata (eg GUID)
            tag_name = "cura:setting"
        else:
            # Skip material properties (eg diameter) or metadata (eg GUID)
            return

        if instance.value is True:
            data = "yes"
        elif instance.value is False:
            data = "no"
        else:
            data = str(instance.value)

        builder.start(tag_name, { "key": key })
        builder.data(data)
        builder.end(tag_name)

    @staticmethod
    def _profile_name(material_name, color_name):
        if material_name is None:
            return "Unknown Material"
        if color_name != "Generic":
            return "%s %s" % (color_name, material_name)
        else:
            return material_name

    @staticmethod
    def getPossibleDefinitionIDsFromName(name):
        name_parts = name.lower().split(" ")
        merged_name_parts = []
        for part in name_parts:
            if len(part) == 0:
                continue
            if len(merged_name_parts) == 0:
                merged_name_parts.append(part)
                continue
            if part.isdigit():
                # for names with digit(s) such as Ultimaker 3 Extended, we generate an ID like
                # "ultimaker3_extended", ignoring the space between "Ultimaker" and "3".
                merged_name_parts[-1] = merged_name_parts[-1] + part
            else:
                merged_name_parts.append(part)

        id_list = {name.lower().replace(" ", ""),  # simply removing all spaces
                   name.lower().replace(" ", "_"),  # simply replacing all spaces with underscores
                   "_".join(merged_name_parts),
                   }
        id_list = list(id_list)
        return id_list

    ##  Gets a mapping from product names in the XML files to their definition
    #   IDs.
    #
    #   This loads the mapping from a file.
    @classmethod
    def getProductIdMap(cls) -> Dict[str, List[str]]:
        product_to_id_file = os.path.join(os.path.dirname(sys.modules[cls.__module__].__file__), "product_to_id.json")
        with open(product_to_id_file, encoding = "utf-8") as f:
            product_to_id_map = json.load(f)
        product_to_id_map = {key: [value] for key, value in product_to_id_map.items()}
        #This also loads "Ultimaker S5" -> "ultimaker_s5" even though that is not strictly necessary with the default to change spaces into underscores.
        #However it is not always loaded with that default; this mapping is also used in serialize() without that default.
        return product_to_id_map

    ##  Parse the value of the "material compatible" property.
    @staticmethod
    def _parseCompatibleValue(value: str):
        return value in {"yes", "unknown"}

    ##  Small string representation for debugging.
    def __str__(self):
        return "<XmlMaterialProfile '{my_id}' ('{name}') from base file '{base_file}'>".format(my_id = self.getId(), name = self.getName(), base_file = self.getMetaDataEntry("base_file"))

    _metadata_tags_that_have_cura_namespace = {"pva_compatible", "breakaway_compatible"}

    # Map XML file setting names to internal names
    __material_settings_setting_map = {
        "print temperature": "default_material_print_temperature",
        "heated bed temperature": "default_material_bed_temperature",
        "standby temperature": "material_standby_temperature",
        "processing temperature graph": "material_flow_temp_graph",
        "print cooling": "cool_fan_speed",
        "retraction amount": "retraction_amount",
        "retraction speed": "retraction_speed",
        "adhesion tendency": "material_adhesion_tendency",
        "surface energy": "material_surface_energy",
        "shrinkage percentage": "material_shrinkage_percentage",
        "build volume temperature": "build_volume_temperature",
        "anti ooze retract position": "material_anti_ooze_retracted_position",
        "anti ooze retract speed": "material_anti_ooze_retraction_speed",
        "break preparation position": "material_break_preparation_retracted_position",
        "break preparation speed": "material_break_preparation_speed",
        "break position": "material_break_retracted_position",
        "break speed": "material_break_speed",
        "break temperature": "material_break_temperature"
    }  # type: Dict[str, str]
    __unmapped_settings = [
        "hardware compatible",
        "hardware recommended"
    ]
    __material_properties_setting_map = {
        "diameter": "material_diameter"
    }
    __material_metadata_setting_map = {
        "GUID": "material_guid"
    }

    # Map of recognised namespaces with a proper prefix.
    __namespaces = {
        "um": "http://www.ultimaker.com/material",
        "cura": "http://www.ultimaker.com/cura"
    }

##  Helper function for pretty-printing XML because ETree is stupid
def _indent(elem, level = 0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# The namespace is prepended to the tag name but between {}.
# We are only interested in the actual tag name, so discard everything
# before the last }
def _tag_without_namespace(element):
    return element.tag[element.tag.rfind("}") + 1:]
