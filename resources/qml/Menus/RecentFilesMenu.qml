// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: catalog.i18nc("@title:menu menubar:file", "Open &Recent")
    iconName: "document-open-recent";

    enabled: Printer.recentFiles.length > 0;

    Instantiator
    {
        model: Printer.recentFiles
        MenuItem
        {
            text:
            {
                var path = modelData.toString()
                return (index + 1) + ". " + path.slice(path.lastIndexOf("/") + 1);
            }
            onTriggered: {
                UM.MeshFileHandler.readLocalFile(modelData);
                var meshName = backgroundItem.getMeshName(modelData.toString())
                backgroundItem.hasMesh(decodeURIComponent(meshName))
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }
}
