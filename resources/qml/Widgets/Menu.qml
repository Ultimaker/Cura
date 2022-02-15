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
    padding: 0

    width: UM.Theme.getSize("context_menu").width

    delegate: Cura.MenuItem {}
    background: Rectangle
    {
        color: UM.Theme.getColor("main_background")
        border.color: UM.Theme.getColor("lining")
    }
}