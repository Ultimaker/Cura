// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.1
import UM 1.2 as UM

Item
{
    id: extruderIconItem

    implicitWidth: UM.Theme.getSize("button").width
    implicitHeight: implicitWidth

    property bool checked: true
    property alias materialColor: mainIcon.color
    property alias textColor: extruderNumberText.color

    UM.RecolorImage
    {
        id: mainIcon
        anchors.fill: parent

        sourceSize.width: parent.width
        sourceSize.height: parent.width
        source: UM.Theme.getIcon("extruder_button")
    }

    Rectangle
    {
        id: extruderNumberCircle

        width: height
        height: parent.height / 2
        radius: Math.round(width / 2)
        color: "white"

        anchors
        {
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            // The circle needs to be slightly off center (so it sits in the middle of the square bit of the icon)
            topMargin: (parent.height - height) / 2 - 0.1 * parent.height
        }

        Label
        {
            id: extruderNumberText
            anchors.centerIn: parent
            text: index + 1
            font: UM.Theme.getFont("default")
            width: contentWidth
            height: contentHeight
        }
    }
}