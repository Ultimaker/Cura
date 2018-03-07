// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item {
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    width: childrenRect.width
    height: childrenRect.height
    Image {
        id: statusIcon
        width: UM.Theme.getSize("status_icon").width
        height: UM.Theme.getSize("status_icon").height
        sourceSize.width: width
        sourceSize.height: width
        source: printerConnected ? UM.Theme.getIcon("tab_status_connected") : UM.Theme.getIcon("tab_status_busy")
    }
}



