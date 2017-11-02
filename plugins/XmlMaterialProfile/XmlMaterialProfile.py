# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
import io
from typing import List, Optional
import xml.etree.ElementTree as ET

from UM.Resources import Resources
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication

import UM.Dictionary
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry


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
    @classmethod
    def xmlVersionToSettingVersion(cls, xml_version: str) -> int:
        if xml_version == "1.3":
            return CuraApplication.SettingVersion
        return 0 #Older than 1.3.

    def getInheritedFiles(self):
        return self._inherited_files

    ##  Overridden from InstanceContainer
    def setReadOnly(self, read_only):
        super().setReadOnly(read_only)

        basefile = self.getMetaDataEntry("base_file", self._id)  # if basefile is self.id, this is a basefile.
        for container in ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
            container._read_only = read_only  # prevent loop instead of calling setReadOnly

    ##  Overridden from InstanceContainer
    #   set the meta data for all machine / variant combinations
    def setMetaDataEntry(self, key, value):
        if self.isReadOnly():
            return

        super().setMetaDataEntry(key, value)

        basefile = self.getMetaDataEntry("base_file", self._id)  #if basefile is self.id, this is a basefile.
        # Update all containers that share basefile
        for container in ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
            if container.getMetaDataEntry(key, None) != value: # Prevent recursion
                container.setMetaDataEntry(key, value)

    ##  Overridden from InstanceContainer, similar to setMetaDataEntry.
    #   without this function the setName would only set the name of the specific nozzle / material / machine combination container
    #   The function is a bit tricky. It will not set the name of all containers if it has the correct name itself.
    def setName(self, new_name):
        if self.isReadOnly():
            return

        # Not only is this faster, it also prevents a major loop that causes a stack overflow.
        if self.getName() == new_name:
            return

        super().setName(new_name)

        basefile = self.getMetaDataEntry("base_file", self._id)  # if basefile is self.id, this is a basefile.
        # Update the basefile as well, this is actually what we're trying to do
        # Update all containers that share GUID and basefile
        containers = ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile)
        for container in containers:
            container.setName(new_name)

    ##  Overridden from InstanceContainer, to set dirty to base file as well.
    def setDirty(self, dirty):
        super().setDirty(dirty)
        base_file = self.getMetaDataEntry("base_file", None)
        if base_file is not None and base_file != self._id:
            containers = ContainerRegistry.getInstance().findContainers(id=base_file)
            if containers:
                base_container = containers[0]
                if not base_container.isReadOnly():
                    base_container.setDirty(dirty)

    ##  Overridden from InstanceContainer
    # def setProperty(self, key, property_name, property_value, container = None):
    #     if self.isReadOnly():
    #         return
    #
    #     super().setProperty(key, property_name, property_value)
    #
    #     basefile = self.getMetaDataEntry("base_file", self._id)  #if basefile is self.id, this is a basefile.
    #     for container in UM.Settings.ContainerRegistry.ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
    #         if not container.isReadOnly():
    #             container.setDirty(True)

    ##  Overridden from InstanceContainer
    # base file: common settings + supported machines
    # machine / variant combination: only changes for itself.
    def serialize(self, ignored_metadata_keys: Optional[List] = None):
        registry = ContainerRegistry.getInstance()

        base_file = self.getMetaDataEntry("base_file", "")
        if base_file and self.id != base_file:
            # Since we create an instance of XmlMaterialProfile for each machine and nozzle in the profile,
            # we should only serialize the "base" material definition, since that can then take care of
            # serializing the machine/nozzle specific profiles.
            raise NotImplementedError("Ignoring serializing non-root XML materials, the data is contained in the base material")

        builder = ET.TreeBuilder()

        root = builder.start("fdmmaterial",
                             {"xmlns": "http://www.ultimaker.com/material",
                              "version": self.CurrentFdmMaterialVersion})

        ## Begin Metadata Block
        builder.start("metadata")

        metadata = copy.deepcopy(self.getMetaData())
        # setting_version is derived from the "version" tag in the schema, so don't serialize it into a file
        if ignored_metadata_keys is None:
            ignored_metadata_keys = []
        ignored_metadata_keys = ignored_metadata_keys + ["setting_version"]
        # remove the keys that we want to ignore in the metadata
        for key in ignored_metadata_keys:
            if key in metadata:
                del metadata[key]
        properties = metadata.pop("properties", {})

        # Metadata properties that should not be serialized.
        metadata.pop("status", "")
        metadata.pop("variant", "")
        metadata.pop("type", "")
        metadata.pop("base_file", "")
        metadata.pop("approximate_diameter", "")

        ## Begin Name Block
        builder.start("name")

        builder.start("brand")
        builder.data(metadata.pop("brand", ""))
        builder.end("brand")

        builder.start("material")
        builder.data(metadata.pop("material", ""))
        builder.end("material")

        builder.start("color")
        builder.data(metadata.pop("color_name", ""))
        builder.end("color")

        builder.start("label")
        builder.data(self._name)
        builder.end("label")

        builder.end("name")
        ## End Name Block

        for key, value in metadata.items():
            builder.start(key)
            if value is not None: #Nones get handled well by the builder.
                #Otherwise the builder always expects a string.
                #Deserialize expects the stringified version.
                value = str(value)
            builder.data(value)
            builder.end(key)

        builder.end("metadata")
        ## End Metadata Block

        ## Begin Properties Block
        builder.start("properties")

        for key, value in properties.items():
            builder.start(key)
            builder.data(value)
            builder.end(key)

        builder.end("properties")
        ## End Properties Block

        ## Begin Settings Block
        builder.start("settings")

        if self.getDefinition().id == "fdmprinter":
            for instance in self.findInstances():
                self._addSettingElement(builder, instance)

        machine_container_map = {}
        machine_nozzle_map = {}

        all_containers = registry.findInstanceContainers(GUID = self.getMetaDataEntry("GUID"), base_file = self._id)
        for container in all_containers:
            definition_id = container.getDefinition().id
            if definition_id == "fdmprinter":
                continue

            if definition_id not in machine_container_map:
                machine_container_map[definition_id] = container

            if definition_id not in machine_nozzle_map:
                machine_nozzle_map[definition_id] = {}

            variant = container.getMetaDataEntry("variant")
            if variant:
                machine_nozzle_map[definition_id][variant] = container
                continue

            machine_container_map[definition_id] = container

        # Map machine human-readable names to IDs
        product_id_map = {}
        for container in registry.findDefinitionContainers(type = "machine"):
            product_id_map[container.getName()] = container.getId()

        for definition_id, container in machine_container_map.items():
            definition = container.getDefinition()
            try:
                product = UM.Dictionary.findKey(product_id_map, definition_id)
            except ValueError:
                # An unknown product id; export it anyway
                product = definition_id

            builder.start("machine")
            builder.start("machine_identifier", {
                "manufacturer": container.getMetaDataEntry("machine_manufacturer", definition.getMetaDataEntry("manufacturer", "Unknown")),
                "product":  product
            })
            builder.end("machine_identifier")

            for instance in container.findInstances():
                if self.getDefinition().id == "fdmprinter" and self.getInstance(instance.definition.key) and self.getProperty(instance.definition.key, "value") == instance.value:
                    # If the settings match that of the base profile, just skip since we inherit the base profile.
                    continue

                self._addSettingElement(builder, instance)

            # Find all hotend sub-profiles corresponding to this material and machine and add them to this profile.
            for hotend_id, hotend in machine_nozzle_map[definition_id].items():
                variant_containers = registry.findInstanceContainers(id = hotend.getMetaDataEntry("variant"))
                if not variant_containers:
                    continue

                builder.start("hotend", {"id": variant_containers[0].getName()})

                # Compatible is a special case, as it's added as a meta data entry (instead of an instance).
                compatible = hotend.getMetaDataEntry("compatible")
                if compatible is not None:
                    builder.start("setting", {"key": "hardware compatible"})
                    if compatible:
                        builder.data("yes")
                    else:
                        builder.data("no")
                    builder.end("setting")

                for instance in hotend.findInstances():
                    if container.getInstance(instance.definition.key) and container.getProperty(instance.definition.key, "value") == instance.value:
                        # If the settings match that of the machine profile, just skip since we inherit the machine profile.
                        continue

                    self._addSettingElement(builder, instance)

                builder.end("hotend")

            builder.end("machine")

        builder.end("settings")
        ## End Settings Block

        builder.end("fdmmaterial")

        root = builder.close()
        _indent(root)
        stream = io.BytesIO()
        tree = ET.ElementTree(root)
        # this makes sure that the XML header states encoding="utf-8"
        tree.write(stream, encoding="utf-8", xml_declaration=True)

        return stream.getvalue().decode('utf-8')

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

        with open(path, encoding="utf-8") as f:
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

    def _createKey(self, element):
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
    def _combineElement(self, first, second):
        # Create a mapping from tag name to element.

        mapping = {}
        for element in first:
            key = self._createKey(element)
            mapping[key] = element
        for element in second:
            key = self._createKey(element)
            if len(element):  # Check if element has children.
                try:
                    if "setting" in element.tag and not "settings" in element.tag:
                        # Setting can have points in it. In that case, delete all values and override them.
                        for child in list(mapping[key]):
                            mapping[key].remove(child)
                        for child in element:
                            mapping[key].append(child)
                    else:
                        self._combineElement(mapping[key], element)  # Multiple elements, handle those.
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
        self._metadata = {}
        self._name = ""
        self._definition = None
        self._instances = {}
        self._read_only = False
        self._dirty = False
        self._path = ""

    def getConfigurationTypeFromSerialized(self, serialized: str) -> Optional[str]:
        return "materials"

    @classmethod
    def getVersionFromSerialized(cls, serialized: str) -> Optional[int]:
        data = ET.fromstring(serialized)

        version = XmlMaterialProfile.Version
        # get setting version
        if "version" in data.attrib:
            setting_version = XmlMaterialProfile.xmlVersionToSettingVersion(data.attrib["version"])
        else:
            setting_version = XmlMaterialProfile.xmlVersionToSettingVersion("1.2")

        return version * 1000000 + setting_version

    ##  Overridden from InstanceContainer
    def deserialize(self, serialized):
        containers_to_add = []
        # update the serialized data first
        from UM.Settings.Interfaces import ContainerInterface
        serialized = ContainerInterface.deserialize(self, serialized)

        try:
            data = ET.fromstring(serialized)
        except:
            Logger.logException("e", "An exception occured while parsing the material profile")
            return

        # Reset previous metadata
        self.clearData() # Ensure any previous data is gone.
        meta_data = {}
        meta_data["type"] = "material"
        meta_data["base_file"] = self.id
        meta_data["status"] = "unknown"  # TODO: Add material verification

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

        metadata = data.iterfind("./um:metadata/*", self.__namespaces)
        for entry in metadata:
            tag_name = _tag_without_namespace(entry)

            if tag_name == "name":
                brand = entry.find("./um:brand", self.__namespaces)
                material = entry.find("./um:material", self.__namespaces)
                color = entry.find("./um:color", self.__namespaces)
                label = entry.find("./um:label", self.__namespaces)

                if label is not None:
                    self._name = label.text
                else:
                    self._name = self._profile_name(material.text, color.text)
                meta_data["brand"] = brand.text
                meta_data["material"] = material.text
                meta_data["color_name"] = color.text
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

        property_values = {}
        properties = data.iterfind("./um:properties/*", self.__namespaces)
        for entry in properties:
            tag_name = _tag_without_namespace(entry)
            property_values[tag_name] = entry.text

            if tag_name in self.__material_properties_setting_map:
                common_setting_values[self.__material_properties_setting_map[tag_name]] = entry.text

        meta_data["approximate_diameter"] = str(round(float(property_values.get("diameter", 2.85)))) # In mm
        meta_data["properties"] = property_values

        self.setDefinition(ContainerRegistry.getInstance().findDefinitionContainers(id = "fdmprinter")[0])

        common_compatibility = True
        settings = data.iterfind("./um:settings/um:setting", self.__namespaces)
        for entry in settings:
            key = entry.get("key")
            if key in self.__material_settings_setting_map:
                common_setting_values[self.__material_settings_setting_map[key]] = entry.text
            elif key in self.__unmapped_settings:
                if key == "hardware compatible":
                    common_compatibility = self._parseCompatibleValue(entry.text)
        self._cached_values = common_setting_values # from InstanceContainer ancestor

        meta_data["compatible"] = common_compatibility
        self.setMetaData(meta_data)
        self._dirty = False

        # Map machine human-readable names to IDs
        product_id_map = {}
        for container in ContainerRegistry.getInstance().findDefinitionContainers(type = "machine"):
            product_id_map[container.getName()] = container.getId()

        machines = data.iterfind("./um:settings/um:machine", self.__namespaces)
        for machine in machines:
            machine_compatibility = common_compatibility
            machine_setting_values = {}
            settings = machine.iterfind("./um:setting", self.__namespaces)
            for entry in settings:
                key = entry.get("key")
                if key in self.__material_settings_setting_map:
                    machine_setting_values[self.__material_settings_setting_map[key]] = entry.text
                elif key in self.__unmapped_settings:
                    if key == "hardware compatible":
                        machine_compatibility = self._parseCompatibleValue(entry.text)
                else:
                    Logger.log("d", "Unsupported material setting %s", key)

            cached_machine_setting_properties = common_setting_values.copy()
            cached_machine_setting_properties.update(machine_setting_values)

            identifiers = machine.iterfind("./um:machine_identifier", self.__namespaces)
            for identifier in identifiers:
                machine_id = product_id_map.get(identifier.get("product"), None)
                if machine_id is None:
                    # Lets try again with some naive heuristics.
                    machine_id = identifier.get("product").replace(" ", "").lower()

                definitions = ContainerRegistry.getInstance().findDefinitionContainers(id = machine_id)
                if not definitions:
                    Logger.log("w", "No definition found for machine ID %s", machine_id)
                    continue

                definition = definitions[0]

                machine_manufacturer = identifier.get("manufacturer", definition.getMetaDataEntry("manufacturer", "Unknown")) #If the XML material doesn't specify a manufacturer, use the one in the actual printer definition.

                if machine_compatibility:
                    new_material_id = self.id + "_" + machine_id

                    # The child or derived material container may already exist. This can happen when a material in a
                    # project file and the a material in Cura have the same ID.
                    # In the case if a derived material already exists, override that material container because if
                    # the data in the parent material has been changed, the derived ones should be updated too.
                    found_materials = ContainerRegistry.getInstance().findInstanceContainers(id = new_material_id)
                    is_new_material = False
                    if found_materials:
                        new_material = found_materials[0]
                    else:
                        new_material = XmlMaterialProfile(new_material_id)
                        is_new_material = True

                    # Update the private directly, as we want to prevent the lookup that is done when using setName
                    new_material._name = self.getName()
                    new_material.setMetaData(copy.deepcopy(self.getMetaData()))
                    new_material.setDefinition(definition)
                    # Don't use setMetadata, as that overrides it for all materials with same base file
                    new_material.getMetaData()["compatible"] = machine_compatibility
                    new_material.getMetaData()["machine_manufacturer"] = machine_manufacturer

                    new_material.setCachedValues(cached_machine_setting_properties)

                    new_material._dirty = False

                    if is_new_material:
                        containers_to_add.append(new_material)

                hotends = machine.iterfind("./um:hotend", self.__namespaces)
                for hotend in hotends:
                    hotend_id = hotend.get("id")
                    if hotend_id is None:
                        continue

                    variant_containers = ContainerRegistry.getInstance().findInstanceContainers(id = hotend_id)
                    if not variant_containers:
                        # It is not really properly defined what "ID" is so also search for variants by name.
                        variant_containers = ContainerRegistry.getInstance().findInstanceContainers(definition = definition.id, name = hotend_id)

                    if not variant_containers:
                        #Logger.log("d", "No variants found with ID or name %s for machine %s", hotend_id, definition.id)
                        continue

                    hotend_compatibility = machine_compatibility
                    hotend_setting_values = {}
                    settings = hotend.iterfind("./um:setting", self.__namespaces)
                    for entry in settings:
                        key = entry.get("key")
                        if key in self.__material_settings_setting_map:
                            hotend_setting_values[self.__material_settings_setting_map[key]] = entry.text
                        elif key in self.__unmapped_settings:
                            if key == "hardware compatible":
                                hotend_compatibility = self._parseCompatibleValue(entry.text)
                        else:
                            Logger.log("d", "Unsupported material setting %s", key)

                    new_hotend_id = self.id + "_" + machine_id + "_" + hotend_id.replace(" ", "_")

                    # Same as machine compatibility, keep the derived material containers consistent with the parent
                    # material
                    found_materials = ContainerRegistry.getInstance().findInstanceContainers(id = new_hotend_id)
                    is_new_material = False
                    if found_materials:
                        new_hotend_material = found_materials[0]
                    else:
                        new_hotend_material = XmlMaterialProfile(new_hotend_id)
                        is_new_material = True

                    # Update the private directly, as we want to prevent the lookup that is done when using setName
                    new_hotend_material._name = self.getName()
                    new_hotend_material.setMetaData(copy.deepcopy(self.getMetaData()))
                    new_hotend_material.setDefinition(definition)
                    new_hotend_material.addMetaDataEntry("variant", variant_containers[0].id)
                    # Don't use setMetadata, as that overrides it for all materials with same base file
                    new_hotend_material.getMetaData()["compatible"] = hotend_compatibility
                    new_hotend_material.getMetaData()["machine_manufacturer"] = machine_manufacturer

                    cached_hotend_setting_properties = cached_machine_setting_properties.copy()
                    cached_hotend_setting_properties.update(hotend_setting_values)

                    new_hotend_material.setCachedValues(cached_hotend_setting_properties)

                    new_hotend_material._dirty = False

                    if is_new_material:
                        containers_to_add.append(new_hotend_material)

        for container_to_add in containers_to_add:
            ContainerRegistry.getInstance().addContainer(container_to_add)

    def _addSettingElement(self, builder, instance):
        try:
            key = UM.Dictionary.findKey(self.__material_settings_setting_map, instance.definition.key)
        except ValueError:
            return

        builder.start("setting", { "key": key })
        builder.data(str(instance.value))
        builder.end("setting")

    def _profile_name(self, material_name, color_name):
        if color_name != "Generic":
            return "%s %s" % (color_name, material_name)
        else:
            return material_name

    ##  Parse the value of the "material compatible" property.
    def _parseCompatibleValue(self, value: str):
        return value in {"yes", "unknown"}

    # Map XML file setting names to internal names
    __material_settings_setting_map = {
        "print temperature": "default_material_print_temperature",
        "heated bed temperature": "material_bed_temperature",
        "standby temperature": "material_standby_temperature",
        "processing temperature graph": "material_flow_temp_graph",
        "print cooling": "cool_fan_speed",
        "retraction amount": "retraction_amount",
        "retraction speed": "retraction_speed",
        "adhesion tendency": "material_adhesion_tendency",
        "surface energy": "material_surface_energy"
    }
    __unmapped_settings = [
        "hardware compatible"
    ]
    __material_properties_setting_map = {
        "diameter": "material_diameter"
    }
    __material_metadata_setting_map = {
        "GUID": "material_guid"
    }

    # Map of recognised namespaces with a proper prefix.
    __namespaces = {
        "um": "http://www.ultimaker.com/material"
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