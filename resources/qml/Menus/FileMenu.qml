// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&File")

    MenuItem
    {
        id: newProjectMenu
        action: Cura.Actions.newProject
    }

    MenuItem
    {
        id: openMenu
        action: Cura.Actions.open
    }

    RecentFilesMenu { }

    MenuItem
    {
        id: saveWorkspaceMenu
        shortcut: StandardKey.Save
        text: catalog.i18nc("@title:menu menubar:file", "&Save...")
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

    MenuSeparator { }

    MenuItem
    {
        id: saveAsMenu
        text: catalog.i18nc("@title:menu menubar:file", "&Export...")
        onTriggered:
        {
            var localDeviceId = "local_file"
            UM.OutputDeviceManager.requestWriteToDevice(localDeviceId, PrintInformation.jobName, { "filter_by_machine": false, "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"})
        }
    }

    MenuItem
    {
        id: exportSelectionMenu
        text: catalog.i18nc("@action:inmenu menubar:file", "Export Selection...")
        enabled: UM.Selection.hasSelection
        iconName: "document-save-as"
        onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file", PrintInformation.jobName, { "filter_by_machine": false, "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"})
    }

    MenuSeparator { }

    MenuItem
    {
        id: reloadAllMenu
        action: Cura.Actions.reloadAll
    }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.quit }
}