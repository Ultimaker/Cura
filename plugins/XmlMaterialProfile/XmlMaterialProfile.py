# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import math
import copy
import io
import xml.etree.ElementTree as ET
import uuid

from UM.Resources import Resources
from UM.Logger import Logger
from UM.Util import parseBool
from cura.CuraApplication import CuraApplication

import UM.Dictionary

import UM.Settings

##  Handles serializing and deserializing material containers from an XML file
class XmlMaterialProfile(UM.Settings.InstanceContainer):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)
        self._inherited_files = []

    def getInheritedFiles(self):
        return self._inherited_files

    ##  Overridden from InstanceContainer
    def setReadOnly(self, read_only):
        super().setReadOnly(read_only)

        basefile = self.getMetaDataEntry("base_file", self._id)  # if basefile is self.id, this is a basefile.
        for container in UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
            container._read_only = read_only  # prevent loop instead of calling setReadOnly

    ##  Overridden from InstanceContainer
    #   set the meta data for all machine / variant combinations
    def setMetaDataEntry(self, key, value):
        if self.isReadOnly():
            return
        if self.getMetaDataEntry(key, None) == value:
            # Prevent loop caused by for loop.
            return

        super().setMetaDataEntry(key, value)

        basefile = self.getMetaDataEntry("base_file", self._id)  #if basefile is self.id, this is a basefile.
        # Update all containers that share GUID and basefile
        for container in UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
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
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile)
        for container in containers:
            container.setName(new_name)

    ##  Overridden from InstanceContainer
    # def setProperty(self, key, property_name, property_value, container = None):
    #     if self.isReadOnly():
    #         return
    #
    #     super().setProperty(key, property_name, property_value)
    #
    #     basefile = self.getMetaDataEntry("base_file", self._id)  #if basefile is self.id, this is a basefile.
    #     for container in UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
    #         if not container.isReadOnly():
    #             container.setDirty(True)

    ##  Overridden from InstanceContainer
    # base file: global settings + supported machines
    # machine / variant combination: only changes for itself.
    def serialize(self):
        registry = UM.Settings.ContainerRegistry.getInstance()

        base_file = self.getMetaDataEntry("base_file", "")
        if base_file and self.id != base_file:
            # Since we create an instance of XmlMaterialProfile for each machine and nozzle in the profile,
            # we should only serialize the "base" material definition, since that can then take care of
            # serializing the machine/nozzle specific profiles.
            raise NotImplementedError("Ignoring serializing non-root XML materials, the data is contained in the base material")

        builder = ET.TreeBuilder()

        root = builder.start("fdmmaterial", { "xmlns": "http://www.ultimaker.com/material"})

        ## Begin Metadata Block
        builder.start("metadata")

        metadata = copy.deepcopy(self.getMetaData())
        properties = metadata.pop("properties", {})

        # Metadata properties that should not be serialized.
        metadata.pop("status", "")
        metadata.pop("variant", "")
        metadata.pop("type", "")
        metadata.pop("base_file", "")

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
            # Normally value is a string.
            # Nones get handled well.
            if isinstance(value, bool):
                value = str(value)  # parseBool in deserialize expects 'True'.
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

        all_containers = registry.findInstanceContainers(GUID = self.getMetaDataEntry("GUID"))
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

        for definition_id, container in machine_container_map.items():
            definition = container.getDefinition()
            try:
                product = UM.Dictionary.findKey(self.__product_id_map, definition_id)
            except ValueError:
                # An unknown product id; export it anyway
                product = definition_id

            builder.start("machine")
            builder.start("machine_identifier", { "manufacturer": definition.getMetaDataEntry("manufacturer", ""), "product":  product})
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

                builder.start("hotend", { "id": variant_containers[0].getName() })

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
        stream = io.StringIO()
        tree = ET.ElementTree(root)
        tree.write(stream, encoding="unicode", xml_declaration=True)

        return stream.getvalue()

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

    ##  Overridden from InstanceContainer
    def deserialize(self, serialized):
        data = ET.fromstring(serialized)

        self.addMetaDataEntry("type", "material")
        self.addMetaDataEntry("base_file", self.id)

        # TODO: Add material verfication
        self.addMetaDataEntry("status", "unknown")

        inherits = data.find("./um:inherits", self.__namespaces)
        if inherits is not None:
            inherited = self._resolveInheritance(inherits.text)
            data = self._mergeXML(inherited, data)

        metadata = data.iterfind("./um:metadata/*", self.__namespaces)
        for entry in metadata:
            tag_name = _tag_without_namespace(entry)

            if tag_name == "name":
                brand = entry.find("./um:brand", self.__namespaces)
                material = entry.find("./um:material", self.__namespaces)
                color = entry.find("./um:color", self.__namespaces)
                label = entry.find("./um:label", self.__namespaces)

                if label is not None:
                    self.setName(label.text)
                else:
                    self.setName(self._profile_name(material.text, color.text))

                self.addMetaDataEntry("brand", brand.text)
                self.addMetaDataEntry("material", material.text)
                self.addMetaDataEntry("color_name", color.text)

                continue

            self.addMetaDataEntry(tag_name, entry.text)

        if not "description" in self.getMetaData():
            self.addMetaDataEntry("description", "")

        if not "adhesion_info" in self.getMetaData():
            self.addMetaDataEntry("adhesion_info", "")

        property_values = {}
        properties = data.iterfind("./um:properties/*", self.__namespaces)
        for entry in properties:
            tag_name = _tag_without_namespace(entry)
            property_values[tag_name] = entry.text

        diameter = float(property_values.get("diameter", 2.85)) # In mm
        density = float(property_values.get("density", 1.3)) # In g/cm3

        self.addMetaDataEntry("properties", property_values)

        self.setDefinition(UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id = "fdmprinter")[0])

        global_compatibility = True
        global_setting_values = {}
        settings = data.iterfind("./um:settings/um:setting", self.__namespaces)
        for entry in settings:
            key = entry.get("key")
            if key in self.__material_property_setting_map:
                self.setProperty(self.__material_property_setting_map[key], "value", entry.text, self._definition)
                global_setting_values[self.__material_property_setting_map[key]] = entry.text
            elif key in self.__unmapped_settings:
                if key == "hardware compatible":
                    global_compatibility = parseBool(entry.text)
            else:
                Logger.log("d", "Unsupported material setting %s", key)

        self._dirty = False

        machines = data.iterfind("./um:settings/um:machine", self.__namespaces)
        for machine in machines:
            machine_compatibility = global_compatibility
            machine_setting_values = {}
            settings = machine.iterfind("./um:setting", self.__namespaces)
            for entry in settings:
                key = entry.get("key")
                if key in self.__material_property_setting_map:
                    machine_setting_values[self.__material_property_setting_map[key]] = entry.text
                elif key in self.__unmapped_settings:
                    if key == "hardware compatible":
                        machine_compatibility = parseBool(entry.text)
                else:
                    Logger.log("d", "Unsupported material setting %s", key)

            identifiers = machine.iterfind("./um:machine_identifier", self.__namespaces)
            for identifier in identifiers:
                machine_id = self.__product_id_map.get(identifier.get("product"), None)
                if machine_id is None:
                    # Lets try again with some naive heuristics.
                    machine_id = identifier.get("product").replace(" ", "").lower()

                definitions = UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id = machine_id)
                if not definitions:
                    Logger.log("w", "No definition found for machine ID %s", machine_id)
                    continue

                definition = definitions[0]

                if machine_compatibility:
                    new_material = XmlMaterialProfile(self.id + "_" + machine_id)
                    new_material.setName(self.getName())
                    new_material.setMetaData(copy.deepcopy(self.getMetaData()))
                    new_material.setDefinition(definition)

                    for key, value in global_setting_values.items():
                        new_material.setProperty(key, "value", value, definition)

                    for key, value in machine_setting_values.items():
                        new_material.setProperty(key, "value", value, definition)

                    new_material._dirty = False

                    UM.Settings.ContainerRegistry.getInstance().addContainer(new_material)


                hotends = machine.iterfind("./um:hotend", self.__namespaces)
                for hotend in hotends:
                    hotend_id = hotend.get("id")
                    if hotend_id is None:
                        continue

                    variant_containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = hotend_id)
                    if not variant_containers:
                        # It is not really properly defined what "ID" is so also search for variants by name.
                        variant_containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(definition = definition.id, name = hotend_id)

                    if not variant_containers:
                        Logger.log("d", "No variants found with ID or name %s for machine %s", hotend_id, definition.id)
                        continue

                    hotend_compatibility = machine_compatibility
                    hotend_setting_values = {}
                    settings = hotend.iterfind("./um:setting", self.__namespaces)
                    for entry in settings:
                        key = entry.get("key")
                        if key in self.__material_property_setting_map:
                            hotend_setting_values[self.__material_property_setting_map[key]] = entry.text
                        elif key in self.__unmapped_settings:
                            if key == "hardware compatible":
                                hotend_compatibility = parseBool(entry.text)
                        else:
                            Logger.log("d", "Unsupported material setting %s", key)

                    new_hotend_material = XmlMaterialProfile(self.id + "_" + machine_id + "_" + hotend_id.replace(" ", "_"))
                    new_hotend_material.setName(self.getName())
                    new_hotend_material.setMetaData(copy.deepcopy(self.getMetaData()))
                    new_hotend_material.setDefinition(definition)
                    new_hotend_material.addMetaDataEntry("variant", variant_containers[0].id)
                    new_hotend_material.addMetaDataEntry("compatible", hotend_compatibility)

                    for key, value in global_setting_values.items():
                        new_hotend_material.setProperty(key, "value", value, definition)

                    for key, value in machine_setting_values.items():
                        new_hotend_material.setProperty(key, "value", value, definition)

                    for key, value in hotend_setting_values.items():
                        new_hotend_material.setProperty(key, "value", value, definition)

                    new_hotend_material._dirty = False
                    UM.Settings.ContainerRegistry.getInstance().addContainer(new_hotend_material)

        if not global_compatibility:
            # Change the type of this container so it is not shown as an option in menus.
            # This uses InstanceContainer.setMetaDataEntry because otherwise all containers that
            # share this basefile are also updated.
            dirty = self.isDirty()
            super().setMetaDataEntry("type", "incompatible_material")
            super().setDirty(dirty) # reset dirty flag after setMetaDataEntry

    def _addSettingElement(self, builder, instance):
        try:
            key = UM.Dictionary.findKey(self.__material_property_setting_map, instance.definition.key)
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

    # Map XML file setting names to internal names
    __material_property_setting_map = {
        "print temperature": "material_print_temperature",
        "heated bed temperature": "material_bed_temperature",
        "standby temperature": "material_standby_temperature",
        "processing temperature graph": "material_flow_temp_graph",
        "print cooling": "cool_fan_speed",
        "retraction amount": "retraction_amount",
        "retraction speed": "retraction_speed"
    }
    __unmapped_settings = [
        "hardware compatible"
    ]

    # Map XML file product names to internal ids
    # TODO: Move this to definition's metadata
    __product_id_map = {
        "Ultimaker 2": "ultimaker2",
        "Ultimaker 2+": "ultimaker2_plus",
        "Ultimaker 2 Go": "ultimaker2_go",
        "Ultimaker 2 Extended": "ultimaker2_extended",
        "Ultimaker 2 Extended+": "ultimaker2_extended_plus",
        "Ultimaker Original": "ultimaker_original",
        "Ultimaker Original+": "ultimaker_original_plus"
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
