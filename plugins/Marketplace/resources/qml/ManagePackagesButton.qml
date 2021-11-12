// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.2 as UM
import Cura 1.6 as Cura

import QtQuick 2.15
import QtQuick.Controls 2.15

Button
{
    id: root
    width: UM.Theme.getSize("button_icon").width
    height: UM.Theme.getSize("button_icon").height
    hoverEnabled: true
    property color backgroundColor: hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")

    background: Rectangle
    {
        color: backgroundColor
        border.color: "transparent"
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
        anchors.centerIn: parent

    }
}
