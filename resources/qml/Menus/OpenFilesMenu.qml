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
    title: catalog.i18nc("@title:menu menubar:file", "Open File(s)...")

    Instantiator
    {
        id: fileProviders
        model: CuraApplication.getFileProviderModel()
        Cura.MenuItem
        {
            text: model.displayText
            onTriggered:
            {
                if (model.index == 0)  // The 0th element is the "From Disk" option, which should activate the open local file dialog
                {
                    Cura.Actions.open.trigger()
                }
                else
                {
                    CuraApplication.getFileProviderModel().trigger(model.name);
                }
            }
            shortcut: model.shortcut
        }
        onObjectAdded: function(index, object) { openFilesMenu.insertItem(index, object)}

        onObjectRemoved: function(index, object) { openFilesMenu.removeItem(object) }
    }
}
