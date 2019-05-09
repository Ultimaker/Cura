// Copyright (c) 2019 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM
import Cura 1.1 as Cura

Cura.ScrollView
{
    id: page
    width: parent.width
    height: parent.height

    Column
    {
        width: page.width
        spacing: UM.Theme.getSize("default_margin").height
        padding: UM.Theme.getSize("wide_margin").width
        visible: toolbox.pluginsInstalledModel.items.length > 0
        height: childrenRect.height + 2 * UM.Theme.getSize("wide_margin").height

        Label
        {
            width: parent.width - 2 * parent.padding
            text: catalog.i18nc("@title:tab", "Plugins")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("large")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            id: installedPlugins
            color: "transparent"
            width: parent.width - 2 * parent.padding
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            Column
            {
                anchors
                {
                    top: parent.top
                    right: parent.right
                    left: parent.left
                    margins: UM.Theme.getSize("default_margin").width
                }
                Repeater
                {
                    id: materialList
                    model: toolbox.pluginsInstalledModel
                    delegate: ToolboxInstalledTile {}
                }
            }
        }

        Label
        {
            width: parent.width - 2 * parent.padding
            text: catalog.i18nc("@title:tab", "Materials")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            id: installedMaterials
            color: "transparent"
            width: parent.width - 2 * parent.padding
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            Column
            {
                anchors
                {
                    top: parent.top
                    right: parent.right
                    left: parent.left
                    margins: UM.Theme.getSize("default_margin").width
                }
                Repeater
                {
                    id: pluginList
                    model: toolbox.materialsInstalledModel
                    delegate: ToolboxInstalledTile {}
                }
            }
        }
    }
}
