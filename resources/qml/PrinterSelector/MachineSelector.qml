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
    property bool isPrinterConnected: Cura.MachineManager.printerConnected
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
            if (isNetworkPrinter)
            {
                if (machineSelector.outputDevice != null && machineSelector.outputDevice.clusterSize > 1)
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

        UM.RecolorImage
        {
            id: icon

            anchors.bottom: parent.bottom
            x: UM.Theme.getSize("thick_margin").width

            source: UM.Theme.getIcon("printer_connected")
            width: UM.Theme.getSize("printer_status_icon").width
            height: UM.Theme.getSize("printer_status_icon").height

            sourceSize.width: width
            sourceSize.height: height

            color: UM.Theme.getColor("primary")
            visible: isNetworkPrinter && isPrinterConnected

            // Make a themable circle in the background so we can change it in other themes
            Rectangle
            {
                id: iconBackground
                anchors.centerIn: parent
                // Make it a bit bigger so there is an outline
                width: parent.width + 2
                height: parent.height + 2
                radius: Math.round(width / 2)
                color: UM.Theme.getColor("main_background")
                z: parent.z - 1
            }
        }
    }

    popupItem: Item
    {
        id: popup
        width: UM.Theme.getSize("machine_selector_widget_content").width

        ScrollView
        {
            id: scroll
            width: parent.width
            clip: true

            MachineSelectorList
            {
                // Can't use parent.width since the parent is the flickable component and not the ScrollView
                width: scroll.width - 2 * UM.Theme.getSize("default_lining").width
                x: UM.Theme.getSize("default_lining").width
                property real maximumHeight: UM.Theme.getSize("machine_selector_widget_content").height - buttonRow.height

                onHeightChanged:
                {
                    scroll.height = Math.min(height, maximumHeight)
                    popup.height = scroll.height + buttonRow.height
                }
            }
        }

        Rectangle
        {
            id: separator

            anchors.top: scroll.bottom
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        Row
        {
            id: buttonRow

            // The separator is inside the buttonRow. This is to avoid some weird behaviours with the scroll bar.
            anchors.top: separator.top
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
