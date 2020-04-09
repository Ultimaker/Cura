// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Button
{
    id: objectItemButton

    width: parent.width
    height: UM.Theme.getSize("action_button").height
    leftPadding: UM.Theme.getSize("thin_margin").width
    rightPadding: UM.Theme.getSize("thin_margin").width
    checkable: true
    hoverEnabled: true

    contentItem: Item
    {
        width: objectItemButton.width - objectItemButton.leftPadding
        height: UM.Theme.getSize("action_button").height

        Label
        {
            id: buttonText
            anchors
            {
                left: parent.left
                right: parent.right
                verticalCenter: parent.verticalCenter
            }
            text: objectItemButton.text
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_scene")
            opacity: (outsideBuildArea) ? 0.5 : 1.0
            visible: text != ""
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    background: Rectangle
    {
        id: backgroundRect
        color: objectItemButton.hovered ? UM.Theme.getColor("action_button_hovered") : "transparent"
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: objectItemButton.checked ? UM.Theme.getColor("primary") : "transparent"
    }

    TextMetrics
    {
        id: buttonTextMetrics
        text: buttonText.text
        font: buttonText.font
        elide: buttonText.elide
        elideWidth: buttonText.width
    }

    Cura.ToolTip
    {
        id: tooltip
        tooltipText: objectItemButton.text
        visible: objectItemButton.hovered && buttonTextMetrics.elidedText != buttonText.text
    }

    onClicked: Cura.SceneController.changeSelection(index)
}
