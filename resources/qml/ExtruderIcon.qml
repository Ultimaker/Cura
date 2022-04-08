// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.11
import UM 1.5 as UM

Item
{
    id: extruderIconItem

    implicitWidth: UM.Theme.getSize("extruder_icon").width
    implicitHeight: UM.Theme.getSize("extruder_icon").height

    property bool checked: true
    property color materialColor
    property alias textColor: extruderNumberText.color
    property bool extruderEnabled: true
    property var iconSize
    property string iconVariant: "medium"

    Item
    {
        opacity: extruderEnabled ? 1 : UM.Theme.getColor("extruder_disabled").a
        anchors.fill: parent
        layer.enabled: true // Prevent weird opacity effects.

        UM.ColorImage
        {
            anchors.fill: parent
            width: mainIcon.sourceSize.width
            height: mainIcon.sourceSize.height

            source: UM.Theme.getIcon("ExtruderColor", iconVariant)
            color: materialColor
        }
        UM.ColorImage
        {
            id: mainIcon
            anchors.fill: parent
            width: UM.Theme.getSize("extruder_icon").width
            height: UM.Theme.getSize("extruder_icon").height

            source: UM.Theme.getIcon("Extruder", iconVariant)
            color: extruderNumberText.color
        }

        UM.Label
        {
            id: extruderNumberText
            anchors.centerIn: parent
            text: index + 1
            font: UM.Theme.getFont("small_emphasis")
            width: contentWidth
            height: contentHeight
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
