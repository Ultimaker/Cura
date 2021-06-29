// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.11
import QtQuick.Controls 1.1
import UM 1.2 as UM

Item
{
    id: extruderIconItem

    implicitWidth: UM.Theme.getSize("extruder_icon").width
    implicitHeight: UM.Theme.getSize("extruder_icon").height

    property bool checked: true
    property color materialColor
    property alias textColor: extruderNumberText.color
    property bool extruderEnabled: true

    Item
    {
        opacity: extruderEnabled ? 1 : 0.4
        anchors.fill: parent

        UM.RecolorImage
        {
            id: blorp
            anchors.fill: parent

            source: UM.Theme.getIcon("ExtruderColor", "medium")
            color: materialColor
        }
        UM.RecolorImage
        {
            id: mainIcon
            anchors.fill: parent

            source: UM.Theme.getIcon("Extruder", "medium")
            color: UM.Theme.getColor("text")
        }

        Label
        {
            id: extruderNumberText
            anchors.centerIn: parent
            text: index + 1
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text")
            width: contentWidth
            height: contentHeight
            renderType: Text.NativeRendering
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}
