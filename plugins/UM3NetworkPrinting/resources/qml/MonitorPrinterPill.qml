// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import UM 1.2 as UM

/**
 * A MonitorPrinterPill is a blue-colored tag indicating which printers a print
 * job is compatible with. It is used by the MonitorPrintJobCard component.
 */
Item
{
    // The printer name
    property alias text: printerNameLabel.text;

    implicitHeight: 18 * screenScaleFactor // TODO: Theme!
    implicitWidth: printerNameLabel.contentWidth + 12 // TODO: Theme!

    Rectangle {
        id: background
        anchors.fill: parent
        color: "#e4e4f2" // TODO: Theme!
        radius: 2 * screenScaleFactor // TODO: Theme!
    }

    Label {
        id: printerNameLabel
        anchors.centerIn: parent
        color: "#535369" // TODO: Theme!
        text: ""
        font.pointSize: 10
    }
}