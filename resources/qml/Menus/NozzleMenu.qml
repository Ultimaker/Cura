// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Nozzle"

    Instantiator
    {
        model: UM.InstanceContainersModel
        {
            filter:
            {
                "type": "variant",
                "definition": Cura.MachineManager.activeDefinitionId //Only show variants of this machine
            }
        }
        MenuItem {
            text: model.name;
            checkable: true;
            checked: model.id == Cura.MachineManager.activeVariantId;
            exclusiveGroup: group
            onTriggered: Cura.MachineManager.setActiveVariant(model.id)
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group }
}
