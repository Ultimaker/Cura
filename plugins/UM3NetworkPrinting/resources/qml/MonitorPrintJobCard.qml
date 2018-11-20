// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

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
        headerItem: Row
        {
            height: 48 * screenScaleFactor // TODO: Theme!
            anchors.left: parent.left
            anchors.leftMargin: 24 * screenScaleFactor // TODO: Theme!
            spacing: 18 * screenScaleFactor // TODO: Theme!

            MonitorPrintJobPreview
            {
                printJob: base.printJob
                size: 32 * screenScaleFactor // TODO: Theme!
                anchors.verticalCenter: parent.verticalCenter
            }

            Label
            {
                text: printJob && printJob.name ? printJob.name : ""
                color: "#374355"
                elide: Text.ElideRight
                font: UM.Theme.getFont("medium") // 14pt, regular
                anchors.verticalCenter: parent.verticalCenter
                width: 216 * screenScaleFactor // TODO: Theme!

                // FIXED-LINE-HEIGHT:
                height: 18 * screenScaleFactor // TODO: Theme!
                verticalAlignment: Text.AlignVCenter
            }
            
            Label
            {
                text: printJob ? OutputDevice.formatDuration(printJob.timeTotal) : ""
                color: "#374355"
                elide: Text.ElideRight
                font: UM.Theme.getFont("medium") // 14pt, regular
                anchors.verticalCenter: parent.verticalCenter
                width: 216 * screenScaleFactor // TODO: Theme!

                // FIXED-LINE-HEIGHT:
                height: 18 * screenScaleFactor // TODO: Theme!
                verticalAlignment: Text.AlignVCenter
            }

            Label
            {
                color: "#374355"
                elide: Text.ElideRight
                font: UM.Theme.getFont("medium") // 14pt, regular
                text: {
                    if (printJob !== null) {
                        if (printJob.assignedPrinter == null)
                        {
                            if (printJob.state == "error")
                            {
                                return catalog.i18nc("@label", "Waiting for: Unavailable printer")
                            }
                            return catalog.i18nc("@label", "Waiting for: First available")
                        }
                        else
                        {
                            return catalog.i18nc("@label", "Waiting for: ") + printJob.assignedPrinter.name
                        }
                    }
                    return ""
                }
                visible: printJob
                anchors.verticalCenter: parent.verticalCenter
                width: 216 * screenScaleFactor // TODO: Theme!

                // FIXED-LINE-HEIGHT:
                height: 18 * screenScaleFactor // TODO: Theme!
                verticalAlignment: Text.AlignVCenter
            }
        }
        drawerItem: Row
        {
            anchors
            {
                left: parent.left
                leftMargin: 74 * screenScaleFactor // TODO: Theme!
            }
            height: 96 * screenScaleFactor // TODO: Theme!
            spacing: 18 * screenScaleFactor // TODO: Theme!

            MonitorPrinterConfiguration
            {
                id: printerConfiguration
                anchors.verticalCenter: parent.verticalCenter
                printJob: base.printJob
            }
            Label {
                text: printJob && printJob.owner ? printJob.owner : ""
                color: "#374355" // TODO: Theme!
                elide: Text.ElideRight
                font: UM.Theme.getFont("medium") // 14pt, regular
                anchors.top: printerConfiguration.top

                // FIXED-LINE-HEIGHT:
                height: 18 * screenScaleFactor // TODO: Theme!
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}