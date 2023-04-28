// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: menu
    title: "Printer type"
    property var outputDevice: Cura.MachineManager.printerOutputDevices[0]

    Instantiator
    {
        id: printerTypeInstantiator
        model: outputDevice != null ? outputDevice.connectedPrintersTypeCount : []

        Cura.MenuItem
        {
            text: modelData.machine_type
            checkable: true
            checked: Cura.MachineManager.activeMachine.definition.name == modelData.machine_type
            onTriggered:
            {
                Cura.MachineManager.switchPrinterType(modelData.machine_type)
            }
        }
        onObjectAdded: function(index, object) { return menu.insertItem(index, object); }
        onObjectRemoved: function(index, object) { return menu.removeItem(object); }
    }
}
