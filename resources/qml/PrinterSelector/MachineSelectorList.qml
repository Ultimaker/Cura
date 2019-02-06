// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

ListView
{
    id: listView
    model: Cura.GlobalStacksModel {}
    section.property: "hasRemoteConnection"
    property real contentHeight: childrenRect.height

    section.delegate: Label
    {
        text: section == "true" ? catalog.i18nc("@label", "Connected printers") : catalog.i18nc("@label", "Preset printers")
        width: parent.width
        height: UM.Theme.getSize("action_button").height
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
        outputDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

        checked:
        {
            // If the machine has a remote connection
            var result = Cura.MachineManager.activeMachineId == model.id
            if (Cura.MachineManager.activeMachineHasRemoteConnection)
            {
                result |= Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["group_name"]
            }
            return result
        }
    }
}
