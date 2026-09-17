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

    Repeater
    {
        model: Qt.platform.os === "osx" ? 0 : 1 // MacOS ignores the menus visibility, so we need to really not create it
        Cura.MenuItem
        {
            id: itemOpemFileFromDisk
            action: Cura.Actions.open
            visible: !Cura.Actions.hasExtraOpenFileActions
            enabled: visible
            text: openFileMenu.title
        }
    }

    OpenFilesMenu
    {
        id: openFileMenu
        shouldBeVisible: Cura.Actions.hasExtraOpenFileActions
        title: catalog.i18nc("@action:inmenu menubar:file", "&Open File(s)...")
    }

    RecentFilesMenu { }

    Repeater
    {
        model: Qt.platform.os === "osx" ? 0 : 1 // MacOS ignores the menus visibility, so we need to really not create it
        Cura.MenuItem
        {
            id: saveWorkspaceMenu
            action: Cura.Actions.saveWorkspaceActions[0]
            visible: !Cura.Actions.hasExtraSaveWorkspaceActions
            text: saveProjectMenu.title
        }
    }

    SaveProjectMenu
    {
        id: saveProjectMenu
        shouldBeVisible: Cura.Actions.hasExtraSaveWorkspaceActions
        title: catalog.i18nc("@action:inmenu menubar:file", "&Save Project...")
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
