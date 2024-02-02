// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.7 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&File")
    property var fileProviderModel: CuraApplication.getFileProviderModel()


    Cura.MenuItem
    {
        id: newProjectMenu
        action: Cura.Actions.newProject
    }

    Cura.MenuItem
    {
        id: openMenu
        action: Cura.Actions.open
        visible: base.fileProviderModel.count == 1
        enabled: base.fileProviderModel.count == 1
    }

    OpenFilesMenu
    {
        id: openFilesMenu

        shouldBeVisible: base.fileProviderModel.count > 1
        enabled: shouldBeVisible
    }

    RecentFilesMenu { }

    Cura.MenuItem
    {
        id: saveWorkspaceMenu
        shortcut: StandardKey.Save
        text: catalog.i18nc("@title:menu menubar:file", "&Save Project...")
        visible: saveProjectMenu.model.count == 1
        enabled: UM.WorkspaceFileHandler.enabled && saveProjectMenu.model.count == 1
        onTriggered:
        {
            var args = { "filter_by_machine": false, "file_type": "workspace", "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml" };
            if(UM.Preferences.getValue("cura/dialog_on_project_save"))
            {
                saveWorkspaceDialog.args = args
                saveWorkspaceDialog.open()
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
        id: savePCBMenu
        text: catalog.i18nc("@title:menu menubar:file", "&Save PCB Project...")
        enabled: UM.WorkspaceFileHandler.enabled
        onTriggered:
        {
            var args = { "filter_by_machine": false, "file_type": "workspace", "preferred_mimetypes": "application/x-pcb" };
            UM.OutputDeviceManager.requestWriteToDevice("local_file", PrintInformation.jobName, args)
        }
    }

    Cura.MenuSeparator { }

    UM.MeshWritersModel { id: meshWritersModel }

    ExportMenu
    {
        id: exportMenu
        title: catalog.i18nc("@title:menu menubar:file", "&Export...")
        model: meshWritersModel
        shouldBeVisible: model.count > 0
    }

    ExportMenu
    {
        id: exportSelectionMenu
        title: catalog.i18nc("@action:inmenu menubar:file", "Export Selection...")
        model: meshWritersModel
        shouldBeVisible: model.count > 0
        enabled: UM.Selection.hasSelection
        selectionOnly: true
    }

    Cura.MenuSeparator { }

    Cura.MenuItem
    {
        id: reloadAllMenu
        action: Cura.Actions.reloadAll
    }

    Cura.MenuSeparator { }

    Cura.MenuItem { action: Cura.Actions.quit }
}
