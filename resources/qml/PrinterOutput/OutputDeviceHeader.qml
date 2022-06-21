// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2

import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura


Item
{
    implicitWidth: parent.width
    implicitHeight: Math.floor(childrenRect.height + UM.Theme.getSize("default_margin").height * 2)
    property var outputDevice: null

    Connections
    {
        target: Cura.MachineManager
        function onGlobalContainerChanged()
        {
            outputDevice = Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null;
        }
    }

    Rectangle
    {
        height: childrenRect.height
        color: UM.Theme.getColor("setting_category")

        UM.Label
        {
            id: outputDeviceNameLabel
            font: UM.Theme.getFont("large_bold")
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: outputDevice != null ? outputDevice.activePrinter.name : ""
        }

        UM.Label
        {
            id: outputDeviceAddressLabel
            text: (outputDevice != null && outputDevice.address != null) ? outputDevice.address : ""
            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text_inactive")
            anchors.top: outputDeviceNameLabel.bottom
            anchors.left: parent.left
            anchors.margins: UM.Theme.getSize("default_margin").width
        }

        UM.Label
        {
            text: outputDevice != null ? "" : catalog.i18nc("@info:status", "The printer is not connected.")
            color: outputDevice != null && outputDevice.acceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
            wrapMode: Text.WordWrap
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
        }
    }
}