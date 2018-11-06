// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM

// This item will show a label with a squared icon in the left
Item
{
    id: container

    property alias text: label.text
    property alias source: icon.source
    property alias color: label.color
    property alias font: label.font

    height: childrenRect.height

    UM.RecolorImage
    {
        id: icon

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter

        source: UM.Theme.getIcon("dot")
        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height

        sourceSize.width: width
        sourceSize.height: height

        color: label.color
    }

    Label
    {
        id: label
        anchors.left: icon.right
        anchors.leftMargin: UM.Theme.getSize("thin_margin").width
        anchors.verticalCenter: parent.verticalCenter
        text: "Empty label"
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("very_small")
        renderType: Text.NativeRendering
    }
}