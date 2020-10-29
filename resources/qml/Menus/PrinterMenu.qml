// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
//    TODO Enable custom style to the menu
//    style: MenuStyle
//    {
//        frame: Rectangle
//        {
//            color: "white"
//        }
//    }

    MenuItem
    {
        text: catalog.i18nc("@label:category menu label", "Network enabled printers")
        enabled: false
        visible: networkPrinterMenu.count > 0
    }

    NetworkPrinterMenu
    {
        id: networkPrinterMenu
    }

    MenuSeparator
    {
        visible: networkPrinterMenu.count > 0
    }

    MenuItem
    {
        text: catalog.i18nc("@label:category menu label", "Local printers")
        enabled: false
        visible: localPrinterMenu.count > 0
    }

    LocalPrinterMenu
    {
        id: localPrinterMenu
    }

    ExclusiveGroup { id: group; }

    MenuSeparator
    {
        visible: localPrinterMenu.count > 0
    }

    MenuItem { action: Cura.Actions.addMachine; }
    MenuItem { action: Cura.Actions.configureMachines; }
}
