// Copyright (c) 2017 Ultimaker B.V.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.3 as UM
import Cura 1.0 as Cura

Loader
{
    property real maximumWidth: parent.width
    property real maximumHeight: parent.height

    sourceComponent: Cura.MachineManager.printerOutputDevices.length > 0 ? Cura.MachineManager.printerOutputDevices[0].monitorItem: null
    visible: sourceComponent != null
}
