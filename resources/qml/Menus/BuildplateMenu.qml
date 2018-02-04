// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Build plate"

    Instantiator
    {
        id: buildplateInstantiator
        model: UM.InstanceContainersModel
        {
            filter:
            {
                "type": "variant",
                "hardware_type": "buildplate",
                "definition": Cura.MachineManager.activeDefinitionId //Only show variants of this machine
            }
        }
        MenuItem {
            text: model.name
            checkable: true
            checked: model.id == Cura.MachineManager.globalVariantId
            exclusiveGroup: group
            onTriggered:
            {
                Cura.MachineManager.setActiveVariantBuildplate(model.id);
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group }
}
