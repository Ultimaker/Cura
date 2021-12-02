// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.1 as UM

//
// Menu with Cura styling.
//
Menu
{
    id: menu
    padding: 0

    implicitWidth: UM.Theme.getSize("setting_control").width
    width: Math.max.apply(Math, Object.values(contentChildren).map(function(c) { return c.width }))

    background: Rectangle {
        color: UM.Theme.getColor("setting_control")
        border.color: UM.Theme.getColor("setting_control_border")
    }
}