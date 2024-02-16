// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import UM 1.5 as UM
import Cura 1.0 as Cura

// This is the root component for the monitor stage.
Component
{
    Rectangle
    {
        id: monitorFrame

        height: maximumHeight
        onVisibleChanged:
        {
            if (monitorFrame != null && !monitorFrame.visible)
            {
                OutputDevice.setActiveCameraUrl("")
            }
        }
        width: maximumWidth
        color: UM.Theme.getColor("monitor_stage_background")

        // Enable keyboard navigation. NOTE: This is done here so that we can also potentially
        // forward to the queue items in the future. (Deleting selected print job, etc.)
        Keys.forwardTo: carousel
        Component.onCompleted: forceActiveFocus()

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        Item
        {
            id: printers
            visible: !Cura.MachineManager.activeMachineIsAbstractCloudPrinter
            anchors
            {
                top: parent.top
                topMargin: 48 * screenScaleFactor // TODO: Theme!
            }
            width: parent.width
            height: 264 * screenScaleFactor // TODO: Theme!
            MonitorCarousel
            {
                id: carousel
                printers:
                {
                    if (OutputDevice.receivedData)
                    {
                        return OutputDevice.printers
                    }
                    return [null]
                }
            }
        }

        MonitorQueue
        {
            id: queue
            width: Math.min(834 * screenScaleFactor, maximumWidth)
            anchors
            {
                bottom: parent.bottom
                horizontalCenter: parent.horizontalCenter
                top: printers.bottom
                topMargin: 48 * screenScaleFactor // TODO: Theme!
            }
            visible: OutputDevice.supportsPrintJobQueue && OutputDevice.canReadPrintJobs && !Cura.MachineManager.activeMachineIsAbstractCloudPrinter
        }

        PrinterVideoStream
        {
            anchors.fill: parent
            cameraUrl: OutputDevice.activeCameraUrl
            visible: OutputDevice.activeCameraUrl != "" && !Cura.MachineManager.activeMachineIsAbstractCloudPrinter
        }

        Rectangle
        {
            id: sendToFactoryCard

            visible: Cura.MachineManager.activeMachineIsAbstractCloudPrinter

            color: UM.Theme.getColor("monitor_stage_background")
            height: childrenRect.height + UM.Theme.getSize("default_margin").height * 2
            width: childrenRect.width + UM.Theme.getSize("wide_margin").width * 2
            anchors
            {
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: UM.Theme.getSize("wide_margin").height * screenScaleFactor * 2
            }

            Column
            {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                spacing: UM.Theme.getSize("wide_margin").height
                padding: UM.Theme.getSize("default_margin").width
                topPadding: 0

                Image
                {
                    id: sendToFactoryImage
                    anchors.horizontalCenter: parent.horizontalCenter
                    source: UM.Theme.getImage("cura_connected_printers")
                }

                UM.Label
                {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: catalog.i18nc("@info", "Monitor your printers from everywhere using Ultimaker Digital Factory")
                    font: UM.Theme.getFont("medium")
                    width: sendToFactoryImage.width
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                Cura.PrimaryButton
                {
                    id: sendToFactoryButton
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: catalog.i18nc("@button", "View printers in Digital Factory")
                    onClicked: Qt.openUrlExternally("https://digitalfactory.ultimaker.com/app/welcome?utm_source=cura&utm_medium=software&utm_campaign=monitor-view-cloud-printer-type")
                }
            }
        }
    }
}
