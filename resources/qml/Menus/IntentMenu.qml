// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.6 as Cura

Menu
{
    id: menu
    title: "Intent"

    property int extruderIndex: 0

    Cura.IntentModel
    {
        id: intentModel
    }

    Instantiator
    {
        model: intentModel

        MenuItem
        {
            text: model.name
            checkable: true
            checked: false
            Binding on checked
            {
                when: Cura.MachineManager.activeStack != null
                value: Cura.MachineManager.activeStack.intent == model.container
            }
            exclusiveGroup: group
            onTriggered: Cura.MachineManager.activeStack.intent = model.container
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }
    ExclusiveGroup { id: group }
}
