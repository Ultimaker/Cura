// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu;

    Instantiator
    {
        model: UM.ContainerStacksModel
        {
            filter: {"type": "machine"}
        }
        MenuItem
        {
            text: model.name;
            checkable: true;
            checked: Cura.MachineManager.activeMachineId == model.id
            exclusiveGroup: group;
            onTriggered: Cura.MachineManager.setActiveMachine(model.id);
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group; }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.addMachine; }
    MenuItem { action: Cura.Actions.configureMachines; }
}
