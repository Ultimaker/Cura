// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Cura.ExpandablePopup
{
    id: machineSelector

    property bool isNetworkPrinter: Cura.MachineManager.activeMachineHasNetworkConnection
    property bool isCloudPrinter: Cura.MachineManager.activeMachineHasCloudConnection
    property bool isGroup: Cura.MachineManager.activeMachineIsGroup

    contentPadding: UM.Theme.getSize("default_lining").width
    contentAlignment: Cura.ExpandablePopup.ContentAlignment.AlignLeft

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    headerItem: Cura.IconWithText
    {
        text:
        {
            if (isNetworkPrinter && Cura.MachineManager.activeMachineNetworkGroupName != "")
            {
                return Cura.MachineManager.activeMachineNetworkGroupName
            }
            if(Cura.MachineManager.activeMachine != null)
            {
                return Cura.MachineManager.activeMachine.name
            }
            return ""
        }
        source:
        {
            if (isGroup)
            {
                return UM.Theme.getIcon("printer_group")
            }
            else if (isNetworkPrinter || isCloudPrinter)
            {
                return UM.Theme.getIcon("printer_single")
            }
            else
            {
                return ""
            }
        }
        font: UM.Theme.getFont("medium")
        iconColor: UM.Theme.getColor("machine_selector_printer_icon")
        iconSize: source != "" ? UM.Theme.getSize("machine_selector_icon").width: 0

        UM.RecolorImage
        {
            anchors
            {
                bottom: parent.bottom
                left: parent.left
                leftMargin: UM.Theme.getSize("thick_margin").width
            }

            source:
            {
                if (isNetworkPrinter)
                {
                    return UM.Theme.getIcon("printer_connected")
                }
                else if (isCloudPrinter)
                {
                    return UM.Theme.getIcon("printer_cloud_connected")
                }
                else
                {
                    return ""
                }
            }

            width: UM.Theme.getSize("printer_status_icon").width
            height: UM.Theme.getSize("printer_status_icon").height

            color: UM.Theme.getColor("primary")
            visible: isNetworkPrinter || isCloudPrinter

            // Make a themable circle in the background so we can change it in other themes
            Rectangle
            {
                id: iconBackground
                anchors.centerIn: parent
                // Make it a bit bigger so there is an outline
                width: parent.width + 2 * UM.Theme.getSize("default_lining").width
                height: parent.height + 2 * UM.Theme.getSize("default_lining").height
                radius: Math.round(width / 2)
                color: UM.Theme.getColor("main_background")
                z: parent.z - 1
            }
        }
    }

    contentItem: Item
    {
        id: popup
        width: UM.Theme.getSize("machine_selector_widget_content").width

        ScrollView
        {
            id: scroll
            width: parent.width
            clip: true
            leftPadding: UM.Theme.getSize("default_lining").width
            rightPadding: UM.Theme.getSize("default_lining").width

            MachineSelectorList
            {
                id: machineSelectorList
                // Can't use parent.width since the parent is the flickable component and not the ScrollView
                width: scroll.width - scroll.leftPadding - scroll.rightPadding
                property real maximumHeight: UM.Theme.getSize("machine_selector_widget_content").height - buttonRow.height

                // We use an extra property here, since we only want to to be informed about the content size changes.
                onContentHeightChanged:
                {
                    scroll.height = Math.min(contentHeight, maximumHeight)
                    popup.height = scroll.height + buttonRow.height
                }

                Component.onCompleted:
                {
                    scroll.height = Math.min(contentHeight, maximumHeight)
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

            Cura.SecondaryButton
            {
                id: addPrinterButton
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Add printer")
                // The maximum width of the button is half of the total space, minus the padding of the parent, the left
                // padding of the component and half the spacing because of the space between buttons.
                maximumWidth: UM.Theme.getSize("machine_selector_widget_content").width / 2 - parent.padding - leftPadding - parent.spacing / 2
                onClicked:
                {
                    toggleContent()
                    Cura.Actions.addMachine.trigger()
                }
            }

            Cura.SecondaryButton
            {
                id: managePrinterButton
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Manage printers")
                // The maximum width of the button is half of the total space, minus the padding of the parent, the right
                // padding of the component and half the spacing because of the space between buttons.
                maximumWidth: UM.Theme.getSize("machine_selector_widget_content").width / 2 - parent.padding - rightPadding - parent.spacing / 2
                onClicked:
                {
                    toggleContent()
                    Cura.Actions.configureMachines.trigger()
                }
            }
        }
    }
}
