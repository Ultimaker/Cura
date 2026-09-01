// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.1 as Cura

Cura.Menu
{
    id: saveProjectMenu

    Repeater
    {
        id: projectOutputDevices
        model: Cura.Actions.saveWorkspaceActions
        Cura.MenuItem
        {
            required property var modelData

            action: modelData
            visible: action.enabled
            enabled: visible
        }
    }
}
