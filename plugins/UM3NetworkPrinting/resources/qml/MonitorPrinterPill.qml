// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import UM 1.5 as UM

/**
 * A MonitorPrinterPill is a blue-colored tag indicating which printers a print
 * job is compatible with. It is used by the MonitorPrintJobCard component.
 */
Item
{
    id: monitorPrinterPill
    property var text: ""

    implicitHeight: 18 * screenScaleFactor // TODO: Theme!
    implicitWidth: Math.max(printerNameLabel.contentWidth + 12 * screenScaleFactor, 36 * screenScaleFactor) // TODO: Theme!

    Rectangle
    {
        id: background
        anchors.fill: parent
        color: printerNameLabel.visible ? UM.Theme.getColor("monitor_printer_family_tag") : UM.Theme.getColor("monitor_skeleton_loading")
        radius: 2 * screenScaleFactor // TODO: Theme!
    }

    UM.Label
    {
        id: printerNameLabel
        anchors.centerIn: parent
        text: monitorPrinterPill.text
        visible: monitorPrinterPill.text !== ""
    }
}
