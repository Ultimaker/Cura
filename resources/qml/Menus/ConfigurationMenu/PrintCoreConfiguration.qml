// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Row
{
    id: extruderInfo
    property var printCoreConfiguration

    height: childrenRect.height
    spacing: UM.Theme.getSize("default_margin").width

    //Extruder icon.
    Item
    {
        width: childrenRect.width
        height: information.height
        Cura.ExtruderIcon
        {
            materialColor: printCoreConfiguration.material.color
            anchors.verticalCenter: parent.verticalCenter
            extruderEnabled: printCoreConfiguration.material.name !== "" && printCoreConfiguration.hotendID !== ""
        }
    }

    Column
    {
        id: information
        Label
        {
            text: printCoreConfiguration.material.brand
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_inactive")
        }
        Label
        {
            text: printCoreConfiguration.material.name
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
        }
        Label
        {
            text: printCoreConfiguration.hotendID
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_inactive")
        }
    }
}
