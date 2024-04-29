// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.11
import UM 1.5 as UM

Item
{
    id: extruderIconItem

    property bool checked: true
    property color materialColor
    property alias textColor: extruderNumberText.color
    property bool extruderEnabled: true
    property int iconSize: UM.Theme.getSize("extruder_icon").width
    property string iconVariant: "medium"
    property alias font: extruderNumberText.font
    property alias text: extruderNumberText.text

    implicitWidth: iconSize
    implicitHeight: iconSize

    Item
    {
        opacity: extruderEnabled ? 1 : UM.Theme.getColor("extruder_disabled").a
        anchors.fill: parent
        layer.enabled: true // Prevent weird opacity effects.

        UM.ColorImage
        {
            anchors.fill: parent
            width: iconSize
            height: iconSize

            source: UM.Theme.getIcon("ExtruderColor", iconVariant)
            color: materialColor
        }
        UM.ColorImage
        {
            anchors.fill: parent
            width: iconSize
            height: iconSize

            source: UM.Theme.getIcon("Extruder", iconVariant)
            color: extruderNumberText.color
        }

        UM.Label
        {
            id: extruderNumberText
            width: contentWidth
            height: contentHeight
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.right: parent.right
            horizontalAlignment: Text.AlignHCenter
            text: (index + 1).toString()
            font: UM.Theme.getFont("small_emphasis")
        }
    }
}
