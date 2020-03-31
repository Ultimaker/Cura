// Copyright (c) 2019 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM

import "../components"

ScrollView
{
    id: page
    clip: true
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
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            text: catalog.i18nc("@title:tab", "My installed plugins")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            id: installedPlugins
            color: "transparent"
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            visible: false  // Will become true if any children are 'repeaterized', see below.
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
                    model: toolbox.pluginsInstalledModel
                    delegate: ToolboxInstalledTile { visible: ! model.is_bundled; onVisibleChanged: { installedPlugins.visible = true } }
                }
            }
        }

        Label
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            text: catalog.i18nc("@title:tab", "My installed materials")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            id: installedMaterials
            color: "transparent"
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            visible: false  // Will become true if any children are 'repeaterized', see below.
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
                    id: installedMaterialsList
                    model: toolbox.materialsInstalledModel
                    delegate: ToolboxInstalledTile { visible: ! model.is_bundled; onVisibleChanged: { installedMaterialsList.visible = true } }
                }
            }
        }

        Label
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            text: catalog.i18nc("@title:tab", "Bundled plugins")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            id: bundledPlugins
            color: "transparent"
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            visible: false  // Will become true if any children are 'repeaterized', see below.
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
                    id: bundledPluginsList
                    model: toolbox.pluginsInstalledModel
                    delegate: ToolboxInstalledTile { visible: model.is_bundled; onVisibleChanged: { bundledPlugins.visible = true }  }
                }
            }
        }

        Label
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            text: catalog.i18nc("@title:tab", "Bundled materials")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            anchors
            {
                left: parent.left
                right: parent.right
                margins: parent.padding
            }
            id: bundledMaterials
            color: "transparent"
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            visible: false  // Will become true if any children are 'repeaterized', see below.
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
                    id: bundledMaterialsList
                    model: toolbox.materialsInstalledModel
                    delegate: ToolboxInstalledTile { visible: model.is_bundled; onVisibleChanged: { bundledMaterials.visible = true }  }
                }
            }
        }
    }
}
