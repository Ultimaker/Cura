// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM


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

        // Rounded item to show the extruder number
        Item
        {
            id: extruderIconItem
            anchors.verticalCenter: extruderLabel.verticalCenter
            anchors.left: extruderLabel.right
            anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").width / 2)

            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height

            UM.RecolorImage {
                id: mainCircle
                anchors.fill: parent

                anchors.centerIn: parent
                sourceSize.width: parent.width
                sourceSize.height: parent.height
                source: UM.Theme.getIcon("extruder_button")
                color: mainColor
            }

            Label
            {
                id: extruderNumberText
                anchors.centerIn: parent
                text: printCoreConfiguration.position + 1
                renderType: Text.NativeRendering
                font: UM.Theme.getFont("default")
                color: mainColor
            }
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
