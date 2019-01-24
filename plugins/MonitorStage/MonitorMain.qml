// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura


// We show a nice overlay on the 3D viewer when the current output device has no monitor view
Rectangle
{
    id: viewportOverlay

    property bool isConnected: Cura.MachineManager.activeMachineHasActiveNetworkConnection || Cura.MachineManager.activeMachineHasActiveCloudConnection
    property string printerName: Cura.MachineManager.activeMachineDefinitionName
    property bool isNetworkEnabled: ["Ultimaker 3", "Ultimaker 3 Extended", "Ultimaker S5"].indexOf(printerName) > -1

    color: UM.Theme.getColor("viewport_overlay")
    anchors.fill: parent

    // This mouse area is to prevent mouse clicks to be passed onto the scene.
    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onWheel: wheel.accepted = true
    }

    // Disable dropping files into Cura when the monitor page is active
    DropArea
    {
        anchors.fill: parent
    }
    Loader
    {
        id: monitorViewComponent

        anchors.fill: parent

        height: parent.height

        property real maximumWidth: parent.width
        property real maximumHeight: parent.height

        sourceComponent: Cura.MachineManager.printerOutputDevices.length > 0 ? Cura.MachineManager.printerOutputDevices[0].monitorItem : null
    }

    Column
    {
        anchors
        {
            top: parent.top
            topMargin: 67 * screenScaleFactor
            horizontalCenter: parent.horizontalCenter
        }
        width: 480 * screenScaleFactor
        spacing: UM.Theme.getSize("default_margin").height

        Label
        {
            anchors
            {
                horizontalCenter: parent.horizontalCenter
            }
            visible: isNetworkEnabled && !isConnected
            text: "Please smake sure your printer has connection:\n- Check if the printer is turned on.\n- Check if the printer is connected to the network."
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("monitor_text_primary")
            wrapMode: Text.WordWrap
            lineHeight: 28 * screenScaleFactor
            lineHeightMode: Text.FixedHeight
            width: contentWidth
        }

        Cura.PrimaryButton
        {
            anchors
            {
                horizontalCenter: parent.horizontalCenter
            }
            visible: isNetworkEnabled && !isConnected
            text: "Reconnect"
            onClicked:
            {
                // nothing
            }
        }

        Label
        {
            anchors
            {
                horizontalCenter: parent.horizontalCenter
            }
            visible: !isNetworkEnabled
            text: "Please select a network connected printer to monitor the status and queue or connect your Ultimaker printer to your local network."
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("monitor_text_primary")
            wrapMode: Text.WordWrap
            width: parent.width
            lineHeight: 28 * screenScaleFactor
            lineHeightMode: Text.FixedHeight
        }
        Item
        {
            anchors
            {
                left: parent.left
            }
            visible: !isNetworkEnabled
            height: 18 * screenScaleFactor // TODO: Theme!
            width: childrenRect.width

            UM.RecolorImage
            {
                id: externalLinkIcon
                anchors.verticalCenter: parent.verticalCenter
                color: UM.Theme.getColor("monitor_text_link")
                source: UM.Theme.getIcon("external_link")
                width: 16 * screenScaleFactor // TODO: Theme! (Y U NO USE 18 LIKE ALL OTHER ICONS?!)
                height: 16 * screenScaleFactor // TODO: Theme! (Y U NO USE 18 LIKE ALL OTHER ICONS?!)
            }
            Label
            {
                id: manageQueueText
                anchors
                {
                    left: externalLinkIcon.right
                    leftMargin: 6 * screenScaleFactor // TODO: Theme!
                    verticalCenter: externalLinkIcon.verticalCenter
                }
                color: UM.Theme.getColor("monitor_text_link")
                font: UM.Theme.getFont("medium") // 14pt, regular
                linkColor: UM.Theme.getColor("monitor_text_link")
                text: catalog.i18nc("@label link to technical assistance", "More information on connecting the printer")
                renderType: Text.NativeRendering
            }
        }
    }
}