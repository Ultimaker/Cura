// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura

// Reusable component that holds an (re-colorable) icon on the left with some text on the right
Item
{
    property alias iconColor: icon.color
    property alias source: icon.source
    property alias text: label.text

    implicitWidth: icon.width + 100
    implicitHeight: icon.height

    Component.onCompleted: print(label.contentWidth)

    UM.RecolorImage
    {
        id: icon
        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height

        sourceSize.width: width
        sourceSize.height: height
        color: "black"

        anchors
        {
            left: parent.left
            verticalCenter: parent.verticalCenter
        }

    }

    Label
    {
        id: label
        height: contentHeight
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
        anchors
        {
            left: icon.right
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            rightMargin: 0
            margins: UM.Theme.getSize("narrow_margin").width
        }
    }
}