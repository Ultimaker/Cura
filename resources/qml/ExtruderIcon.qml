// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
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

    UM.RecolorImage
    {
        id: mainIcon
        anchors.fill: parent

        source: UM.Theme.getIcon("Extruder", "medium")
        color: extruderEnabled ? materialColor: UM.Theme.getColor("disabled")
    }

    Rectangle
    {
        id: extruderNumberCircle

        width: height
        height: Math.round(parent.height / 2)
        radius: Math.round(width)
        color: UM.Theme.getColor("toolbar_background")

        anchors
        {
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: (parent.height - height) / 2
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
            visible: extruderEnabled
            renderType: Text.NativeRendering
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        UM.RecolorImage
        {
            id: disabledIcon
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("thick_lining").width
            sourceSize.height: width
            source: UM.Theme.getIcon("Cancel")
            visible: !extruderEnabled
            color: UM.Theme.getColor("text")
        }
    }
}
