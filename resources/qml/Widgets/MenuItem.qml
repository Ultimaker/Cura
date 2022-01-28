// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.1 as UM

//
// MenuItem with Cura styling.
//
MenuItem
{
    id: menuItem

    implicitHeight: UM.Theme.getSize("setting_control").height + UM.Theme.getSize("narrow_margin").height
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
        source: UM.Theme.getIcon("Check")
        color: UM.Theme.getColor("setting_control_text")
    }

    contentItem: Text {
        leftPadding: menuItem.checkable ? menuItem.indicator.width + UM.Theme.getSize("default_margin").width : UM.Theme.getSize("thin_margin").width
        rightPadding: menuItem.subMenu ? menuItem.arrow.width + UM.Theme.getSize("default_margin").width : UM.Theme.getSize("thin_margin").width
        text: menuItem.text

        textFormat: Text.PlainText
        renderType: Text.NativeRendering
        color: UM.Theme.getColor("setting_control_text")
        font: UM.Theme.getFont("default")
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        x: UM.Theme.getSize("default_lining").width
        y: UM.Theme.getSize("default_lining").width
        width: menuItem.width - 2 * UM.Theme.getSize("default_lining").width
        height: menuItem.height - 2 * UM.Theme.getSize("default_lining").height

        color: menuItem.highlighted ?  UM.Theme.getColor("setting_control_highlight") : "transparent"
        border.color: menuItem.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
    }
}