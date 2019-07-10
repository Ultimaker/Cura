// Copyright (c) 2016 Ultimaker B.V.
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
                var path = modelData.toString()
                return (index + 1) + ". " + path.slice(path.lastIndexOf("/") + 1);
            }
            onTriggered:
            {
                var toShowDialog = false;
                var toOpenAsProject = false;
                var toOpenAsModel = false;

                if (CuraApplication.checkIsValidProjectFile(modelData)) {
                    // check preference
                    var choice = UM.Preferences.getValue("cura/choice_on_open_project");

                    if (choice == "open_as_project")
                    {
                        toOpenAsProject = true;
                    }else if (choice == "open_as_model"){
                        toOpenAsModel = true;
                    }else{
                        toShowDialog = true;
                    }
                }
                else {
                    toOpenAsModel = true;
                }

                if (toShowDialog) {
                    askOpenAsProjectOrModelsDialog.fileUrl = modelData;
                    askOpenAsProjectOrModelsDialog.show();
                    return;
                }

                // open file in the prefered way
                if (toOpenAsProject)
                {
                    UM.WorkspaceFileHandler.readLocalFile(modelData);
                }
                else if (toOpenAsModel)
                {
                    CuraApplication.readLocalFile(modelData, true);
                }
                var meshName = backgroundItem.getMeshName(modelData.toString())
                backgroundItem.hasMesh(decodeURIComponent(meshName))
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    Cura.AskOpenAsProjectOrModelsDialog
    {
        id: askOpenAsProjectOrModelsDialog
    }
}
