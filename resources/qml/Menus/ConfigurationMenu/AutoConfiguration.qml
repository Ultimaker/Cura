// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.5 as UM
import Cura 1.0 as Cura

Item
{
    width: parent.width
    height: childrenRect.height

    UM.Label
    {
        id: header
        text: catalog.i18nc("@header", "Configurations")
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("small_button_text")
        height: contentHeight

        anchors
        {
            left: parent.left
            right: parent.right
        }
    }

    ConfigurationListView
    {
        anchors.top: header.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").width
        width: parent.width

        outputDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
    }
}