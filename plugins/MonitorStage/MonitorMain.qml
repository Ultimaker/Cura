// Copyright (c) 2017 Ultimaker B.V.

import QtQuick 2.10
import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura


Item
{
    // We show a nice overlay on the 3D viewer when the current output device has no monitor view
    Rectangle
    {
        id: viewportOverlay

        color: UM.Theme.getColor("viewport_overlay")
        anchors.fill: parent
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

        anchors.fill: parent

        height: parent.height

        property real maximumWidth: parent.width
        property real maximumHeight: parent.height

        sourceComponent: Cura.MachineManager.printerOutputDevices.length > 0 ? Cura.MachineManager.printerOutputDevices[0].monitorItem: null
    }
}
