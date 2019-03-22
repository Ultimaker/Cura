// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Instantiator
{
    model: Cura.GlobalStacksModel {}

    MenuItem
    {
        text: model.name
        checkable: true
        checked: Cura.MachineManager.activeMachineId == model.id
        exclusiveGroup: group
        visible: !model.hasRemoteConnection
        onTriggered: Cura.MachineManager.setActiveMachine(model.id)
    }
    onObjectAdded: menu.insertItem(index, object)
    onObjectRemoved: menu.removeItem(object)
}
