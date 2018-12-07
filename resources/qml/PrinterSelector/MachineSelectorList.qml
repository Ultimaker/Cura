// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: machineSelectorList

    Label
    {
        text: catalog.i18nc("@label", "Connected printers")
        visible: networkedPrintersModel.items.length > 0
        leftPadding: UM.Theme.getSize("default_margin").width
        height: visible ? contentHeight + 2 * UM.Theme.getSize("default_margin").height : 0
        renderType: Text.NativeRendering
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text_medium")
        verticalAlignment: Text.AlignVCenter
    }

    Repeater
    {
        id: networkedPrinters

        model: UM.ContainerStacksModel
        {
            id: networkedPrintersModel
            filter:
            {
                "type": "machine", "um_network_key": "*", "hidden": "False"
            }
        }

        delegate: MachineSelectorButton
        {
            text: model.metadata["connect_group_name"]
            checked: Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
            outputDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

            Connections
            {
                target: Cura.MachineManager
                onActiveMachineNetworkGroupNameChanged: checked = Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
            }
        }
    }

    Label
    {
        text: catalog.i18nc("@label", "Preset printers")
        visible: virtualPrintersModel.items.length > 0
        leftPadding: UM.Theme.getSize("default_margin").width
        height: visible ? contentHeight + 2 * UM.Theme.getSize("default_margin").height : 0
        renderType: Text.NativeRendering
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text_medium")
        verticalAlignment: Text.AlignVCenter
    }

    Repeater
    {
        id: virtualPrinters

        model: UM.ContainerStacksModel
        {
            id: virtualPrintersModel
            filter:
            {
                "type": "machine", "um_network_key": null
            }
        }

        delegate: MachineSelectorButton
        {
            text: model.name
            checked: Cura.MachineManager.activeMachineId == model.id
        }
    }
}