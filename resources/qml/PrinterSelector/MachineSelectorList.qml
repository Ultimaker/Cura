// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

ListView
{
    id: listView
    height: childrenRect.height
    width: 200
    model: Cura.PrintersModel {}
    section.property: "hasRemoteConnection"

    section.delegate: Label
    {
        text: section == "true" ? catalog.i18nc("@label", "Connected printers") : catalog.i18nc("@label", "Preset printers")
        width: parent.width
        leftPadding: UM.Theme.getSize("default_margin").width
        renderType: Text.NativeRendering
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text_medium")
        verticalAlignment: Text.AlignVCenter
    }

    delegate: MachineSelectorButton
    {
        text: model.name
        width: listView.width
    }
}
    /*



    Repeater
    {
        id: networkedPrinters

        model: Cura.PrintersModel
        {
            id: networkedPrintersModel
        }

        delegate: MachineSelectorButton
        {
            text: model.name //model.metadata["connect_group_name"]
            //checked: Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
            outputDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

            Connections
            {
                target: Cura.MachineManager
                onActiveMachineNetworkGroupNameChanged: checked = Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
            }
        }
    }*/

