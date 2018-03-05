// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM


Column
{
    id: extruderInfo
    property var printCoreConfiguration
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
            elide: Text.ElideRight
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            font: UM.Theme.getFont("default")
        }

        // Rounded item to show the extruder number
        Item
        {
            id: extruderIconItem
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: extruderLabel.right
            anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").width / 2)

            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height

            UM.RecolorImage {
                id: mainCircle
                anchors.fill: parent

                sourceSize.width: parent.width
                sourceSize.height: parent.height
                source: UM.Theme.getIcon("extruder_button")

                color: extruderNumberText.color
            }

            Label
            {
                id: extruderNumberText
                anchors.centerIn: parent
                text: printCoreConfiguration.position + 1
                font: UM.Theme.getFont("default")
            }
        }
    }

    Label
    {
        id: materialLabel
        text: printCoreConfiguration.material
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("default_bold")
    }

    Label
    {
        id: printCoreTypeLabel
        text: printCoreConfiguration.hotendID
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("default")
    }
}
