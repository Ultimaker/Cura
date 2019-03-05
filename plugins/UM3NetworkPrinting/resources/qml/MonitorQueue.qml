// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
import Cura 1.0 as Cura

/**
 * This component contains the print job queue, extracted from the primary
 * MonitorStage.qml file not for reusability but simply to keep it lean and more
 * readable.
 */
Item
{
    // If the printer is a cloud printer or not. Other items base their enabled state off of this boolean. In the future
    // they might not need to though.
    property bool cloudConnection: Cura.MachineManager.activeMachineIsUsingCloudConnection

    Label
    {
        id: queuedLabel
        anchors
        {
            left: queuedPrintJobs.left
            top: parent.top
        }
        color: UM.Theme.getColor("monitor_text_primary")
        font: UM.Theme.getFont("large")
        text: catalog.i18nc("@label", "Queued")
    }

    Item
    {
        id: manageQueueLabel
        anchors
        {
            right: queuedPrintJobs.right
            verticalCenter: queuedLabel.verticalCenter
        }
        height: 18 * screenScaleFactor // TODO: Theme!
        width: childrenRect.width
        visible: !cloudConnection

        UM.RecolorImage
        {
            id: externalLinkIcon
            anchors.verticalCenter: manageQueueLabel.verticalCenter
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
            text: catalog.i18nc("@label link to connect manager", "Go to Cura Connect")
            renderType: Text.NativeRendering
        }
    }

    MouseArea
    {
        anchors.fill: manageQueueLabel
        enabled: !cloudConnection
        hoverEnabled: !cloudConnection
        onClicked: Cura.MachineManager.printerOutputDevices[0].openPrintJobControlPanel()
        onEntered:
        {
            manageQueueText.font.underline = true
        }
        onExited:
        {
            manageQueueText.font.underline = false
        }
    }

    Row
    {
        id: printJobQueueHeadings
        anchors
        {
            left: queuedPrintJobs.left
            leftMargin: 6 * screenScaleFactor // TODO: Theme!
            top: queuedLabel.bottom
            topMargin: 24 * screenScaleFactor // TODO: Theme!
        }
        spacing: 18 * screenScaleFactor // TODO: Theme!

        Label
        {
            text: catalog.i18nc("@label", "Print jobs")
            color: UM.Theme.getColor("monitor_text_primary")
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium") // 14pt, regular
            anchors.verticalCenter: parent.verticalCenter
            width: 284 * screenScaleFactor // TODO: Theme! (Should match column size)

            // FIXED-LINE-HEIGHT:
            height: 18 * screenScaleFactor // TODO: Theme!
            verticalAlignment: Text.AlignVCenter
        }

        Label
        {
            text: catalog.i18nc("@label", "Total print time")
            color: UM.Theme.getColor("monitor_text_primary")
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium") // 14pt, regular
            anchors.verticalCenter: parent.verticalCenter
            width: 216 * screenScaleFactor // TODO: Theme! (Should match column size)

            // FIXED-LINE-HEIGHT:
            height: 18 * screenScaleFactor // TODO: Theme!
            verticalAlignment: Text.AlignVCenter
        }

        Label
        {
            text: catalog.i18nc("@label", "Waiting for")
            color: UM.Theme.getColor("monitor_text_primary")
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium") // 14pt, regular
            anchors.verticalCenter: parent.verticalCenter
            width: 216 * screenScaleFactor // TODO: Theme! (Should match column size)

            // FIXED-LINE-HEIGHT:
            height: 18 * screenScaleFactor // TODO: Theme!
            verticalAlignment: Text.AlignVCenter
        }
    }

    ScrollView
    {
        id: queuedPrintJobs
        anchors
        {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            top: printJobQueueHeadings.bottom
            topMargin: 12 * screenScaleFactor // TODO: Theme!
        }
        style: UM.Theme.styles.scrollview
        width: parent.width

        ListView
        {
            id: printJobList
            anchors.fill: parent
            delegate: MonitorPrintJobCard
            {
                anchors
                {
                    left: parent.left
                    right: parent.right
                }
                printJob: modelData
            }
            model:
            {
                // When printing over the cloud we don't recieve print jobs until there is one, so
                // unless there's at least one print job we'll be stuck with skeleton loading
                // indefinitely.
                if (Cura.MachineManager.activeMachineIsUsingCloudConnection || OutputDevice.receivedPrintJobs)
                {
                    return OutputDevice.queuedPrintJobs
                }
                return [null, null]
            }
            spacing: 6  // TODO: Theme!
        }
    }

    Rectangle
    {
        anchors
        {
            horizontalCenter: parent.horizontalCenter
            top: printJobQueueHeadings.bottom
            topMargin: 12 * screenScaleFactor // TODO: Theme!
        }
        height: 48 * screenScaleFactor // TODO: Theme!
        width: parent.width
        color: UM.Theme.getColor("monitor_card_background")
        border.color: UM.Theme.getColor("monitor_card_border")
        radius: 2 * screenScaleFactor // TODO: Theme!

        visible: printJobList.model.length == 0

        Row
        {
            anchors
            {
                left: parent.left
                leftMargin: 18 * screenScaleFactor // TODO: Theme!
                verticalCenter: parent.verticalCenter
            }
            spacing: 18 * screenScaleFactor // TODO: Theme!
            height: 18 * screenScaleFactor // TODO: Theme!

            Label
            {
                text: "All jobs are printed."
                color: UM.Theme.getColor("monitor_text_primary")
                font: UM.Theme.getFont("medium") // 14pt, regular
            }

            Item
            {
                id: viewPrintHistoryLabel
                
                height: 18 * screenScaleFactor // TODO: Theme!
                width: childrenRect.width
                visible: !cloudConnection

                UM.RecolorImage
                {
                    id: printHistoryIcon
                    anchors.verticalCenter: parent.verticalCenter
                    color: UM.Theme.getColor("monitor_text_link")
                    source: UM.Theme.getIcon("external_link")
                    width: 16 * screenScaleFactor // TODO: Theme! (Y U NO USE 18 LIKE ALL OTHER ICONS?!)
                    height: 16 * screenScaleFactor // TODO: Theme! (Y U NO USE 18 LIKE ALL OTHER ICONS?!)
                }
                Label
                {
                    id: viewPrintHistoryText
                    anchors
                    {
                        left: printHistoryIcon.right
                        leftMargin: 6 * screenScaleFactor // TODO: Theme!
                        verticalCenter: printHistoryIcon.verticalCenter
                    }
                    color: UM.Theme.getColor("monitor_text_link")
                    font: UM.Theme.getFont("medium") // 14pt, regular
                    linkColor: UM.Theme.getColor("monitor_text_link")
                    text: catalog.i18nc("@label link to connect manager", "View print history")
                    renderType: Text.NativeRendering
                }
                MouseArea
                {
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: Cura.MachineManager.printerOutputDevices[0].openPrintJobControlPanel()
                    onEntered:
                    {
                        viewPrintHistoryText.font.underline = true
                    }
                    onExited:
                    {
                        viewPrintHistoryText.font.underline = false
                    }
                }
            }
        }
    }
}
