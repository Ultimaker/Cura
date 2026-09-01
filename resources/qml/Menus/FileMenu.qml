// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.6 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&File")

    Cura.MenuItem
    {
        action: Cura.Actions.newProject
    }

    Cura.MenuItem
    {
        id: itemOpemFileFromDisk
        action: Cura.Actions.open
        visible: !Cura.Actions.hasExtraOpenFileActions
        enabled: visible
        text: catalog.i18nc("@action:inmenu menubar:file", "&Open File(s)...")
    }

    OpenFilesMenu
    {
        shouldBeVisible: Cura.Actions.hasExtraOpenFileActions
        title: itemOpemFileFromDisk.text
    }

    RecentFilesMenu { }

    Cura.MenuItem
    {
        id: saveWorkspaceMenu
        text: catalog.i18nc("@title:menu menubar:file", "&Save Project...")
        visible: saveProjectMenu.model.count == 1
        enabled: UM.WorkspaceFileHandler.enabled && saveProjectMenu.model.count == 1
        onTriggered:
        {
            const args = {
                "filter_by_machine": false,
                "file_type": "workspace",
                "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                "limit_mimetypes":["application/vnd.ms-package.3dmanufacturing-3dmodel+xml"],
            };
            if (UM.Preferences.getValue("cura/dialog_on_project_save"))
            {
                saveWorkspaceDialogComponent.createObject(base, {"args": args}).open()
            }
            else
            {
                UM.OutputDeviceManager.requestWriteToDevice("local_file", PrintInformation.jobName, args)
            }
        }
    }

    UM.ProjectOutputDevicesModel { id: projectOutputDevicesModel }

    SaveProjectMenu
    {
        id: saveProjectMenu
        model: projectOutputDevicesModel
        shouldBeVisible: model.count > 1
        enabled: UM.WorkspaceFileHandler.enabled
    }

    Cura.MenuItem
    {
        action: Cura.Actions.saveUCP
    }

    Cura.MenuSeparator { }

    Cura.MenuItem
    {
        action: Cura.Actions.exportAll
    }

    Cura.MenuItem
    {
        action: Cura.Actions.exportSelection
    }

    Cura.MenuSeparator { }

    Cura.MenuItem
    {
        action: Cura.Actions.reloadAll
    }

    Cura.MenuSeparator { }

    Cura.MenuItem { action: Cura.Actions.quit }
}
