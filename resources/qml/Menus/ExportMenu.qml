// Copyright (c) 2024 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.1 as Cura

import "../Dialogs"

Cura.Menu
{
    id: exportMenu
    property alias model: meshWriters.model
    property bool selectionOnly: false

    Instantiator
    {
        id: meshWriters
        Cura.MenuItem
        {
            text: model.description
            onTriggered:
            {
                var localDeviceId = "local_file"
                var file_name = PrintInformation.jobName
                var args = { "filter_by_machine": false, "limit_mimetypes": model.mime_type}
                if(exportMenu.selectionOnly)
                {
                    UM.OutputDeviceManager.requestWriteSelectionToDevice(localDeviceId, file_name, args)
                }
                else
                {
                    UM.OutputDeviceManager.requestWriteToDevice(localDeviceId, file_name, args)
                }
            }
            shortcut: model.shortcut
            enabled: exportMenu.shouldBeVisible
        }
        onObjectAdded: function(index, object) {  exportMenu.insertItem(index, object)}
        onObjectRemoved: function(index, object) {  exportMenu.removeItem(object)}
    }
}
