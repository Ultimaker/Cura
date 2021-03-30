// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Button
{
    id: base

    property alias toolItem: contentItemLoader.sourceComponent

    // These two properties indicate whether the toolbar button is at the top of the toolbar column or at the bottom.
    // If it is somewhere in the middle, then both has to be false. If there is only one element in the column, then
    // both properties have to be set to true. This is used to create a rounded corner.
    property bool isTopElement: false
    property bool isBottomElement: false

    hoverEnabled: true

    background: Rectangle
    {
        implicitWidth: UM.Theme.getSize("button").width
        implicitHeight: UM.Theme.getSize("button").height
        color:
        {
            if (base.checked && base.hovered)
            {
                return UM.Theme.getColor("toolbar_button_active_hover")
            }
            else if (base.checked)
            {
                return UM.Theme.getColor("toolbar_button_active")
            }
            else if(base.hovered)
            {
                return UM.Theme.getColor("toolbar_button_hover")
            }
            return UM.Theme.getColor("toolbar_background")
        }
        radius: UM.Theme.getSize("default_radius").width

        Rectangle
        {
            id: topSquare
            anchors
            {
                left: parent.left
                right: parent.right
                top: parent.top
            }
            height: parent.radius
            color: parent.color
            visible: !base.isTopElement
        }

        Rectangle
        {
            id: bottomSquare
            anchors
            {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: parent.radius
            color: parent.color
            visible: !base.isBottomElement
        }

        Rectangle
        {
            id: leftSquare
            anchors
            {
                left: parent.left
                top: parent.top
                bottom: parent.bottom
            }
            width: parent.radius
            color: parent.color
        }
    }

    contentItem: Item
    {
        opacity: parent.enabled ? 1.0 : 0.2
        Loader
        {
            id: contentItemLoader
            anchors.centerIn: parent
            width: UM.Theme.getSize("button_icon").width
            height: UM.Theme.getSize("button_icon").height
        }
    }

    Cura.ToolTip
    {
        id: tooltip
        tooltipText: base.text
        visible: base.hovered
    }
}
