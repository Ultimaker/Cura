// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.6 as UM
import Cura 1.0 as Cura

import "../Dialogs"

Cura.Menu
{
    id: openFilesMenu

    Cura.MenuItem
    {
        action: Cura.Actions.open
    }

    Repeater
    {
        id: fileProviders
        model: Cura.Actions.extraOpenFileActions
        Cura.MenuItem
        {
            required property var modelData

            action: modelData
            visible: action.enabled
            enabled: visible
        }
    }
}
