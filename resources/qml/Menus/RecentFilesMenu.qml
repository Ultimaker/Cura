// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.3 as UM
import Cura 1.0 as Cura

import "../Dialogs"

Menu
{
    id: menu
    title: catalog.i18nc("@title:menu menubar:file", "Open &Recent")
    iconName: "document-open-recent";

    enabled: CuraApplication.recentFiles.length > 0;

    Instantiator
    {
        model: CuraApplication.recentFiles
        MenuItem
        {
            text:
            {
                var path = decodeURIComponent(modelData.toString())
                return (index + 1) + ". " + path.slice(path.lastIndexOf("/") + 1);
            }
            onTriggered: CuraApplication.readLocalFile(modelData)
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    Cura.AskOpenAsProjectOrModelsDialog
    {
        id: askOpenAsProjectOrModelsDialog
    }
}
