// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Nozzle"

    property int extruderIndex: 0

    Cura.NozzleModel
    {
        id: nozzleModel
    }

    Instantiator
    {
        model: nozzleModel

        MenuItem
        {
            text: model.hotend_name
            checkable: true
            checked: Cura.MachineManager.activeVariantName == model.hotend_name
            exclusiveGroup: group
            onTriggered: {
                var position = Cura.ExtruderManager.activeExtruderIndex;
                Cura.MachineManager.setVariantGroup(position, model.container_node);
            }
        }

        onObjectAdded: menu.insertItem(index, object);
        onObjectRemoved: menu.removeItem(object);
    }

    ExclusiveGroup { id: group }
}
