// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.0 as Cura

// A Print Job Card is essentially just a filled-in Expandable Card item.
Item
{
    id: base
    property var printJob: null

    width: parent.width
    height: childrenRect.height

    ExpandableCard
    {
        headerItem: Row
        {
            height: 48
            anchors.left: parent.left
            anchors.leftMargin: 24
            spacing: 18

            MonitorPrintJobPreview
            {
                printJob: base.printJob
                size: 32
                anchors.verticalCenter: parent.verticalCenter
            }

            Label
            {
                text: printJob && printJob.name ? printJob.name : ""
                color: "#374355"
                elide: Text.ElideRight
                font: UM.Theme.getFont("default_bold")
                anchors.verticalCenter: parent.verticalCenter
                width: 216
                height: 18
            }
            
            Label
            {
                text: printJob ? OutputDevice.formatDuration(printJob.timeTotal) : ""
                color: "#374355"
                elide: Text.ElideRight
                font: UM.Theme.getFont("default_bold")
                anchors.verticalCenter: parent.verticalCenter
                width: 216
                height: 18
            }

            Label
            {
                color: "#374355"
                height: 18
                elide: Text.ElideRight
                font: UM.Theme.getFont("default_bold")
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
                width: 216
            }
        }
        drawerItem: Row
        {
            height: 96
            anchors.left: parent.left
            anchors.leftMargin: 74
            spacing: 18

            Rectangle
            {
                id: printerConfiguration
                width: 450
                height: 72
                color: "blue"
                anchors.verticalCenter: parent.verticalCenter
            }
            Label {
                height: 18
                text: printJob && printJob.owner ? printJob.owner : ""
                color: "#374355"
                elide: Text.ElideRight
                font: UM.Theme.getFont("default_bold")
                anchors.top: printerConfiguration.top
            }
        }
    }
}