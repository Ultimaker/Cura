// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Printer type"
    property var outputDevice: Cura.MachineManager.printerOutputDevices[0]

    Instantiator
    {
        id: printerTypeInstantiator
        model: outputDevice != null ? outputDevice.connectedPrintersTypeCount : []

        MenuItem
        {
            text: modelData.machine_type
            checkable: true
            checked: Cura.MachineManager.activeMachine.definition.name == modelData.machine_type
            exclusiveGroup: group
            onTriggered:
            {
                Cura.MachineManager.switchPrinterType(modelData.machine_type)
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group }
}
