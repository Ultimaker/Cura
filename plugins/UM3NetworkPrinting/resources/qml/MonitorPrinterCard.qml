// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.1
import UM 1.3 as UM
import Cura 1.0 as Cura

/**
 * A Printer Card is has two main components: the printer portion and the print job portion, the latter being paired in
 * the UI when a print job is paired a printer in-cluster.
 *
 * NOTE: For most labels, a fixed height with vertical alignment is used to make layouts more deterministic (like the
 * fixed-size textboxes used in original mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    id: base

    // The printer which all printer data is derived from
    property var printer: null

    property var borderSize: 1 * screenScaleFactor // TODO: Theme, and remove from here

    // If the printer card's controls are enabled. This is used by the carousel to prevent opening the context menu or
    // camera while the printer card is not "in focus"
    property var enabled: true

    // If the printer is a cloud printer or not. Other items base their enabled state off of this boolean. In the future
    // they might not need to though.
    property bool cloudConnection: Cura.MachineManager.activeMachineIsUsingCloudConnection

    width: 834 * screenScaleFactor // TODO: Theme!
    height: childrenRect.height

    Rectangle
    {
        id: background
        anchors.fill: parent
        color: UM.Theme.getColor("monitor_card_background")
        border
        {
            color: UM.Theme.getColor("monitor_card_border")
            width: borderSize // TODO: Remove once themed
        }
        radius: 2 * screenScaleFactor // TODO: Theme!
    }

    // Printer portion
    Item
    {
        id: printerInfo

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

            Rectangle
            {
                id: printerImage
                width: 108 * screenScaleFactor // TODO: Theme!
                height: 108 * screenScaleFactor // TODO: Theme!
                color: printer ? "transparent" : UM.Theme.getColor("monitor_skeleton_loading")
                radius: 8 // TODO: Theme!
                Image
                {
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectFit
                    source: printer ? "../png/" + printer.type + ".png" : ""
                    mipmap: true
                }
            }
            

            Item
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                width: 180 * screenScaleFactor // TODO: Theme!
                height: printerNameLabel.height + printerFamilyPill.height + 6 * screenScaleFactor // TODO: Theme!

                Rectangle
                {
                    id: printerNameLabel
                    color: printer ? "transparent" : UM.Theme.getColor("monitor_skeleton_loading")
                    height: 18 * screenScaleFactor // TODO: Theme!
                    width: parent.width
                    radius: 2 * screenScaleFactor // TODO: Theme!
                    
                    Label
                    {
                        text: printer && printer.name ? printer.name : ""
                        color: UM.Theme.getColor("monitor_text_primary")
                        elide: Text.ElideRight
                        font: UM.Theme.getFont("large") // 16pt, bold
                        width: parent.width
                        visible: printer

                        // FIXED-LINE-HEIGHT:
                        height: parent.height
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Rectangle
                {
                    color: UM.Theme.getColor("monitor_skeleton_loading")
                    height: 18 * screenScaleFactor // TODO: Theme!
                    radius: 2 * screenScaleFactor // TODO: Theme!
                    visible: !printer
                    width: 48 * screenScaleFactor // TODO: Theme!
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
                    text: printer ? printer.type : ""
                }
            }

            MonitorPrinterConfiguration
            {
                id: printerConfiguration
                anchors.verticalCenter: parent.verticalCenter
                buildplate: printer ? "Glass" : null // 'Glass' as a default
                configurations:
                {
                    var configs = []
                    if (printer)
                    {
                        configs.push(printer.printerConfiguration.extruderConfigurations[0])
                        configs.push(printer.printerConfiguration.extruderConfigurations[1])
                    }
                    else
                    {
                        configs.push(null, null)
                    }
                    return configs
                }
                height: 72 * screenScaleFactor // TODO: Theme!te theRect's x property
            }
        }

        MonitorContextMenuButton
        {
            id: contextMenuButton
            anchors
            {
                right: parent.right
                rightMargin: 12 * screenScaleFactor // TODO: Theme!
                top: parent.top
                topMargin: 12 * screenScaleFactor // TODO: Theme!
            }
            width: 36 * screenScaleFactor // TODO: Theme!
            height: 36 * screenScaleFactor // TODO: Theme!
            enabled: !cloudConnection
            
            onClicked: enabled ? contextMenu.switchPopupState() : {}
            visible:
            {
                if (!printer || !printer.activePrintJob) {
                    return false
                }
                var states = ["queued", "error", "sent_to_printer", "pre_print", "printing", "pausing", "paused", "resuming"]
                return states.indexOf(printer.activePrintJob.state) !== -1
            }
        }

        MonitorContextMenu
        {
            id: contextMenu
            printJob: printer ? printer.activePrintJob : null
            target: contextMenuButton
        }

        // For cloud printing, add this mouse area over the disabled contextButton to indicate that it's not available
        MouseArea
        {
            id: contextMenuDisabledButtonArea
            anchors.fill: contextMenuButton
            hoverEnabled: contextMenuButton.visible && !contextMenuButton.enabled
            onEntered: contextMenuDisabledInfo.open()
            onExited: contextMenuDisabledInfo.close()
            enabled: !contextMenuButton.enabled
        }

        MonitorInfoBlurb
        {
            id: contextMenuDisabledInfo
            text: catalog.i18nc("@info", "These options are not available because you are monitoring a cloud printer.")
            target: contextMenuButton
        }

        CameraButton
        {
            id: cameraButton
            anchors
            {
                right: parent.right
                rightMargin: 20 * screenScaleFactor // TODO: Theme!
                bottom: parent.bottom
                bottomMargin: 20 * screenScaleFactor // TODO: Theme!
            }
            iconSource: "../svg/icons/camera.svg"
            enabled: !cloudConnection
            visible: printer
        }

        // For cloud printing, add this mouse area over the disabled cameraButton to indicate that it's not available
        MouseArea
        {
            id: cameraDisabledButtonArea
            anchors.fill: cameraButton
            hoverEnabled: cameraButton.visible && !cameraButton.enabled
            onEntered: cameraDisabledInfo.open()
            onExited: cameraDisabledInfo.close()
            enabled: !cameraButton.enabled
        }

        MonitorInfoBlurb
        {
            id: cameraDisabledInfo
            text: catalog.i18nc("@info", "The webcam is not available because you are monitoring a cloud printer.")
            target: cameraButton
        }
    }


    // Divider
    Rectangle
    {
        anchors
        {
            top: printJobInfo.top
            left: printJobInfo.left
            right: printJobInfo.right
        }
        height: borderSize // Remove once themed
        color: background.border.color
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
            color: printer && printer.activePrintJob && printer.activePrintJob.configurationChanges.length > 0 ? UM.Theme.getColor("warning") : "transparent" // TODO: Theme!
            width: borderSize // TODO: Remove once themed
        }
        color: "transparent" // TODO: Theme!
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
                color: printer ? UM.Theme.getColor("monitor_text_primary") : UM.Theme.getColor("monitor_text_disabled")
                font: UM.Theme.getFont("large_bold") // 16pt, bold
                text: {
                    if (!printer) {
                        return catalog.i18nc("@label:status", "Loading...")
                    }
                    if (printer && printer.state == "disabled")
                    {
                        return catalog.i18nc("@label:status", "Unavailable")
                    }
                    if (printer && printer.state == "unreachable")
                    {
                        return catalog.i18nc("@label:status", "Unreachable")
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
                    printJob: printer ? printer.activePrintJob : null
                    size: parent.height
                }
                visible: printer && printer.activePrintJob && !printerStatus.visible
            }

            Item
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                width: 180 * screenScaleFactor // TODO: Theme!
                height: printerNameLabel.height + printerFamilyPill.height + 6 * screenScaleFactor // TODO: Theme!
                visible: printer && printer.activePrintJob && !printerStatus.visible

                Label
                {
                    id: printerJobNameLabel
                    color: printer && printer.activePrintJob && printer.activePrintJob.isActive ? UM.Theme.getColor("monitor_text_primary") : UM.Theme.getColor("monitor_text_disabled")
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("large") // 16pt, bold
                    text: printer && printer.activePrintJob ? printer.activePrintJob.name : catalog.i18nc("@label", "Untitled")
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
                    color: printer && printer.activePrintJob && printer.activePrintJob.isActive ? UM.Theme.getColor("monitor_text_primary") : UM.Theme.getColor("monitor_text_disabled")
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("default") // 12pt, regular
                    text: printer && printer.activePrintJob ? printer.activePrintJob.owner : catalog.i18nc("@label", "Anonymous")
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
                printJob: printer && printer.activePrintJob
                visible: printer && printer.activePrintJob && printer.activePrintJob.configurationChanges.length === 0 && !printerStatus.visible
            }

            Label
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                }
                font: UM.Theme.getFont("default")
                text: catalog.i18nc("@label:status", "Requires configuration changes")
                visible: printer && printer.activePrintJob && printer.activePrintJob.configurationChanges.length > 0 && !printerStatus.visible
                color: UM.Theme.getColor("monitor_text_primary")

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
                color: UM.Theme.getColor("monitor_secondary_button_shadow")
                radius: 2 * screenScaleFactor // Todo: Theme!
                Rectangle
                {
                    anchors.fill: parent
                    anchors.bottomMargin: 2 * screenScaleFactor // TODO: Theme!
                    color: detailsButton.hovered ? UM.Theme.getColor("monitor_secondary_button_hover") : UM.Theme.getColor("monitor_secondary_button")
                    radius: 2 * screenScaleFactor // Todo: Theme!
                }
            }
            contentItem: Label
            {
                anchors.fill: parent
                anchors.bottomMargin: 2 * screenScaleFactor // TODO: Theme!
                color: UM.Theme.getColor("monitor_secondary_button_text")
                font: UM.Theme.getFont("medium") // 14pt, regular
                text: catalog.i18nc("@action:button","Details");
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                height: 18 * screenScaleFactor // TODO: Theme!
            }
            implicitHeight: 32 * screenScaleFactor // TODO: Theme!
            implicitWidth: 96 * screenScaleFactor // TODO: Theme!
            visible: printer && printer.activePrintJob && printer.activePrintJob.configurationChanges.length > 0 && !printerStatus.visible
            onClicked: base.enabled ? overrideConfirmationDialog.open() : {}
        }
    }

    MonitorConfigOverrideDialog
    {
        id: overrideConfirmationDialog
        printer: base.printer
    }
}