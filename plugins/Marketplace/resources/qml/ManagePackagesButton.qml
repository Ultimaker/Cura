// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.2 as UM
import Cura 1.6 as Cura

import QtQuick 2.15
import QtQuick.Controls 2.15

TabButton
{
    id: root
    width: UM.Theme.getSize("button_icon").width + UM.Theme.getSize("narrow_margin").width
    height: UM.Theme.getSize("button_icon").height
    hoverEnabled: true
    property color inactiveBackgroundColor : hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("detail_background")
    property color activeBackgroundColor : UM.Theme.getColor("main_background")
    leftInset: UM.Theme.getSize("narrow_margin").width

    background: Rectangle
    {
        color: parent.checked ? activeBackgroundColor : inactiveBackgroundColor
        border.color: parent.checked ? UM.Theme.getColor("detail_background") : "transparent"
        border.width: UM.Theme.getSize("thick_lining").width
        radius: Math.round(width * 0.5)
    }

    Cura.ToolTip
    {
        id: tooltip

        tooltipText: catalog.i18nc("@info:tooltip", "Manage packages")
        visible: root.hovered
    }

    UM.RecolorImage
    {
        id: icon

        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height
  
        color: UM.Theme.getColor("icon")
        source: UM.Theme.getIcon("Settings")
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.horizontalCenterOffset: Math.round(UM.Theme.getSize("narrow_margin").width /2)
        anchors.verticalCenter: parent.verticalCenter
    }
}
