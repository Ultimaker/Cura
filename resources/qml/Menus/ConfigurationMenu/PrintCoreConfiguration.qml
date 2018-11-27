// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: extruderInfo
    property var printCoreConfiguration
    property var mainColor: "black"
    spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)

    height: childrenRect.height

    Item
    {
        id: extruder
        width: parent.width
        height: childrenRect.height

        Label
        {
            id: extruderLabel
            text: catalog.i18nc("@label:extruder label", "Extruder")
            renderType: Text.NativeRendering
            elide: Text.ElideRight
            anchors.left: parent.left
            font: UM.Theme.getFont("default")
            color: mainColor
        }

        Cura.ExtruderIcon
        {
            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height
            materialColor: printCoreConfiguration.material.color
            anchors.left: extruderLabel.right
            anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
        }
    }

    Label
    {
        id: materialLabel
        text: printCoreConfiguration.material.name
        renderType: Text.NativeRendering
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("default_bold")
        color: mainColor
    }

    Label
    {
        id: printCoreTypeLabel
        text: printCoreConfiguration.hotendID
        renderType: Text.NativeRendering
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("default")
        color: mainColor
    }
}
