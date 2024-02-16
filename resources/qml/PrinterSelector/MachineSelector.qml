// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura

Cura.ExpandablePopup
{
    id: machineSelector

    property var machineManager: Cura.MachineManager
    property bool isNetworkPrinter: machineManager.activeMachineHasNetworkConnection
    property bool isConnectedCloudPrinter: machineManager.activeMachineHasCloudConnection
    property bool isCloudRegistered: machineManager.activeMachineHasCloudRegistration
    property bool isGroup: machineManager.activeMachineIsGroup
    property string machineName: {
        if (isNetworkPrinter && machineManager.activeMachineNetworkGroupName != "")
        {
            return machineManager.activeMachineNetworkGroupName
        }
        if (machineManager.activeMachine != null)
        {
            return machineManager.activeMachine.name
        }
        return ""
    }

    property alias machineListModel: machineSelectorList.model
    property alias onSelectPrinter: machineSelectorList.onSelectPrinter

    property list<Item> buttons

    property string connectionStatus: {
        if (isNetworkPrinter)
        {
            return "printer_connected"
        }
        else if (isConnectedCloudPrinter && Cura.API.connectionStatus.isInternetReachable)
        {
            return "printer_cloud_connected"
        }
        else if (isCloudRegistered)
        {
            return "printer_cloud_not_available"
        }
        else
        {
            return ""
        }
    }

    function getConnectionStatusMessage() {
        if (connectionStatus == "printer_cloud_not_available")
        {
            if(Cura.API.connectionStatus.isInternetReachable)
            {
                if (Cura.API.account.isLoggedIn)
                {
                    if (machineManager.activeMachineIsLinkedToCurrentAccount)
                    {
                        return catalog.i18nc("@status", "The cloud printer is offline. Please check if the printer is turned on and connected to the internet.")
                    }
                    else
                    {
                        return catalog.i18nc("@status", "This printer is not linked to your account. Please visit the Ultimaker Digital Factory to establish a connection.")
                    }
                }
                else
                {
                    return catalog.i18nc("@status", "The cloud connection is currently unavailable. Please sign in to connect to the cloud printer.")
                }
            }
            else
            {
                return catalog.i18nc("@status", "The cloud connection is currently unavailable. Please check your internet connection.")
            }
        }
        else
        {
            return ""
        }
    }

    contentPadding: UM.Theme.getSize("default_lining").width
    contentAlignment: Cura.ExpandablePopup.ContentAlignment.AlignLeft

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    headerItem: Cura.IconWithText
    {
        text: machineName

        source:
        {
            if (isGroup)
            {
                return UM.Theme.getIcon("PrinterTriple", "medium")
            }
            else if (isNetworkPrinter || isCloudRegistered)
            {
                return UM.Theme.getIcon("Printer", "medium")
            }

            else
            {
                return ""
            }
        }
        font: UM.Theme.getFont("medium")
        iconColor: UM.Theme.getColor("machine_selector_printer_icon")
        iconSize: source != "" ? UM.Theme.getSize("machine_selector_icon").width: 0

        UM.ColorImage
        {
            id: connectionStatusImage
            anchors
            {
                bottom: parent.bottom
                bottomMargin: - Math.round(height * 1 / 6)
                left: parent.left
                leftMargin: iconSize - Math.round(width * 5 / 6)
            }

            source:
            {
                if (connectionStatus == "printer_connected")
                {
                    return UM.Theme.getIcon("CheckBlueBG", "low")
                }
                else if (connectionStatus == "printer_cloud_connected" || connectionStatus == "printer_cloud_not_available")
                {
                    return UM.Theme.getIcon("CloudBadge", "low")
                }
                else
                {
                    return ""
                }
            }

            width: UM.Theme.getSize("printer_status_icon").width
            height: UM.Theme.getSize("printer_status_icon").height

            color: connectionStatus == "printer_cloud_not_available" ? UM.Theme.getColor("cloud_unavailable") : UM.Theme.getColor("primary")

            visible: (isNetworkPrinter || isCloudRegistered) && source != ""

            // Make a themable circle in the background so we can change it in other themes
            Rectangle
            {
                id: iconBackground
                anchors.centerIn: parent
                width: parent.width - 1.5  //1.5 pixels smaller, (at least sqrt(2), regardless of screen pixel scale) so that the circle doesn't show up behind the icon due to anti-aliasing.
                height: parent.height - 1.5
                radius: width / 2
                color: UM.Theme.getColor("connection_badge_background")
                z: parent.z - 1
            }

        }

        // Connection status tooltip hover area
        MouseArea
        {
            id: connectionStatusTooltipHoverArea
            anchors.fill: parent
            hoverEnabled: getConnectionStatusMessage() !== ""
            acceptedButtons: Qt.NoButton // react to hover only, don't steal clicks

            onEntered:
            {
                machineSelector.mouseArea.entered() // we want both this and the outer area to be entered
                tooltip.tooltipText = getConnectionStatusMessage()
                tooltip.show()
            }
            onExited: { tooltip.hide() }
        }

        UM.ToolTip
        {
            id: tooltip

            width: 250 * screenScaleFactor
            tooltipText: getConnectionStatusMessage()
            arrowSize: UM.Theme.getSize("button_tooltip_arrow").width
            x: connectionStatusImage.x - UM.Theme.getSize("narrow_margin").width
            y: connectionStatusImage.y + connectionStatusImage.height + UM.Theme.getSize("narrow_margin").height
            z: popup.z + 1
            targetPoint: Qt.point(
                connectionStatusImage.x + Math.round(connectionStatusImage.width / 2),
                connectionStatusImage.y
            )
        }
    }

    property int minDropDownWidth: UM.Theme.getSize("machine_selector_widget_content").width
    property int maxDropDownHeight: UM.Theme.getSize("machine_selector_widget_content").height

    contentItem: Item
    {
        id: popup
        implicitWidth: Math.max(machineSelector.width, minDropDownWidth)
        implicitHeight: Math.min(machineSelectorList.contentHeight + separator.height + buttonRow.height, maxDropDownHeight) //Maximum height is the theme entry.
        MachineSelectorList
        {
            id: machineSelectorList
            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("default_lining").width
                right: parent.right
                rightMargin: UM.Theme.getSize("default_lining").width
                top: parent.top
                bottom: separator.top
            }
            clip: true
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
            anchors.left: parent.left
            anchors.right: parent.right

            padding: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").width

            children: buttons
        }

        states: [
            State {
                name: "noButtons"
                when: !buttons || buttons.length == 0
                PropertyChanges
                {
                    target: buttonRow
                    height: 0
                    padding: 0
                }
                PropertyChanges
                {
                    target: separator
                    height: 0
                }
            }
        ]
    }
}
