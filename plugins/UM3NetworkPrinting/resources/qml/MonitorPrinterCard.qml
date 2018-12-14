// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.1
import UM 1.3 as UM

/**
 * A Printer Card is has two main components: the printer portion and the print
 * job portion, the latter being paired in the UI when a print job is paired
 * a printer in-cluster.
 *
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    id: base

    // The printer which all printer data is derived from
    property var printer: null

    property var borderSize: 1 * screenScaleFactor // TODO: Theme, and remove from here

    // If the printer card's controls are enabled. This is used by the carousel
    // to prevent opening the context menu or camera while the printer card is not
    // "in focus"
    property var enabled: true

    width: 834 * screenScaleFactor // TODO: Theme!
    height: childrenRect.height

    // Printer portion
    Rectangle
    {
        id: printerInfo
        border
        {
            color: "#CCCCCC" // TODO: Theme!
            width: borderSize // TODO: Remove once themed
        }
        color: "white" // TODO: Theme!
        width: parent.width
        height: 144 * screenScaleFactor // TODO: Theme!

        Row
        {
            anchors
            {
                left: parent.left
                leftMargin: 36 * screenScaleFactor // TODO: Theme!
                verticalCenter: parent.verticalCenter
            }
            spacing: 18 * screenScaleFactor // TODO: Theme!

            Image
            {
                id: printerImage
                width: 108 * screenScaleFactor // TODO: Theme!
                height: 108 * screenScaleFactor // TODO: Theme!
                fillMode: Image.PreserveAspectFit
                source: "../png/" + printer.type + ".png"
                mipmap: true
            }

            Item
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                width: 180 * screenScaleFactor // TODO: Theme!
                height: printerNameLabel.height + printerFamilyPill.height + 6 * screenScaleFactor // TODO: Theme!

                Label
                {
                    id: printerNameLabel
                    text: printer && printer.name ? printer.name : ""
                    color: "#414054" // TODO: Theme!
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("large") // 16pt, bold
                    width: parent.width

                    // FIXED-LINE-HEIGHT:
                    height: 18 * screenScaleFactor // TODO: Theme!
                    verticalAlignment: Text.AlignVCenter
                }

                MonitorPrinterPill
                {
                    id: printerFamilyPill
                    anchors
                    {
                        top: printerNameLabel.bottom
                        topMargin: 6 * screenScaleFactor // TODO: Theme!
                        left: printerNameLabel.left
                    }
                    text: printer.type
                }
            }

            MonitorPrinterConfiguration
            {
                id: printerConfiguration
                anchors.verticalCenter: parent.verticalCenter
                buildplate: "Glass"
                configurations:
                [
                    base.printer.printerConfiguration.extruderConfigurations[0],
                    base.printer.printerConfiguration.extruderConfigurations[1]
                ]
                height: 72 * screenScaleFactor // TODO: Theme!
            }
        }

        PrintJobContextMenu
        {
            id: contextButton
            anchors
            {
                right: parent.right
                rightMargin: 12 * screenScaleFactor // TODO: Theme!
                top: parent.top
                topMargin: 12 * screenScaleFactor // TODO: Theme!
            }
            printJob: printer.activePrintJob
            width: 36 * screenScaleFactor // TODO: Theme!
            height: 36 * screenScaleFactor // TODO: Theme!
            enabled: base.enabled
        }
        CameraButton
        {
            id: cameraButton;
            anchors
            {
                right: parent.right
                rightMargin: 20 * screenScaleFactor // TODO: Theme!
                bottom: parent.bottom
                bottomMargin: 20 * screenScaleFactor // TODO: Theme!
            }
            iconSource: "../svg/icons/camera.svg"
            enabled: base.enabled
        }
    }


    // Print job portion
    Rectangle
    {
        id: printJobInfo
        anchors
        {
            top: printerInfo.bottom
            topMargin: -borderSize * screenScaleFactor // TODO: Theme!
        }
        border
        {
            color: printer.activePrintJob && printer.activePrintJob.configurationChanges.length > 0 ? "#f5a623" : "#CCCCCC" // TODO: Theme!
            width: borderSize // TODO: Remove once themed
        }
        color: "white" // TODO: Theme!
        height: 84 * screenScaleFactor + borderSize // TODO: Remove once themed
        width: parent.width

        Row
        {
            anchors
            {
                fill: parent
                topMargin: 12 * screenScaleFactor + borderSize // TODO: Theme!
                bottomMargin: 12 * screenScaleFactor // TODO: Theme!
                leftMargin: 36 * screenScaleFactor // TODO: Theme!
            }
            height: childrenRect.height
            spacing: 18 * screenScaleFactor // TODO: Theme!

            Label
            {
                id: printerStatus
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                color: "#414054" // TODO: Theme!
                font: UM.Theme.getFont("large") // 16pt, bold
                text: {
                    if (printer && printer.state == "disabled")
                    {
                        return catalog.i18nc("@label:status", "Unavailable")
                    }
                    if (printer && printer.state == "unreachable")
                    {
                        return catalog.i18nc("@label:status", "Unavailable")
                    }
                    if (printer && !printer.activePrintJob && printer.state == "idle")
                    {
                        return catalog.i18nc("@label:status", "Idle")
                    }
                    return ""
                }
                visible: text !== ""
            }

            Item
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                width: printerImage.width
                height: 60 * screenScaleFactor // TODO: Theme!
                MonitorPrintJobPreview
                {
                    anchors.centerIn: parent
                    printJob: base.printer.activePrintJob
                    size: parent.height
                }
                visible: printer.activePrintJob
            }

            Item
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                width: 180 * screenScaleFactor // TODO: Theme!
                height: printerNameLabel.height + printerFamilyPill.height + 6 * screenScaleFactor // TODO: Theme!
                visible: printer.activePrintJob

                Label
                {
                    id: printerJobNameLabel
                    color: printer.activePrintJob && printer.activePrintJob.isActive ? "#414054" : "#babac1" // TODO: Theme!
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("large") // 16pt, bold
                    text: base.printer.activePrintJob ? base.printer.activePrintJob.name : "Untitled" // TODO: I18N
                    width: parent.width

                    // FIXED-LINE-HEIGHT:
                    height: 18 * screenScaleFactor // TODO: Theme!
                    verticalAlignment: Text.AlignVCenter
                }

                Label
                {
                    id: printerJobOwnerLabel
                    anchors
                    {
                        top: printerJobNameLabel.bottom
                        topMargin: 6 * screenScaleFactor // TODO: Theme!
                        left: printerJobNameLabel.left
                    }
                    color: printer.activePrintJob && printer.activePrintJob.isActive ? "#53657d" : "#babac1" // TODO: Theme!
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("default") // 12pt, regular
                    text: printer.activePrintJob ? printer.activePrintJob.owner : "Anonymous" // TODO: I18N
                    width: parent.width

                    // FIXED-LINE-HEIGHT:
                    height: 18 * screenScaleFactor // TODO: Theme!
                    verticalAlignment: Text.AlignVCenter
                }
            }

            MonitorPrintJobProgressBar
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                printJob: printer.activePrintJob
                visible: printer.activePrintJob && printer.activePrintJob.configurationChanges.length === 0
            }

            Label
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                font: UM.Theme.getFont("default")
                text: "Requires configuration changes"
                visible: printer.activePrintJob && printer.activePrintJob.configurationChanges.length > 0

                // FIXED-LINE-HEIGHT:
                height: 18 * screenScaleFactor // TODO: Theme!
                verticalAlignment: Text.AlignVCenter
            }
        }

        Button
        {
            id: detailsButton
            anchors
            {
                verticalCenter: parent.verticalCenter
                right: parent.right
                rightMargin: 18 * screenScaleFactor // TODO: Theme!
            }
            background: Rectangle
            {
                color: "#d8d8d8" // TODO: Theme!
                radius: 2 * screenScaleFactor // Todo: Theme!
                Rectangle
                {
                    anchors.fill: parent
                    anchors.bottomMargin: 2 * screenScaleFactor // TODO: Theme!
                    color: detailsButton.hovered ? "#e4e4e4" : "#f0f0f0" // TODO: Theme!
                    radius: 2 * screenScaleFactor // Todo: Theme!
                }
            }
            contentItem: Label
            {
                anchors.fill: parent
                anchors.bottomMargin: 2 * screenScaleFactor // TODO: Theme!
                color: "#1e66d7" // TODO: Theme!
                font: UM.Theme.getFont("medium") // 14pt, regular
                text: "Details" // TODO: I18NC!
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                height: 18 * screenScaleFactor // TODO: Theme!
            }
            implicitHeight: 32 * screenScaleFactor // TODO: Theme!
            implicitWidth: 96 * screenScaleFactor // TODO: Theme!
            visible: printer.activePrintJob && printer.activePrintJob.configurationChanges.length > 0
            onClicked: base.enabled ? overrideConfirmationDialog.open() : {}
        }
    }

    MonitorConfigOverrideDialog
    {
        id: overrideConfirmationDialog
        printer: base.printer
    }
}