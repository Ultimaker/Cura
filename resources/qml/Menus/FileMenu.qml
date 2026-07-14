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
    property var fileProviderModel: CuraApplication.getFileProviderModel()

    Timer {
        id: menuRefreshTimerOpen
        interval: 25
        onTriggered: {
            base.open()
        }
    }

    Timer {
        id: menuRefreshTimerClose
        interval: 50
        onTriggered: {
            base.close()
        }
    }
    
    Connections {
        target: base.fileProviderModel
        function onCountChanged() {
            // workaround for a bug where the menu does not refresh (properly) when the model changes
            if (Qt.platform.os == "osx")
            {
                menuRefreshTimerOpen.restart()
                menuRefreshTimerClose.restart()
            }
        }
    }

    Cura.MenuItem
    {
        action: Cura.Actions.newProject
    }

    Cura.MenuItem
    {
        action: Cura.Actions.open
        visible: base.fileProviderModel.count == 1
    }

    OpenFilesMenu
    {
        shouldBeVisible: base.fileProviderModel.count > 1
        enabled: shouldBeVisible
    }

    RecentFilesMenu { }

    Cura.MenuItem
    {
        action: Cura.Actions.save
        visible: saveProjectMenu.model.count == 1
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
