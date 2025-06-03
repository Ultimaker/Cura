import QtQuick 2.2

import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura


Item
{
    implicitWidth: parent.width
    implicitHeight: Math.floor(childrenRect.height + UM.Theme.getSize("default_margin").height * 2)
    property var outputDevice: null

    Connections
    {
        target: Cura.MachineManager
        onGlobalContainerChanged:
        {
            outputDevice = Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null;
        }
    }

    Rectangle
    {
        height: childrenRect.height
        color: UM.Theme.getColor("setting_category")

        Label
        {
            id: outputDeviceNameLabel
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("setting_category_text")
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: outputDevice != null ? outputDevice.activePrinter.name : ""
        }

        Label
        {
            id: outputDeviceAddressLabel
            text: (outputDevice != null && outputDevice.address != null) ? outputDevice.address : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("setting_category_disabled_text")
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: UM.Theme.getSize("default_margin").width
        }

        Label
        {
            text: outputDevice != null ? "" : catalog.i18nc("@info:status", "The printer is not connected.")
            color: outputDevice != null && outputDevice.acceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
            font: UM.Theme.getFont("very_small")
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