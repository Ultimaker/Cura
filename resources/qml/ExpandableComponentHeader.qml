// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

// Header of the popup
Cura.RoundedRectangle
{
    id: header

    property alias headerTitle: headerLabel.text
    property alias xPosCloseButton: closeButton.left

    height: UM.Theme.getSize("expandable_component_content_header").height
    color: UM.Theme.getColor("secondary")
    cornerSide: Cura.RoundedRectangle.Direction.Up
    border.width: UM.Theme.getSize("default_lining").width
    border.color: UM.Theme.getColor("lining")
    radius: UM.Theme.getSize("default_radius").width

    Label
    {
        id: headerLabel
        text: ""
        font: UM.Theme.getFont("medium")
        renderType: Text.NativeRendering
        verticalAlignment: Text.AlignVCenter
        color: UM.Theme.getColor("small_button_text")
        height: parent.height

        anchors
        {
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").height
        }
    }

    Button
    {
        id: closeButton
        width: UM.Theme.getSize("message_close").width
        height: UM.Theme.getSize("message_close").height
        hoverEnabled: true

        anchors
        {
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
            verticalCenter: parent.verticalCenter
        }

        contentItem: UM.RecolorImage
        {
            anchors.fill: parent
            sourceSize.width: width
            color: closeButton.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
            source: UM.Theme.getIcon("Cancel")
        }

        background: Item {}

        onClicked: toggleContent() // Will hide the popup item
    }
}
