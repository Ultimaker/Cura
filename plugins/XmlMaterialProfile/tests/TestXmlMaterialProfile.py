from unittest.mock import patch, MagicMock
import sys
import os

# Prevents error: "PyCapsule_GetPointer called with incorrect name" with conflicting SIP configurations between Arcus and PyQt: Import Arcus and Savitar first!
import Savitar  # Dont remove this line
import Arcus  # No really. Don't. It needs to be there!
from UM.Qt.QtApplication import QtApplication  # QtApplication import is required, even though it isn't used.

import pytest
import XmlMaterialProfile

def createXmlMaterialProfile(material_id):
    try:
        return XmlMaterialProfile.XmlMaterialProfile.XmlMaterialProfile(material_id)
    except AttributeError:
        return XmlMaterialProfile.XmlMaterialProfile(material_id)


def test_setName():
    material_1 = createXmlMaterialProfile("herpderp")
    material_2 = createXmlMaterialProfile("OMGZOMG")

    material_1.getMetaData()["base_file"] = "herpderp"
    material_2.getMetaData()["base_file"] = "herpderp"

    container_registry = MagicMock()
    container_registry.isReadOnly = MagicMock(return_value = False)
    container_registry.findInstanceContainers = MagicMock(return_value = [material_1, material_2])

    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
        material_1.setName("beep!")

    assert material_1.getName() == "beep!"
    assert material_2.getName() == "beep!"


def test_setDirty():
    material_1 = createXmlMaterialProfile("herpderp")
    material_2 = createXmlMaterialProfile("OMGZOMG")

    material_1.getMetaData()["base_file"] = "herpderp"
    material_2.getMetaData()["base_file"] = "herpderp"

    container_registry = MagicMock()
    container_registry.isReadOnly = MagicMock(return_value=False)
    container_registry.findContainers = MagicMock(return_value=[material_1, material_2])

    # Sanity check. Since we did a hacky thing to set the metadata, the container should not be dirty.
    # But this test assumes that it works like that, so we need to validate that.
    assert not material_1.isDirty()
    assert not material_2.isDirty()

    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        material_2.setDirty(True)

    assert material_1.isDirty()
    assert material_2.isDirty()

    # Setting the base material dirty does not set it's child as dirty.
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        material_1.setDirty(False)

    assert not material_1.isDirty()
    assert material_2.isDirty()


def test_serializeNonBaseMaterial():
    material_1 = createXmlMaterialProfile("herpderp")
    material_1.getMetaData()["base_file"] = "omgzomg"

    container_registry = MagicMock()
    container_registry.isReadOnly = MagicMock(return_value=False)
    container_registry.findContainers = MagicMock(return_value=[material_1])

    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        with pytest.raises(NotImplementedError):
            # This material is not a base material, so it can't be serialized!
            material_1.serialize()
            