// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Cura.ExpandableComponent
{
    id: machineSelector

    property bool isNetworkPrinter: Cura.MachineManager.activeMachineNetworkKey != ""
    property var outputDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

    popupPadding: 0
    popupAlignment: Cura.ExpandableComponent.PopupAlignment.AlignLeft
    iconSource: expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    headerItem: Cura.IconLabel
    {
        text: isNetworkPrinter ? Cura.MachineManager.activeMachineNetworkGroupName : Cura.MachineManager.activeMachineName
        source:
        {
            if (isNetworkPrinter && machineSelector.outputDevice != null)
            {
                if (machineSelector.outputDevice.clusterSize > 1)
                {
                    return UM.Theme.getIcon("printer_group")
                }
                return UM.Theme.getIcon("printer_single")
            }
            return ""
        }
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text")
        iconSize: UM.Theme.getSize("machine_selector_icon").width
    }

    popupItem: Item
    {
        id: popup
        width: UM.Theme.getSize("machine_selector_widget_content").width
        height: UM.Theme.getSize("machine_selector_widget_content").height

        ScrollView
        {
            id: scroll
            width: parent.width
            anchors.top: parent.top
            anchors.bottom: separator.top
            clip: true

            Column
            {
                id: column

                // Can't use parent.width since the parent is the flickable component and not the ScrollView
                width: scroll.width - 2 * UM.Theme.getSize("default_lining").width
                x: UM.Theme.getSize("default_lining").width

                Label
                {
                    text: catalog.i18nc("@label", "Network connected printers")
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
                        filter: {"type": "machine", "um_network_key": "*", "hidden": "False"}
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
                        filter: {"type": "machine", "um_network_key": null}
                    }

                    delegate: MachineSelectorButton
                    {
                        text: model.name
                        checked: Cura.MachineManager.activeMachineId == model.id
                    }
                }
            }
        }

        Rectangle
        {
            id: separator

            anchors.bottom: buttonRow.top
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        Row
        {
            id: buttonRow

            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            padding: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").width

            Cura.ActionButton
            {
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Add printer")
                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                onClicked:
                {
                    togglePopup()
                    Cura.Actions.addMachine.trigger()
                }
            }

            Cura.ActionButton
            {
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Manage printers")
                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                onClicked:
                {
                    togglePopup()
                    Cura.Actions.configureMachines.trigger()
                }
            }
        }
    }
}
