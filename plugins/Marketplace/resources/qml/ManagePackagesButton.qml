// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.2 as UM
import Cura 1.6 as Cura

import QtQuick 2.15
import QtQuick.Controls 2.15

Button
{
    id: root
    width: childrenRect.width
    height: childrenRect.height

    hoverEnabled: true

    background: Rectangle
    {
        color: UM.Theme.getColor("action_button")
        border.color: "transparent"
        border.width: UM.Theme.getSize("default_lining").width
    }

    Cura.ToolTip
    {
        id: tooltip

        tooltipText: catalog.i18nc("@info:tooltip", "Manage packages")
        arrowSize: 0
        visible: root.hovered
    }

    UM.RecolorImage
    {
        id: icon

        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height

        color: UM.Theme.getColor("icon")
        source: UM.Theme.getIcon("Settings")
    }
}
