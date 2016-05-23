# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import XmlMaterialProfile

from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Material Profiles"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides capabilities to read and write XML-based material profiles."),
            "api": 3
        },
        "settings_container": {
            "mimetype": "application/x-ultimaker-material-profile"
        }
    }

def register(app):
    mime_type = MimeType(
        name = "application/x-ultimaker-material-profile",
        comment = "Ultimaker Material Profile",
        suffixes = [ "xml.fdm_material" ]
    )
    MimeTypeDatabase.addMimeType(mime_type)
    return { "settings_container": XmlMaterialProfile.XmlMaterialProfile("default_xml_material_profile") }

