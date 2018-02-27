// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu;

    MenuItem
    {
        text: catalog.i18nc("@label:category menu label", "Network printers")
        enabled: false
    }

    NetworkPrinterMenu { }

    MenuSeparator { }

    MenuItem
    {
        text: catalog.i18nc("@label:category menu label", "Local printers")
        enabled: false
    }

    LocalPrinterMenu { }

    ExclusiveGroup { id: group; }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.addMachine; }
    MenuItem { action: Cura.Actions.configureMachines; }
}
