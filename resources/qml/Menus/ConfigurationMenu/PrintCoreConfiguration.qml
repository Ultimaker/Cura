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

    height: information.height
    spacing: UM.Theme.getSize("default_margin").width

    //Extruder icon.
    Cura.ExtruderIcon
    {
        materialColor: printCoreConfiguration.material.color
        anchors.verticalCenter: parent.verticalCenter
        extruderEnabled: printCoreConfiguration.material.brand !== "" && printCoreConfiguration.hotendID !== ""
    }

    Column
    {
        id: information
        Label
        {
            text: printCoreConfiguration.material.brand ? printCoreConfiguration.material.brand : " " //Use space so that the height is still correct.
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_inactive")
        }
        Label
        {
            text: printCoreConfiguration.material.brand ? printCoreConfiguration.material.name : " " //Use space so that the height is still correct.
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text")
        }
        Label
        {
            text: printCoreConfiguration.hotendID ? printCoreConfiguration.hotendID : " " //Use space so that the height is still correct.
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_inactive")
        }
    }
}
