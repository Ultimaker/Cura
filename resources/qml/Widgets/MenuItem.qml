// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM

//
// MenuItem with Cura styling.
//
UM.MenuItem
{
    id: menuItem

    implicitHeight: UM.Theme.getSize("menu").height + UM.Theme.getSize("narrow_margin").height
    implicitWidth: UM.Theme.getSize("menu").width
    opacity: enabled ? 1.0 : 0.5

    arrow: UM.RecolorImage
    {
        visible: menuItem.subMenu
        height: UM.Theme.getSize("default_arrow").height
        width: height
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        source: UM.Theme.getIcon("ChevronSingleRight")
        color: UM.Theme.getColor("setting_control_text")
    }

    indicator: UM.RecolorImage
    {
        id: check
        visible: menuItem.checkable && menuItem.checked
        height: UM.Theme.getSize("default_arrow").height
        width: height
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        source: UM.Theme.getIcon("Check", "low")
        color: UM.Theme.getColor("setting_control_text")
    }

    background: Rectangle
    {
        x: UM.Theme.getSize("default_lining").width
        y: UM.Theme.getSize("default_lining").width
        width: menuItem.width - 2 * UM.Theme.getSize("default_lining").width
        height: menuItem.height - 2 * UM.Theme.getSize("default_lining").height

        color: menuItem.highlighted ?  UM.Theme.getColor("setting_control_highlight") : "transparent"
        border.color: menuItem.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
    }
}