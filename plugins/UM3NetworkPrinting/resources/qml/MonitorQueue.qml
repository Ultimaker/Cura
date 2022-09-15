// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.15
import UM 1.5 as UM
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

    UM.Label
    {
        id: queuedLabel
        anchors
        {
            left: printJobList.left
            top: parent.top
        }
        font: UM.Theme.getFont("large")
        text: catalog.i18nc("@label", "Queued")
    }

    Item
    {
        id: manageQueueLabel
        anchors
        {
            right: printJobList.right
            verticalCenter: queuedLabel.verticalCenter
        }
        height: 18 * screenScaleFactor // TODO: Theme!
        width: childrenRect.width
        visible: OutputDevice.canReadPrinterDetails

        UM.ColorImage
        {
            id: externalLinkIcon
            anchors.verticalCenter: manageQueueLabel.verticalCenter
            color: UM.Theme.getColor("text_link")
            source: UM.Theme.getIcon("LinkExternal")
            width: 16 * screenScaleFactor // TODO: Theme! (Y U NO USE 18 LIKE ALL OTHER ICONS?!)
            height: 16 * screenScaleFactor // TODO: Theme! (Y U NO USE 18 LIKE ALL OTHER ICONS?!)
        }
        UM.Label
        {
            id: manageQueueText
            anchors
            {
                left: externalLinkIcon.right
                leftMargin: UM.Theme.getSize("narrow_margin").width
                verticalCenter: externalLinkIcon.verticalCenter
            }
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("medium") // 14pt, regular
            text: catalog.i18nc("@label link to connect manager", "Manage in browser")
        }
    }

    MouseArea
    {
        anchors.fill: manageQueueLabel
        onClicked: OutputDevice.openPrintJobControlPanel()
        onEntered: manageQueueText.font.underline = true

        onExited: manageQueueText.font.underline = false
    }

    Row
    {
        id: printJobQueueHeadings
        anchors
        {
            left: printJobList.left
            leftMargin: UM.Theme.getSize("narrow_margin").width
            top: queuedLabel.bottom
            topMargin: 24 * screenScaleFactor // TODO: Theme!
        }
        spacing: 18 * screenScaleFactor // TODO: Theme!

        UM.Label
        {
            text: catalog.i18nc("@label", "There are no print jobs in the queue. Slice and send a job to add one.")
            font: UM.Theme.getFont("medium")
            anchors.verticalCenter: parent.verticalCenter
            visible: printJobList.count === 0
        }

        UM.Label
        {
            text: catalog.i18nc("@label", "Print jobs")
            font: UM.Theme.getFont("medium") // 14pt, regular
            anchors.verticalCenter: parent.verticalCenter
            width: 284 * screenScaleFactor // TODO: Theme! (Should match column size)
            visible: printJobList.count > 0
        }

        UM.Label
        {
            text: catalog.i18nc("@label", "Total print time")
            font: UM.Theme.getFont("medium") // 14pt, regular
            anchors.verticalCenter: parent.verticalCenter
            width: UM.Theme.getSize("monitor_column").width
            visible: printJobList.count > 0
        }

        UM.Label
        {
            text: catalog.i18nc("@label", "Waiting for")
            font: UM.Theme.getFont("medium") // 14pt, regular
            anchors.verticalCenter: parent.verticalCenter
            width: UM.Theme.getSize("monitor_column").width
            visible: printJobList.count > 0
        }
    }

    ListView
    {
        id: printJobList
        anchors
        {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            top: printJobQueueHeadings.bottom
            topMargin: UM.Theme.getSize("default_margin").width
        }
        width: parent.width

        ScrollBar.vertical: UM.ScrollBar
        {
            id: printJobScrollBar
        }
        spacing: UM.Theme.getSize("narrow_margin").width
        clip: true

        delegate: MonitorPrintJobCard
        {
            anchors
            {
                left: parent.left
                right: parent.right
                rightMargin: printJobScrollBar.width
            }
            printJob: modelData
        }
        model:
        {
            if (OutputDevice.receivedData)
            {
                return OutputDevice.queuedPrintJobs
            }
            return [null, null]
        }
    }
}
