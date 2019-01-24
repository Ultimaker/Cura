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
    Label
    {
        id: queuedLabel
        anchors
        {
            left: queuedPrintJobs.left
            top: parent.top
        }
        color: UM.Theme.getColor("text")
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

        UM.RecolorImage
        {
            id: externalLinkIcon
            anchors.verticalCenter: manageQueueLabel.verticalCenter
            color: UM.Theme.getColor("text_link")
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
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("default") // 12pt, regular
            linkColor: UM.Theme.getColor("text_link")
            text: catalog.i18nc("@label link to connect manager", "Manage queue in Cura Connect")
            renderType: Text.NativeRendering
        }
    }

    MouseArea
    {
        anchors.fill: manageQueueLabel
        hoverEnabled: true
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
            color: "#666666"
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
            color: "#666666"
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
            color: "#666666"
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
            model: OutputDevice.receivedPrintJobs ? OutputDevice.queuedPrintJobs : [null,null]
            spacing: 6  // TODO: Theme!
        }
    }
}