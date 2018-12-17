// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
import Cura 1.0 as Cura
import QtGraphicalEffects 1.0

// This is the root component for the monitor stage.
Component
{
    Item
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

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        LinearGradient
        {
            anchors.fill: parent
            gradient: Gradient
            {
                GradientStop
                {
                    position: 0.0
                    color: "#f6f6f6" // TODO: Theme!
                }
                GradientStop
                {
                    position: 1.0
                    color: "#ffffff" // TODO: Theme!
                }
            }
        }

        ScrollView
        {
            id: printers
            anchors
            {
                left: queue.left
                right: queue.right
                top: parent.top
                topMargin: 48 * screenScaleFactor // TODO: Theme!
            }
            height: 264 * screenScaleFactor // TODO: Theme!

            Row
            {
                spacing: 60 * screenScaleFactor // TODO: Theme!
                
                Repeater
                {
                    model: OutputDevice.printers

                    MonitorPrinterCard
                    {
                        printer: modelData
                    }
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
        }

        PrinterVideoStream
        {
            anchors.fill: parent
            cameraUrl: OutputDevice.activeCameraUrl
            visible: OutputDevice.activeCameraUrl != ""
        }
    }
}
