// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: extensionMenu
    title: catalog.i18nc("@title:menu menubar:toplevel", "E&xtensions")
    property var extensionModel: UM.ExtensionModel { }
    Component
    {
        id: extensionsMenuItem

        Cura.MenuItem
        {
            text: modelText
            onTriggered: extensionsModel.subMenuTriggered(extensionName, modelText)
        }
    }

    Component
    {
        id: extensionsMenuSeparator

        Cura.MenuSeparator {}
    }

    Instantiator
    {
        id: extensions
        model: extensionModel

        Cura.Menu
        {
            id: sub_menu
            title: model.name
            shouldBeVisible: actions !== undefined
            enabled: actions != null
            Instantiator
            {
                model: actions
                Loader
                {
                    property var extensionsModel: extensions.model
                    property var modelText: model.text
                    property var extensionName: name

                    sourceComponent: modelText.trim() == "" ? extensionsMenuSeparator : extensionsMenuItem
                }

                onObjectAdded: function(index, object) { sub_menu.insertItem(index, object.item)}
                onObjectRemoved: function(index, object) { sub_menu.removeItem(object.item)}
            }
        }

        onObjectAdded: function(index, object) { extensionMenu.insertMenu(index, object) }
        onObjectRemoved: function(index, object) { extensionMenu.removeMenu(object)}
    }
}