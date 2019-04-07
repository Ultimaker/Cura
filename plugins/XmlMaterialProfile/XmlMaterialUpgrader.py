# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import xml.etree.ElementTree as ET

from UM.VersionUpgrade import VersionUpgrade

from .XmlMaterialProfile import XmlMaterialProfile


class XmlMaterialUpgrader(VersionUpgrade):
    def getXmlVersion(self, serialized):
        return XmlMaterialProfile.getVersionFromSerialized(serialized)

    def _xmlVersionToSettingVersion(self, xml_version: str) -> int:
        return XmlMaterialProfile.xmlVersionToSettingVersion(xml_version)

    def upgradeMaterial(self, serialised, filename):
        data = ET.fromstring(serialised)

        # update version
        metadata = data.iterfind("./um:metadata/*", {"um": "http://www.ultimaker.com/material"})
        for entry in metadata:
            if _tag_without_namespace(entry) == "version":
                entry.text = "2"
                break

        data.attrib["version"] = "1.3"

        # this makes sure that the XML header states encoding="utf-8"
        new_serialised = ET.tostring(data, encoding="utf-8").decode("utf-8")

        return [filename], [new_serialised]


def _tag_without_namespace(element):
    return element.tag[element.tag.rfind("}") + 1:]
