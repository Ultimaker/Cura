# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import xml.etree.ElementTree as ET

from UM.VersionUpgrade import VersionUpgrade

from .XmlMaterialProfile import XmlMaterialProfile


CARTESIO_VARIANT_ID_TO_NEW = {
    "0.25 mm": {"id": "0.25mm thermoplastic extruder",
                "alternative_ids": "0.25 mm"},
    "0.4 mm": {"id": "0.4mm thermoplastic extruder",
               "alternative_ids": "0.4 mm"},
    "0.8 mm": {"id": "0.8mm thermoplastic extruder",
               "alternative_ids": "0.8 mm"},
}


class XmlMaterialUpgrader(VersionUpgrade):
    def getXmlVersion(self, serialized):
        return XmlMaterialProfile.getVersionFromSerialized(serialized)

    def _xmlVersionToSettingVersion(self, xml_version: str) -> int:
        return XmlMaterialProfile.xmlVersionToSettingVersion(xml_version)

    def upgradeMaterial(self, serialised, filename):
        data = ET.fromstring(serialised)

        ns = {"um": "http://www.ultimaker.com/material"}

        # Fix cartesio variant names
        machine_nodes = data.findall('./um:settings/um:machine', ns)
        for machine_node in machine_nodes:
            identifiers = machine_node.iterfind("./um:machine_identifier", ns)
            is_cartesio = False
            for identifier in identifiers:
                if identifier.get("product") == "cartesio":
                    is_cartesio = True
                    break

            if not is_cartesio:
                continue

            hotend_nodes = machine_node.findall("um:hotend", ns)
            for hotend_node in hotend_nodes:
                hotend_id = hotend_node.get("id")
                if hotend_id not in CARTESIO_VARIANT_ID_TO_NEW:
                    continue

                new_dict = CARTESIO_VARIANT_ID_TO_NEW[hotend_id]
                for key, value in new_dict.items():
                    hotend_node.set(key, value)

        # update version
        metadata = data.iterfind("./um:metadata/*", ns)
        for entry in metadata:
            if _tag_without_namespace(entry) == "version":
                entry.text = "2"
                break

        data.attrib["version"] = "1.4"

        # this makes sure that the XML header states encoding="utf-8"
        new_serialised = ET.tostring(data, encoding="utf-8").decode("utf-8")

        return [filename], [new_serialised]


def _tag_without_namespace(element):
    return element.tag[element.tag.rfind("}") + 1:]
