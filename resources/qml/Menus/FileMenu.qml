// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.6 as UM
import Cura 1.0 as Cura

import "../Dialogs"

Cura.Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&File")
    property var fileProviderModel: CuraApplication.getFileProviderModel()

    Cura.MenuItem
    {
        action: Cura.Actions.newProject
    }

    Cura.MenuItem
    {
        action: Cura.Actions.open
    }

    Instantiator
    {
        id: fileProviderShortcuts
        model: base.fileProviderModel
        delegate: QtObject { readonly property string itemShortcut: model.shortcut }
    }

    Cura.MenuItem
    {
        text: catalog.i18nc("@action:inmenu menubar:file", "Open from Digital Library")
        enabled: base.fileProviderModel.count > 1
        shortcut: base.fileProviderModel.count > 1 ? fileProviderShortcuts.objectAt(1).itemShortcut : ""
        onTriggered: CuraApplication.getFileProviderModel().trigger("DigitalLibrary")
    }

    RecentFilesMenu { }

    Cura.MenuItem
    {
        action: Cura.Actions.save
    }

    UM.ProjectOutputDevicesModel { id: projectOutputDevicesModel }

    Instantiator
    {
        id: outputDeviceShortcuts
        model: projectOutputDevicesModel
        delegate: QtObject { readonly property string itemShortcut: model.shortcut }
    }

    Cura.MenuItem
    {
        text: catalog.i18nc("@action:inmenu menubar:file", "Save Project to Digital Library")
        enabled: projectOutputDevicesModel.count > 1 && UM.WorkspaceFileHandler.enabled
        shortcut: projectOutputDevicesModel.count > 1 ? outputDeviceShortcuts.objectAt(1).itemShortcut : ""
        onTriggered:
        {
            if (!UM.WorkspaceFileHandler.enabled)
            {
                return
            }
            const args = {
                "filter_by_machine": false,
                "file_type": "workspace",
                "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                "limit_mimetypes": ["application/vnd.ms-package.3dmanufacturing-3dmodel+xml"],
            };
            if (UM.Preferences.getValue("cura/dialog_on_project_save"))
            {
                saveWorkspaceDialogComponent.createObject(base, {"args": args, "deviceId": "digital_factory"}).open()
            }
            else
            {
                UM.OutputDeviceManager.requestWriteToDevice("digital_factory", PrintInformation.jobName, args)
            }
        }
    }

    Component
    {
        id: saveWorkspaceDialogComponent
        WorkspaceSummaryDialog
        {
            property var args
            property var deviceId
            onAccepted: UM.OutputDeviceManager.requestWriteToDevice(deviceId, PrintInformation.jobName, args)
            selfDestroy: true
        }
    }

    Cura.MenuItem
    {
        action: Cura.Actions.saveUCP
    }

    Cura.MenuSeparator { }

    Cura.MenuItem
    {
        action: Cura.Actions.export_
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

