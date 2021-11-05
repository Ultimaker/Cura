// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
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
            visible: OutputDevice.supportsPrintJobQueue
        }

        PrinterVideoStream
        {
            anchors.fill: parent
            cameraUrl: OutputDevice.activeCameraUrl
            visible: OutputDevice.activeCameraUrl != ""
        }
    }
}
