// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.6 as UM
import Cura 1.0 as Cura

import "../Dialogs"

Menu
{
    id: openFilesMenu
    title: catalog.i18nc("@title:menu menubar:file", "Open File(s)...")
    iconName: "document-open-recent";

    Instantiator
    {
        id: fileProviders
        model: CuraApplication.getFileProviderModel()
        MenuItem
        {
            text: model.displayText
            onTriggered: CuraApplication.getFileProviderModel().trigger(model.name)
            shortcut: model.shortcut
        }
        onObjectAdded: openFilesMenu.insertItem(index, object)
        onObjectRemoved: openFilesMenu.removeItem(object)
    }
}
