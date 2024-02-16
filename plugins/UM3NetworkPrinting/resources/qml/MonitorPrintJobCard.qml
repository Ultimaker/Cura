// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.5 as UM
import Cura 1.0 as Cura

/**
 * A Print Job Card is essentially just a filled-in Expandable Card item. All
 * data within it is derived from being passed a printJob property.
 *
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    id: base

    // The print job which all other data is derived from
    property var printJob: null

    width: parent.width
    height: childrenRect.height

    ExpandableCard
    {
        enabled: printJob != null
        borderColor: printJob && printJob.configurationChanges.length !== 0 ? UM.Theme.getColor("warning") : UM.Theme.getColor("monitor_card_border")
        headerItem: Row
        {
            height: Math.round(48 * screenScaleFactor) // TODO: Theme!
            anchors.left: parent.left
            anchors.leftMargin: Math.round(24 * screenScaleFactor) // TODO: Theme!
            spacing: Math.round(18 * screenScaleFactor) // TODO: Theme!

            MonitorPrintJobPreview
            {
                printJob: base.printJob
                size: Math.round(32 * screenScaleFactor) // TODO: Theme!
                anchors.verticalCenter: parent.verticalCenter
            }

            Item
            {
                anchors.verticalCenter: parent.verticalCenter
                height: Math.round(18 * screenScaleFactor) // TODO: Theme!
                width: UM.Theme.getSize("monitor_column").width
                Rectangle
                {
                    color: UM.Theme.getColor("monitor_skeleton_loading")
                    width: Math.round(parent.width / 2)
                    height: parent.height
                    visible: !printJob
                    radius: 2 * screenScaleFactor // TODO: Theme!
                }
                UM.Label
                {
                    text: printJob && printJob.name ? printJob.name : ""
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("medium") // 14pt, regular
                    visible: printJob

                    // FIXED-LINE-HEIGHT:
                    width: parent.width
                    height: parent.height
                }
            }

            Item
            {
                anchors.verticalCenter: parent.verticalCenter
                height: Math.round(18 * screenScaleFactor) // TODO: Theme!
                width: UM.Theme.getSize("monitor_column").width

                Rectangle
                {
                    color: UM.Theme.getColor("monitor_skeleton_loading")
                    width: Math.round(parent.width / 3)
                    height: parent.height
                    visible: !printJob
                    radius: 2 * screenScaleFactor // TODO: Theme!
                }

                UM.Label
                {
                    text: printJob ? OutputDevice.formatDuration(printJob.timeTotal) : ""
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("medium") // 14pt, regular
                    visible: printJob

                    // FIXED-LINE-HEIGHT:
                    height: Math.round(18 * screenScaleFactor) // TODO: Theme!
                }
            }

            Item
            {
                anchors.verticalCenter: parent.verticalCenter
                height: Math.round(18 * screenScaleFactor) // TODO: This should be childrenRect.height but QML throws warnings
                width: childrenRect.width

                Rectangle
                {
                    color: UM.Theme.getColor("monitor_skeleton_loading")
                    width: Math.round(72 * screenScaleFactor) // TODO: Theme!
                    height: parent.height
                    visible: !printJob
                    radius: 2 * screenScaleFactor // TODO: Theme!
                }

                UM.Label
                {
                    id: printerAssignmentLabel
                    anchors.verticalCenter: parent.verticalCenter
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("medium") // 14pt, regular
                    text: {
                        if (printJob !== null)
                        {
                            if (printJob.assignedPrinter == null)
                            {
                                if (printJob.state == "error")
                                {
                                    return catalog.i18nc("@label", "Unavailable printer");
                                }
                                return catalog.i18nc("@label", "First available");
                            }
                            return printJob.assignedPrinter.name;
                        }
                        return "";
                    }
                    visible: printJob
                    width: Math.round(120 * screenScaleFactor) // TODO: Theme!

                    // FIXED-LINE-HEIGHT:
                    height: parent.height
                }

                Row
                {
                    id: printerFamilyPills
                    anchors
                    {
                        left: printerAssignmentLabel.right;
                        leftMargin: Math.round(12 * screenScaleFactor) // TODO: Theme!
                        verticalCenter: parent.verticalCenter
                    }
                    height: childrenRect.height
                    spacing: Math.round(6 * screenScaleFactor) // TODO: Theme!
                    visible: printJob

                    MonitorPrinterPill
                    {
                        text: printJob ? printJob.configuration.printerType : ""
                    }
                }
            }
        }
        drawerItem: Row
        {
            anchors
            {
                left: parent.left
                leftMargin: Math.round(74 * screenScaleFactor) // TODO: Theme!
            }
            height: Math.round(108 * screenScaleFactor) // TODO: Theme!
            spacing: Math.round(18 * screenScaleFactor) // TODO: Theme!

            MonitorPrinterConfiguration
            {
                id: printerConfiguration
                anchors.verticalCenter: parent.verticalCenter
                configurations: base.printJob ? base.printJob.configuration.extruderConfigurations : null
                height: Math.round(72 * screenScaleFactor) // TODO: Theme!
            }

            UM.Label
            {
                text: printJob && printJob.owner ? printJob.owner : ""
                elide: Text.ElideRight
                font: UM.Theme.getFont("medium") // 14pt, regular
                anchors.top: printerConfiguration.top

                // FIXED-LINE-HEIGHT:
                height: Math.round(18 * screenScaleFactor) // TODO: Theme!
            }
        }
    }

    MonitorContextMenuButton
    {
        id: contextMenuButton
        anchors
        {
            right: parent.right
            rightMargin: Math.round(8 * screenScaleFactor) // TODO: Theme!
            top: parent.top
            topMargin: Math.round(8 * screenScaleFactor) // TODO: Theme!
        }
        width: Math.round(32 * screenScaleFactor) // TODO: Theme!
        height: Math.round(32 * screenScaleFactor) // TODO: Theme!
        enabled: OutputDevice.supportsPrintJobActions
        onClicked: enabled ? contextMenu.switchPopupState() : {}
        visible:
        {
            if(!printJob)
            {
                return false;
            }
            if(!contextMenu.hasItems)
            {
                return false;
            }
            var states = ["queued", "error", "sent_to_printer", "pre_print", "printing", "pausing", "paused", "resuming"];
            return states.indexOf(printJob.state) !== -1;
        }
    }

    MonitorContextMenu
    {
        id: contextMenu
        printJob: base.printJob ? base.printJob : null
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
         text: catalog.i18nc("@info", "Please update your printer's firmware to manage the queue remotely.")
         target: contextMenuButton
     }
}
