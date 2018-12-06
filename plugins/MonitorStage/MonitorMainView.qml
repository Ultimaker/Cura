// Copyright (c) 2017 Ultimaker B.V.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.3 as UM
import Cura 1.0 as Cura

Item
{
    // parent could be undefined as this component is not visible at all times
    width: parent ? parent.width : 0
    height: parent ? parent.height : 0

    // We show a nice overlay on the 3D viewer when the current output device has no monitor view
    Rectangle
    {
        id: viewportOverlay

        color: UM.Theme.getColor("viewport_overlay")
        width: parent.width
        height: parent.height

        MouseArea
        {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onWheel: wheel.accepted = true
        }
    }

    Loader
    {
        id: monitorViewComponent

        width: parent.width
        height: parent.height

        property real maximumWidth: parent.width
        property real maximumHeight: parent.height

        sourceComponent: Cura.MachineManager.printerOutputDevices.length > 0 ? Cura.MachineManager.printerOutputDevices[0].monitorItem: null
        visible: sourceComponent != null
    }
}
