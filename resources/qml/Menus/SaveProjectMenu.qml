// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.1 as Cura

import "../Dialogs"

Cura.Menu
{
    id: saveProjectMenu
    title: catalog.i18nc("@title:menu menubar:file", "Save Project...")
    property alias model: projectOutputDevices.model

    Instantiator
    {
        id: projectOutputDevices
        Cura.MenuItem
        {
            text: model.name
            onTriggered:
            {
                if(!UM.WorkspaceFileHandler.enabled)
                {
                    // Prevent shortcut triggering if the item is disabled!
                    return
                }
                var args = {
                    "filter_by_machine": false,
                    "file_type": "workspace",
                    "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                    "limit_mimetypes": ["application/vnd.ms-package.3dmanufacturing-3dmodel+xml"],
                };
                if (UM.Preferences.getValue("cura/dialog_on_project_save"))
                {
                    saveWorkspaceDialog.deviceId = model.id
                    saveWorkspaceDialog.args = args
                    saveWorkspaceDialog.open()
                }
                else
                {
                    UM.OutputDeviceManager.requestWriteToDevice(model.id, PrintInformation.jobName, args)
                }
            }
            shortcut: model.shortcut
            enabled: saveProjectMenu.shouldBeVisible
        }
        onObjectAdded: function(index, object) {  saveProjectMenu.insertItem(index, object)}
        onObjectRemoved: function(index, object) {  saveProjectMenu.removeItem(object)}
    }

    WorkspaceSummaryDialog
    {
        id: saveWorkspaceDialog
        property var args
        property var deviceId
        onAccepted: UM.OutputDeviceManager.requestWriteToDevice(deviceId, PrintInformation.jobName, args)
    }
}
