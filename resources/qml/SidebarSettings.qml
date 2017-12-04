// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2

Sidebar
{
    id: sidebarSettings

    property bool showPrintMonitor: false

    anchors {
        top: parent.top
        bottom: parent.bottom
        left: parent.left
        right: parent.right
    }

    width: parent.width
    monitoringPrint: showPrintMonitor
}
