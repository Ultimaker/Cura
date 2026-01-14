// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

Button
{
    id: objectItemButton

    width: parent.width
    height: UM.Theme.getSize("action_button").height
    checkable: true
    hoverEnabled: true

    onHoveredChanged:
    {
        if(hovered && (buttonTextMetrics.elidedText != buttonText.text))
        {
            tooltip.show()
        } else
        {
            tooltip.hide()
        }
    }


    onClicked: Cura.SceneController.changeSelection(index)

    background: Rectangle
    {
        id: backgroundRect
        color: objectItemButton.hovered ? UM.Theme.getColor("action_button_hovered") : "transparent"
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: objectItemButton.checked ? UM.Theme.getColor("primary") : "transparent"
    }

    contentItem: Item
    {
        width: objectItemButton.width - objectItemButton.leftPadding
        height: UM.Theme.getSize("action_button").height

        Rectangle
        {
            id: swatch
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            width: UM.Theme.getSize("standard_arrow").height
            height: UM.Theme.getSize("standard_arrow").height
            radius: Math.round(width / 2)
            color: extruderColor
            visible: showExtruderSwatches && extruderColor != ""
        }

        UM.Label
        {
            id: buttonText
            anchors
            {
                left: showExtruderSwatches ? swatch.right : parent.left
                leftMargin: showExtruderSwatches ? UM.Theme.getSize("narrow_margin").width : 0
                right: perObjectSettingsInfo.visible ? perObjectSettingsInfo.left : parent.right
                verticalCenter: parent.verticalCenter
            }
            text: objectItemButton.text
            color: UM.Theme.getColor("text_scene")
            opacity: (outsideBuildArea) ? 0.5 : 1.0
            visible: text != ""
            elide: Text.ElideRight
        }
    }

    TextMetrics
    {
        id: buttonTextMetrics
        text: buttonText.text
        font: buttonText.font
        elide: buttonText.elide
        elideWidth: buttonText.width
    }

    UM.ToolTip
    {
        id: tooltip
        tooltipText: objectItemButton.text
    }

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }
}
