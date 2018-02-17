// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.8
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Build plate"

    Instantiator
    {
        model: Cura.BuildPlateModel

        MenuItem {
            text: model.name
            checkable: true
            checked: model.name == Cura.MachineManager.globalVariantName // TODO
            exclusiveGroup: group
            onTriggered: {
                Cura.MachineManager.setGlobalVariant(model.container_node); // TODO
            }
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group }
}
