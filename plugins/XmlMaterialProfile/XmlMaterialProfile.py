# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import math
import copy
import io
import xml.etree.ElementTree as ET
import uuid

from UM.Logger import Logger

import UM.Dictionary

import UM.Settings

# The namespace is prepended to the tag name but between {}.
# We are only interested in the actual tag name, so discard everything
# before the last }
def _tag_without_namespace(element):
        return element.tag[element.tag.rfind("}") + 1:]

class XmlMaterialProfile(UM.Settings.InstanceContainer):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

    def duplicate(self, new_id, new_name = None):
        result = super().duplicate(self.getMetaDataEntry("brand") + "_" + new_id, new_name)
        result.setMetaDataEntry("GUID", str(uuid.uuid4()))
        return result

    def serialize(self):
        if self.getDefinition().id != "fdmprinter":
            # Since we create an instance of XmlMaterialProfile for each machine and nozzle in the profile,
            # we should only serialize the "base" material definition, since that can then take care of
            # serializing the machine/nozzle specific profiles.
            raise NotImplementedError("Cannot serialize non-root XML materials")

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

        ## Begin Name Block
        builder.start("name")

        builder.start("brand")
        builder.data(metadata.pop("brand", ""))
        builder.end("brand")

        builder.start("material")
        builder.data(self.getName())
        metadata.pop("material", "")
        builder.end("material")

        builder.start("color")
        builder.data(metadata.pop("color_name", ""))
        builder.end("color")

        builder.end("name")
        ## End Name Block

        for key, value in metadata.items():
            builder.start(key)
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

        for instance in self.findInstances():
            builder.start("setting", { "key": UM.Dictionary.findKey(self.__material_property_setting_map, instance.definition.key) })
            builder.data(str(instance.value))
            builder.end("setting")

        # Find all machine sub-profiles corresponding to this material and add them to this profile.
        machines = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = self.getId() + "_*")
        for machine in machines:
            if machine.getMetaDataEntry("variant"):
                # Since the list includes variant-specific containers but we do not yet want to add those, we just skip them.
                continue

            builder.start("machine")

            definition = machine.getDefinition()
            builder.start("machine_identifier", { "manufacturer": definition.getMetaDataEntry("manufacturer", ""), "product": UM.Dictionary.findKey(self.__product_id_map, definition.id) })
            builder.end("machine_identifier")

            for instance in machine.findInstances():
                if self.getInstance(instance.definition.key) and self.getProperty(instance.definition.key, "value") == instance.value:
                    # If the settings match that of the base profile, just skip since we inherit the base profile.
                    continue

                builder.start("setting", { "key": UM.Dictionary.findKey(self.__material_property_setting_map, instance.definition.key) })
                builder.data(str(instance.value))
                builder.end("setting")

            # Find all hotend sub-profiles corresponding to this material and machine and add them to this profile.
            hotends = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = machine.getId() + "_*")
            for hotend in hotends:
                variant_containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = hotend.getMetaDataEntry("variant"))
                if variant_containers:
                    builder.start("hotend", { "id": variant_containers[0].getName() })

                    for instance in hotend.findInstances():
                        if self.getInstance(instance.definition.key) and self.getProperty(instance.definition.key, "value") == instance.value:
                            # If the settings match that of the base profile, just skip since we inherit the base profile.
                            continue

                        if machine.getInstance(instance.definition.key) and machine.getProperty(instance.definition.key, "value") == instance.value:
                            # If the settings match that of the machine profile, just skip since we inherit the machine profile.
                            continue

                        builder.start("setting", { "key": UM.Dictionary.findKey(self.__material_property_setting_map, instance.definition.key) })
                        builder.data(str(instance.value))
                        builder.end("setting")

                    builder.end("hotend")

            builder.end("machine")

        builder.end("settings")
        ## End Settings Block

        builder.end("fdmmaterial")

        root = builder.close()
        _indent(root)
        stream = io.StringIO()
        tree = ET.ElementTree(root)
        tree.write(stream, "unicode", True)

        return stream.getvalue()

    def deserialize(self, serialized):
        data = ET.fromstring(serialized)

        self.addMetaDataEntry("type", "material")

        # TODO: Add material verfication
        self.addMetaDataEntry("status", "unknown")

        metadata = data.iterfind("./um:metadata/*", self.__namespaces)
        for entry in metadata:
            tag_name = _tag_without_namespace(entry)

            if tag_name == "name":
                brand = entry.find("./um:brand", self.__namespaces)
                material = entry.find("./um:material", self.__namespaces)
                color = entry.find("./um:color", self.__namespaces)

                self.setName(material.text)

                self.addMetaDataEntry("brand", brand.text)
                self.addMetaDataEntry("material", material.text)
                self.addMetaDataEntry("color_name", color.text)

                continue

            self.addMetaDataEntry(tag_name, entry.text)

        property_values = {}
        properties = data.iterfind("./um:properties/*", self.__namespaces)
        for entry in properties:
            tag_name = _tag_without_namespace(entry)
            property_values[tag_name] = entry.text

        diameter = float(property_values.get("diameter", 2.85)) # In mm
        density = float(property_values.get("density", 1.3)) # In g/cm3

        weight_per_cm = (math.pi * (diameter / 20) ** 2 * 0.1) * density

        spool_weight = property_values.get("spool_weight")
        spool_length = property_values.get("spool_length")
        if spool_weight:
            length = float(spool_weight) / weight_per_cm
            property_values["spool_length"] = str(length / 100)
        elif spool_length:
            weight = (float(spool_length) * 100) * weight_per_cm
            property_values["spool_weight"] = str(weight)

        self.addMetaDataEntry("properties", property_values)

        self.setDefinition(UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id = "fdmprinter")[0])

        global_setting_values = {}
        settings = data.iterfind("./um:settings/um:setting", self.__namespaces)
        for entry in settings:
            key = entry.get("key")
            if key in self.__material_property_setting_map:
                self.setProperty(self.__material_property_setting_map[key], "value", entry.text, self._definition)
                global_setting_values[self.__material_property_setting_map[key]] = entry.text
            else:
                Logger.log("d", "Unsupported material setting %s", key)

        self._dirty = False

        machines = data.iterfind("./um:settings/um:machine", self.__namespaces)
        for machine in machines:
            machine_setting_values = {}
            settings = machine.iterfind("./um:setting", self.__namespaces)
            for entry in settings:
                key = entry.get("key")
                if key in self.__material_property_setting_map:
                    machine_setting_values[self.__material_property_setting_map[key]] = entry.text
                else:
                    Logger.log("d", "Unsupported material setting %s", key)

            identifiers = machine.iterfind("./um:machine_identifier", self.__namespaces)
            for identifier in identifiers:
                machine_id = self.__product_id_map.get(identifier.get("product"), None)
                if machine_id is None:
                    Logger.log("w", "Cannot create material for unknown machine %s", machine_id)
                    continue

                definitions = UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id = machine_id)
                if not definitions:
                    Logger.log("w", "No definition found for machine ID %s", machine_id)
                    continue

                definition = definitions[0]

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

                    new_hotend_material = XmlMaterialProfile(self.id + "_" + machine_id + "_" + hotend_id.replace(" ", "_"))
                    new_hotend_material.setName(self.getName())
                    new_hotend_material.setMetaData(copy.deepcopy(self.getMetaData()))
                    new_hotend_material.setDefinition(definition)

                    new_hotend_material.addMetaDataEntry("variant", variant_containers[0].id)

                    for key, value in global_setting_values.items():
                        new_hotend_material.setProperty(key, "value", value, definition)

                    for key, value in machine_setting_values.items():
                        new_hotend_material.setProperty(key, "value", value, definition)

                    settings = hotend.iterfind("./um:setting", self.__namespaces)
                    for entry in settings:
                        key = entry.get("key")
                        if key in self.__material_property_setting_map:
                            new_hotend_material.setProperty(self.__material_property_setting_map[key], "value", entry.text, definition)
                        else:
                            Logger.log("d", "Unsupported material setting %s", key)

                    new_hotend_material._dirty = False
                    UM.Settings.ContainerRegistry.getInstance().addContainer(new_hotend_material)


    # Map XML file setting names to internal names
    __material_property_setting_map = {
        "print temperature": "material_print_temperature",
        "heated bed temperature": "material_bed_temperature",
        "standby temperature": "material_standby_temperature",
        "print cooling": "cool_fan_speed",
        "retraction amount": "retraction_amount",
        "retraction speed": "retraction_speed",
    }

    # Map XML file product names to internal ids
    __product_id_map = {
        "Ultimaker2": "ultimaker2",
        "Ultimaker2+": "ultimaker2_plus",
        "Ultimaker2go": "ultimaker2_go",
        "Ultimaker2extended": "ultimaker2_extended",
        "Ultimaker2extended+": "ultimaker2_extended_plus",
        "Ultimaker Original": "ultimaker_original",
        "Ultimaker Original+": "ultimaker_original_plus"
    }

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
