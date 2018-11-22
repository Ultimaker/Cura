// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
import Cura 1.0 as Cura
import QtGraphicalEffects 1.0

Component
{
    Rectangle
    {
        id: monitorFrame

        property var emphasisColor: UM.Theme.getColor("setting_control_border_highlight")
        property var cornerRadius: UM.Theme.getSize("monitor_corner_radius").width

        color: "transparent"
        height: maximumHeight
        onVisibleChanged:
        {
            if (monitorFrame != null && !monitorFrame.visible)
            {
                OutputDevice.setActiveCameraUrl("")
            }
        }
        width: maximumWidth

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        LinearGradient {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop {
                    position: 0.0
                    color: "#f6f6f6"
                }
                GradientStop {
                    position: 1.0
                    color: "#ffffff"
                }
            }
        }

        Item
        {
            id: queue

            anchors.fill: parent
            anchors.top: parent.top
            anchors.topMargin: 400 * screenScaleFactor // TODO: Insert carousel here

            Label
            {
                id: queuedLabel
                anchors
                {
                    left: queuedPrintJobs.left
                    top: parent.top
                }
                color: UM.Theme.getColor("text")
                font: UM.Theme.getFont("large_nonbold")
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
                    color: UM.Theme.getColor("primary")
                    source: "../svg/icons/external_link.svg"
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
                    color: UM.Theme.getColor("primary")
                    font: UM.Theme.getFont("default")
                    linkColor: UM.Theme.getColor("primary")
                    text: catalog.i18nc("@label link to connect manager", "Manage queue in Cura Connect")
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
                anchors {
                    bottom: parent.bottom
                    horizontalCenter: parent.horizontalCenter
                    top: printJobQueueHeadings.bottom
                    topMargin: 12 * screenScaleFactor // TODO: Theme!
                }
                style: UM.Theme.styles.scrollview
                visible: OutputDevice.receivedPrintJobs
                width: Math.min(834 * screenScaleFactor, maximumWidth)

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
                    model: OutputDevice.queuedPrintJobs
                    spacing: 6
                }
            }
        }

        PrinterVideoStream {
            anchors.fill: parent
            cameraUrl: OutputDevice.activeCameraUrl
            visible: OutputDevice.activeCameraUrl != ""
        }
    }
    
}
