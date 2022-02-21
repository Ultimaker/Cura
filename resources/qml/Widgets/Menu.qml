// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7

import UM 1.5 as UM
import Cura 1.0 as Cura

//
// Menu with Cura styling.
//
UM.Menu
{
    id: menu
    topPadding: UM.Theme.getSize("narrow_margin").height
    bottomPadding: UM.Theme.getSize("narrow_margin").height
    padding: 0

    implicitWidth: UM.Theme.getSize("menu").width

    delegate: Cura.MenuItem {}
    background: Rectangle
    {
        color: UM.Theme.getColor("setting_control")
        border.color: UM.Theme.getColor("setting_control_border")
    }
}